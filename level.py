"""Level system for Chroma Lie - tiles, obstacles, traps, and collision detection."""

import pygame
from config import *
from deception import deception

class Tile:
    """A colored tile that can be safe or dangerous based on current rules."""
    def __init__(self, x, y, color, tile_type="static"):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.color = color  # "red", "blue", "purple", "yellow"
        self.tile_type = tile_type  # "static", "timed"
        self.active = True
        self.timer = 0.0
        self.cycle_time = 2.0  # seconds for timed tiles
        self.warning_time = 0.5  # blink before activation

    def update(self, dt):
        """Update timed tile state."""
        if self.tile_type == "timed":
            self.timer += dt
            cycle = self.timer % (self.cycle_time * 2)
            if cycle < self.cycle_time - self.warning_time:
                self.active = True
            elif cycle < self.cycle_time:
                # Warning blink
                self.active = int(cycle * 10) % 2 == 0
            else:
                self.active = False

    def is_dangerous(self):
        """Check if this tile is currently dangerous."""
        if not self.active:
            return False
        return not deception.get_tile_safety(self.color)

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the tile with gradient and pattern."""
        if not self.active:
            return

        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]

        # Get base color
        if self.color == "red":
            base_color = RED_DANGER
        elif self.color == "blue":
            base_color = BLUE_SAFE
        elif self.color == "purple":
            base_color = PURPLE_TILE
        elif self.color == "yellow":
            base_color = YELLOW_TILE
        else:
            base_color = (200, 200, 200)

        # Draw tile with gradient
        tile_rect = pygame.Rect(draw_x, draw_y, TILE_SIZE, TILE_SIZE)
        # Main color
        pygame.draw.rect(screen, base_color, tile_rect)

        # Subtle gradient overlay (darker at bottom)
        gradient = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        for i in range(TILE_SIZE):
            alpha = int(40 * (i / TILE_SIZE))
            pygame.draw.line(gradient, (0, 0, 0, alpha), (0, i), (TILE_SIZE, i))
        screen.blit(gradient, (draw_x, draw_y))

        # Diagonal line pattern for "digital" feel
        pattern_color = (min(255, base_color[0] + 40), min(255, base_color[1] + 40), min(255, base_color[2] + 40), 60)
        pattern_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        for i in range(-TILE_SIZE, TILE_SIZE * 2, 8):
            pygame.draw.line(pattern_surf, pattern_color, (i, 0), (i + TILE_SIZE, TILE_SIZE), 1)
        screen.blit(pattern_surf, (draw_x, draw_y))

        # Border
        pygame.draw.rect(screen, (min(255, base_color[0] + 60), min(255, base_color[1] + 60), min(255, base_color[2] + 60)), tile_rect, 1)


class MovingObstacle:
    """A moving obstacle that is always deadly."""
    def __init__(self, x, y, width, height, movement_type="horizontal", range_dist=200, speed=150):
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x = x
        self.start_y = y
        self.movement_type = movement_type  # "horizontal", "vertical", "circular"
        self.range = range_dist
        self.speed = speed
        self.timer = 0.0
        self.direction = 1

    def update(self, dt):
        """Update obstacle position."""
        self.timer += dt

        if self.movement_type == "horizontal":
            self.rect.x = self.start_x + int(self.range * __import__('math').sin(self.timer * self.speed / self.range))
        elif self.movement_type == "vertical":
            self.rect.y = self.start_y + int(self.range * __import__('math').sin(self.timer * self.speed / self.range))
        elif self.movement_type == "circular":
            self.rect.x = self.start_x + int(self.range * __import__('math').cos(self.timer * self.speed / self.range))
            self.rect.y = self.start_y + int(self.range * __import__('math').sin(self.timer * self.speed / self.range))
        elif self.movement_type == "patrol":
            # Simple back-and-forth patrol
            self.rect.x += self.direction * self.speed * dt
            if self.rect.x >= self.start_x + self.range:
                self.rect.x = self.start_x + self.range
                self.direction = -1
            elif self.rect.x <= self.start_x:
                self.rect.x = self.start_x
                self.direction = 1

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the moving obstacle."""
        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]
        rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)

        # Main body
        pygame.draw.rect(screen, OBSTACLE_COLOR, rect, border_radius=4)

        # Warning stripes
        stripe_color = (255, 255, 255, 100)
        stripe_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        for i in range(0, self.rect.width + self.rect.height, 10):
            pygame.draw.line(stripe_surf, stripe_color, (i, 0), (i - self.rect.height, self.rect.height), 2)
        screen.blit(stripe_surf, (draw_x, draw_y))

        # Border
        pygame.draw.rect(screen, (255, 180, 180), rect, 2, border_radius=4)


