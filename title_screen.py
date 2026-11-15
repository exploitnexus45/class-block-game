"""Title screen for Glocinshmeel io (graphics proposal).

Preview it on its own:      python title_screen.py
Save a test picture:        python title_screen.py --screenshot   (writes artifacts/title.png)

Uses only Ursina and Pillow, which are already in requirements.txt.
All artwork is drawn by this code; no outside image files.
Nothing here reads or changes world data.

The PLAY button is a glossy red bouncy ball. Catch it (click it) and the screen flashes colored blocks,
then a loading screen counts
1...2......4 ... 1024!  To start the game after loading, pass a function: TitleScreen(on_loaded=start_game).
Without one, the loading screen goes back to the title when it finishes. See docs/handoff-title-screen.md.
"""
import argparse
import math
import random
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from ursina import Entity, Button, Text, Texture, camera, color, window, time, curve, destroy, invoke, application

GAME_NAME = 'GLOCINSHMEEL IO'
ART_H = 144          # the background is drawn as 144 rows of chunky pixels


# ---------------------------------------------------------------- small helpers

def hexrgb(h):
    """'#ffcc1a' -> (255, 204, 26)"""
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def make_texture(img):
    """Turn a Pillow image into an Ursina texture that stays crisp and pixelly."""
    tex = Texture(img)
    tex.filtering = None
    return tex


def sprite_image(rows, palette, flip=False):
    """Draw a sprite from text rows. Each letter in a row is looked up in palette; '.' is see-through."""
    h, w = len(rows), len(rows[0])
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.' and ch in palette:
                img.putpixel((w - 1 - x if flip else x, y), hexrgb(palette[ch]) + (255,))
    return img


def bounce(t, i):
    """Height of a hop from 0 (on the ground) to 1 (top). Each letter i starts a little later."""
    p = t + i * 0.13
    f = p - int(p)
    return 4 * f * (1 - f)


# ---------------------------------------------------------------- block font: every letter 7 blocks wide and 9 tall,
# with lines 2 blocks thick, so all the letters are even

FONT = {
    'G': ['.######', '#######', '##.....', '##.....', '##..###', '##..###', '##...##', '#######', '.######'],
    'L': ['##.....', '##.....', '##.....', '##.....', '##.....', '##.....', '##.....', '#######', '#######'],
    'O': ['.#####.', '#######', '##...##', '##...##', '##...##', '##...##', '##...##', '#######', '.#####.'],
    'C': ['.######', '#######', '##.....', '##.....', '##.....', '##.....', '##.....', '#######', '.######'],
    'I': ['#######', '#######', '..###..', '..###..', '..###..', '..###..', '..###..', '#######', '#######'],
    'N': ['##...##', '###..##', '####.##', '##.####', '##..###', '##...##', '##...##', '##...##', '##...##'],
    'S': ['.######', '#######', '##.....', '######.', '.######', '.....##', '.....##', '#######', '######.'],
    'H': ['##...##', '##...##', '##...##', '#######', '#######', '##...##', '##...##', '##...##', '##...##'],
    'M': ['##...##', '###.###', '#######', '##.#.##', '##...##', '##...##', '##...##', '##...##', '##...##'],
    'E': ['#######', '#######', '##.....', '#####..', '#####..', '##.....', '##.....', '#######', '#######'],
    'B': ['######.', '#######', '##...##', '######.', '######.', '##...##', '##...##', '#######', '######.'],
    'Y': ['##...##', '##...##', '###.###', '.#####.', '..###..', '..###..', '..###..', '..###..', '..###..'],
    'P': ['######.', '#######', '##...##', '##...##', '#######', '######.', '##.....', '##.....', '##.....'],
    'A': ['.#####.', '#######', '##...##', '##...##', '#######', '#######', '##...##', '##...##', '##...##'],
    'D': ['######.', '#######', '##...##', '##...##', '##...##', '##...##', '##...##', '#######', '######.'],
    '0': ['.#####.', '#######', '##...##', '##..###', '##.#.##', '###..##', '##...##', '#######', '.#####.'],
    '1': ['..###..', '.####..', '#####..', '..###..', '..###..', '..###..', '..###..', '#######', '#######'],
    '2': ['.#####.', '#######', '##...##', '....###', '..####.', '.###...', '###....', '#######', '#######'],
    '3': ['######.', '#######', '.....##', '.#####.', '.#####.', '.....##', '.....##', '#######', '######.'],
    '4': ['##...##', '##...##', '##...##', '#######', '#######', '.....##', '.....##', '.....##', '.....##'],
    '5': ['#######', '#######', '##.....', '######.', '#######', '.....##', '##...##', '#######', '.#####.'],
    '6': ['.#####.', '#######', '##.....', '######.', '#######', '##...##', '##...##', '#######', '.#####.'],
    '8': ['.#####.', '#######', '##...##', '.#####.', '#######', '##...##', '##...##', '#######', '.#####.'],
    '!': ['.###.', '.###.', '.###.', '.###.', '.###.', '.###.', '.....', '.###.', '.###.'],
}

# what the loading screen counts, typed out a little at a time
COUNT_TEXT = '1...2......4......8.....16......32.......64........128........256.....512.....1024!'
COUNT_NUMBERS = [m for m in re.finditer(r'\d+', COUNT_TEXT)]

# letter colors: (shine at the top, main color, darker at the bottom)
LETTER_COLORS = {
    'gold':  ('#fff3a8', '#ffc828', '#d98a00'),
    'green': ('#d6ffb0', '#5cd660', '#1f9a38'),
    'blue':  ('#d4ecff', '#4c9cff', '#1e56d0'),
    'white': ('#ffffff', '#ffffff', '#d8d8e2'),
}
CELL = 24      # picture pixels for each square of the font when a letter is drawn
PAD = 1        # empty font squares around each letter picture, for the outline and shadow
_letter_pictures = {}


