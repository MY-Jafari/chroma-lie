"""
ui.py - HUD, the instruction banner (which may lie), menus and screens.
Fonts are loaded once at start-up.
"""
import math
import random
import pygame
from config import (WIDTH, HEIGHT, RED, BLUE, PURPLE, TEXT, TEXT_DIM, PANEL, PANEL_EDGE, EXIT,
                    HAZARD, PLAYER, INTRO_TIME)
from effects import blur, scale_color, mix, blit_glow

WORD_COLORS = {"RED": RED, "BLUE": BLUE, "PURPLE": PURPLE, "DANGER": (255, 140, 150),
               "SAFE": (160, 235, 255), "???": PURPLE}
GLITCH_CHARS = "#@%&$!?/\\<>*"
FONT_NAMES = "bahnschrift,segoeuisemibold,segoeui,montserrat,arialblack,helveticaneue,arial,dejavusans"


def load_font(size, bold=True):
    try:
        f = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
        if f is not None:
            return f
    except Exception:
        pass
    return pygame.font.Font(None, int(size * 1.3))


class Button:
    def __init__(self, label, action, enabled=True):
        self.label, self.action, self.enabled = label, action, enabled
        self.rect = pygame.Rect(0, 0, 300, 50)


class UI:
    def __init__(self):
        self.f_title = load_font(96)
        self.f_big = load_font(40)
        self.f_banner = load_font(30)
        self.f_mid = load_font(26)
        self.f_small = load_font(18, bold=False)
        self.f_tiny = load_font(15, bold=False)
        self._banner_cache = {}
        self._title_cache = None

    # ------------------------------------------------------------ helpers
    def text(self, surf, s, font, color, center=None, topleft=None, topright=None, alpha=255):
        img = font.render(s, True, color)
        if alpha < 255:
            img.set_alpha(alpha)
        r = img.get_rect()
        if center:
            r.center = center
        elif topleft:
            r.topleft = topleft
        elif topright:
            r.topright = topright
        surf.blit(img, r)
        return r

    def glow_text(self, surf, s, font, color, center, glow=0.6):
        img = font.render(s, True, color)
        r = img.get_rect(center=center)
        pad = 24
        g = pygame.Surface((r.w + pad * 2, r.h + pad * 2))
        g.fill((0, 0, 0))
        g.blit(font.render(s, True, scale_color(color, glow)), (pad, pad))
        g = blur(g, 5)
        surf.blit(g, (r.x - pad, r.y - pad), special_flags=pygame.BLEND_ADD)
        surf.blit(img, r)
        return r

    def panel(self, surf, rect, alpha=210, edge=PANEL_EDGE, radius=14):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, PANEL + (alpha,), s.get_rect(), border_radius=radius)
        pygame.draw.rect(s, edge + (255,), s.get_rect(), 1, border_radius=radius)
        surf.blit(s, rect.topleft)

    # ------------------------------------------------------------ instruction banner
    def _render_banner(self, text, cache=True):
        """Render the instruction with colored keywords and a soft glow. Cached per text."""
        if cache and text in self._banner_cache:
            return self._banner_cache[text]
        parts = []
        for word in text.split(" "):
            if word == "":
                parts.append((" ", TEXT))
                continue
            parts.append((word + " ", WORD_COLORS.get(word, TEXT)))
        imgs = [self.f_banner.render(w, True, c) for w, c in parts]
        w = sum(i.get_width() for i in imgs)
        h = max(i.get_height() for i in imgs)
        pad = 22
        base = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        glow = pygame.Surface(base.get_size())
        glow.fill((0, 0, 0))
        x = pad
        for img, (wd, c) in zip(imgs, parts):
            base.blit(img, (x, pad))
            glow.blit(self.f_banner.render(wd, True, scale_color(c, 0.55)), (x, pad))
            x += img.get_width()
        if not cache:
            return base, None
        result = (base, blur(glow, 5))
        self._banner_cache[text] = result
        return result

    def draw_banner(self, surf, text, glitch, t, cycle_progress=None):
        base, glow = self._render_banner(text)
        cx = WIDTH // 2
        rect = base.get_rect(center=(cx, 40))
        box = pygame.Rect(0, 0, rect.w - 10, 48)
        box.center = (cx, 40)
        self.panel(surf, box, 200, radius=24)
        if glitch > 0:
            # chromatic split + scrambled characters: something just changed
            scrambled = "".join(random.choice(GLITCH_CHARS) if (ch != " " and random.random() < 0.25) else ch
                                for ch in text)
            gb, _ = self._render_banner(scrambled, cache=False)
            dx = random.randint(3, 9)
            red = gb.copy()
            red.fill((255, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
            cyan = gb.copy()
            cyan.fill((0, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            r2 = gb.get_rect(center=(cx, 40))
            surf.blit(red, r2.move(-dx, random.randint(-2, 2)))
            surf.blit(cyan, r2.move(dx, random.randint(-2, 2)))
        else:
            surf.blit(glow, rect, special_flags=pygame.BLEND_ADD)
            surf.blit(base, rect)
        if cycle_progress is not None:
            bar = pygame.Rect(box.x + 24, box.bottom + 6, box.w - 48, 4)
            pygame.draw.rect(surf, PANEL_EDGE, bar, border_radius=2)
            fill = bar.copy()
            fill.w = int(bar.w * cycle_progress)
            col = HAZARD if cycle_progress > 0.82 else TEXT_DIM
            pygame.draw.rect(surf, col, fill, border_radius=2)

    # ------------------------------------------------------------ HUD
    def draw_hud(self, surf, level_def, deaths, t, intro):
        # top-right: level + deaths
        r = pygame.Rect(WIDTH - 178, 16, 162, 48)
        self.panel(surf, r, 190, radius=12)
        self.text(surf, "LEVEL", self.f_tiny, TEXT_DIM, topleft=(r.x + 14, r.y + 7))
        self.text(surf, "{:02d}/15".format(level_def["id"]), self.f_mid, TEXT, topleft=(r.x + 14, r.y + 18))
        self.text(surf, "DEATHS", self.f_tiny, TEXT_DIM, topright=(r.right - 14, r.y + 7))
        self.text(surf, str(deaths), self.f_mid, RED if deaths else TEXT, topright=(r.right - 14, r.y + 18))
        # top-left: level title
        self.text(surf, level_def["title"], self.f_small, TEXT_DIM, topleft=(20, 22))
        # bottom hint
        self.text(surf, "R restart   ESC pause   F11 fullscreen", self.f_tiny, scale_color(TEXT_DIM, 0.8),
                  topleft=(18, HEIGHT - 24))
        # intro card
        if intro > 0:
            k = min(1.0, intro / 0.5, (INTRO_TIME - intro) / 0.25 + 0.001)
            a = int(255 * max(0.0, min(1.0, k)))
            card = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
            card.fill((10, 12, 18, int(a * 0.75)))
            surf.blit(card, (0, HEIGHT // 2 - 60))
            self.text(surf, "LEVEL {:02d}".format(level_def["id"]), self.f_small, TEXT_DIM,
                      center=(WIDTH // 2, HEIGHT // 2 - 26), alpha=a)
            self.text(surf, level_def["title"], self.f_big, TEXT, center=(WIDTH // 2, HEIGHT // 2 + 12), alpha=a)

    def draw_message(self, surf, message, timer, t):
        if not message:
            return
        a = int(255 * max(0.0, min(1.0, timer / 0.5, 1.0)))
        jitter = (random.randint(-1, 1), random.randint(-1, 1)) if random.random() < 0.15 else (0, 0)
        self.text(surf, message, self.f_big, (200, 205, 225), center=(WIDTH // 2 + jitter[0], 150 + jitter[1]), alpha=a)

    # ------------------------------------------------------------ menus
    def layout_buttons(self, buttons, top, width=320, height=50, gap=12):
        for i, b in enumerate(buttons):
            b.rect = pygame.Rect(0, 0, width, height)
            b.rect.center = (WIDTH // 2, top + i * (height + gap))

    def draw_buttons(self, surf, buttons, selected, t):
        for i, b in enumerate(buttons):
            sel = i == selected and b.enabled
            edge = mix(BLUE, (255, 255, 255), 0.2) if sel else PANEL_EDGE
            if sel:
                blit_glow(surf, b.rect.center, 90, BLUE, 0.25)
            self.panel(surf, b.rect, 235 if sel else 180, edge=edge, radius=12)
            col = TEXT if b.enabled else scale_color(TEXT_DIM, 0.6)
            self.text(surf, b.label, self.f_mid, col, center=b.rect.center)
            if sel:
                pygame.draw.rect(surf, BLUE, (b.rect.x + 14, b.rect.centery - 6, 6, 12), border_radius=2)

    def draw_title(self, surf, t, y=160):
        """'CHROMA LIE' with a living chromatic split that sometimes glitches hard."""
        word = "CHROMA LIE"
        img = self.f_title.render(word, True, TEXT)
        r = img.get_rect(center=(WIDTH // 2, y))
        hard = (t % 3.7) < 0.18
        dx = 3 + (random.randint(4, 14) if hard else int(2 * math.sin(t * 2)))
        red = self.f_title.render(word, True, RED)
        blue = self.f_title.render(word, True, BLUE)
        glow = pygame.Surface((r.w + 60, r.h + 60))
        glow.fill((0, 0, 0))
        glow.blit(self.f_title.render(word, True, (90, 90, 130)), (30, 30))
        surf.blit(blur(glow, 6), (r.x - 30, r.y - 30), special_flags=pygame.BLEND_ADD)
        surf.blit(red, r.move(-dx, 0), special_flags=pygame.BLEND_ADD)
        surf.blit(blue, r.move(dx, 0), special_flags=pygame.BLEND_ADD)
        surf.blit(img, r, special_flags=pygame.BLEND_ADD if hard else 0)

    def draw_level_select(self, surf, unlocked, selected, levels, t, best):
        self.text(surf, "SELECT LEVEL", self.f_big, TEXT, center=(WIDTH // 2, 80))
        cells = []
        size, gap = 104, 20
        total_w = 5 * size + 4 * gap
        x0 = (WIDTH - total_w) // 2
        for i in range(15):
            c, r = i % 5, i // 5
            rect = pygame.Rect(x0 + c * (size + gap), 150 + r * (size + gap), size, size)
            cells.append(rect)
            open_ = i < unlocked
            sel = i == selected
            edge = BLUE if sel else (PANEL_EDGE if open_ else (40, 44, 60))
            if sel:
                blit_glow(surf, rect.center, 80, BLUE, 0.3)
            self.panel(surf, rect, 230 if open_ else 120, edge=edge, radius=14)
            if open_:
                self.text(surf, "{:02d}".format(i + 1), self.f_big, TEXT, center=(rect.centerx, rect.centery - 10))
                label = "{} deaths".format(best[str(i + 1)]) if str(i + 1) in best else "new"
                self.text(surf, label, self.f_tiny, TEXT_DIM, center=(rect.centerx, rect.centery + 28))
            else:
                lock = pygame.Rect(0, 0, 22, 18)
                lock.center = (rect.centerx, rect.centery + 6)
                pygame.draw.rect(surf, (70, 76, 100), lock, border_radius=3)
                pygame.draw.arc(surf, (70, 76, 100), (lock.x + 3, lock.y - 12, 16, 20), 0, math.pi, 3)
        name = levels[selected]["title"] if selected < unlocked else "LOCKED"
        self.text(surf, name, self.f_mid, TEXT, center=(WIDTH // 2, 540))
        self.text(surf, "arrows to choose   ENTER to play   ESC back", self.f_small, TEXT_DIM,
                  center=(WIDTH // 2, 590))
        return cells

    def draw_how_to(self, surf, t):
        self.text(surf, "HOW TO PLAY", self.f_big, TEXT, center=(WIDTH // 2, 90))
        box = pygame.Rect(WIDTH // 2 - 330, 140, 660, 380)
        self.panel(surf, box, 210)
        lines = [
            ("ARROWS / A D", "move"),
            ("SPACE", "jump (hold for higher)"),
            ("R", "restart level"),
            ("ESC", "pause"),
            ("F11", "toggle fullscreen"),
        ]
        for i, (k, v) in enumerate(lines):
            y = box.y + 36 + i * 40
            self.text(surf, k, self.f_mid, BLUE, topleft=(box.x + 50, y))
            self.text(surf, v, self.f_mid, TEXT, topleft=(box.x + 300, y))
        tips = ["Reach the glowing gate. Touch anything deadly and you restart instantly.",
                "Amber things are always deadly. Colors mean what the screen says... usually.",
                "The world never lies as well as the words do. Watch closely."]
        for i, s in enumerate(tips):
            self.text(surf, s, self.f_small, TEXT_DIM, center=(WIDTH // 2, box.y + 262 + i * 30))
        self.text(surf, "ESC / ENTER to go back", self.f_small, TEXT_DIM, center=(WIDTH // 2, 580))

    def draw_end(self, surf, t, deaths, elapsed):
        lines = ["No rule was ever absolute.",
                 "The text lied. The colors lied. Your eyes never did.",
                 "Trust what you observe over what you are told."]
        self.draw_title(surf, t, 130)
        for i, s in enumerate(lines):
            start = 0.6 + i * 1.3
            if elapsed < start:
                break
            n = int((elapsed - start) * 40)
            shown = s[:n]
            self.text(surf, shown, self.f_mid, TEXT if i < 2 else EXIT, center=(WIDTH // 2, 290 + i * 48))
        if elapsed > 4.8:
            self.text(surf, "total deaths: {}".format(deaths), self.f_small, TEXT_DIM, center=(WIDTH // 2, 470))
            a = int(160 + 95 * math.sin(t * 3))
            self.text(surf, "press ENTER", self.f_small, (a, a, a), center=(WIDTH // 2, 540))
