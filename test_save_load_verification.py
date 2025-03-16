from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
from pyRisk.save_load_manager import SaveLoadManager
import tkinter as tk
import os
import json

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Save/Load Verification Test")
    root.geometry("1000x700")
    
    app = MSPaintRiskEditor(root)
    
    # Create test players with different races and region bonuses
    human_player = Player("Human Player", (255, 0, 0), "HUMAN")
    human_player.region_bonus = 3
    human_player.gold = 10
    human_player.research = 15
    human_player.influence = 5
    
    wizard_player = Player("Wizard Player", (0, 0, 255), "WIZARD")
    wizard_player.region_bonus = 2
    wizard_player.mana = 8
    
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
        text="Save/Load Verification Test", 
        font=("Arial", 12, "bold"),
        bg='#f0f0f0'
    ).pack(pady=(10, 5))
    
    # Instructions
    instructions_text = """
    This test verifies that all features are properly saved and loaded:
    
    1. Initial values:
       - Human Player: 3 region bonus points, HUMAN race, 10 gold, 15 research, 5 influence
       - Wizard Player: 2 region bonus points, WIZARD race, 8 mana
       - Other Player: 1 region bonus point, DWARF race
    
    2. Test procedure:
       - Click "Save Test Game" to save the current state
       - Click "Verify Save File" to check the contents of the save file
       - Change some values using the UI
       - Click "Load Test Game" to restore the original values
       - Click "Verify Loaded State" to check that all values were restored correctly
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
    
    # Test file path
    test_file = "verification_test_save.mprg"
    
    # Save test game function
    def save_test_game():
        # Prepare game data
        game_data = {
            "game_name": "Verification Test Game",
            "current_turn": 1,
            "roll_mode": app.roll_mode,
            "players": [{
                "name": player.name,
                "color": player.color,
                "faction": player.faction,
                "allies": [],
                "naps": [],
                "region_bonus": player.region_bonus,
                # Include resource values
                "gold": player.gold,
                "research": player.research,
                "mana": player.mana,
                "influence": player.influence
            } for player in app.players],
            "game_states": [],
            "tile_owners": {},
            "roll_table": {},
            "all_roll_results": []
        }
        
        # Save to file
        with open(test_file, 'w') as f:
            json.dump(game_data, f)
            
        print(f"Test game saved to {test_file}")
        
    # Verify save file function
    def verify_save_file():
        if not os.path.exists(test_file):
            print("No test save file found. Please save first.")
            return
            
        # Load from file
        with open(test_file, 'r') as f:
            game_data = json.load(f)
            
        print("\nVerifying save file contents:")
        print("-----------------------------")
        
        # Check game info
        print(f"Game name: {game_data.get('game_name')}")
        print(f"Current turn: {game_data.get('current_turn')}")
        print(f"Roll mode: {game_data.get('roll_mode')}")
        
        # Check player data
        print("\nPlayer data:")
        for player_data in game_data.get("players", []):
            print(f"  Player: {player_data.get('name')}")
            print(f"    Faction: {player_data.get('faction')}")
            print(f"    Region bonus: {player_data.get('region_bonus')}")
            print(f"    Gold: {player_data.get('gold')}")
            print(f"    Research: {player_data.get('research')}")
            print(f"    Mana: {player_data.get('mana')}")
            print(f"    Influence: {player_data.get('influence')}")
            print()
    
    # Load test game function
    def load_test_game():
        if not os.path.exists(test_file):
            print("No test save file found. Please save first.")
            return
            
        # Load from file
        with open(test_file, 'r') as f:
            game_data = json.load(f)
            
        # Create new players
        app.players = []
        
        for pdata in game_data.get("players", []):
            player = Player(pdata["name"], pdata["color"], pdata.get("faction"))
            
            # Load region bonus
            if "region_bonus" in pdata:
                player.region_bonus = pdata["region_bonus"]
                
            # Load resource values
            if "gold" in pdata:
                player.gold = pdata["gold"]
            if "research" in pdata:
                player.research = pdata["research"]
            if "mana" in pdata:
                player.mana = pdata["mana"]
            if "influence" in pdata:
                player.influence = pdata["influence"]
                
            app.players.append(player)
            
        # Update resources and display
        app.update_player_resources()
        app.current_screen.update_player_list()
        
        print(f"Test game loaded from {test_file}")
    
    # Verify loaded state function
    def verify_loaded_state():
        print("\nVerifying loaded state:")
        print("----------------------")
        
        for player in app.players:
            print(f"Player: {player.name}")
            print(f"  Faction: {player.faction}")
            print(f"  Region bonus: {player.region_bonus}")
            print(f"  Gold: {player.gold} (+{player.gold_per_turn}/turn)")
            print(f"  Research: {player.research} (+{player.research_per_turn}/turn)")
            print(f"  Mana: {player.mana} (+{player.mana_per_turn}/turn)")
            print(f"  Influence: {player.influence} (+{player.influence_per_turn}/turn)")
            
            # Print resource sources
            print("  Resource sources:")
            for resource_type in ['gold', 'research', 'mana', 'influence']:
                sources = player.get_resource_sources(resource_type)
                if sources:
                    print(f"    {resource_type.upper()}:")
                    for amount, description in sources:
                        print(f"      +{amount}: {description}")
            print()
    
    # Add buttons
    tk.Button(test_frame, text="Save Test Game", command=save_test_game).pack(side=tk.LEFT, padx=5)
    tk.Button(test_frame, text="Verify Save File", command=verify_save_file).pack(side=tk.LEFT, padx=5)
    tk.Button(test_frame, text="Load Test Game", command=load_test_game).pack(side=tk.LEFT, padx=5)
    tk.Button(test_frame, text="Verify Loaded State", command=verify_loaded_state).pack(side=tk.LEFT, padx=5)
    
    # Start the main loop
    root.mainloop()
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    main() 