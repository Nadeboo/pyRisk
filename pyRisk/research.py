# research.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Set, Optional

class ResearchTier(Enum):
    """Represents the different tiers of research available"""
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4
    TIER_5 = 5

    @property
    def display_name(self) -> str:
        return f"Tier {self.value}"

class ResearchType(Enum):
    """Represents all available research types"""
    # Tier 1
    FARMING = ("FARMING", "Farming", ResearchTier.TIER_1)
    HERDING = ("HERDING", "Herding", ResearchTier.TIER_1)
    FLETCHING = ("FLETCHING", "Fletching", ResearchTier.TIER_1)

    def __init__(self, code: str, display_name: str, tier: ResearchTier):
        self.code = code
        self.display_name = display_name
        self.tier = tier

    @classmethod
    def get_by_tier(cls, tier: ResearchTier) -> Set['ResearchType']:
        """Returns all research types in a given tier"""
        return {r_type for r_type in cls if r_type.tier == tier}

    @classmethod
    def get_by_code(cls, code: str) -> Optional['ResearchType']:
        """Returns a research type by its code, or None if not found"""
        try:
            return next(r_type for r_type in cls if r_type.code == code.upper())
        except StopIteration:
            return None

class ResearchManager:
    """Manages the research state for a player"""
    def __init__(self):
        self.completed_research: Set[ResearchType] = set()

    def has_research(self, research_type: ResearchType) -> bool:
        """Check if a player has completed a specific research"""
        return research_type in self.completed_research

    def complete_research(self, research_type: ResearchType) -> None:
        """Complete a research"""
        self.completed_research.add(research_type)

    def get_completed_research(self) -> Set[ResearchType]:
        """Get all completed research"""
        return self.completed_research.copy()