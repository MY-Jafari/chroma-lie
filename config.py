"""
config.py - every tunable constant of Chroma Lie lives here.
Change resolution, colors, physics or timings without touching game code.
"""

TITLE = "Chroma Lie"

# ---------------------------------------------------------------- display
WIDTH, HEIGHT = 960, 640      # logical resolution (the game is scaled to fit the monitor)
FPS = 60
FULLSCREEN = True             # F11 toggles at runtime
VSYNC = True

TILE = 32
COLS, ROWS = WIDTH // TILE, HEIGHT // TILE   # 30 x 20 grid

# ---------------------------------------------------------------- palette
BG = (18, 20, 28)             # #12141c
BG_GRID = (28, 32, 46)
BG_GRID_MAJOR = (36, 41, 60)
RED = (255, 59, 92)           # #ff3b5c
BLUE = (46, 196, 255)         # #2ec4ff
PURPLE = (184, 77, 255)       # #b84dff
NEUTRAL = (52, 58, 80)
NEUTRAL_EDGE = (104, 114, 150)
MOTION = (60, 232, 176)
HAZARD = (255, 168, 48)       # amber = ALWAYS deadly (obstacles, lasers, spikes)
EXIT = (120, 255, 200)
PLAYER = (236, 242, 255)
TEXT = (232, 236, 248)
TEXT_DIM = (122, 130, 158)
PANEL = (24, 27, 38)
PANEL_EDGE = (58, 64, 88)

COLOR_OF_TILE = {"R": RED, "B": BLUE, "P": PURPLE}

# ---------------------------------------------------------------- physics (pixels / seconds)
PLAYER_SIZE = 24
GRAVITY = 2000.0
MAX_FALL = 900.0
MOVE_SPEED = 260.0
GROUND_ACCEL = 2600.0
AIR_ACCEL = 1900.0
GROUND_FRICTION = 3200.0
JUMP_VELOCITY = 720.0         # ~4 tiles high, ~5.8 tiles far
JUMP_CUT = 0.45               # releasing jump early cuts the rise (variable jump height)
COYOTE_TIME = 0.10            # can still jump shortly after leaving a ledge
JUMP_BUFFER = 0.12            # jump pressed slightly before landing still counts
SPRING_VELOCITY = 1050.0
FALL_DEATH_Y = HEIGHT + 60

# ---------------------------------------------------------------- rules & traps
RULE_GRACE = 0.35             # after a rule change colored tiles wait this long before killing
MOTION_FUSE = 0.30            # seconds you may stand still on a motion tile
MOTION_MIN_SPEED = 40.0
LATE_TRAP_FUSE = 0.35         # late-trap tiles collapse this long after the first touch
TRAP_WARNING = 0.45           # timed lasers blink this long before switching on
GLITCH_DURATION = 0.40
MESSAGE_TIME = 2.2

# ---------------------------------------------------------------- flow
DEATH_RESET_DELAY = 0.40      # death burst plays, then the level resets instantly
WIN_DELAY = 0.75
INTRO_TIME = 2.2
SPARK_RATE = 1.3              # sparks / second / deadly tile  (the honest tell!)

SAVE_FILE = "chroma_lie_save.json"

# ---------------------------------------------------------------- audio (synthesized in memory, no asset files)
SFX_VOLUME = 0.7              # master volume for sound effects
AMBIENT_VOLUME = 0.35         # volume of the soft lab drone (looping)

