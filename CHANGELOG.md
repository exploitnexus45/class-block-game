# Changes

## v0.1

Shared classroom starter: fixed-size world, first-person controls, block building, three materials, crystal collection, pause/respawn, JSON save/load, tests, contracts, Claude rules, and task cards.

## Glocinshmeel io title screen

- `lobby/index.html`: the web game now opens on the Glocinshmeel io title screen (hills, playing dogs, miner dogs in the mine shaft, a bouncy red PLAY ball to catch, then a loading count to 1024!). After loading, the game starts. The page title is now "Glocinshmeel io".
- `title_screen.py`: the same title screen for the Python/Ursina game. Use `TitleScreen(on_loaded=start_the_game)`. Run `python title_screen.py` to see it on its own.
