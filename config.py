"""Configuration constants for Chroma Lie game."""

# Screen settings
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
WINDOW_TITLE = "Chroma Lie"

# Colors (modern neon palette on dark background)
BG_COLOR = (18, 20, 28)           # Dark navy background
RED_DANGER = (255, 59, 92)        # Neon red #ff3b5c
BLUE_SAFE = (46, 196, 255)        # Neon blue #2ec4ff
PLAYER_COLOR = (255, 255, 255)    # White player with glow
EXIT_GATE_COLOR = (100, 255, 150) # Green-ish exit gate
PARTICLE_COLORS = [RED_DANGER, BLUE_SAFE, (255, 200, 50), (200, 100, 255)]
TEXT_COLOR = (240, 240, 250)
TEXT_GLOW_COLOR = (80, 80, 120)
HUD_COLOR = (200, 200, 220)
GRID_COLOR = (40, 45, 60)
OBSTACLE_COLOR = (255, 120, 120)
TIMED_TRAP_ACTIVE = (255, 59, 92)
TIMED_TRAP_INACTIVE = (60, 60, 90)
PURPLE_TILE = (180, 80, 255)
YELLOW_TILE = (255, 220, 60)

# Player physics
PLAYER_SIZE = 28
PLAYER_SPEED = 350.0          # pixels per second
PLAYER_JUMP_FORCE = -550.0    # negative = up
GRAVITY = 1200.0
FRICTION = 0.85
DASH_SPEED = 800.0
DASH_DURATION = 0.15
DASH_COOLDOWN = 1.0

# Tile settings
TILE_SIZE = 40

# Glitch effect settings
GLITCH_DURATION = 0.4         # seconds
GLITCH_INTENSITY = 8          # pixel offset for chromatic aberration
CAMERA_SHAKE_DURATION = 0.3
CAMERA_SHAKE_INTENSITY = 6

# Game settings
DEATH_PARTICLE_COUNT = 30
DEATH_PARTICLE_LIFETIME = 0.8
LEVEL_TRANSITION_DELAY = 0.5

# Font settings
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 32
FONT_SIZE_SMALL = 20
FONT_NAME = None  # None = system default, or path to .ttf file