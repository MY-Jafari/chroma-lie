"""Visual effects module for Chroma Lie:
Camera shake, chromatic aberration glitch, scanlines, background grid, and particle systems.
"""

import math
import random
import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BG_COLOR,
    GRID_COLOR,
    RED_DANGER,
    BLUE_SAFE,
    PARTICLE_COLORS,
)


class Particle:
    """A single particle with decay and movement."""

    def __init__(self, x, y, vel_x, vel_y, color, lifetime, size=3, shrink=True, gravity=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vel_x = float(vel_x)
        self.vel_y = float(vel_y)
        self.color = color
        self.max_life = lifetime
        self.life = lifetime
        self.initial_size = size
        self.size = size
        self.shrink = shrink
        self.gravity = gravity

    def update(self, dt):
        """Update particle physics and lifetime."""
        self.life -= dt
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.vel_y += self.gravity * dt

        if self.shrink and self.max_life > 0:
            ratio = max(0.0, self.life / self.max_life)
            self.size = max(1.0, self.initial_size * ratio)

    def is_alive(self):
        return self.life > 0

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.life <= 0:
            return
        alpha = int(255 * max(0.0, min(1.0, self.life / self.max_life)))
        radius = int(self.size)
        px = int(self.x + offset_x)
        py = int(self.y + offset_y)

        part_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], alpha)
        pygame.draw.circle(part_surf, color_with_alpha, (radius + 1, radius + 1), radius)
        surface.blit(part_surf, (px - radius - 1, py - radius - 1))


class ParticleSystem:
    """Manages pools of particles for various game events."""

    def __init__(self):
        self.particles = []
        self.ambient_particles = []
        self._init_ambient()

    def _init_ambient(self):
        """Pre-populate subtle floating ambient digital particles."""
        for _ in range(40):
            x = random.uniform(0, SCREEN_WIDTH)
            y = random.uniform(0, SCREEN_HEIGHT)
            vel_x = random.uniform(-10, 10)
            vel_y = random.uniform(-20, -5)
            color = random.choice([(40, 60, 90), (60, 40, 80), (30, 80, 100)])
            life = random.uniform(3.0, 7.0)
            p = Particle(x, y, vel_x, vel_y, color, life, size=random.uniform(1.5, 3.0), shrink=False)
            self.ambient_particles.append(p)

    def emit_death_burst(self, x, y):
        """Explosion of neon shards upon player demise."""
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 360)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(PARTICLE_COLORS)
            life = random.uniform(0.4, 0.9)
            size = random.uniform(3, 7)
            self.particles.append(
                Particle(x, y, vx, vy, color, life, size=size, shrink=True, gravity=500.0)
            )

    def emit_trail(self, x, y, color):
        """Subtle glow particle trail behind the player."""
        vx = random.uniform(-15, 15)
        vy = random.uniform(-15, 15)
        life = random.uniform(0.2, 0.4)
        size = random.uniform(2, 4)
        self.particles.append(
            Particle(x, y, vx, vy, color, life, size=size, shrink=True)
        )

    def emit_gate_spark(self, x, y, width, height):
        """Pulsing portal sparks around the exit gate."""
        if random.random() < 0.4:
            px = random.uniform(x, x + width)
            py = random.uniform(y, y + height)
            vx = random.uniform(-20, 20)
            vy = random.uniform(-50, -10)
            color = random.choice([(100, 255, 180), (150, 255, 220), (50, 220, 140)])
            self.particles.append(
                Particle(px, py, vx, vy, color, lifetime=0.6, size=random.uniform(2, 4))
            )

    def update(self, dt):
        """Update all active particles."""
        # Dynamic active particles
        for p in self.particles[:]:
            p.update(dt)
            if not p.is_alive():
                self.particles.remove(p)

        # Ambient floating dust
        for p in self.ambient_particles:
            p.update(dt)
            if not p.is_alive() or p.y < -10 or p.x < -10 or p.x > SCREEN_WIDTH + 10:
                p.x = random.uniform(0, SCREEN_WIDTH)
                p.y = SCREEN_HEIGHT + 5
                p.life = random.uniform(4.0, 8.0)
                p.vel_y = random.uniform(-25, -8)

    def draw(self, surface, offset_x=0, offset_y=0):
        for p in self.ambient_particles:
            p.draw(surface, offset_x, offset_y)
        for p in self.particles:
            p.draw(surface, offset_x, offset_y)

    def clear(self):
        self.particles.clear()


