from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List, Set


class UnitType(Enum):
    INFANTRY = "Infantry"
    CAVALRY = "Cavalry"
    SPEARMEN = "Spearmen"
    
    @property
    def movement_speed(self) -> int:
        speeds = {
            UnitType.INFANTRY: 8,
            UnitType.CAVALRY: 12,
            UnitType.SPEARMEN: 6
        }
        return speeds.get(self, 0)
        
    @property
    def attack_dice(self) -> str:
        dice = {
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "1d8",
            UnitType.SPEARMEN: "1d3"
        }
        return dice.get(self, "")
    
    @property
    def special_properties(self) -> Set[str]:
        if self == UnitType.SPEARMEN:
            return {"phalanx"}
        return set()
    
    def get_attack_dice(self, special_properties: Set[str]) -> str:
        if self == UnitType.SPEARMEN and "phalanx" in special_properties:
            return "1d6"
        return self.attack_dice
    
    @property
    def casualty_dice(self) -> str:
        dice = {
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "2d4",
            UnitType.SPEARMEN: "1d4"
        }
        return dice.get(self, "")
    
    @property
    def wall_dice(self) -> str:
        dice = {
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "1d4",
            UnitType.SPEARMEN: "1d6"
        }
        return dice.get(self, "")
    
    @property
    def wall_bonus(self) -> int:
        bonuses = {
            UnitType.INFANTRY: 1,
            UnitType.CAVALRY: 0,
            UnitType.SPEARMEN: 2
        }
        return bonuses.get(self, 0)
        
    @property
    def shorthand(self) -> str:
        shorthands = {
            UnitType.INFANTRY: "INF",
            UnitType.CAVALRY: "CAV",
            UnitType.SPEARMEN: "SPR"
        }
        return shorthands.get(self, "")


@dataclass
class Unit:
    owner: str  # Player name
    unit_type: UnitType
    unit_id: int
    position: Optional[Tuple[int, int]] = None  # (x, y) coordinates on map
    sub_units: List['Unit'] = field(default_factory=list)  # List of units in this army
    special_properties: Set[str] = field(default_factory=set)  # Active special properties
    
    @property
    def is_army(self) -> bool:
        """Return True if this unit is actually an army (contains sub-units)"""
        return len(self.sub_units) > 0
    
    @property
    def available_special_properties(self) -> Set[str]:
        """Get all available special properties from sub-units"""
        if not self.is_army:
            return self.unit_type.special_properties
        properties = set()
        for unit in self.sub_units:
            properties.update(unit.unit_type.special_properties)
        return properties
    
    def _combine_dice(self, dice_str_list: List[str]) -> str:
        """Combine dice strings like ['1d4', '1d4', '1d8'] into a simplified format."""
        if not dice_str_list:
            return "0"
            
        dice_counts = {}
        for dice_str in dice_str_list:
            if not dice_str:
                continue
            count, die = dice_str.split('d')
            count = int(count)
            dice_counts[die] = dice_counts.get(die, 0) + count
        
        dice_strs = [f"{count}d{die}" for die, count in sorted(dice_counts.items())]
        return " + ".join(dice_strs) if dice_strs else "0"
    
    @property
    def attack_dice(self) -> str:
        if self.is_army:
            # Use special property modified attack dice for sub-units
            return self._combine_dice([
                unit.unit_type.get_attack_dice(self.special_properties) 
                for unit in self.sub_units
            ])
        return self.unit_type.get_attack_dice(self.special_properties)
    
    @property
    def casualty_dice(self) -> str:
        if self.is_army:
            return self._combine_dice([unit.unit_type.casualty_dice for unit in self.sub_units])
        return self.unit_type.casualty_dice
    
    @property
    def wall_dice(self) -> str:
        if self.is_army:
            return self._combine_dice([unit.unit_type.wall_dice for unit in self.sub_units])
        return self.unit_type.wall_dice
    
    @property
    def wall_bonus(self) -> int:
        if self.is_army:
            return sum(unit.unit_type.wall_bonus for unit in self.sub_units)
        return self.unit_type.wall_bonus
        
    @property
    def shorthand(self) -> str:
        if self.is_army:
            unit_counts = {}
            for unit in self.sub_units:
                unit_counts[unit.unit_type.shorthand] = unit_counts.get(unit.unit_type.shorthand, 0) + 1
            return '\n'.join(f"{count}{type}" for type, count in sorted(unit_counts.items()))
        return self.unit_type.shorthand
        
    @property
    def movement_speed(self) -> int:
        if self.is_army:
            if not self.sub_units:
                return 0
            return min(unit.unit_type.movement_speed for unit in self.sub_units)
        return self.unit_type.movement_speed