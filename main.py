"""Chroma Lie - Main Game Entry Point.

A 2D puzzle-action game where the rules lie and the player must adapt.
"""

import sys
import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    WINDOW_TITLE,
    BG_COLOR,
    RED_DANGER,
    BLUE_SAFE,
    EXIT_GATE_COLOR,
    GLITCH_DURATION,
    GLITCH_INTENSITY,
    CAMERA_SHAKE_DURATION,
    CAMERA_SHAKE_INTENSITY,
    DEATH_RESPAWN_DELAY,
    COYOTE_TIME,
    JUMP_BUFFER_TIME,
)
from player import Player
from level import Level
from levels_data import LEVELS, get_level, get_total_levels
from deception import deception
from effects import BackgroundGrid, CameraShake, GlitchManager, ParticleSystem
from ui import UIManager


class GameState:
    MENU = "menu"
    HOW_TO_PLAY = "how_to_play"
    PLAYING = "playing"
    LEVEL_COMPLETE = "level_complete"
    NARRATIVE_ENDING = "narrative_ending"


class ChromaLie:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = GameState.MENU
        self.current_level_idx = 0
        self.total_deaths = 0

        # Core systems
        self.background = BackgroundGrid()
        self.camera_shake = CameraShake()
        self.glitch = GlitchManager()
        self.particles = ParticleSystem()
        self.ui = UIManager()

        # Game objects
        self.player = None
        self.current_level = None
        self.level_data = None

        # Timers
        self.menu_timer = 0.0
        self.menu_selected = 0
        self.ending_timer = 0.0
        self.transition_timer = 0.0
        self.level_complete_timer = 0.0

        # Audio init (optional - placeholder for future sound)
        self.sfx_enabled = True

        self.load_level(1)

    def load_level(self, level_num):
        """Initialize a new level."""
        self.level_data = get_level(level_num)
        if not self.level_data:
            return False

        self.current_level_idx = level_num - 1
        self.current_level = Level(self.level_data)
        start_x, start_y = self.level_data["player_start"]

        # Reset player
        if self.player is None:
            self.player = Player(start_x, start_y)
        else:
            self.player.reset(start_x, start_y)

        # Reset deception for this level
        rule_change = self.level_data.get("rule_change", None)
        deception.reset_for_level(level_num, rule_change)

        # Apply all scripted rule changes
        changes = rule_change if isinstance(rule_change, list) else ([rule_change] if rule_change else [])
        for change in changes:
            if change.get("type") != "none":
                deception.apply_scripted_change(change)

        # Trigger glitch visual if any change occurred
        if changes:
            self.glitch.trigger(GLITCH_DURATION, GLITCH_INTENSITY)
            self.camera_shake.start(CAMERA_SHAKE_DURATION, CAMERA_SHAKE_INTENSITY)

        self.level_complete_timer = 0.0
        self.death_timer = 0.0
        return True

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Process all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    self.handle_menu_input(event.key)
                elif self.state == GameState.HOW_TO_PLAY:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self.state = GameState.MENU
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    elif event.key == pygame.K_r:
                        self.restart_level()
                    else:
                        self.player.handle_event(event)
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.advance_level()
                elif self.state == GameState.NARRATIVE_ENDING:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.return_to_menu()

            elif event.type == pygame.KEYUP and self.state == GameState.PLAYING:
                # KEYUP must reach the player or a held key stays stuck on
                self.player.handle_event(event)

    def handle_menu_input(self, key):
        """Handle main menu navigation."""
        if key == pygame.K_UP:
            self.menu_selected = (self.menu_selected - 1) % 3
        elif key == pygame.K_DOWN:
            self.menu_selected = (self.menu_selected + 1) % 3
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu_selected == 0:
                self.start_game()
            elif self.menu_selected == 1:
                self.state = GameState.HOW_TO_PLAY
            elif self.menu_selected == 2:
                self.running = False

    def start_game(self):
        """Begin a fresh playthrough from level 1."""
        self.current_level_idx = 0
        self.total_deaths = 0
        self.load_level(1)
        self.state = GameState.PLAYING

    def advance_level(self):
        """Move to next level or trigger ending."""
        self.current_level_idx += 1
        next_level = self.current_level_idx + 1

        if next_level > get_total_levels():
            self.state = GameState.NARRATIVE_ENDING
            self.ending_timer = 0.0
        else:
            self.load_level(next_level)
            self.state = GameState.PLAYING

    def restart_level(self):
        """Immediate level restart on death."""
        self.total_deaths += 1
        if self.current_level:
            self.current_level.death_count += 1
        self.load_level(self.current_level_idx + 1)
    def return_to_menu(self):
        """Return to main menu after game completion."""
        self.state = GameState.MENU
        self.menu_selected = 0
        self.menu_timer = 0.0

    def update(self, dt):
        """Update all game systems."""
        self.background.update(dt)
        self.camera_shake.update(dt)
        self.glitch.update(dt)
        self.particles.update(dt)
        self.ui.update(dt)

        if self.state == GameState.MENU:
            self.menu_timer += dt
        elif self.state == GameState.PLAYING:
            self.update_playing(dt)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.level_complete_timer += dt
            if self.level_complete_timer > 0.5:
                self.advance_level()
        elif self.state == GameState.NARRATIVE_ENDING:
            self.ending_timer += dt

    def update_playing(self, dt):
        """Update gameplay systems."""
        if self.player.dead:
            # Let the death animation play, then respawn at the start
            self.death_timer += dt
            self.player.update_death(dt)
            if self.death_timer >= DEATH_RESPAWN_DELAY:
                self.restart_level()
            return

        # Get collision rects for physics
        collision_rects = self.current_level.get_all_collision_rects()

        # Update player
        self.player.update(dt, collision_rects)

        # Check all collisions
        result = self.current_level.check_collisions(self.player.rect)

        if result == "death":
            self.player.trigger_death((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.particles.emit_death_burst(self.player.rect.centerx, self.player.rect.centery)
            self.camera_shake.start(0.25, 12.0)
            self.glitch.trigger(0.35, 10.0)

        elif result == "exit":
            self.player.dead = True  # Freeze player
            self.state = GameState.LEVEL_COMPLETE
            self.level_complete_timer = 0.0
            self.camera_shake.start(0.3, 8.0)

        # Update level elements
        self.current_level.update(dt)

    def draw(self):
        """Render the complete frame."""
        # Create offscreen buffer for glitch effects
        buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Draw background grid
        self.background.draw(buffer)

        if self.state == GameState.MENU:
            self.ui.draw_menu(buffer, self.menu_selected, self.menu_timer)

        elif self.state == GameState.HOW_TO_PLAY:
            # Draw background game dimmed
            self.background.draw(buffer)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 12, 20, 180))
            buffer.blit(overlay, (0, 0))
            self.ui.draw_how_to_play(buffer)

        elif self.state in (GameState.PLAYING, GameState.LEVEL_COMPLETE):
            # Get camera offset (centered on player with bounds)
            cam_x = -self.player.rect.centerx + SCREEN_WIDTH // 2
            cam_y = -self.player.rect.centery + SCREEN_HEIGHT // 2

            # Clamp camera to level bounds (optional - allows overflow for now)
            cam_x = max(min(cam_x, 0), -(2000 - SCREEN_WIDTH))
            cam_y = max(min(cam_y, 0), -(1000 - SCREEN_HEIGHT))

            # Get shake and glitch offsets
            shake_offset = self.camera_shake.get_offset()
            glitch_offset = self.glitch.get_glitch_offset() if self.glitch.is_active() else (0, 0)

            total_offset_x = cam_x + shake_offset[0] + glitch_offset[0]
            total_offset_y = cam_y + shake_offset[1] + glitch_offset[1]

            # Draw level elements
            self.current_level.draw(buffer, (total_offset_x, total_offset_y), glitch_offset)

            # Draw player
            self.player.draw(buffer, (total_offset_x, total_offset_y), glitch_offset)

            # Draw HUD (no camera offset) - use total deaths across all levels
            rule_text = deception.get_displayed_rule_text()
            warning = deception.message_text if deception.message_timer > 0 else ""
            self.ui.draw_hud(
                buffer,
                self.current_level_idx + 1,
                get_total_levels(),
                self.total_deaths,
                rule_text,
                warning,
                deception.current_rules.get("controls_swapped", False)
            )

            # Draw particles on top
            self.particles.draw(buffer, total_offset_x, total_offset_y)

            # Apply glitch post-processing to buffer
            self.glitch.apply_to_surface(buffer)

        elif self.state == GameState.NARRATIVE_ENDING:
            self.ui.draw_narrative_ending(buffer, self.total_deaths, self.ending_timer)

        # Blit buffer to screen
        self.screen.blit(buffer, (0, 0))
        pygame.display.flip()


def main():
    """Entry point."""
    game = ChromaLie()
    game.run()


if __name__ == "__main__":
    main()