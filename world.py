"""Pure Python world data. No graphics dependencies; easy to test."""
from blocks import MATERIALS
MIN_XZ, MAX_XZ = -6, 5
MAX_HEIGHT = 10
MAX_BLOCKS = (MAX_XZ - MIN_XZ + 1) ** 2 * (MAX_HEIGHT + 1)

def valid_position(position):
    return (isinstance(position, (list, tuple)) and len(position) == 3
            and all(type(n) is int for n in position)
            and MIN_XZ <= position[0] <= MAX_XZ
            and 0 <= position[1] <= MAX_HEIGHT
            and MIN_XZ <= position[2] <= MAX_XZ)

def generate_world():
    return {(x, 0, z): 'grass' for x in range(MIN_XZ, MAX_XZ + 1)
            for z in range(MIN_XZ, MAX_XZ + 1)}

def intersects_player(position, player):
    x, y, z = position
    px, py, pz = player  # Player position is the feet, not the eye.
    return abs(x - px) < .85 and abs(z - pz) < .85 and y + .5 > py and y - .5 < py + 1.8

def can_place(blocks, position, material, player):
    return (valid_position(position) and material in MATERIALS
            and tuple(position) not in blocks
            and not intersects_player(position, player))

def can_remove(blocks, position):
    return tuple(position) in blocks and position[1] > 0

def spawn_position(blocks):
    height = max((y for x, y, z in blocks if x == 0 and z == 0), default=0)
    return (0, height + 2, 0)
