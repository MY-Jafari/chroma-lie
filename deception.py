"""Deception system - manages rule changes and lies in Chroma Lie."""

import random
from config import *

class DeceptionManager:
    """Central manager for all deception mechanics."""

    def __init__(self):
        self.current_rules = {
            "red_meaning": "danger",
            "blue_meaning": "safe",
            "controls_swapped": False,
            "hidden_rule_active": None,
            "hidden_rule_params": {}
        }
        self.displayed_rules = {
            "red_meaning": "danger",
            "blue_meaning": "safe"
        }
        self.glitch_timer = 0.0
        self.glitch_active = False
        self.message_timer = 0.0
        self.message_text = ""
        self.level_rule_changes = []
        self.change_history = []

    def reset_for_level(self, level_id, rule_change_data=None):
        """Reset rules for a new level, applying any scripted changes."""
        self.current_rules = {
            "red_meaning": "danger",
            "blue_meaning": "safe",
            "controls_swapped": False,
            "hidden_rule_active": None,
            "hidden_rule_params": {}
        }
        self.displayed_rules = {
            "red_meaning": "danger",
            "blue_meaning": "safe"
        }
        self.glitch_timer = 0.0
        self.glitch_active = False
        self.message_timer = 0.0
        self.message_text = ""

        if rule_change_data:
            self.level_rule_changes = rule_change_data if isinstance(rule_change_data, list) else [rule_change_data]
        else:
            self.level_rule_changes = []

    def apply_scripted_change(self, change_data):
        """Apply a scripted rule change from level data."""
        change_type = change_data.get("type", "")
        reveal = change_data.get("reveal", "silent")

        if change_type == "swap_colors":
            self._swap_color_meanings(reveal)
        elif change_type == "swap_controls":
            self._swap_controls(reveal)
        elif change_type == "hidden_rule":
            self._activate_hidden_rule(change_data.get("rule"), reveal)
        elif change_type == "glitch_text":
            self._trigger_text_glitch(reveal)

        self.change_history.append({
            "level": len(self.change_history) + 1,
            "type": change_type,
            "reveal": reveal
        })

    def _swap_color_meanings(self, reveal="silent"):
        """Swap the meaning of red and blue tiles."""
        self.current_rules["red_meaning"], self.current_rules["blue_meaning"] = \
            self.current_rules["blue_meaning"], self.current_rules["red_meaning"]
        self._trigger_glitch(reveal)

    def _swap_controls(self, reveal="silent"):
        """Swap left/right controls."""
        self.current_rules["controls_swapped"] = not self.current_rules["controls_swapped"]
        self._trigger_glitch(reveal)

    def _activate_hidden_rule(self, rule_name, reveal="silent"):
        """Activate a hidden rule."""
        self.current_rules["hidden_rule_active"] = rule_name
        self.current_rules["hidden_rule_params"] = {}
        self._trigger_glitch(reveal)

    def _trigger_text_glitch(self, reveal="silent"):
        """Trigger a text glitch effect on the displayed rules."""
        self.displayed_rules["red_meaning"] = random.choice(["danger", "safe", "???", "lie"])
        self.displayed_rules["blue_meaning"] = random.choice(["safe", "danger", "???", "lie"])
        self._trigger_glitch(reveal)

    def _trigger_glitch(self, reveal_type):
        """Trigger visual glitch effect based on reveal type."""
        self.glitch_timer = GLITCH_DURATION
        self.glitch_active = True

        if reveal_type == "message":
            messages = [
                "Are you sure?",
                "Rules still the same?",
                "Trust your eyes?",
                "Red means stop... or does it?",
                "Memory is unreliable.",
                "The display lies."
            ]
            self.message_text = random.choice(messages)
            self.message_timer = 2.0
        elif reveal_type == "subtle":
            # Just a brief visual hint
            pass

    def maybe_random_change(self, level_id, probability=0.15):
        """Randomly apply a deception change (for later levels)."""
        if random.random() < probability:
            change_type = random.choice(["swap_colors", "swap_controls", "hidden_rule"])
            if change_type == "hidden_rule":
                rule = random.choice(["purple_deadly", "yellow_safe_when_moving", "safe_only_while_jumping"])
                self._activate_hidden_rule(rule, "silent")
            elif change_type == "swap_colors":
                self._swap_color_meanings("silent")
            else:
                self._swap_controls("silent")

    def update(self, dt):
        """Update timers."""
        if self.glitch_timer > 0:
            self.glitch_timer -= dt
            if self.glitch_timer <= 0:
                self.glitch_active = False
                # Restore displayed rules to match current (unless text glitch active)
                if self.current_rules.get("hidden_rule_active") != "glitch_text":
                    self.displayed_rules["red_meaning"] = self.current_rules["red_meaning"]
                    self.displayed_rules["blue_meaning"] = self.current_rules["blue_meaning"]

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text = ""

    def get_tile_safety(self, tile_color):
        """Check if a tile color is safe or dangerous based on current rules."""
        # Hidden rules override everything
        if self.current_rules["hidden_rule_active"] == "purple_deadly" and tile_color == "purple":
            return False
        if self.current_rules["hidden_rule_active"] == "yellow_safe_when_moving" and tile_color == "yellow":
            return self.current_rules["hidden_rule_params"].get("player_moving", False)
        if self.current_rules["hidden_rule_active"] == "safe_only_while_jumping" and tile_color in ["red", "blue"]:
            return self.current_rules["hidden_rule_params"].get("player_jumping", False)

        # Standard color rules
        if tile_color == "red":
            return self.current_rules["red_meaning"] == "safe"
        elif tile_color == "blue":
            return self.current_rules["blue_meaning"] == "safe"
        elif tile_color == "purple":
            return self.current_rules.get("purple_meaning", "danger") == "safe"
        elif tile_color == "yellow":
            return self.current_rules.get("yellow_meaning", "danger") == "safe"
        return True  # Default safe for unknown colors

    def get_displayed_rule_text(self):
        """Get the text to display for rules (may be glitched)."""
        return f"RED = {self.displayed_rules['red_meaning'].upper()}    BLUE = {self.displayed_rules['blue_meaning'].upper()}"

    def get_glitch_offset(self):
        """Get current glitch offset for rendering."""
        if not self.glitch_active or self.glitch_timer <= 0:
            return (0, 0)
        # Oscillating offset based on remaining time
        import math
        t = self.glitch_timer / GLITCH_DURATION
        offset = int(GLITCH_INTENSITY * math.sin(t * 20) * t)
        return (offset, 0)

    def get_camera_shake(self):
        """Get camera shake offset."""
        if not self.glitch_active or self.glitch_timer > GLITCH_DURATION - CAMERA_SHAKE_DURATION:
            import random
            return (random.randint(-CAMERA_SHAKE_INTENSITY, CAMERA_SHAKE_INTENSITY),
                    random.randint(-CAMERA_SHAKE_INTENSITY, CAMERA_SHAKE_INTENSITY))
        return (0, 0)

    def set_player_state(self, moving=False, jumping=False):
        """Update hidden rule parameters based on player state."""
        if self.current_rules["hidden_rule_active"] == "yellow_safe_when_moving":
            self.current_rules["hidden_rule_params"]["player_moving"] = moving
        if self.current_rules["hidden_rule_active"] == "safe_only_while_jumping":
            self.current_rules["hidden_rule_params"]["player_jumping"] = jumping


# Global instance
deception = DeceptionManager()