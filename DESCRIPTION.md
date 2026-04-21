# Project Description
# Cryptic Combat

## 1. Overview

**Cryptic Combat** is a Python + Pygame action-word roguelike that combines real-time overworld exploration with word-based combat encounters  
Players travel across connected realms, interact with statues tied to mythic factions, and enter battle sequences where solving 5-letter words drives damage output, combo growth, and encounter pacing

The core gameplay loop is:
1. Explore realm maps and locate interactable encounters
2. Enter battle and solve words under limited attempts
3. Build combo streaks to amplify attack damage
4. Collect rewards, manage inventory items, and continue progression
5. Review performance through in-game statistics dashboards

### Target Experience
- Hybrid gameplay between puzzle-solving and RPG combat
- Short, repeatable combat cycles with visible skill expression
- Clear progression through map traversal, enemy tiers, and resource management

### Core Features
- Word-driven combat with feedback-based guess evaluation (green/yellow/gray states)
- Combo-scaling damage model for risk-reward momentum
- Multiple enemy tiers: Follower, Zealot, Apostle, and Boss-avatar encounters
- Realm-based map generation and traversal with boss-realm milestones
- Inventory system with consumables and tactical utility items
- Save-slot support and persistent progression state
- Gameplay statistics logging and in-game chart visualization

---

## 2. Concept

### 2.1 Design Intent
The project is designed around one central question:  
How can word puzzle skill be converted into meaningful combat performance?

Instead of using typing as a passive mini-game, Cryptic Combat maps word-solving quality directly into battle outcomes:
- Faster and cleaner solving improves combat rhythm
- Consecutive success increases combo and burst potential
- Mistakes break momentum and expose the player to counter-damage

This creates a loop where language processing, input precision, and tactical item usage all affect survival

### 2.2 Gameplay Pillars
- **Cognitive Pressure:** The player must solve words while managing combat stakes
- **Mechanical Clarity:** Each guess has explicit color feedback and immediate consequence
- **Momentum Economy:** Combo and damage escalation reward consistency, not randomness
- **Exploration Continuity:** Battles are embedded in overworld progression rather than isolated rounds
- **Data-Driven Reflection:** Session logs are converted into charts for post-run performance review

### 2.3 Technical Concept
The codebase uses a modular `PygameApp` composition approach via mixins. 
This separates concerns such as setup, rendering, event handling, world gameplay flow, save/load logic, and statistics UI while keeping one runtime app controller

---

## 3. UML Class Diagram Details

**Diagram File:** `diagram_uml.pdf`

The UML class diagram documents major classes, responsibilities, and key relationships across gameplay, data, and rendering systems

### 3.1 Main Structural Groups

**Application Orchestration**
- `PygameApp`: central runtime class coordinating state transitions and game loop
- Mixin components:
  - `AppSetupMixin`
  - `EventHandlerMixin`
  - `MenuRenderMixin`
  - `StateRenderMixin`
  - `WorldGameplayMixin`
  - `SaveDataMixin`
  - `StatsInventoryMixin`

**Core Domain Model**
- `Player`
- `Enemy`
- `Boss` (inherits from `Enemy`)
- `GameManager` (combat timing, win checks, and CSV stat buffering)

**Word Mechanics**
- `WordDictionary` (word source and hint retrieval)
- `TileBoard` (guess evaluation and attempt progression)

**Map and World Objects**
- `GameMap`
- `MapObject`
- `TileType`

**Utility / UI Support**
- `SpriteSheet`
- UI constants module (`src/ui/constants.py`)

### 3.2 Relationship Summary
- **Inheritance:** `Boss -> Enemy`; `PygameApp` composes behavior from multiple mixins.
- **Composition/Ownership:** `PygameApp` owns `GameManager`, `WordDictionary`, `TileBoard`, `GameMap`, and active entity instances
- **Dependency:** `WorldGameplayMixin` depends on `Enemy`, `GameMap`, and combat state managed by `PygameApp`
- **Persistence Flow:** `SaveDataMixin` serializes player/session state and coordinates file-backed save slots
- **Analytics Flow:** `GameManager` records per-word combat metrics and exports to CSV; `StatsInventoryMixin` reads these metrics for in-game visualization

### 3.3 Diagram Scope and Current Status
- The current UML emphasizes class responsibility and runtime interaction points
- Detailed per-method signatures are partially represented and may evolve during refactor
- Some implementation details in mixin internals may be simplified in the diagram for readability

---

## 4. YouTube Presentation

**Status:** Unfinished

The project presentation video is not finalized yet  
This section will be updated with the final link and summary once recording and editing are complete.

---

## 5. Current Deliverable Status

- Project implementation: In active development
- DESCRIPTION document: Completed (this version)
- UML class diagram: Draft available (`diagram_uml.pdf`), ongoing refinement
- YouTube presentation: Unfinished
