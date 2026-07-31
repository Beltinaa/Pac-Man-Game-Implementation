"""
Loader/adapter for the assigned "A-Maze-ing" package (mazegenerator).

Project rule (5.4): "You must not write your own generator [...] You must use
their package as-is, without modifying it [...] Your loader must adapt to
their interface, not the opposite."

This module is that loader. It:
  * imports the mazegenerator package exactly as published (the .whl in
    this repo is installed unmodified, see requirements.txt),
  * calls it with perfect=False, as required, so the resulting maze is
    braided (no dead ends) and therefore Pac-Man-compatible,
  * translates the package's own cell/wall-bit representation into the
    tile-code 2D grid that board.py / pacman.py already know how to draw,
    move on and collide with (0=empty, 1=dot, 2=power dot, 3/4=straight
    wall, 5-8=wall corners, 9=ghost gate -- see board.py header),
  * catches every failure the generator can produce and turns it into a
    single MazeGenerationError, so callers can fail cleanly instead of
    crashing pygame mid-startup.

Nothing in pacman.py's movement/collision/rendering code changes: it is all
built around a 30-column x 33-row tile grid at a 900x950 window, and this
adapter simply produces a grid of exactly that shape, so nothing that
currently works is broken.

Ghost house: the generator's own centered "42" watermark (maze cell value
15 -- see its _add_42_to_maze) is solid by design and always sits dead
center. Rather than carving a separate ghost-house rectangle that could
overlap it, generate_board() finds the one background column running down
the middle of the "42" glyph (the natural gap between the "4" and the "2"),
opens it up as a small pocket, and gates its top -- so the ghost house is
literally the inside of the "42", never a shape stamped on top of it.
generate_board() returns that pocket's tile coordinates (as a GhostPocket)
alongside the board so callers can compute pixel bounds/targets from it
instead of hardcoding them.
"""

from __future__ import annotations

from collections import namedtuple

try:
    from mazegenerator import MazeGenerator  # supplied package, unmodified
except Exception as exc:  # pragma: no cover - import-time failure
    MazeGenerator = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class MazeGenerationError(Exception):
    """Raised whenever the assigned maze generator cannot be used, for any
    reason (missing package, bad output, internal exception, ...)."""


# ---------------------------------------------------------------------------
# Tile codes, identical to the ones documented at the top of board.py.
# ---------------------------------------------------------------------------
EMPTY, DOT, POWER = 0, 1, 2
WALL_V, WALL_H = 3, 4
CORNER_TR, CORNER_TL, CORNER_BL, CORNER_BR = 5, 6, 7, 8
GATE = 9
# Solid-block wall: only ever used for the generator's own "42" watermark
# cells, rendered by pacman.py as a filled rectangle instead of a thin
# line/arc so the logo reads as a bold shape (see draw_board). Collision
# code only ever checks `tile >= 3`, so this is exactly as solid as any
# other wall value -- purely a rendering distinction.
SOLID = 10

# mazegenerator wall-bit codes (see its README's "Wall Encoding" section).
MAZE_N, MAZE_E, MAZE_S, MAZE_W = 1, 2, 4, 8

# Each maze cell becomes a 2x2 block of tiles, so a (width x height) maze
# becomes a (2*width x 2*height) tile grid. 15x16 -> 30x32, which (plus one
# padding wall row appended below, matching the original hand-made board's
# incidental 33rd row) gives the exact 30x33 shape pacman.py's pixel math
# (WIDTH=900, HEIGHT=950) already assumes.
MAZE_WIDTH, MAZE_HEIGHT = 15, 16
BOARD_COLS, BOARD_ROWS = MAZE_WIDTH * 2, MAZE_HEIGHT * 2

_TUNNEL_ROW = 15