class CameraShake:
    """Procedural screenshake with decay."""

    def __init__(self):
        self.duration = 0.0
        self.intensity = 0.0
        self.timer = 0.0

    def start(self, duration=0.3, intensity=8.0):
        self.duration = duration
        self.intensity = intensity
        self.timer = duration

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    def get_offset(self):
        if self.timer <= 0 or self.duration <= 0:
            return (0, 0)
        progress = self.timer / self.duration
        cur_intensity = self.intensity * progress
        ox = random.uniform(-cur_intensity, cur_intensity)
        oy = random.uniform(-cur_intensity, cur_intensity)
        return (int(ox), int(oy))


class GlitchManager:
    """Simulates CRT scanlines, chromatic aberration, and digital slices."""

    def __init__(self):
        self.glitch_time = 0.0
        self.total_duration = 0.0
        self.intensity = 6.0
        self.slice_glitches = []
        self._scanline_surface = None
        self._create_scanlines()

    def _create_scanlines(self):
        """Pre-render subtle horizontal CRT scanlines."""
        self._scanline_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(self._scanline_surface, (0, 0, 0, 30), (0, y), (SCREEN_WIDTH, y), 1)

    def trigger(self, duration=0.4, intensity=8.0):
        """Trigger an active digital glitch."""
        self.total_duration = duration
        self.glitch_time = duration
        self.intensity = intensity
        self.slice_glitches = []

        # Generate a few random slice displacements
        num_slices = random.randint(3, 7)
        for _ in range(num_slices):
            y_start = random.randint(20, SCREEN_HEIGHT - 60)
            height = random.randint(8, 30)
            shift = random.randint(-int(intensity * 2), int(intensity * 2))
            self.slice_glitches.append((y_start, height, shift))

    def update(self, dt):
        if self.glitch_time > 0:
            self.glitch_time -= dt
            # Periodically re-randomize slice shifts while active
            if random.random() < 0.2:
                for i in range(len(self.slice_glitches)):
                    y_start, height, _ = self.slice_glitches[i]
                    shift = random.randint(-int(self.intensity * 2.5), int(self.intensity * 2.5))
                    self.slice_glitches[i] = (y_start, height, shift)
        else:
            self.slice_glitches.clear()

    def is_active(self):
        return self.glitch_time > 0

    def apply_to_surface(self, target_surface):
        """Applies chromatic aberration and slice glitches directly to surface."""
        # 1. Slice horizontal displacement
        if self.is_active() and self.slice_glitches:
            temp_copy = target_surface.copy()
            for y, h, shift in self.slice_glitches:
                if y + h > SCREEN_HEIGHT:
                    continue
                slice_rect = pygame.Rect(0, y, SCREEN_WIDTH, h)
                target_surface.blit(temp_copy, (shift, y), slice_rect)

        # 2. Chromatic aberration color split
        if self.is_active() and self.total_duration > 0:
            factor = self.glitch_time / self.total_duration
            offset = int(self.intensity * factor * math.sin(self.glitch_time * 50))
            if abs(offset) > 1:
                # Tint overlay simulation
                red_tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                blue_tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                red_tint.fill((255, 0, 0, 20))
                blue_tint.fill((0, 100, 255, 20))
                target_surface.blit(red_tint, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)
                target_surface.blit(blue_tint, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)

        # 3. Always blit subtle scanlines for cyber feel
        if self._scanline_surface:
            target_surface.blit(self._scanline_surface, (0, 0))


class BackgroundGrid:
    """Renders a digital grid with subtle scrolling and pulse."""

    def __init__(self, cell_size=40):
        self.cell_size = cell_size
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.offset_x = (self.offset_x + 8.0 * dt) % self.cell_size
        self.offset_y = (self.offset_y + 4.0 * dt) % self.cell_size

    def draw(self, surface):
        surface.fill(BG_COLOR)

        # Draw grid lines
        alpha_pulse = 28 + int(10 * math.sin(self.time * 1.5))
        grid_color = (*GRID_COLOR[:3], alpha_pulse)
        grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        start_x = int(-self.cell_size + self.offset_x)
        for x in range(start_x, SCREEN_WIDTH + self.cell_size, self.cell_size):
            pygame.draw.line(grid_surf, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)

        start_y = int(-self.cell_size + self.offset_y)
        for y in range(start_y, SCREEN_HEIGHT + self.cell_size, self.cell_size):
            pygame.draw.line(grid_surf, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

        surface.blit(grid_surf, (0, 0))
