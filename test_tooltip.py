from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Resource Tooltip Test")
    root.geometry("800x600")
    
    app = MSPaintRiskEditor(root)
    
    # Create test players with different races
    human_player = Player("Human Player", (255, 0, 0), "HUMAN")
    wizard_player = Player("Wizard Player", (0, 0, 255), "WIZARD")
    other_player = Player("Other Player", (0, 255, 0), "DWARF")
    
    # Add players to the app
    app.players = [human_player, wizard_player, other_player]
    
    # Add some resource tiles
    app.resource_tiles = {
        (100, 100): {'type': 'gold', 'owner': 'Human Player'},
        (200, 200): {'type': 'gold', 'owner': 'Human Player'},
        (300, 300): {'type': 'mana', 'owner': 'Wizard Player'}
    }
    
    # Update resources
    app.update_player_resources()
    
    # Show the players screen
    app.show_players_screen()
    
    # Add instructions
    instructions = tk.Label(root, text="Hover over the resource per-turn values to see the tooltip breakdown")
    instructions.pack(side=tk.BOTTOM, pady=10)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 