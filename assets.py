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
small_font = pygame.font.Font('freesansbold.ttf', 16)

def _fit(surface, size):
    """Trim transparent padding, then scale to fill `size` keeping the aspect
    ratio, centred on a transparent square.

    Artwork does not arrive framed consistently: the themed enemy art fills
    about 73% x 50% of its canvas while the player art fills 90% x 97%.
    Scaling both to the same box therefore drew the enemies far smaller than
    the player even though the boxes matched. Cropping to the actual content
    first makes every sprite fill its box, so on-screen size is decided by
    the game rather than by whitespace in the source file.
    """
    surface = surface.convert_alpha()
    content = surface.get_bounding_rect(min_alpha=1)
    if content.width and content.height:
        surface = surface.subsurface(content).copy()

    width, height = surface.get_size()
    scale = min(size[0] / width, size[1] / height)
    scaled = pygame.transform.smoothscale(
        surface, (max(1, round(width * scale)), max(1, round(height * scale))))

    canvas = pygame.Surface(size, pygame.SRCALPHA)
    canvas.blit(scaled, scaled.get_rect(center=(size[0] // 2, size[1] // 2)))
    return canvas


def _load_sprite(subdir_attr, filename, size=(45, 45)):
    """Load one themed sprite, trimmed and scaled. theme.sprite_path falls
    back to the classic art when the active theme has not supplied it."""
    path = theme_module.sprite_path(THEME, subdir_attr, filename)
    return _fit(pygame.image.load(path), size)


def _load_pacgum(relative, pixels):
    """A pacgum image for the active theme, or None to draw plain circles."""
    path = theme_module.image_path(relative)
    if path is None:
        return None
    return _fit(pygame.image.load(path), (pixels, pixels))


player_images = [_load_sprite('player_dir', f'{i}.png') for i in range(1, 5)]

blinky_img = _load_sprite('ghost_dir', 'red.png')
pinky_img = _load_sprite('ghost_dir', 'pink.png')
inky_img = _load_sprite('ghost_dir', 'blue.png')
clyde_img = _load_sprite('ghost_dir', 'orange.png')
spooked_img = _load_sprite('ghost_dir', 'powerup.png')
dead_img = _load_sprite('ghost_dir', 'dead.png')

# Pacgum artwork -- None on themes that use the arcade's plain circles.
dot_img = _load_pacgum(THEME.dot_image, THEME.dot_image_px)
power_img = _load_pacgum(THEME.power_image, THEME.power_image_px)

# Enemy sprites are drawn at this size; the collision box stays 36px either
# way, so a theme scaling its art up changes looks only, never hitboxes.
GHOST_PX = max(1, round(36 * THEME.ghost_scale))

# Re-export for modules that used the old module-level names
color = COLOR
PI = math.pi
