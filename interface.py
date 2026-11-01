"""Interface team. Game logic stays in the other modules."""
from ursina import Text, Entity, camera, color
from blocks import MATERIALS, material_ids

class HUD:
    def __init__(self):
        self.panel = Entity(parent=camera.ui, model='quad', color=color.rgba32(20, 36, 31, 220),
                            position=(-.40, .35), scale=(.72, .30), z=.1)
        self.bar = Entity(parent=camera.ui, model='quad', color=color.rgba32(20, 36, 31, 220),
                          position=(0, -.39), scale=(1.50, .16), z=.1)
        self.title = Text('CLASS BLOCK WORLD  /  v0.1', parent=camera.ui, position=(-.72, .46), scale=.95)
        self.controls = Text('WASD move | Mouse look | Space jump\nLeft click break | Right click build\n1-3 material | F5 save | F9 load\nR respawn | Esc pause | Q quit while paused',
                             parent=camera.ui, position=(-.72, .40), scale=.8)
        self.quest = Text('', parent=camera.ui, position=(-.72, .27), scale=1)
        self.hotbar = Text('', parent=camera.ui, origin=(0, 0), position=(0, -.43), scale=.95)
        self.message = Text('', parent=camera.ui, origin=(0, 0), position=(0, -.34), scale=.75)
        self.pause = Text('PAUSED\nEsc to continue\nQ to quit (save with F5 first)', parent=camera.ui,
                          origin=(0, 0), scale=1.5, background=True, enabled=False)

    def refresh(self, inventory, objectives):
        self.quest.text = objectives.status()
        self.hotbar.text = '   '.join(f'{i}. {MATERIALS[m]["label"]}' + (' *' if m == inventory.selected else '')
                                      for i, m in enumerate(material_ids(), 1))

    def notify(self, message):
        self.message.text = message
