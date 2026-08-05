import json
import math
import sys
from pathlib import Path

import pygame

_CONFIG_PATH = Path(__file__).with_name('config.json')

_REQUIRED_KEYS = (
    'highscore_filename',
    'lives',
    'points_per_pacgum',
    'points_per_super_pacgum',
    'points_per_ghost',
    'seed',
    'level_max_time',
    'levels',
)

_REQUIRED_LEVEL_KEYS = ('width', 'height', 'pacgum')


def _config_error(message):
    sys.exit(f'Config error: {message}')


def _load_config():
    if not _CONFIG_PATH.is_file():
        _config_error(f'missing {_CONFIG_PATH.name}')

    try:
        with _CONFIG_PATH.open(encoding='utf-8') as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        _config_error(f'invalid JSON in {_CONFIG_PATH.name}: {exc}')

    if not isinstance(data, dict):
        _config_error(f'{_CONFIG_PATH.name} must contain a JSON object')

    missing = [key for key in _REQUIRED_KEYS if key not in data]
    if missing:
        _config_error(
            f'missing required key(s) in {_CONFIG_PATH.name}: {", ".join(missing)}'
        )

    levels = data['levels']
    if not isinstance(levels, list) or not levels:
        _config_error('"levels" must be a non-empty list')

    for index, level in enumerate(levels):
        if not isinstance(level, dict):
            _config_error(f'levels[{index}] must be an object')
        missing_level = [key for key in _REQUIRED_LEVEL_KEYS if key not in level]
        if missing_level:
            _config_error(
                f'missing required key(s) in levels[{index}]: '
                f'{", ".join(missing_level)}'
            )

    return data


_cfg = _load_config()

# --- values from config.json ---
HIGHSCORES_FILE = _cfg['highscore_filename']
STARTING_LIVES = _cfg['lives']
DOT_SCORE = _cfg['points_per_pacgum']
POWER_PELLET_SCORE = _cfg['points_per_super_pacgum']
GHOST_EAT_BASE_SCORE = _cfg['points_per_ghost']
LEVEL_1_SEED = _cfg['seed']
LEVEL_TIME_LIMIT_SECONDS = _cfg['level_max_time']
LEVELS = _cfg['levels']
TOTAL_LEVELS = len(LEVELS)

# Display
# Background music. Drop your own audio file at this path -- .ogg is the
# safest format (pygame reads .ogg and .wav everywhere; .mp3 depends on the
# SDL_mixer build). A missing file is not an error: the game runs silently
# and the HUD sound button shows as muted.
# Optional override. Each theme names its own track (see theme.py), which is
# used when it exists; set this to a real path to force one track for every
# theme instead. If neither exists, any audio file in the folder is played.
MUSIC_FILE = 'assets/sounds/music.ogg'
MUSIC_VOLUME = 0.3

# Fallback skin. The main menu's character picker chooses the theme at
# runtime, so this only matters to code that runs before a pick is made.
# See theme.py for the available names and for how to add your own art.
THEME_NAME = 'web-slinger'

WIDTH = 900
HEIGHT = 950
FPS = 60

# Rendering
COLOR = 'blue'
PI = math.pi

# Highscores (not in config.json)
MAX_HIGHSCORES = 10
NAME_INPUT_MAX_LEN = 12

# Cheats (not in config.json)
CHEATS_ENABLED = True
PLAYER_SPEED_NORMAL = 2
PLAYER_SPEED_BOOSTED = 4

# Ghost AI (not in config.json)
GHOST_RESPAWN_DELAY_SECONDS = 1
GHOST_HOME_ARRIVAL_RADIUS = 20

# Game state machine
STATE_MENU = 'MENU'
STATE_INSTRUCTIONS = 'INSTRUCTIONS'
STATE_HIGHSCORES = 'HIGHSCORES'
STATE_PLAYING = 'PLAYING'
STATE_PAUSED = 'PAUSED'
STATE_GAME_OVER = 'GAME_OVER'
STATE_VICTORY = 'VICTORY'

PAUSE_KEY = pygame.K_ESCAPE
