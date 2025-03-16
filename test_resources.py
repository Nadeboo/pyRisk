from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk

# Create a test environment
root = tk.Tk()
app = MSPaintRiskEditor(root)

# Create test players with different races
human_player = Player("Human Player", (255, 0, 0), "HUMAN")
wizard_player = Player("Wizard Player", (0, 0, 255), "WIZARD")
other_player = Player("Other Player", (0, 255, 0), "DWARF")

# Add players to the app
app.players = [human_player, wizard_player, other_player]

# Update resources
app.update_player_resources()

# Print results
print("Resource calculation test results:")
print("---------------------------------")
for player in app.players:
    print(f"Player: {player.name}")
    print(f"  Faction: {player.faction}")
    print(f"  Gold per turn: {player.gold_per_turn}")
    print(f"  Research per turn: {player.research_per_turn}")
    print(f"  Mana per turn: {player.mana_per_turn}")
    print(f"  Influence per turn: {player.influence_per_turn}")
    print()

# Clean up
root.destroy() 