# The generator always stamps this exact 7x5 glyph, centered, via its own
# _add_42_to_maze -- reproduced here strictly as read-only geometry (we
# never write this back into the generator or otherwise touch its
# behaviour) so this loader can locate the "42" without guessing. If a
# future generator version ever draws a different glyph, _validate_
# ghost_pocket() below notices the mismatch and fails loudly instead of
# carving a pocket in the wrong place.
_FT_SMALL = [
    [1, 0, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]
_GLYPH_ROWS, _GLYPH_COLS = len(_FT_SMALL), len(_FT_SMALL[0])
_GLYPH_POS_Y = (MAZE_HEIGHT - _GLYPH_ROWS) // 2
_GLYPH_POS_X = (MAZE_WIDTH - _GLYPH_COLS) // 2

# Tile-coordinate bounding box of the ghost house pocket, plus the single
# gate tile that connects it to the corridor above.
GhostPocket = namedtuple(
    "GhostPocket", "row_start row_end col_start col_end gate_row gate_col")


def _autotile(is_wall, r, c, rows, cols):
    """Pick a wall sprite purely for rendering. Collision logic elsewhere
    only ever checks `tile >= 3`, so any wall-family value is functionally
    equivalent; this just keeps corners looking reasonable."""

    def wall_at(rr, cc):
        if 0 <= rr < rows and 0 <= cc < cols:
            return is_wall[rr][cc]
        return True  # outside the board counts as solid

    up, down = wall_at(r - 1, c), wall_at(r + 1, c)
    left, right = wall_at(r, c - 1), wall_at(r, c + 1)

    if up and down and not (left and right):
        return WALL_V
    if left and right and not (up and down):
        return WALL_H
    if not up and not left:
        return CORNER_TL
    if not up and not right:
        return CORNER_TR
    if not down and not left:
        return CORNER_BL
    if not down and not right:
        return CORNER_BR
    return WALL_V


def _find_glyph_gap_column():
    """The one glyph column that is background (0) in every row -- the
    natural gap between the "4" and the "2" -- is where the ghost pocket
    goes. Returns None if the glyph has no such column."""
    for x in range(_GLYPH_COLS):
        if all(row[x] == 0 for row in _FT_SMALL):
            return x
    return None


def _compute_ghost_pocket():
    """Tile-coordinate bounds of the pocket behind the "42", derived only
    from the glyph's fixed, known geometry -- never from the random seed,
    so it is identical on every generated maze."""
    gap_col = _find_glyph_gap_column()
    if gap_col is None:
        raise MazeGenerationError(
            "42 glyph has no background column to carve a ghost pocket in")

    cell_col = _GLYPH_POS_X + gap_col
    cell_row_start = _GLYPH_POS_Y
    cell_row_end = _GLYPH_POS_Y + _GLYPH_ROWS - 1

    row_start, row_end = cell_row_start * 2, cell_row_end * 2 + 1
    col_start, col_end = cell_col * 2, cell_col * 2 + 1
    gate_row, gate_col = row_start - 1, col_start

    if not (0 <= gate_row and row_end < BOARD_ROWS
            and 0 <= col_start and col_end < BOARD_COLS):
        raise MazeGenerationError(
            "42 ghost pocket falls outside the generated board")

    return GhostPocket(row_start, row_end, col_start, col_end,
                        gate_row, gate_col)


def _validate_ghost_pocket(board, pocket):
    """The tiles immediately left/right of the pocket, at its vertical
    midpoint, must belong to a solid "42" stroke -- confirming the pocket
    really sits inside the generator's own glyph and our geometry still
    matches _add_42_to_maze. If it does not, fail the same way every other
    generator problem fails instead of carving a pocket into empty space
    or somewhere unreachable."""
    mid_row = (pocket.row_start + pocket.row_end) // 2
    left, right = pocket.col_start - 1, pocket.col_end + 1
    if not (0 <= left and right < BOARD_COLS):
        raise MazeGenerationError("42 ghost pocket has no room to flank")
    if board[mid_row][left] < WALL_V or board[mid_row][right] < WALL_V:
        raise MazeGenerationError(
            "42 ghost pocket is not actually inside the generated '42'")


def _carve_ghost_pocket(board, pocket):
    """Open the pocket interior and gate its top tile. This is the only
    place the ghost house is carved -- entirely inside the "42"'s own
    footprint, never overlapping or overwriting its solid cells.

    The interior cells are guaranteed open by construction (they're the
    glyph's own background column), but the pocket's *boundary* is not:
    the generator's random maze decides, seed by seed, whether the wall
    segments around it are open or closed, since nothing in
    _add_42_to_maze forces them shut (only cells directly touching an
    actual digit stroke get a forced wall). Must run after _carve_tunnel:
    the tunnel row runs straight through the pocket's row range and
    force-opens every column across it (needed for the wraparound at the
    far left/right edges, nowhere near this pocket), which would
    otherwise wipe any flank wall added here right back open again.

    Deliberate design choice: only the gate row is force-walled below
    (so there's exactly one gate tile, not two gaps side by side at the
    top). The left/right/bottom flanks are intentionally left as the
    generator produced them, so the area around the "4" and "2" reads as
    more open -- on many seeds this does mean the pocket can be entered/
    exited from the sides or bottom as well as through the gate, not
    just the gate alone. If that ever needs to change back to a fully
    sealed box (single-entrance guarantee on every seed), wall the left/
    right flanks (pocket.col_start - 1 / pocket.col_end + 1, every row
    from row_start to row_end) and the row at pocket.row_end + 1 (every
    column from col_start to col_end) the same way the gate row below
    does.
    """
    for r in range(pocket.row_start, pocket.row_end + 1):
        for c in range(pocket.col_start, pocket.col_end + 1):
            board[r][c] = EMPTY

    for c in range(pocket.col_start, pocket.col_end + 1):
        if c == pocket.gate_col:
            continue
        if board[pocket.gate_row][c] < WALL_V:
            board[pocket.gate_row][c] = WALL_V

    board[pocket.gate_row][pocket.gate_col] = GATE


def _seal_outer_border(board):
    """Force the board's absolute outer edge (row 0 and column 0) solid.

    The maze<->tile expansion in generate_board() only ever writes a raw
    maze cell's own East/South wall bits into tiles; a cell's North/West
    wall is only ever represented by its north/west NEIGHBOR's own South/
    East connector tile. Cells on the top row or left column have no such
    neighbor, so that outward-facing wall is never actually written and
    silently defaults to open -- on most seeds this leaves stray gaps
    clean through the top and/or left edge of the maze. (The bottom row
    and right column don't have this problem: each of those cells' own
    South/East bit already encodes its outward wall directly.) Must run
    before _carve_tunnel, which still deliberately reopens one row on
    both the left and right edges for the wraparound tunnel."""
    last_row = BOARD_ROWS - 1
    for c in range(BOARD_COLS):
        if board[0][c] < WALL_V:
            board[0][c] = WALL_H
        if board[last_row][c] < WALL_V:
            board[last_row][c] = WALL_H
    for r in range(BOARD_ROWS):
        if board[r][0] < WALL_V:
            board[r][0] = WALL_V
        if board[r][BOARD_COLS - 1] < WALL_V:
            board[r][BOARD_COLS - 1] = WALL_V


def _carve_tunnel(board):
    """Guarantee a left/right wrap-around row, since pacman.py's player
    wraparound (`player_x > 900` / `< -50`) needs at least one open edge.

    SOLID tiles are skipped: the tunnel row runs straight through the middle
    of the generator's centered "42", and opening it there would cut a
    walkable lane clean through the logo. The wraparound only needs the two
    ends of the row open, not an uninterrupted corridor between them, so the
    logo stays solid and the row simply stops at it. Tiles that merely touch
    a SOLID one are skipped too: those are the logo's own surrounding walls,
    and opening them would let the player walk along the row right between
    the digits."""
    def touches_logo(c):
        if board[_TUNNEL_ROW][c] == SOLID:
            return True
        for r2, c2 in ((_TUNNEL_ROW - 1, c), (_TUNNEL_ROW + 1, c),
                       (_TUNNEL_ROW, c - 1), (_TUNNEL_ROW, c + 1)):
            if (0 <= r2 < BOARD_ROWS and 0 <= c2 < BOARD_COLS
                    and board[r2][c2] == SOLID):
                return True
        return False

    for c in range(BOARD_COLS):
        if board[_TUNNEL_ROW][c] >= WALL_V and not touches_logo(c):
            board[_TUNNEL_ROW][c] = EMPTY


PERIMETER_RING_THICKNESS = 1  # tiles wide; classic Pac-Man's own outer ring is 1


def _carve_perimeter_ring(board, thickness=PERIMETER_RING_THICKNESS):
    """Force open a continuous loop, `thickness` tiles wide, just inside
    the sealed outer border, connecting all 4 corners in an unbroken
    ring -- like classic hand-designed Pac-Man's outer ring corridor,
    just wider and more visually obvious as a distinct path (built from
    `thickness` concentric single-tile loops, each one tile further in
    than the last, which together cover every tile of the band). The
    generator's random maze doesn't guarantee this on its own (the wall
    pattern near the edge is just whatever it happened to carve), so
    without this a path running along the edge can dead-end partway."""
    def open_cell(r, c):
        if (0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS
                and board[r][c] >= WALL_V and board[r][c] != SOLID):
            board[r][c] = DOT

    for t in range(thickness):
        top, bottom = 1 + t, BOARD_ROWS - 2 - t
        left, right = 1 + t, BOARD_COLS - 2 - t
        for c in range(left, right + 1):
            open_cell(top, c)
            open_cell(bottom, c)
        for r in range(top, bottom + 1):
            open_cell(r, left)
            open_cell(r, right)


def _thin_pacgums(board):
    """Space the pacgums one maze cell apart, like the original game.

    Every open tile starts out holding one, but a maze cell is two tiles
    wide here, so that puts a pacgum on each cell *and* on each opening
    between two cells -- twice the density the original board has. Keeping
    only the tiles where (row + col) is even drops every other one along any
    corridor, which leaves exactly the cell centres (both coordinates even)
    plus the same 2-tile spacing on the odd lanes such as the perimeter
    ring. Only existing pacgums are removed, never added, so the ghost
    house and the tunnel row stay empty."""
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if board[r][c] == DOT and (r + c) % 2:
                board[r][c] = EMPTY


def _place_power_pellets(board):
    """Drop a power pellet near each of the 4 corners, mirroring the
    original hand-made board's layout, on whichever nearby tile is open."""
    corners = [(2, 2, 1, 1), (2, BOARD_COLS - 3, 1, -1),
               (BOARD_ROWS - 3, 2, -1, 1), (BOARD_ROWS - 3, BOARD_COLS - 3, -1, -1)]
    for r0, c0, dr, dc in corners:
        r, c = r0, c0
        for _ in range(6):
            if 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and board[r][c] == DOT:
                board[r][c] = POWER
                break
            r, c = r + dr, c + dc


def generate_board(seed: int = 0):
    """Build a full Pac-Man tile grid using the assigned MazeGenerator
    package. Returns (board, ghost_pocket). Raises MazeGenerationError on
    any failure.
    """
    if MazeGenerator is None:
        raise MazeGenerationError(f"mazegenerator package is not available: {_IMPORT_ERROR}")

    try:
        gen = MazeGenerator(size=(MAZE_WIDTH, MAZE_HEIGHT), perfect=False, seed=seed)
        cells = gen.maze
    except Exception as exc:  # the generator is a black box we do not own
        raise MazeGenerationError(f"maze generator raised an error: {exc}") from exc

    if (not cells or len(cells) != MAZE_HEIGHT
            or any(len(row) != MAZE_WIDTH for row in cells)):
        raise MazeGenerationError(
            "maze generator returned a maze with an unexpected shape")

    is_wall = [[False] * BOARD_COLS for _ in range(BOARD_ROWS)]
    digit_tiles = []
    for cy in range(MAZE_HEIGHT):
        for cx in range(MAZE_WIDTH):
            bits = cells[cy][cx]
            tr, tc = cy * 2, cx * 2
            is_wall[tr][tc] = (bits == 15)          # '42' logo -> solid block
            is_wall[tr][tc + 1] = bool(bits & MAZE_E)
            is_wall[tr + 1][tc] = bool(bits & MAZE_S)
            is_wall[tr + 1][tc + 1] = True           # corner post
            if bits == 15:
                # every sub-tile of a '42' cell is solid by construction
                # (bits==15 sets all 4 wall bits) -- render its whole 2x2
                # block as one filled square, not thin lines/arcs.
                digit_tiles.extend([(tr, tc), (tr, tc + 1), (tr + 1, tc), (tr + 1, tc + 1)])

    board = [[EMPTY] * BOARD_COLS for _ in range(BOARD_ROWS)]
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            board[r][c] = (_autotile(is_wall, r, c, BOARD_ROWS, BOARD_COLS)
                            if is_wall[r][c] else DOT)
    for r, c in digit_tiles:
        board[r][c] = SOLID

    ghost_pocket = _compute_ghost_pocket()
    _validate_ghost_pocket(board, ghost_pocket)
    _seal_outer_border(board)
    _carve_tunnel(board)
    _carve_perimeter_ring(board)
    _carve_ghost_pocket(board, ghost_pocket)
    _thin_pacgums(board)
    _place_power_pellets(board)

    # pad one extra wall row so the shape exactly matches the 30x33 grid the
    # rest of pacman.py's pixel math was written against
    board.append([WALL_H] * BOARD_COLS)

    return board, ghost_pocket
