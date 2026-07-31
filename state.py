from config import (
    FPS,
    LEVEL_TIME_LIMIT_SECONDS,
    STARTING_LIVES,
    STATE_MENU,
    TOTAL_LEVELS,
)

# Derived timing constants (depend on FPS)
GHOST_RESPAWN_DELAY_FRAMES = 1 * FPS
LEVEL_TIME_LIMIT_FRAMES = LEVEL_TIME_LIMIT_SECONDS * FPS

# Level / board
level = []
ghost_pocket = None
current_level = 1
level_time_remaining = LEVEL_TIME_LIMIT_FRAMES

# Spawn points (set by prepare_level)
SPAWN_PLAYER = (0, 0)
SPAWN_BLINKY = (0, 0, 0)
SPAWN_INKY = (0, 0, 0)
SPAWN_PINKY = (0, 0, 0)
SPAWN_CLYDE = (0, 0, 0)

# Ghost-house box
BOX_X0 = BOX_X1 = BOX_Y0 = BOX_Y1 = 0
BOX_USE_CENTER = False
EXIT_TARGET = (0, 0)
EXIT_TILE = (0, 0)

# Player
player_x = 0
player_y = 0
direction = 0
direction_command = 0
player_speed = 2
turns_allowed = [False, False, False, False]
counter = 0
flicker = False

# Ghost positions and state
blinky_x = blinky_y = blinky_direction = 0
inky_x = inky_y = inky_direction = 0
pinky_x = pinky_y = pinky_direction = 0
clyde_x = clyde_y = clyde_direction = 0

blinky_dead = inky_dead = clyde_dead = pinky_dead = False
blinky_box = inky_box = clyde_box = pinky_box = False
blinky_going_home = inky_going_home = pinky_going_home = clyde_going_home = False
blinky_respawn_timer = inky_respawn_timer = pinky_respawn_timer = clyde_respawn_timer = 0

ghost_speeds = [1, 1, 1, 1]
ghost_waypoints = [None, None, None, None]
targets = [(0, 0)] * 4
eaten_ghost = [False, False, False, False]

# Power-up
powerup = False
power_counter = 0

# Score / lives / game flow
score = 0
lives = STARTING_LIVES
game_over = False
game_won = False
moving = False
startup_counter = 0

# Cheats
cheat_invincible = False
cheat_ghosts_frozen = False

# UI / menu
game_state = STATE_MENU
menu_options = ['Start Game', 'Highscores', 'Instructions', 'Exit']
menu_index = 0
name_input = ''
