import copy
import json
import random
from collections import deque
from board import load_level, LEVEL_1_SEED
import pygame
import math

pygame.init()

WIDTH = 900
HEIGHT = 950
screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
fps = 60
font = pygame.font.Font('freesansbold.ttf', 20)
title_font = pygame.font.Font('freesansbold.ttf', 48)
color = 'blue'
PI = math.pi
player_images = []
for i in range(1, 5):
    player_images.append(pygame.transform.scale(pygame.image.load(f'assets/player_images/{i}.png'), (45, 45)))
blinky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/red.png'), (45, 45))
pinky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/pink.png'), (45, 45))
inky_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/blue.png'), (45, 45))
clyde_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/orange.png'), (45, 45))
spooked_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/powerup.png'), (45, 45))
dead_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/dead.png'), (45, 45))

# ---------------------------------------------------------------------------
# Scoring and lives
# ---------------------------------------------------------------------------
DOT_SCORE = 10             # X: points per pacgum
POWER_PELLET_SCORE = 50    # Y: points per super-pacgum
GHOST_EAT_BASE_SCORE = 100  # Z: points for the 1st edible ghost eaten in a
                             # combo; each further ghost in the same combo is
                             # worth 2x the last (2**eaten_count * Z), already
                             # implemented below -- kept as-is per spec.
STARTING_LIVES = 3

# ---------------------------------------------------------------------------
# Highscores: Top 10 (name, score) persisted to a local JSON file so they
# survive restarting the app. Corrupt/missing file -> treated as empty,
# same "fail cleanly" spirit as the maze generator's own fallback.
# ---------------------------------------------------------------------------
HIGHSCORES_FILE = 'highscores.json'
MAX_HIGHSCORES = 10
NAME_INPUT_MAX_LEN = 12


def load_highscores():
    try:
        with open(HIGHSCORES_FILE, 'r') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    entries = []
    for entry in data:
        if isinstance(entry, dict) and 'name' in entry and 'score' in entry:
            try:
                entries.append({'name': str(entry['name']), 'score': int(entry['score'])})
            except (TypeError, ValueError):
                continue
    entries.sort(key=lambda e: e['score'], reverse=True)
    return entries[:MAX_HIGHSCORES]


def save_highscore(name, score_value):
    name = (name.strip() or 'PLAYER')[:NAME_INPUT_MAX_LEN]
    entries = load_highscores()
    entries.append({'name': name, 'score': score_value})
    entries.sort(key=lambda e: e['score'], reverse=True)
    entries = entries[:MAX_HIGHSCORES]
    try:
        with open(HIGHSCORES_FILE, 'w') as f:
            json.dump(entries, f, indent=2)
    except OSError:
        pass
    return entries


# ---------------------------------------------------------------------------
# Ghost AI
#
# Chase (not edible): BFS shortest path to the player's current tile,
# recomputed every frame -- simple, and cheap enough at this board size
# (33x30 tiles) to run for all 4 ghosts every frame.
# Flee (edible, after a super-pacgum): step to whichever of the ghost's
# own passable neighbor tiles is farthest from the player's tile.
# Eaten: becomes eyes, walks to the ghost-house pocket (existing gate/
# pocket logic), waits there for GHOST_RESPAWN_DELAY_SECONDS, then walks
# back to its own corner before resuming chase/flee.
# ---------------------------------------------------------------------------
GHOST_RESPAWN_DELAY_SECONDS = 7
GHOST_RESPAWN_DELAY_FRAMES = GHOST_RESPAWN_DELAY_SECONDS * fps
GHOST_HOME_ARRIVAL_RADIUS = 20  # pixels; "close enough" to its corner to stop walking home

# ---------------------------------------------------------------------------
# Levels: level 1 is always the same fixed-seed maze; every level after
# that is freshly, randomly generated. A level ends when every pacgum and
# super-pacgum on it is eaten; clearing the last level wins the game. Each
# level also has a time limit -- running out costs a life, exactly like
# ghost contact (see lose_a_life(), used by both).
# ---------------------------------------------------------------------------
TOTAL_LEVELS = 5
LEVEL_TIME_LIMIT_SECONDS = 150
LEVEL_TIME_LIMIT_FRAMES = LEVEL_TIME_LIMIT_SECONDS * fps

current_level = 1
level_time_remaining = LEVEL_TIME_LIMIT_FRAMES


