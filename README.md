# Pac-Man Game Implementation

A Python/Pygame Pac-Man clone with a full menu/pause/game-over state
machine, multi-level play (level 1 uses a fixed seed, every level after
is freshly randomly generated), autonomous ghost behavior (chase, flee,
and eaten-ghost respawn), and a persisted Top 10 highscores list.

The maze itself is generated at runtime by the assigned "A-Maze-ing"
package (`mazegenerator`), which stamps a "42" watermark into the middle
of every generated maze and doubles as the ghost house. If the generator
can't be used for any reason, the game falls back to a small built-in
static maze instead of crashing.

## Requirements

- **Python 3.10 or newer** (any 3.10+ works — 3.11, 3.14, whatever you
  have). The assigned `mazegenerator` package uses modern type-hint
  syntax (`str | bool`) that only runs on 3.10+. On an older Python,
  `mazegenerator` fails to import and the game silently falls back to
  the static maze — it still runs, but you won't see the "42" logo or
  the dynamically generated corners.
- `pygame`
- `mazegenerator==2.1.0` (bundled in this repo as
  `mazegenerator-2.1.0-py3-none-any.whl`; it isn't on PyPI, so it must be
  installed from that local wheel)

## Setup

Run these from the repository root. `venv/` is gitignored, so this needs
to be redone on every machine you clone the repo onto.

```bash
python3 --version                 # confirm it's 3.10+ before continuing

python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows

python --version                  
pip install --upgrade pip
pip install pygame
pip install ./mazegenerator-2.1.0-py3-none-any.whl

# Verify the generator actually imports before trying to launch the game
python -c "from mazegenerator import MazeGenerator; print('OK')"
```

That last line must print `OK` with no traceback. If it doesn't, see
Troubleshooting below before moving on.

## Running the game

With the venv activated:

```bash
python pacman.py
```

or, without activating, by calling the venv's Python directly:

```bash
./venv/bin/python3 pacman.py       # venv\Scripts\python.exe on Windows
```

Either way, watch the very first lines printed to the terminal. If you
see:

```
[board] Maze generator failed (...); using built-in fallback maze.
```

...you're on the static fallback maze, not the generated one — go to
Troubleshooting.

## Controls

- **Move:** Arrow keys or WASD
- **Pause / Resume:** Esc
- **Menus:** Up/Down (or W/S) to navigate, Enter to select, Esc to go back
- **Highscore name entry:** type your name, Enter to save, Esc to skip

## Troubleshooting

**`[board] Maze generator failed (...)` at startup, or the maze has no
"42" logo.** This means `import mazegenerator` failed inside whichever
Python actually ran `pacman.py`. Run the two checks below with the venv
activated:

```bash
python --version
python -c "from mazegenerator import MazeGenerator; print('OK')"
```

- If `python --version` is below 3.10, you're on too old a Python for
  the assigned package — rebuild the venv against a newer `python3.x`.
- If the version is fine but the import still fails (commonly
  `ModuleNotFoundError: No module named 'mazegenerator'`), `pip` and
  `python` are very likely resolving to two different environments —
  especially confusing when `pip install ./mazegenerator...whl` reports
  *"already installed with the same version... use --force-reinstall"*
  while the import still fails. That message means pip's own bookkeeping
  is stale, not that the package is actually usable. Force it:

  ```bash
  pip install --force-reinstall pygame
  pip install --force-reinstall ./mazegenerator-2.1.0-py3-none-any.whl
  python -c "from mazegenerator import MazeGenerator; print('OK')"
  ```

- If it *still* fails after `--force-reinstall`, stop patching and
  rebuild the venv from scratch — this fully resets whatever's
  inconsistent about its state:

  ```bash
  deactivate
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  python --version
  pip install --upgrade pip
  pip install pygame
  pip install ./mazegenerator-2.1.0-py3-none-any.whl
  python -c "from mazegenerator import MazeGenerator; print('OK')"
  ```

## Notes

- `highscores.json` persists the Top 10 scores across runs — don't
  delete it if you want to keep your scores.
