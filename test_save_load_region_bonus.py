from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk
import os
import json

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Save/Load Region Bonus Test")
    root.geometry("1000x700")
    
    app = MSPaintRiskEditor(root)
    
    # Create test players with different races and region bonuses
    human_player = Player("Human Player", (255, 0, 0), "HUMAN")
    human_player.region_bonus = 3
    
    wizard_player = Player("Wizard Player", (0, 0, 255), "WIZARD")
    wizard_player.region_bonus = 2
    
    other_player = Player("Other Player", (0, 255, 0), "DWARF")
    other_player.region_bonus = 1
    
    # Add players to the app
    app.players = [human_player, wizard_player, other_player]
    
    # Update resources
    app.update_player_resources()
    
    # Show the players screen
    app.show_players_screen()
    
    # Add instructions and test controls
    instructions_frame = tk.Frame(root, bg='#f0f0f0', relief=tk.RAISED, bd=2)
    instructions_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
    
    # Title
    tk.Label(
        instructions_frame, 
        text="Save/Load Region Bonus Test", 
        font=("Arial", 12, "bold"),
        bg='#f0f0f0'
    ).pack(pady=(10, 5))
    
    # Instructions
    instructions_text = """
    This test demonstrates saving and loading region bonuses:
    
    1. Initial region bonus values:
       - Human Player: 3 region bonus points
       - Wizard Player: 2 region bonus points
       - Other Player: 1 region bonus point
    
    2. Test procedure:
       - Click "Save Test Game" to save the current state
       - Change some region bonus values using the +/- buttons
       - Click "Load Test Game" to restore the original values
    """
    
    tk.Label(
        instructions_frame, 
        text=instructions_text,
        justify=tk.LEFT,
        bg='#f0f0f0',
        padx=20
    ).pack(pady=5)
    
    # Test controls
    test_frame = tk.Frame(instructions_frame, bg='#f0f0f0')
    test_frame.pack(pady=10)
    
    # Save test game function
    def save_test_game():
        # Create a temporary file for testing
        test_file = "test_region_bonus_save.mprg"
        
        # Prepare game data
        game_data = {
            "game_name": "Test Game",
            "current_turn": 1,
            "roll_mode": app.roll_mode,
            "players": [{
                "name": player.name,
                "color": player.color,
                "faction": player.faction,
                "allies": [],
                "naps": [],
                "region_bonus": player.region_bonus
            } for player in app.players],
            "game_states": [],
            "tile_owners": {},
            "roll_table": {},
            "all_roll_results": []
        }
        
        # Save to file
        with open(test_file, 'w') as f:
            json.dump(game_data, f)
            
        print(f"Test game saved with region bonuses: {[p.region_bonus for p in app.players]}")
        
    # Load test game function
    def load_test_game():
        test_file = "test_region_bonus_save.mprg"
        
        if not os.path.exists(test_file):
            print("No test save file found. Please save first.")
            return
            
        # Load from file
        with open(test_file, 'r') as f:
            game_data = json.load(f)
            
        # Create new players
        app.players = []
        name_to_player = {}
        
        for pdata in game_data.get("players", []):
            player = Player(pdata["name"], pdata["color"], pdata.get("faction"))
            if "region_bonus" in pdata:
                player.region_bonus = pdata["region_bonus"]
            app.players.append(player)
            
        # Update resources and display
        app.update_player_resources()
        app.current_screen.update_player_list()
        
        print(f"Test game loaded with region bonuses: {[p.region_bonus for p in app.players]}")
    
    # Add buttons
    tk.Button(test_frame, text="Save Test Game", command=save_test_game).pack(side=tk.LEFT, padx=10)
    tk.Button(test_frame, text="Load Test Game", command=load_test_game).pack(side=tk.LEFT, padx=10)
    
    # Start the main loop
    root.mainloop()
    
    # Clean up test file
    if os.path.exists("test_region_bonus_save.mprg"):
        os.remove("test_region_bonus_save.mprg")

if __name__ == "__main__":
    main() 