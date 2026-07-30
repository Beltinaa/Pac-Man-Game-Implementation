PYTHON_BIN ?= python3
VENV       := venv
PYTHON     := $(VENV)/bin/python3
PIP        := $(VENV)/bin/pip
MAZEGEN_WHEEL := mazegenerator-2.1.0-py3-none-any.whl

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs
SKIP_FLAKE8 ?= 0
SKIP_MYPY ?= 0

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