class TimedTrap:
    """A trap that activates/deactivates on a timer."""
    def __init__(self, x, y, width, height, cycle_time=3.0, active_time=1.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.cycle_time = cycle_time
        self.active_time = active_time
        self.timer = 0.0
        self.active = True
        self.warning = False

    def update(self, dt):
        """Update trap state."""
        self.timer += dt
        cycle_pos = self.timer % self.cycle_time

        if cycle_pos < self.active_time - 0.5:
            self.active = True
            self.warning = False
        elif cycle_pos < self.active_time:
            self.active = True
            self.warning = True
        else:
            self.active = False
            self.warning = False

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the timed trap."""
        if not self.active and not self.warning:
            return  # Invisible when inactive

        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]
        rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)

        if self.warning:
            # Blinking warning state
            if int(self.timer * 8) % 2 == 0:
                color = TIMED_TRAP_ACTIVE
            else:
                color = TIMED_TRAP_INACTIVE
        else:
            color = TIMED_TRAP_ACTIVE

        pygame.draw.rect(screen, color, rect, border_radius=3)

        # Skull/cross pattern for danger
        pattern_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        center_x = self.rect.width // 2
        center_y = self.rect.height // 2
        size = min(self.rect.width, self.rect.height) // 3
        pygame.draw.line(pattern_surf, (255, 255, 255, 180),
                        (center_x - size, center_y - size), (center_x + size, center_y + size), 3)
        pygame.draw.line(pattern_surf, (255, 255, 255, 180),
                        (center_x + size, center_y - size), (center_x - size, center_y + size), 3)
        screen.blit(pattern_surf, (draw_x, draw_y))


class ExitGate:
    """The level exit gate - always safe, pulsating glow."""
    def __init__(self, x, y, width=60, height=80):
        self.rect = pygame.Rect(x, y, width, height)
        self.timer = 0.0
        self.pulse_speed = 3.0

    def update(self, dt):
        """Update pulse animation."""
        self.timer += dt

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the exit gate with pulsing glow."""
        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]
        rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)

        import math
        pulse = (math.sin(self.timer * self.pulse_speed) + 1) / 2  # 0 to 1
        glow_size = int(10 + pulse * 15)
        glow_alpha = int(50 + pulse * 100)

        # Outer glow
        glow_rect = pygame.Rect(draw_x - glow_size//2, draw_y - glow_size//2,
                               self.rect.width + glow_size, self.rect.height + glow_size)
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*EXIT_GATE_COLOR, glow_alpha), glow_surf.get_rect(), border_radius=12)
        screen.blit(glow_surf, glow_rect)

        # Main gate
        pygame.draw.rect(screen, EXIT_GATE_COLOR, rect, border_radius=6)

        # Inner pattern
        inner_rect = pygame.Rect(draw_x + 8, draw_y + 8, self.rect.width - 16, self.rect.height - 16)
        pygame.draw.rect(screen, (min(255, EXIT_GATE_COLOR[0] + 50), min(255, EXIT_GATE_COLOR[1] + 50), min(255, EXIT_GATE_COLOR[2] + 50)), inner_rect, border_radius=4)

        # Arrow indicator
        arrow_points = [
            (draw_x + self.rect.width//2, draw_y + self.rect.height - 15),
            (draw_x + self.rect.width//2 - 8, draw_y + self.rect.height - 25),
            (draw_x + self.rect.width//2 + 8, draw_y + self.rect.height - 25)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), arrow_points)


class Level:
    """Manages a complete level with all its elements."""
    def __init__(self, level_data):
        self.level_data = level_data
        self.tiles = []
        self.moving_obstacles = []
        self.timed_traps = []
        self.exit_gate = None
        self.player_start = level_data.get("player_start", (50, 500))
        self.death_count = 0
        self.completed = False

        self.load_level()

    def load_level(self):
        """Create all level objects from data."""
        # Tiles
        for tile_data in self.level_data.get("tiles", []):
            tile = Tile(tile_data["x"], tile_data["y"], tile_data["color"], tile_data.get("type", "static"))
            self.tiles.append(tile)

        # Moving obstacles
        for obs_data in self.level_data.get("moving_obstacles", []):
            obs = MovingObstacle(
                obs_data["x"], obs_data["y"],
                obs_data.get("width", 40), obs_data.get("height", 40),
                obs_data.get("movement_type", "horizontal"),
                obs_data.get("range", 200),
                obs_data.get("speed", 150)
            )
            self.moving_obstacles.append(obs)

        # Timed traps
        for trap_data in self.level_data.get("timed_traps", []):
            trap = TimedTrap(
                trap_data["x"], trap_data["y"],
                trap_data.get("width", 40), trap_data.get("height", 40),
                trap_data.get("cycle_time", 3.0),
                trap_data.get("active_time", 1.5)
            )
            self.timed_traps.append(trap)

        # Exit gate
        gate_data = self.level_data.get("exit_gate", (900, 100))
        self.exit_gate = ExitGate(gate_data[0], gate_data[1])

    def update(self, dt):
        """Update all level elements."""
        for tile in self.tiles:
            tile.update(dt)
        for obs in self.moving_obstacles:
            obs.update(dt)
        for trap in self.timed_traps:
            trap.update(dt)
        if self.exit_gate:
            self.exit_gate.update(dt)

    def check_collisions(self, player_rect):
        """Check all collisions for the player.
        Returns: "death", "exit", or "none"
        """
        # Fall off the screen / kill plane check
        if player_rect.top > SCREEN_HEIGHT + 50:
            return "death"

        # Check tiles (use an expanded rect downwards to catch standing/touching contacts)
        check_rect = player_rect.inflate(0, 4)
        for tile in self.tiles:
            if tile.active and check_rect.colliderect(tile.rect):
                if tile.is_dangerous():
                    return "death"

        # Check moving obstacles (always deadly)
        for obs in self.moving_obstacles:
            if player_rect.colliderect(obs.rect):
                return "death"

        # Check timed traps
        for trap in self.timed_traps:
            if trap.active and player_rect.colliderect(trap.rect):
                return "death"

        # Check exit gate
        if self.exit_gate and player_rect.colliderect(self.exit_gate.rect):
            return "exit"

        return "none"

    def get_all_collision_rects(self):
        """Get all solid collision rects for physics."""
        rects = []
        for tile in self.tiles:
            if tile.active:
                rects.append(tile.rect)
        for obs in self.moving_obstacles:
            rects.append(obs.rect)
        for trap in self.timed_traps:
            if trap.active:
                rects.append(trap.rect)
        return rects

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw all level elements."""
        for tile in self.tiles:
            tile.draw(screen, camera_offset, glitch_offset)
        for obs in self.moving_obstacles:
            obs.draw(screen, camera_offset, glitch_offset)
        for trap in self.timed_traps:
            trap.draw(screen, camera_offset, glitch_offset)
        if self.exit_gate:
            self.exit_gate.draw(screen, camera_offset, glitch_offset)

    def reset(self):
        """Reset level state."""
        self.death_count = 0
        self.completed = False
        self.load_level()