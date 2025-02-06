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

        # Resource counters
        self.gold = 0
        self.research = 0
        self.mana = 0
        self.influence = 0
        
        # Per-turn increases
        self.gold_per_turn = 0
        self.research_per_turn = 0
        self.mana_per_turn = 0
        self.influence_per_turn = 0

    def add_ally(self, player):
        if player not in self.allies:
            self.allies.append(player)

    def add_nap(self, player):
        if player not in self.naps:
            self.naps.append(player)

    def apply_turn_increases(self):
        """Apply all per-turn resource increases"""
        self.gold += self.gold_per_turn
        self.research += self.research_per_turn
        self.mana += self.mana_per_turn
        self.influence += self.influence_per_turn