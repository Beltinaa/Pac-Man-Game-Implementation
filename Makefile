# The assigned mazegenerator wheel annotates with PEP 604 unions ("str | bool",
# see its mazegenerator.py lines 26 and 35). Those are evaluated at runtime, so
# the package only imports on Python 3.10+. It ships no Requires-Python, so pip
# installs it happily on an older interpreter and it then fails at import with
# "unsupported operand type(s) for |". macOS's own /usr/bin/python3 is 3.9, so
# pick the newest interpreter on PATH rather than whatever "python3" resolves
# to. Override explicitly with: make install PYTHON_BIN=/path/to/python3.12
# Version choice also decides whether you get SOUND. pygame publishes
# prebuilt wheels (which bundle SDL_mixer, SDL_image and friends) only for
# the Python versions it was released against -- 2.6.1 covers 3.9 to 3.13.
# On anything newer, pip has no wheel to install, falls back to compiling
# pygame from source, and quietly omits every optional module whose C
# headers are absent on the machine. That is how you end up with a working
# pygame that raises "mixer module not available": nothing failed loudly,
# the build just skipped audio. So prefer a version with wheels, and only
# fall back to a bare "python3" if none of them is installed.
PYTHON_BIN ?= $(shell for p in python3.13 python3.12 python3.11 python3.10 python3; do \
                  command -v $$p >/dev/null 2>&1 && echo $$p && break; done)
MIN_PYTHON := import sys; sys.exit(sys.version_info < (3, 10))
HAS_MIXER  := import pygame; pygame.mixer
VENV       := venv
PYTHON     := $(VENV)/bin/python3
PIP        := $(VENV)/bin/pip
MAZEGEN_WHEEL := mazegenerator-2.1.0-py3-none-any.whl

# Which pygame distribution to install. "pygame-ce" is a drop-in fork that
# still imports as `pygame`; it publishes wheels for newer Python versions
# than upstream pygame does, so it is the way to get working audio on a
# machine that only has a very recent interpreter:
#     make fclean && make install PYGAME_PKG=pygame-ce
PYGAME_PKG ?= pygame

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs
SKIP_FLAKE8 ?= 0
SKIP_MYPY ?= 0

.PHONY: install run debug clean fclean lint lint-strict check-audio

install:
	@$(PYTHON_BIN) -c '$(MIN_PYTHON)' || { \
		echo "$(PYTHON_BIN) is not usable, but the maze generator needs Python 3.10+."; \
		echo "See what you have:   ls /usr/bin/python3.*"; \
		echo "then:                make install PYTHON_BIN=<one of them>"; \
		exit 1; }
	@if [ -x $(PYTHON) ] && ! $(PYTHON) -c '$(MIN_PYTHON)'; then \
		echo "existing $(VENV) is `$(PYTHON) -V 2>&1` -- too old, recreating it"; \
		rm -rf $(VENV); \
	fi
	$(PYTHON_BIN) -m venv $(VENV)
	$(PIP) install --upgrade pip
	@# --only-binary refuses to compile pygame from source. A source build
	@# succeeds while silently dropping audio, so failing here is the more
	@# useful outcome: it tells you to pick a different interpreter instead
	@# of leaving you with a mysteriously silent game.
	@$(PIP) install --only-binary=:all: $(PYGAME_PKG) || { \
		echo ""; \
		echo "No prebuilt $(PYGAME_PKG) wheel for `$(PYTHON) -V 2>&1`."; \
		echo "Building from source would work but would come out WITHOUT SOUND."; \
		echo "Either use an interpreter that has wheels (ls /usr/bin/python3.*):"; \
		echo "    make fclean && make install PYTHON_BIN=python3.12"; \
		echo "or use the drop-in fork, which ships wheels for newer Pythons:"; \
		echo "    make fclean && make install PYGAME_PKG=pygame-ce"; \
		echo ""; \
		exit 1; }
	$(PIP) install flake8 mypy
	$(PIP) install ./$(MAZEGEN_WHEEL)
	@$(MAKE) --no-print-directory check-audio

# Reports whether this install can play sound, and what to do if not.
check-audio:
	@if $(PYTHON) -c '$(HAS_MIXER)' 2>/dev/null; then \
		echo "audio: OK -- pygame has the mixer module"; \
	else \
		echo "audio: MISSING -- this pygame has no mixer module, the game will be silent."; \
		echo "  This pygame was compiled from source without SDL_mixer, which happens"; \
		echo "  when no wheel exists for `$(PYTHON) -V 2>&1`."; \
		echo "  Fix without root by using an interpreter that has wheels:"; \
		echo "      make fclean && make install PYTHON_BIN=python3.12"; \
		echo "  If no such interpreter is installed, use the drop-in fork:"; \
		echo "      make fclean && make install PYGAME_PKG=pygame-ce"; \
	fi

run:
	$(PYTHON) pacman.py

debug:
	$(PYTHON) -m pdb pacman.py

clean:
	find . -path ./$(VENV) -prune -o -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

fclean: clean
	rm -rf $(VENV)

lint:
	@status=0; \
	if [ "$(SKIP_FLAKE8)" != "1" ]; then \
		$(PYTHON) -m flake8 . || status=1; \
	fi; \
	if [ "$(SKIP_MYPY)" != "1" ]; then \
		$(PYTHON) -m mypy . $(MYPY_FLAGS) || status=1; \
	fi; \
	exit $$status

lint-strict:
	@status=0; \
	if [ "$(SKIP_FLAKE8)" != "1" ]; then \
		$(PYTHON) -m flake8 . || status=1; \
	fi; \
	if [ "$(SKIP_MYPY)" != "1" ]; then \
		$(PYTHON) -m mypy . --strict || status=1; \
	fi; \
	exit $$status
