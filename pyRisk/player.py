# player.py

class Player:
    def __init__(self, name, color, faction=None):
        if not name or not isinstance(name, str):
            raise ValueError("Invalid player name")
        if not isinstance(color, tuple) or len(color) != 3:
            raise ValueError("Invalid color format")
        self.name = name
        self.color = color
        self.faction = faction
        self.allies = []
        self.naps = []


    def add_ally(self, player):
        if player not in self.allies:
            self.allies.append(player)

    def add_nap(self, player):
        if player not in self.naps:
            self.naps.append(player)
