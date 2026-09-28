"""
tools/check_screenshot.py - quick pixel statistics for screenshot.png.

    python tools/check_screenshot.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

from config import RED, BLUE, PURPLE, HAZARD, EXIT  # noqa: E402


def near(c, target, tol=40):
    return all(abs(a - b) <= tol for a, b in zip(c[:3], target))


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenshot.png")
    pygame.init()
    img = pygame.image.load(os.path.abspath(path))
    w, h = img.get_size()
    assert (w, h) == (960, 640), "unexpected size {}".format((w, h))
    counts = {"red": 0, "blue": 0, "purple": 0, "amber": 0, "exit": 0, "text": 0}
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            c = img.get_at((x, y))
            if near(c, RED):
                counts["red"] += 1
            elif near(c, BLUE):
                counts["blue"] += 1
            elif near(c, PURPLE):
                counts["purple"] += 1
            elif near(c, HAZARD):
                counts["amber"] += 1
            elif near(c, EXIT):
                counts["exit"] += 1
            elif c.r > 200 and c.g > 200 and c.b > 200:
                counts["text"] += 1
    print("size: {}x{}".format(w, h))
    for k, v in counts.items():
        print("{:>7}: {:5d}".format(k, v))
    for key in ("red", "blue", "amber", "text"):
        assert counts[key] > 30, "screenshot missing {}: {}".format(key, counts)
    pygame.quit()
    print("SCREENSHOT OK")


if __name__ == "__main__":
    main()
