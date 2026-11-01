"""Creative inventory: unlimited blocks; number keys choose a material."""
from blocks import material_ids

class Inventory:
    def __init__(self):
        self.selected = material_ids()[0]

    def select_slot(self, number):
        choices = material_ids()
        if 1 <= number <= len(choices):
            self.selected = choices[number - 1]
            return True
        return False
