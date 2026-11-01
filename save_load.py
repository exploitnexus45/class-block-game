"""Save team: validate the whole save before replacing a running world."""
import json
from pathlib import Path
from blocks import MATERIALS
from objectives import CRYSTALS
from world import MAX_BLOCKS, valid_position, MIN_XZ, MAX_XZ

SAVE_PATH = Path(__file__).resolve().parent / 'saves' / 'world.json'

def validate(data):
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Unsupported save format.')
    rows = data.get('blocks')
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_BLOCKS:
        raise ValueError('Invalid block list.')
    blocks = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid block entry.')
        position, material = row.get('position'), row.get('material')
        if not valid_position(position) or not isinstance(material, str) or material not in MATERIALS:
            raise ValueError('Invalid position or unknown material.')
        position = tuple(position)
        if position in blocks:
            raise ValueError('Duplicate block position.')
        blocks[position] = material
    if any((x, 0, z) not in blocks for x in range(MIN_XZ, MAX_XZ + 1) for z in range(MIN_XZ, MAX_XZ + 1)):
        raise ValueError('The protected ground layer is missing.')
    collected = data.get('collected', [])
    if not isinstance(collected, list) or any(not isinstance(name, str) or name not in CRYSTALS for name in collected):
        raise ValueError('Invalid quest progress.')
    selected = data.get('selected')
    if not isinstance(selected, str) or selected not in MATERIALS:
        raise ValueError('Unknown selected material.')
    return blocks, set(collected), selected

def save_world(blocks, collected, selected, path=SAVE_PATH):
    data = {'version': 1, 'blocks': [{'position': list(p), 'material': m} for p, m in sorted(blocks.items())],
            'collected': sorted(collected), 'selected': selected}
    validate(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
    temporary.replace(path)

def load_world(path=SAVE_PATH):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError('Save is too large for this classroom world.')
    return validate(json.loads(path.read_text(encoding='utf-8')))