def prepare_level(seed):
    """Load one level's board (fixed seed for level 1, random for every
    level after -- see the callers) and (re)derive every spawn point plus
    the ghost-house box/eyes-target from it. Runs once at startup and
    again on every level transition, so nothing here is tied to a single
    board the way the original one-time setup was."""
    global level, ghost_pocket, level_time_remaining
    global SPAWN_PLAYER, SPAWN_BLINKY, SPAWN_INKY, SPAWN_PINKY, SPAWN_CLYDE
    global BOX_X0, BOX_X1, BOX_Y0, BOX_Y1, BOX_USE_CENTER, EXIT_TARGET, EXIT_TILE

    board_grid, ghost_pocket = load_level(seed)
    level = copy.deepcopy(board_grid)

    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    rows, cols = len(level), len(level[0])

    if ghost_pocket is not None:
        # Generated maze: player/ghost spawns and the ghost-house box are all
        # derived from the actual board + the pocket carved behind its "42"
        # (see maze_adapter.py), never hardcoded, so they're valid on every seed.
        def nearest_passable_tile(row, col, forbidden=frozenset(), allowed=None):
            def ok(r, c):
                return (level[r][c] < 3 and (r, c) not in forbidden
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
            """Every tile reachable from start using only the player's own
            movement rule (< 3, no gate) -- used to keep ghost corner
            spawns off of small pockets that a generated maze can
            occasionally leave isolated from the main play area."""
            seen = {start}
            queue = deque([start])
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in seen and level[nr][nc] < 3):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            return seen

        def tile_center_pixel(row, col):
            return col * num2 + num2 // 2, row * num1 + num1 // 2

        pocket_tiles = frozenset(
            (r, c)
            for r in range(ghost_pocket.row_start, ghost_pocket.row_end + 1)
            for c in range(ghost_pocket.col_start, ghost_pocket.col_end + 1)
        )

        # player spawn: nearest open tile to the maze's center, excluding the
        # ghost pocket itself (which also sits dead-center behind the "42")
        p_row, p_col = nearest_passable_tile(rows // 2, cols // 2, forbidden=pocket_tiles)
        p_cx, p_cy = tile_center_pixel(p_row, p_col)
        SPAWN_PLAYER = (p_cx - 23, p_cy - 24)

        # every tile actually reachable from the player -- corners must be
        # searched within this, not just "nearest passable tile", since a
        # generated maze can leave a small isolated pocket near a corner
        # that a plain passability search would otherwise happily return
        main_area = reachable_tiles((p_row, p_col))

        # ghost corner spawns: nearest open (and reachable) tile to each of
        # the 4 board corners, excluding the leftmost/rightmost columns --
        # Ghost.check_collisions (unchanged, see its "0 < center_x // 30 <
        # 29" branch) treats those two columns as the tunnel wraparound
        # edge and only ever offers left/right turns there, which would
        # permanently trap a ghost spawned in a literal grid corner the
        # instant it needs to move vertically to actually reach the maze.
        # Blinky top-left, Pinky top-right, Inky bottom-left, Clyde bottom-right
        edge_columns = frozenset((r, c) for r in range(rows) for c in (0, cols - 1))

        def corner_spawn(row, col, direction_):
            r, c = nearest_passable_tile(row, col, forbidden=edge_columns, allowed=main_area)
            cx, cy = tile_center_pixel(r, c)
            return cx - 22, cy - 22, direction_

        SPAWN_BLINKY = corner_spawn(0, 0, 0)
        SPAWN_PINKY = corner_spawn(0, cols - 1, 1)
        SPAWN_INKY = corner_spawn(rows - 1, 0, 0)
        SPAWN_CLYDE = corner_spawn(rows - 1, cols - 1, 1)

        # ghost-house box bounds + eyes-return-home target, from the pocket's
        # own tile coordinates (see Ghost.check_collisions and get_targets)
        BOX_X0 = ghost_pocket.col_start * num2
        BOX_X1 = (ghost_pocket.col_end + 1) * num2
        BOX_Y0 = ghost_pocket.row_start * num1
        BOX_Y1 = (ghost_pocket.row_end + 1) * num1
        BOX_USE_CENTER = True
        EXIT_TARGET = ((BOX_X0 + BOX_X1) // 2, (BOX_Y0 + BOX_Y1) // 2)
    else:
        # Static fallback maze: keep the original fixed spawns/box exactly as
        # they were before the maze generator was introduced.
        SPAWN_PLAYER = (450, 663)
        SPAWN_BLINKY = (56, 58, 0)
        SPAWN_INKY = (440, 388, 2)
        SPAWN_PINKY = (440, 438, 2)
        SPAWN_CLYDE = (440, 438, 2)
        BOX_X0, BOX_X1 = 350, 550
        BOX_Y0, BOX_Y1 = 370, 480
        BOX_USE_CENTER = False
        EXIT_TARGET = (400, 100)

    # tile version of the box's center, for eyes' BFS path home (see
    # _ghost_target/_sticky_bfs_target): a fixed pixel target alone can
    # leave a greedy mover committed to the wrong direction for the length
    # of a long corridor, same class of issue chase/going-home already
    # solve with a BFS waypoint that's recomputed on real progress.
    EXIT_TILE = ((BOX_Y0 + BOX_Y1) // 2 // num1, (BOX_X0 + BOX_X1) // 2 // num2)

    level_time_remaining = LEVEL_TIME_LIMIT_FRAMES


def reset_positions_to_spawn():
    """Send the player and all 4 ghosts back to their spawns for whichever
    board is currently loaded. Used both after losing a life and after
    clearing a level -- score, lives and the level/board itself are
    deliberately untouched here; callers own those."""
    global player_x, player_y, direction, direction_command
    global blinky_x, blinky_y, blinky_direction
    global inky_x, inky_y, inky_direction
    global pinky_x, pinky_y, pinky_direction
    global clyde_x, clyde_y, clyde_direction
    global eaten_ghost, blinky_dead, inky_dead, clyde_dead, pinky_dead
    global powerup, power_counter, startup_counter, targets
    global blinky_going_home, inky_going_home, pinky_going_home, clyde_going_home
    global blinky_respawn_timer, inky_respawn_timer, pinky_respawn_timer, clyde_respawn_timer
    global ghost_waypoints

    player_x, player_y = SPAWN_PLAYER
    direction = 0
    direction_command = 0
    blinky_x, blinky_y, blinky_direction = SPAWN_BLINKY
    inky_x, inky_y, inky_direction = SPAWN_INKY
    pinky_x, pinky_y, pinky_direction = SPAWN_PINKY
    clyde_x, clyde_y, clyde_direction = SPAWN_CLYDE
    eaten_ghost = [False, False, False, False]
    blinky_dead = False
    inky_dead = False
    clyde_dead = False
    pinky_dead = False
    blinky_going_home = False
    inky_going_home = False
    pinky_going_home = False
    clyde_going_home = False
    blinky_respawn_timer = 0
    inky_respawn_timer = 0
    pinky_respawn_timer = 0
    clyde_respawn_timer = 0
    powerup = False
    power_counter = 0
    startup_counter = 0
    targets = [(player_x, player_y)] * 4
    ghost_waypoints = [None, None, None, None]


def _tile_of(x_pos, y_pos):
    """Tile (row, col) a ghost/player pixel top-left position sits in,
    using the same +22 center offset the Ghost class already uses."""
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    return (y_pos + 22) // num1, (x_pos + 22) // num2


def _pixel_center_of(row, col):
    """Ghost top-left (x_pos, y_pos) that puts a ghost's own center (which
    check_collisions computes as x_pos + 22 / y_pos + 22, same as
    _tile_of above) exactly on this tile's true pixel center. Used only
    for ghost targets, which move_toward_target compares against x_pos/
    y_pos directly -- getting this offset wrong leaves a ghost's center
    permanently 22px off from where the tile-alignment checks in
    check_collisions expect it, which is enough to make it miss a single-
    tile-wide gate's alignment window and never actually turn into it."""
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    return col * num2 + num2 // 2 - 22, row * num1 + num1 // 2 - 22


def _bfs_next_tile(start_tile, goal_tile):
    """First step of the shortest path from start_tile to goal_tile over
    the current level grid (corridors and the ghost-house gate are both
    passable; walls are not -- the gate is a dead-end pocket, so allowing
    it never shortens any other path). Returns start_tile unchanged if
    already there or if no path exists."""
    if start_tile == goal_tile:
        return start_tile
    rows, cols = len(level), len(level[0])
    start_r, start_c = start_tile
    goal_r, goal_c = goal_tile
    if not (0 <= start_r < rows and 0 <= start_c < cols
            and 0 <= goal_r < rows and 0 <= goal_c < cols):
        return start_tile

    def passable(r, c):
        v = level[r][c]
        return v < 3 or v == 9

    prev = {start_tile: None}
    queue = deque([start_tile])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal_tile:
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and (nr, nc) not in prev and passable(nr, nc)):
                prev[(nr, nc)] = (r, c)
                queue.append((nr, nc))

    if goal_tile not in prev:
        return start_tile
    step = goal_tile
    while prev[step] is not None and prev[step] != start_tile:
        step = prev[step]
    return step


def _update_ghost_respawn(dead, in_box, timer, going_home, x_pos, y_pos, spawn):
    """Advance one ghost's eaten -> waiting-in-the-pocket -> walking-home
    state machine by one frame. Returns (dead, timer, going_home)."""
    if dead and in_box:
        timer += 1
        if timer >= GHOST_RESPAWN_DELAY_FRAMES:
            dead = False
            going_home = True
            timer = 0
    else:
        timer = 0
    if going_home:
        if (abs(x_pos - spawn[0]) < GHOST_HOME_ARRIVAL_RADIUS
                and abs(y_pos - spawn[1]) < GHOST_HOME_ARRIVAL_RADIUS):
            going_home = False
    return dead, timer, going_home


def lose_a_life():
    """Costs a life on ghost contact or on the level timer running out --
    both funnel through here so the two triggers stay consistent. Per
    spec: respawn centered, ghosts back to their corners, score and the
    level's remaining pacgums untouched; all lives gone ends the game."""
    global lives, game_over, moving, level_time_remaining
    if lives > 0:
        lives -= 1
        reset_positions_to_spawn()
        level_time_remaining = LEVEL_TIME_LIMIT_FRAMES
    else:
        game_over = True
        moving = False
        _enter_game_end_state(STATE_GAME_OVER)


def start_new_game():
    """Fresh game from the main menu: score/lives reset, level 1 reloaded
    with its fixed seed (so it's identical every time), positions reset."""
    global score, lives, current_level, game_over, game_won
    score = 0
    lives = STARTING_LIVES
    current_level = 1
    game_over = False
    game_won = False
    prepare_level(LEVEL_1_SEED)
    reset_positions_to_spawn()


def advance_level():
    """Called when every pacgum + super-pacgum on the current level is
    gone. Clearing the last level wins the game; otherwise the next level
    is freshly, randomly generated (score/lives carry over, per spec)."""
    global current_level, game_won, moving
    if current_level >= TOTAL_LEVELS:
        game_won = True
        moving = False
        _enter_game_end_state(STATE_VICTORY)
    else:
        current_level += 1
        prepare_level(random.randint(1, 999_999))
        reset_positions_to_spawn()


prepare_level(LEVEL_1_SEED)
reset_positions_to_spawn()
counter = 0
flicker = False
# R, L, U, D
turns_allowed = [False, False, False, False]
direction_command = 0
player_speed = 2
score = 0
powerup = False
power_counter = 0
eaten_ghost = [False, False, False, False]
targets = [(player_x, player_y), (player_x, player_y), (player_x, player_y), (player_x, player_y)]
blinky_dead = False
inky_dead = False
clyde_dead = False
pinky_dead = False
blinky_box = False
inky_box = False
clyde_box = False
pinky_box = False
moving = False
ghost_speeds = [2, 2, 2, 2]
startup_counter = 0
lives = STARTING_LIVES
game_over = False
game_won = False

# ---------------------------------------------------------------------------
# Game state machine
# ---------------------------------------------------------------------------
STATE_MENU = 'MENU'
STATE_INSTRUCTIONS = 'INSTRUCTIONS'
STATE_HIGHSCORES = 'HIGHSCORES'
STATE_PLAYING = 'PLAYING'
STATE_PAUSED = 'PAUSED'
STATE_GAME_OVER = 'GAME_OVER'
STATE_VICTORY = 'VICTORY'

PAUSE_KEY = pygame.K_ESCAPE  # pauses PLAYING, and doubles as "back" in menus

game_state = STATE_MENU
menu_options = ['Start Game', 'Highscores', 'Instructions', 'Exit']
menu_index = 0
name_input = ''


def _enter_game_end_state(new_state):
    """Switch to STATE_GAME_OVER or STATE_VICTORY with a fresh name-entry
    prompt (whatever was typed for a previous game over/victory doesn't
    carry over)."""
    global game_state, name_input
    game_state = new_state
    name_input = ''


class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id):
        self.x_pos = x_coord
        self.y_pos = y_coord
        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22
        self.target = target
        self.speed = speed
        self.img = img
        self.direction = direct
        self.dead = dead
        self.in_box = box
        self.id = id
        self.turns, self.in_box = self.check_collisions()
        self.rect = self.draw()

    def draw(self):
        if (not powerup and not self.dead) or (eaten_ghost[self.id] and powerup and not self.dead):
            screen.blit(self.img, (self.x_pos, self.y_pos))
        elif powerup and not self.dead and not eaten_ghost[self.id]:
            screen.blit(spooked_img, (self.x_pos, self.y_pos))
        else:
            screen.blit(dead_img, (self.x_pos, self.y_pos))
        ghost_rect = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36, 36))
        return ghost_rect

    def check_collisions(self):
        # R, L, U, D
        num1 = ((HEIGHT - 50) // 32)
        num2 = (WIDTH // 30)
        num3 = 15
        self.turns = [False, False, False, False]
        if 0 < self.center_x // 30 < 29:
            if level[(self.center_y - num3) // num1][self.center_x // num2] == 9:
                self.turns[2] = True
            if level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                    or (level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                    or (level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                    or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                    or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= self.center_x % num2 <= 18:
                    if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if level[self.center_y // num1][(self.center_x - num2) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x - num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // num1][(self.center_x + num2) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x + num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= self.center_x % num2 <= 18:
                    if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True
        box_ref_x, box_ref_y = (self.center_x, self.center_y) if BOX_USE_CENTER else (self.x_pos, self.y_pos)
        if BOX_X0 < box_ref_x < BOX_X1 and BOX_Y0 < box_ref_y < BOX_Y1:
            self.in_box = True
        else:
            self.in_box = False
        return self.turns, self.in_box

    def move_toward_target(self):
        # r, l, u, d
        # shared chase/flee/return mover: greedily steps toward self.target,
        # turning only at intersections self.turns (from check_collisions) allows
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos - 30
        return self.x_pos, self.y_pos, self.direction


def draw_misc():
    score_text = font.render(f'Score: {score}', True, 'white')
    screen.blit(score_text, (10, 920))
    level_text = font.render(f'Level: {current_level}/{TOTAL_LEVELS}', True, 'white')
    screen.blit(level_text, (200, 920))
    time_text = font.render(f'Time: {max(0, level_time_remaining) // fps}s', True, 'white')
    screen.blit(time_text, (400, 920))
    if powerup:
        pygame.draw.circle(screen, 'blue', (140, 930), 15)
    for i in range(lives):
        screen.blit(pygame.transform.scale(player_images[0], (30, 30)), (650 + i * 40, 915))


def draw_menu():
    title = title_font.render('PAC-MAN', True, 'yellow')
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
    for i, label in enumerate(menu_options):
        label_color = 'yellow' if i == menu_index else 'white'
        prefix = '> ' if i == menu_index else '  '
        text = font.render(prefix + label, True, label_color)
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 420 + i * 50)))
    hint = font.render('UP/DOWN to choose, ENTER to select', True, 'gray')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 420 + len(menu_options) * 50 + 40)))


