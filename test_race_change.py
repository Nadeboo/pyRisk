from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Race Change Test")
    root.geometry("800x600")
    
    app = MSPaintRiskEditor(root)
    
    # Create a test player with no race initially
    test_player = Player("Test Player", (255, 0, 0), None)
    
    # Add player to the app
    app.players = [test_player]
    
    # Update resources
    app.update_player_resources()
    
    # Print initial resource values
    print("Initial resources (no race):")
    print(f"Gold: {test_player.gold_per_turn}")
    print(f"Research: {test_player.research_per_turn}")
    print(f"Mana: {test_player.mana_per_turn}")
    print(f"Influence: {test_player.influence_per_turn}")
    print()
    
    # Show the players screen
    app.show_players_screen()
    
    # Add instructions
    instructions_frame = tk.Frame(root)
    instructions_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)
    
    instructions = tk.Label(
        instructions_frame, 
        text="1. Select HUMAN race and observe resource changes in console\n"
             "2. Then select WIZARD race and observe resource changes\n"
             "3. Finally, uncheck all races and observe resource changes",
        justify=tk.LEFT
    )
    instructions.pack(pady=5)
    
    # Add buttons to simulate race changes
    button_frame = tk.Frame(instructions_frame)
    button_frame.pack(pady=5)
    
    def change_to_human():
        test_player.faction = "HUMAN"
        app.update_player_resources()
        print("Changed to HUMAN:")
        print(f"Gold: {test_player.gold_per_turn}")
        print(f"Research: {test_player.research_per_turn}")
        print(f"Mana: {test_player.mana_per_turn}")
        print(f"Influence: {test_player.influence_per_turn}")
        print()
        app.current_screen.update_player_list()
    
    def change_to_wizard():
        test_player.faction = "WIZARD"
        app.update_player_resources()
        print("Changed to WIZARD:")
        print(f"Gold: {test_player.gold_per_turn}")
        print(f"Research: {test_player.research_per_turn}")
        print(f"Mana: {test_player.mana_per_turn}")
        print(f"Influence: {test_player.influence_per_turn}")
        print()
        app.current_screen.update_player_list()
    
    def change_to_none():
        test_player.faction = None
        app.update_player_resources()
        print("Changed to NO RACE:")
        print(f"Gold: {test_player.gold_per_turn}")
        print(f"Research: {test_player.research_per_turn}")
        print(f"Mana: {test_player.mana_per_turn}")
        print(f"Influence: {test_player.influence_per_turn}")
        print()
        app.current_screen.update_player_list()
    
    tk.Button(button_frame, text="Change to HUMAN", command=change_to_human).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Change to WIZARD", command=change_to_wizard).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Clear Race", command=change_to_none).pack(side=tk.LEFT, padx=5)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 