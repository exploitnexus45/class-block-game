"""Materials team: add materials here without changing the world's interface."""
MATERIALS = {
    'grass': {'label': 'Grass', 'rgb': (112, 166, 83)},
    'dirt': {'label': 'Dirt', 'rgb': (145, 102, 68)},
    'stone': {'label': 'Stone', 'rgb': (139, 151, 159)},
}

def material_ids():
    return list(MATERIALS)
