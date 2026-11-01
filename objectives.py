"""Quest team: stable IDs let collected items survive saving and loading."""
CRYSTALS = {'corner': (4, 1.3, 4), 'ridge': (-4, 1.3, 3), 'trail': (3, 1.3, -4)}

class Objectives:
    def __init__(self):
        self.collected = set()

    def collect_near(self, player):
        found = []
        for name, position in CRYSTALS.items():
            distance_squared = sum((a - b) ** 2 for a, b in zip(player, position))
            if name not in self.collected and distance_squared < 2.25:
                self.collected.add(name)
                found.append(name)
        return found

    def status(self):
        count = len(self.collected)
        return f'Crystals: {count}/{len(CRYSTALS)}' + (' - Quest complete!' if count == len(CRYSTALS) else '')