def draw_instructions():
    lines = [
        'HOW TO PLAY',
        '',
        'Move: Arrow Keys',
        'Eat every pacgum and super-pacgum to clear a level.',
        'A super-pacgum makes the ghosts edible for a short time --',
        'eat them for bonus points before it wears off.',
        'Touching a non-edible ghost costs you a life.',
        '',
        'Pause: ESC',
        '',
        'Press ESC or ENTER to return to the menu',
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, 'white')
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 180 + i * 40)))


def draw_highscores_screen():
    title = title_font.render('HIGHSCORES', True, 'yellow')
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
    entries = load_highscores()
    if not entries:
        text = font.render('No highscores yet -- be the first!', True, 'white')
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 320)))
    else:
        for i, entry in enumerate(entries):
            rank_color = 'yellow' if i == 0 else 'white'
            line = f'{i + 1:2d}.  {entry["name"]:<{NAME_INPUT_MAX_LEN}s}  {entry["score"]}'
            text = font.render(line, True, rank_color)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 250 + i * 42)))
    hint = font.render('Press ESC or ENTER to return to the menu', True, 'gray')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 900)))


def draw_pause_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill('black')
    screen.blit(overlay, (0, 0))
    text = title_font.render('PAUSED', True, 'yellow')
    screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
    hint = font.render('ESC: Resume     M: Main Menu', True, 'white')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def draw_name_entry_screen(title_text, title_color, subtitle=None):
    title = title_font.render(title_text, True, title_color)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
    y = 300
    if subtitle:
        sub = font.render(subtitle, True, 'white')
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, y)))
        y += 40
    text = font.render(f'Final score: {score}', True, 'white')
    screen.blit(text, text.get_rect(center=(WIDTH // 2, y)))
    y += 80
    prompt = font.render('Enter your name for the highscore list:', True, 'white')
    screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, y)))
    y += 50
    box_text = font.render((name_input or '') + '_', True, 'yellow')
    screen.blit(box_text, box_text.get_rect(center=(WIDTH // 2, y)))
    y += 60
    hint = font.render('ENTER to save     BACKSPACE to edit     ESC to skip', True, 'gray')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, y)))


