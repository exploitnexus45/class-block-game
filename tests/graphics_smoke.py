"""Optional real-window integration check: python tests/graphics_smoke.py."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main as game_module
from ursina import Ursina, camera, invoke, application, mouse
from objectives import CRYSTALS
from save_load import save_world, load_world

app = Ursina(development_mode=False, borderless=False)
game = game_module.Game()
mouse.locked = False
errors = []
temporary = tempfile.TemporaryDirectory()
save_path = Path(temporary.name) / 'test.json'
game_module.save_world = lambda blocks, collected, selected: save_world(blocks, collected, selected, save_path)
game_module.load_world = lambda: load_world(save_path)

def prepare():
    game.player.gravity = 0
    game.player.position = (0, 2, -3)
    game.player.rotation_y = 0
    game.player.camera_pivot.rotation_x = 55

def check():
    try:
        before = len(game.blocks)
        game.input('2')
        assert game.inventory.selected == 'dirt'
        game.input('right mouse down')
        assert len(game.blocks) == before + 1, 'Raycast placement failed'
        game.input('f5')
        assert save_path.exists()
        game.input('left mouse down')
        assert len(game.blocks) == before, 'Removal failed'
        game.input('f9')
        assert len(game.blocks) == before + 1, 'Load failed'
        save_path.write_text('bad json')
        game.input('f9')
        assert len(game.blocks) == before + 1, 'Bad load changed world'
        game.input('escape')
        assert game.paused and not game.player.enabled
        game.input('escape')
        assert not game.paused and game.player.enabled
        for position in CRYSTALS.values():
            game.player.position = position
            game.update()
        assert len(game.objectives.collected) == len(CRYSTALS)
        assert not game.crystals
        print('GRAPHICS INTEGRATION PASS: raycast build/remove, selection, save/load, invalid load, pause, crystals')
    except Exception as error:
        errors.append(error)
        print('GRAPHICS INTEGRATION FAILED:', repr(error))
    finally:
        application.quit()

invoke(prepare, delay=1)
invoke(check, delay=2)
app.run()
temporary.cleanup()
if errors:
    raise SystemExit(1)
