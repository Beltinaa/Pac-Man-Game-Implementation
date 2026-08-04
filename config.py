import math
import pygame

# Display
# Background music. Drop your own audio file at this path -- .ogg is the
# safest format (pygame reads .ogg and .wav everywhere; .mp3 depends on the
# SDL_mixer build). A missing file is not an error: the game runs silently
# and the HUD sound button shows as muted.
MUSIC_FILE = 'assets/sounds/music.ogg'
MUSIC_VOLUME = 0.4

# Visual skin. See theme.py for the available names ('classic',
# 'web-slinger') and for how to add your own art.
THEME_NAME = 'web-slinger'

WIDTH = 900
HEIGHT = 950
FPS = 60

# Rendering
COLOR = 'blue'
PI = math.pi

# Scoring and lives
DOT_SCORE = 10
POWER_PELLET_SCORE = 50
GHOST_EAT_BASE_SCORE = 100
STARTING_LIVES = 3

# Highscores
HIGHSCORES_FILE = 'highscores.json'
MAX_HIGHSCORES = 10
NAME_INPUT_MAX_LEN = 12

# Cheats
CHEATS_ENABLED = True
PLAYER_SPEED_NORMAL = 2
PLAYER_SPEED_BOOSTED = 4

# Ghost AI
GHOST_RESPAWN_DELAY_SECONDS = 1
GHOST_HOME_ARRIVAL_RADIUS = 20

# Levels
TOTAL_LEVELS = 10
LEVEL_TIME_LIMIT_SECONDS = 150

# Game state machine
STATE_MENU = 'MENU'
STATE_INSTRUCTIONS = 'INSTRUCTIONS'
STATE_HIGHSCORES = 'HIGHSCORES'
STATE_PLAYING = 'PLAYING'
STATE_PAUSED = 'PAUSED'
STATE_GAME_OVER = 'GAME_OVER'
STATE_VICTORY = 'VICTORY'

PAUSE_KEY = pygame.K_ESCAPE