def letter_texture(ch, name):
    """Draw one solid letter: smooth color fading top to bottom with a shiny top edge, inside a
    blocky, stair-stepped dark outline and a blocky shadow. The FONT grid gives the shape."""
    if (ch, name) in _letter_pictures:
        return _letter_pictures[(ch, name)]
    rows = FONT[ch]
    W, H = (len(rows[0]) + 2 * PAD) * CELL, (len(rows) + 2 * PAD) * CELL

    # 1. the shape: fill in every '#'
    grid = Image.new('L', (W, H), 0)
    draw = ImageDraw.Draw(grid)
    for r, line in enumerate(rows):
        for c, bit in enumerate(line):
            if bit == '#':
                x0, y0 = (c + PAD) * CELL, (r + PAD) * CELL
                draw.rectangle([x0, y0, x0 + CELL - 1, y0 + CELL - 1], fill=255)
    # the colored part gets softened corners so it looks smooth inside
    shape = grid.filter(ImageFilter.GaussianBlur(CELL * .3)).point(lambda v: 255 if v > 110 else 0)
    # the outline grows out from the square grid with a square brush and no blur,
    # so its edges stay straight and step like blocks
    outline = grid.filter(ImageFilter.MaxFilter(2 * int(CELL * .34) + 1))

    def layer(rgb, mask, strength=1.0):
        part = Image.new('RGBA', (W, H), rgb + (0,))
        part.putalpha(mask.point(lambda v: int(v * strength)))
        return part

    def moved(mask, dx, dy):
        out = Image.new('L', (W, H), 0)
        out.paste(mask, (dx, dy))
        return out

    # 2. color that fades from the shine color at the top to the darker color at the bottom
    top, main, bottom = (hexrgb(c) for c in LETTER_COLORS[name])
    fill = Image.new('RGBA', (W, H))
    paint = ImageDraw.Draw(fill)
    y0, y1 = PAD * CELL, H - PAD * CELL
    for y in range(H):
        f = min(1, max(0, (y - y0) / (y1 - y0)))
        a, b, k = (top, main, f / .5) if f < .5 else (main, bottom, (f - .5) / .5)
        paint.line([(0, y), (W, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)) + (255,))
    fill.putalpha(shape)

    # 3. stack it up: shadow, outline, color, shiny top edges, darker bottom edges
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    img = Image.alpha_composite(img, layer((0, 0, 0), moved(outline, int(CELL * .34), int(CELL * .34)), .5))
    img = Image.alpha_composite(img, layer((8, 8, 14), outline))
    img = Image.alpha_composite(img, fill)
    img = Image.alpha_composite(img, layer((255, 255, 255), ImageChops.subtract(shape, moved(shape, 0, int(CELL * .22))), .55))
    img = Image.alpha_composite(img, layer((0, 0, 0), ImageChops.subtract(shape, moved(shape, 0, -int(CELL * .18))), .22))

    texture = Texture(img)          # smooth, not pixelly
    _letter_pictures[(ch, name)] = texture
    return texture


# ---------------------------------------------------------------- the glossy PLAY ball

def ball_textures(size=160):
    """Two pictures for the bouncy PLAY ball: the shiny red ball itself, and a soft white shine
    that sits on top and always stays at the upper left, so the ball looks glossy even while it spins."""
    r0 = size / 2 - 6
    body = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            dx, dy = x - size / 2 + .5, y - size / 2 + .5
            d = (dx * dx + dy * dy) ** .5
            if d > r0 + 5:
                continue
            if d > r0:                                                   # dark outline
                body.putpixel((x, y), (20, 6, 8, 255))
                continue
            lx, ly = dx + r0 * .35, dy + r0 * .4                         # light comes from the upper left
            f = min(1, (lx * lx + ly * ly) ** .5 / (r0 * 1.55))
            light, mid, dark = (255, 120, 104), (226, 38, 40), (120, 8, 16)
            a, b, k = (light, mid, f / .45) if f < .45 else (mid, dark, (f - .45) / .55)
            c = [int(a[i] + (b[i] - a[i]) * k) for i in range(3)]
            rim = max(0, (d / r0 - .82) / .18) * max(0, (dx + dy) / (r0 * 1.4))   # bounce light on the lower right
            c = [min(255, int(v + 90 * rim)) for v in c]
            body.putpixel((x, y), tuple(c) + (255,))
    shine = Image.new('L', (size, size), 0)
    ImageDraw.Draw(shine).ellipse([size * .22, size * .14, size * .56, size * .38], fill=235)
    ImageDraw.Draw(shine).ellipse([size * .62, size * .66, size * .7, size * .74], fill=120)
    shine = shine.filter(ImageFilter.GaussianBlur(size * .025))
    gloss = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    gloss.putalpha(shine)
    return Texture(body), Texture(gloss)


# ---------------------------------------------------------------- sprites

# A dog facing right, 20 x 14. B = fur, b = darker fur, W = light fur, K = eye and nose, T = tongue, C = collar.
DOG_TOP = [
    '..............bb....',
    '.............bBBb...',
    '............bBBBBB..',
    '............BBKBBBWW',
    '............BBBBWWWK',
    '............BBBBWWT.',
    '............CCCCC.T.',
    '..bBBBBBBBBBBBBB....',
    '..BBBBBBBBBBBBBB....',
    '..BBBBBBBBBBBBBB....',
    '..bBBWWWWWWWWBBb....',
]
DOG_LEGS = {
    'run1':  ['..bB........bB......', '.bB..........bB.....', '.bb...........bb....'],
    'run2':  ['...bB......bB.......', '....bB....bB........', '....bb....bb........'],
    'stand': ['..bB.bB...bB.bB.....', '..bB.bB...bB.bB.....', '..bb.bb...bb.bb.....'],
}
DOG_TAILS = [[(1, 6), (0, 5), (0, 4)], [(1, 7), (0, 7), (0, 6)]]      # tail up, tail down: wagging
DOG_FURS = [
    {'B': '#d9a25a', 'b': '#9c6a32', 'W': '#f6e2bf', 'C': '#e02828'},   # golden dog, red collar
    {'B': '#3d3d44', 'b': '#1f1f24', 'W': '#d8d8de', 'C': '#2a7cf0'},   # black-and-white dog, blue collar
    {'B': '#f2f2f4', 'b': '#b4b4bc', 'W': '#ffffff', 'C': '#2ec850'},   # white dog, green collar
    {'B': '#8a5a3a', 'b': '#5a3a22', 'W': '#d9b08a', 'C': '#ffcc28'},   # brown dog, yellow collar
    {'B': '#c8c8cc', 'b': '#7d7d86', 'W': '#efefef', 'C': '#c04ad8'},   # gray dog, purple collar
    {'B': '#c4562c', 'b': '#86361a', 'W': '#f4cfa6', 'C': '#ffffff'},   # red dog, white collar: chases the PLAY ball
]
DOG_FIXED = {'K': '#151515', 'T': '#ff7a9a'}


