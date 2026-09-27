# Chroma Lie

**A 2D puzzle-action platformer where the rules deceive you.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Pygame](https://img.shields.io/badge/pygame-2.x-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## Overview

Chroma Lie is a psychological platformer about trust, observation, and adaptation. The game teaches you a simple rule:

> **RED = DANGER** • **BLUE = SAFE**

Then it systematically breaks that rule — silently, without warning. Colors swap meanings, controls invert, and entirely new hidden mechanics emerge. Your only tool is careful observation and experimentation.

**15 handcrafted levels** across 5 phases of escalating deception.

---

## Installation

### Requirements
- Python 3.10+
- pygame 2.x

### Quick Start
```bash
# Clone and install dependencies
git clone https://github.com/your-repo/chroma-lie.git
cd chroma-lie

# Install pygame
pip install pygame

# Run the game
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| **← / →** or **A / D** | Move left / right |
| **SPACE** / **W** / **↑** | Jump |
| **SHIFT** | Dash (short burst of speed) |
| **R** | Quick restart current level |
| **ESC** | Return to menu |

> **Warning:** Controls may be inverted without notice. Watch your movement.

---

## Gameplay

### Core Mechanics
- **Color Tiles**: Red and blue tiles cover the levels. Stepping on a "danger" color = instant death.
- **Moving Obstacles**: Always lethal. Dodge or time your jumps.
- **Timed Traps**: Blink before activating. Learn their rhythm.
- **Exit Gate**: Green pulsing gate. Always safe. Reach it to advance.

### The Deception System
The game lies to you through multiple channels:

| Deception Type | Effect |
|----------------|--------|
| **Color Swap** | Red becomes safe, Blue becomes deadly (or vice versa) |
| **Control Inversion** | Left/right inputs are swapped |
| **Hidden Rules** | New tile types (Purple, Yellow) with secret behaviors |
| **Text Glitch** | The on-screen rule display itself corrupts |

> **Critical**: The rule banner at the top *may* still show the original "RED = DANGER" text even when it's false. Trust your eyes, not the UI.

---

## Level Progression

### Phase 1: Baseline (Levels 1–3)
Learn the honest rules. Red kills, blue saves. Basic platforming.

### Phase 2: First Lies (Levels 4–6)
Color meanings flip. The display still claims the old rule. Timed traps appear.

### Phase 3: Motor Betrayal (Levels 7–10)
Controls invert. Colors may or may not be swapped. Moving obstacles hunt you.

### Phase 4: Unwritten Laws (Levels 11–13)
**Purple tiles** appear — never mentioned, always lethal.
**Yellow tiles** appear — safe *only while moving*. Stand still, you die.
All previous deceptions combine.

### Phase 5: Total Breakdown (Levels 14–15)
Everything changes constantly. Controls inverted, colors swapped, glitched text, hidden rules active simultaneously. Pure observation and reflex.

---

## Visual Features

- **CRT Scanlines & Chromatic Aberration**: Authentic digital glitch aesthetic
- **Camera Shake**: Reactive feedback on death, rule changes, level complete
- **Particle Systems**: Death explosions, movement trails, ambient atmosphere
- **Neon Glow Typography**: Rule banner and HUD with pulsing glow effects
- **Scrolling Background Grid**: Subtle depth without visual noise

---

## Project Structure

```
chroma-lie/
├── main.py           # Game loop, state management, input handling
├── config.py         # Constants: colors, physics, screen, timing
├── player.py         # Player physics, movement, collision, death FX
├── level.py          # Tile, Obstacle, Trap, ExitGate, Level classes
├── levels_data.py    # 15 handcrafted level definitions
├── deception.py      # Core deception engine: rule swaps, hidden mechanics
├── effects.py        # Camera shake, glitch renderer, particles, grid
├── ui.py             # HUD, menus, narrative screens, glow text
└── README.md         # This file
```

---

## Design Philosophy

> *"The only constant is that there are no constants."*

- **No hand-holding**: Death is instant. Restart is immediate. Rhythm is preserved.
- **Fair deception**: Every lie has a visual or behavioral tell. The game is solvable by observation.
- **Minimalist UI**: No health bars, no score, no clutter. Only the rule banner, level number, and death count.
- **Narrative through mechanics**: The story is told by what the game *does*, not text dumps.

---

## Development

### Running in Dev Mode
```bash
python main.py
```

### Adding Levels
Edit `levels_data.py` — each level is a dictionary with:
- `id`, `title`, `player_start`, `exit_gate`
- `tiles[]` — static or timed color tiles
- `moving_obstacles[]` — patrolling/killer objects
- `timed_traps[]` — blinking hazard zones
- `rule_change` — deception script for this level

### Extending Deceptions
Add new hidden rule types in `deception.py` → `DeceptionManager.get_tile_safety()` and register in `levels_data.py`.

---

## License

MIT License — Free to use, modify, and distribute.

---

## Credits

Developed as a **Claude Code** project.  
Built with **Python** + **Pygame-ce**.

---

*"You survived not by obeying instructions, but by questioning every single certainty."*