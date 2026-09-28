"""
tools/screenshot.py - render a real gameplay frame of the game (no window)
and save it as screenshot.png next to the README.

    python tools/screenshot.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

import main as game_mod  # noqa: E402
from levels_data import LEVELS  # noqa: E402


def main():
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshot.png")
    game = game_mod.Game(headless=True)
    game.start_level(11)                     # level 12: colors + orbit saws + laser
    # skip the intro card, walk in a little so the trail/sparks feel alive
    game.intro = 0.0
    game.update(1 / 60)
    game.deception.signals.clear()
    game.update(1 / 60)
    game.draw()
    pygame.image.save(game.frame, os.path.abspath(out_path))
    pygame.quit()
    print("wrote", os.path.abspath(out_path))


if __name__ == "__main__":
    main()
