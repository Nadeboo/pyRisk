from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List, Set, Dict, Any
import math

# Default maximum number of units in an army
DEFAULT_MAX_ARMY_SIZE = 12


class UnitClass(Enum):
    """Classification of unit types"""
    LAND = "Land"
    NAVAL = "Naval"


class UnitType(Enum):
    # Land units
    INFANTRY = "Infantry"
    CAVALRY = "Cavalry"
    SPEARMEN = "Spearmen"
    TREANT = "Treant"
    GRYPHON = "Gryphon"
    ARTILLERY = "Artillery"
    MOUNTAIN_GIANT = "Mountain Giant"
    GRAVELORD = "Gravelord"
    
    # Naval units
    GALLEY = "Galley"
    GALLEON = "Galleon"
    CARAVEL = "Caravel"
    
    @property
    def unit_class(self) -> UnitClass:
        """Get the class of this unit (Land or Naval)"""
        naval_units = {UnitType.GALLEY, UnitType.GALLEON, UnitType.CARAVEL}
        return UnitClass.NAVAL if self in naval_units else UnitClass.LAND
    
    @property
    def movement_speed(self) -> int:
        speeds = {
            # Land units
            UnitType.INFANTRY: 8,
            UnitType.CAVALRY: 12,
            UnitType.SPEARMEN: 6,
            UnitType.TREANT: 8,  # Same as Infantry when not rooted
            UnitType.GRYPHON: 12,  # Same as Cavalry
            UnitType.ARTILLERY: 8,  # Same as Infantry
            UnitType.MOUNTAIN_GIANT: 6,  # Slower than Infantry
            UnitType.GRAVELORD: 8,  # Standard speed
            
            # Naval units
            UnitType.GALLEY: 4,
            UnitType.GALLEON: 3,
            UnitType.CARAVEL: 5
        }
        return speeds.get(self, 0)
        
    @property
    def attack_dice(self) -> str:
        dice = {
            # Land units
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "1d8",
            UnitType.SPEARMEN: "1d3",
            UnitType.TREANT: "1d4",  # Same as Infantry when not rooted
            UnitType.GRYPHON: "1d8",  # Same as Cavalry
            UnitType.ARTILLERY: "2d4",  # Base artillery attack
            UnitType.MOUNTAIN_GIANT: "12d8",  # Powerful attack
            UnitType.GRAVELORD: "1d4",  # Default value, will be overridden
            
            # Naval units
            UnitType.GALLEY: "1d8",
            UnitType.GALLEON: "2d8",
            UnitType.CARAVEL: "1d6"
        }
        return dice.get(self, "")
    
    @property
    def special_properties(self) -> Set[str]:
        if self == UnitType.SPEARMEN:
            return {"phalanx"}
        elif self == UnitType.TREANT:
            return {"rooted"}
        elif self == UnitType.GRYPHON:
            return {"attacking"}
        elif self.unit_class == UnitClass.NAVAL:
            return {"naval"}
        return set()
    
    def get_attack_dice(self, special_properties: Set[str], custom_params: Dict[str, Any] = None) -> str:
        if self == UnitType.SPEARMEN and "phalanx" in special_properties:
            return "1d6"
        elif self == UnitType.TREANT and "rooted" in special_properties:
            return "1d4+2"  # Enhanced attack when rooted
        elif self == UnitType.GRYPHON and "attacking" in special_properties:
            return "1d8+2"  # Enhanced attack when attacking
        elif self == UnitType.GRAVELORD and custom_params and "dice_count" in custom_params:
            return f"{custom_params['dice_count']}d4"  # Custom dice count for Gravelord
        return self.attack_dice
    
    def get_casualty_dice(self, custom_params: Dict[str, Any] = None) -> str:
        dice = {
            # Land units
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "2d4",
            UnitType.SPEARMEN: "1d4",
            UnitType.TREANT: "1d4",  # Same as Infantry
            UnitType.GRYPHON: "2d4",  # Same as Cavalry
            UnitType.ARTILLERY: "1d6",  # Artillery casualty dice
            UnitType.MOUNTAIN_GIANT: "8d6",  # High casualty production
            UnitType.GRAVELORD: "1d4",  # Default value, will be overridden
            
            # Naval units
            UnitType.GALLEY: "1d4",
            UnitType.GALLEON: "2d4",
            UnitType.CARAVEL: "1d4"
        }
        
        if self == UnitType.GRAVELORD and custom_params and "dice_count" in custom_params:
            return f"{custom_params['dice_count']}d4"  # Custom dice count for Gravelord
        return dice.get(self, "")
    
    def get_wall_dice(self, custom_params: Dict[str, Any] = None) -> str:
        # Naval units don't have wall dice
        if self.unit_class == UnitClass.NAVAL:
            return "0"  # Naval units can't attack walls
            
        dice = {
            UnitType.INFANTRY: "1d4",
            UnitType.CAVALRY: "1d4",
            UnitType.SPEARMEN: "1d6",
            UnitType.TREANT: "1d4",  # Same as Infantry
            UnitType.GRYPHON: "1d4",  # Same as Cavalry
            UnitType.ARTILLERY: "2d8",  # Artillery wall dice
            UnitType.MOUNTAIN_GIANT: "16d8",  # Extremely effective against walls
            UnitType.GRAVELORD: "1d8"  # Default value, will be overridden
        }
        
        if self == UnitType.GRAVELORD and custom_params and "dice_count" in custom_params:
            return f"{custom_params['dice_count']}d8"  # Custom dice count for Gravelord
        return dice.get(self, "")
    
    @property
    def casualty_dice(self) -> str:
        return self.get_casualty_dice()
    
    @property
    def wall_dice(self) -> str:
        return self.get_wall_dice()
    
    @property
    def wall_bonus(self) -> int:
        # Naval units don't have wall bonus
        if self.unit_class == UnitClass.NAVAL:
            return 0
            
        bonuses = {
            UnitType.INFANTRY: 1,
            UnitType.CAVALRY: 0,
            UnitType.SPEARMEN: 2,
            UnitType.TREANT: 1,  # Same as Infantry
            UnitType.GRYPHON: 0,  # Same as Cavalry
            UnitType.ARTILLERY: 1,  # Artillery wall bonus
            UnitType.MOUNTAIN_GIANT: 1,  # Standard wall bonus
            UnitType.GRAVELORD: 0  # No wall bonus
        }
        return bonuses.get(self, 0)
    
    @property
    def carrying_capacity(self) -> int:
        """Get the carrying capacity for naval units"""
        capacities = {
            UnitType.GALLEY: 6,
            UnitType.GALLEON: 12,
            UnitType.CARAVEL: 4
        }
        return capacities.get(self, 0)
        
    @property
    def shorthand(self) -> str:
        shorthands = {
            # Land units
            UnitType.INFANTRY: "INF",
            UnitType.CAVALRY: "CAV",
            UnitType.SPEARMEN: "SPR",
            UnitType.TREANT: "TRE",
            UnitType.GRYPHON: "GRY",
            UnitType.ARTILLERY: "ART",
            UnitType.MOUNTAIN_GIANT: "MGT",
            UnitType.GRAVELORD: "GRL",
            
            # Naval units
            UnitType.GALLEY: "GAL",
            UnitType.GALLEON: "GLN",
            UnitType.CARAVEL: "CRV"
        }
        return shorthands.get(self, "")
    
    def get_slots_used(self, custom_params: Dict[str, Any] = None) -> int:
        """Get the number of army slots this unit type uses.
        
        Args:
            custom_params: Custom parameters for special units
            
        Returns:
            Number of slots used in an army
        """
        # Gravelords use X/2 slots (rounded up)
        if self == UnitType.GRAVELORD and custom_params and "dice_count" in custom_params:
            return math.ceil(custom_params["dice_count"] / 2)
        # All other units use 1 slot
        return 1


