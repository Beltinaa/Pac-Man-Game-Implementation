import pygame

import assets
from assets import screen, timer
import theme as theme_module
from config import (
    CHEATS_ENABLED,
    FPS,
    GHOST_EAT_BASE_SCORE,
    NAME_INPUT_MAX_LEN,
    PAUSE_KEY,
    PLAYER_SPEED_BOOSTED,
    PLAYER_SPEED_NORMAL,
    STATE_GAME_OVER,
    STATE_HIGHSCORES,
    STATE_INSTRUCTIONS,
    STATE_MENU,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_VICTORY,
)
from ghosts import Ghost, get_targets, update_ghost_respawn
from highscores import save_highscore
from level import advance_level, init_game, lose_a_life, start_new_game
from player import check_collisions, check_position, move_player, update_direction_from_input
import state
from ui import (
    draw_board,
    draw_game_over_screen,
    draw_highscores_screen,
    draw_instructions,
    draw_menu,
    draw_misc,
    draw_pause_overlay,
    draw_player,
    draw_victory_screen,
    character_at,
    sound_button_rect,
)
import audio

def return_to_menu():
    """Go back to the main menu and clear the chosen character.

    The menu shows the picker with nothing selected and runs silent, so the
    theme has to be released on the way out -- otherwise the next visit would
    show a pre-picked character and keep playing the previous skin's music.
    """
    audio.stop()
    theme_module.ACTIVE = None
    state.game_state = STATE_MENU


def choose_character(name):
    """Pick a skin and start its music.

    The main menu deliberately runs silent: no character has been chosen
    there, so there is no theme and no soundtrack to play. Picking one is
    what loads and starts the track.
    """
    if theme_module.ACTIVE is not None and theme_module.ACTIVE.name == name:
        return
    theme_module.set_active(name)
    audio.play_theme()


init_game()
audio.init()

