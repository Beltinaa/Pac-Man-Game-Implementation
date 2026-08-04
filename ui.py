import pygame

from assets import THEME, font, player_images, screen, title_font
from config import CHEATS_ENABLED, FPS, HEIGHT, NAME_INPUT_MAX_LEN, TOTAL_LEVELS, WIDTH
from highscores import load_highscores
import state
from walls import render_wall_layer
import audio

# HUD cheat badges: the gap between the timer readout (x=400) and the life
# icons (x=650), vertically centred on the HUD text baseline.
CHEAT_BADGE_X = 560
CHEAT_BADGE_Y = 930
CHEAT_BADGE_RADIUS = 14
CHEAT_BADGE_SPACING = 34

# Sound button: far right of the HUD strip, clear of the life icons.
SOUND_BUTTON_CENTER = (865, 930)
SOUND_BUTTON_RADIUS = 18
# Life icons are 30px wide on a 40px pitch starting at x=650. Four of them
# reach x=800, still clear of the button's left edge at 847; beyond that they
# are summarised as "+N" so a cheat-inflated life count cannot run into it.
LIFE_ICON_X = 650
LIFE_ICON_PITCH = 40
MAX_LIFE_ICONS = 4


def draw_misc():
    score_text = font.render(f'Score: {state.score}', True, THEME.hud_text)
    screen.blit(score_text, (10, 920))
    level_text = font.render(
        f'Level: {state.current_level}/{TOTAL_LEVELS}', True, THEME.hud_text
    )
    screen.blit(level_text, (200, 920))
    time_text = font.render(
        f'Time: {max(0, state.level_time_remaining) // FPS}s', True, THEME.hud_text
    )
    screen.blit(time_text, (400, 920))
    if state.powerup:
        pygame.draw.circle(screen, THEME.accent, (140, 930), 15)
    shown = min(state.lives, MAX_LIFE_ICONS)
    for i in range(shown):
        screen.blit(
            pygame.transform.scale(player_images[0], (30, 30)),
            (LIFE_ICON_X + i * LIFE_ICON_PITCH, 915),
        )
    if state.lives > shown:
        extra = font.render(f'+{state.lives - shown}', True, THEME.hud_text)
        screen.blit(extra, extra.get_rect(
            midleft=(LIFE_ICON_X + shown * LIFE_ICON_PITCH, 930)))
    draw_cheat_indicator()
    draw_sound_button()


def sound_button_rect():
    """Clickable area of the HUD sound button."""
    cx, cy = SOUND_BUTTON_CENTER
    r = SOUND_BUTTON_RADIUS
    return pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)


