"""Comprehensive level designs for Chroma Lie.
15 handcrafted levels progressing from baseline tutorial to deceptive breakdown.
"""

def generate_solid_floor(start_x, end_x, y, color="blue"):
    """Helper to generate a horizontal row of tiles."""
    tiles = []
    for x in range(start_x, end_x, 40):
        tiles.append({"x": x, "y": y, "color": color, "type": "static"})
    return tiles

def generate_platform(x, y, count, color="blue"):
    """Helper to generate a floating platform."""
    tiles = []
    for i in range(count):
        tiles.append({"x": x + i * 40, "y": y, "color": color, "type": "static"})
    return tiles


LEVELS = [
    # -------------------------------------------------------------
    # PHASE 1: TUTORIAL & BASELINE (Honest Rules: RED=DANGER, BLUE=SAFE)
    # -------------------------------------------------------------
    {
        "id": 1,
        "title": "PROTOCOL INITIALIZATION",
        "player_start": (60, 520),
        "exit_gate": (860, 480),
        "rule_change": {"type": "none", "reveal": "silent"},
        "tiles": [
            # Solid safe blue floor
            *generate_solid_floor(0, 960, 560, "blue"),
            # Small hazard pit in the middle to learn jumping
            {"x": 440, "y": 560, "color": "red", "type": "static"},
            {"x": 480, "y": 560, "color": "red", "type": "static"},
            # Elevated safe step
            *generate_platform(440, 460, 2, "blue"),
        ],
        "moving_obstacles": [],
        "timed_traps": [],
    },
    {
        "id": 2,
        "title": "COLOR DISCRIMINATION",
        "player_start": (60, 520),
        "exit_gate": (860, 200),
        "rule_change": {"type": "none", "reveal": "silent"},
        "tiles": [
            # Floor segments with red danger zones
            *generate_platform(0, 560, 4, "blue"),
            *generate_platform(160, 560, 4, "red"),
            *generate_platform(320, 560, 4, "blue"),
            *generate_platform(480, 560, 4, "red"),
            *generate_platform(640, 560, 8, "blue"),
            # Stepping platforms upward
            *generate_platform(240, 440, 3, "blue"),
            *generate_platform(440, 340, 3, "blue"),
            *generate_platform(680, 260, 4, "blue"),
        ],
        "moving_obstacles": [],
        "timed_traps": [],
    },
    {
        "id": 3,
        "title": "HAZARD AVOIDANCE",
        "player_start": (60, 520),
        "exit_gate": (860, 160),
        "rule_change": {"type": "none", "reveal": "silent"},
        "tiles": [
            # Ground with alternating hazard teeth
            *generate_platform(0, 560, 3, "blue"),
            *generate_platform(120, 560, 2, "red"),
            *generate_platform(200, 560, 2, "blue"),
            *generate_platform(280, 560, 2, "red"),
            *generate_platform(360, 560, 3, "blue"),
            *generate_platform(480, 560, 3, "red"),
            *generate_platform(600, 560, 4, "blue"),
            *generate_platform(760, 560, 5, "blue"),
            # Vertical platforming sequence
            *generate_platform(160, 430, 2, "blue"),
            *generate_platform(320, 340, 2, "blue"),
            *generate_platform(520, 270, 3, "blue"),
            *generate_platform(720, 220, 4, "blue"),
        ],
        "moving_obstacles": [
            {"x": 420, "y": 200, "width": 30, "height": 30, "movement_type": "horizontal", "range": 120, "speed": 140}
        ],
        "timed_traps": [],
    },

    # -------------------------------------------------------------
    # PHASE 2: FIRST LIES (COLOR SWAP - RED=SAFE, BLUE=DANGER)
    # -------------------------------------------------------------
    {
        "id": 4,
        "title": "ANOMALOUS DATA",
        "player_start": (60, 520),
        "exit_gate": (860, 480),
        # First lie: Display still says RED=DANGER, but RED is now SAFE and BLUE is DANGER!
        "rule_change": {"type": "swap_colors", "reveal": "subtle", "msg": "SYSTEM FLICKER DETECTED"},
        "tiles": [
            # Starting safe haven
            *generate_platform(0, 560, 3, "red"),  # Now red is safe!
            # The bridge is made of red tiles (safe) with blue traps (deadly)
            *generate_platform(120, 560, 4, "blue"), # Danger!
            *generate_platform(280, 560, 5, "red"),  # Safe!
            *generate_platform(480, 560, 3, "blue"), # Danger!
            *generate_platform(600, 560, 9, "red"),  # Safe path to exit!
            # High path
            *generate_platform(200, 420, 3, "red"),
            *generate_platform(420, 360, 3, "red"),
        ],
        "moving_obstacles": [],
        "timed_traps": [],
    },
    {
        "id": 5,
        "title": "COGNITIVE DISSONANCE",
        "player_start": (60, 520),
        "exit_gate": (860, 220),
        # Red is still safe, blue is danger
        "rule_change": {"type": "swap_colors", "reveal": "message", "msg": "ARE YOU SURE OF WHAT YOU SEE?"},
        "tiles": [
            *generate_platform(0, 560, 4, "red"),
            *generate_platform(160, 560, 4, "blue"),
            *generate_platform(320, 560, 4, "red"),
            *generate_platform(480, 560, 4, "blue"),
            *generate_platform(640, 560, 8, "red"),
            # Elevated stepped route
            *generate_platform(180, 450, 3, "red"),
            *generate_platform(360, 360, 3, "red"),
            *generate_platform(560, 290, 3, "red"),
            *generate_platform(740, 280, 4, "red"),
        ],
        "moving_obstacles": [
            {"x": 260, "y": 300, "width": 30, "height": 30, "movement_type": "vertical", "range": 80, "speed": 160}
        ],
        "timed_traps": [],
    },
    {
        "id": 6,
        "title": "TIMED DISRUPTION",
        "player_start": (60, 520),
        "exit_gate": (860, 160),
        # Red is safe, plus timed blinking tiles
        "rule_change": {"type": "swap_colors", "reveal": "subtle", "msg": "DIRECTIVE UNVERIFIED"},
        "tiles": [
            *generate_platform(0, 560, 3, "red"),
            # Timed red and blue tiles
            {"x": 120, "y": 560, "color": "red", "type": "timed"},
            {"x": 160, "y": 560, "color": "red", "type": "timed"},
            *generate_platform(200, 560, 3, "blue"), # Dangerous
            *generate_platform(320, 560, 4, "red"),
            *generate_platform(480, 560, 4, "blue"),
            *generate_platform(640, 560, 8, "red"),
            # High ladder
            *generate_platform(160, 430, 2, "red"),
            *generate_platform(340, 340, 3, "red"),
            *generate_platform(540, 250, 3, "red"),
            *generate_platform(740, 220, 4, "red"),
        ],
        "moving_obstacles": [],
        "timed_traps": [
            {"x": 420, "y": 300, "width": 60, "height": 20, "cycle_time": 2.5, "active_time": 1.2}
        ],
    },

    # -------------------------------------------------------------
    # PHASE 3: CONTROL INVERSION & MULTI-THREATS
    # -------------------------------------------------------------
    {
        "id": 7,
        "title": "MOTOR MALFUNCTION",
        "player_start": (60, 520),
        "exit_gate": (860, 480),
        # Standard colors (Blue safe, Red danger), BUT CONTROLS ARE SWAPPED!
        "rule_change": {"type": "swap_controls", "reveal": "subtle", "msg": "MOTOR FEEDBACK REVERSED"},
        "tiles": [
            *generate_solid_floor(0, 960, 560, "blue"),
            # Hazard gaps
            {"x": 280, "y": 560, "color": "red", "type": "static"},
            {"x": 320, "y": 560, "color": "red", "type": "static"},
            {"x": 560, "y": 560, "color": "red", "type": "static"},
            {"x": 600, "y": 560, "color": "red", "type": "static"},
            # Stepping blocks
            *generate_platform(280, 440, 2, "blue"),
            *generate_platform(560, 440, 2, "blue"),
        ],
        "moving_obstacles": [],
        "timed_traps": [],
    },
    {
        "id": 8,
        "title": "DUAL DECEPTION",
        "player_start": (60, 520),
        "exit_gate": (860, 200),
        # BOTH controls swapped AND color meanings swapped (Red=Safe)!
        "rule_change": [
            {"type": "swap_colors", "reveal": "silent"},
            {"type": "swap_controls", "reveal": "message", "msg": "ALL INPUTS ARE UNSTABLE"}
        ],
        "tiles": [
            *generate_platform(0, 560, 4, "red"),
            *generate_platform(160, 560, 4, "blue"),
            *generate_platform(320, 560, 4, "red"),
            *generate_platform(480, 560, 4, "blue"),
            *generate_platform(640, 560, 8, "red"),
            # High path
            *generate_platform(200, 450, 3, "red"),
            *generate_platform(400, 360, 3, "red"),
            *generate_platform(620, 280, 4, "red"),
            *generate_platform(780, 250, 4, "red"),
        ],
        "moving_obstacles": [
            {"x": 300, "y": 400, "width": 30, "height": 30, "movement_type": "horizontal", "range": 80, "speed": 150}
        ],
        "timed_traps": [],
    },
    {
        "id": 9,
        "title": "ORBITAL KINETICS",
        "player_start": (60, 520),
        "exit_gate": (860, 160),
        # Controls inverted, Blue is safe again!
        "rule_change": {"type": "swap_controls", "reveal": "silent"},
        "tiles": [
            *generate_platform(0, 560, 4, "blue"),
            *generate_platform(160, 560, 4, "red"),
            *generate_platform(320, 560, 4, "blue"),
            *generate_platform(480, 560, 4, "red"),
            *generate_platform(640, 560, 8, "blue"),
            # Step stones
            *generate_platform(180, 440, 2, "blue"),
            *generate_platform(360, 360, 2, "blue"),
            *generate_platform(540, 280, 2, "blue"),
            *generate_platform(720, 220, 4, "blue"),
        ],
        "moving_obstacles": [
            {"x": 260, "y": 380, "width": 30, "height": 30, "movement_type": "circular", "range": 60, "speed": 180},
            {"x": 460, "y": 300, "width": 30, "height": 30, "movement_type": "circular", "range": 60, "speed": 180}
        ],
        "timed_traps": [],
    },
    {
        "id": 10,
        "title": "SYNAPSE OVERLOAD",
        "player_start": (60, 520),
        "exit_gate": (860, 140),
        # Colors swapped (Red safe), controls inverted, moving laser wall
        "rule_change": [
            {"type": "swap_colors", "reveal": "silent"},
            {"type": "swap_controls", "reveal": "message", "msg": "CAN YOU STILL TELL LEFT FROM RIGHT?"}
        ],
        "tiles": [
            *generate_platform(0, 560, 3, "red"),
            *generate_platform(120, 560, 3, "blue"),
            *generate_platform(240, 560, 3, "red"),
            *generate_platform(360, 560, 3, "blue"),
            *generate_platform(480, 560, 4, "red"),
            *generate_platform(640, 560, 8, "red"),
            # Climbing platforms
            *generate_platform(140, 440, 2, "red"),
            *generate_platform(280, 350, 2, "red"),
            *generate_platform(440, 270, 3, "red"),
            *generate_platform(640, 200, 3, "red"),
            *generate_platform(800, 180, 4, "red"),
        ],
        "moving_obstacles": [
            {"x": 360, "y": 220, "width": 25, "height": 80, "movement_type": "horizontal", "range": 100, "speed": 160}
        ],
        "timed_traps": [
            {"x": 520, "y": 240, "width": 50, "height": 20, "cycle_time": 2.0, "active_time": 1.0}
        ],
    },

    # -------------------------------------------------------------
    # PHASE 4: HIDDEN & UNWRITTEN RULES (PURPLE / YELLOW TILES)
    # -------------------------------------------------------------
    {
        "id": 11,
        "title": "THE UNSEEN SPECTRUM",
        "player_start": (60, 520),
        "exit_gate": (860, 480),
        # Introduce Purple tiles (Never mentioned on HUD, always deadly!)
        "rule_change": {"type": "hidden_rule", "rule": "purple_deadly", "reveal": "subtle", "msg": "A NEW FREQUENCY APPEARS"},
        "tiles": [
            *generate_solid_floor(0, 960, 560, "blue"),
            # Purple tiles disguised along the path
            {"x": 280, "y": 560, "color": "purple", "type": "static"},
            {"x": 320, "y": 560, "color": "purple", "type": "static"},
            {"x": 520, "y": 560, "color": "purple", "type": "static"},
            {"x": 560, "y": 560, "color": "purple", "type": "static"},
            # Jump steps over purple
            *generate_platform(280, 440, 2, "blue"),
            *generate_platform(520, 440, 2, "blue"),
        ],
        "moving_obstacles": [],
        "timed_traps": [],
    },
    {
        "id": 12,
        "title": "KINETIC STABILITY",
        "player_start": (60, 520),
        "exit_gate": (860, 180),
        # Introduce Yellow tiles: Safe ONLY when the player is continuously moving!
        "rule_change": {"type": "hidden_rule", "rule": "yellow_safe_when_moving", "reveal": "message", "msg": "STAND STILL AND YOU PERISH"},
        "tiles": [
            *generate_platform(0, 560, 3, "blue"),
            # Yellow running track
            *generate_platform(120, 560, 10, "yellow"),
            *generate_platform(520, 560, 4, "blue"),
            *generate_platform(680, 560, 7, "blue"),
            # Platforms
            *generate_platform(200, 440, 3, "yellow"),
            *generate_platform(400, 360, 3, "yellow"),
            *generate_platform(620, 280, 3, "blue"),
            *generate_platform(780, 240, 4, "blue"),
        ],
        "moving_obstacles": [
            {"x": 300, "y": 500, "width": 30, "height": 30, "movement_type": "horizontal", "range": 100, "speed": 200}
        ],
        "timed_traps": [],
    },
    {
        "id": 13,
        "title": "CHROMATIC CONVERGENCE",
        "player_start": (60, 520),
        "exit_gate": (860, 140),
        # Purple deadly + Red safe + Yellow running track + Moving hazards!
        "rule_change": [
            {"type": "swap_colors", "reveal": "silent"},
            {"type": "hidden_rule", "rule": "purple_deadly", "reveal": "subtle", "msg": "EVERY COLOR CARRIES A SECRET"}
        ],
        "tiles": [
            *generate_platform(0, 560, 3, "red"),
            *generate_platform(120, 560, 3, "purple"),
            *generate_platform(240, 560, 3, "red"),
            *generate_platform(360, 560, 3, "blue"),
            *generate_platform(480, 560, 4, "red"),
            *generate_platform(640, 560, 8, "red"),
            # Multi-colored platform staircase
            *generate_platform(140, 450, 2, "red"),
            *generate_platform(280, 370, 2, "purple"), # Trap in disguise!
            *generate_platform(380, 370, 2, "red"),    # Real step
            *generate_platform(520, 290, 3, "red"),
            *generate_platform(720, 210, 4, "red"),
        ],
        "moving_obstacles": [
            {"x": 420, "y": 320, "width": 30, "height": 30, "movement_type": "vertical", "range": 90, "speed": 170}
        ],
        "timed_traps": [
            {"x": 600, "y": 260, "width": 50, "height": 20, "cycle_time": 2.2, "active_time": 1.1}
        ],
    },

    # -------------------------------------------------------------
    # PHASE 5: THE GRAND BREAKDOWN & CHAOS (FINAL LEVELS 14 & 15)
    # -------------------------------------------------------------
    {
        "id": 14,
        "title": "REALITY FRACTURE",
        "player_start": (60, 520),
        "exit_gate": (860, 120),
        # Inverted controls + Glitched text banner + Red is safe + Timed Traps
        "rule_change": [
            {"type": "swap_colors", "reveal": "silent"},
            {"type": "swap_controls", "reveal": "silent"},
            {"type": "glitch_text", "reveal": "message", "msg": "THE DISPLAY LIES TO ITSELF"}
        ],
        "tiles": [
            *generate_platform(0, 560, 3, "red"),
            *generate_platform(120, 560, 3, "blue"),
            *generate_platform(240, 560, 3, "red"),
            *generate_platform(360, 560, 3, "blue"),
            *generate_platform(480, 560, 3, "red"),
            *generate_platform(600, 560, 9, "red"),
            # Complex vertical climb
            *generate_platform(140, 460, 2, "red"),
            *generate_platform(280, 390, 2, "red"),
            *generate_platform(420, 320, 2, "red"),
            *generate_platform(580, 250, 3, "red"),
            *generate_platform(760, 180, 4, "red"),
        ],
        "moving_obstacles": [
            {"x": 220, "y": 420, "width": 25, "height": 25, "movement_type": "circular", "range": 50, "speed": 200},
            {"x": 500, "y": 280, "width": 25, "height": 25, "movement_type": "horizontal", "range": 80, "speed": 180}
        ],
        "timed_traps": [
            {"x": 340, "y": 360, "width": 40, "height": 20, "cycle_time": 2.0, "active_time": 1.0}
        ],
    },
    {
        "id": 15,
        "title": "THE FINAL ILLUSION",
        "player_start": (60, 520),
        "exit_gate": (860, 100),
        # Ultimate test: Red=Safe, Controls Inverted, Purple deadly, constant glitching!
        "rule_change": [
            {"type": "swap_colors", "reveal": "silent"},
            {"type": "swap_controls", "reveal": "silent"},
            {"type": "hidden_rule", "rule": "purple_deadly", "reveal": "silent"},
            {"type": "glitch_text", "reveal": "message", "msg": "NOTHING WAS EVER CERTAIN"}
        ],
        "tiles": [
            *generate_platform(0, 560, 3, "red"),
            *generate_platform(120, 560, 2, "purple"),
            *generate_platform(200, 560, 3, "red"),
            *generate_platform(320, 560, 2, "blue"),
            *generate_platform(400, 560, 3, "red"),
            *generate_platform(520, 560, 2, "purple"),
            *generate_platform(600, 560, 9, "red"),
            # Precision ascending gauntlet
            *generate_platform(120, 460, 2, "red"),
            *generate_platform(260, 390, 2, "purple"), # Fake platform!
            *generate_platform(260, 420, 2, "red"),    # Real lower step
            *generate_platform(400, 340, 2, "red"),
            *generate_platform(560, 260, 2, "red"),
            *generate_platform(720, 180, 4, "red"),
            *generate_platform(820, 140, 3, "red"),
        ],
        "moving_obstacles": [
            {"x": 200, "y": 350, "width": 30, "height": 30, "movement_type": "horizontal", "range": 90, "speed": 190},
            {"x": 480, "y": 220, "width": 30, "height": 30, "movement_type": "vertical", "range": 80, "speed": 180},
            {"x": 660, "y": 240, "width": 25, "height": 25, "movement_type": "circular", "range": 55, "speed": 210}
        ],
        "timed_traps": [
            {"x": 330, "y": 380, "width": 45, "height": 20, "cycle_time": 1.8, "active_time": 0.9},
            {"x": 640, "y": 220, "width": 45, "height": 20, "cycle_time": 2.0, "active_time": 1.0}
        ],
    }
]


def get_level(level_id):
    """Retrieve level data dictionary by 1-based level_id."""
    for lvl in LEVELS:
        if lvl["id"] == level_id:
            return lvl
    return None

def get_total_levels():
    """Return total number of crafted levels."""
    return len(LEVELS)
