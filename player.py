import pygame

from config import DOT_SCORE, HEIGHT, POWER_PELLET_SCORE, WIDTH
import state


def check_collisions(scor, power, power_count, eaten_ghosts):
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    center_x = state.player_x + 23
    center_y = state.player_y + 24
    if 0 < state.player_x < 870:
        if state.level[center_y // num1][center_x // num2] == 1:
            state.level[center_y // num1][center_x // num2] = 0
            scor += DOT_SCORE
        if state.level[center_y // num1][center_x // num2] == 2:
            state.level[center_y // num1][center_x // num2] = 0
            scor += POWER_PELLET_SCORE
            power = True
            power_count = 0
            eaten_ghosts = [False, False, False, False]
    return scor, power, power_count, eaten_ghosts


def check_position(centerx, centery):
    turns = [False, False, False, False]
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    num3 = 15
    if centerx // 30 < 29:
        if state.direction == 0:
            if state.level[centery // num1][(centerx - num3) // num2] < 3:
                turns[1] = True
        if state.direction == 1:
            if state.level[centery // num1][(centerx + num3) // num2] < 3:
                turns[0] = True
        if state.direction == 2:
            if state.level[(centery + num3) // num1][centerx // num2] < 3:
                turns[3] = True
        if state.direction == 3:
            if state.level[(centery - num3) // num1][centerx // num2] < 3:
                turns[2] = True

        if state.direction == 2 or state.direction == 3:
            if 12 <= centerx % num2 <= 18:
                if state.level[(centery + num3) // num1][centerx // num2] < 3:
                    turns[3] = True
                if state.level[(centery - num3) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if state.level[centery // num1][(centerx - num2) // num2] < 3:
                    turns[1] = True
                if state.level[centery // num1][(centerx + num2) // num2] < 3:
                    turns[0] = True
        if state.direction == 0 or state.direction == 1:
            if 12 <= centerx % num2 <= 18:
                if state.level[(centery + num1) // num1][centerx // num2] < 3:
                    turns[3] = True
                if state.level[(centery - num1) // num1][centerx // num2] < 3:
                    turns[2] = True
            if 12 <= centery % num1 <= 18:
                if state.level[centery // num1][(centerx - num3) // num2] < 3:
                    turns[1] = True
                if state.level[centery // num1][(centerx + num3) // num2] < 3:
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True

    return turns


def move_player(play_x, play_y):
    if state.direction == 0 and state.turns_allowed[0]:
        play_x += state.player_speed
    elif state.direction == 1 and state.turns_allowed[1]:
        play_x -= state.player_speed
    if state.direction == 2 and state.turns_allowed[2]:
        play_y -= state.player_speed
    elif state.direction == 3 and state.turns_allowed[3]:
        play_y += state.player_speed
    return play_x, play_y


def update_direction_from_input():
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
        state.direction_command = 0
    elif pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
        state.direction_command = 1
    elif pressed[pygame.K_UP] or pressed[pygame.K_w]:
        state.direction_command = 2
    elif pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
        state.direction_command = 3
    else:
        state.direction_command = state.direction
