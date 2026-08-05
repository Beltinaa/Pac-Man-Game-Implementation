"""Colour palettes and sprite lookup, so the game can be re-skinned.

Everything that used to be a hard-coded colour or asset path now comes from
the active Theme. Switch skins with THEME_NAME in config.py -- nothing else
needs editing.

Sprites resolve per theme with a fallback: a theme names a subfolder under
assets/, and any file missing from it falls back to the classic art, so a
half-finished skin still runs instead of crashing at import.

To add your own art, drop PNGs into the folders named by `player_dir` and
`ghost_dir` using the same filenames the classic theme uses:

    assets/<player_dir>/1.png .. 4.png     player, 4 animation frames
    assets/<ghost_dir>/red.png             enemy 1
    assets/<ghost_dir>/pink.png            enemy 2
    assets/<ghost_dir>/blue.png            enemy 3
    assets/<ghost_dir>/orange.png          enemy 4
    assets/<ghost_dir>/powerup.png         enemy while you are powered up
    assets/<ghost_dir>/dead.png            enemy eyes, heading home

Use art you have the rights to. Characters from Marvel, Disney and the like
are trademarked, so this file ships an original web-slinger palette rather
than any studio's designs -- point `player_dir` / `ghost_dir` at your own
files and set `enemy_names` to whatever you want them called.
"""

import os
import re
from collections import namedtuple

# `name` is the lookup key matched against config.THEME_NAME -- it is not
# shown anywhere. The names on screen come from `player_name` (menu title)
# and `enemy_names`, so rename those freely; renaming `name` changes what
# THEME_NAME has to be set to.
Theme = namedtuple("Theme", """
    name
    wall wall_interior logo gate
    dot power_pellet
    dot_image power_image dot_image_px power_image_px
    ghost_scale
    hud_text title accent
    player_dir ghost_dir
    player_name enemy_names
""".split())


CLASSIC = Theme(
    name="classic",
    wall=(33, 33, 222),          # arcade maze blue
    wall_interior=(0, 0, 0),
    logo=(247, 18, 232),         # the "42" watermark
    gate=(255, 183, 255),
    dot=(255, 255, 255),
    power_pellet=(255, 255, 255),
    # Pacgum artwork. None = draw the plain circles the arcade game uses.
    # Paths are relative to assets/; the _px values are the drawn size, and
    # both are a little larger than the circles they replace so a detailed
    # sprite is still readable at speed.
    dot_image=None,
    power_image=None,
    dot_image_px=20,
    power_image_px=28,
    # Multiplies the enemy sprite size. 1.0 matches the player exactly.
    ghost_scale=1.0,
    hud_text=(255, 255, 255),
    title=(255, 255, 0),
    accent=(0, 0, 255),
    player_dir="player_images",
    ghost_dir="ghost_images",
    player_name="PAC-MAN",
    enemy_names=("BLINKY", "PINKY", "INKY", "CLYDE"),
)

# An original comic-book skin: red webbing, blue shadows, white web-line
# pacgums. No studio's characters or logos -- see the module docstring.
WEB_SLINGER = CLASSIC._replace(
    name="web-slinger",
    wall=(200, 30, 45),          # web red
    wall_interior=(6, 4, 20),    # near-black with a blue cast
    logo=(30, 70, 200),          # the "42" in suit blue
    gate=(255, 210, 120),
    dot=(235, 240, 255),         # web-line white
    power_pellet=(255, 90, 60),
    hud_text=(235, 240, 255),
    title=(200, 30, 45),
    accent=(30, 70, 200),
    dot_image="webslinger/spider.png",
    power_image="webslinger/net.png",
    ghost_scale=1.15,
    player_dir="webslinger/player",
    ghost_dir="webslinger/enemies",
    player_name="WEB-SLINGER",
    enemy_names=("SCARLET", "VIOLET", "AZURE", "AMBER"),
)

def _slug(name):
    """Normalise a theme name for lookup: case, spaces, hyphens and
    underscores all stop mattering, so 'web-slinger', 'web_slinger' and
    'Web Slinger' all find the same theme."""
    return re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")


THEMES = {_slug(t.name): t for t in (CLASSIC, WEB_SLINGER)}


def get(name):
    """The named theme, falling back to classic if it is unknown.

    An unknown name is reported rather than swallowed: silently serving the
    classic theme for a typo'd THEME_NAME looks exactly like the theme system
    being broken, which is a miserable thing to debug.
    """
    theme = THEMES.get(_slug(name))
    if theme is None:
        print("[theme] unknown THEME_NAME %r -- using '%s'. Available: %s"
              % (name, CLASSIC.name, ", ".join(sorted(THEMES))))
        return CLASSIC
    return theme


def image_path(relative):
    """Path to a themed image under assets/, or None if it is not there."""
    if not relative:
        return None
    path = os.path.join("assets", relative)
    return path if os.path.exists(path) else None


def sprite_path(theme, subdir_attr, filename):
    """Path to one sprite, falling back to the classic art when the theme
    does not supply that file. Keeps a partially-drawn skin runnable."""
    themed = os.path.join("assets", getattr(theme, subdir_attr), filename)
    if os.path.exists(themed):
        return themed
    return os.path.join("assets", getattr(CLASSIC, subdir_attr), filename)
