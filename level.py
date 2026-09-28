"""
level.py - builds a level from levels_data, runs its moving parts and draws it.
Also home of check_collisions(), the single place that decides life or death.
"""
import math
import random
import pygame
from config import (TILE, COLS, ROWS, WIDTH, HEIGHT, RED, BLUE, PURPLE, NEUTRAL, NEUTRAL_EDGE,
                    MOTION, HAZARD, EXIT, COLOR_OF_TILE, TRAP_WARNING, MOTION_FUSE,
                    MOTION_MIN_SPEED, LATE_TRAP_FUSE, FALL_DEATH_Y)
from effects import blit_glow, scale_color, mix, blur

SOLID_KINDS = set("#RBPMLJ")


class Solid:
    __slots__ = ("rect", "kind", "owner")

    def __init__(self, rect, kind, owner=None):
        self.rect, self.kind, self.owner = rect, kind, owner


# ================================================================ moving parts
class Oscillator:
    """A hazard block that eases back and forth. Always deadly, color ignored."""

    def __init__(self, d):
        self.base = pygame.Rect(d["rect"])
        self.axis = d.get("axis", "y")
        self.distance = d.get("distance", 96)
        self.period = d.get("period", 2.0)
        self.phase = d.get("phase", 0.0)
        self.rect = self.base.copy()

    def update(self, t):
        k = 0.5 - 0.5 * math.cos(math.tau * (t / self.period + self.phase))
        off = int(self.distance * k)
        self.rect = self.base.move((off, 0) if self.axis == "x" else (0, off))

    def hits(self, rect):
        return self.rect.colliderect(rect.inflate(-4, -4))

    def draw(self, surf, t):
        # faint track = the path it will travel (fairness)
        track = self.base.union(self.base.move((self.distance, 0) if self.axis == "x" else (0, self.distance)))
        pygame.draw.rect(surf, scale_color(HAZARD, 0.16), track, 1, border_radius=3)
        r = self.rect
        blit_glow(surf, r.center, max(r.w, r.h), HAZARD, 0.35)
        pygame.draw.rect(surf, scale_color(HAZARD, 0.8), r, border_radius=3)
        clip = surf.get_clip()
        surf.set_clip(r)
        for i in range(-r.h, r.w + r.h, 12):
            pygame.draw.line(surf, (40, 26, 10), (r.x + i, r.bottom), (r.x + i + r.h, r.y), 4)
        surf.set_clip(clip)
        pygame.draw.rect(surf, (255, 222, 150), r, 2, border_radius=3)


