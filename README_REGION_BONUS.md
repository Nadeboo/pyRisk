# Region Bonus Feature Documentation

## Overview
The Region Bonus feature allows players to receive additional resources based on the number of regions they control. This bonus is applied to the player's influence generation per turn, providing strategic incentives for controlling multiple regions.

## Implementation Details

### Player Class Modifications
The `Player` class has been extended to include:
- A `region_bonus` attribute to store the number of bonus points
- Logic in the resource calculation to apply the bonus to influence generation
- Resource source tracking to display the bonus in tooltips

### Resource Calculation
The region bonus is applied during the `update_player_resources` method:
- Each region bonus point adds +1 to the player's influence per turn
- The bonus is tracked separately from base influence generation
- The source of the bonus is displayed in resource tooltips as "Region Bonus"

### Save/Load Integration
The region bonus is properly saved and loaded with the game state:
- When saving a game, the region bonus is stored in the player data
- When loading a game, the region bonus is restored from the saved data
- The `SaveLoadManager` class handles all save/load operations

## Testing
A comprehensive test script (`test_save_load_verification.py`) has been created to verify:
- Region bonus values are correctly saved to the game file
- Region bonus values are correctly loaded from the game file
- Resource calculations properly include the region bonus
- Resource tooltips correctly display the region bonus contribution

## Usage
1. Assign region bonus points to players based on the number of regions they control
2. The bonus will automatically be applied to influence generation
3. Players can see the bonus contribution in resource tooltips
4. The bonus persists when saving and loading the game

## Example
```python
# Assign region bonus
player.region_bonus = 3  # Player controls 3 regions

# Update resources (called automatically each turn)
app.update_player_resources()

# Player will receive +3 influence per turn from region bonus
```

## Integration with Save/Load System
The save/load system has been refactored to use the `SaveLoadManager` class, which:
- Centralizes all save/load logic
- Ensures consistent handling of game state
- Properly preserves all player attributes including region bonuses
- Provides error handling and validation

### Save Process
```python
# In pyRisk.py
def save_game(self):
    SaveLoadManager.save_game(self)
```

### Load Process
```python
# In pyRisk.py
def load_game(self):
    SaveLoadManager.load_game(self)
```

## Future Enhancements
Potential future enhancements for the region bonus feature:
- Different bonus types based on region characteristics
- Race-specific bonuses for controlling certain region types
- Visual indicators on the map showing region bonus values
- Dynamic region bonus values based on game progression 