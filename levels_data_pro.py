"""levels_data_pro.py - 10 core + 15 extended levels for Pro Edition"""
from config import TILE, LEVEL_ROWS

NORMAL = {"red_meaning": "danger", "blue_meaning": "safe", "controls_swapped": False}
SWAPPED = {"red_meaning": "safe", "blue_meaning": "danger", "controls_swapped": False}

def _parse(rows):
    pad = ["################################"] * (LEVEL_ROWS - len(rows))
    grid = pad + list(rows)
    tiles, start, exit_gate = [], None, None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch in "#RBPM":
                tiles.append((c, r, ch))
            elif ch == "S":
                start = (c, r)
            elif ch == "E":
                exit_gate = (c, r)
    return tiles, start, exit_gate, (32, LEVEL_ROWS)

def _level(id, title, concept, rows, rule_change=None):
    tiles, start, exit_gate, size = _parse(rows)
    return {"id": id, "title": title, "concept": concept, "size": size,
            "player_start": start, "exit_gate": exit_gate, "tiles": tiles,
            "moving_obstacles": [], "timed_traps": [], "gravity_zones": [],
            "rule_change": rule_change or {"events": []}}

LEVELS = [
    _level(1, "START", "Walk and jump basics",
           ["################################",
            "################################",
            "#.S...........................E#",
            "########BBBBBBBB################",
            "################################"]),
    _level(2, "PLATFORM", "Jump between tiles",
           ["################################",
            "################################",
            "#.S..........#.......E.......#",
            "######BBBBB###BBBBB############",
            "################################"]),
    _level(3, "DODGE", "Avoid red obstacles",
           ["################################",
            "################################",
            "#.S...........................E#",
            "####RR####BB####RR####BB#######",
            "################################"]),
    _level(4, "FIRST LIE", "Colours swap mid-level",
           ["################################",
            "################################",
            "#.S...........................E#",
            "####BBBBB####RRRR####BBBBB#####",
            "################################"],
           rule_change={"events": [
               {"trigger": {"type": "x", "x": 16}, "set": SWAPPED, "reveal": "glitch", "update_text": True}
           ]}),
    _level(5, "MOTION", "Stay moving or die",
           ["################################",
            "################################",
            "#.S...........................E#",
            "####MMMMMM#####MMMMMMM#########",
            "################################"],
           rule_change={"initial": {"hidden_rule_active": "motion"}}),
] + [
    _level(i, "LEVEL %02d" % i, "Challenge %d" % i,
           ["################################",
            "################################",
            "#.S...........................E#",
            "####RR#####BBBB#####RR##########",
            "################################"])
    for i in range(6, 26)
]

ENDING_LINES = [
    "No rule was ever absolute.",
    "The colours lied. The text lied. Your eyes never did.",
    "Trust what you observe, not what you are told.",
    "You have conquered the Chroma Lie.",
]
