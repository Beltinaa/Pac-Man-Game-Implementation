"""Classic arcade-style maze walls.

Instead of drawing every wall tile as its own filled bar, the maze is drawn
the way the original arcade board looks: each run of wall tiles is a hollow
"tube" -- a thin blue outline around a black interior -- with rounded
corners, and every connected piece merges into one continuous shape.

How it works: two passes over the tile grid.

  1. Each wall tile stamps its silhouette in wall blue -- a disc at the tile
     centre plus one rectangle per neighbour it connects to.
  2. The exact same shapes are stamped again in black, shrunk by the line
     thickness.

The second pass hollows out the first, so what survives is a constant-width
outline that follows the outer boundary of the union of all those shapes.
Corners, T-junctions and crossings therefore come out right on their own,
without a hand-written case for each shape -- and because every piece is
built from a disc plus rectangles, both the outside and the inside of a bend
are rounded, exactly like the arcade maze.

This is the same construction the reference implementation uses, with the
same primitives and the same proportions -- it builds one sprite per maze
intersection and blits it, this builds the whole maze in one pass, but a disc
plus rectangles stamped twice is the shape in both cases.

The layer is rendered once per level onto a cached surface (walls never
change while a level is being played); `ui.draw_board` just blits the result
and then draws the pacgums on top.

Tile codes are the ones documented at the top of board.py.
"""

import pygame

import theme as theme_module

# Colours are read from theme.active() at render time rather than captured at
# import, because the character picker in the main menu can change the theme
# while the game is running. Taken from theme rather than assets so this
# module stays independent of the display surface and renders headless.

# --- tile codes ------------------------------------------------------------
WALL_V, WALL_H = 3, 4
CORNER_TR, CORNER_TL, CORNER_BL, CORNER_BR = 5, 6, 7, 8
GATE, SOLID = 9, 10

# --- look --------------------------------------------------------------------
# These are the reference implementation's own numbers, in its own terms: it
# works in maze *cells*, and one cell is two tiles of this board's grid (the
# adapter expands every maze cell into a 2x2 block of tiles).
#
#   wall thickness  = 30% of a cell        (its update_level_layout)
#   blue border     = 15% of that thickness, min 1px  (its draw_wall_sprite)
#   wall blue       = its Colors.WALL_BLUE
#
# Everything is drawn hard-edged, at final resolution, exactly like the
# reference: plain pygame rects and circles, no antialiasing, no scaling and
# no shading of any kind, so the walls stay flat.
# Colours come from the active theme (see theme.py) so the maze re-skins
# along with the sprites; the geometry below is unchanged by the theme.
CELL_TILES = 2                    # tiles per maze cell, set by maze_adapter
THICKNESS_FRAC = 0.30             # wall thickness, as a fraction of a cell
BORDER_FRAC = 0.15                # blue border, as a fraction of the thickness
GATE_HEIGHT_FRAC = 0.16           # thickness of the ghost-house door bar

# --- connectivity ----------------------------------------------------------
_N, _S, _W, _E = (-1, 0), (1, 0), (0, -1), (0, 1)
_DIRECTIONS = (_N, _S, _W, _E)
_OPPOSITE = {_N: _S, _S: _N, _W: _E, _E: _W}

# Which way each wall tile code runs. The keys of this table are exactly the
# tile values that count as wall, which is what is_wall_tile() checks.
_DECLARED = {
    WALL_V: (_N, _S),
    WALL_H: (_W, _E),
    CORNER_TR: (_W, _S),
    CORNER_TL: (_E, _S),
    CORNER_BL: (_N, _E),
    CORNER_BR: (_N, _W),
    SOLID: _DIRECTIONS,
}


def _tile_at(grid, row, col):
    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        return grid[row][col]
    return None


def _is_logo_cell(grid, row, col):
    """True on the one tile that is the *inside* of a "42" cell.

    maze_adapter expands each maze cell into a 2x2 tile block whose top-left
    tile is the cell itself and whose other three are that cell's east wall,
    south wall and corner post. It marks all four SOLID for a "42" cell, but
    only the last three are really wall -- the top-left one is the cell
    interior, which is what gets filled with the logo colour.
    """
    return (grid[row][col] == SOLID
            and row % CELL_TILES == 0 and col % CELL_TILES == 0)


def _is_wall(grid, row, col):
    """True where a wall tube should be drawn."""
    tile = _tile_at(grid, row, col)
    if tile is None or tile not in _DECLARED:
        return False
    return not _is_logo_cell(grid, row, col)


