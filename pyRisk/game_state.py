# game_state.py

from typing import List, Dict, Any, Optional, Tuple

class GameState:
    def __init__(self, turn_number: int, map_image_path: str):
        self.turn_number = turn_number
        self.map_image_path = map_image_path
        self.unit_positions: List[Dict[str, Any]] = []  # Store unit data for this turn
        
    def save_unit_state(self, units):
        """Save the state of all units for this turn"""
        self.unit_positions = [
            {
                'owner': unit.owner,
                'unit_type': unit.unit_type.value,
                'unit_id': unit.unit_id,
                'position': unit.position
            }
            for unit in units
        ]
        
    def restore_unit_state(self, app):
        """Restore units to their positions for this turn"""
        # Keep track of existing units by ID
        unit_map = {unit.unit_id: unit for unit in app.units}
        
        for unit_data in self.unit_positions:
            unit_id = unit_data['unit_id']
            position = tuple(unit_data['position']) if unit_data['position'] else None
            
            # Update existing unit if it exists
            if unit_id in unit_map:
                unit_map[unit_id].position = position