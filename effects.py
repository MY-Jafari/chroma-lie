"""
effects.py - juice: particles, glow, screen shake, flash, glitch
(chromatic aberration) and the animated background.
Everything is code-generated, no image assets.
"""
import math
import random
import pygame
from config import WIDTH, HEIGHT, BG, BG_GRID, BG_GRID_MAJOR, TILE


def scale_color(color, k):
    return (max(0, min(255, int(color[0] * k))),
            max(0, min(255, int(color[1] * k))),
            max(0, min(255, int(color[2] * k))))


def mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


# ---------------------------------------------------------------- glow
_glow_cache = {}


def glow_surface(radius, color, intensity=1.0):
    """Radial glow on black; blit with BLEND_ADD. Cached."""
    key = (radius, color, round(intensity, 2))
    surf = _glow_cache.get(key)
    if surf is None:
        surf = pygame.Surface((radius * 2, radius * 2))
        surf.fill((0, 0, 0))
        for r in range(radius, 0, -2):
            k = ((1 - r / radius) ** 2) * intensity
            pygame.draw.circle(surf, scale_color(color, k), (radius, radius), r)
        _glow_cache[key] = surf
    return surf


def blit_glow(target, pos, radius, color, intensity=1.0):
    g = glow_surface(radius, color, intensity)
    target.blit(g, (int(pos[0] - radius), int(pos[1] - radius)), special_flags=pygame.BLEND_ADD)


