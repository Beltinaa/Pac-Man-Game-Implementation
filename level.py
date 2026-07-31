import copy
import random
from collections import deque

from board import LEVEL_1_SEED, load_level
from config import (
    HEIGHT,
    STARTING_LIVES,
    STATE_GAME_OVER,
    STATE_VICTORY,
    TOTAL_LEVELS,
    WIDTH,
)
import state
from state import LEVEL_TIME_LIMIT_FRAMES


def prepare_level(seed):
    """Load one level's board and derive spawn points from it."""
    state.level, state.ghost_pocket = load_level(seed)
    state.level = copy.deepcopy(state.level)

    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    rows, cols = len(state.level), len(state.level[0])

    if state.ghost_pocket is not None:
        def nearest_passable_tile(row, col, forbidden=frozenset(), allowed=None):
            def ok(r, c):
                return (state.level[r][c] < 3 and (r, c) not in forbidden
                        and (allowed is None or (r, c) in allowed))

            row = min(max(row, 0), rows - 1)
            col = min(max(col, 0), cols - 1)
            if ok(row, col):
                return row, col
            seen = {(row, col)}
            queue = deque([(row, col)])
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        if ok(nr, nc):
                            return nr, nc
                        queue.append((nr, nc))
            raise RuntimeError('generated maze has no passable tile near the requested spot')

        def reachable_tiles(start):
            seen = {start}
            queue = deque([start])
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in seen and state.level[nr][nc] < 3):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            return seen

        def tile_center_pixel(row, col):
            return col * num2 + num2 // 2, row * num1 + num1 // 2

        pocket = state.ghost_pocket
        pocket_tiles = frozenset(
            (r, c)
            for r in range(pocket.row_start, pocket.row_end + 1)
            for c in range(pocket.col_start, pocket.col_end + 1)
        )

        p_row, p_col = nearest_passable_tile(rows // 2, cols // 2, forbidden=pocket_tiles)
        p_cx, p_cy = tile_center_pixel(p_row, p_col)
        state.SPAWN_PLAYER = (p_cx - 23, p_cy - 24)

        main_area = reachable_tiles((p_row, p_col))
        edge_columns = frozenset((r, c) for r in range(rows) for c in (0, cols - 1))

        def corner_spawn(row, col, direction_):
            r, c = nearest_passable_tile(row, col, forbidden=edge_columns, allowed=main_area)
            cx, cy = tile_center_pixel(r, c)
            return cx - 22, cy - 22, direction_

        state.SPAWN_BLINKY = corner_spawn(0, 0, 0)
        state.SPAWN_PINKY = corner_spawn(0, cols - 1, 1)
        state.SPAWN_INKY = corner_spawn(rows - 1, 0, 0)
        state.SPAWN_CLYDE = corner_spawn(rows - 1, cols - 1, 1)

        state.BOX_X0 = pocket.col_start * num2
        state.BOX_X1 = (pocket.col_end + 1) * num2
        state.BOX_Y0 = pocket.row_start * num1
        state.BOX_Y1 = (pocket.row_end + 1) * num1
        state.BOX_USE_CENTER = True
        state.EXIT_TARGET = ((state.BOX_X0 + state.BOX_X1) // 2, (state.BOX_Y0 + state.BOX_Y1) // 2)
    else:
        state.SPAWN_PLAYER = (450, 663)
        state.SPAWN_BLINKY = (56, 58, 0)
        state.SPAWN_INKY = (440, 388, 2)
        state.SPAWN_PINKY = (440, 438, 2)
        state.SPAWN_CLYDE = (440, 438, 2)
        state.BOX_X0, state.BOX_X1 = 350, 550
        state.BOX_Y0, state.BOX_Y1 = 370, 480
        state.BOX_USE_CENTER = False
        state.EXIT_TARGET = (400, 100)

    state.EXIT_TILE = (
        (state.BOX_Y0 + state.BOX_Y1) // 2 // num1,
        (state.BOX_X0 + state.BOX_X1) // 2 // num2,
    )
    state.level_time_remaining = LEVEL_TIME_LIMIT_FRAMES


def reset_positions_to_spawn():
    """Send the player and all 4 ghosts back to their spawns."""
    state.player_x, state.player_y = state.SPAWN_PLAYER
    state.direction = 0
    state.direction_command = 0
    state.blinky_x, state.blinky_y, state.blinky_direction = state.SPAWN_BLINKY
    state.inky_x, state.inky_y, state.inky_direction = state.SPAWN_INKY
    state.pinky_x, state.pinky_y, state.pinky_direction = state.SPAWN_PINKY
    state.clyde_x, state.clyde_y, state.clyde_direction = state.SPAWN_CLYDE
    state.eaten_ghost = [False, False, False, False]
    state.blinky_dead = False
    state.inky_dead = False
    state.clyde_dead = False
    state.pinky_dead = False
    state.blinky_going_home = False
    state.inky_going_home = False
    state.pinky_going_home = False
    state.clyde_going_home = False
    state.blinky_respawn_timer = 0
    state.inky_respawn_timer = 0
    state.pinky_respawn_timer = 0
    state.clyde_respawn_timer = 0
    state.powerup = False
    state.power_counter = 0
    state.startup_counter = 0
    state.targets = [(state.player_x, state.player_y)] * 4
    state.ghost_waypoints = [None, None, None, None]


def lose_a_life():
    """Costs a life on ghost contact or on the level timer running out."""
    if state.cheat_invincible:
        return
    if state.lives > 0:
        state.lives -= 1
        reset_positions_to_spawn()
        state.level_time_remaining = LEVEL_TIME_LIMIT_FRAMES
    else:
        state.game_over = True
        state.moving = False
        enter_game_end_state(STATE_GAME_OVER)


def start_new_game():
    """Fresh game from the main menu."""
    state.score = 0
    state.lives = STARTING_LIVES
    state.current_level = 1
    state.game_over = False
    state.game_won = False
    prepare_level(LEVEL_1_SEED)
    reset_positions_to_spawn()


def advance_level():
    """Called when every pacgum + super-pacgum on the current level is gone."""
    if state.current_level >= TOTAL_LEVELS:
        state.game_won = True
        state.moving = False
        enter_game_end_state(STATE_VICTORY)
    else:
        state.current_level += 1
        prepare_level(random.randint(1, 999_999))
        reset_positions_to_spawn()


def enter_game_end_state(new_state):
    """Switch to game over or victory with a fresh name-entry prompt."""
    state.game_state = new_state
    state.name_input = ''


def init_game():
    """Load level 1 and reset positions at startup."""
    prepare_level(LEVEL_1_SEED)
    reset_positions_to_spawn()
