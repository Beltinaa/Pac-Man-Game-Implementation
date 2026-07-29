# Makefile for Pac-Man Game Implementation
#
# Requires Python 3.10+ (the assigned mazegenerator package uses modern
# type-hint syntax that only runs there -- see README.md). If your
# system's default `python3` is older, override it, e.g.:
#   make install PYTHON_BIN=python3.11

PYTHON_BIN ?= python3
VENV       := venv
PYTHON     := $(VENV)/bin/python3
PIP        := $(VENV)/bin/pip
MAZEGEN_WHEEL := mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	$(PYTHON_BIN) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install pygame flake8 mypy
	$(PIP) install ./$(MAZEGEN_WHEEL)

run:
	$(PYTHON) pacman.py

debug:
	$(PYTHON) -m pdb pacman.py

clean:
	find . -path ./$(VENV) -prune -o -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

# Both tools always run, even if the first one finds issues -- but the
# target still exits non-zero overall if either did (useful in CI).
lint:
	@status=0; \
	$(PYTHON) -m flake8 . || status=1; \
	$(PYTHON) -m mypy . $(MYPY_FLAGS) || status=1; \
	exit $$status

lint-strict:
	@status=0; \
	$(PYTHON) -m flake8 . || status=1; \
	$(PYTHON) -m mypy . --strict || status=1; \
	exit $$status