def blur(surface, factor=6):
    """Cheap blur: shrink then enlarge with smoothscale."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // factor), max(1, h // factor)))
    return pygame.transform.smoothscale(small, (w, h))


# ---------------------------------------------------------------- particles
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color", "gravity", "drag", "shrink")

    def __init__(self, x, y, vx, vy, life, size, color, gravity=0.0, drag=0.0, shrink=True):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.color = size, color
        self.gravity, self.drag, self.shrink = gravity, drag, shrink


class ParticleSystem:
    MAX = 1400

    def __init__(self):
        self.items = []

    def emit(self, x, y, vx, vy, life, size, color, gravity=0.0, drag=0.0, shrink=True):
        if len(self.items) < self.MAX:
            self.items.append(Particle(x, y, vx, vy, life, size, color, gravity, drag, shrink))

    def burst(self, x, y, color, count, speed=(80, 320), life=(0.4, 0.9), size=(3, 7), gravity=600.0):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(*speed)
            self.emit(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(*life),
                      random.uniform(*size), color, gravity, 1.5)

    def clear(self):
        self.items.clear()

    def update(self, dt):
        alive = []
        for p in self.items:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            if p.drag:
                f = max(0.0, 1 - p.drag * dt)
                p.vx *= f
                p.vy *= f
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.items = alive

    def draw(self, surf, offset=(0, 0)):
        ox, oy = offset
        for p in self.items:
            k = p.life / p.max_life
            s = p.size * (k if p.shrink else 1.0)
            if s < 0.6:
                continue
            rect = (int(p.x - s / 2 + ox), int(p.y - s / 2 + oy), max(1, int(s)), max(1, int(s)))
            surf.fill(scale_color(p.color, 0.25 + 0.75 * k), rect, special_flags=pygame.BLEND_ADD)


# ---------------------------------------------------------------- camera shake / flash / glitch
class Shake:
    def __init__(self):
        self.trauma = 0.0

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - dt * 1.8)

    def offset(self):
        if self.trauma <= 0:
            return 0, 0
        m = 14 * self.trauma * self.trauma
        return int(random.uniform(-m, m)), int(random.uniform(-m, m))


class Flash:
    def __init__(self):
        self.alpha = 0.0
        self.color = (255, 59, 92)
        self.overlay = pygame.Surface((WIDTH, HEIGHT))

    def trigger(self, color, alpha=150):
        self.color, self.alpha = color, alpha

    def update(self, dt):
        self.alpha = max(0.0, self.alpha - dt * 520)

    def draw(self, surf):
        if self.alpha > 1:
            self.overlay.fill(self.color)
            self.overlay.set_alpha(int(self.alpha))
            surf.blit(self.overlay, (0, 0))


class Glitch:
    """Chromatic aberration (split red / cyan layers) + displaced horizontal slices."""

    def __init__(self):
        self.timer = 0.0
        self.duration = 0.4
        self.strength = 1.0

    def trigger(self, duration=0.4, strength=1.0):
        self.timer = self.duration = duration
        self.strength = strength

    def update(self, dt):
        self.timer = max(0.0, self.timer - dt)

    @property
    def active(self):
        return self.timer > 0

    def apply(self, frame):
        if self.timer <= 0:
            return frame
        k = self.timer / self.duration
        shift = int(2 + 9 * k * self.strength)
        red = frame.copy()
        red.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
        cyan = frame.copy()
        cyan.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
        out = pygame.Surface(frame.get_size())
        out.fill((0, 0, 0))
        out.blit(red, (shift, 0), special_flags=pygame.BLEND_ADD)
        out.blit(cyan, (-shift, 0), special_flags=pygame.BLEND_ADD)
        w, h = out.get_size()
        for _ in range(int(2 + 6 * k * self.strength)):
            y = random.randrange(0, h - 4)
            sh = min(random.randint(3, 22), h - y)
            strip = out.subsurface((0, y, w, sh)).copy()
            out.blit(strip, (random.randint(-28, 28), y))
        return out


# ---------------------------------------------------------------- background
class Background:
    """Dark navy lab: slowly drifting grid, faint motes and a vignette."""

    def __init__(self):
        size = (WIDTH + TILE * 4, HEIGHT + TILE * 4)
        self.grid = pygame.Surface(size)
        self.grid.fill(BG)
        for x in range(0, size[0], TILE):
            pygame.draw.line(self.grid, BG_GRID_MAJOR if x % (TILE * 4) == 0 else BG_GRID, (x, 0), (x, size[1]))
        for y in range(0, size[1], TILE):
            pygame.draw.line(self.grid, BG_GRID_MAJOR if y % (TILE * 4) == 0 else BG_GRID, (0, y), (size[0], y))
        self.motes = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(4, 16),
                       random.uniform(1, 2.5), random.uniform(0, math.tau)] for _ in range(46)]
        self.vignette = self._make_vignette()
        self.t = 0.0

    @staticmethod
    def _make_vignette():
        sw, sh = 48, 32
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                dx = (x - sw / 2 + 0.5) / (sw / 2)
                dy = (y - sh / 2 + 0.5) / (sh / 2)
                d = min(1.0, math.sqrt(dx * dx + dy * dy) / 1.25)
                small.set_at((x, y), (0, 0, 0, int(200 * d ** 2.2)))
        return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))

    def update(self, dt):
        self.t += dt
        for m in self.motes:
            m[1] -= m[2] * dt
            m[0] += math.sin(self.t * 0.6 + m[4]) * 4 * dt
            if m[1] < -4:
                m[1] = HEIGHT + 4
                m[0] = random.uniform(0, WIDTH)

    def draw(self, surf):
        off = (self.t * 7) % (TILE * 4)
        surf.blit(self.grid, (-off, -off))
        for x, y, _, s, ph in self.motes:
            k = 0.35 + 0.25 * math.sin(self.t * 1.3 + ph)
            surf.fill(scale_color((90, 110, 170), k), (int(x), int(y), int(s), int(s)),
                      special_flags=pygame.BLEND_ADD)

    def draw_vignette(self, surf):
        surf.blit(self.vignette, (0, 0))


class Effects:
    """Bundle so the game owns one object for all juice."""

    def __init__(self):
        self.particles = ParticleSystem()
        self.shake = Shake()
        self.flash = Flash()
        self.glitch = Glitch()

    def update(self, dt):
        self.particles.update(dt)
        self.shake.update(dt)
        self.flash.update(dt)
        self.glitch.update(dt)
