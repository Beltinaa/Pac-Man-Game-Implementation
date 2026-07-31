# *This activity has been created as part of the 42 curriculum by `bmanalla` and `jhima`.*

# Pac-Man Game Implementation

A Python/Pygame implementation of the classic **Pac-Man** game featuring procedurally generated mazes, multiple levels, autonomous ghost AI, persistent highscores, and a complete game state system.

The project combines the classic Pac-Man gameplay with dynamically generated mazes using the assigned **A-Maze-ing** package while maintaining the original mechanics of collecting pellets, avoiding ghosts, and progressing through increasingly challenging levels.

---

# Description

This project recreates the classic Pac-Man experience while extending it with procedural maze generation.

The objective of the game is to guide Pac-Man through each maze, collect every pellet, avoid ghosts, and advance through progressively generated levels. The first level uses a deterministic maze generated from a fixed seed to ensure reproducibility, while every subsequent level generates a new maze to increase replayability.

The project demonstrates object-oriented programming, event-driven game development with Pygame, procedural content generation, persistent data storage, and modular software design.

## Main Features

* Procedurally generated mazes using the assigned **A-Maze-ing** package
* Fixed seed for the first level
* Random maze generation for subsequent levels
* Autonomous ghost AI
* Power pellets and frightened ghost mode
* Ghost respawn system
* Multiple game levels
* Persistent Top 10 highscores
* Menu, pause and game-over screens
* Built-in fallback maze when maze generation fails
* Cheat mode for testing and debugging

---

# Gameplay

The player controls Pac-Man and must collect every pellet within the maze while avoiding ghosts.

Power pellets temporarily place ghosts into a frightened state, allowing Pac-Man to eat them for additional points.

Once all pellets have been collected, the game advances to the next level, generating a new maze.

The game ends when the player loses all available lives.

---

# Features

* Dynamic maze generation
* Seeded and random maze support
* Four autonomous ghosts
* Ghost house generated from the maze's "42" watermark
* Collision detection
* Score tracking
* Extra lives
* Persistent Top 10 highscores
* Complete menu system
* Pause functionality
* Level progression
* Game Over screen
* Static maze fallback
* Cheat mode

---

# Instructions

## Requirements

* Python 3.10 or newer
* pygame
* mazegenerator 2.1.0

The required maze generator is included in this repository as:

```
mazegenerator-2.1.0-py3-none-any.whl
```

Since the package is not available on PyPI, it must be installed locally.

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

Verify the installation:

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

| Action         | Keys              |
| -------------- | ----------------- |
| Move           | Arrow Keys / WASD |
| Pause / Resume | ESC               |
| Navigate Menus | Arrow Keys / W,S  |
| Select         | Enter             |
| Cancel         | ESC               |

### Cheat Mode

| Key | Function      |
| --- | ------------- |
| F1  | Extra Life    |
| F2  | Skip Level    |
| F3  | Invincibility |
| F4  | Freeze Ghosts |
| F5  | Speed Boost   |

---

# Configuration

The game behaviour is controlled through configuration constants defined within the project source code.

The default configuration includes values such as:

| Parameter             | Purpose                  | Default         |
| --------------------- | ------------------------ | --------------- |
| Window Size           | Game window resolution   | 1000 × 950      |
| Tile Size             | Size of each maze tile   | 25 px           |
| Initial Lives         | Player starting lives    | 3               |
| FPS                   | Target frame rate        | 60              |
| Player Speed          | Pac-Man movement speed   | Project default |
| Ghost Speed           | Ghost movement speed     | Project default |
| Pellet Score          | Normal pellet points     | Project default |
| Power Pellet Duration | Frightened mode duration | Project default |

Maze generation follows the following configuration strategy:

* **Level 1** uses a fixed random seed to produce the same maze every execution.
* **Levels 2 and above** generate a completely new random maze.
* The provided **A-Maze-ing** package internally handles maze dimensions, path validity, and placement of the required "42" watermark.

If maze generation fails or the package cannot be imported, the application automatically loads a built-in fallback maze to ensure uninterrupted gameplay.

---

# Highscore

The highscore system stores game results inside:

```
highscores.json
```

After every completed game, the player's score is compared against the existing Top 10 scores.