def draw_sound_button():
    """Speaker icon in the HUD strip: on, off, or unavailable.

    Drawn in the band below the maze (y >= 900) at the far right, past the
    life icons, so it never covers the board or another readout. The icon is
    vector-drawn rather than an image so it needs no new asset and picks up
    the theme colours.

    The icon says two independent things, which is what the first version
    got wrong: it lit up only when `sound_enabled and audio.available`, so on a
    machine with no working audio -- a pygame built without SDL_mixer, or no
    music file yet -- clicking flipped the flag while the icon stayed
    identical, and the button looked dead.

      * switch position, always: waves = on, slash = off. This follows
        `sound_enabled` alone, so every click visibly changes something.
      * whether audio can actually play: full brightness when it can, half
        when it cannot. audio.init() prints the reason once at startup.
    """
    cx, cy = SOUND_BUTTON_CENTER
    on = state.sound_enabled
    usable = audio.available
    hovered = sound_button_rect().collidepoint(pygame.mouse.get_pos())

    base = THEME.accent if on else (150, 150, 150)
    # dimmed to half when nothing can actually play
    color = base if usable else tuple(channel // 2 for channel in base)

    # hover highlight, so the button reads as clickable
    if hovered:
        pygame.draw.circle(screen, (45, 45, 45), (cx, cy), SOUND_BUTTON_RADIUS)

    pygame.draw.circle(screen, color, (cx, cy), SOUND_BUTTON_RADIUS, 2)

    # speaker body: a small square with a triangular cone opening right
    pygame.draw.rect(screen, color, (cx - 9, cy - 4, 5, 8))
    pygame.draw.polygon(screen, color,
                        [(cx - 4, cy - 4), (cx + 2, cy - 9),
                         (cx + 2, cy + 9), (cx - 4, cy + 4)])

    if on:
        # two arcs suggesting sound coming out
        for radius in (5, 9):
            pygame.draw.circle(screen, color, (cx + 3, cy), radius, 2,
                               draw_top_right=True, draw_bottom_right=True)
    else:
        # a slash across the speaker when muted
        pygame.draw.line(screen, color, (cx - 10, cy + 10), (cx + 10, cy - 10), 2)


def draw_cheat_indicator():
    """Show active cheats as small badges in the HUD strip.

    The maze occupies y < 900 (32 rows of (HEIGHT - 50) // 32 pixels); the
    band below it is the HUD, so anything drawn there cannot cover the board.
    The old version wrote the full cheat names at the top-right corner, which
    sat directly on top of the play area and hid pacgums and walls behind it.

    Each cheat becomes a one-letter disc in its own colour, placed in the gap
    between the timer readout and the row of life icons. The letters are
    listed on the instructions screen; there is no hover tooltip, because a
    label long enough to be useful would reach back over the timer readout.
    """
    if not CHEATS_ENABLED:
        return

    active_cheats = [
        (letter, label, color)
        for letter, label, color, on in (
            ('I', 'INVINCIBLE', 'cyan', state.cheat_invincible),
            ('F', 'GHOSTS FROZEN', 'orange', state.cheat_ghosts_frozen),
            ('S', 'SPEED BOOST', 'lime', state.cheat_speed_boost),
        )
        if on
    ]
    if not active_cheats:
        return

    for index, (letter, _label, color) in enumerate(active_cheats):
        center = (CHEAT_BADGE_X + index * CHEAT_BADGE_SPACING, CHEAT_BADGE_Y)
        pygame.draw.circle(screen, color, center, CHEAT_BADGE_RADIUS)
        pygame.draw.circle(screen, 'black', center, CHEAT_BADGE_RADIUS, 2)
        glyph = font.render(letter, True, 'black')
        screen.blit(glyph, glyph.get_rect(center=center))


def draw_menu():
    title = title_font.render(THEME.player_name, True, THEME.title)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))
    for i, label in enumerate(state.menu_options):
        label_color = THEME.title if i == state.menu_index else THEME.hud_text
        prefix = '> ' if i == state.menu_index else '  '
        text = font.render(prefix + label, True, label_color)
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 420 + i * 50)))
    hint = font.render('UP/DOWN to choose, ENTER to select', True, 'gray')
    screen.blit(
        hint,
        hint.get_rect(center=(WIDTH // 2, 420 + len(state.menu_options) * 50 + 40)),
    )


def draw_instructions():
    title = title_font.render('HOW TO PLAY', True, 'yellow')
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
    lines = [
        '',
        'Move: Arrow Keys or WASD',
        'Eat every pacgum and super-pacgum to clear a level.',
        'A super-pacgum makes the ghosts edible for a short time --',
        'eat them for bonus points before it wears off.',
        'Touching a non-edible ghost costs you a life.',
        '',
        'Pause: ESC or P',
        'Sound: click the speaker in the bottom-right corner',
        '',
        'Press ESC or ENTER to return to the menu',
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, 'white')
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 180 + i * 40)))

    if CHEATS_ENABLED:
        cheat_title = font.render(
            'some secret power moves ...  (badges: I / F / S)', True, 'navy')
        screen.blit(cheat_title, cheat_title.get_rect(center=(WIDTH // 2, 180 + len(lines) * 40 + 20)))
        cheat_lines = [
            'F1: +1 life',
            'F2: clear all pacgums',
            'F3: toggle invincibility',
            'F4: toggle ghost freeze',
            'F5: toggle speed boost',
        ]
        for i, line in enumerate(cheat_lines):
            text = font.render(line, True, 'navy')
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


# --- board ------------------------------------------------------------------
# The maze itself is drawn by walls.py in the classic arcade style (hollow
# blue tubes rather than filled bars). It only depends on the wall tiles,
# which never change during a level, so the whole layer is rendered once and
# cached; only the pacgums are redrawn each frame. The cache is keyed on the
# level grid object itself, so prepare_level()'s fresh copy rebuilds it.
_wall_layer = None
_wall_layer_level = None


def _wall_layer_for(level, tile_w, tile_h):
    global _wall_layer, _wall_layer_level
    if _wall_layer is None or _wall_layer_level is not level:
        _wall_layer = render_wall_layer(level, WIDTH, HEIGHT, tile_w, tile_h)
        _wall_layer_level = level
    return _wall_layer


def draw_board():
    num1 = (HEIGHT - 50) // 32
    num2 = WIDTH // 30
    screen.blit(_wall_layer_for(state.level, num2, num1), (0, 0))
    for i in range(len(state.level)):
        for j in range(len(state.level[i])):
            if state.level[i][j] == 1:
                pygame.draw.circle(
                    screen, THEME.dot,
                    (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4,
                )
            if state.level[i][j] == 2 and not state.flicker:
                pygame.draw.circle(
                    screen, THEME.power_pellet,
                    (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10,
                )


def draw_player():
    base_image = pygame.transform.scale(player_images[state.counter // 5], (36, 36))
    if state.direction == 0:
        screen.blit(base_image, (state.player_x, state.player_y))
    elif state.direction == 1:
        screen.blit(
            pygame.transform.flip(base_image, True, False),
            (state.player_x, state.player_y),
        )
    elif state.direction == 2:
        screen.blit(
            pygame.transform.rotate(base_image, 90),
            (state.player_x, state.player_y),
        )
    elif state.direction == 3:
        screen.blit(
            pygame.transform.rotate(base_image, 270),
            (state.player_x, state.player_y),
        )
