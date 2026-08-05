"""Strip the baked-in checkerboard from the spider / net art.

Both PNGs arrived fully opaque: what looks like transparency is actually a
light-grey checkerboard painted into the pixels. Blitting them as-is would
drop grey squares onto the maze, so the background has to become real alpha.

A plain "make every light pixel transparent" pass would also eat white
highlights inside the artwork, so this flood-fills inward from the border
instead: only background connected to the edge is removed, and anything
enclosed by the drawing survives. The result is cropped to its content so
the sprite fills its box when scaled.

Run once, offline; the game just loads the cleaned files.
"""

from collections import deque

from PIL import Image

# A checkerboard pixel is light and colourless. The art is either saturated
# (blue spider, yellow web) or dark (black linework), so neither matches.
LIGHT_MIN = 165
MAX_CHROMA = 30


def is_background(px):
    r, g, b = px[0], px[1], px[2]
    return min(r, g, b) >= LIGHT_MIN and max(r, g, b) - min(r, g, b) <= MAX_CHROMA


def strip(path, out_path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    px = img.load()

    seen = bytearray(w * h)
    queue = deque()

    for x in range(w):
        for y in (0, h - 1):
            if is_background(px[x, y]) and not seen[y * w + x]:
                seen[y * w + x] = 1
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_background(px[x, y]) and not seen[y * w + x]:
                seen[y * w + x] = 1
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        px[x, y] = (255, 255, 255, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if is_background(px[nx, ny]):
                    seen[ny * w + nx] = 1
                    queue.append((nx, ny))

    box = img.getbbox()
    if box:
        img = img.crop(box)
    img.save(out_path)
    print("%s -> %s  size=%s" % (path, out_path, img.size))


for name in ("spider", "net"):
    strip("assets/webslinger/%s.png" % name, "assets/webslinger/%s.png" % name)
