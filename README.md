# Project Name

Cryptic Combat

# Project Description

Cryptic Combat is a Python + Pygame word-combat roguelike where the player explores connected realms, fights myth-themed enemies through word guessing, manages items, and progresses through battle rewards and map traversal

# Installation / Running Guide

## Requirements

- Python 3.12 or newer recommended
- `pip`
- A desktop environment that supports Pygame windows and audio

## Windows

1. Open PowerShell in the project root
2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Run the game:

```powershell
python main.py
```

## Mac

1. Open Terminal in the project root.
2. Create a virtual environment:

```bash
python3 -m venv .venv
```

3. Activate the virtual environment:

```bash
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the game:

```bash
python3 main.py
```

# Tutorial / Usage

## Basic Controls

- `Mouse`: click menu buttons and UI panels
- `E`: open or close inventory and statistics
- `ESC`: pause, close overlays, or back out of menus
- `WASD` or arrow keys: move in the overworld
- `SPACE`, `ENTER`, or `F`: interact with nearby objects
- `1-5`: use hotbar items

## Battle Flow

1. Approach a statue or enemy encounter in the overworld.
2. Start a battle interaction.
3. Type a 5-letter guess and press `ENTER`.
4. Correct guesses deal damage and build combo.
5. Wrong sequences can cause enemy counterattacks.
6. Use potions and hint scrolls when needed.

## Inventory / Stats

- Press `E` to open the inventory and statistics panel.
- Click charts to expand them.
- Click `Summarize` to open the summary dashboard overlay.

# Game Features

- Word-based battle system integrated with RPG combat
- Combo-based damage scaling
- Overworld exploration across multiple realms
- Boss, Apostle, Zealot, and Follower enemy tiers
- Inventory with consumables such as potions, hint scrolls, and warp scrolls
- Statistics dashboard for gameplay performance
- Character appearance selection system
- Merchant shop and upgrade rewards
- Save slot and realm progression support
- Map editor support through `map_editor.py`

# File Structure

```text
cryptic_combat/
|-- assets/
|   |-- images/
|   `-- sounds/
|-- data/
|   |-- raw/
|   |-- session/
|   |-- slots/
|   `-- words/
|-- docs/
|-- src/
|   |-- app/
|   |   |-- app_setup_mixin.py
|   |   |-- event_handler_mixin.py
|   |   |-- game_app.py
|   |   |-- menu_render_mixin.py
|   |   |-- save_data_mixin.py
|   |   |-- state_render_mixin.py
|   |   |-- stats_inventory_mixin.py
|   |   `-- world_gameplay_mixin.py
|   |-- ui/
|   |   |-- constants.py
|   |   `-- spritesheet.py
|   |-- config.py
|   |-- entities.py
|   |-- game_manager.py
|   |-- map_loader.py
|   `-- mechanics.py
|-- main.py
|-- map_editor.py
|-- README.md
`-- requirements.txt
```

## Structure Notes

- `main.py` is the entry point used to launch the game.
- `src/app/game_app.py` assembles the main `PygameApp`.
- `src/app/` contains gameplay and UI behavior split by responsibility.
- `src/ui/` contains shared UI constants and rendering helpers.
- `src/game_manager.py`, `src/mechanics.py`, and `src/entities.py` contain core gameplay systems.
- `data/` contains words, saves, generated sessions, and gameplay logs.

# Known Bugs

- No formal bug tracker is maintained in this repository yet.
- During ongoing refactor work, minor UI alignment issues may still appear in some overlays or menus depending on state transitions.

# Unfinished Works

- Codebase modularization is still in progress. `game_app.py` is already much smaller, but some logic can still be separated further into smaller state-specific modules if needed.

# External Sources

- Assets: Gemini, Kenny.nl, MidJourney
- Sounds: Suno.ai
