# Class Block World - shared classroom starter v0.1

A small Python block-building game for a class to develop together with Claude.
Start with **docs/INSTRUCTOR.md**. Give students **docs/STUDENT_START.md** and one task card.
The master copy belongs to the instructor; students work in separate copies.

## Playable baseline

A 12 by 12 world, first-person movement, jump, building/removing blocks above a protected ground layer, three materials, a crystal hunt, pause, respawn, and validated JSON saving/loading. Creative inventory is unlimited. Worlds have fixed bounds and a height limit. This is a small single-player prototype: students collaborate on the code, not a multiplayer server.

## Install and run

Install Python **3.13** on each classroom machine for consistency (engine minimum is 3.12). Extract the ZIP first. Open a terminal in this folder. No Claude API key is needed.

Windows:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

macOS:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

If `python3.13` is unavailable, check `python3 --version`; use `python3` when it reports 3.13. The instructor's Mac already has the local environment installed. After installation, double-click `Play.command` on Mac or `Play.bat` on Windows, or use the final command above. macOS may require launching the script from Terminal on a newly downloaded copy.

Internet is needed for the initial package installation. The installed game runs locally. Browser-only Chromebooks/tablets cannot use these steps; test the actual student machines before class. Windows instructions are provided but have not been verified on a Windows machine.

## Controls

- WASD: move; mouse: look; Space: jump.
- Left click: remove an added block. Right click: place selected material.
- 1, 2, 3: select grass, dirt, or stone.
- F5: save. F9: load. On a Mac use Fn+F5 / Fn+F9 if function keys control system features.
- R: respawn above the center of the map. Falling off the map also respawns you.
- Escape: pause/release the mouse. Q while paused: quit.
- F5/F9 also work while paused. Closing the window does not automatically save.

Saved blocks, selected material, and collected crystals go in `saves/world.json`. Loading respawns the player safely at the center rather than restoring their exact location. Save files are personal and should not be submitted as source changes.

## Check the game

```sh
# Mac; use .venv\Scripts\python on Windows
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py --smoke-test
```

The smoke test opens a real game window, takes a screenshot under `artifacts/`, and exits. Use docs/TEST_CHECKLIST.md for playtesting.

## File ownership

| File | Owner |
| --- | --- |
| main.py, requirements.txt, tests/, shared contracts | Instructor |
| world.py | World team |
| blocks.py | Materials team |
| inventory.py, interface.py | Interface team |
| objectives.py | Quest team |
| save_load.py | Save team (later session) |

Start with up to four pairs; smaller classes combine teams. See docs/CONTRACTS.md before changing a shared function. `assets/` is reserved for student-created or licensed artwork; baseline visuals use engine primitives. Ursina is an external dependency: https://www.ursinaengine.org/ .

## Verified baseline

Tested on the instructor's Mac with Python 3.13.5: eight logic tests and a real-window integration check covering raycast placement/removal, selection, save/load, invalid saves, pause, and crystal collection. Run the latter with `.venv/bin/python tests/graphics_smoke.py`. A screenshot was visually reviewed.

Ursina emits startup shader/icon warnings on this Mac even after the in-memory compatibility fix; the rendered game and integration checks work. These warnings are from engine initialization. Windows and student machines still require a setup/play check before class.

Instructor release packaging: `python package_release.py v0.2` writes a fresh ZIP beside this folder and excludes environments, saves, and Git history.
