"""
Chroma Lie - a deceptive 2D puzzle-platformer.
Run:  python main.py

main.py owns the loop and the game states: menu, level select, how-to, play, pause, end.
"""
import json
import os
import random
import sys
import pygame

from config import (TITLE, WIDTH, HEIGHT, FPS, FULLSCREEN, VSYNC, TILE, RED, EXIT, PLAYER, HAZARD,
                    MOTION, COLOR_OF_TILE, SPARK_RATE, DEATH_RESET_DELAY, WIN_DELAY, INTRO_TIME,
                    SAVE_FILE, TEXT_DIM, MOTION_FUSE)
from levels_data import LEVELS
from level import Level, check_collisions
from player import Player, InputState
from deception import DeceptionSystem
from effects import Effects, Background, scale_color
from audio import Audio
from ui import UI, Button

if getattr(sys, "frozen", False):                    # PyInstaller exe: save next to the .exe
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(BASE_DIR, SAVE_FILE)


def load_save():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("unlocked", 1)
        data.setdefault("best", {})
        data.setdefault("muted", False)
        return data
    except (OSError, ValueError):
        return {"unlocked": 1, "best": {}}


def write_save(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


class Game:
    def __init__(self, headless=False):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.fullscreen = FULLSCREEN and not headless
        self.screen = self._make_display()
        self.clock = pygame.time.Clock()
        self.frame = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.ui = UI()
        self.fx = Effects()
        self.bg = Background()
        self.input = InputState()
        self.save = load_save()
        self.audio = Audio(muted=self.save.get("muted", False))   # fails soft without a device
        self.t = 0.0
        self.running = True

        self.state = "menu"
        self.menu_sel = 0
        self.pause_sel = 0
        self.select_sel = 0
        self.end_time = 0.0
        self.run_deaths = 0
        self._build_menu()

        self.level_index = 0
        self.level = self.deception = self.player = None
        self.deaths = 0

    # ------------------------------------------------------------ display
    def _make_display(self):
        flags = pygame.SCALED  # renders at 960x640, scales to any monitor with letterboxing
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            return pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1 if VSYNC else 0)
        except (pygame.error, TypeError):
            return pygame.display.set_mode((WIDTH, HEIGHT), flags)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            self.screen = self._make_display()

    # ------------------------------------------------------------ menus
    def _build_menu(self):
        nxt = min(self.save["unlocked"], len(LEVELS))
        self.menu_buttons = [Button("START", "start")]
        if nxt > 1:
            self.menu_buttons.insert(0, Button("CONTINUE  ({:02d})".format(nxt), "continue"))
        self.menu_buttons += [Button("LEVEL SELECT", "select"), Button("HOW TO PLAY", "howto"), Button("QUIT", "quit")]
        self.ui.layout_buttons(self.menu_buttons, 330)
        self.menu_sel = 0
        self.pause_buttons = [Button("RESUME", "resume"), Button("RESTART LEVEL", "restart"), Button("MAIN MENU", "menu")]
        self.ui.layout_buttons(self.pause_buttons, 300)

    def menu_action(self, action):
        if action == "start":
            self.run_deaths = 0
            self.start_level(0)
        elif action == "continue":
            self.run_deaths = 0
            self.start_level(min(self.save["unlocked"], len(LEVELS)) - 1)
        elif action == "select":
            self.state = "select"
            self.select_sel = min(self.save["unlocked"], len(LEVELS)) - 1
        elif action == "howto":
            self.state = "howto"
        elif action == "quit":
            self.running = False
        elif action == "resume":
            self.state = "play"
        elif action == "restart":
            self.state = "play"
            self.reset_level()
        elif action == "menu":
            self._build_menu()
            self.state = "menu"

    # ------------------------------------------------------------ level flow
    def start_level(self, idx):
        self.level_index = idx
        self.deaths = 0
        self.intro = INTRO_TIME
        self.reset_level()
        self.state = "play"

    def reset_level(self):
        data = LEVELS[self.level_index]
        self.level = Level(data)
        self.deception = DeceptionSystem(data)
        self.player = Player(*self.level.spawn)
        self.dead_timer = 0.0
        self.win_timer = 0.0
        self.fx.glitch.timer = 0.0

    def kill_player(self, reason):
        r = self.player.rect
        self.audio.play("death_" + reason)          # each death reason has its own sound
        self.fx.particles.burst(r.centerx, r.centery, PLAYER, 26)
        self.fx.particles.burst(r.centerx, r.centery, RED, 18, speed=(60, 240))
        self.fx.flash.trigger(RED, 120)
        self.fx.shake.add(0.6)
        self.deaths += 1
        self.run_deaths += 1
        self.dead_timer = DEATH_RESET_DELAY

    def win_level(self):
        r = self.level.exit_rect
        self.audio.play("win")
        self.fx.particles.burst(r.centerx, r.centery, EXIT, 40, speed=(60, 260), gravity=-80)
        self.fx.flash.trigger(EXIT, 70)
        self.win_timer = WIN_DELAY
        n = self.level_index + 1
        best = self.save["best"].get(str(n))
        if best is None or self.deaths < best:
            self.save["best"][str(n)] = self.deaths
        self.save["unlocked"] = max(self.save["unlocked"], min(n + 1, len(LEVELS)))
        write_save(self.save)

    # ------------------------------------------------------------ events
    def handle_events(self):
        jump_pressed = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if self.state == "play":
                    if e.key in InputState.JUMP:
                        jump_pressed = True
                    elif e.key == pygame.K_r:
                        self.reset_level()
                    elif e.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.state = "pause"
                        self.pause_sel = 0
                if e.key == pygame.K_m:
                    self.save["muted"] = self.audio.toggle_mute()
                    write_save(self.save)
                elif self.state == "menu":
                    self._nav(e, self.menu_buttons, "menu_sel", back=lambda: setattr(self, "running", False))
                elif self.state == "pause":
                    self._nav(e, self.pause_buttons, "pause_sel", back=lambda: setattr(self, "state", "play"))
                elif self.state == "select":
                    self._select_keys(e)
                elif self.state == "howto":
                    if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        self.audio.play("back")
                        self.state = "menu"
                elif self.state == "end":
                    if self.end_time > 2.0 and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_KP_ENTER):
                        self._build_menu()
                        self.state = "menu"
            elif e.type == pygame.MOUSEMOTION:
                self._hover(e.pos)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._click(e.pos)
        self.input.poll(jump_pressed)

    def _nav(self, e, buttons, attr, back):
        sel = getattr(self, attr)
        if e.key in (pygame.K_DOWN, pygame.K_s):
            setattr(self, attr, (sel + 1) % len(buttons))
            self.audio.play("move")
        elif e.key in (pygame.K_UP, pygame.K_w):
            setattr(self, attr, (sel - 1) % len(buttons))
            self.audio.play("move")
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self.audio.play("confirm")
            self.menu_action(buttons[sel].action)
        elif e.key == pygame.K_ESCAPE:
            self.audio.play("back")
            back()

    def _select_keys(self, e):
        s = self.select_sel
        if e.key == pygame.K_RIGHT:
            s = min(14, s + 1)
        elif e.key == pygame.K_LEFT:
            s = max(0, s - 1)
        elif e.key == pygame.K_DOWN:
            s = min(14, s + 5)
        elif e.key == pygame.K_UP:
            s = max(0, s - 5)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if s < self.save["unlocked"]:
                self.audio.play("confirm")
                self.run_deaths = 0
                self.start_level(s)
        elif e.key == pygame.K_ESCAPE:
            self.audio.play("back")
            self.state = "menu"
        if s != self.select_sel:
            self.audio.play("move")
        self.select_sel = s

    def _hover(self, pos):
        if self.state in ("menu", "pause"):
            buttons = self.menu_buttons if self.state == "menu" else self.pause_buttons
            for i, b in enumerate(buttons):
                if b.rect.collidepoint(pos):
                    if self.state == "menu":
                        self.menu_sel = i
                    else:
                        self.pause_sel = i
        elif self.state == "select":
            for i, r in enumerate(getattr(self, "_cells", [])):
                if r.collidepoint(pos):
                    self.select_sel = i

    def _click(self, pos):
        if self.state in ("menu", "pause"):
            buttons = self.menu_buttons if self.state == "menu" else self.pause_buttons
            for b in buttons:
                if b.rect.collidepoint(pos):
                    self.menu_action(b.action)
                    return
        elif self.state == "select":
            for i, r in enumerate(getattr(self, "_cells", [])):
                if r.collidepoint(pos) and i < self.save["unlocked"]:
                    self.run_deaths = 0
                    self.start_level(i)
        elif self.state == "howto":
            self.state = "menu"
        elif self.state == "end" and self.end_time > 2.0:
            self._build_menu()
            self.state = "menu"

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        self.bg.update(dt)
        self.fx.update(dt)
        if self.state == "play":
            self.update_play(dt)
        elif self.state == "end":
            self.end_time += dt

    def update_play(self, dt):
        self.intro = max(0.0, self.intro - dt)
        if self.win_timer > 0:
            self.win_timer -= dt
            self.level.update_parts(dt)
            if self.win_timer <= 0:
                if self.level_index + 1 < len(LEVELS):
                    self.start_level(self.level_index + 1)
                else:
                    self.state = "end"
                    self.end_time = 0.0
            return
        if self.dead_timer > 0:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.reset_level()
            return

        self.deception.update(dt, self.player.rect)
        for sig in self.deception.signals:
            if sig == "glitch":
                self.fx.glitch.trigger(0.4, 1.0)
                self.fx.shake.add(0.45)
            elif sig == "blip":
                self.fx.glitch.trigger(0.18, 0.5)
                self.fx.shake.add(0.2)
        self.deception.signals.clear()

        self.level.update_parts(dt)
        self.player.update(dt, self.input, self.level, self.deception.controls_swapped)
        self.level.update_tiles(dt, self.player)

        result, reason = check_collisions(self.player.rect, self.level, self.deception)
        if result == "exit":
            self.win_level()
        elif result == "danger":
            self.kill_player(reason)
        self._spawn_ambient(dt)

    def _spawn_ambient(self, dt):
        p = self.player
        r = p.rect
        # one-shot movement sounds
        if p.just_jumped:
            self.audio.play("jump")
        if p.just_landed:
            self.audio.play("land")
        if p.sprung:
            self.audio.play("spring")
        # movement trail
        if abs(p.vx) > 40 or abs(p.vy) > 60:
            if random.random() < 0.8:
                self.fx.particles.emit(r.centerx + random.uniform(-6, 6), r.centery + random.uniform(-6, 6),
                                       -p.vx * 0.05, -p.vy * 0.05, random.uniform(0.2, 0.4), random.uniform(2, 5),
                                       scale_color(PLAYER, 0.6))
        if p.just_landed:
            for _ in range(8):
                self.fx.particles.emit(r.centerx + random.uniform(-10, 10), r.bottom, random.uniform(-90, 90),
                                       random.uniform(-80, -20), 0.35, 3, scale_color(PLAYER, 0.6), 300)
        if p.sprung:
            self.fx.particles.burst(r.centerx, r.bottom, EXIT, 14, speed=(60, 200), gravity=200)
        # THE honest tell: deadly colored tiles quietly shed sparks
        for kind in ("R", "B", "P"):
            if not self.deception.is_danger(kind):
                continue
            color = COLOR_OF_TILE[kind]
            for tr in self.level.by_kind.get(kind, []):
                if random.random() < SPARK_RATE * dt:
                    self.fx.particles.emit(tr.x + random.uniform(3, TILE - 3), tr.y + random.uniform(-2, 4),
                                           random.uniform(-6, 6), random.uniform(-40, -18), random.uniform(0.5, 0.9),
                                           random.uniform(1.5, 2.8), color, -10)
        if self.level.late_active:
            for tr in self.level.by_kind.get("L", []):
                if random.random() < SPARK_RATE * dt:
                    self.fx.particles.emit(tr.x + random.uniform(2, TILE - 2), tr.y, random.uniform(-6, 6),
                                           random.uniform(-40, -18), 0.7, 2.2, HAZARD, -10)
        if self.level.motion_fuse > 0:
            k = self.level.motion_fuse / MOTION_FUSE
            for tr in self.level.motion_touch:
                if random.random() < 12 * k * dt:
                    self.fx.particles.emit(tr.x + random.uniform(0, TILE), tr.y, 0, random.uniform(-60, -30),
                                           0.4, 2.5, RED, -20)
        # exit shimmer
        er = self.level.exit_rect
        if random.random() < 8 * dt:
            self.fx.particles.emit(er.x + random.uniform(2, er.w - 2), er.bottom - 4, random.uniform(-8, 8),
                                   random.uniform(-70, -30), random.uniform(0.6, 1.1), random.uniform(2, 3.5), EXIT, -20)

    # ------------------------------------------------------------ draw
    def draw(self):
        f = self.frame
        self.bg.draw(f)
        if self.state in ("play", "pause"):
            self.draw_play(f)
        elif self.state == "menu":
            self._menu_backdrop(f)
            self.ui.draw_title(f, self.t)
            self.ui.text(f, "trust what you see", self.ui.f_small, TEXT_DIM, center=(WIDTH // 2, 232))
            self.ui.draw_buttons(f, self.menu_buttons, self.menu_sel, self.t)
            self.ui.text(f, "arrows + ENTER  or  mouse      F11 fullscreen", self.ui.f_tiny, TEXT_DIM,
                         center=(WIDTH // 2, HEIGHT - 26))
        elif self.state == "select":
            self._cells = self.ui.draw_level_select(f, self.save["unlocked"], self.select_sel, LEVELS, self.t,
                                                    self.save["best"])
        elif self.state == "howto":
            self.ui.draw_how_to(f, self.t)
        elif self.state == "end":
            self.fx.particles.draw(f)
            if random.random() < 0.3:
                self.fx.particles.emit(random.uniform(0, WIDTH), HEIGHT + 4, 0, random.uniform(-80, -30), 4,
                                       random.uniform(2, 4), random.choice((RED, EXIT, (46, 196, 255))), 0)
            self.ui.draw_end(f, self.t, self.run_deaths, self.end_time)

        self.bg.draw_vignette(f)
        out = self.fx.glitch.apply(f)
        if self.state in ("play", "pause"):
            self.draw_hud(out)
        self.screen.fill((0, 0, 0))
        ox, oy = self.fx.shake.offset() if self.state == "play" else (0, 0)
        self.screen.blit(out, (ox, oy))
        pygame.display.flip()

    def _menu_backdrop(self, f):
        # a few drifting colored tiles for flavor
        for i, col in enumerate(((255, 59, 92), (46, 196, 255), (184, 77, 255))):
            x = (self.t * (18 + i * 7) + i * 330) % (WIDTH + 80) - 40
            y = 470 + i * 40
            r = pygame.Rect(int(x), y, 28, 28)
            f.fill(scale_color(col, 0.25), r.inflate(10, 10), special_flags=pygame.BLEND_ADD)
            pygame.draw.rect(f, col, r, 2, border_radius=4)

    def draw_play(self, f):
        self.level.draw(f, self.deception, self.t)
        self.fx.particles.draw(f)
        if self.dead_timer <= 0 and self.win_timer <= 0:
            self.player.draw(f, self.t)
        self.fx.flash.draw(f)

    def draw_hud(self, out):
        d = self.deception
        self.ui.draw_banner(out, d.shown_text(), d.text_glitch, self.t, d.cycle_progress())
        self.ui.draw_hud(out, LEVELS[self.level_index], self.deaths, self.t, self.intro)
        self.ui.draw_message(out, d.message, d.message_timer, self.t)
        if self.state == "pause":
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((8, 10, 16, 170))
            out.blit(dim, (0, 0))
            self.ui.text(out, "PAUSED", self.ui.f_big, (232, 236, 248), center=(WIDTH // 2, 210))
            self.ui.draw_buttons(out, self.pause_buttons, self.pause_sel, self.t)

    # ------------------------------------------------------------ loop
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)   # delta time, clamped
            self.handle_events()
            # two sub-steps keep collisions solid even on slow frames
            steps = 2 if dt > 1 / 55 else 1
            for _ in range(steps):
                self.update(dt / steps)
                self.input.jump_pressed = False      # the jump buffer remembers it
            self.draw()
        if self.audio.ok:
            pygame.mixer.quit()          # close the audio device cleanly
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
    sys.exit(0)
