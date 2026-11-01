# Shared contracts - instructor-owned

- Coordinates are integer `(x, y, z)` tuples. Y points up. Cubes are centered on these positions, so the ground at y=0 has a top at y=0.5.
- World data is `{(x, y, z): material_id}`. x and z range from -6 to 5; y from 0 to 10. Keep all 144 y=0 blocks. Never put Ursina Entity objects into saved data.
- `generate_world()` returns a fresh dictionary. Terrain additions must obey the bounds and use known materials.
- `MATERIALS` maps stable IDs to `{'label': str, 'rgb': (r, g, b)}` with integer channels 0..255. Do not rename existing IDs. `material_ids()` returns the selection order. Limit selectable materials to nine for number-key controls.
- `can_place(blocks, position, material, player)` and `can_remove(blocks, position)` return booleans without modifying data. Player coordinates refer to feet. `spawn_position(blocks)` returns a safe center spawn.
- `Inventory.selected` is a material ID. `select_slot(number)` is one-based and returns a success boolean.
- `HUD.refresh(inventory, objectives)` redraws labels; `HUD.notify(message)` shows a status message. `HUD.pause` is an Entity with an enabled property. UI code never changes world data.
- `CRYSTALS` maps stable names to positions. Objectives exposes a `collected` set, `collect_near(player)` returning newly collected IDs, and `status()` returning text. Keep IDs stable so old saves work. Keep quests away from terrain structures; coordinate proposed positions before merging.
- `save_world(blocks, collected, selected, path=...)` writes version 1 JSON atomically. `load_world(path=...)` validates everything first and returns `(blocks, collected_set, selected)`. Errors raise ValueError or OSError; never partially mutate the active world.
- main.py owns rendering, movement, input dispatch, and integration. All teams send proposals here through the instructor.
