from collections import deque

import pygame

from assets import dead_img, screen, spooked_img
from config import GHOST_HOME_ARRIVAL_RADIUS, HEIGHT, WIDTH
import state
from state import GHOST_RESPAWN_DELAY_FRAMES


def tile_of(x_pos, y_pos):
    """Tile (row, col) a ghost/player pixel top-left position sits in."""
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    return (y_pos + 22) // num1, (x_pos + 22) // num2


def pixel_center_of(row, col):
    """Ghost top-left (x_pos, y_pos) centered on a tile."""
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    return col * num2 + num2 // 2 - 22, row * num1 + num1 // 2 - 22


def bfs_next_tile(start_tile, goal_tile):
    """First step of the shortest path from start_tile to goal_tile."""
    if start_tile == goal_tile:
        return start_tile
    rows, cols = len(state.level), len(state.level[0])
    start_r, start_c = start_tile
    goal_r, goal_c = goal_tile
    if not (0 <= start_r < rows and 0 <= start_c < cols
            and 0 <= goal_r < rows and 0 <= goal_c < cols):
        return start_tile

    def passable(r, c):
        v = state.level[r][c]
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


def update_ghost_respawn(dead, in_box, timer, going_home, x_pos, y_pos, spawn):
    """Advance one ghost's eaten -> waiting -> walking-home state machine."""
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


class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, ghost_id):
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
        self.id = ghost_id
        self.turns, self.in_box = self.check_collisions()
        self.rect = self.draw()

    def draw(self):
        if (not state.powerup and not self.dead) or (
                state.eaten_ghost[self.id] and state.powerup and not self.dead):
            screen.blit(self.img, (self.x_pos, self.y_pos))
        elif state.powerup and not self.dead and not state.eaten_ghost[self.id]:
            screen.blit(spooked_img, (self.x_pos, self.y_pos))
        else:
            screen.blit(dead_img, (self.x_pos, self.y_pos))
        ghost_rect = pygame.rect.Rect(
            (self.center_x - 18, self.center_y - 18), (36, 36)
        )
        return ghost_rect

    def check_collisions(self):
        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30
        num3 = 15
        self.turns = [False, False, False, False]
        if 0 < self.center_x // 30 < 29:
            if state.level[(self.center_y - num3) // num1][self.center_x // num2] == 9:
                self.turns[2] = True
            if state.level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                    or (state.level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if state.level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                    or (state.level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if state.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                    or (state.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if state.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                    or (state.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= self.center_x % num2 <= 18:
                    if state.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (state.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if state.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (state.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if state.level[self.center_y // num1][(self.center_x - num2) // num2] < 3 \
                            or (state.level[self.center_y // num1][(self.center_x - num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if state.level[self.center_y // num1][(self.center_x + num2) // num2] < 3 \
                            or (state.level[self.center_y // num1][(self.center_x + num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= self.center_x % num2 <= 18:
                    if state.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (state.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if state.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (state.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if state.level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                            or (state.level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if state.level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                            or (state.level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True
        box_ref_x, box_ref_y = (
            (self.center_x, self.center_y) if state.BOX_USE_CENTER else (self.x_pos, self.y_pos)
        )
        if state.BOX_X0 < box_ref_x < state.BOX_X1 and state.BOX_Y0 < box_ref_y < state.BOX_Y1:
            self.in_box = True
        else:
            self.in_box = False
        return self.turns, self.in_box

    def move_toward_target(self):
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


def sticky_bfs_target(ghost_id, ghost, goal_tile):
    """Step toward goal_tile via BFS with a sticky waypoint."""
    ghost_tile = tile_of(ghost.x_pos, ghost.y_pos)
    waypoint_tile = state.ghost_waypoints[ghost_id]
    if waypoint_tile is None or ghost_tile == waypoint_tile:
        waypoint_tile = bfs_next_tile(ghost_tile, goal_tile)
        state.ghost_waypoints[ghost_id] = waypoint_tile
    return pixel_center_of(*waypoint_tile)


def ghost_target(ghost_id, ghost, dead, going_home, eaten_this_combo, spawn):
    """One ghost's target for the next frame."""
    if dead:
        return sticky_bfs_target(ghost_id, ghost, state.EXIT_TILE)

    if going_home:
        spawn_tile = tile_of(spawn[0], spawn[1])
        return sticky_bfs_target(ghost_id, ghost, spawn_tile)

    if state.powerup and not eaten_this_combo:
        state.ghost_waypoints[ghost_id] = None
        ghost_tile = tile_of(ghost.x_pos, ghost.y_pos)
        neighbor_offsets = ((0, 1), (0, -1), (-1, 0), (1, 0))
        player_tile = tile_of(state.player_x, state.player_y)
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
        return pixel_center_of(*farthest)

    player_tile = tile_of(state.player_x, state.player_y)
    return sticky_bfs_target(ghost_id, ghost, player_tile)


def get_targets(blinky, inky, pinky, clyde):
    return [
        ghost_target(0, blinky, state.blinky_dead, state.blinky_going_home,
                     state.eaten_ghost[0], state.SPAWN_BLINKY),
        ghost_target(1, inky, state.inky_dead, state.inky_going_home,
                     state.eaten_ghost[1], state.SPAWN_INKY),
        ghost_target(2, pinky, state.pinky_dead, state.pinky_going_home,
                     state.eaten_ghost[2], state.SPAWN_PINKY),
        ghost_target(3, clyde, state.clyde_dead, state.clyde_going_home,
                     state.eaten_ghost[3], state.SPAWN_CLYDE),
    ]