run = True
while run:
    timer.tick(FPS)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            run = False
        # Handled here, before the per-state branches, so the HUD sound
        # button works in every screen that draws it.
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if sound_button_rect().collidepoint(event.pos):
                audio.toggle()

    if state.game_state == STATE_MENU:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                picked = character_at(event.pos)
                if picked is not None:
                    choose_character(picked)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    state.menu_index = (state.menu_index - 1) % len(state.menu_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    state.menu_index = (state.menu_index + 1) % len(state.menu_options)
                elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    # step through the character portraits
                    names = theme_module.names()
                    step = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                    current = (names.index(theme_module.ACTIVE.name)
                               if theme_module.ACTIVE is not None else -step)
                    choose_character(names[(current + step) % len(names)])
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected = state.menu_options[state.menu_index]
                    if selected == 'Start Game':
                        if theme_module.ACTIVE is None:
                            # nothing chosen yet: treat ENTER as picking the
                            # first character rather than silently doing
                            # nothing, so the menu always responds
                            choose_character(theme_module.names()[0])
                        else:
                            start_new_game()
                            state.game_state = STATE_PLAYING
                    elif selected == 'Highscores':
                        state.game_state = STATE_HIGHSCORES
                    elif selected == 'Instructions':
                        state.game_state = STATE_INSTRUCTIONS
                    elif selected == 'Exit':
                        run = False
        screen.fill(theme_module.active().wall_interior)
        draw_menu()

    elif state.game_state == STATE_INSTRUCTIONS:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return_to_menu()
        screen.fill(theme_module.active().wall_interior)
        draw_instructions()

    elif state.game_state == STATE_HIGHSCORES:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return_to_menu()
        screen.fill(theme_module.active().wall_interior)
        draw_highscores_screen()

    elif state.game_state == STATE_PAUSED:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (PAUSE_KEY, pygame.K_r):
                    state.game_state = STATE_PLAYING
                elif event.key == pygame.K_m:
                    return_to_menu()
        screen.fill(theme_module.active().wall_interior)
        draw_board()
        draw_player()
        blinky = Ghost(
            state.blinky_x, state.blinky_y, state.targets[0], state.ghost_speeds[0],
            assets.bundle().blinky_img, state.blinky_direction, state.blinky_dead, state.blinky_box, 0,
        )
        inky = Ghost(
            state.inky_x, state.inky_y, state.targets[1], state.ghost_speeds[1],
            assets.bundle().inky_img, state.inky_direction, state.inky_dead, state.inky_box, 1,
        )
        pinky = Ghost(
            state.pinky_x, state.pinky_y, state.targets[2], state.ghost_speeds[2],
            assets.bundle().pinky_img, state.pinky_direction, state.pinky_dead, state.pinky_box, 2,
        )
        clyde = Ghost(
            state.clyde_x, state.clyde_y, state.targets[3], state.ghost_speeds[3],
            assets.bundle().clyde_img, state.clyde_direction, state.clyde_dead, state.clyde_box, 3,
        )
        blinky.draw()
        inky.draw()
        pinky.draw()
        clyde.draw()
        draw_misc()
        draw_pause_overlay()

    elif state.game_state == STATE_GAME_OVER:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_highscore(state.name_input, state.score)
                    state.game_state = STATE_HIGHSCORES
                elif event.key == pygame.K_ESCAPE:
                    return_to_menu()
                elif event.key == pygame.K_BACKSPACE:
                    state.name_input = state.name_input[:-1]
                elif event.unicode.isalnum() and len(state.name_input) < NAME_INPUT_MAX_LEN:
                    state.name_input += event.unicode.upper()
        screen.fill(theme_module.active().wall_interior)
        draw_game_over_screen()

    elif state.game_state == STATE_VICTORY:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_highscore(state.name_input, state.score)
                    state.game_state = STATE_HIGHSCORES
                elif event.key == pygame.K_ESCAPE:
                    return_to_menu()
                elif event.key == pygame.K_BACKSPACE:
                    state.name_input = state.name_input[:-1]
                elif event.unicode.isalnum() and len(state.name_input) < NAME_INPUT_MAX_LEN:
                    state.name_input += event.unicode.upper()
        screen.fill(theme_module.active().wall_interior)
        draw_victory_screen()

    elif state.game_state == STATE_PLAYING:
        if state.counter < 19:
            state.counter += 1
            if state.counter > 3:
                state.flicker = False
        else:
            state.counter = 0
            state.flicker = True
        if state.powerup and state.power_counter < 600:
            state.power_counter += 1
        elif state.powerup and state.power_counter >= 600:
            state.power_counter = 0
            state.powerup = False
            state.eaten_ghost = [False, False, False, False]
        if state.startup_counter < 180 and not state.game_over and not state.game_won:
            state.moving = False
            state.startup_counter += 1
        else:
            state.moving = True

        if state.moving and not state.game_over and not state.game_won:
            state.level_time_remaining -= 1
            if state.level_time_remaining <= 0:
                lose_a_life()

        screen.fill(theme_module.active().wall_interior)
        draw_board()
        center_x = state.player_x + 23
        center_y = state.player_y + 24
        if state.cheat_ghosts_frozen:
            # Freeze is absolute while active, so even ghosts that are returning
            # to base or have been marked dead still stay motionless.
            state.ghost_speeds = [0, 0, 0, 0]
        else:
            state.ghost_speeds = [1, 1, 1, 1]
            if state.eaten_ghost[0]:
                state.ghost_speeds[0] = 1
            if state.eaten_ghost[1]:
                state.ghost_speeds[1] = 1
            if state.eaten_ghost[2]:
                state.ghost_speeds[2] = 1
            if state.eaten_ghost[3]:
                state.ghost_speeds[3] = 1
            if state.blinky_dead:
                state.ghost_speeds[0] = 4
            if state.inky_dead:
                state.ghost_speeds[1] = 4
            if state.pinky_dead:
                state.ghost_speeds[2] = 4
            if state.clyde_dead:
                state.ghost_speeds[3] = 4

        level_cleared = True
        for i in range(len(state.level)):
            if 1 in state.level[i] or 2 in state.level[i]:
                level_cleared = False
        if level_cleared:
            advance_level()

        player_circle = pygame.draw.circle(screen, 'black', (center_x, center_y), 20, 2)
        draw_player()
        blinky = Ghost(
            state.blinky_x, state.blinky_y, state.targets[0], state.ghost_speeds[0],
            assets.bundle().blinky_img, state.blinky_direction, state.blinky_dead, state.blinky_box, 0,
        )
        inky = Ghost(
            state.inky_x, state.inky_y, state.targets[1], state.ghost_speeds[1],
            assets.bundle().inky_img, state.inky_direction, state.inky_dead, state.inky_box, 1,
        )
        pinky = Ghost(
            state.pinky_x, state.pinky_y, state.targets[2], state.ghost_speeds[2],
            assets.bundle().pinky_img, state.pinky_direction, state.pinky_dead, state.pinky_box, 2,
        )
        clyde = Ghost(
            state.clyde_x, state.clyde_y, state.targets[3], state.ghost_speeds[3],
            assets.bundle().clyde_img, state.clyde_direction, state.clyde_dead, state.clyde_box, 3,
        )
        draw_misc()
        state.targets = get_targets(blinky, inky, pinky, clyde)

        state.turns_allowed = check_position(center_x, center_y)
        if state.moving:
            state.player_speed = PLAYER_SPEED_BOOSTED if state.cheat_speed_boost else PLAYER_SPEED_NORMAL
            state.player_x, state.player_y = move_player(state.player_x, state.player_y)
            if not (state.blinky_dead and blinky.in_box):
                state.blinky_x, state.blinky_y, state.blinky_direction = blinky.move_toward_target()
            if not (state.inky_dead and inky.in_box):
                state.inky_x, state.inky_y, state.inky_direction = inky.move_toward_target()
            if not (state.pinky_dead and pinky.in_box):
                state.pinky_x, state.pinky_y, state.pinky_direction = pinky.move_toward_target()
            if not (state.clyde_dead and clyde.in_box):
                state.clyde_x, state.clyde_y, state.clyde_direction = clyde.move_toward_target()
        state.score, state.powerup, state.power_counter, state.eaten_ghost = check_collisions(
            state.score, state.powerup, state.power_counter, state.eaten_ghost,
        )
        if not state.powerup:
            if (player_circle.colliderect(blinky.rect) and not blinky.dead) or \
                    (player_circle.colliderect(inky.rect) and not inky.dead) or \
                    (player_circle.colliderect(pinky.rect) and not pinky.dead) or \
                    (player_circle.colliderect(clyde.rect) and not clyde.dead):
                lose_a_life()
        if state.powerup and player_circle.colliderect(blinky.rect) and state.eaten_ghost[0] and not blinky.dead:
            lose_a_life()
        if state.powerup and player_circle.colliderect(inky.rect) and state.eaten_ghost[1] and not inky.dead:
            lose_a_life()
        if state.powerup and player_circle.colliderect(pinky.rect) and state.eaten_ghost[2] and not pinky.dead:
            lose_a_life()
        if state.powerup and player_circle.colliderect(clyde.rect) and state.eaten_ghost[3] and not clyde.dead:
            lose_a_life()
        if state.powerup and player_circle.colliderect(blinky.rect) and not blinky.dead and not state.eaten_ghost[0]:
            state.blinky_dead = True
            state.eaten_ghost[0] = True
            state.score += (2 ** state.eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if state.powerup and player_circle.colliderect(inky.rect) and not inky.dead and not state.eaten_ghost[1]:
            state.inky_dead = True
            state.eaten_ghost[1] = True
            state.score += (2 ** state.eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if state.powerup and player_circle.colliderect(pinky.rect) and not pinky.dead and not state.eaten_ghost[2]:
            state.pinky_dead = True
            state.eaten_ghost[2] = True
            state.score += (2 ** state.eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE
        if state.powerup and player_circle.colliderect(clyde.rect) and not clyde.dead and not state.eaten_ghost[3]:
            state.clyde_dead = True
            state.eaten_ghost[3] = True
            state.score += (2 ** state.eaten_ghost.count(True)) * GHOST_EAT_BASE_SCORE

        update_direction_from_input()

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (PAUSE_KEY, pygame.K_p):
                    state.game_state = STATE_PAUSED

                if CHEATS_ENABLED:
                    if event.key == pygame.K_F1:
                        state.lives += 1
                    if event.key == pygame.K_F2:
                        for row in state.level:
                            for i in range(len(row)):
                                if row[i] in (1, 2):
                                    row[i] = 0
                    if event.key == pygame.K_F3:
                        state.cheat_invincible = not state.cheat_invincible
                    if event.key == pygame.K_F4:
                        state.cheat_ghosts_frozen = not state.cheat_ghosts_frozen
                    if event.key == pygame.K_F5:
                        state.cheat_speed_boost = not state.cheat_speed_boost

        if state.direction_command == 0 and state.turns_allowed[0]:
            state.direction = 0
        if state.direction_command == 1 and state.turns_allowed[1]:
            state.direction = 1
        if state.direction_command == 2 and state.turns_allowed[2]:
            state.direction = 2
        if state.direction_command == 3 and state.turns_allowed[3]:
            state.direction = 3

        if state.player_x > 900:
            state.player_x = -47
        elif state.player_x < -50:
            state.player_x = 897

        state.blinky_dead, state.blinky_respawn_timer, state.blinky_going_home = update_ghost_respawn(
            state.blinky_dead, blinky.in_box, state.blinky_respawn_timer,
            state.blinky_going_home, state.blinky_x, state.blinky_y, state.SPAWN_BLINKY,
        )
        state.inky_dead, state.inky_respawn_timer, state.inky_going_home = update_ghost_respawn(
            state.inky_dead, inky.in_box, state.inky_respawn_timer,
            state.inky_going_home, state.inky_x, state.inky_y, state.SPAWN_INKY,
        )
        state.pinky_dead, state.pinky_respawn_timer, state.pinky_going_home = update_ghost_respawn(
            state.pinky_dead, pinky.in_box, state.pinky_respawn_timer,
            state.pinky_going_home, state.pinky_x, state.pinky_y, state.SPAWN_PINKY,
        )
        state.clyde_dead, state.clyde_respawn_timer, state.clyde_going_home = update_ghost_respawn(
            state.clyde_dead, clyde.in_box, state.clyde_respawn_timer,
            state.clyde_going_home, state.clyde_x, state.clyde_y, state.SPAWN_CLYDE,
        )

    pygame.display.flip()
pygame.quit()
