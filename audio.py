"""
audio.py - all the sound of Chroma Lie, synthesized in memory at start-up.

No asset files, no new dependencies: every sample is written with the
standard-library `array`/`math` modules and wrapped in pygame.mixer.Sound.

Layout
    game.sfx["jump"]        one-shot Sound objects        -> game.sfx_play(name)
    game.sfx["death"]["fall"]  7 distinct death sounds    -> game.sfx_play("death_" + reason)
    game.ambient            looping drone (dark lab hum)  -> starts muted/unmuted from the save

Everything fails soft: with no audio device (or any mixer error) every call
becomes a no-op, so headless runs and silent machines keep working.
"""
import math
import struct

import pygame

from config import SFX_VOLUME, AMBIENT_VOLUME

RATE = 22050


# ------------------------------------------------------------------ helpers
def _samples(seconds):
    """Pre-allocated sample buffer + bound time list for one sound."""
    n = int(RATE * seconds)
    buf = [0.0] * n
    return buf, [i / RATE for i in range(n)]


def _sound(buf, volume=1.0):
    """Clamp, convert to 16-bit stereo and wrap in a mixer Sound."""
    data = bytearray()
    for s in buf:
        v = int(max(-1.0, min(1.0, s)) * 32000 * volume)
        data += struct.pack("<hh", v, v)          # same sample on both channels
    return pygame.mixer.Sound(buffer=bytes(data))


def _env(t, attack, release, total):
    """Linear attack + exponential-ish release, clipped to the sound length."""
    if t < attack:
        return t / max(attack, 1e-6)
    return math.exp(-3.5 * (t - attack) / max(total - attack, 1e-6))


def _tone(buf, ts, freq, vol, attack=0.004, release=0.5, bend=1.0):
    """Sine tone with pitch bend (`bend` = end frequency as a multiple)."""
    phase = 0.0
    for i, t in enumerate(ts):
        f = freq * (bend ** (t / ts[-1]))
        phase += 2.0 * math.pi * f / RATE
        buf[i] += vol * _env(t, attack, release, ts[-1]) * math.sin(phase)


def _saw(buf, ts, freq, vol, attack=0.004, release=0.5):
    phase = 0.0
    for i, t in enumerate(ts):
        phase += freq / RATE
        buf[i] += vol * _env(t, attack, release, ts[-1]) * (2.0 * (phase % 1.0) - 1.0)


def _noise(buf, ts, vol, attack=0.002, release=0.3, lp=0.0, seed=1):
    """White noise; `lp` in 0..1 slowly low-passes it (higher = duller)."""
    state, y = seed, 0.0
    for i, t in enumerate(ts):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        x = state / 0x3FFFFFFF - 1.0
        y += lp * (x - y)
        buf[i] += vol * _env(t, attack, release, ts[-1]) * y


def _sweep(buf, ts, f0, f1, vol, attack=0.003, release=0.6):
    """Continuous exponential pitch sweep (true glissando, for falls)."""
    phase = 0.0
    ln = ts[-1]
    for i, t in enumerate(ts):
        f = f0 * (f1 / f0) ** (t / ln)
        phase += 2.0 * math.pi * f / RATE
        buf[i] += vol * _env(t, attack, release, ln) * math.sin(phase)


def _zap(buf, ts, f0, f1, vol, attack=0.002, release=0.5, duty=0.35):
    """Square-ish zap with an exponential sweep - the electric bite."""
    phase = 0.0
    ln = ts[-1]
    for i, t in enumerate(ts):
        f = f0 * (f1 / f0) ** (t / ln)
        phase += f / RATE
        s = 1.0 if (phase % 1.0) < duty else -1.0
        buf[i] += vol * _env(t, attack, release, ln) * s


def _mix(bufs):
    """Sum several buffers element-wise into one."""
    n = max(len(b) for b in bufs)
    out = [0.0] * n
    for b in bufs:
        for i, s in enumerate(b):
            out[i] += s
    return out


