# player.py

class Player:
    def __init__(self, name, color, faction=None):
        self.name = name
        self.color = color  # Tuple (R, G, B)
        self.faction = faction
        self.allies = []
        self.naps = []

    def add_ally(self, player):
        if player not in self.allies:
            self.allies.append(player)

    def add_nap(self, player):
        if player not in self.naps:
            self.naps.append(player)
