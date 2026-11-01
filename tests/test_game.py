import json
import tempfile
import unittest
from pathlib import Path
from blocks import MATERIALS
from inventory import Inventory
from objectives import Objectives, CRYSTALS
from save_load import save_world, load_world
from world import generate_world, valid_position, can_place, can_remove, spawn_position

class GameTests(unittest.TestCase):
    def test_world_is_fresh_valid_data(self):
        first, second = generate_world(), generate_world()
        self.assertIsNot(first, second)
        self.assertTrue(all(valid_position(p) and m in MATERIALS for p, m in first.items()))
        self.assertTrue(all((x, 0, z) in first for x in range(-6, 6) for z in range(-6, 6)))

    def test_place_boundaries_and_body(self):
        blocks = generate_world()
        self.assertTrue(can_place(blocks, (2, 1, 2), 'grass', (0, .5, 0)))
        for p in [(6, 1, 0), (0, 11, 0), (0, -1, 0), (0, 0, 0), (0, 1, 0)]:
            self.assertFalse(can_place(blocks, p, 'grass', (0, .5, 0)), p)
        self.assertFalse(can_place(blocks, (2, 1, 2), 'unknown', (0, .5, 0)))
        self.assertFalse(valid_position((True, 1, 1)))

    def test_protected_floor_and_added_blocks(self):
        blocks = generate_world()
        self.assertFalse(can_remove(blocks, (0, 0, 0)))
        self.assertFalse(can_remove(blocks, (1, 1, 1)))
        blocks[(1, 1, 1)] = 'stone'
        self.assertTrue(can_remove(blocks, (1, 1, 1)))

    def test_spawn_above_center(self):
        blocks = generate_world()
        blocks[(0, 4, 0)] = 'stone'
        self.assertEqual(spawn_position(blocks), (0, 6, 0))

    def test_inventory_invalid_slot_preserves_selection(self):
        inventory = Inventory()
        self.assertTrue(inventory.select_slot(2))
        previous = inventory.selected
        self.assertFalse(inventory.select_slot(99))
        self.assertEqual(inventory.selected, previous)

    def test_crystals_collected_only_once(self):
        quest = Objectives()
        for name, position in CRYSTALS.items():
            self.assertIn(name, quest.collect_near(position))
            self.assertEqual(quest.collect_near(position), [])
        self.assertIn('Quest complete', quest.status())

    def test_save_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.json'
            blocks = generate_world()
            blocks[(2, 1, 2)] = 'stone'
            save_world(blocks, {'corner'}, 'dirt', path)
            self.assertEqual(load_world(path), (blocks, {'corner'}, 'dirt'))
            self.assertFalse(path.with_suffix('.tmp').exists())

    def test_bad_save_rejected_and_valid_save_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.json'
            blocks = generate_world()
            save_world(blocks, set(), 'grass', path)
            original = path.read_text()
            with self.assertRaises(ValueError):
                save_world({(0, 0, 0): 'grass'}, set(), 'grass', path)
            self.assertEqual(path.read_text(), original)
            data = json.loads(original)
            for mutation in [lambda d: d.update(version=2),
                             lambda d: d['blocks'].append(d['blocks'][0]),
                             lambda d: d['blocks'][0].update(material='missing'),
                             lambda d: d.update(collected=['not-a-crystal'])]:
                copy = json.loads(original)
                mutation(copy)
                path.write_text(json.dumps(copy))
                with self.assertRaises(ValueError):
                    load_world(path)
            path.write_text('{bad json')
            with self.assertRaises(ValueError):
                load_world(path)

if __name__ == '__main__':
    unittest.main()