If the score qualifies, the player is prompted to enter a name.

The program then:

1. Inserts the new score.
2. Sorts all scores in descending order.
3. Keeps only the highest ten entries.
4. Saves the updated list back to `highscores.json`.

JSON was chosen because it is lightweight, human-readable, portable, and directly supported by Python's standard library without requiring additional dependencies.

---

# Maze Generation

Maze generation is performed using the assigned **A-Maze-ing** package.

The game imports the generator through:

```python
from mazegenerator import MazeGenerator
```

The generator is responsible for:

* Creating a valid random maze.
* Ensuring that every generated maze is solvable.
* Embedding the required **"42"** watermark in the center of the maze.
* Producing a different maze whenever a new random seed is used.

The project uses the generated **"42"** watermark as the ghost house, integrating the mandatory maze feature directly into gameplay.

To ensure deterministic testing, the first level always uses the same fixed seed.

Every subsequent level generates a new maze using a different seed, increasing replayability while maintaining valid layouts.

If the maze generator cannot be imported or generation fails, the game automatically falls back to a predefined static maze, allowing gameplay to continue without interruption.

---

# Implementation

The project follows a modular, object-oriented architecture.

The implementation includes:

* Event-driven game loop
* Finite state machine for menus and gameplay
* Tile-based movement and collision detection
* Sprite rendering using Pygame
* Autonomous ghost AI
* Frightened and respawn ghost states
* Pellet and power pellet handling
* Runtime maze generation
* Persistent score management
* JSON serialization for highscores
* Static maze fallback

Each frame performs the following sequence:

1. Process user input.
2. Update the game state.
3. Move Pac-Man.
4. Update ghost behaviour.
5. Detect collisions.
6. Update scores and lives.
7. Render the current frame.

---

# General Software Architecture

The project is divided into independent modules, each responsible for a specific part of the application.

```
pacman.py
│
├── Game Loop
├── State Manager
├── Board
├── Maze Generator
├── Player
├── Ghost Manager
├── Highscore Manager
├── UI
└── Rendering
```

## Module Overview

### pacman.py

Application entry point containing the main game loop.

### Board

Creates and manages the playable maze, tile collisions, pellets, and level loading.

### Maze Generator

Interfaces with the provided **A-Maze-ing** package and handles fallback behaviour if maze generation fails.

### Player

Controls Pac-Man movement, collisions, scoring, and lives.

### Ghost Manager

Controls ghost movement, AI behaviour, frightened mode, collisions, and respawning.

### UI

Displays menus, score information, pause screens, level transitions, and game-over screens.

### Highscore Manager

Loads, updates, sorts, and saves the persistent Top 10 highscores.

---

# Project Management

The project was developed collaboratively by **bmanalla** and **jhima**.

Development was organised by dividing the work into separate implementation tasks, including gameplay mechanics, ghost behaviour, maze integration, user interface, score management, testing, debugging, and documentation.

Git branches were used to develop features independently before merging them into the main branch.

Project planning, task organisation, and development history are documented in the project's management directory:

```
project_management/
```

---

# Resources

## Documentation

* Python Documentation
* Pygame Documentation
* JSON Documentation
* A-Maze-ing Package Documentation

## References

* https://docs.python.org/3/
* https://www.pygame.org/docs/
* https://www.json.org/json-en.html

## AI Usage

Artificial Intelligence tools were used exclusively as development assistants.

**ChatGPT** was used for:

* explaining Python concepts
* debugging implementation issues
* discussing algorithms
* improving documentation
* reviewing software architecture
* refining the README
* generating development suggestions

All software design decisions, gameplay mechanics, architecture, implementation, testing, debugging, and final code were completed, reviewed, and validated by the project authors.

---

# Troubleshooting

If the generated maze does not appear or the game reports that the maze generator failed, verify the installation:

```bash
python --version
python -c "from mazegenerator import MazeGenerator; print('OK')"
```

If necessary, reinstall the required packages:

```bash
pip install --force-reinstall pygame
pip install --force-reinstall ./mazegenerator-2.1.0-py3-none-any.whl
```

If the issue persists, recreate the virtual environment and reinstall all dependencies.

---

# License

This project was developed as part of the **42 School Common Core curriculum** and is intended exclusively for educational purposes.
