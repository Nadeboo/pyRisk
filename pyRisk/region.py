# region.py

from typing import Set, Dict, Tuple, Optional, List, Any
import json
import os

class Region:
    """
    Represents a region on the game map, consisting of multiple tiles.
    """
    def __init__(self, region_id: int, name: str = None):
        """
        Initialize a new region.
        
        Args:
            region_id: Unique identifier for the region
            name: Display name for the region (defaults to "Region {region_id}")
        """
        self.region_id = region_id
        self.name = name or f"Region {region_id}"
        self.tiles: Set[Tuple[int, int]] = set()  # Set of (x,y) coordinates in this region
        self.color = None  # Visual indicator color
        self.bonus_value = 1  # Default bonus for controlling the region
        self.properties: Dict[str, Any] = {}  # Additional region properties
        
    def add_tile(self, x: int, y: int) -> None:
        """Add a tile to this region"""
        self.tiles.add((x, y))
        
    def remove_tile(self, x: int, y: int) -> bool:
        """
        Remove a tile from this region.
        
        Returns:
            bool: True if the tile was in the region and was removed, False otherwise
        """
        if (x, y) in self.tiles:
            self.tiles.remove((x, y))
            return True
        return False
        
    def contains(self, x: int, y: int) -> bool:
        """Check if the region contains a specific tile"""
        return (x, y) in self.tiles
        
    def get_tile_count(self) -> int:
        """Get the number of tiles in this region"""
        return len(self.tiles)
        
    def check_control(self, tile_owners: Dict[Tuple[int, int], str]) -> Tuple[Optional[str], float]:
        """
        Check if a single player controls all tiles in this region.
        
        Args:
            tile_owners: Dictionary mapping (x,y) -> player_name
            
        Returns:
            Tuple[Optional[str], float]: (controlling_player, control_percentage)
            where controlling_player is None if no single player controls all tiles
        """
        if not self.tiles:
            return None, 0.0
            
        # Count tiles owned by each player
        player_counts: Dict[str, int] = {}
        total_tiles = len(self.tiles)
        owned_tiles = 0
        
        for x, y in self.tiles:
            owner = tile_owners.get((x, y))
            if owner:
                player_counts[owner] = player_counts.get(owner, 0) + 1
                owned_tiles += 1
        
        # Find player with most tiles
        if not player_counts:
            return None, 0.0
            
        dominant_player, count = max(player_counts.items(), key=lambda x: x[1])
        
        # Calculate control percentage
        control_percentage = (count / total_tiles) * 100
        
        # Check if dominant player owns all tiles
        if count == total_tiles:
            return dominant_player, 100.0
        else:
            return None, control_percentage
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert region to dictionary for serialization"""
        return {
            'id': self.region_id,
            'name': self.name,
            'tiles': list(self.tiles),
            'color': self.color,
            'bonus_value': self.bonus_value,
            'properties': self.properties
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Region':
        """Create a Region from a dictionary"""
        region = cls(data['id'], data['name'])
        region.tiles = set(tuple(tile) for tile in data['tiles'])
        region.color = data.get('color')
        region.bonus_value = data.get('bonus_value', 1)
        region.properties = data.get('properties', {})
        return region


class RegionManager:
    """
    Manages regions and provides utilities for region operations.
    """
    def __init__(self):
        self.regions: Dict[int, Region] = {}
        self.tile_to_region: Dict[Tuple[int, int], int] = {}
        
    def add_region(self, region: Region) -> None:
        """Add a region to the manager"""
        self.regions[region.region_id] = region
        # Update tile to region mapping
        for tile in region.tiles:
            self.tile_to_region[tile] = region.region_id
            
    def remove_region(self, region_id: int) -> bool:
        """
        Remove a region from the manager.
        
        Returns:
            bool: True if the region was found and removed, False otherwise
        """
        if region_id in self.regions:
            # Remove tile mappings
            for tile in self.regions[region_id].tiles:
                if tile in self.tile_to_region:
                    del self.tile_to_region[tile]
            # Remove region
            del self.regions[region_id]
            return True
        return False
        
    def get_region(self, region_id: int) -> Optional[Region]:
        """Get a region by ID"""
        return self.regions.get(region_id)
        
    def get_region_for_tile(self, x: int, y: int) -> Optional[Region]:
        """Get the region containing a specific tile"""
        region_id = self.tile_to_region.get((x, y))
        if region_id is not None:
            return self.regions.get(region_id)
        return None
        
    def check_all_regions_control(self, tile_owners: Dict[Tuple[int, int], str]) -> Dict[int, Dict[str, Any]]:
        """
        Check control status for all regions.
        
        Args:
            tile_owners: Dictionary mapping (x,y) -> player_name
            
        Returns:
            Dict[int, Dict[str, Any]]: Dictionary mapping region_id to control information
        """
        control_status = {}
        
        for region_id, region in self.regions.items():
            controller, percentage = region.check_control(tile_owners)
            control_status[region_id] = {
                'controller': controller,
                'percentage': percentage,
                'region_name': region.name,
                'tile_count': region.get_tile_count(),
                'bonus_value': region.bonus_value
            }
            
        return control_status
        
    def save_to_file(self, filename: str) -> bool:
        """
        Save regions to a JSON file.
        
        Args:
            filename: Path to save the regions data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                'regions': [region.to_dict() for region in self.regions.values()]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving regions: {e}")
            return False
            
    @classmethod
    def load_from_file(cls, filename: str) -> Optional['RegionManager']:
        """
        Load regions from a JSON file.
        
        Args:
            filename: Path to the regions data file
            
        Returns:
            RegionManager or None if loading failed
        """
        if not os.path.exists(filename):
            print(f"Regions file not found: {filename}")
            return None
            
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            manager = cls()
            for region_data in data.get('regions', []):
                region = Region.from_dict(region_data)
                manager.add_region(region)
                
            return manager
        except Exception as e:
            print(f"Error loading regions: {e}")
            return None 