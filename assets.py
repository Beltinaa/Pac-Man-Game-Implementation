import math

import pygame

from config import COLOR, HEIGHT, THEME_NAME, WIDTH
import theme as theme_module

THEME = theme_module.get(THEME_NAME)

pygame.init()

screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 20)
title_font = pygame.font.Font('freesansbold.ttf', 48)

def _load_sprite(subdir_attr, filename, size=(45, 45)):
    """Load one themed sprite, scaled. theme.sprite_path falls back to the
    classic art when the active theme has not supplied that file."""
    path = theme_module.sprite_path(THEME, subdir_attr, filename)
    return pygame.transform.scale(pygame.image.load(path), size)


player_images = [_load_sprite('player_dir', f'{i}.png') for i in range(1, 5)]

blinky_img = _load_sprite('ghost_dir', 'red.png')
pinky_img = _load_sprite('ghost_dir', 'pink.png')
inky_img = _load_sprite('ghost_dir', 'blue.png')
clyde_img = _load_sprite('ghost_dir', 'orange.png')
spooked_img = _load_sprite('ghost_dir', 'powerup.png')
dead_img = _load_sprite('ghost_dir', 'dead.png')

# Re-export for modules that used the old module-level names
color = COLOR
PI = math.pi