# ------------------------------------------------------------------ one-shots
def _make_jump():
    buf, ts = _samples(0.16)
    _tone(buf, ts, 340, 0.5, release=0.12, bend=2.2)
    return buf


def _make_land():
    thud, ts1 = _samples(0.09)
    _sweep(thud, ts1, 190, 70, 0.9, release=0.06)
    tap, ts2 = _samples(0.05)
    _noise(tap, ts2, 0.30, release=0.04, lp=0.25, seed=7)
    return _mix([thud, tap])


def _make_spring():
    buf, ts = _samples(0.34)
    _tone(buf, ts, 180, 0.45, release=0.3, bend=3.4)
    ring, ts2 = _samples(0.3)
    _tone(ring, ts2, 1500, 0.10, release=0.24)
    return _mix([buf, ring])


def _make_move():
    buf, ts = _samples(0.06)
    _tone(buf, ts, 900, 0.22, release=0.045)
    return buf


def _make_confirm():
    buf, ts = _samples(0.12)
    _tone(buf, ts, 660, 0.3, release=0.1)
    buf2, ts2 = _samples(0.12)
    for i, t in enumerate(ts2):
        if t >= 0.06:
            buf2[i] = buf[i - int(0.06 * RATE)]
    _tone(buf2, ts2, 990, 0.0, release=0.1)
    out = _mix([buf, buf2])
    return out


def _make_back():
    buf, ts = _samples(0.12)
    _tone(buf, ts, 500, 0.28, release=0.1, bend=0.72)
    return buf


def _make_win():
    """Little rising arpeggio, a third per step, with a soft chime tail."""
    steps = (523.25, 659.25, 783.99, 1046.5)   # C5 E5 G5 C6
    bufs = []
    for i, f in enumerate(steps):
        buf, ts = _samples(0.32)
        delay = int(i * 0.09 * RATE)
        body, _ = _samples(0.32)
        _tone(body, ts, f, 0.32, release=0.24)
        chime, _ = _samples(0.32)
        _tone(chime, ts, f * 2, 0.10, release=0.3)
        both = _mix([body, chime])
        for j, s in enumerate(both):
            if delay + j < len(buf):
                buf[delay + j] = s
        bufs.append(buf)
    return _mix(bufs)


# ------------------------------------------------------------------ deaths
def _make_death_fall():
    buf, ts = _samples(0.55)
    _sweep(buf, ts, 800, 90, 0.6, release=0.5)     # falling whistle
    thud, ts2 = _samples(0.08)
    _sweep(thud, ts2, 140, 55, 0.95, release=0.06)
    out = _mix([buf, thud])
    return out


def _make_death_color():
    buf, ts = _samples(0.30)
    _zap(buf, ts, 900, 70, 0.5, release=0.24)
    crackle, ts2 = _samples(0.3)
    _noise(crackle, ts2, 0.22, release=0.2, lp=0.15, seed=3)
    return _mix([buf, crackle])


def _make_death_obstacle():
    buf, ts = _samples(0.22)
    _saw(buf, ts, 260, 0.5, release=0.16)
    _tone(buf, ts, 104, 0.5, release=0.16, bend=0.6)
    clang, ts2 = _samples(0.14)
    _noise(clang, ts2, 0.4, release=0.1, lp=0.35, seed=11)
    return _mix([buf, clang])


def _make_death_trap():
    buf, ts = _samples(0.26)
    _zap(buf, ts, 2200, 160, 0.5, release=0.2, duty=0.5)
    hum, ts2 = _samples(0.26)
    _tone(hum, ts2, 110, 0.4, release=0.2)
    return _mix([buf, hum])


def _make_death_spikes():
    buf, ts = _samples(0.2)
    _noise(buf, ts, 0.75, release=0.14, lp=0.05, seed=5)
    puncture, ts2 = _samples(0.12)
    _sweep(puncture, ts2, 420, 130, 0.5, release=0.09)
    return _mix([buf, puncture])