def _arms(grid, row, col):
    """The directions this tile's tube extends toward.

    A pair of neighbouring wall tiles is joined when *either* of the two
    declares the join. Both sides agreeing would not be enough: the maze
    adapter's autotiler has no T-junction or crossing code, so where three
    or four walls meet it labels the middle tile a plain straight piece, and
    only the arm tile knows the join is there. Conversely, when neither side
    declares it -- two lines merely running side by side, like the double
    outer border of the static fallback board -- they stay separate tubes.
    """
    declared = _DECLARED.get(grid[row][col], ())
    arms = []
    for direction in _DIRECTIONS:
        n_row, n_col = row + direction[0], col + direction[1]
        neighbour = _tile_at(grid, n_row, n_col)
        if neighbour is None:
            # Off the board: run to the edge if the tile points that way, so
            # border walls end flush instead of with a rounded stump.
            if direction in declared:
                arms.append(direction)
            continue
        if not _is_wall(grid, n_row, n_col):
            continue
        if direction in declared or _OPPOSITE[direction] in _DECLARED[neighbour]:
            arms.append(direction)
    return arms


def _stamp_tube(surface, color, x0, y0, x1, y1, half, arms):
    """One tile of tube: a disc at the centre, plus an arm to each edge it
    connects to. `half` is the half-width, so shrinking it is what hollows
    the tube out on the second pass."""
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    pygame.draw.circle(surface, color, (cx, cy), half)
    for direction in arms:
        if direction == _N:
            rect = (cx - half, y0, 2 * half, cy - y0)
        elif direction == _S:
            rect = (cx - half, cy, 2 * half, y1 - cy)
        elif direction == _W:
            rect = (x0, cy - half, cx - x0, 2 * half)
        else:
            rect = (cx, cy - half, x1 - cx, 2 * half)
        pygame.draw.rect(surface, color, rect)


def _stamp_pass(surface, grid, tile_w, tile_h, half, color):
    """Stamp every wall tile once, at the given half-width."""
    for row, line in enumerate(grid):
        y0, y1 = row * tile_h, (row + 1) * tile_h
        for col, tile in enumerate(line):
            if not _is_wall(grid, row, col):
                continue
            x0, x1 = col * tile_w, (col + 1) * tile_w
            _stamp_tube(surface, color, x0, y0, x1, y1, half,
                        _arms(grid, row, col))


def _draw_logo(surface, grid, tile_w, tile_h, half, logo_color):
    """Fill each "42" cell with the logo colour, the way the reference's
    draw_maze does for its cell==15 tiles.

    The reference fills from one wall centre-line to half a thickness short
    of the next, and lets the wall tubes cover the overlap. This insets by
    half a thickness on all four sides instead, which paints exactly the same
    pixels wherever a wall is present -- and, unlike the reference version,
    does not bleed into the corridor on a side where the surrounding wall
    happens to have been carved away.
    """
    for row in range(0, len(grid), CELL_TILES):
        for col in range(0, len(grid[row]), CELL_TILES):
            if not _is_logo_cell(grid, row, col):
                continue
            x = col * tile_w - tile_w // 2 + half
            y = row * tile_h - tile_h // 2 + half
            pygame.draw.rect(
                surface, logo_color,
                (x, y,
                 CELL_TILES * tile_w - 2 * half, CELL_TILES * tile_h - 2 * half),
            )


def _draw_gates(surface, grid, tile_w, tile_h, bar_h, gate_color):
    """The ghost-house door: a flat coloured bar, not part of the tubes."""
    for row, line in enumerate(grid):
        for col, tile in enumerate(line):
            if tile != GATE:
                continue
            y_mid = row * tile_h + tile_h // 2
            pygame.draw.rect(
                surface, gate_color,
                (col * tile_w, y_mid - bar_h // 2, tile_w, bar_h),
            )


def render_wall_layer(grid, width, height, tile_w, tile_h):
    """Render the whole maze (walls + ghost gate) to a transparent surface of
    `width` x `height`, ready to be blitted under the pacgums and sprites."""
    theme = theme_module.active()
    wall_color = theme.wall
    interior_color = theme.wall_interior + (255,)   # opaque: hollows the tube
    gate_color = theme.gate
    logo_color = theme.logo

    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    cell = min(tile_w, tile_h) * CELL_TILES
    thickness = max(1, int(cell * THICKNESS_FRAC))
    border = max(1, int(thickness * BORDER_FRAC))
    inner = thickness - 2 * border

    # the "42" goes down first, then the walls are drawn over it
    _draw_logo(surface, grid, tile_w, tile_h, thickness // 2, logo_color)
    # pass 1: the solid silhouette -- pass 2: the same shapes, hollowed out
    _stamp_pass(surface, grid, tile_w, tile_h, thickness // 2, wall_color)
    if 0 < inner < thickness:
        _stamp_pass(surface, grid, tile_w, tile_h, inner // 2, interior_color)
    _draw_gates(surface, grid, tile_w, tile_h,
                max(2, int(cell * GATE_HEIGHT_FRAC)), gate_color)
    return surface
