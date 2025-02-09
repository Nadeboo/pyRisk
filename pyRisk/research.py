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
    # Steel Path - Tier 1
    FARMING = ("FRM", "Farming", ResearchTier.TIER_1, "steel")
    HERDING = ("HRD", "Herding", ResearchTier.TIER_1, "steel")
    FLETCHING = ("FLT", "Fletching", ResearchTier.TIER_1, "steel")

    # Steel Path - Tier 2
    WRITING = ("WRT", "Writing", ResearchTier.TIER_2, "steel")
    WAYSTONES = ("WAY", "Waystones", ResearchTier.TIER_2, "steel")
    SAILING = ("SLG", "Sailing", ResearchTier.TIER_2, "steel")
    STONEWORKING = ("STO", "Stoneworking", ResearchTier.TIER_2, "steel")
    CITYBUILDING = ("CTY", "Citybuilding", ResearchTier.TIER_2, "steel")
    ORGANIZATION = ("ORG", "Organization", ResearchTier.TIER_2, "steel")

    # Steel Path - Tier 3
    SCHOOLING = ("SCH", "Schooling", ResearchTier.TIER_3, "steel")
    THEOLOGY = ("THO", "Theology", ResearchTier.TIER_3, "steel")
    ADV_SAILING = ("ADS", "Advanced Sailing", ResearchTier.TIER_3, "steel")
    IRONWORKING = ("IRW", "Ironworking", ResearchTier.TIER_3, "steel")
    ADV_FARMING = ("ADF", "Advanced Farming", ResearchTier.TIER_3, "steel")
    RIDING = ("RID", "Riding", ResearchTier.TIER_3, "steel")

    # Steel Path - Tier 4
    INSTITUTES = ("INS", "Institutes", ResearchTier.TIER_4, "steel")
    ORG_RELIGIONS = ("ORR", "Organized Religions", ResearchTier.TIER_4, "steel")
    TRADE = ("TRD", "Trade", ResearchTier.TIER_4, "steel")
    CANNONS = ("CNN", "Cannons", ResearchTier.TIER_4, "steel")
    MACHINING = ("MCH", "Machining", ResearchTier.TIER_4, "steel")
    HORSE_CARTS = ("HRC", "Horse-Carts", ResearchTier.TIER_4, "steel")

    # Steel Path - Tier 5
    STATE_EDUCATION = ("STE", "State Education", ResearchTier.TIER_5, "steel")
    STATE_CULTS = ("STC", "State Cults", ResearchTier.TIER_5, "steel")
    MERCANTILISM = ("MRC", "Mercantilism", ResearchTier.TIER_5, "steel")
    FORTIFICATIONS = ("FRT", "Fortifications", ResearchTier.TIER_5, "steel")
    FACTORIES = ("FAC", "Factories", ResearchTier.TIER_5, "steel")
    STANDING_ARMY = ("STA", "Standing Army", ResearchTier.TIER_5, "steel")
    MUSKETS = ("MUS", "Muskets", ResearchTier.TIER_5, "steel")

    # Magic Path - Tier 1
    HYDROMANCY = ("HYD", "Hydromancy", ResearchTier.TIER_1, "magic")
    PSYCHOMANCY = ("PSY", "Psychomancy", ResearchTier.TIER_1, "magic")
    PYROMANCY = ("PYR", "Pyromancy", ResearchTier.TIER_1, "magic")
    GEOMANCY = ("GEO", "Geomancy", ResearchTier.TIER_1, "magic")

    # Magic Path - Tier 2
    ADV_HYDROMANCY = ("AHD", "Advanced Hydromancy", ResearchTier.TIER_2, "magic")
    SPATIAL_THEORY = ("SPT", "Spatial Theory", ResearchTier.TIER_2, "magic")
    BURNING_WILL = ("BRN", "Burning Will", ResearchTier.TIER_2, "magic")
    ADV_PYROMANCY = ("APR", "Advanced Pyromancy", ResearchTier.TIER_2, "magic")
    HEMOMANCY = ("HEM", "Hemomancy", ResearchTier.TIER_2, "magic")
    ADV_GEOMANCY = ("AGO", "Advanced Geomancy", ResearchTier.TIER_2, "magic")

    # Magic Path - Tier 3
    WILL_OF_WATER = ("WOW", "Will of Water", ResearchTier.TIER_3, "magic")
    TEMPESTOMANCY = ("TMP", "Tempestomancy", ResearchTier.TIER_3, "magic")
    DISTORTION = ("DIS", "Distortion", ResearchTier.TIER_3, "magic")
    ANIMAL_SPIRIT = ("ANM", "Animal Spirit", ResearchTier.TIER_3, "magic")
    SIDEROMANCY = ("SID", "Sideromancy", ResearchTier.TIER_3, "magic")
    MEDITATION = ("MED", "Meditation", ResearchTier.TIER_3, "magic")
    ALCHEMY = ("ALC", "Alchemy", ResearchTier.TIER_3, "magic")
    GEOGENESIS = ("GGS", "Geogenesis", ResearchTier.TIER_3, "magic")

    # Magic Path - Tier 4
    CRYOMANCY = ("CRY", "Cryomancy", ResearchTier.TIER_4, "magic")
    TELEPORTATION = ("TLP", "Teleportation", ResearchTier.TIER_4, "magic")
    GRAVITURGY = ("GRA", "Graviturgy", ResearchTier.TIER_4, "magic")
    WOODVOICE = ("WDW", "Woodvoice", ResearchTier.TIER_4, "magic")
    ADV_PERSUASION = ("APS", "Advanced Persuasion", ResearchTier.TIER_4, "magic")
    OSTEOMANCY = ("OST", "Osteomancy", ResearchTier.TIER_4, "magic")
    ADV_ALCHEMY = ("AAC", "Advanced Alchemy", ResearchTier.TIER_4, "magic")

    # Magic Path - Tier 5
    CRYOGENESIS = ("CRG", "Cryogenesis", ResearchTier.TIER_5, "magic")
    ADV_TELEPORT = ("ADT", "Advanced Teleport", ResearchTier.TIER_5, "magic")
    BIRDFORM = ("BRD", "Birdform", ResearchTier.TIER_5, "magic")
    GAIAS_TOUCH = ("GAI", "Gaia's Touch", ResearchTier.TIER_5, "magic")
    NECROMANCY = ("NEC", "Necromancy", ResearchTier.TIER_5, "magic")
    SOUL_HARNESSING = ("SOL", "Soul Harnessing", ResearchTier.TIER_5, "magic")
    VIMANA = ("VIM", "Vimana", ResearchTier.TIER_5, "magic")
    TERRAGENESIS = ("TRG", "Terragenesis", ResearchTier.TIER_5, "magic")

    def __init__(self, code: str, display_name: str, tier: ResearchTier, path: str):
        self.code = code
        self.display_name = display_name
        self.tier = tier
        self.path = path  # 'steel' or 'magic'

    @classmethod
    def get_by_tier(cls, tier: ResearchTier) -> Set['ResearchType']:
        """Returns all research types in a given tier"""
        return {r_type for r_type in cls if r_type.tier == tier}

    @classmethod
    def get_by_path(cls, path: str) -> Set['ResearchType']:
        """Returns all research types in a given path"""
        return {r_type for r_type in cls if r_type.path == path}

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