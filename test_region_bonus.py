from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Region Bonus Test")
    root.geometry("1000x700")
    
    app = MSPaintRiskEditor(root)
    
    # Create test players with different races
    human_player = Player("Human Player", (255, 0, 0), "HUMAN")
    wizard_player = Player("Wizard Player", (0, 0, 255), "WIZARD")
    dwarf_player = Player("Dwarf Player", (0, 255, 0), "DWARF")
    elf_player = Player("Elf Player", (255, 255, 0), "ELF")
    
    # Add players to the app
    app.players = [human_player, wizard_player, dwarf_player, elf_player]
    
    # Show the players screen
    app.show_players_screen()
    
    # Add test controls
    test_frame = tk.Frame(root, bg='#f0f0f0', relief=tk.RAISED, bd=2)
    test_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
    
    # Title
    tk.Label(
        test_frame, 
        text="Region Bonus Test", 
        font=("Arial", 12, "bold"),
        bg='#f0f0f0'
    ).pack(pady=(10, 5))
    
    # Instructions
    instructions_text = """
    This test verifies that region bonuses are correctly applied to player resources.
    
    1. Use the sliders to adjust region bonus values for each player
    2. Click "Update Resources" to apply the changes
    3. Observe the influence per turn values and resource tooltips
    4. The "Run Test Cases" button will automatically test various scenarios
    """
    
    tk.Label(
        test_frame, 
        text=instructions_text,
        justify=tk.LEFT,
        bg='#f0f0f0',
        padx=20
    ).pack(pady=5)
    
    # Create sliders for each player
    sliders_frame = tk.Frame(test_frame, bg='#f0f0f0')
    sliders_frame.pack(pady=10)
    
    player_sliders = {}
    
    for i, player in enumerate(app.players):
        player_frame = tk.Frame(sliders_frame, bg='#f0f0f0')
        player_frame.grid(row=0, column=i, padx=10)
        
        tk.Label(
            player_frame,
            text=f"{player.name} ({player.faction})",
            bg='#f0f0f0',
            fg=f"#{player.color[0]:02x}{player.color[1]:02x}{player.color[2]:02x}"
        ).pack()
        
        slider = tk.Scale(
            player_frame,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            label="Region Bonus",
            bg='#f0f0f0'
        )
        slider.pack()
        player_sliders[player.name] = slider
    
    # Create a frame for buttons
    buttons_frame = tk.Frame(test_frame, bg='#f0f0f0')
    buttons_frame.pack(pady=10)
    
    # Results text area
    results_text = tk.Text(test_frame, height=10, width=80)
    results_text.pack(pady=10)
    
    # Function to update resources based on slider values
    def update_resources():
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "Updating resources with region bonuses:\n\n")
        
        for player in app.players:
            # Get slider value
            bonus = player_sliders[player.name].get()
            player.region_bonus = bonus
            
            results_text.insert(tk.END, f"{player.name} ({player.faction}): Region Bonus = {bonus}\n")
        
        # Update resources
        app.update_player_resources()
        
        # Display results
        results_text.insert(tk.END, "\nResource calculation results:\n")
        for player in app.players:
            results_text.insert(tk.END, f"\n{player.name} ({player.faction}):\n")
            results_text.insert(tk.END, f"  Gold: {player.gold} (+{player.gold_per_turn}/turn)\n")
            results_text.insert(tk.END, f"  Research: {player.research} (+{player.research_per_turn}/turn)\n")
            results_text.insert(tk.END, f"  Mana: {player.mana} (+{player.mana_per_turn}/turn)\n")
            results_text.insert(tk.END, f"  Influence: {player.influence} (+{player.influence_per_turn}/turn)\n")
            
            # Display resource sources
            results_text.insert(tk.END, "  Resource sources:\n")
            for resource_type in ['gold', 'research', 'mana', 'influence']:
                sources = player.get_resource_sources(resource_type)
                if sources:
                    results_text.insert(tk.END, f"    {resource_type.upper()}:\n")
                    for amount, description in sources:
                        results_text.insert(tk.END, f"      +{amount}: {description}\n")
    
    # Function to run automated test cases
    def run_test_cases():
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "Running automated test cases:\n\n")
        
        test_cases = [
            {"name": "No region bonuses", "bonuses": [0, 0, 0, 0]},
            {"name": "Equal region bonuses", "bonuses": [3, 3, 3, 3]},
            {"name": "Varied region bonuses", "bonuses": [1, 2, 3, 4]},
            {"name": "High region bonuses", "bonuses": [8, 7, 6, 5]},
        ]
        
        for test_case in test_cases:
            results_text.insert(tk.END, f"Test Case: {test_case['name']}\n")
            results_text.insert(tk.END, "----------------------------------------\n")
            
            # Set slider values
            for i, player in enumerate(app.players):
                bonus = test_case["bonuses"][i]
                player_sliders[player.name].set(bonus)
                player.region_bonus = bonus
            
            # Update resources
            app.update_player_resources()
            
            # Display results
            for player in app.players:
                results_text.insert(tk.END, f"{player.name} ({player.faction}): Region Bonus = {player.region_bonus}\n")
                results_text.insert(tk.END, f"  Influence per turn: +{player.influence_per_turn}\n")
                
                # Display influence sources
                sources = player.get_resource_sources('influence')
                if sources:
                    results_text.insert(tk.END, f"  Influence sources:\n")
                    for amount, description in sources:
                        results_text.insert(tk.END, f"    +{amount}: {description}\n")
                
                results_text.insert(tk.END, "\n")
            
            results_text.insert(tk.END, "\n")
    
    # Add buttons
    tk.Button(buttons_frame, text="Update Resources", command=update_resources).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="Run Test Cases", command=run_test_cases).pack(side=tk.LEFT, padx=5)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 