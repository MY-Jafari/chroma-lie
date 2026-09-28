"""
tools/smoke_audio.py - headless smoke test for audio.py.

    python tools/smoke_audio.py

With a real audio device it exercises every play path; with the dummy SDL
driver it still verifies the fail-soft behavior and that the Audio bundle
synthesizes all sounds (or no-ops cleanly when no device is available).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

import config  # noqa: E402
from audio import Audio  # noqa: E402

pygame.init()

DEATH_REASONS = ("fall", "color", "obstacle", "trap", "spikes", "motion", "late")
SFX_NAMES = ("jump", "land", "spring", "move", "confirm", "back", "win")

audio = Audio()
print("mixer ok:", audio.ok)

if audio.ok:
    missing = [n for n in SFX_NAMES if n not in audio.sfx]
    missing += ["death_" + r for r in DEATH_REASONS if r not in audio.death]
    assert not missing, "missing sounds: {}".format(missing)
    assert audio.ambient is not None
    for name in SFX_NAMES + tuple("death_" + r for r in DEATH_REASONS):
        audio.play(name)
    assert audio.toggle_mute() is True
    assert audio.toggle_mute() is False
    # ambient channel actually playing and audible when unmuted
    ch = audio.ambient.get_num_channels()
    assert ch >= 1, "ambient loop is not playing"
    print("all", len(SFX_NAMES) + len(DEATH_REASONS), "sounds synthesized and playable")
else:
    print("no audio device - fail-soft path verified (no crash)")

# save round-trip of the mute flag, mirroring main.py's write path
save = {"muted": audio.muted}
import json
tmp = os.path.join(config.SAVE_FILE)
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(save, f)
with open(tmp, "r", encoding="utf-8") as f:
    back = json.load(f)
assert back["muted"] == audio.muted
os.remove(tmp)
print("save round-trip ok")

pygame.quit()
print("SMOKE OK")