def dog_rows(legs, tail):
    rows = [list(r) for r in DOG_TOP + DOG_LEGS[legs]]
    for x, y in DOG_TAILS[tail]:
        rows[y][x] = 'B'
    return [''.join(r) for r in rows]


BALL = ['.RR.', 'RRWR', 'RRRR', '.RR.']
CLOUD = [
    '.....WWWW...........',
    '...WWWWWWWW...WWW...',
    '..WWWWWWWWWWWWWWWWW.',
    '.WWWWWWWWWWWWWWWWWWW',
    'WWWWWWWWWWWWWWWWWWWW',
    'GWWWWWWWWWWWWWWWWWWG',
    '.GGGGGGGGGGGGGGGGGG.',
]
TREE = ['...LLLLL...', '..LLlLLLL..', '.LLLLLLlLL.', 'LLlLLLLLLLL', 'LLLLLLlLLLd', 'LLLLLLLLLdd',
        '.dLLlLLLdd.', '..ddddddd..', '.....T.....', '.....Tt....', '.....T.....', '....TTT....']
FLOWER_COLORS = ['#ffd84a', '#7fd2ff', '#ffffff', '#ff8ac8', '#ff6a4a']

# A miner dog facing right, 26 x 18, with a yellow helmet and lamp. The pickaxe is added by PICK_UP or PICK_DOWN.
MINER = [
    '............hhYYYy........',
    '...........hYYYYYYyL......',
    '...........YYYYYYYYLL.....',
    '..........yyyyyyyyyy......',
    '..........bBBBBBBBB.......',
    '.........bbBKKBBBWWW......',
    '.........bbBKEBBWWWWWK....',
    '.........bbBBBBWWWWWWK....',
    '..........bBBBBwWWWW......',
    '...........BBBBBwTT.......',
    '..........CCCCCC..T.......',
    '....HHHHHHHHHBBBBB........',
    '...BBBBBBBBBBBBBBB........',
    '...BBBBBBBBBBBBBBB........',
    '...bBBBwwwwwwwwBBb........',
    '...bB..bB....bB..bB.......',
    '...bB..bB....bB..bB.......',
    '...KK..KK....KK..KK.......',
]
MINER_TAILS = [[(2, 10), (1, 11), (2, 11), (2, 12)], [(0, 11), (1, 11), (2, 11), (1, 12), (2, 12)]]
PICK_UP = [(18, 11, 'B'), (19, 11, 'B'), (20, 11, 'B'), (21, 11, 'b'),
           (23, 3, 'P'), (23, 4, 'p'), (23, 5, 'P'), (23, 6, 'p'), (23, 7, 'P'), (23, 8, 'p'), (23, 9, 'P'), (23, 10, 'p'), (23, 11, 'P'),
           (21, 3, 'G'), (22, 2, 'G'), (23, 2, 'G'), (24, 2, 'G'), (25, 3, 'G'), (23, 1, 'g'), (22, 1, 'g')]
PICK_DOWN = [(18, 12, 'B'), (19, 12, 'b'),
             (18, 13, 'P'), (19, 13, 'p'), (20, 13, 'P'), (21, 13, 'p'), (22, 13, 'P'), (23, 13, 'p'),
             (24, 10, 'G'), (25, 11, 'G'), (25, 12, 'g'), (24, 12, 'G'), (24, 13, 'G'), (24, 14, 'G'), (25, 14, 'g'), (25, 15, 'G'), (24, 16, 'G')]
MINER_FIXED = {'Y': '#ffd400', 'y': '#c79a00', 'h': '#fff07a', 'L': '#fffbe0', 'K': '#0d0d0d', 'E': '#ffffff',
               'T': '#ff7a9a', 'P': '#7a5230', 'p': '#9b6b40', 'G': '#a7b0ba', 'g': '#e1e7ec'}
MINER_FURS = [
    {'B': '#c98b4b', 'b': '#8d5a2b', 'H': '#e2ac6c', 'W': '#f3dcb6', 'w': '#d8b88e', 'C': '#d62020'},   # golden miner
    {'B': '#3d3d42', 'b': '#222226', 'H': '#5b5b63', 'W': '#8f8f96', 'w': '#6d6d74', 'C': '#2a7cf0'},   # black miner
]


def miner_rows(pick_down, tail):
    rows = [list(r) for r in MINER]
    for x, y in MINER_TAILS[tail]:
        rows[y][x] = 'B'
    for x, y, ch in (PICK_DOWN if pick_down else PICK_UP):
        rows[y][x] = ch
    return [''.join(r) for r in rows]


CART = ['...gObGOg...', '.KKKKKKKKKK.', '.KSSSSSSSSK.', '.KSsSSSSsSK.', '.KKKKKKKKKK.', '..KK....KK..']
WEB = ['W.W.W.', '.WWW..', 'WWW...', '.W....', 'W.....']
LAYERS = {
    'dirt': ['#7a5232', '#6a4528', '#86593a', '#5c3b22'],
    'stone': ['#7b7b7b', '#6d6d6d', '#878787', '#626262'],
    'deepslate': ['#43434c', '#38383f', '#4d4d56', '#2f2f35'],
    'bedrock': ['#161616', '#3a3a3a', '#585858', '#0a0a0a', '#2a2a2a'],
}
ORES = ['#ffcc1a', '#2ee86b', '#3a7bff', '#141414']        # gold, green, blue, coal
ORE_SHINE = ['#fff2a0', '#b6ffcf', '#b8d4ff', '#3a3a3a']
BLOCK = 8              # art pixels per block, like one block in the game
STONE_TOP = 96         # art row where the dirt ends and the stone starts


# ---------------------------------------------------------------- the background scene

