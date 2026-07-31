import math

import pygame

from config import COLOR, HEIGHT, WIDTH

pygame.init()

screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 20)
title_font = pygame.font.Font('freesansbold.ttf', 48)

player_images = []
for i in range(1, 5):
    player_images.append(
        pygame.transform.scale(
            pygame.image.load(f'assets/player_images/{i}.png'), (45, 45)
        )
    )

blinky_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/red.png'), (45, 45)
)
pinky_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/pink.png'), (45, 45)
)
inky_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/blue.png'), (45, 45)
)
clyde_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/orange.png'), (45, 45)
)
spooked_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/powerup.png'), (45, 45)
)
dead_img = pygame.transform.scale(
    pygame.image.load('assets/ghost_images/dead.png'), (45, 45)
)

# Re-export for modules that used the old module-level names
color = COLOR
PI = math.pi
