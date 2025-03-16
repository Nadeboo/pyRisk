from pyRisk.pyRisk import MSPaintRiskEditor
from pyRisk.player import Player
import tkinter as tk

def main():
    # Create a test environment
    root = tk.Tk()
    root.title("Resource Tooltip and Race Change Test")
    root.geometry("1000x700")
    
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
    
    # Add instructions panel at the bottom
    instructions_frame = tk.Frame(root, bg='#f0f0f0', relief=tk.RAISED, bd=2)
    instructions_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
    
    # Title
    tk.Label(
        instructions_frame, 
        text="Resource Tooltip and Race Change Test", 
        font=("Arial", 12, "bold"),
        bg='#f0f0f0'
    ).pack(pady=(10, 5))
    
    # Instructions
    instructions_text = """
    This test demonstrates:
    
    1. Resource tooltips: Hover over any resource's per-turn value to see a breakdown
       of where those resources come from (base income, race bonuses, resource tiles).
       
    2. Race-specific bonuses:
       - HUMAN players get +1 influence per turn
       - WIZARD players get +1 mana per turn
       
    3. Race changes: Try changing a player's race by clicking the checkboxes.
       The resource values and tooltips will update immediately.
       
    4. Visual indicators: Resources with race bonuses show a "(Race)" indicator.
    """
    
    tk.Label(
        instructions_frame, 
        text=instructions_text,
        justify=tk.LEFT,
        bg='#f0f0f0',
        padx=20
    ).pack(pady=5)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 