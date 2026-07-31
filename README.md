# *This activity has been created as part of the 42 curriculum by `bmanalla` and `jhima`.*

# Pac-Man Game Implementation

A Python/Pygame implementation of the classic Pac-Man game featuring procedurally generated mazes, multiple game levels, autonomous ghost AI, score persistence, and a complete game state system.

---

# Description

This project recreates the classic Pac-Man gameplay while extending it with dynamically generated mazes using the assigned **A-Maze-ing** package.

The objective is to collect all pellets while avoiding ghosts. As the player progresses through levels, new mazes are generated, increasing replayability while preserving the original Pac-Man experience.

Main features include:

- Procedurally generated mazes
- Multiple game levels
- Autonomous ghost AI
- Power pellets and frightened mode
- Persistent Top 10 highscore system
- Menu, pause and game-over state management
- Fallback static maze if the maze generator cannot be loaded
- Cheat mode for testing

---

# Features

- Dynamic maze generation using the assigned `mazegenerator` package
- Seeded first level for reproducible gameplay
- Random maze generation for every following level
- Four autonomous ghosts with different behaviors
- Ghost house generated from the maze's "42" watermark
- Collision detection
- Score tracking
- Extra lives
- Persistent Top 10 highscores
- Complete menu system
- Pause menu
- Game Over screen
- Level progression
- Built-in fallback maze
- Cheat mode for debugging

---

# Instructions

## Requirements

- Python 3.10+
- pygame
- mazegenerator 2.1.0

The provided maze generator is included as:

```
mazegenerator-2.1.0-py3-none-any.whl
```

and must be installed locally.

---

## Installation

Clone the repository and create a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install pygame
pip install ./mazegenerator-2.1.0-py3-none-any.whl
```

Verify that the maze generator is correctly installed:

```bash
python -c "from mazegenerator import MazeGenerator; print('OK')"
```

The command should print:

```
OK
```

---

## Running the Game

```bash
python pacman.py
```

or

```bash
./venv/bin/python pacman.py
```

---

## Controls

| Action | Keys |
|---------|------|
| Move | Arrow Keys / WASD |
| Pause | ESC |
| Navigate Menus | Arrow Keys / W,S |
| Confirm | Enter |
| Cancel | ESC |

### Cheat Mode

| Key | Function |
|-----|----------|
| F1 | Add an extra life |
| F2 | Skip current level |
| F3 | Invincible |
| F4 | FROZEN |
| F5 | SPEED BOOST |

---

# Configuration

The project uses several configurable constants to control gameplay.

These include values such as:

- Window dimensions
- Player speed
- Ghost speed
- Number of lives
- Tile size
- Pellet values
- Power pellet duration
- Frame rate

The first level is generated using a fixed seed to ensure deterministic behaviour during evaluation.

Every subsequent level is generated using a new random seed to improve replayability.

The maze generator itself is configured internally by the provided `mazegenerator` package.

---

# Highscore

The game stores highscores inside:

```
highscores.json
```

Only the **Top 10** scores are preserved.

When a game ends, the player's score is compared with the existing list.

If it belongs in the Top 10, the player is prompted to enter a name.

The list is then:

1. Sorted in descending order.
2. Trimmed to ten entries.
3. Written back to the JSON file.

JSON was chosen because it is:

- Human readable
- Easy to modify
- Lightweight
- Supported directly by Python

---

# Maze Generation

Maze generation is performed using the assigned **A-Maze-ing** package.

The project imports:

```python
from mazegenerator import MazeGenerator
```

The generator creates a valid maze at runtime while embedding the mandatory "42" watermark in its center.

The watermark is reused as the ghost house.

Generation strategy:

- Level 1 uses a fixed seed to guarantee reproducible layouts.
- Every later level generates a new random maze.

If the package cannot be imported or maze generation fails, the game automatically switches to a built-in static maze, ensuring the game remains fully playable.

---

# Implementation

The project follows a modular design where each major responsibility is isolated into its own module.

The implementation includes:

- Event-driven game loop
- Finite game state machine
- Sprite rendering using Pygame
- Tile-based collision detection
- Autonomous ghost movement
- Pellet collection system
- Score management
- Level progression
- Highscore persistence
- Runtime maze generation
- Static maze fallback

The game loop updates:

1. Input
2. Player
3. Ghosts
4. Collisions
5. Rendering

every frame.

---

# General Software Architecture

The project is divided into several logical modules.

```
pacman.py
│
├── Game Loop
├── State Management
├── Rendering
├── Player
├── Ghosts
├── Board
├── Maze Generator
├── Highscores
└── UI
```

### Main Components

**pacman.py**

Entry point containing the primary game loop.

**Board**

Loads generated mazes and handles collision logic.

**Maze Generator**

Interfaces with the provided A-Maze-ing package.

**Player**

Processes movement, collisions and scoring.

**Ghosts**

Implements autonomous ghost behaviour including chase, frightened and respawn states.

**UI**

Draws menus, score display and end screens.

**Highscore Manager**

Loads and stores highscores using JSON.

---

# Project Management

Development was managed collaboratively by both authors.

The work was divided into independent tasks such as:

- Gameplay implementation
- Ghost AI
- Maze integration
- User interface
- Highscore system
- Testing
- Documentation

Git branches and pull requests were used to isolate features before merging into the main branch.

Project planning and progress tracking can be found in:

```
project_management/
```

---

# Resources

### Documentation

- Python Documentation
- Pygame Documentation
- JSON Documentation
- 42 A-Maze-ing package documentation

### References

- https://docs.python.org/3/
- https://www.pygame.org/docs/
- https://www.json.org/json-en.html

### AI Usage

Artificial Intelligence tools (ChatGPT) were used as development assistants for:

- brainstorming implementation ideas
- debugging Python errors
- improving documentation
- explaining algorithms
- reviewing code structure
- refining the README

All architectural decisions, implementation, testing and final code were designed, written and validated by the project authors.

---

# Troubleshooting

If the maze generator cannot be imported, verify:

```bash
python --version
python -c "from mazegenerator import MazeGenerator; print('OK')"
```

If necessary, reinstall the required packages:

```bash
pip install --force-reinstall pygame
pip install --force-reinstall ./mazegenerator-2.1.0-py3-none-any.whl
```

If the issue persists, recreate the virtual environment.

---

# License

This project was developed as part of the **42 School Common Core curriculum**.

It is intended for educational purposes.