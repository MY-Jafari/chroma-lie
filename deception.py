"""
deception.py - the lying brain of Chroma Lie.

Holds the CURRENT real rule set and the (possibly lying) instruction text.
Rule changes are fired by zone triggers, timers, or a periodic cycle (level 14)
and are revealed silently, with a glitch, or with a vague message.
"""
from config import RULE_GRACE, GLITCH_DURATION, MESSAGE_TIME

DEFAULT_RULES = {
    "red_meaning": "danger",
    "blue_meaning": "safe",
    "purple_meaning": "safe",
    "controls_swapped": False,
    "hidden_rule_active": None,
}

TILE_TO_RULE = {"R": "red_meaning", "B": "blue_meaning", "P": "purple_meaning"}


class DeceptionSystem:
    def __init__(self, level_def):
        self.rules = dict(DEFAULT_RULES)
        self.rules.update(level_def.get("initial_rules", {}))
        self.display_text = level_def.get("instruction", "RED = DANGER   BLUE = SAFE")
        self.events = [dict(e, fired=False) for e in level_def.get("rule_change", [])]
        self.cycle = level_def.get("cycle")
        self.cycle_index = 0
        self.cycle_clock = 0.0
        self.time = 0.0
        self.grace = 0.0            # colored tiles are harmless while > 0
        self.text_glitch = 0.0      # seconds of glitch left on the instruction text
        self.flicker_truth = False  # lying text briefly shows the truth now and then
        self.message = None
        self.message_timer = 0.0
        self._pending = []          # [seconds_left, event] waiting for their pre-glitch
        self.signals = []           # effect requests consumed by main.py: "glitch", "blip"

    # ------------------------------------------------------------ queries
    def is_danger(self, tile_char):
        """True if the tile is deadly under the CURRENT (real) rule."""
        key = TILE_TO_RULE.get(tile_char)
        return key is not None and self.rules[key] == "danger"

    def is_lethal(self, tile_char):
        """Deadly right now (respects the short grace window after a change)."""
        return self.grace <= 0 and self.is_danger(tile_char)

    @property
    def controls_swapped(self):
        return self.rules["controls_swapped"]

    def truth_text(self):
        return "RED = {}   BLUE = {}".format(self.rules["red_meaning"].upper(),
                                            self.rules["blue_meaning"].upper())

    def shown_text(self):
        """Text the HUD displays. Lying text flickers to the truth for a split second."""
        if self.flicker_truth and (self.time % 2.6) < 0.12:
            return self.truth_text()
        return self.display_text

    def cycle_progress(self):
        if not self.cycle:
            return None
        return min(1.0, self.cycle_clock / self.cycle["period"])

    # ------------------------------------------------------------ update
    def update(self, dt, player_rect):
        self.time += dt
        self.grace = max(0.0, self.grace - dt)
        self.text_glitch = max(0.0, self.text_glitch - dt)
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None

        for ev in self.events:
            if not ev["fired"] and self._triggered(ev["trigger"], player_rect):
                ev["fired"] = True
                pre = ev.get("pre_glitch", 0)
                if pre > 0:                       # subtle tell BEFORE the lie happens
                    self.text_glitch = max(self.text_glitch, pre)
                    self._pending.append([pre, ev])
                else:
                    self._apply(ev)

        for item in self._pending[:]:
            item[0] -= dt
            if item[0] <= 0:
                self._pending.remove(item)
                self._apply(item[1])

        if self.cycle:
            self._update_cycle(dt)

    def _triggered(self, trig, player_rect):
        if trig["type"] == "time":
            return self.time >= trig["t"]
        if trig["type"] == "zone":
            x, y, w, h = trig["rect"]
            return player_rect.colliderect((x, y, w, h))
        return False

    def _apply(self, ev):
        self.rules.update(ev.get("changes", {}))
        if ev.get("changes"):
            self.grace = RULE_GRACE
        if "display" in ev:
            self.display_text = ev["display"]
        if ev.get("flicker_truth"):
            self.flicker_truth = True
        method = ev.get("method", "silent")
        if method == "glitch":
            self.signals.append("glitch")
            self.text_glitch = max(self.text_glitch, GLITCH_DURATION)
        elif method == "vague_message":
            self.message = ev.get("message", "are you sure?")
            self.message_timer = MESSAGE_TIME
        # "silent": nothing at all. Only the world itself tells the truth.

    def _update_cycle(self, dt):
        period, warn = self.cycle["period"], self.cycle["warn"]
        before = self.cycle_clock
        self.cycle_clock += dt
        if before < period - warn <= self.cycle_clock:
            self.text_glitch = max(self.text_glitch, warn)      # fair warning
        if self.cycle_clock >= period:
            self.cycle_clock -= period
            self.cycle_index = (self.cycle_index + 1) % len(self.cycle["states"])
            state = self.cycle["states"][self.cycle_index]
            self.rules.update(state["changes"])
            self.display_text = state.get("display", self.display_text)
            self.grace = RULE_GRACE
            self.signals.append("blip")