class Scene:
    """Draws the background as one picture: a sunny sky and rolling hills on top, and a cut-away of the
    ground underneath with a mine shaft. It also remembers where the hills, torches and miner dogs are."""

    def __init__(self, art_w):
        self.w, self.h = art_w, ART_H
        rnd = random.Random(1337)
        px = [[(0, 0, 0)] * self.w for _ in range(self.h)]

        def put(x, y, c):
            if 0 <= x < self.w and 0 <= y < self.h:
                px[y][x] = c if isinstance(c, tuple) else hexrgb(c)

        def stamp(rows, x0, y0, palette, flip=False):
            width = len(rows[0])
            for j, row in enumerate(rows):
                for i, ch in enumerate(row):
                    if ch in palette:
                        put(x0 + (width - 1 - i if flip else i), y0 + j, palette[ch])

        def mix(a, b, f):
            a, b = hexrgb(a), hexrgb(b)
            return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

        def shade(c, i, j):
            """Lighter top-left edge and darker bottom-right edge, so each block looks like a cube."""
            if i == 0 or j == 0:
                return tuple(min(255, v + 12) for v in c)
            if i == BLOCK - 1 or j == BLOCK - 1:
                return tuple(int(v * .82) for v in c)
            return c

        # ---- sky and sun
        for y in range(self.h):
            sky = mix('#2470cf', '#86c4ee', min(1, y / 60))
            for x in range(self.w):
                px[y][x] = sky
        sx, sy = round(self.w * .86), 44
        for dy in range(-9, 10):
            for dx in range(-9, 10):
                d = (dx * dx + dy * dy) ** .5
                if d <= 8.6:
                    put(sx + dx, sy + dy, '#fff6b0' if d < 5 else '#ffe14d' if d < 7.4 else '#ffc21a')
        for k in range(8):
            ang = k * math.pi / 4
            for r in range(11, 15):
                put(round(sx + math.cos(ang) * r), round(sy + math.sin(ang) * r), '#ffd84a')

        # ---- far and middle hills
        for x in range(self.w):
            far_top = int(self.far(x))
            for y in range(far_top, self.h):
                put(x, y, '#c3ead0' if y == far_top else ('#a6dbb4' if (x + y) % 7 else '#9ccfaa'))
        for x in range(0, self.w, 17):
            stamp(['.F.', 'FFF', 'FFF', '.t.'], x, int(self.far(x + 1)) - 4, {'F': '#86c497', 't': '#8a9c86'})
        for f in (.08, .3, .7):
            x = round(self.w * f)
            stamp(TREE, x, int(self.mid(x + 5)) - len(TREE) + 1,
                  {'L': '#5fbf4e', 'l': '#8ee06a', 'd': '#3f9038', 'T': '#7a5230', 't': '#9b6b40'})
        for x in range(self.w):
            mid_top = int(self.mid(x))
            for y in range(mid_top, self.h):
                depth = y - mid_top
                c = '#a2ee78' if depth < 2 else mix('#6ccc5a', '#4fa648', min(1, depth / 12))
                if depth >= 2 and rnd.random() < .08:
                    c = mix('#5cbc4e', '#3f9038', min(1, depth / 12))
                put(x, y, c)

        # ---- the front hill is cut open: grass on top, then dirt, then the stone layers with the mine shaft
        rows = (self.h - STONE_TOP) // BLOCK                 # 6 rows of blocks under the dirt
        cols = self.w // BLOCK + 1
        self.c0, self.c1 = max(1, round(cols * .16)), min(cols - 2, round(cols * .84))
        tunnel_rows = (1, 2)
        self.ceil, self.floor = STONE_TOP + BLOCK, STONE_TOP + 3 * BLOCK

        def layer(r):
            return 'bedrock' if r == rows - 1 else 'deepslate' if r == rows - 2 else 'stone'

        blocks, self.ores = {}, []
        for r in range(rows):
            for c in range(cols):
                in_tunnel = r in tunnel_rows and self.c0 <= c <= self.c1
                ore = None
                if layer(r) != 'bedrock' and not in_tunnel and rnd.random() < .1:
                    ore = 3 if rnd.random() < .35 else rnd.randrange(3)
                if r in tunnel_rows and c == self.c0 - 1:
                    ore = 0                                   # gold wall for the left miner
                if r in tunnel_rows and c == self.c1 + 1:
                    ore = 2                                   # blue wall for the right miner
                blocks[r, c] = (layer(r), in_tunnel, ore)
                if ore is not None and ore < 3:
                    self.ores.append((c * BLOCK + 4, STONE_TOP + r * BLOCK + 4))

        roots = {c: rnd.randrange(1, 6) for c in range(cols) if rnd.random() < .25}
        for x in range(self.w):
            top = int(self.near(x))
            hang = 3 + (1 if (x * 3) % 5 == 0 else 0) + (1 if x % 3 == 0 else 0)
            if rnd.random() < .45:
                put(x, top - 1, '#7ad85a')                    # grass tufts
            for y in range(top, self.h):
                i, depth = x % BLOCK, y - top
                if y < STONE_TOP:
                    if depth < 2:
                        c = hexrgb('#b4f57e')
                    elif depth < hang:
                        c = hexrgb(rnd.choice(('#5fae3f', '#4f9a34', '#438a2b')))
                    else:
                        c = hexrgb(rnd.choice(LAYERS['dirt']))
                        if rnd.random() < .06:
                            c = (143, 138, 132)              # pebbles
                        if roots.get(x // BLOCK) == i and depth < 14:
                            c = (59, 38, 20)                 # roots
                        c = shade(c, i, y % BLOCK)
                else:
                    r, j = (y - STONE_TOP) // BLOCK, (y - STONE_TOP) % BLOCK
                    kind, in_tunnel, ore = blocks[r, x // BLOCK]
                    pal = LAYERS[kind]
                    if kind == 'deepslate' and j % 3 == 1:
                        pal = [pal[1], pal[3]]
                    c = hexrgb(rnd.choice(pal))
                    roll = rnd.random()
                    if kind == 'stone' and roll < .05:
                        c = (77, 77, 77)
                    if kind == 'bedrock' and roll < .08:
                        c = (106, 106, 106)
                    if ore is not None and 0 < i < 7 and 0 < j < 7 and rnd.random() < .26:
                        c = hexrgb(ORE_SHINE[ore] if rnd.random() < .3 else ORES[ore])
                    c = shade(c, i, j)
                    if in_tunnel:
                        c = tuple(int(v * .6) for v in c)    # the back wall of the tunnel is a little shaded
                put(x, y, c)
            if rnd.random() < .06:                           # flowers on the front hill
                put(x, top - 1, '#3a8a2c')
                put(x, top - 2, rnd.choice(FLOWER_COLORS))

        # ---- inside the mine shaft: beams, posts, rails, cobwebs, a minecart, torches
        tx0, tx1 = self.c0 * BLOCK, (self.c1 + 1) * BLOCK
        for x in range(tx0, tx1):
            put(x, self.ceil, '#7a5530')
            put(x, self.ceil + 1, '#4a311c')
        for c in range(self.c0 + 2, self.c1, 4):
            x = c * BLOCK + 3
            for y in range(self.ceil, self.floor):
                put(x, y, '#7a5530')
                put(x + 1, y, '#4a311c')
        for x in range(tx0, tx1):
            put(x, self.floor - 2, '#8d96a0')
            if x % 3 != 2:
                put(x, self.floor - 1, '#3d2a18')
        stamp(WEB, tx0, self.ceil + 2, {'W': '#8c8e96'})
        stamp(WEB, tx1 - 6, self.ceil + 2, {'W': '#8c8e96'}, flip=True)
        stamp(CART, (tx0 + tx1) // 2 - 14, self.floor - 2 - len(CART),
              {'K': '#24252b', 'S': '#646c78', 's': '#9aa3ad', 'g': ORES[0], 'O': ORES[3], 'b': ORES[2], 'G': ORES[1]})
        self.torches = [(round(tx0 + (tx1 - tx0) * f), self.ceil + 5) for f in (.36, .66)]
        for tx, ty in self.torches:
            for y in range(ty, ty + 5):
                put(tx, y, '#6b4423')

        # where the miner dogs stand, facing the ore walls at each end
        self.miner_scale = .8
        dog_w, dog_h = 26 * self.miner_scale, 18 * self.miner_scale
        foot = self.floor - 2
        self.miners = [(tx0 + 1 + dog_w / 2, foot - dog_h / 2, True),
                       (tx1 - 1 - dog_w / 2, foot - dog_h / 2, False)]
        lamps = [(x + (-1 if flip else 1) * 5, y - 4) for x, y, flip in self.miners]

        # ---- light: the stone gets darker deeper down, with light around torches, helmet lamps and shiny ore
        lights = [(x, y, 34, .95) for x, y in self.torches]
        lights += [(x + (-8 if k == 0 else 8), y + 5, 22, .9) for k, (x, y) in enumerate(lamps)]
        lights += [(x, y, 6, .35) for x, y in self.ores]
        warm = [(x, y - 1, 16, (255, 140, 30), .26) for x, y in self.torches]
        warm += [(x, y, 6, (255, 230, 120), .3) for x, y in lamps]
        for y in range(STONE_TOP - 6, self.h):
            for x in range(self.w):
                top = int(self.near(x))
                if y < top:
                    continue
                if y < STONE_TOP:
                    d = .25 * (y - (STONE_TOP - 6)) / 6       # dirt fades a little darker just above the stone
                else:
                    d = .12 + .38 * (y - STONE_TOP) / (self.h - STONE_TOP)
                for lx, ly, rad, a in lights:
                    dist = ((x - lx) ** 2 + (y - ly) ** 2) ** .5
                    if dist < rad:
                        d *= 1 - a * (1 - dist / rad)
                r, g, b = px[y][x]
                r, g, b = r * (1 - d), g * (1 - d), b * (1 - d) + 8 * d
                for lx, ly, rad, (wr, wg, wb), a in warm:
                    dist = ((x - lx) ** 2 + (y - ly) ** 2) ** .5
                    if dist < rad:
                        f = a * (1 - dist / rad)
                        r, g, b = r + wr * f, g + wg * f, b + wb * f
                px[y][x] = (min(255, int(r)), min(255, int(g)), min(255, int(b)))

        img = Image.new('RGB', (self.w, self.h))
        img.putdata([c for row in px for c in row])
        self.image = img

    # the top edge of each hill row, in art pixels, at a given x
    def far(self, x):
        return 60 + 4 * math.sin(x * .021 + .5) + 2 * math.sin(x * .058 + 1.3)

    def mid(self, x):
        return 69 + 4 * math.sin(x * .03 + 3.1) + 2 * math.sin(x * .075)

    def near(self, x):
        return 82 + 4 * math.sin(x * .034 + 1.0) + 2 * math.sin(x * .09 + 2.0)


# ---------------------------------------------------------------- the screen itself

class TitleScreen(Entity):
    """Title screen with the game name, a red PLAY button, sunny rolling hills with dogs playing,
    and a mine shaft underneath where two miner dogs dig."""

    def __init__(self, on_loaded=None, **kwargs):
        super().__init__(**kwargs)
        self.on_loaded = on_loaded          # the game to start when loading finishes (can be added later)
        self.clock = 0
        self.aspect = window.aspect_ratio
        self.scene = Scene(round(ART_H * self.aspect))
        self.art_w = self.scene.w

        # background picture filling the window
        self.background = Entity(parent=camera.ui, model='quad', texture=make_texture(self.scene.image),
                                 scale=(self.aspect, 1), z=1)

        # clouds drifting across the sky
        cloud_tex = make_texture(sprite_image(CLOUD, {'W': '#ffffff', 'G': '#dbe9f7'}))
        self.clouds = []
        for k, (cx, cy, size) in enumerate(((.12, 46, 1.0), (.3, 38, .8), (.66, 50, 1.1), (.95, 34, .7))):
            cloud = Entity(parent=camera.ui, model='quad', texture=cloud_tex, z=.7,
                           position=self.ui(cx * self.art_w, cy), scale=(20 * size / ART_H, 7 * size / ART_H))
            cloud.speed = .012 + .006 * k
            self.clouds.append(cloud)

        # the two miner dogs digging at each end of the mine shaft
        self.miner_frames, self.miner_dogs = [], []
        s = self.scene.miner_scale
        for k, (x, y, facing_left) in enumerate(self.scene.miners):
            palette = {**MINER_FIXED, **MINER_FURS[k]}
            frames = [[make_texture(sprite_image(miner_rows(down, tail), palette, facing_left)) for tail in (0, 1)]
                      for down in (False, True)]
            self.miner_frames.append(frames)
            self.miner_dogs.append(Entity(parent=camera.ui, model='quad', texture=frames[0][0], z=.5,
                                          position=self.ui(x, y), scale=(26 * s / ART_H, 18 * s / ART_H)))
        self.flames = [Entity(parent=camera.ui, model='quad', color=color.rgb32(255, 176, 0), z=.5,
                              position=self.ui(tx + .5, ty - 1.5), scale=(2 / ART_H, 3 / ART_H))
                       for tx, ty in self.scene.torches]
        self.chips = []

        # the dogs playing on the hills: each has its own fur, size, and game
        self.dog_textures = {}
        self.dogs = []
        for fur, size, z in ((0, 1, .48), (1, 1, .47), (2, 1, .5), (3, .6, .6), (4, .6, .6)):
            dog = Entity(parent=camera.ui, model='quad', z=z, scale=(20 * size / ART_H, 14 * size / ART_H))
            dog.fur, dog.size = fur, size
            self.dogs.append(dog)
        # one more dog that runs along the front hill trying to catch the bouncy PLAY ball
        self.chaser = Entity(parent=camera.ui, model='quad', z=.46, scale=(20 / ART_H, 14 / ART_H))
        self.chaser.fur, self.chaser.size = 5, 1
        self.chaser_x, self.chaser_jump, self.chaser_left = self.art_w * .5, 0, False
        self.ball = Entity(parent=camera.ui, model='quad', z=.49, scale=4 / ART_H,
                           texture=make_texture(sprite_image(BALL, {'R': '#e83a2c', 'W': '#ffffff'})))

        self.title_group = Entity(parent=camera.ui)
        self.build_title()
        self.loading_group = Entity(parent=camera.ui, enabled=False)
        self.build_loading()
        self.warp_cells = []
        self.warp_time = None
        self.after_flash = None

    # art pixel -> screen position
    def ui(self, ax, ay):
        return ((ax / self.art_w - .5) * self.aspect, .5 - ay / ART_H)

    # ---------------- letters
    def word(self, text, parent, center_y, max_width, max_square, color_names, drop=True):
        """Write text in big smooth letters, centered. Every letter is the same width, so they line up evenly."""
        widths = [3 if ch == ' ' else len(FONT[ch][0]) + 1 for ch in text]
        total = sum(widths) - 1
        size = min(max_width / total, max_square)        # screen size of one square of the font
        x = -total * size / 2
        letters = []
        n = 0
        for ch, w in zip(text, widths):
            if ch == ' ':
                x += w * size
                continue
            cols, rows = len(FONT[ch][0]), len(FONT[ch])
            top = center_y + rows * size / 2
            letter = Entity(parent=parent, position=(x, top))
            Entity(parent=letter, model='quad', texture=letter_texture(ch, color_names[n % len(color_names)]),
                   position=(cols * size / 2, -rows * size / 2), scale=((cols + 2 * PAD) * size, (rows + 2 * PAD) * size))
            letter.spots = [((c + .5) * size, -(r + .5) * size)
                            for r, line in enumerate(FONT[ch]) for c, bit in enumerate(line) if bit == '#']
            if drop:                    # each letter drops in from above, one after another, and bounces into place
                letter.y = top + .8
                letter.animate_y(top, duration=.5, delay=.3 + n * .12, curve=curve.out_bounce)
            letters.append(letter)
            x += w * size
            n += 1
        return letters, size

    def build_title(self):
        g = self.title_group
        self.letters, self.square = self.word(GAME_NAME, g, .355, self.aspect * .9, .022, ['gold', 'green', 'blue'])
        self.letter_y = [.355 + len(FONT['G']) * self.square / 2] * len(self.letters)
        self.tagline = Text('DIG.   BUILD.   EXPLORE.', parent=g, origin=(0, 0), position=(0, .25), scale=1.1,
                            color=color.rgb32(20, 52, 110))
        self.hint = Text('CATCH THE BALL TO PLAY!', parent=g, origin=(0, 0), position=(0, .19), scale=1.2,
                         color=color.rgb32(200, 24, 30))
        # the PLAY button is a glossy red bouncy ball: click it to catch it
        body_tex, gloss_tex = ball_textures()
        self.ball_size = .17
        self.ball_root = Entity(parent=g, position=(0, .1, -.05))
        self.play = Button(parent=self.ball_root, model='quad', texture=body_tex, text='', scale=self.ball_size,
                           color=color.white, highlight_color=color.rgb32(255, 228, 228), pressed_color=color.rgb32(220, 200, 200))
        self.play.on_click = self.catch_ball
        self.ball_word = Entity(parent=self.ball_root, z=-.01)
        self.word('PLAY', self.ball_word, 0, self.ball_size * .62, .0065, ['white'], drop=False)
        Entity(parent=self.ball_root, model='quad', texture=gloss_tex, scale=self.ball_size, z=-.02)
        self.ball_vel = [.42, .9]
        self.ball_caught = False
        # sparkle that hops around the letters
        self.sparkle = Entity(parent=g, model='quad', color=color.white, scale=.012, rotation_z=45, z=-.01)
        self.sparkle_timer = 0

    # ---------------- the bouncy PLAY ball
    def bounce_ball(self, dt):
        if not self.title_group.enabled or self.ball_caught:
            return
        dt = min(dt, 1 / 30)
        r = self.ball_size / 2
        ball, vel = self.ball_root, self.ball_vel
        vel[1] -= 1.5 * dt                                   # gravity pulls it down
        ball.x += vel[0] * dt
        ball.y += vel[1] * dt
        left, right = -self.aspect / 2 + r, self.aspect / 2 - r
        if ball.x < left or ball.x > right:                  # bounce off the sides
            ball.x = min(max(ball.x, left), right)
            vel[0] = -vel[0]
        if ball.y > .5 - r:                                  # bounce off the top
            ball.y, vel[1] = .5 - r, -abs(vel[1])
        if ball.y < -.5 + r:                                 # bounce off the bottom, a bit higher or lower each time
            ball.y = -.5 + r
            vel[1] = random.uniform(1.15, 1.45)
            vel[0] = math.copysign(random.uniform(.3, .62), vel[0])
            ball.scale = (1.18, .8, 1)                       # squish when it hits
            ball.animate_scale((1, 1, 1), duration=.22, curve=curve.out_back)
        self.ball_word.rotation_z += vel[0] * 260 * dt         # PLAY spins as the ball rolls through the air

    def chase_ball(self, t, dt):
        """The red dog runs along the front hill toward the ball and jumps when it comes close."""
        dt = min(dt, 1 / 30)
        w = self.art_w
        ball_x = (self.ball_root.x / self.aspect + .5) * w          # ball position in art pixels
        ball_y = (.5 - self.ball_root.y) * ART_H
        playing = self.title_group.enabled and not self.ball_caught
        target = min(max(ball_x, 12), w - 12) if playing else self.chaser_x
        dx = target - self.chaser_x
        moving = abs(dx) > 2
        if moving:
            step = 42 * dt
            self.chaser_x += max(-step, min(step, dx))
            self.chaser_left = dx < 0
        ground = self.scene.near(self.chaser_x)
        ball_close = abs(ball_x - self.chaser_x) < 14 and ground - 45 < ball_y < ground + 10
        if playing and self.chaser_jump <= 0 and ball_close:
            self.chaser_jump = .5
        lift = 0
        if self.chaser_jump > 0:
            self.chaser_jump -= dt
            lift = math.sin((1 - max(0, self.chaser_jump) / .5) * math.pi) * 12
        legs = ('run1' if int(t / .09) % 2 else 'run2') if moving or lift else 'stand'
        self.put_dog(self.chaser, self.chaser_x, ground, legs, int(t / .1) % 2, self.chaser_left, lift)

    def catch_ball(self):
        if self.ball_caught or self.warp_time is not None:
            return
        self.ball_caught = True
        self.ball_root.animate_scale((1.35, 1.35, 1), duration=.15, curve=curve.out_back)
        self.flash(after=self.start_loading)

    def reset_ball(self):
        self.ball_caught = False
        self.ball_root.position = (0, .1, -.05)
        self.ball_root.scale = 1
        self.ball_vel = [random.choice((-1, 1)) * .42, .9]

    # ---------------- loading screen
    def build_loading(self):
        g = self.loading_group
        Entity(parent=g, model='quad', color=color.rgba32(6, 10, 26, 210), scale=(self.aspect + .1, 1.1), z=.2)
        self.word('LOADING', g, .33, .5, .011, ['white'], drop=False)
        self.big_number = Entity(parent=g, y=.1)
        self.count_line = Text('', parent=g, origin=(0, 0), position=(0, -.08), scale=1.35,
                               color=color.rgb32(219, 230, 255))
        # a bar with one slot for each number: 1, 2, 4 ... 1024
        n, slot_w, gap = len(COUNT_NUMBERS), .052, .012
        x0 = -(n * slot_w + (n - 1) * gap) / 2 + slot_w / 2
        self.slot_colors = [color.rgb32(255, 200, 40), color.rgb32(92, 214, 96), color.rgb32(76, 156, 255)]
        self.slots = []
        for i in range(n):
            x = x0 + i * (slot_w + gap)
            Entity(parent=g, model='quad', color=color.rgb32(8, 8, 14), position=(x, -.17), scale=(slot_w + .01, .046), z=.01)
            self.slots.append(Entity(parent=g, model='quad', color=color.rgb32(40, 44, 58), position=(x, -.17),
                                     scale=(slot_w, .034)))

    def start_loading(self):
        self.title_group.enabled = False
        self.loading_group.enabled = True
        self.loading_time = 0
        self.shown_chars = -1
        self.shown_number = ''
        self.count_line.text = ''
        for slot in self.slots:
            slot.color = color.rgb32(40, 44, 58)
        for child in list(self.big_number.children):
            destroy(child)

    def back_to_title(self):
        self.loading_group.enabled = False
        self.title_group.enabled = True
        self.loading_time = None
        self.reset_ball()

    def finish_loading(self):
        self.loading_time = None
        if self.on_loaded:
            start = self.on_loaded
            self.close()
            start()
        else:
            self.flash(after=self.back_to_title)

    def update_loading(self, dt):
        if getattr(self, 'loading_time', None) is None:
            return
        self.loading_time += dt
        shown = min(len(COUNT_TEXT), int(self.loading_time / .06))
        if shown != self.shown_chars:
            self.shown_chars = shown
            self.count_line.text = COUNT_TEXT[:shown]
            done = [m for m in COUNT_NUMBERS if m.end() <= shown]       # numbers typed all the way
            for i, slot in enumerate(self.slots):
                if i < len(done):
                    slot.color = self.slot_colors[i % 3]
            number = (done[-1].group() if done else '') + ('!' if shown == len(COUNT_TEXT) else '')
            if number != self.shown_number:
                self.shown_number = number
                for child in list(self.big_number.children):
                    destroy(child)
                colors = [['gold', 'green', 'blue'][len(done) % 3]]
                self.word(number, self.big_number, 0, .7, .02, colors, drop=False)
                self.big_number.scale = 1.35                             # the new number pops in
                self.big_number.animate_scale(1, duration=.18, curve=curve.out_back)
        if shown == len(COUNT_TEXT) and self.loading_time > len(COUNT_TEXT) * .06 + 1.6:
            self.finish_loading()

    def close(self):
        for e in ([self.background, self.title_group, self.loading_group, self.sparkle, self.ball, self.chaser]
                  + self.clouds + self.dogs
                  + self.miner_dogs + self.flames + self.chips + self.warp_cells):
            destroy(e)
        destroy(self)

    # ---------------- PLAY flash: the screen fills with colored blocks, then clears again
    def flash(self, after=None):
        if self.warp_time is not None:
            return
        self.warp_time = 0
        self.after_flash = after            # what to switch to while the blocks cover the screen
        cell = 16 / ART_H
        palette = [color.rgb32(166, 255, 77), color.rgb32(111, 208, 255), color.rgb32(255, 211, 77),
                   color.rgb32(122, 43, 214), color.black]
        cols, rows = int(self.aspect / cell) + 1, int(1 / cell) + 1
        for c in range(cols):
            for r in range(rows):
                e = Entity(parent=camera.ui, model='quad', color=random.choice(palette), scale=cell,
                           position=(-self.aspect / 2 + (c + .5) * cell, .5 - (r + .5) * cell), z=-.5, enabled=False)
                e.show_at, e.hide_at = random.uniform(0, .38), random.uniform(.5, .88)
                self.warp_cells.append(e)

    # ---------------- every frame
    def update(self):
        dt = time.dt
        self.clock += dt
        t = self.clock

        # once they have landed, all the letters float up and down together, so they stay even
        if t > 2.6:
            float_y = math.sin((t - 2.6) * 1.6) * self.square * .5
            for i, letter in enumerate(self.letters):
                letter.y = self.letter_y[i] + float_y

        # sparkle twinkles on a random spot of a random letter
        self.sparkle_timer -= dt
        if self.sparkle_timer <= 0 and t > 2.6:
            self.sparkle_timer = .5
            letter = random.choice(self.letters)
            sx, sy = random.choice(letter.spots)
            self.sparkle.position = (letter.x + sx, letter.y + sy, -.01)
            self.sparkle.scale = self.square * 1.1
            self.sparkle.animate_scale(0, duration=.45)

        # clouds drift and come back around
        for cloud in self.clouds:
            cloud.x += cloud.speed * dt
            if cloud.x > self.aspect / 2 + .1:
                cloud.x = -self.aspect / 2 - .1

        self.play_with_dogs(t)
        self.dig(t, dt)
        self.update_loading(dt)
        self.bounce_ball(dt)
        self.chase_ball(t, dt)

        # PLAY flash blocks
        if self.warp_time is not None:
            self.warp_time += dt
            w = self.warp_time
            if w >= .38 and self.after_flash:
                switch, self.after_flash = self.after_flash, None
                switch()
            for e in self.warp_cells:
                e.enabled = e.show_at <= w < e.hide_at
            if w > .9:
                for e in self.warp_cells:
                    destroy(e)
                self.warp_cells = []
                self.warp_time = None

    # ---------------- dogs playing on the hills
    def dog_texture(self, fur, legs, tail, facing_left):
        key = (fur, legs, tail, facing_left)
        if key not in self.dog_textures:
            img = sprite_image(dog_rows(legs, tail), {**DOG_FIXED, **DOG_FURS[fur]}, facing_left)
            self.dog_textures[key] = make_texture(img)
        return self.dog_textures[key]

    def put_dog(self, dog, x, ground, legs, tail, facing_left, lift=0):
        """Stand a dog with its paws on the ground line (art pixels), lifted up by lift pixels when it jumps."""
        dog.texture = self.dog_texture(dog.fur, legs, tail, facing_left)
        dog.position = self.ui(x, ground - 7 * dog.size - lift)

    def play_with_dogs(self, t):
        w, scene = self.art_w, self.scene
        stride = 'run1' if int(t / .11) % 2 else 'run2'
        wag = int(t / .15) % 2
        loop = w + 60

        # 1 and 2: the golden dog runs along the front hill and the black-and-white dog chases it
        lead = (t * 24) % loop - 30
        for k, x in enumerate((lead, lead - 30 if lead - 30 > -30 else lead - 30 + loop)):
            hop = abs(math.sin(t * 13 + k * 1.7)) * 2
            legs = stride if k == 0 else ('run2' if stride == 'run1' else 'run1')
            self.put_dog(self.dogs[k], x, scene.near(x), legs, wag, False, hop)

        # 3: the white dog plays fetch, running back and forth under the ball and jumping to catch it
        period = 2.6
        throw, p = divmod(t, period)
        p /= period
        left, right = w * .56, w * .9
        start, end = (left, right) if int(throw) % 2 == 0 else (right, left)
        dog_x = start + (end - start) * p ** 1.4
        jump = math.sin(min(1, max(0, (p - .74) / .26)) * math.pi) * 8
        facing_left = end < start
        self.put_dog(self.dogs[2], dog_x, scene.near(dog_x), stride, wag, facing_left, jump)
        if p < .93:
            ball_x = start + (end - start) * p
            ball_y = scene.near(ball_x) - 9 - 24 * 4 * p * (1 - p)
        else:                                                  # caught: the ball sits in the dog's mouth
            ball_x = dog_x + (-9 if facing_left else 9)
            ball_y = scene.near(dog_x) - 8.5 - jump
        self.ball.position = self.ui(ball_x, ball_y)

        # 4: the brown dog on the middle hill sits wagging its tail and hops for joy every few seconds
        x = w * .22
        hop = bounce(t / 2.2, 0) * 5 if (t % 2.2) < .9 else 0
        self.put_dog(self.dogs[3], x, scene.mid(x), 'stand', int(t / .09) % 2, False, hop)

        # 5: the gray dog trots along the middle hill the other way
        x = w + 30 - (t * 9) % loop
        self.put_dog(self.dogs[4], x, scene.mid(x), stride, wag, True, abs(math.sin(t * 10)) * 1.2)


    # ---------------- miner dogs digging in the mine shaft
    def dig(self, t, dt):
        for k, dog in enumerate(self.miner_dogs):
            down = (t / .7 + (0, .45)[k]) % 1 > .55
            if down and not getattr(dog, 'was_down', False):
                self.spawn_chips(k)
            dog.was_down = down
            dog.texture = self.miner_frames[k][down][int(t / .22 + k) % 2]
        for chip in self.chips[:]:                            # rock chips fly and fall
            chip.vy -= .9 * dt
            chip.x += chip.vx * dt
            chip.y += chip.vy * dt
            chip.life -= dt
            if chip.life <= 0:
                self.chips.remove(chip)
                destroy(chip)
        for f in self.flames:                                 # torch flames flicker
            f.scale_y = (3 + random.choice((0, 1))) / ART_H

    def spawn_chips(self, k):
        x, y, facing_left = self.scene.miners[k]
        sx, sy = self.ui(x + (-1 if facing_left else 1) * 13 * self.scene.miner_scale, y + 3)
        for _ in range(5):
            chip = Entity(parent=camera.ui, model='quad', z=.4, scale=1 / ART_H, position=(sx, sy),
                          color=color.rgb32(*hexrgb(random.choice((ORES[(0, 2)[k]], '#7b7b7b')))))
            chip.vx = (1 if facing_left else -1) * random.uniform(.03, .1)
            chip.vy = random.uniform(.05, .12)
            chip.life = .6
            self.chips.append(chip)


# ---------------------------------------------------------------- preview on its own

def preview():
    parser = argparse.ArgumentParser()
    parser.add_argument('--screenshot', action='store_true', help='Save a picture of the title screen, then close.')
    args = parser.parse_args()
    import main as game_main          # applies the game's macOS shader fix, same as running main.py
    from ursina import Ursina
    app = Ursina(title='Glocinshmeel io', borderless=False, fullscreen=False, development_mode=False)
    window.size = (1100, 720)
    window.color = color.rgb32(36, 112, 207)
    if sys.platform == 'darwin':
        from ursina import scene
        shaders = (game_main.unlit_shader, game_main.unlit_with_fog_shader, game_main.text_shader)
        for entity in scene.entities:
            if entity.shader in shaders:
                entity.shader = entity.shader
    TitleScreen()
    if args.screenshot:
        out = Path(__file__).resolve().parent / 'artifacts'
        out.mkdir(exist_ok=True)
        invoke(lambda: app.screenshot(namePrefix=str(out / 'title.png'), defaultFilename=False), delay=4)
        invoke(application.quit, delay=4.5)
    app.run()


if __name__ == '__main__':
    preview()
