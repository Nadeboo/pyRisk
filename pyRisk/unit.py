# unit.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class UnitType(Enum):
    INFANTRY = "Infantry"
    
    @property
    def attack_dice(self) -> str:
        if self == UnitType.INFANTRY:
            return "1d4"
        return ""
    
    @property
    def casualty_dice(self) -> str:
        if self == UnitType.INFANTRY:
            return "1d4"
        return ""
    
    @property
    def wall_dice(self) -> str:
        if self == UnitType.INFANTRY:
            return "1d4"
        return ""
    
    @property
    def wall_bonus(self) -> int:
        if self == UnitType.INFANTRY:
            return 1
        return 0
        
    @property
    def shorthand(self) -> str:
        if self == UnitType.INFANTRY:
            return "INF"
        return ""


@dataclass
class Unit:
    owner: str  # Player name
    unit_type: UnitType
    unit_id: int
    position: Optional[Tuple[int, int]] = None  # (x, y) coordinates on map
    
    @property
    def attack_dice(self) -> str:
        return self.unit_type.attack_dice
    
    @property
    def casualty_dice(self) -> str:
        return self.unit_type.casualty_dice
    
    @property
    def wall_dice(self) -> str:
        return self.unit_type.wall_dice
    
    @property
    def wall_bonus(self) -> int:
        return self.unit_type.wall_bonus
        
    @property
    def shorthand(self) -> str:
        return self.unit_type.shorthand