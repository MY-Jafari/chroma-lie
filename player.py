"""
player.py - the neon square: movement, jump, gravity and tile collision.
"""
import math
import pygame
from config import (PLAYER_SIZE, GRAVITY, MAX_FALL, MOVE_SPEED, GROUND_ACCEL, AIR_ACCEL,
                    GROUND_FRICTION, JUMP_VELOCITY, JUMP_CUT, COYOTE_TIME, JUMP_BUFFER,
                    SPRING_VELOCITY, PLAYER)
from effects import blit_glow, scale_color


def approach(value, target, step):
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


class InputState:
    """Boolean key state polled every frame (smooth movement, not just KEYDOWN)."""
    LEFT = (pygame.K_LEFT, pygame.K_a)
    RIGHT = (pygame.K_RIGHT, pygame.K_d)
    JUMP = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)

    def __init__(self):
        self.left = self.right = self.jump_held = False
        self.jump_pressed = False

    def poll(self, jump_pressed_this_frame):
        keys = pygame.key.get_pressed()
        self.left = any(keys[k] for k in self.LEFT)
        self.right = any(keys[k] for k in self.RIGHT)
        self.jump_held = any(keys[k] for k in self.JUMP)
        self.jump_pressed = jump_pressed_this_frame


class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.w = self.h = PLAYER_SIZE
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.ground_kinds = set()
        self.riding = None
        self.coyote = 0.0
        self.buffer = 0.0
        self.facing = 1
        self.squash = 0.0          # >0 squashed (landing), <0 stretched (jump)
        self.just_landed = False
        self.just_jumped = False
        self.sprung = False
        self._spring_rise = False  # spring launches ignore the jump-cut

    @property
    def rect(self):
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.w, self.h)

    # ------------------------------------------------------------ update
    def update(self, dt, inp, level, controls_swapped):
        self.just_landed = self.just_jumped = self.sprung = False
        direction = (1 if inp.right else 0) - (1 if inp.left else 0)
        if controls_swapped:
            direction = -direction
        if direction:
            self.facing = direction

        target = direction * MOVE_SPEED
        if self.on_ground:
            accel = GROUND_ACCEL if direction else GROUND_FRICTION
        else:
            accel = AIR_ACCEL
        self.vx = approach(self.vx, target, accel * dt)

        # jump buffer + coyote time = forgiving, fair jumps
        self.buffer = JUMP_BUFFER if inp.jump_pressed else max(0.0, self.buffer - dt)
        self.coyote = COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        if self.buffer > 0 and self.coyote > 0:
            self.vy = -JUMP_VELOCITY
            self.buffer = self.coyote = 0.0
            self.on_ground = False
            self.riding = None
            self.just_jumped = True
            self.squash = -0.35
        if not inp.jump_held and self.vy < -JUMP_VELOCITY * JUMP_CUT and not self._spring_rise:
            self.vy = -JUMP_VELOCITY * JUMP_CUT
        if self.vy >= 0:
            self._spring_rise = False
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)

        # ride moving platforms
        if self.riding is not None:
            self.x += self.riding.dx
            self.y += self.riding.dy

        was_ground = self.on_ground
        self.x += self.vx * dt
        self._collide(level, "x")
        self.y += self.vy * dt
        self._collide(level, "y")
        self._probe_ground(level)

        if self.on_ground and not was_ground:
            self.just_landed = True
            self.squash = 0.3
        if self.on_ground and "J" in self.ground_kinds:
            self.vy = -SPRING_VELOCITY
            self._spring_rise = True
            self.on_ground = False
            self.riding = None
            self.sprung = True
            self.squash = -0.5
        self.squash = approach(self.squash, 0.0, dt * 2.2)

    def _collide(self, level, axis):
        r = self.rect
        for solid in level.solids_near(r):
            if not r.colliderect(solid.rect):
                continue
            s = solid.rect
            if axis == "x":
                if self.vx > 0 or (self.vx == 0 and r.centerx < s.centerx):
                    self.x = s.left - self.w
                else:
                    self.x = s.right
                self.vx = 0.0
            else:
                if self.vy > 0 or (self.vy == 0 and r.centery < s.centery):
                    self.y = s.top - self.h
                else:
                    self.y = s.bottom
                self.vy = 0.0
            r = self.rect

    def _probe_ground(self, level):
        """Look 1px below the feet: stable ground detection + which tiles we stand on."""
        probe = self.rect.move(0, 1)
        self.on_ground = False
        self.ground_kinds = set()
        self.riding = None
        if self.vy < 0:
            return
        for solid in level.solids_near(probe):
            if probe.colliderect(solid.rect) and solid.rect.top >= self.rect.bottom:
                self.on_ground = True
                self.ground_kinds.add(solid.kind)
                if solid.owner is not None:
                    self.riding = solid.owner

    # ------------------------------------------------------------ draw
    def draw(self, surf, t, offset=(0, 0)):
        ox, oy = offset
        r = self.rect
        k = self.squash
        w = int(self.w * (1 + k * 0.6))
        h = int(self.h * (1 - k * 0.6))
        body = pygame.Rect(0, 0, w, h)
        body.midbottom = (r.centerx + ox, r.bottom + oy)
        blit_glow(surf, body.center, 34, PLAYER, 0.55)
        pygame.draw.rect(surf, (20, 24, 36), body, border_radius=4)
        inner = body.inflate(-8, -8)
        pulse = 0.55 + 0.15 * math.sin(t * 5)
        pygame.draw.rect(surf, scale_color(PLAYER, pulse * 0.45), inner, border_radius=2)
        pygame.draw.rect(surf, PLAYER, body, 2, border_radius=4)
        # "eye" shows which way we face
        eye = pygame.Rect(0, 0, 5, 5)
        eye.center = (body.centerx + self.facing * 5, body.centery - 2)
        pygame.draw.rect(surf, PLAYER, eye)
