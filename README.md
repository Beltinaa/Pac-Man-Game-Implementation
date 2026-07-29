# Pac-Man Game Implementation

A Python/Pygame Pac-Man clone with a full menu/pause/game-over state
machine, multi-level play (level 1 uses a fixed seed, every level after
is freshly randomly generated), autonomous ghost  (chase, flee, and
eaten-ghost respawn), and a persisted Top 10 highscores list.

The maze itself is generated at runtime by the assigned "A-Maze-ing"
package (`mazegenerator`), which stamps a "42" watermark into the middle
of every generated maze and doubles as the ghost house. If the generator
can't be used for any reason, the game falls back to a small built-in
static maze instead of crashing.

## Requirements

- **Python 3.10 or newer.** The assigned `mazegenerator` package uses
  modern type-hint syntax (`str | bool`) that only runs on 3.10+.
  On an older Python, `mazegenerator` fails to import and the game
  silently falls back to the static maze — it still runs, but you won't
  see the "42" logo or the dynamically generated corners.
- `pygame`
- `mazegenerator==2.1.0` (bundled in this repo as
  `mazegenerator-2.1.0-py3-none-any.whl`; it isn't on PyPI, so it must be
  installed from that local wheel)

## Setup

Run these from the repository root. `venv/` is gitignored, so this needs
to be redone on every machine you clone the repo onto.

```bash
# 1. Make sure you have Python 3.10+. On macOS via Homebrew:
brew install python@3.11

# 2. Create a virtual environment with that Python (adjust the path if
#    your Python 3.10+ lives somewhere else, e.g. `python3.11` on Linux)
/opt/homebrew/bin/python3.11 -m venv venv

# 3. Install dependencies into that venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install pygame
./venv/bin/pip install ./mazegenerator-2.1.0-py3-none-any.whl
```

On Linux, swap step 1 for however you install Python 3.10+ there
(`apt install python3.11`, `pyenv install 3.11`, etc.); steps 2-3 are the
same. On Windows, the venv's executable is `venv\Scripts\python.exe`
instead of `./venv/bin/python3`.

## Running the game

Always launch with the venv's own Python, not the system `python3` —
that's the most common way to accidentally end up on the static fallback
maze instead of the generated one:

```bash
./venv/bin/python3 pacman.py
```

## Controls

- **Move:** Arrow keys or WASD
- **Pause / Resume:** Esc
- **Menus:** Up/Down (or W/S) to navigate, Enter to select, Esc to go back
- **Highscore name entry:** type your name, Enter to save, Esc to skip

## Notes

- `highscores.json` persists the Top 10 scores across runs — don't
  delete it if you want to keep your scores.
- If you ever see `[board] Maze generator failed (...)` printed on
  startup, you're on the static fallback maze — double-check you're
  running with a Python 3.10+ venv per the Setup section above.
