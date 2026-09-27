"""Player class for Chroma Lie."""

import pygame
from config import *
from deception import deception

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dead = False
        self.death_timer = 0.0
        self.death_particles = []

        # Sub-pixel accumulators for ultra-smooth floating movement
        self._sub_x = 0.0
        self._sub_y = 0.0

        # Movement state flags (supports both Arrow keys and WASD)
        self.move_left = False
        self.move_right = False
        self.jump_buffered = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

    def handle_event(self, event):
        """Handle keyboard events for movement with multi-key support."""
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.move_left = False
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.move_right = False
            return

        if self.dead:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.move_left = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.move_right = True
            elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.request_jump()
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.dash()

    def request_jump(self):
        """Request a jump, utilizing coyote time and jump buffer."""
        if self.on_ground or self.coyote_timer > 0:
            self.execute_jump()
        else:
            self.jump_buffered = True
            self.jump_buffer_timer = JUMP_BUFFER_TIME

    def execute_jump(self):
        """Perform the actual jump velocity application."""
        self.vel_y = PLAYER_JUMP_FORCE
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffered = False

    def dash(self):
        """Perform a quick dash in the current facing direction."""
        if self.dash_cooldown_timer <= 0 and not self.dead:
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            dash_dir = 1 if self.facing_right else -1
            self.vel_x = dash_dir * DASH_SPEED

    def update(self, dt, level_tiles):
        """Update player position and physics with coyote time and buffer."""
        if self.dead:
            self.update_death(dt)
            return

        # Update jump buffer timer
        if self.jump_buffered:
            self.jump_buffer_timer -= dt
            if self.jump_buffer_timer <= 0:
                self.jump_buffered = False

        # Update coyote timer
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        else:
            if self.coyote_timer > 0:
                self.coyote_timer -= dt

        # Apply control swap from deception
        controls_swapped = deception.current_rules.get("controls_swapped", False)
        move_left = self.move_right if controls_swapped else self.move_left
        move_right = self.move_left if controls_swapped else self.move_right

        # Horizontal movement
        target_vel_x = 0.0
        if move_left:
            target_vel_x = -PLAYER_SPEED
            self.facing_right = False
        if move_right:
            target_vel_x = PLAYER_SPEED
            self.facing_right = True

        # Smooth acceleration/deceleration
        if self.dash_timer > 0:
            self.dash_timer -= dt
        else:
            if abs(target_vel_x) > 0.1:
                self.vel_x = target_vel_x
            else:
                self.vel_x *= FRICTION
                if abs(self.vel_x) < 10:
                    self.vel_x = 0

        # Apply gravity
        self.vel_y += GRAVITY * dt
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # Update dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        # Move horizontally and vertically
        self.move_horizontally(level_tiles, dt)
        self.move_vertically(level_tiles, dt)

        # Check if jump buffer can now execute upon landing
        if self.jump_buffered and (self.on_ground or self.coyote_timer > 0):
            self.execute_jump()

        # Update deception with player state
        deception.set_player_state(
            moving=(abs(self.vel_x) > 10),
            jumping=not self.on_ground
        )

    def move_horizontally(self, rects, dt):
        """Sub-pixel precise horizontal movement."""
        self._sub_x += self.vel_x * dt
        dx = int(self._sub_x)
        if dx == 0:
            return
        self._sub_x -= dx

        self.rect.x += dx
        for item in rects:
            tile_rect = item.rect if hasattr(item, 'rect') else item
            if not self.rect.colliderect(tile_rect):
                continue
            if dx > 0:
                self.rect.right = tile_rect.left
            elif dx < 0:
                self.rect.left = tile_rect.right
            self.vel_x = 0
            self._sub_x = 0.0
            break

    def move_vertically(self, rects, dt):
        """Sub-pixel precise vertical movement with ground probe."""
        self._sub_y += self.vel_y * dt
        dy = int(self._sub_y)
        if dy == 0:
            return
        self._sub_y -= dy

        self.rect.y += dy

        landed = False
        for item in rects:
            tile_rect = item.rect if hasattr(item, 'rect') else item
            if not self.rect.colliderect(tile_rect):
                continue
            if dy > 0:
                self.rect.bottom = tile_rect.top
                landed = True
            elif dy < 0:
                self.rect.top = tile_rect.bottom
                self.vel_y = 0
            self._sub_y = 0.0

        self.on_ground = False
        if landed:
            probe = self.rect.move(0, GROUND_PROBE)
            for item in rects:
                tile_rect = item.rect if hasattr(item, 'rect') else item
                if probe.colliderect(tile_rect):
                    self.on_ground = True
                    break

    def update_death(self, dt):
        """Update death animation and particles."""
        self.death_timer += dt
        for particle in self.death_particles[:]:
            particle['life'] -= dt
            particle['x'] += particle['vel_x'] * dt
            particle['y'] += particle['vel_y'] * dt
            particle['vel_y'] += GRAVITY * 0.5 * dt
            if particle['life'] <= 0:
                self.death_particles.remove(particle)

    def trigger_death(self, screen_center):
        """Trigger death animation at current position."""
        self.dead = True
        self.death_timer = 0.0
        self.death_particles = []

        import random
        for _ in range(DEATH_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(100, 300)
            self.death_particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'vel_x': speed * __import__('math').cos(angle),
                'vel_y': speed * __import__('math').sin(angle),
                'life': random.uniform(0.3, DEATH_PARTICLE_LIFETIME),
                'color': random.choice(PARTICLE_COLORS),
                'size': random.randint(3, 8)
            })

    def reset(self, x, y):
        """Reset player to starting position."""
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0.0
        self.vel_y = 0.0
        self._sub_x = 0.0
        self._sub_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dead = False
        self.death_timer = 0.0
        self.death_particles = []
        self.move_left = False
        self.move_right = False
        self.jump_buffered = False

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the player with glow effect."""
        if self.dead:
            for particle in self.death_particles:
                alpha = int(255 * (particle['life'] / DEATH_PARTICLE_LIFETIME))
                size = max(1, int(particle['size'] * (particle['life'] / DEATH_PARTICLE_LIFETIME)))
                x = int(particle['x'] + camera_offset[0] + glitch_offset[0])
                y = int(particle['y'] + camera_offset[1] + glitch_offset[1])
                pygame.draw.circle(screen, particle['color'], (x, y), size)
            return

        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]

        glow_surf = pygame.Surface((PLAYER_SIZE + 16, PLAYER_SIZE + 16), pygame.SRCALPHA)
        for i in range(4):
            alpha = 30 - i * 7
            size_inc = i * 4
            pygame.draw.rect(glow_surf, (*PLAYER_COLOR, alpha),
                           (8 - size_inc//2, 8 - size_inc//2, PLAYER_SIZE + size_inc, PLAYER_SIZE + size_inc),
                           border_radius=6)
        screen.blit(glow_surf, (draw_x - 8, draw_y - 8))

        player_rect = pygame.Rect(draw_x, draw_y, PLAYER_SIZE, PLAYER_SIZE)
        pygame.draw.rect(screen, PLAYER_COLOR, player_rect, border_radius=4)

        highlight_rect = pygame.Rect(draw_x + 4, draw_y + 4, PLAYER_SIZE - 8, PLAYER_SIZE - 8)
        highlight_color = (min(255, PLAYER_COLOR[0] + 30), min(255, PLAYER_COLOR[1] + 30), min(255, PLAYER_COLOR[2] + 30))
        pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=2)

        if self.facing_right:
            points = [(draw_x + PLAYER_SIZE - 6, draw_y + PLAYER_SIZE//2),
                      (draw_x + PLAYER_SIZE - 12, draw_y + PLAYER_SIZE//2 - 4),
                      (draw_x + PLAYER_SIZE - 12, draw_y + PLAYER_SIZE//2 + 4)]
        else:
            points = [(draw_x + 6, draw_y + PLAYER_SIZE//2),
                      (draw_x + 12, draw_y + PLAYER_SIZE//2 - 4),
                      (draw_x + 12, draw_y + PLAYER_SIZE//2 + 4)]
        pygame.draw.polygon(screen, (255, 255, 255), points)