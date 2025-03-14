# player.py

from pyRisk.research import ResearchManager, ResearchType

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

        # Initialize research manager
        self.research_manager = ResearchManager()

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

    # Research-related methods
    def has_research(self, research_type: ResearchType) -> bool:
        """Check if player has completed a specific research"""
        return self.research_manager.has_research(research_type)

    def complete_research(self, research_type: ResearchType):
        """Complete a research"""
        self.research_manager.complete_research(research_type)

    def get_completed_research(self) -> set[ResearchType]:
        """Get all completed research"""
        return self.research_manager.get_completed_research()