"""UI system for Chroma Lie:
HUD, rule banners, text glow effects, menus, victory/narrative screens.
"""

import math
import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TEXT_COLOR,
    RED_DANGER,
    BLUE_SAFE,
    EXIT_GATE_COLOR,
)


class UIManager:
    """Handles rendering of text, HUD, menus, and narrative screens."""

    def __init__(self):
        self.fonts = {}
        self._init_fonts()
        self.hud_timer = 0.0

    def _init_fonts(self):
        """Initialize and cache modern fonts."""
        pygame.font.init()
        # Prefer monospace or clean sans fonts available on the system
        preferred_fonts = ["consolas", "couriernew", "dejavusansmono", "lucidaconsole", "arial"]
        chosen_font = None
        for fn in preferred_fonts:
            matched = pygame.font.match_font(fn)
            if matched:
                chosen_font = matched
                break

        try:
            self.fonts["title"] = pygame.font.Font(chosen_font, 64) if chosen_font else pygame.font.SysFont("consolas", 64, bold=True)
            self.fonts["subtitle"] = pygame.font.Font(chosen_font, 22) if chosen_font else pygame.font.SysFont("consolas", 22)
            self.fonts["large"] = pygame.font.Font(chosen_font, 36) if chosen_font else pygame.font.SysFont("consolas", 36, bold=True)
            self.fonts["medium"] = pygame.font.Font(chosen_font, 22) if chosen_font else pygame.font.SysFont("consolas", 22, bold=True)
            self.fonts["small"] = pygame.font.Font(chosen_font, 16) if chosen_font else pygame.font.SysFont("consolas", 16)
        except Exception:
            self.fonts["title"] = pygame.font.Font(None, 64)
            self.fonts["subtitle"] = pygame.font.Font(None, 24)
            self.fonts["large"] = pygame.font.Font(None, 38)
            self.fonts["medium"] = pygame.font.Font(None, 24)
            self.fonts["small"] = pygame.font.Font(None, 18)

    def render_glow_text(self, surface, text, font, pos, color, glow_color, center=False, glow_radius=4):
        """Render text with an outer neon glow."""
        base_surf = font.render(text, True, color)
        w, h = base_surf.get_size()

        glow_surf = pygame.Surface((w + glow_radius * 4, h + glow_radius * 4), pygame.SRCALPHA)
        # Multi-layer glow
        for r in range(glow_radius, 0, -1):
            alpha = int(40 / r)
            tint = (*glow_color[:3], alpha)
            rendered_glow = font.render(text, True, tint)
            glow_surf.blit(rendered_glow, (glow_radius * 2 - r, glow_radius * 2))
            glow_surf.blit(rendered_glow, (glow_radius * 2 + r, glow_radius * 2))
            glow_surf.blit(rendered_glow, (glow_radius * 2, glow_radius * 2 - r))
            glow_surf.blit(rendered_glow, (glow_radius * 2, glow_radius * 2 + r))

        glow_surf.blit(base_surf, (glow_radius * 2, glow_radius * 2))

        if center:
            dest_x = pos[0] - glow_surf.get_width() // 2
            dest_y = pos[1] - glow_surf.get_height() // 2
        else:
            dest_x = pos[0] - glow_radius * 2
            dest_y = pos[1] - glow_radius * 2

        surface.blit(glow_surf, (dest_x, dest_y))
        return pygame.Rect(dest_x, dest_y, glow_surf.get_width(), glow_surf.get_height())

    def update(self, dt):
        self.hud_timer += dt

    def draw_hud(self, surface, level_id, total_levels, deaths, rule_text, warning_msg, controls_swapped):
        """Draw top banner with current instructions and stats."""
        # Top banner background bar
        bar_height = 48
        bar_surf = pygame.Surface((SCREEN_WIDTH, bar_height), pygame.SRCALPHA)
        bar_surf.fill((10, 12, 18, 220))
        pygame.draw.line(bar_surf, (50, 60, 85, 180), (0, bar_height - 1), (SCREEN_WIDTH, bar_height - 1), 1)
        surface.blit(bar_surf, (0, 0))

        # Main Rule Text in center with neon styling
        pulse = 0.5 + 0.5 * math.sin(self.hud_timer * 4.0)
        glow_col = (int(100 + 50 * pulse), int(120 + 50 * pulse), 200)

        # Parse rule text to highlight RED and BLUE dynamically
        # Standard: RED = DANGER    BLUE = SAFE
        self.render_glow_text(
            surface,
            rule_text,
            self.fonts["medium"],
            (SCREEN_WIDTH // 2, bar_height // 2),
            TEXT_COLOR,
            glow_col,
            center=True,
            glow_radius=3,
        )

        # Level Indicator on Left
        lvl_str = f"TEST: {level_id:02d} / {total_levels:02d}"
        self.render_glow_text(
            surface,
            lvl_str,
            self.fonts["small"],
            (24, bar_height // 2),
            (160, 200, 255),
            (30, 80, 160),
            center=False,
            glow_radius=2,
        )

        # Deaths Counter on Right
        deaths_str = f"DEATHS: {deaths}"
        right_surf = self.fonts["small"].render(deaths_str, True, (255, 120, 140))
        rx = SCREEN_WIDTH - right_surf.get_width() - 24
        self.render_glow_text(
            surface,
            deaths_str,
            self.fonts["small"],
            (rx, bar_height // 2),
            (255, 120, 140),
            (150, 30, 50),
            center=False,
            glow_radius=2,
        )

        # Vague lie warning banner if triggered
        if warning_msg:
            warn_pulse = abs(math.sin(self.hud_timer * 8.0))
            w_color = (255, int(220 * warn_pulse), int(60 * warn_pulse))
            w_box = pygame.Surface((SCREEN_WIDTH, 30), pygame.SRCALPHA)
            w_box.fill((30, 10, 15, 180))
            surface.blit(w_box, (0, bar_height))
            self.render_glow_text(
                surface,
                f">> {warning_msg} <<",
                self.fonts["small"],
                (SCREEN_WIDTH // 2, bar_height + 15),
                w_color,
                (200, 50, 50),
                center=True,
                glow_radius=2,
            )

        # Controls swapped subtle icon if active
        if controls_swapped:
            warn_text = "[CONTROLS INVERTED]"
            c_surf = self.fonts["small"].render(warn_text, True, (255, 180, 50))
            surface.blit(c_surf, (24, bar_height + 8))

    def draw_menu(self, surface, selected_idx, timer):
        """Render the cybernetic main menu."""
        # Main Title with chromatic glitch shadow
        title = "CHROMA LIE"
        cx = SCREEN_WIDTH // 2
        cy = 160

        # Background chromatic shadow
        self.render_glow_text(surface, title, self.fonts["title"], (cx + 3, cy), RED_DANGER, (150, 0, 50), center=True)
        self.render_glow_text(surface, title, self.fonts["title"], (cx - 3, cy), BLUE_SAFE, (0, 100, 180), center=True)
        self.render_glow_text(surface, title, self.fonts["title"], (cx, cy), (255, 255, 255), (100, 180, 255), center=True, glow_radius=6)

        # Subtitle
        sub_text = "TRUST NOTHING. OBSERVE EVERYTHING."
        self.render_glow_text(surface, sub_text, self.fonts["subtitle"], (cx, cy + 65), (180, 190, 220), (50, 60, 100), center=True)

        # Options
        options = ["BEGIN EXPERIMENT", "CONTROLS & MANUAL", "QUIT"]
        start_y = 310
        spacing = 54

        for idx, opt in enumerate(options):
            is_selected = (idx == selected_idx)
            y_pos = start_y + idx * spacing

            if is_selected:
                # Pulsing selection arrow and box
                p = 0.5 + 0.5 * math.sin(timer * 6.0)
                box_w = 340
                box_h = 42
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box_surf.fill((30, 45, 75, int(100 + 60 * p)))
                pygame.draw.rect(box_surf, (*BLUE_SAFE[:3], int(150 + 100 * p)), (0, 0, box_w, box_h), 2, border_radius=4)
                surface.blit(box_surf, (cx - box_w // 2, y_pos - box_h // 2))

                text_str = f">  {opt}  <"
                self.render_glow_text(
                    surface,
                    text_str,
                    self.fonts["medium"],
                    (cx, y_pos),
                    (255, 255, 255),
                    BLUE_SAFE,
                    center=True,
                    glow_radius=4,
                )
            else:
                self.render_glow_text(
                    surface,
                    opt,
                    self.fonts["medium"],
                    (cx, y_pos),
                    (130, 140, 170),
                    (40, 50, 80),
                    center=True,
                    glow_radius=1,
                )

        # Footer notes
        footer = "UP / DOWN: SELECT    ENTER: CONFIRM    SPACE: JUMP"
        f_surf = self.fonts["small"].render(footer, True, (80, 95, 130))
        surface.blit(f_surf, (cx - f_surf.get_width() // 2, SCREEN_HEIGHT - 40))

    def draw_how_to_play(self, surface):
        """Render controls and gameplay rules dialog."""
        # Modal overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 14, 20, 240))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        cy = 80
        self.render_glow_text(surface, "OPERATIONAL MANUAL", self.fonts["large"], (cx, cy), BLUE_SAFE, (40, 100, 200), center=True)

        lines = [
            ("CONTROLS", (100, 220, 255)),
            ("ARROW KEYS / WASD : Move left & right", TEXT_COLOR),
            ("SPACE : Jump across platforms and hazards", TEXT_COLOR),
            ("SHIFT : Quick dash through tight gaps", TEXT_COLOR),
            ("R : Quick restart level upon failure", TEXT_COLOR),
            ("ESC : Return to title menu", TEXT_COLOR),
            ("", TEXT_COLOR),
            ("CRITICAL WARNING", RED_DANGER),
            ("- Initial directive: RED = DANGER, BLUE = SAFE.", TEXT_COLOR),
            ("- As testing progresses, directives may not remain factual.", TEXT_COLOR),
            ("- Controls and color properties will be distorted without warning.", TEXT_COLOR),
            ("- Reach the green pulsating EXIT GATE to proceed.", EXIT_GATE_COLOR),
            ("", TEXT_COLOR),
            ("PRESS ENTER OR ESCAPE TO RETURN", (180, 255, 200)),
        ]

        start_y = 140
        for text, col in lines:
            if text.startswith("CONTROLS") or text.startswith("CRITICAL"):
                self.render_glow_text(surface, text, self.fonts["medium"], (cx, start_y), col, (50, 80, 120), center=True)
            elif text.startswith("PRESS"):
                self.render_glow_text(surface, text, self.fonts["medium"], (cx, start_y + 10), col, (40, 120, 80), center=True)
            else:
                self.render_glow_text(surface, text, self.fonts["small"], (cx, start_y), col, (20, 30, 50), center=True)
            start_y += 32

    def draw_narrative_ending(self, surface, total_deaths, timer):
        """Render final philosophical ending sequence."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 245))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        self.render_glow_text(
            surface,
            "EXPERIMENT ARCHIVED",
            self.fonts["large"],
            (cx, 110),
            EXIT_GATE_COLOR,
            (40, 180, 100),
            center=True,
            glow_radius=5,
        )

        lines = [
            "You followed the rules until they failed you.",
            "You trusted the signs until they lied.",
            "In the end, you survived not by obeying instructions,",
            "but by questioning every single certainty.",
            "",
            f"TOTAL SYSTEM FAILURES (DEATHS): {total_deaths}",
            "",
            "PRESS [SPACE] OR [ENTER] TO RETURN TO REALITY",
        ]

        curr_y = 190
        for idx, line in enumerate(lines):
            # Gradual reveal based on timer
            revealed_threshold = idx * 0.8
            if timer < revealed_threshold:
                continue

            if "TOTAL SYSTEM" in line:
                self.render_glow_text(surface, line, self.fonts["medium"], (cx, curr_y), RED_DANGER, (150, 40, 60), center=True)
            elif "PRESS" in line:
                pulse = 0.5 + 0.5 * math.sin(timer * 5.0)
                p_col = (int(180 + 75 * pulse), 255, int(180 + 75 * pulse))
                self.render_glow_text(surface, line, self.fonts["medium"], (cx, curr_y + 20), p_col, (40, 160, 80), center=True)
            else:
                self.render_glow_text(surface, line, self.fonts["subtitle"], (cx, curr_y), TEXT_COLOR, (40, 50, 80), center=True)

            curr_y += 38