class Orbit:
    """Spinning saw blades orbiting a center point."""

    def __init__(self, d):
        self.center = d["center"]
        self.radius = d["radius"]
        self.count = d.get("count", 2)
        self.speed = d.get("speed", 2.0)
        self.size = d.get("size", 10)
        self.balls = []

    def update(self, t):
        cx, cy = self.center
        self.angle = t * self.speed
        self.balls = [(cx + math.cos(self.angle + i * math.tau / self.count) * self.radius,
                       cy + math.sin(self.angle + i * math.tau / self.count) * self.radius)
                      for i in range(self.count)]

    def hits(self, rect):
        for bx, by in self.balls:
            nx = max(rect.left, min(bx, rect.right))
            ny = max(rect.top, min(by, rect.bottom))
            if (bx - nx) ** 2 + (by - ny) ** 2 < (self.size - 1) ** 2:
                return True
        return False

    def draw(self, surf, t):
        pygame.draw.circle(surf, scale_color(HAZARD, 0.16), self.center, self.radius, 1)
        pygame.draw.circle(surf, scale_color(HAZARD, 0.5), self.center, 4)
        for bx, by in self.balls:
            blit_glow(surf, (bx, by), self.size * 3, HAZARD, 0.5)
            pts = []
            for i in range(16):
                a = self.angle * 3 + i * math.tau / 16
                rr = self.size + (3 if i % 2 == 0 else -1)
                pts.append((bx + math.cos(a) * rr, by + math.sin(a) * rr))
            pygame.draw.polygon(surf, HAZARD, pts)
            pygame.draw.circle(surf, (60, 36, 12), (int(bx), int(by)), self.size // 2)


class TimedTrap:
    """Laser that is on for `on` seconds out of every `period`. Blinks before it fires."""

    def __init__(self, d):
        self.rect = pygame.Rect(d["rect"])
        self.period = d.get("period", 2.0)
        self.on = d.get("on", 1.0)
        self.offset = d.get("offset", 0.0)
        self.active = self.warning = False

    def update(self, t):
        ph = (t + self.offset) % self.period
        self.active = ph < self.on
        self.warning = (not self.active) and ph > self.period - TRAP_WARNING

    def hits(self, rect):
        return self.active and self.rect.colliderect(rect.inflate(-4, -2))

    def draw(self, surf, t):
        r = self.rect
        vertical = r.h >= r.w
        # emitters
        if vertical:
            caps = [pygame.Rect(r.centerx - 8, r.top - 6, 16, 8), pygame.Rect(r.centerx - 8, r.bottom - 2, 16, 8)]
        else:
            caps = [pygame.Rect(r.left - 6, r.centery - 8, 8, 16), pygame.Rect(r.right - 2, r.centery - 8, 8, 16)]
        for c in caps:
            pygame.draw.rect(surf, (70, 60, 50), c, border_radius=2)
            pygame.draw.rect(surf, HAZARD if (self.active or self.warning) else (120, 100, 70), c, 1, border_radius=2)
        if self.active:
            glow = pygame.Surface(r.inflate(24, 24).size)
            glow.fill((0, 0, 0))
            pygame.draw.rect(glow, scale_color(HAZARD, 0.55), pygame.Rect(12, 12, r.w, r.h).inflate(10, 10), border_radius=6)
            glow = blur(glow, 4)
            surf.blit(glow, r.inflate(24, 24).topleft, special_flags=pygame.BLEND_ADD)
            pygame.draw.rect(surf, HAZARD, r)
            core = r.inflate(-r.w // 2, 0) if vertical else r.inflate(0, -r.h // 2)
            pygame.draw.rect(surf, (255, 245, 220), core)
        elif self.warning:
            if int(t * 16) % 2 == 0:
                line = r.inflate(-r.w + 2, 0) if vertical else r.inflate(0, -r.h + 2)
                pygame.draw.rect(surf, HAZARD, line)
        else:
            step = 10
            if vertical:
                for y in range(r.top, r.bottom, step):
                    surf.fill(scale_color(HAZARD, 0.18), (r.centerx, y, 1, 4))
            else:
                for x in range(r.left, r.right, step):
                    surf.fill(scale_color(HAZARD, 0.18), (x, r.centery, 4, 1))


class MovingPlatform:
    """Solid neutral platform that eases between two points and carries the player."""

    def __init__(self, d):
        self.start = pygame.Vector2(d["rect"][0], d["rect"][1])
        self.end = pygame.Vector2(d["to"])
        self.rect = pygame.Rect(d["rect"])
        self.period = d.get("period", 3.0)
        self.dx = self.dy = 0
        self.solid = Solid(self.rect, "#", self)

    def update(self, t):
        k = 0.5 - 0.5 * math.cos(math.tau * t / self.period)
        pos = self.start.lerp(self.end, k)
        nx, ny = int(round(pos.x)), int(round(pos.y))
        self.dx, self.dy = nx - self.rect.x, ny - self.rect.y
        self.rect.topleft = (nx, ny)

    def draw(self, surf, t):
        a = (int(self.start.x) + self.rect.w // 2, int(self.start.y) + self.rect.h // 2)
        b = (int(self.end.x) + self.rect.w // 2, int(self.end.y) + self.rect.h // 2)
        pygame.draw.line(surf, scale_color(BLUE, 0.18), a, b, 1)
        pygame.draw.rect(surf, NEUTRAL, self.rect, border_radius=3)
        pygame.draw.rect(surf, NEUTRAL_EDGE, self.rect, 1, border_radius=3)
        for i in range(3):
            lx = self.rect.x + 14 + i * (self.rect.w - 28) // 2
            on = int(t * 4 + i) % 3 == 0
            surf.fill(EXIT if on else scale_color(EXIT, 0.35), (lx - 3, self.rect.y + 6, 6, 3))


def make_obstacle(d):
    return Orbit(d) if d["type"] == "orbit" else Oscillator(d)


# ================================================================ tile art (cached)
_tile_cache = {}


def _gradient_tile(top, bottom, pattern_color, pattern="diag"):
    s = pygame.Surface((TILE, TILE))
    for y in range(TILE):
        s.fill(mix(top, bottom, y / (TILE - 1)), (0, y, TILE, 1))
    over = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    if pattern == "diag":
        for i in range(-TILE, TILE, 8):
            pygame.draw.line(over, pattern_color + (34,), (i, TILE), (i + TILE, 0), 1)
    elif pattern == "grid":
        for i in range(4, TILE, 8):
            for j in range(4, TILE, 8):
                over.fill(pattern_color + (40,), (i, j, 1, 1))
    elif pattern == "chevron":
        for cx in (6, 18):
            pygame.draw.lines(over, pattern_color + (120,), False, [(cx, 9), (cx + 7, 16), (cx, 23)], 2)
    s.blit(over, (0, 0))
    return s


def tile_surface(kind):
    if kind in _tile_cache:
        return _tile_cache[kind]
    if kind in ("R", "B", "P"):
        c = COLOR_OF_TILE[kind]
        s = _gradient_tile(mix(c, (255, 255, 255), 0.08), scale_color(c, 0.38), (255, 255, 255))
        pygame.draw.rect(s, scale_color(c, 0.55), (TILE // 2 - 3, TILE // 2 - 3, 6, 6), 1)
    elif kind == "L":   # disguised as blue with hairline cracks (the subtle tell)
        c = BLUE
        s = _gradient_tile(mix(c, (255, 255, 255), 0.08), scale_color(c, 0.38), (255, 255, 255))
        pygame.draw.rect(s, scale_color(c, 0.55), (TILE // 2 - 3, TILE // 2 - 3, 6, 6), 1)
        crack = scale_color(c, 0.22)
        pygame.draw.lines(s, crack, False, [(4, 0), (9, 9), (7, 15), (13, 22)], 1)
        pygame.draw.lines(s, crack, False, [(26, 32), (22, 24), (25, 18)], 1)
    elif kind == "L_on":
        s = _gradient_tile((70, 40, 24), (30, 18, 14), HAZARD)
    elif kind == "M":
        s = _gradient_tile(mix(MOTION, (255, 255, 255), 0.05), scale_color(MOTION, 0.3), (255, 255, 255), "chevron")
    elif kind == "J":
        s = _gradient_tile(NEUTRAL, scale_color(NEUTRAL, 0.5), (255, 255, 255), "grid")
        pygame.draw.rect(s, EXIT, (3, 0, TILE - 6, 6), border_radius=2)
        for y in (10, 16, 22):
            pygame.draw.line(s, scale_color(EXIT, 0.7), (8, y), (TILE - 8, y + 3), 2)
    else:               # neutral lab block
        s = _gradient_tile(mix(NEUTRAL, (255, 255, 255), 0.06), scale_color(NEUTRAL, 0.55), (200, 210, 255), "grid")
    _tile_cache[kind] = s
    return s


def edge_color(kind):
    if kind in COLOR_OF_TILE:
        return mix(COLOR_OF_TILE[kind], (255, 255, 255), 0.35)
    if kind == "L":
        return mix(BLUE, (255, 255, 255), 0.35)
    if kind == "M":
        return mix(MOTION, (255, 255, 255), 0.3)
    return NEUTRAL_EDGE


# ================================================================ level
class Level:
    def __init__(self, data):
        self.data = data
        self.id = data["id"]
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.solids = {}
        self.by_kind = {}
        rows = data["tiles"]
        for r in range(ROWS):
            line = rows[r] if r < len(rows) else ""
            line = (line + "." * COLS)[:COLS]
            for c, ch in enumerate(line):
                if ch in ".SE ":
                    continue
                rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                self.grid[r][c] = ch
                self.by_kind.setdefault(ch, []).append(rect)
                if ch in SOLID_KINDS:
                    self.solids[(c, r)] = Solid(rect, ch)
        sc, sr = data["player_start"]
        self.spawn = (sc * TILE + (TILE - 24) // 2, (sr + 1) * TILE - 24)
        ec, er = data["exit_gate"]
        self.exit_rect = pygame.Rect(ec * TILE + 2, (er + 1) * TILE - 46, TILE - 4, 46)
        self.spikes = [pygame.Rect(r.x + 4, r.y + 16, r.w - 8, 16) for r in self.by_kind.get("^", [])]

        self.obstacles = [make_obstacle(o) for o in data.get("moving_obstacles", [])]
        self.traps = [TimedTrap(t) for t in data.get("timed_traps", [])]
        self.platforms = [MovingPlatform(p) for p in data.get("moving_platforms", [])]

        self.time = 0.0
        self.late_timer = -1.0      # <0 = untouched, counting up after first touch
        self.late_active = False
        self.motion_fuse = 0.0
        self.motion_touch = []      # motion tiles under the player this frame
        self._static = None
        self._glow = None
        self.update_parts(0.0)

    # ------------------------------------------------------------ queries
    def solids_near(self, rect):
        c0, c1 = max(0, rect.left // TILE - 1), min(COLS - 1, rect.right // TILE + 1)
        r0, r1 = max(0, rect.top // TILE - 1), min(ROWS - 1, rect.bottom // TILE + 1)
        out = [self.solids[(c, r)] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if (c, r) in self.solids]
        out.extend(p.solid for p in self.platforms)
        return out

    def touching(self, rect):
        """Tiles within 1px of the player (standing on, bumping into, or brushing)."""
        probe = rect.inflate(2, 2)
        c0, c1 = max(0, probe.left // TILE), min(COLS - 1, (probe.right - 1) // TILE)
        r0, r1 = max(0, probe.top // TILE), min(ROWS - 1, (probe.bottom - 1) // TILE)
        out = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                k = self.grid[r][c]
                if k is not None:
                    tr = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                    if probe.colliderect(tr):
                        # ignore pure corner contact so brushing a diagonal edge is fair
                        overlap = probe.clip(tr)
                        if overlap.w >= 2 or overlap.h >= 2:
                            out.append((k, tr))
        return out

    # ------------------------------------------------------------ update
    def update_parts(self, dt):
        self.time += dt
        for o in self.obstacles:
            o.update(self.time)
        for tr in self.traps:
            tr.update(self.time)
        for p in self.platforms:
            p.update(self.time)

    def update_tiles(self, dt, player):
        """Stateful tiles: late traps (fuse after first touch) and motion tiles."""
        touched = self.touching(player.rect)
        if self.late_timer < 0 and any(k == "L" for k, _ in touched):
            self.late_timer = 0.0
        if self.late_timer >= 0 and not self.late_active:
            self.late_timer += dt
            if self.late_timer >= LATE_TRAP_FUSE:
                self.late_active = True

        self.motion_touch = [tr for k, tr in touched if k == "M"] if player.on_ground and "M" in player.ground_kinds else []
        if self.motion_touch and abs(player.vx) < MOTION_MIN_SPEED:
            self.motion_fuse += dt
        else:
            self.motion_fuse = max(0.0, self.motion_fuse - dt * 3)
        if not self.motion_touch:
            self.motion_fuse = 0.0

    # ------------------------------------------------------------ drawing
    def _build_static(self):
        self._static = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        glow = pygame.Surface((WIDTH, HEIGHT))
        glow.fill((0, 0, 0))
        for r in range(ROWS):
            for c in range(COLS):
                k = self.grid[r][c]
                if k not in ("#", "R", "B", "P", "M", "J"):
                    continue
                x, y = c * TILE, r * TILE
                self._static.blit(tile_surface(k), (x, y))
                e = edge_color(k)

                def empty(cc, rr):
                    return not (0 <= cc < COLS and 0 <= rr < ROWS) or self.grid[rr][cc] in (None, "^")
                if empty(c, r - 1):
                    pygame.draw.line(self._static, e, (x, y), (x + TILE - 1, y), 2)
                if empty(c - 1, r):
                    pygame.draw.line(self._static, scale_color(e, 0.7), (x, y), (x, y + TILE - 1))
                if empty(c + 1, r):
                    pygame.draw.line(self._static, scale_color(e, 0.7), (x + TILE - 1, y), (x + TILE - 1, y + TILE - 1))
                if empty(c, r + 1):
                    pygame.draw.line(self._static, scale_color(e, 0.45), (x, y + TILE - 1), (x + TILE - 1, y + TILE - 1))
                if k in COLOR_OF_TILE or k == "M":
                    col = COLOR_OF_TILE.get(k, MOTION)
                    glow.fill(scale_color(col, 0.55), (x - 2, y - 2, TILE + 4, TILE + 4))
        self._glow = blur(glow, 10)

    def draw(self, surf, deception, t):
        if self._static is None:
            self._build_static()
        surf.blit(self._glow, (0, 0), special_flags=pygame.BLEND_ADD)
        surf.blit(self._static, (0, 0))

        # motion tiles heat up while you stand still
        if self.motion_fuse > 0:
            k = min(1.0, self.motion_fuse / MOTION_FUSE)
            for tr in self.motion_touch:
                surf.fill(scale_color(RED, 0.8 * k), tr, special_flags=pygame.BLEND_ADD)

        # late-trap tiles
        for tr in self.by_kind.get("L", []):
            if self.late_active:
                surf.blit(tile_surface("L_on"), tr.topleft)
                for i in range(4):
                    x0 = tr.x + i * 8
                    pygame.draw.polygon(surf, HAZARD, [(x0, tr.y + 2), (x0 + 4, tr.y - 8), (x0 + 8, tr.y + 2)])
            else:
                jitter = (random.randint(-1, 1), 0) if self.late_timer >= 0 else (0, 0)
                surf.blit(tile_surface("L"), (tr.x + jitter[0], tr.y))
                pygame.draw.line(surf, edge_color("L"), (tr.x, tr.y), (tr.right - 1, tr.y), 2)
                if random.random() < 0.004:      # a rare flicker: something is off here
                    surf.fill((0, 0, 0), tr.inflate(-6, -6))

        for sp in self.by_kind.get("^", []):
            for i in range(4):
                x0 = sp.x + i * 8
                pygame.draw.polygon(surf, HAZARD, [(x0, sp.bottom), (x0 + 4, sp.bottom - 14), (x0 + 8, sp.bottom)])

        for p in self.platforms:
            p.draw(surf, t)
        for tr in self.traps:
            tr.draw(surf, t)
        for o in self.obstacles:
            o.draw(surf, t)
        self.draw_exit(surf, t)

    def draw_exit(self, surf, t):
        r = self.exit_rect
        pulse = 0.5 + 0.5 * math.sin(t * 3.2)
        blit_glow(surf, r.center, 46 + int(6 * pulse), EXIT, 0.45 + 0.25 * pulse)
        pygame.draw.rect(surf, (16, 40, 36), r, border_radius=6)
        for i in range(5):                       # rising scanlines
            y = r.bottom - ((t * 30 + i * 10) % r.h)
            surf.fill(scale_color(EXIT, 0.35 + 0.3 * pulse), (r.x + 4, int(y), r.w - 8, 2), special_flags=pygame.BLEND_ADD)
        pygame.draw.rect(surf, mix(EXIT, (255, 255, 255), 0.3 * pulse), r, 2, border_radius=6)


# ================================================================ the judge
def check_collisions(player_rect, level, deception):
    """Returns (result, reason). result is one of 'exit', 'danger', 'safe', 'none'."""
    if player_rect.colliderect(level.exit_rect.inflate(-6, -6)):
        return "exit", "gate"
    if player_rect.top > FALL_DEATH_Y:
        return "danger", "fall"
    for o in level.obstacles:
        if o.hits(player_rect):
            return "danger", "obstacle"
    for tr in level.traps:
        if tr.hits(player_rect):
            return "danger", "trap"
    for sp in level.spikes:
        if sp.colliderect(player_rect):
            return "danger", "spikes"
    if level.motion_fuse >= MOTION_FUSE:
        return "danger", "motion"
    touched = level.touching(player_rect)
    safe = False
    for kind, _ in touched:
        if kind == "L" and level.late_active:
            return "danger", "late"
        if kind in COLOR_OF_TILE:
            if deception.is_lethal(kind):
                return "danger", "color"
            safe = True
    return ("safe" if safe else "none"), None
