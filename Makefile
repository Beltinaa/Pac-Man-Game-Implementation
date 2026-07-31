# The assigned mazegenerator wheel annotates with PEP 604 unions ("str | bool",
# see its mazegenerator.py lines 26 and 35). Those are evaluated at runtime, so
# the package only imports on Python 3.10+. It ships no Requires-Python, so pip
# installs it happily on an older interpreter and it then fails at import with
# "unsupported operand type(s) for |". macOS's own /usr/bin/python3 is 3.9, so
# pick the newest interpreter on PATH rather than whatever "python3" resolves
# to. Override explicitly with: make install PYTHON_BIN=/path/to/python3.12
PYTHON_BIN ?= $(shell for p in python3.13 python3.12 python3.11 python3.10 python3; do \
                  command -v $$p >/dev/null 2>&1 && echo $$p && break; done)
MIN_PYTHON := import sys; sys.exit(sys.version_info < (3, 10))
VENV       := venv
PYTHON     := $(VENV)/bin/python3
PIP        := $(VENV)/bin/pip
MAZEGEN_WHEEL := mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs
SKIP_FLAKE8 ?= 0
SKIP_MYPY ?= 0

.PHONY: install run debug clean fclean lint lint-strict

install:
	@$(PYTHON_BIN) -c '$(MIN_PYTHON)' || { \
		echo "$(PYTHON_BIN) is `$(PYTHON_BIN) -V 2>&1`, but the maze generator needs Python 3.10+."; \
		echo "Install one (e.g. brew install python@3.12) then: make install PYTHON_BIN=python3.12"; \
		exit 1; }
	@if [ -x $(PYTHON) ] && ! $(PYTHON) -c '$(MIN_PYTHON)'; then \
		echo "existing $(VENV) is `$(PYTHON) -V 2>&1` -- too old, recreating it"; \
		rm -rf $(VENV); \
	fi
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
