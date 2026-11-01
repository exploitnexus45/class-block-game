"""Instructor-owned assembly. Run with: python main.py"""
from pathlib import Path
import argparse
import sys
from ursina import Ursina, Entity, Sky, color, camera, mouse, raycast, destroy, application, window, invoke
from ursina.prefabs.first_person_controller import FirstPersonController

# macOS uses a legacy OpenGL context. Adapt the engine's simple shaders in memory
# to GLSL 120; never modify installed dependency files.
if sys.platform == 'darwin':
    from ursina.shaders.unlit_shader import unlit_shader
    from ursina.shaders.unlit_with_fog_shader import unlit_with_fog_shader
    from ursina.shaders.text_shader import text_shader
    import re
    from ursina.shader import imported_shaders
    for shader in set(imported_shaders.values()) | {unlit_shader, unlit_with_fog_shader, text_shader}:
        shader.vertex = re.sub(r'#version \d+', '#version 120', shader.vertex)
        shader.vertex = re.sub(r'^in ', 'attribute ', shader.vertex, flags=re.M)
        shader.vertex = re.sub(r'^out ', 'varying ', shader.vertex, flags=re.M)
        shader.fragment = re.sub(r'#version \d+', '#version 120', shader.fragment)
        shader.fragment = re.sub(r'^in ', 'varying ', shader.fragment, flags=re.M)
        outputs = re.findall(r'out vec4 (\w+);', shader.fragment)
        shader.fragment = re.sub(r'out vec4 \w+;', '', shader.fragment)
        for output in outputs:
            shader.fragment = re.sub(r'\b' + output + r'\b', 'gl_FragColor', shader.fragment)
        shader.fragment = shader.fragment.replace('texture(', 'texture2D(')
        shader.compiled = False

from blocks import MATERIALS
from world import generate_world, can_place, can_remove, spawn_position
from inventory import Inventory
from objectives import Objectives, CRYSTALS
from interface import HUD
from save_load import save_world, load_world

class Game(Entity):
    def __init__(self):
        super().__init__()
        self.blocks = generate_world()
        self.block_root = Entity()
        self.views = {}
        self.crystals = {}
        self.inventory = Inventory()
        self.objectives = Objectives()
        self.paused = False
        self.rebuild()
        self.player = FirstPersonController(position=spawn_position(self.blocks), speed=5)
        self.player.cursor.color = color.white
        self.hud = HUD()
        self.hud.refresh(self.inventory, self.objectives)
        self.hud.notify('Find three crystals and build a shelter. The ground layer is protected.')
        Sky()

    def add_view(self, position, material):
        self.views[position] = Entity(parent=self.block_root, model='cube', texture='white_cube',
            position=position, color=color.rgb32(*MATERIALS[material]['rgb']), collider='box')

    def rebuild(self):
        for entity in list(self.views.values()) + list(self.crystals.values()):
            destroy(entity)
        self.views.clear()
        self.crystals.clear()
        for position, material in self.blocks.items():
            self.add_view(position, material)
        for name, position in CRYSTALS.items():
            if name not in self.objectives.collected:
                self.crystals[name] = Entity(model='cube', texture='white_cube', position=position, scale=.35,
                    rotation=(35, 45, 0), color=color.cyan)

    def respawn(self):
        self.player.position = spawn_position(self.blocks)
        self.player.air_time = 0

    def input(self, key):
        if key == 'escape':
            self.paused = not self.paused
            self.player.enabled = not self.paused
            mouse.locked = not self.paused
            self.hud.pause.enabled = self.paused
            return
        if key == 'q' and self.paused:
            application.quit()
        if key == 'f5':
            try:
                save_world(self.blocks, self.objectives.collected, self.inventory.selected)
                self.hud.notify('Saved to saves/world.json')
            except (OSError, ValueError) as error:
                self.hud.notify(f'Could not save: {error}')
        if key == 'f9':
            try:
                blocks, collected, selected = load_world()
                self.blocks = blocks
                self.objectives.collected = collected
                self.inventory.selected = selected
                self.rebuild()
                self.respawn()
                self.hud.refresh(self.inventory, self.objectives)
                self.hud.notify('Loaded world and quest progress. Returned to the center.')
            except (OSError, ValueError) as error:
                self.hud.notify(f'Could not load; your current world is unchanged. {error}')
        if self.paused:
            return
        if key == 'r':
            self.respawn()
        if key in '123456789' and len(key) == 1:
            self.inventory.select_slot(int(key))
            self.hud.refresh(self.inventory, self.objectives)
        if key not in ('left mouse down', 'right mouse down'):
            return
        hit = raycast(camera.world_position, camera.forward, distance=6, traverse_target=self.block_root)
        if not hit.hit:
            return
        position = tuple(round(v) for v in hit.entity.position)
        if key == 'left mouse down':
            if can_remove(self.blocks, position):
                del self.blocks[position]
                destroy(self.views.pop(position))
            else:
                self.hud.notify('The ground layer stays in place. Build above it.')
        else:
            target = tuple(round(a + b) for a, b in zip(position, hit.normal))
            if can_place(self.blocks, target, self.inventory.selected, tuple(self.player.position)):
                self.blocks[target] = self.inventory.selected
                self.add_view(target, self.inventory.selected)
            else:
                self.hud.notify('Choose an empty space inside the map and away from your body.')

    def update(self):
        if self.paused:
            return
        if self.player.y < -12:
            self.respawn()
        found = self.objectives.collect_near(tuple(self.player.position))
        for name in found:
            destroy(self.crystals.pop(name))
        if found:
            self.hud.refresh(self.inventory, self.objectives)
            self.hud.notify('Crystal collected! ' + self.objectives.status())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', action='store_true', help='Render a screenshot and exit after a few seconds.')
    args = parser.parse_args()
    app = Ursina(title='Class Block World', borderless=False, fullscreen=False, development_mode=False)
    window.size = (1100, 720)
    window.color = color.rgb32(154, 196, 219)
    # Refresh pre-created engine entities after the macOS shader adaptation.
    if sys.platform == 'darwin':
        from ursina import scene
        for entity in scene.entities:
            if entity.shader in (unlit_shader, unlit_with_fog_shader, text_shader):
                entity.shader = entity.shader
    game = Game()
    if args.smoke_test:
        mouse.locked = False
        game.player.rotation_y = 40
        game.player.camera_pivot.rotation_x = 25
        output = Path(__file__).resolve().parent / 'artifacts'
        output.mkdir(exist_ok=True)
        invoke(lambda: app.screenshot(namePrefix=str(output / 'smoke.png'), defaultFilename=False), delay=6)
        invoke(application.quit, delay=7)
    app.run()

if __name__ == '__main__':
    main()
