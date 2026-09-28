"""
tools/smoke_game.py - headless integration smoke test for the real Game loop.

    python tools/smoke_game.py

Boots the actual Game (no window), simulates frames, and walks the three
critical paths: playing, dying (level resets, deaths counted) and winning
(save written, next level unlocked). The save file is redirected to a temp
path so the player's real progress is never touched.
"""
import json
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

import main as game_mod  # noqa: E402
import config  # noqa: E402
from levels_data import LEVELS  # noqa: E402


def run_frames(game, n):
    """Push n frames through the real update/draw pipeline."""
    dt = 1 / 60
    for _ in range(n):
        game.update(dt)
        game.input.jump_pressed = False      # the real loop clears this every substep
        game.draw()


def main():
    tmpdir = tempfile.mkdtemp()
    save_path = os.path.join(tmpdir, config.SAVE_FILE)
    game_mod.SAVE_PATH = save_path                     # redirect the save away from real progress

    game = game_mod.Game(headless=True)
    assert game.audio is not None and game.audio.ok, "Audio failed to initialize"

    # ---------------- play path: wall-to-wall walking (level 1's honest red
    # floor tiles are deadly, so the walk stays between the two walls)
    game.start_level(0)
    game.intro = 0.0
    game.input.left = True                             # walk left into the boundary wall
    run_frames(game, 20)
    game.input.left = False
    game.input.right = True
    run_frames(game, 12)                               # a short hop back toward the spawn
    game.input.right = False
    run_frames(game, 10)
    assert game.state == "play" and game.deaths == 0, "died during the safe walk"

    # ---------------- jump path: one buffered jump press through the input state
    game.input.right = False
    game.input.poll(jump_pressed_this_frame=True)
    run_frames(game, 2)                                # just_jumped resets at update start
    assert game.player.just_jumped or game.player.vy < 0, "jump did not happen"
    run_frames(game, 40)                               # jump-cut rise + fall, back to ground
    assert game.player.on_ground, "player never landed"

    # ---------------- death path: drop the player into the pit, expect reset
    game.player.x, game.player.y = float(config.WIDTH + 40), float(config.HEIGHT + 40)
    game.player.vx = game.player.vy = 0.0
    run_frames(game, 12)                               # fall past FALL_DEATH_Y (HEIGHT + 60)
    assert game.deaths == 1, "death was not detected"
    run_frames(game, 40)                               # DEATH_RESET_DELAY, then respawn
    assert game.dead_timer <= 0 and game.deaths == 1
    assert game.player.rect.top < config.HEIGHT, "player did not respawn"

    # ---------------- win path: touch the gate, expect save + next level
    game.start_level(0)
    game.intro = 0.0
    game.update(1 / 60)
    ex, ey = game.level.exit_rect.center
    game.player.x, game.player.y = float(ex - game.player.w / 2), float(ey - game.player.h / 2)
    game.player.vx = game.player.vy = 0.0
    run_frames(game, 3)
    assert game.win_timer > 0, "win was not detected"
    run_frames(game, 60)                               # WIN_DELAY, then level 2 starts
    assert game.level_index == 1, "did not advance to level 2"
    with open(save_path, "r", encoding="utf-8") as f:
        save = json.load(f)
    assert save["unlocked"] >= 2, "level 2 not unlocked in save"
    assert save["best"].get("1") == 0, "best score for level 1 not recorded"

    # ---------------- mute toggle round-trip through the game object
    game.save["muted"] = game.audio.toggle_mute()
    assert game.save["muted"] is True
    game.save["muted"] = game.audio.toggle_mute()
    assert game.save["muted"] is False

    pygame.quit()
    print("SMOKE GAME OK")


if __name__ == "__main__":
    main()
