"""Headless regression tests for the three reported bugs.
Run: SDL_VIDEODRIVER=dummy python test_bugs.py
"""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import main as game_main
from main import ChromaLie, GameState
from player import Player
from deception import deception

pygame.init()

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILS.append(name)


def key_down(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def key_up(k):
    return pygame.event.Event(pygame.KEYUP, key=k)


def fresh_game():
    g = ChromaLie()
    g.state = GameState.PLAYING
    return g


def pump(g, frames=1, dt=1 / 60.0):
    for _ in range(frames):
        g.update(dt)


# ---------------------------------------------------------------- BUG 1
print("\n[BUG 1] Held key must not stick forever")
g = fresh_game()
g.player.handle_event(key_down(pygame.K_RIGHT))
pump(g, 2)
moving = abs(g.player.vel_x) > 1
g.player.handle_event(key_up(pygame.K_RIGHT))
pump(g, 30)
stopped = abs(g.player.vel_x) < 1
check("right key sets velocity", moving, f"vel_x={g.player.vel_x}")
check("releasing right stops the player", stopped, f"vel_x={g.player.vel_x}")
check("move_right flag cleared", g.player.move_right is False)

# KEYUP must still be honoured when the player is dead
g2 = fresh_game()
g2.player.handle_event(key_down(pygame.K_LEFT))
g2.player.dead = True
g2.player.handle_event(key_up(pygame.K_LEFT))
check("KEYUP processed while dead", g2.player.move_left is False)

# And through the real main-loop event path
g3 = fresh_game()
g3.handle_events()  # drain
g3.player.move_right = True
pygame.event.post(key_up(pygame.K_RIGHT))
g3.handle_events()
check("main loop routes KEYUP to player", g3.player.move_right is False)

# ---------------------------------------------------------------- BUG 2
print("\n[BUG 2] Falling off the bottom must kill and respawn")
g = fresh_game()
g.player.rect.y = 900
g.player.rect.x = 60
# Put the player somewhere with no floor beneath him
g.player.rect.y = 2000
g.update(1 / 60.0)
check("player dies below the kill plane", g.player.dead is True,
      f"dead={g.player.dead} y={g.player.rect.y}")

# Respawn should happen automatically after the death animation
g.restart_level()
check("respawn clears death", g.player.dead is False)
check("respawn returns to start x", g.player.rect.x == g.level_data["player_start"][0],
      f"x={g.player.rect.x} expected={g.level_data['player_start'][0]}")
check("respawn increments death count", g.total_deaths >= 1, f"deaths={g.total_deaths}")

# The respawn must fire from the update loop, not only via the R key
g4 = fresh_game()
deaths_before = g4.total_deaths
g4.player.rect.y = 2000
for _ in range(90):          # 1.5s of frames, longer than DEATH_RESPAWN_DELAY
    g4.update(1 / 60.0)
check("auto-respawn triggers from update loop", g4.total_deaths > deaths_before,
      f"before={deaths_before} after={g4.total_deaths}")
check("player alive again after auto-respawn", g4.player.dead is False)

# ---------------------------------------------------------------- BUG 3
print("\n[BUG 3] Jump must work while an arrow key is held")
g = fresh_game()
pump(g, 30)                      # settle onto the floor
check("player is on the ground", g.player.on_ground is True)

g.player.handle_event(key_down(pygame.K_RIGHT))
g.player.handle_event(key_down(pygame.K_SPACE))
pump(g, 2)
check("jump fires while moving right", g.player.vel_y < 0,
      f"vel_y={g.player.vel_y} on_ground={g.player.on_ground}")
y_before = g.player.rect.y
pump(g, 12)
check("player actually rises", g.player.rect.y < y_before,
      f"y {y_before} -> {g.player.rect.y}")

# The bug: holding an arrow must not suppress the jump over time
g = fresh_game()
pump(g, 30)
g.player.handle_event(key_down(pygame.K_RIGHT))
pump(g, 40)                      # walk for a while, still holding
on_ground_walk = g.player.on_ground
g.player.handle_event(key_down(pygame.K_SPACE))
pump(g, 2)
check("jump still works after walking", g.player.vel_y < 0 or not on_ground_walk,
      f"vel_y={g.player.vel_y} on_ground={g.player.on_ground}")

# Jump with left held, and after a dash
g = fresh_game()
pump(g, 30)
g.player.handle_event(key_down(pygame.K_LEFT))
g.player.handle_event(key_down(pygame.K_SPACE))
pump(g, 2)
check("jump works while holding left", g.player.vel_y < 0, f"vel_y={g.player.vel_y}")

# ---------------------------------------------------------------- BUG 3b (red tiles)
print("\n[BUG 3b] Standing on a red tile must kill")
g = fresh_game()
pump(g, 30)
red = [t for t in g.current_level.tiles if t.color == "red"]
if not red:
    check("level 1 has a red tile to test", False, "no red tiles found")
else:
    target = red[0]
    g.player.rect.x = target.rect.centerx - g.player.rect.width // 2
    g.player.rect.y = target.rect.top - g.player.rect.height
    result = g.current_level.check_collisions(g.player.rect)
    check("standing on red tile returns death", result == "death", f"got={result}")

    # And a blue tile must be safe
    blue = [t for t in g.current_level.tiles if t.color == "blue"]
    if blue:
        b = blue[0]
        g.player.rect.x = b.rect.centerx - g.player.rect.width // 2
        g.player.rect.y = b.rect.top - g.player.rect.height
        r2 = g.current_level.check_collisions(g.player.rect)
        check("standing on blue tile is safe", r2 != "death", f"got={r2}")

print("\n" + "=" * 60)
if FAILS:
    print(f"FAILED ({len(FAILS)}): {FAILS}")
else:
    print("ALL TESTS PASSED")