@dataclass
class Unit:
    owner: str  # Player name
    unit_type: UnitType
    unit_id: int
    position: Optional[Tuple[int, int]] = None  # (x, y) coordinates on map
    sub_units: List['Unit'] = field(default_factory=list)  # List of units in this army
    special_properties: Set[str] = field(default_factory=set)  # Active special properties
    custom_params: Dict[str, Any] = field(default_factory=dict)  # Custom parameters for special units
    max_army_size: int = DEFAULT_MAX_ARMY_SIZE  # Maximum number of units in this army
    
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
    def current_army_size(self) -> int:
        """Calculate the current size of the army based on slot usage of contained units.
        
        Returns:
            Current size of the army in slots
        """
        if not self.is_army:
            return 0
            
        return sum(unit.unit_type.get_slots_used(unit.custom_params) for unit in self.sub_units)
    
    @property
    def remaining_army_capacity(self) -> int:
        """Calculate the remaining capacity of the army.
        
        Returns:
            Number of slots remaining
        """
        return self.max_army_size - self.current_army_size
    
    def can_add_unit(self, unit_type: UnitType, custom_params: Dict[str, Any] = None) -> bool:
        """Check if a unit can be added to this army based on size limits.
        
        Args:
            unit_type: The type of unit to check
            custom_params: Any custom parameters for the unit
            
        Returns:
            True if the unit can be added, False otherwise
        """
        slots_needed = unit_type.get_slots_used(custom_params)
        return self.remaining_army_capacity >= slots_needed
    
    def can_merge_army(self, other_army: 'Unit') -> bool:
        """Check if another army can be merged into this one based on size limits.
        
        Args:
            other_army: The army to merge into this one
            
        Returns:
            True if the armies can be merged, False otherwise
        """
        return self.remaining_army_capacity >= other_army.current_army_size
    
    @property
    def is_naval_army(self) -> bool:
        """Return True if this army contains any naval units"""
        if not self.is_army:
            return self.unit_type.unit_class == UnitClass.NAVAL
            
        return any(unit.unit_type.unit_class == UnitClass.NAVAL for unit in self.sub_units)
    
    @property
    def total_carrying_capacity(self) -> int:
        """Calculate the total carrying capacity of naval units in this army"""
        if not self.is_army:
            return self.unit_type.carrying_capacity if self.unit_type.unit_class == UnitClass.NAVAL else 0
            
        return sum(unit.unit_type.carrying_capacity for unit in self.sub_units 
                  if unit.unit_type.unit_class == UnitClass.NAVAL)
    
    @property
    def attack_dice(self) -> str:
        if self.is_army:
            # Check if this is a mixed army with naval units
            has_naval = self.is_naval_army
            
            # If naval units are present, only naval units contribute to attack dice
            if has_naval:
                # Filter for naval units only
                naval_units = [unit for unit in self.sub_units 
                              if unit.unit_type.unit_class == UnitClass.NAVAL]
                
                # Return attack dice for naval units only
                return self._combine_dice([
                    unit.unit_type.get_attack_dice(unit.special_properties, unit.custom_params) 
                    for unit in naval_units
                ])
                
            # For land-only armies, proceed with normal logic
            artillery_count = sum(1 for unit in self.sub_units if unit.unit_type == UnitType.ARTILLERY)
            total_units = len(self.sub_units)
            
            # If less than half of the army is artillery, increase artillery attack dice
            if artillery_count > 0 and artillery_count < total_units / 2:
                # Use special property modified attack dice for sub-units
                dice_list = []
                for unit in self.sub_units:
                    if unit.unit_type == UnitType.ARTILLERY:
                        dice_list.append("3d4")  # Increased artillery attack
                    else:
                        dice_list.append(unit.unit_type.get_attack_dice(unit.special_properties, unit.custom_params))
                return self._combine_dice(dice_list)
            else:
                # Normal attack dice combination
                return self._combine_dice([
                    unit.unit_type.get_attack_dice(unit.special_properties, unit.custom_params) 
                    for unit in self.sub_units
                ])
        return self.unit_type.get_attack_dice(self.special_properties, self.custom_params)
    
    @property
    def casualty_dice(self) -> str:
        if self.is_army:
            # Check if this is a mixed army with naval units
            has_naval = self.is_naval_army
            
            # If naval units are present, only naval units contribute to casualty dice
            if has_naval:
                # Filter for naval units only
                naval_units = [unit for unit in self.sub_units 
                              if unit.unit_type.unit_class == UnitClass.NAVAL]
                
                # Return casualty dice for naval units only
                return self._combine_dice([
                    unit.unit_type.get_casualty_dice(unit.custom_params) 
                    for unit in naval_units
                ])
            
            # Normal casualty dice combination for land armies
            return self._combine_dice([
                unit.unit_type.get_casualty_dice(unit.custom_params) 
                for unit in self.sub_units
            ])
        return self.unit_type.get_casualty_dice(self.custom_params)
    
    @property
    def wall_dice(self) -> str:
        if self.is_army:
            # Naval units can't attack walls
            if self.is_naval_army:
                # Check if army has any land units that can attack walls
                land_units = [unit for unit in self.sub_units 
                             if unit.unit_type.unit_class == UnitClass.LAND]
                
                if not land_units:
                    return "0"  # Pure naval force can't attack walls
                
                # Only land units contribute to wall attacks
                return self._combine_dice([
                    unit.unit_type.get_wall_dice(unit.custom_params) 
                    for unit in land_units
                ])
            
            # Normal wall dice combination for land armies
            return self._combine_dice([
                unit.unit_type.get_wall_dice(unit.custom_params) 
                for unit in self.sub_units
            ])
        return self.unit_type.get_wall_dice(self.custom_params)
    
    @property
    def wall_bonus(self) -> int:
        if self.is_army:
            # Naval units don't contribute to wall bonus
            if self.is_naval_army:
                # Check if army has any land units that can provide wall bonus
                land_units = [unit for unit in self.sub_units 
                             if unit.unit_type.unit_class == UnitClass.LAND]
                
                if not land_units:
                    return 0  # Pure naval force has no wall bonus
                
                # Only land units contribute to wall bonus
                return sum(unit.unit_type.wall_bonus for unit in land_units)
            
            # Normal wall bonus calculation for land armies
            return sum(unit.unit_type.wall_bonus for unit in self.sub_units)
        return self.unit_type.wall_bonus
        
    @property
    def shorthand(self) -> str:
        if self.is_army:
            # Group by unit type
            unit_counts = {}
            for unit in self.sub_units:
                unit_counts[unit.unit_type.shorthand] = unit_counts.get(unit.unit_type.shorthand, 0) + 1
            
            # If this is a naval army, add carrying capacity
            if self.is_naval_army:
                shorthand_str = '\n'.join(f"{count}{type}" for type, count in sorted(unit_counts.items()))
                return f"{shorthand_str}\nCapacity: {self.total_carrying_capacity}"
            else:
                return '\n'.join(f"{count}{type}" for type, count in sorted(unit_counts.items()))
        
        # For individual naval units, show carrying capacity
        if self.unit_type.unit_class == UnitClass.NAVAL:
            return f"{self.unit_type.shorthand} (Cap:{self.unit_type.carrying_capacity})"
        
        return self.unit_type.shorthand
        
    @property
    def movement_speed(self) -> int:
        if self.is_army:
            if not self.sub_units:
                return 0
                
            # Calculate movement speed considering different unit classes
            naval_units = [unit for unit in self.sub_units if unit.unit_type.unit_class == UnitClass.NAVAL]
            land_units = [unit for unit in self.sub_units if unit.unit_type.unit_class == UnitClass.LAND]
            
            # Mixed armies take the slower of land vs naval movement
            if naval_units and land_units:
                # Calculate each group's minimum speed
                naval_speed = min(unit.unit_type.movement_speed for unit in naval_units)
                
                # Check for rooted Treants in land units
                if any(unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties 
                       for unit in land_units):
                    land_speed = 0  # Rooted Treant prevents movement
                else:
                    land_speed = min(unit.unit_type.movement_speed for unit in land_units)
                
                # Movement speed is the minimum of the two groups
                return min(naval_speed, land_speed)
                
            # Pure naval army
            elif naval_units:
                return min(unit.unit_type.movement_speed for unit in naval_units)
                
            # Pure land army - check for rooted Treants
            elif land_units:
                # Check if any Treant is rooted
                if any(unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties 
                       for unit in land_units):
                    return 0  # Rooted Treant prevents movement
                    
                return min(unit.unit_type.movement_speed for unit in land_units)
                
            return 0  # Empty army
        
        # For individual units
        if self.unit_type == UnitType.TREANT and "rooted" in self.special_properties:
            return 0  # Rooted Treants can't move
        return self.unit_type.movement_speed
        
    @staticmethod
    def merge_armies(source_army: 'Unit', target_army: 'Unit') -> bool:
        """Merge source_army into target_army if size limits allow.
        
        Args:
            source_army: The army to merge from (will be removed after merging)
            target_army: The army to merge into (will contain all units after merging)
            
        Returns:
            True if the armies were successfully merged, False otherwise
        """
        # Both must be armies (have sub-units)
        if not source_army.is_army or not target_army.is_army:
            return False
            
        # Both must have the same owner
        if source_army.owner != target_army.owner:
            return False
            
        # Check if target army has capacity for all units in source army
        if not target_army.can_merge_army(source_army):
            # Not enough capacity
            return False
            
        # Move all units from source to target
        for unit in source_army.sub_units:
            unit.position = target_army.position
            target_army.sub_units.append(unit)
            
        # Clear the source army's sub-units
        source_army.sub_units.clear()
        
        return True