def _make_death_motion():
    buf, ts = _samples(0.34)
    _noise(buf, ts, 0.65, release=0.24, lp=0.5, seed=9)
    _sweep(buf, ts, 300, 60, 0.4, release=0.3)
    return buf


def _make_death_late():
    buf, ts = _samples(0.45)
    _saw(buf, ts, 210, 0.5, release=0.4)
    crunch, ts2 = _samples(0.45)
    _noise(crunch, ts2, 0.5, release=0.4, lp=0.22, seed=13)
    return _mix([buf, crunch])


# ------------------------------------------------------------------ ambient
def _make_ambient():
    """~9.6 s seamless loop: slow sub-drone + airy filtered noise + slow siren.

    Every layer's period divides 9.6 s exactly, so the loop point is inaudible.
    """
    seconds = 9.6
    buf, ts = _samples(seconds)
    ln = ts[-1]
    for t in ts:                                   # sub drone: 41.2 Hz E1 + slow beating
        beat = 0.5 + 0.5 * math.sin(2.0 * math.pi * (1 / seconds) * t)
        buf[int((t / ln) * (len(buf) - 1))] += 0.05 * beat * math.sin(2 * math.pi * 41.2 * t)
        buf[int((t / ln) * (len(buf) - 1))] += 0.04 * beat * math.sin(2 * math.pi * 41.9 * t + 1.3)
    air, ts2 = _samples(seconds)
    _noise(air, ts2, 0.035, attack=0.5, release=999, lp=0.9, seed=21)
    for i, s in enumerate(air):                    # fade the loop edge seamlessly
        k = min(1.0, i / (0.5 * RATE), (len(air) - i) / (0.5 * RATE))
        buf[i] += s * k
    for t in ts:                                   # eerie slow siren way down in the mix
        k = 0.5 - 0.5 * math.cos(2.0 * math.pi * (1 / seconds) * t)
        buf[int((t / ln) * (len(buf) - 1))] += 0.012 * k * math.sin(2 * math.pi * 220 * t)
    return buf


# ------------------------------------------------------------------ bundle
class Audio:
    """Owns the mixer, the synthesized sounds and the mute state."""

    def __init__(self, muted=False):
        self.ok = False
        self.sfx = {}
        self.death = {}
        self.ambient = None
        self.muted = bool(muted)
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=2, buffer=512)
        except (pygame.error, ValueError):
            return
        self.ok = True
        self.sfx = {
            "jump": _sound(_make_jump(), 0.9),
            "land": _sound(_make_land(), 1.0),
            "spring": _sound(_make_spring(), 0.9),
            "move": _sound(_make_move(), 0.8),
            "confirm": _sound(_make_confirm(), 0.9),
            "back": _sound(_make_back(), 0.9),
            "win": _sound(_make_win(), 0.9),
        }
        self.death = {
            "fall": _sound(_make_death_fall(), 0.95),
            "color": _sound(_make_death_color(), 0.9),
            "obstacle": _sound(_make_death_obstacle(), 0.9),
            "trap": _sound(_make_death_trap(), 0.9),
            "spikes": _sound(_make_death_spikes(), 0.9),
            "motion": _sound(_make_death_motion(), 0.9),
            "late": _sound(_make_death_late(), 0.9),
        }
        self.ambient = _sound(_make_ambient(), AMBIENT_VOLUME)
        self.ambient.set_volume(0.0 if self.muted else AMBIENT_VOLUME)
        self.ambient.play(loops=-1)

    # ------------------------------------------------------------ api
    def play(self, name):
        """Play a one-shot by name; death sounds are 'death_' + reason."""
        if not self.ok or self.muted:
            return
        if name.startswith("death_"):
            snd = self.death.get(name[6:])
        else:
            snd = self.sfx.get(name)
        if snd:
            snd.set_volume(SFX_VOLUME)
            snd.play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok:
            self.ambient.set_volume(0.0 if self.muted else AMBIENT_VOLUME)
        return self.muted
