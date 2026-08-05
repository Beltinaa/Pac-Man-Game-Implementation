# Pac-Man -- build targets
#
#   make install    create the venv and install everything needed
#   make run        play the game
#   make clean      delete the venv, __pycache__ and tool caches
#   make lint       flake8 + mypy
#
# Two environment quirks this file works around, both of which used to fail
# in confusing ways:
#
# 1. Python version. The assigned mazegenerator wheel annotates with PEP 604
#    unions ("str | bool", its mazegenerator.py lines 26 and 35). Those are
#    evaluated at runtime, so it only imports on Python 3.10+. It declares no
#    Requires-Python, so pip installs it happily on 3.9 and it then dies at
#    import with "unsupported operand type(s) for |". macOS ships 3.9 as
#    /usr/bin/python3, hence picking an interpreter rather than trusting the
#    bare name.
#
# 2. Which pygame. Upstream pygame publishes prebuilt wheels only for the
#    Python versions it was released against (2.6.1 covers 3.9 to 3.13).
#    On anything newer pip compiles it from source and silently drops every
#    optional module whose C headers are missing -- which is how you get a
#    working pygame that raises "mixer module not available", and a game
#    with no sound and no error. So: never build from source, and if
#    upstream has no wheel for this interpreter, fall back automatically to
#    pygame-ce, a drop-in fork that imports as `pygame` and ships wheels for
#    newer versions. Pin one with: make install PYGAME_PKG=pygame-ce

PYTHON_BIN ?= $(shell for p in python3.13 python3.12 python3.11 python3.10 python3; do \
                  command -v $$p >/dev/null 2>&1 && echo $$p && break; done)
VENV       := venv
PYTHON     := $(VENV)/bin/python3
PIP        := $(VENV)/bin/pip
MAZEGEN_WHEEL := mazegenerator-2.1.0-py3-none-any.whl

# Empty means "try pygame, then pygame-ce". Set it to pin one.
PYGAME_PKG ?=

MIN_PYTHON := import sys; sys.exit(sys.version_info < (3, 10))
HAS_MIXER  := import pygame; pygame.mixer

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs
SKIP_FLAKE8 ?= 0
SKIP_MYPY ?= 0

.PHONY: all install run debug clean fclean re lint lint-strict check-audio

all: install

install:
	@if [ -z "$(PYTHON_BIN)" ]; then \
		echo "No python3 found on PATH."; exit 1; fi
	@$(PYTHON_BIN) -c '$(MIN_PYTHON)' || { \
		echo "$(PYTHON_BIN) is `$(PYTHON_BIN) -V 2>&1`, but the maze generator needs 3.10+."; \
		echo "See what you have:  ls /usr/bin/python3.*"; \
		echo "then:               make install PYTHON_BIN=<one of them>"; \
		exit 1; }
	@if [ -x $(PYTHON) ] && ! $(PYTHON) -c '$(MIN_PYTHON)' 2>/dev/null; then \
		echo "existing $(VENV) is too old -- recreating it"; rm -rf $(VENV); fi
	@test -x $(PYTHON) || $(PYTHON_BIN) -m venv $(VENV)
	@$(PIP) install --upgrade --quiet pip
	@# --only-binary refuses to compile from source, so a build that would
	@# come out without audio fails here instead of silently succeeding.
	@if [ -n "$(PYGAME_PKG)" ]; then \
		echo "installing $(PYGAME_PKG) ..."; \
		$(PIP) install --quiet --only-binary=:all: $(PYGAME_PKG) || exit 1; \
	elif $(PIP) install --quiet --only-binary=:all: pygame 2>/dev/null; then \
		echo "installing pygame ... done"; \
	else \
		echo "no pygame wheel for `$(PYTHON) -V 2>&1`, using pygame-ce ..."; \
		$(PIP) install --quiet --only-binary=:all: pygame-ce || { \
			echo ""; \
			echo "Neither pygame nor pygame-ce has a wheel for this Python."; \
			echo "Install a 3.10-3.13 interpreter and re-run:"; \
			echo "    make clean && make install PYTHON_BIN=python3.12"; \
			exit 1; }; \
	fi
	@echo "installing flake8, mypy ..."
	@$(PIP) install --quiet flake8 mypy
	@echo "installing the maze generator ..."
	@$(PIP) install --quiet ./$(MAZEGEN_WHEEL)
	@echo ""
	@echo "install complete -- `$(PYTHON) -V 2>&1`"
	@$(MAKE) --no-print-directory check-audio
	@echo "run it with:  make run"

run:
	@test -x $(PYTHON) || { echo "no venv yet -- run: make install"; exit 1; }
	$(PYTHON) pacman.py

debug:
	$(PYTHON) -m pdb pacman.py

# Reports whether this install can play sound, and what to do if not.
check-audio:
	@if $(PYTHON) -c '$(HAS_MIXER)' 2>/dev/null; then \
		echo "audio: OK -- pygame has the mixer module"; \
	else \
		echo "audio: MISSING -- the game will run, but silently."; \
		echo "  This pygame has no mixer module. Try:"; \
		echo "      make clean && make install PYGAME_PKG=pygame-ce"; \
	fi

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

# Kept as an alias: clean already removes everything.
fclean: clean

re: clean install

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
