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

        # For smooth movement
        self.move_left = False
        self.move_right = False

    def handle_event(self, event):
        """Handle keyboard events for movement."""
        if self.dead:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.move_left = True
            elif event.key == pygame.K_RIGHT:
                self.move_right = True
            elif event.key == pygame.K_SPACE:
                self.jump()
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                self.dash()

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.move_left = False
            elif event.key == pygame.K_RIGHT:
                self.move_right = False

    def jump(self):
        """Make the player jump if on ground."""
        if self.on_ground and not self.dead:
            self.vel_y = PLAYER_JUMP_FORCE
            self.on_ground = False

    def dash(self):
        """Perform a quick dash in the current facing direction."""
        if self.dash_cooldown_timer <= 0 and not self.dead:
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            dash_dir = 1 if self.facing_right else -1
            self.vel_x = dash_dir * DASH_SPEED

    def update(self, dt, level_tiles):
        """Update player position and physics."""
        if self.dead:
            self.update_death(dt)
            return

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
            # Normal movement with friction
            if abs(target_vel_x) > 0.1:
                self.vel_x = target_vel_x
            else:
                self.vel_x *= FRICTION
                if abs(self.vel_x) < 10:
                    self.vel_x = 0

        # Apply gravity
        self.vel_y += GRAVITY * dt

        # Update dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        # Move horizontally and check collisions
        self.rect.x += int(self.vel_x * dt)
        self.check_horizontal_collisions(level_tiles)

        # Move vertically and check collisions
        self.rect.y += int(self.vel_y * dt)
        self.on_ground = False
        self.check_vertical_collisions(level_tiles)

        # Update deception with player state
        deception.set_player_state(
            moving=(abs(self.vel_x) > 10),
            jumping=not self.on_ground
        )

    def check_horizontal_collisions(self, tiles):
        """Check and resolve horizontal collisions with tiles."""
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = tile.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = tile.rect.right
                self.vel_x = 0

    def check_vertical_collisions(self, tiles):
        """Check and resolve vertical collisions with tiles."""
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel_y > 0:  # Falling down
                    self.rect.bottom = tile.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping up
                    self.rect.top = tile.rect.bottom
                    self.vel_y = 0

    def update_death(self, dt):
        """Update death animation and particles."""
        self.death_timer += dt
        # Update particles
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
        self.on_ground = False
        self.facing_right = True
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dead = False
        self.death_timer = 0.0
        self.death_particles = []
        self.move_left = False
        self.move_right = False

    def draw(self, screen, camera_offset=(0, 0), glitch_offset=(0, 0)):
        """Draw the player with glow effect."""
        if self.dead:
            # Draw death particles
            for particle in self.death_particles:
                alpha = int(255 * (particle['life'] / DEATH_PARTICLE_LIFETIME))
                size = max(1, int(particle['size'] * (particle['life'] / DEATH_PARTICLE_LIFETIME)))
                x = int(particle['x'] + camera_offset[0] + glitch_offset[0])
                y = int(particle['y'] + camera_offset[1] + glitch_offset[1])
                pygame.draw.circle(screen, particle['color'], (x, y), size)
            return

        # Apply camera and glitch offsets
        draw_x = self.rect.x + camera_offset[0] + glitch_offset[0]
        draw_y = self.rect.y + camera_offset[1] + glitch_offset[1]

        # Draw glow effect (multiple rectangles with decreasing alpha)
        glow_surf = pygame.Surface((PLAYER_SIZE + 16, PLAYER_SIZE + 16), pygame.SRCALPHA)
        for i in range(4):
            alpha = 30 - i * 7
            size_inc = i * 4
            pygame.draw.rect(glow_surf, (*PLAYER_COLOR, alpha),
                           (8 - size_inc//2, 8 - size_inc//2, PLAYER_SIZE + size_inc, PLAYER_SIZE + size_inc),
                           border_radius=6)
        screen.blit(glow_surf, (draw_x - 8, draw_y - 8))

        # Draw main player rectangle with gradient-like effect
        player_rect = pygame.Rect(draw_x, draw_y, PLAYER_SIZE, PLAYER_SIZE)
        pygame.draw.rect(screen, PLAYER_COLOR, player_rect, border_radius=4)

        # Inner highlight
        highlight_rect = pygame.Rect(draw_x + 4, draw_y + 4, PLAYER_SIZE - 8, PLAYER_SIZE - 8)
        highlight_color = (min(255, PLAYER_COLOR[0] + 30), min(255, PLAYER_COLOR[1] + 30), min(255, PLAYER_COLOR[2] + 30))
        pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=2)

        # Direction indicator (small triangle)
        if self.facing_right:
            points = [(draw_x + PLAYER_SIZE - 6, draw_y + PLAYER_SIZE//2),
                      (draw_x + PLAYER_SIZE - 12, draw_y + PLAYER_SIZE//2 - 4),
                      (draw_x + PLAYER_SIZE - 12, draw_y + PLAYER_SIZE//2 + 4)]
        else:
            points = [(draw_x + 6, draw_y + PLAYER_SIZE//2),
                      (draw_x + 12, draw_y + PLAYER_SIZE//2 - 4),
                      (draw_x + 12, draw_y + PLAYER_SIZE//2 + 4)]
        pygame.draw.polygon(screen, (255, 255, 255), points)