def draw_game_over_screen():
    draw_name_entry_screen('GAME OVER', 'red')


def draw_victory_screen():
    draw_name_entry_screen('VICTORY!', 'green', subtitle=f'You cleared all {TOTAL_LEVELS} levels!')


def check_collisions(scor, power, power_count, eaten_ghosts):
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    if 0 < player_x < 870:
        if level[center_y // num1][center_x // num2] == 1:
            level[center_y // num1][center_x // num2] = 0
            scor += DOT_SCORE
        if level[center_y // num1][center_x // num2] == 2:
            level[center_y // num1][center_x // num2] = 0
            scor += POWER_PELLET_SCORE
            power = True
            power_count = 0
            eaten_ghosts = [False, False, False, False]
    return scor, power, power_count, eaten_ghosts


def draw_board():
    num1 = ((HEIGHT - 50) // 32)
    num2 = (WIDTH // 30)
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            if level[i][j] == 2 and not flicker:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
            if level[i][j] == 3:
                pygame.draw.line(screen, color, (j * num2 + (0.5 * num2), i * num1),
                                 (j * num2 + (0.5 * num2), i * num1 + num1), 3)
            if level[i][j] == 4:
                pygame.draw.line(screen, color, (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            if level[i][j] == 5:
                pygame.draw.arc(screen, color, [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                0, PI / 2, 3)
            if level[i][j] == 6:
                pygame.draw.arc(screen, color,
                                [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1], PI / 2, PI, 3)
            if level[i][j] == 7:
                pygame.draw.arc(screen, color, [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1], PI,
                                3 * PI / 2, 3)
            if level[i][j] == 8:
                pygame.draw.arc(screen, color,
                                [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1], 3 * PI / 2,
                                2 * PI, 3)
            if level[i][j] == 9:
                pygame.draw.line(screen, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            if level[i][j] == 10:
                pygame.draw.rect(screen, color, [j * num2, i * num1, num2, num1])


def draw_player():
    # 0-RIGHT, 1-LEFT, 2-UP, 3-DOWN
    if direction == 0:
        screen.blit(player_images[counter // 5], (player_x, player_y))
    elif direction == 1:
        screen.blit(pygame.transform.flip(player_images[counter // 5], True, False), (player_x, player_y))
    elif direction == 2:
        screen.blit(pygame.transform.rotate(player_images[counter // 5], 90), (player_x, player_y))
    elif direction == 3:
        screen.blit(pygame.transform.rotate(player_images[counter // 5], 270), (player_x, player_y))


def check_position(centerx, centery):
    turns = [False, False, False, False]
    num1 = (HEIGHT - 50) // 32
    num2 = (WIDTH // 30)
    num3 = 15
    # check collisions based on center x and center y of player +/- fudge number
    if centerx // 30 < 29:
        if direction == 0:
            if level[centery // num1][(centerx - num3) // num2] < 3:
                turns[1] = True
        if direction == 1:
            if level[centery // num1][(centerx + num3) // num2] < 3:
                turns[0] = True
        if direction == 2:
            if level[(centery + num3) // num1][centerx // num2] < 3:
                turns[3] = True
        if direction == 3:
            if level[(centery - num3) // num1][centerx // num2] < 3:
                turns[2] = True

        if direction == 2 or direction == 3:
            if 12 <= centerx % num2 <= 18:
                if level[(centery + num3) // num1][centerx // num2] < 3:
                    turns[3] = True
                if level[(centery - num3) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if level[centery // num1][(centerx - num2) // num2] < 3:
                    turns[1] = True
                if level[centery // num1][(centerx + num2) // num2] < 3:
                    turns[0] = True
        if direction == 0 or direction == 1:
            if 12 <= centerx % num2 <= 18:
                if level[(centery + num1) // num1][centerx // num2] < 3:
                    turns[3] = True
                if level[(centery - num1) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if level[centery // num1][(centerx - num3) // num2] < 3:
                    turns[1] = True
                if level[centery // num1][(centerx + num3) // num2] < 3:
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True

    return turns


def move_player(play_x, play_y):
    # r, l, u, d
    if direction == 0 and turns_allowed[0]:
        play_x += player_speed
    elif direction == 1 and turns_allowed[1]:
        play_x -= player_speed
    if direction == 2 and turns_allowed[2]:
        play_y -= player_speed
    elif direction == 3 and turns_allowed[3]:
        play_y += player_speed
    return play_x, play_y


def _sticky_bfs_target(ghost_id, ghost, goal_tile):
    """Step toward goal_tile via BFS, but keep re-targeting the SAME
    waypoint TILE until the ghost's own tile actually becomes it, instead
    of recomputing a fresh one every frame. move_toward_target() (the
    shared mover) only fully reconsiders every direction -- including
    reversing course -- at a clean intersection; if the BFS target flips
    to the opposite direction while the ghost is still mid-corridor, the
    mover just keeps going the old way, so a target that changes before
    it's reached can leave the ghost thrashing back and forth instead of
    making steady progress. Arrival is checked by tile, not pixel
    distance to the tile's center: the mover steps one axis at a time, so
    a target that differs in both x and y is only ever closed one axis at
    a time, and a wall blocking the second axis right at that moment
    would otherwise leave the ghost sailing straight past a pixel-radius
    check forever."""
    global ghost_waypoints
    ghost_tile = _tile_of(ghost.x_pos, ghost.y_pos)
    waypoint_tile = ghost_waypoints[ghost_id]
    if waypoint_tile is None or ghost_tile == waypoint_tile:
        waypoint_tile = _bfs_next_tile(ghost_tile, goal_tile)
        ghost_waypoints[ghost_id] = waypoint_tile
    return _pixel_center_of(*waypoint_tile)


def _ghost_target(ghost_id, ghost, dead, going_home, eaten_this_combo, spawn):
    """One ghost's target for next frame, per the state it's in right now:
      1) eaten (eyes)      -> BFS shortest path to the ghost-house pocket
      2) walking home      -> BFS shortest path back to its own spawn corner
      3) edible & not yet eaten this combo -> flee: step to whichever of
         its own passable neighbor tiles is farthest from the player
      4) otherwise (normal, or revived-but-still-dangerous mid-powerup)
         -> chase: BFS shortest path to the player's current tile
    Eaten/going-home/chase all use the sticky BFS waypoint above -- a
    plain fixed pixel target (the pocket, a far-off corner) can leave the
    greedy mover committed the wrong way for the length of a whole
    corridor with nothing to make it reconsider until it hits a wall.
    Flee is a plain 1-step lookahead recomputed fresh every frame -- it
    never asks the mover to reverse mid-corridor, so it doesn't need
    stickiness.
    """
    if dead:
        return _sticky_bfs_target(ghost_id, ghost, EXIT_TILE)

    if going_home:
        spawn_tile = _tile_of(spawn[0], spawn[1])
        return _sticky_bfs_target(ghost_id, ghost, spawn_tile)

    if powerup and not eaten_this_combo:
        ghost_waypoints[ghost_id] = None
        ghost_tile = _tile_of(ghost.x_pos, ghost.y_pos)
        neighbor_offsets = ((0, 1), (0, -1), (-1, 0), (1, 0))  # R, L, U, D -- matches turns[] order
        player_tile = _tile_of(player_x, player_y)
        candidates = [
            (ghost_tile[0] + dr, ghost_tile[1] + dc)
            for i, (dr, dc) in enumerate(neighbor_offsets)
            if ghost.turns[i]
        ]
        if not candidates:
            return ghost.x_pos, ghost.y_pos
        farthest = max(
            candidates,
            key=lambda t: (t[0] - player_tile[0]) ** 2 + (t[1] - player_tile[1]) ** 2,
        )
        return _pixel_center_of(*farthest)

    player_tile = _tile_of(player_x, player_y)
    return _sticky_bfs_target(ghost_id, ghost, player_tile)


def get_targets():
    return [
        _ghost_target(0, blinky, blinky_dead, blinky_going_home, eaten_ghost[0], SPAWN_BLINKY),
        _ghost_target(1, inky, inky_dead, inky_going_home, eaten_ghost[1], SPAWN_INKY),
        _ghost_target(2, pinky, pinky_dead, pinky_going_home, eaten_ghost[2], SPAWN_PINKY),
        _ghost_target(3, clyde, clyde_dead, clyde_going_home, eaten_ghost[3], SPAWN_CLYDE),
    ]


run = True
while run:
    timer.tick(fps)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            run = False

    if game_state == STATE_MENU:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    menu_index = (menu_index - 1) % len(menu_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    menu_index = (menu_index + 1) % len(menu_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected = menu_options[menu_index]
                    if selected == 'Start Game':
                        start_new_game()
                        game_state = STATE_PLAYING
                    elif selected == 'Highscores':
                        game_state = STATE_HIGHSCORES
                    elif selected == 'Instructions':
                        game_state = STATE_INSTRUCTIONS
                    elif selected == 'Exit':
                        run = False
        screen.fill('black')
        draw_menu()

    elif game_state == STATE_INSTRUCTIONS:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                game_state = STATE_MENU
        screen.fill('black')
        draw_instructions()

    elif game_state == STATE_HIGHSCORES:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                game_state = STATE_MENU
        screen.fill('black')
        draw_highscores_screen()

    elif game_state == STATE_PAUSED:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == PAUSE_KEY:
                    game_state = STATE_PLAYING
                elif event.key == pygame.K_m:
                    game_state = STATE_MENU
        screen.fill('black')
        draw_board()
        draw_player()
        blinky.draw()
        inky.draw()
        pinky.draw()
        clyde.draw()
        draw_misc()
        draw_pause_overlay()

    elif game_state == STATE_GAME_OVER:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_highscore(name_input, score)
                    game_state = STATE_HIGHSCORES
                elif event.key == pygame.K_ESCAPE:
                    game_state = STATE_MENU
                elif event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif event.unicode.isalnum() and len(name_input) < NAME_INPUT_MAX_LEN:
                    name_input += event.unicode.upper()
        screen.fill('black')
        draw_game_over_screen()

    elif game_state == STATE_VICTORY:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_highscore(name_input, score)
                    game_state = STATE_HIGHSCORES
                elif event.key == pygame.K_ESCAPE:
                    game_state = STATE_MENU
                elif event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif event.unicode.isalnum() and len(name_input) < NAME_INPUT_MAX_LEN:
                    name_input += event.unicode.upper()
        screen.fill('black')
        draw_victory_screen()

    elif game_state == STATE_PLAYING:
        if counter < 19:
            counter += 1
            if counter > 3:
                flicker = False
        else:
            counter = 0
            flicker = True
        if powerup and power_counter < 600:
            power_counter += 1
        elif powerup and power_counter >= 600:
            power_counter = 0
            powerup = False
            eaten_ghost = [False, False, False, False]
        if startup_counter < 180 and not game_over and not game_won:
            moving = False
            startup_counter += 1
        else:
            moving = True

        if moving and not game_over and not game_won:
            level_time_remaining -= 1
            if level_time_remaining <= 0:
                lose_a_life()

        screen.fill('black')
        draw_board()
        center_x = player_x + 23
        center_y = player_y + 24
        if powerup:
            ghost_speeds = [1, 1, 1, 1]
        else:
            ghost_speeds = [2, 2, 2, 2]
        if eaten_ghost[0]:
            ghost_speeds[0] = 2
        if eaten_ghost[1]:
            ghost_speeds[1] = 2
        if eaten_ghost[2]:
            ghost_speeds[2] = 2
        if eaten_ghost[3]:
            ghost_speeds[3] = 2
        if blinky_dead:
            ghost_speeds[0] = 4
        if inky_dead:
            ghost_speeds[1] = 4
        if pinky_dead:
            ghost_speeds[2] = 4
        if clyde_dead:
            ghost_speeds[3] = 4

        level_cleared = True
        for i in range(len(level)):
            if 1 in level[i] or 2 in level[i]:
                level_cleared = False
        if level_cleared:
            advance_level()

        player_circle = pygame.draw.circle(screen, 'black', (center_x, center_y), 20, 2)
        draw_player()
        blinky = Ghost(blinky_x, blinky_y, targets[0], ghost_speeds[0], blinky_img, blinky_direction, blinky_dead,
                       blinky_box, 0)
        inky = Ghost(inky_x, inky_y, targets[1], ghost_speeds[1], inky_img, inky_direction, inky_dead,
                     inky_box, 1)
        pinky = Ghost(pinky_x, pinky_y, targets[2], ghost_speeds[2], pinky_img, pinky_direction, pinky_dead,
                      pinky_box, 2)
        clyde = Ghost(clyde_x, clyde_y, targets[3], ghost_speeds[3], clyde_img, clyde_direction, clyde_dead,
                      clyde_box, 3)
        draw_misc()
        targets = get_targets()

        turns_allowed = check_position(center_x, center_y)
        if moving:
            player_x, player_y = move_player(player_x, player_y)
            if not (blinky_dead and blinky.in_box):
                blinky_x, blinky_y, blinky_direction = blinky.move_toward_target()
            if not (inky_dead and inky.in_box):
                inky_x, inky_y, inky_direction = inky.move_toward_target()
            if not (pinky_dead and pinky.in_box):
                pinky_x, pinky_y, pinky_direction = pinky.move_toward_target()
            if not (clyde_dead and clyde.in_box):
                clyde_x, clyde_y, clyde_direction = clyde.move_toward_target()
        score, powerup, power_counter, eaten_ghost = check_collisions(score, powerup, power_counter, eaten_ghost)
        # add to if not powerup to check if eaten ghosts
        if not powerup:
            if (player_circle.colliderect(blinky.rect) and not blinky.dead) or \
                    (player_circle.colliderect(inky.rect) and not inky.dead) or \
                    (player_circle.colliderect(pinky.rect) and not pinky.dead) or \
                    (player_circle.colliderect(clyde.rect) and not clyde.dead):
                lose_a_life()
        if powerup and player_circle.colliderect(blinky.rect) and eaten_ghost[0] and not blinky.dead:
            lose_a_life()
        if powerup and player_circle.colliderect(inky.rect) and eaten_ghost[1] and not inky.dead:
            lose_a_life()
        if powerup and player_circle.colliderect(pinky.rect) and eaten_ghost[2] and not pinky.dead:
            lose_a_life()
        if powerup and player_circle.colliderect(clyde.rect) and eaten_ghost[3] and not clyde.dead:
            lose_a_life()
        if powerup and player_circle.colliderect(blinky.rect) and not blinky.dead and not eaten_ghost[0]:
            blinky_dead = True
            eaten_ghost[0] = True
            score += (2 ** eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if powerup and player_circle.colliderect(inky.rect) and not inky.dead and not eaten_ghost[1]:
            inky_dead = True
            eaten_ghost[1] = True
            score += (2 ** eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if powerup and player_circle.colliderect(pinky.rect) and not pinky.dead and not eaten_ghost[2]:
            pinky_dead = True
            eaten_ghost[2] = True
            score += (2 ** eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if powerup and player_circle.colliderect(clyde.rect) and not clyde.dead and not eaten_ghost[3]:
            clyde_dead = True
            eaten_ghost[3] = True
            score += (2 ** eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == PAUSE_KEY:
                    game_state = STATE_PAUSED
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    direction_command = 0
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    direction_command = 1
                if event.key in (pygame.K_UP, pygame.K_w):
                    direction_command = 2
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    direction_command = 3

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_RIGHT, pygame.K_d) and direction_command == 0:
                    direction_command = direction
                if event.key in (pygame.K_LEFT, pygame.K_a) and direction_command == 1:
                    direction_command = direction
                if event.key in (pygame.K_UP, pygame.K_w) and direction_command == 2:
                    direction_command = direction
                if event.key in (pygame.K_DOWN, pygame.K_s) and direction_command == 3:
                    direction_command = direction

        if direction_command == 0 and turns_allowed[0]:
            direction = 0
        if direction_command == 1 and turns_allowed[1]:
            direction = 1
        if direction_command == 2 and turns_allowed[2]:
            direction = 2
        if direction_command == 3 and turns_allowed[3]:
            direction = 3

        if player_x > 900:
            player_x = -47
        elif player_x < -50:
            player_x = 897

        blinky_dead, blinky_respawn_timer, blinky_going_home = _update_ghost_respawn(
            blinky_dead, blinky.in_box, blinky_respawn_timer, blinky_going_home, blinky_x, blinky_y, SPAWN_BLINKY)
        inky_dead, inky_respawn_timer, inky_going_home = _update_ghost_respawn(
            inky_dead, inky.in_box, inky_respawn_timer, inky_going_home, inky_x, inky_y, SPAWN_INKY)
        pinky_dead, pinky_respawn_timer, pinky_going_home = _update_ghost_respawn(
            pinky_dead, pinky.in_box, pinky_respawn_timer, pinky_going_home, pinky_x, pinky_y, SPAWN_PINKY)
        clyde_dead, clyde_respawn_timer, clyde_going_home = _update_ghost_respawn(
            clyde_dead, clyde.in_box, clyde_respawn_timer, clyde_going_home, clyde_x, clyde_y, SPAWN_CLYDE)


    pygame.display.flip()
pygame.quit()
