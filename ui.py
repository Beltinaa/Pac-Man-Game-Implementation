import pygame

from assets import PI, color, font, player_images, screen, title_font
from config import CHEATS_ENABLED, FPS, HEIGHT, NAME_INPUT_MAX_LEN, TOTAL_LEVELS, WIDTH
from highscores import load_highscores
import state


def draw_misc():
    score_text = font.render(f'Score: {state.score}', True, 'white')
    screen.blit(score_text, (10, 920))
    level_text = font.render(
        f'Level: {state.current_level}/{TOTAL_LEVELS}', True, 'white'
    )
    screen.blit(level_text, (200, 920))
    time_text = font.render(
        f'Time: {max(0, state.level_time_remaining) // FPS}s', True, 'white'
    )
    screen.blit(time_text, (400, 920))
    if state.powerup:
        pygame.draw.circle(screen, 'blue', (140, 930), 15)
    for i in range(state.lives):
        screen.blit(
            pygame.transform.scale(player_images[0], (30, 30)),
            (650 + i * 40, 915),
        )
    draw_cheat_indicator()


def draw_cheat_indicator():
    if not CHEATS_ENABLED:
        return

    active_cheats = []
    if state.cheat_invincible:
        active_cheats.append(('INVINCIBLE', 'cyan'))
    if state.cheat_ghosts_frozen:
        active_cheats.append(('FROZEN', 'orange'))
    if state.cheat_speed_boost:
        active_cheats.append(('SPEED BOOST', 'lime'))

    if not active_cheats:
        return

    for index, (label, color) in enumerate(active_cheats):
        text = font.render(label, True, color)
        screen.blit(text, text.get_rect(topright=(WIDTH - 20, 20 + index * 28)))


def draw_menu():
    title = title_font.render('PAC-MAN', True, 'yellow')
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
    for i, label in enumerate(state.menu_options):
        label_color = 'yellow' if i == state.menu_index else 'white'
        prefix = '> ' if i == state.menu_index else '  '
        text = font.render(prefix + label, True, label_color)
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 420 + i * 50)))
    hint = font.render('UP/DOWN to choose, ENTER to select', True, 'gray')
    screen.blit(
        hint,
        hint.get_rect(center=(WIDTH // 2, 420 + len(state.menu_options) * 50 + 40)),
    )


def draw_instructions():
    lines = [
        'HOW TO PLAY',
        '',
        'Move: Arrow Keys or WASD',
        'Eat every pacgum and super-pacgum to clear a level.',
        'A super-pacgum makes the ghosts edible for a short time --',
        'eat them for bonus points before it wears off.',
        'Touching a non-edible ghost costs you a life.',
        '',
        'Pause: ESC or P',
        '',
        'Press ESC or ENTER to return to the menu',
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, 'white')
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 180 + i * 40)))

    if CHEATS_ENABLED:
        cheat_title = font.render('Debug / Cheat Mode:', True, 'gray')
        screen.blit(cheat_title, cheat_title.get_rect(center=(WIDTH // 2, 180 + len(lines) * 40 + 20)))
        cheat_lines = [
            'F1: +1 life',
            'F2: clear all pacgums',
            'F3: toggle invincibility',
            'F4: toggle ghost freeze',
            'F5: toggle speed boost',
        ]
        for i, line in enumerate(cheat_lines):
            text = font.render(line, True, 'gray')
            screen.blit(text, text.get_rect(center=(WIDTH // 2, 180 + len(lines) * 40 + 60 + i * 28)))


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
    hint = font.render('R: Resume     M: Main Menu', True, 'white')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def draw_name_entry_screen(title_text, title_color, subtitle=None):
    title = title_font.render(title_text, True, title_color)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
    y = 300
    if subtitle:
        sub = font.render(subtitle, True, 'white')
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, y)))
        y += 40
    text = font.render(f'Final score: {state.score}', True, 'white')
    screen.blit(text, text.get_rect(center=(WIDTH // 2, y)))
    y += 80
    prompt = font.render('Enter your name for the highscore list:', True, 'white')
    screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, y)))
    y += 50
    box_text = font.render((state.name_input or '') + '_', True, 'yellow')
    screen.blit(box_text, box_text.get_rect(center=(WIDTH // 2, y)))
    y += 60
    hint = font.render('ENTER to save     BACKSPACE to edit     ESC to skip', True, 'gray')
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, y)))


def draw_game_over_screen():
    draw_name_entry_screen('GAME OVER', 'red')


def draw_victory_screen():
    draw_name_entry_screen(
        'VICTORY!', 'green', subtitle=f'You cleared all {TOTAL_LEVELS} levels!'
    )


def draw_board():
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    for i in range(len(state.level)):
        for j in range(len(state.level[i])):
            if state.level[i][j] == 1:
                pygame.draw.circle(
                    screen, 'white',
                    (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4,
                )
            if state.level[i][j] == 2 and not state.flicker:
                pygame.draw.circle(
                    screen, 'white',
                    (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10,
                )
            if state.level[i][j] == 3:
                pygame.draw.line(
                    screen, color,
                    (j * num2 + (0.5 * num2), i * num1),
                    (j * num2 + (0.5 * num2), i * num1 + num1), 3,
                )
            if state.level[i][j] == 4:
                pygame.draw.line(
                    screen, color,
                    (j * num2, i * num1 + (0.5 * num1)),
                    (j * num2 + num2, i * num1 + (0.5 * num1)), 3,
                )
            if state.level[i][j] == 5:
                pygame.draw.arc(
                    screen, color,
                    [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                    0, PI / 2, 3,
                )
            if state.level[i][j] == 6:
                pygame.draw.arc(
                    screen, color,
                    [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1],
                    PI / 2, PI, 3,
                )
            if state.level[i][j] == 7:
                pygame.draw.arc(
                    screen, color,
                    [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1],
                    PI, 3 * PI / 2, 3,
                )
            if state.level[i][j] == 8:
                pygame.draw.arc(
                    screen, color,
                    [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1],
                    3 * PI / 2, 2 * PI, 3,
                )
            if state.level[i][j] == 9:
                pygame.draw.line(
                    screen, 'white',
                    (j * num2, i * num1 + (0.5 * num1)),
                    (j * num2 + num2, i * num1 + (0.5 * num1)), 3,
                )
            if state.level[i][j] == 10:
                pygame.draw.rect(screen, color, [j * num2, i * num1, num2, num1])


def draw_player():
    if state.direction == 0:
        screen.blit(player_images[state.counter // 5], (state.player_x, state.player_y))
    elif state.direction == 1:
        screen.blit(
            pygame.transform.flip(player_images[state.counter // 5], True, False),
            (state.player_x, state.player_y),
        )
    elif state.direction == 2:
        screen.blit(
            pygame.transform.rotate(player_images[state.counter // 5], 90),
            (state.player_x, state.player_y),
        )
    elif state.direction == 3:
        screen.blit(
            pygame.transform.rotate(player_images[state.counter // 5], 270),
            (state.player_x, state.player_y),
        )
