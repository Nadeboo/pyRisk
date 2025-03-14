# save_load_manager.py

import json
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
from pyRisk.player import Player
from pyRisk.game_state import GameState
from pyRisk.unit import Unit, UnitType


class SaveLoadManager:
    @staticmethod
    def save_game(app):
        """
        Saves the current game state to a file.
        
        Args:
            app: The MSPaintRiskEditor instance
        """
        if not app.game_states:
            messagebox.showwarning("No Game to Save", "No game data to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mprg",
            filetypes=[("MSPaint Risk Game files", "*.mprg")]
        )
        
        if file_path:
            game_data = {
                # Basic game info
                "game_name": app.game_name,
                "current_turn": app.current_turn,
                "roll_mode": app.roll_mode,
                
                # Player data
                "players": [{
                    "name": player.name,
                    "color": player.color,
                    "faction": player.faction,
                    "allies": [ally.name for ally in player.allies],
                    "naps": [nap.name for nap in player.naps]
                } for player in app.players],
                
                # Game states and map data
                "game_states": [state.map_image_path for state in app.game_states],
                "tile_owners": app.tile_owners,
                
                # Roll configuration and results
                "roll_table": {
                    "number_values": app.roll_table.number_values,
                    "repeats_config": app.roll_table.repeats_config,
                    "palindromes_config": app.roll_table.palindromes_config
                },
                "all_roll_results": app.all_roll_results,
                
                # Tregonia-specific data
                "tregonia_data": {
                    "units": [
                        {
                            "owner": unit.owner,
                            "unit_type": unit.unit_type.value,
                            "unit_id": unit.unit_id,
                            "position": unit.position
                        }
                        for unit in app.units
                    ],
                    "next_unit_id": app.next_unit_id
                }
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(game_data, f)
                messagebox.showinfo("Game Saved", "Game has been saved successfully.")
            except Exception as e:
                messagebox.showerror("Error Saving Game", f"An error occurred while saving the game:\n{e}")

    @staticmethod
    def load_game(app):
        """
        Loads a game state from a file.
        
        Args:
            app: The MSPaintRiskEditor instance
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("MSPaint Risk Game files", "*.mprg")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                game_data = json.load(f)
            
            # Load basic game data
            app.game_name = game_data.get("game_name", "Untitled Game")
            app.current_turn = game_data.get("current_turn", 0)
            app.roll_mode = game_data.get("roll_mode", "application")
            
            # Load players and their relationships
            app.players = []
            name_to_player = {}
            for pdata in game_data.get("players", []):
                player = Player(pdata["name"], pdata["color"], pdata.get("faction"))
                app.players.append(player)
                name_to_player[player.name] = player
            
            # Set up player relationships (allies and NAPs)
            for pdata, player in zip(game_data.get("players", []), app.players):
                player.allies = [name_to_player[name] for name in pdata.get("allies", []) 
                               if name in name_to_player]
                player.naps = [name_to_player[name] for name in pdata.get("naps", []) 
                             if name in name_to_player]
            
            # Load game states and map
            app.game_states = []
            for path in game_data.get("game_states", []):
                try:
                    turn_number = int(os.path.splitext(os.path.basename(path))[0].split('_')[-1])
                    state = GameState(turn_number, path)
                    if os.path.exists(path):  # Only add if the file exists
                        app.game_states.append(state)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not load game state from {path}: {e}")
            
            # Load last map state if available
            if app.game_states:
                last_state = app.game_states[-1]
                try:
                    app.map_image = Image.open(last_state.map_image_path)
                    app.map_draw = ImageDraw.Draw(app.map_image)
                    if hasattr(app.current_screen, 'display_map_image'):
                        app.current_screen.display_map_image()
                    else:
                        app.show_game_screen()
                except (FileNotFoundError, IOError) as e:
                    messagebox.showerror("Error Loading Map", 
                                       f"Could not load map image: {str(e)}")
                    return
            
            # Load roll table configuration
            roll_table_data = game_data.get("roll_table", {})
            if roll_table_data:
                app.roll_table.number_values = roll_table_data.get(
                    "number_values", app.roll_table.number_values)
                app.roll_table.repeats_config = roll_table_data.get(
                    "repeats_config", app.roll_table.repeats_config)
                app.roll_table.palindromes_config = roll_table_data.get(
                    "palindromes_config", app.roll_table.palindromes_config)
            
            # Load game results
            app.all_roll_results = game_data.get("all_roll_results", [])
            app.tile_owners = game_data.get("tile_owners", {})
            
            # Initialize units list
            app.units = []
            app.next_unit_id = 1
            
            # Load Tregonia-specific data
            if app.roll_mode == 'tregonia':
                tregonia_data = game_data.get("tregonia_data", {})
                
                # Load units
                for unit_data in tregonia_data.get("units", []):
                    try:
                        # Handle position data which could be None or a tuple
                        position = unit_data.get("position")
                        if position is not None:
                            position = tuple(position)  # Convert list to tuple if present
                            
                        unit = Unit(
                            owner=unit_data["owner"],
                            unit_type=UnitType(unit_data["unit_type"]),
                            unit_id=unit_data["unit_id"],
                            position=position
                        )
                        app.units.append(unit)
                    except (KeyError, ValueError) as e:
                        print(f"Warning: Could not load unit: {e}")
                        continue
                
                # Safely calculate next_unit_id
                if app.units:
                    # Use a list comprehension with a default value to handle invalid unit_ids
                    valid_ids = [unit.unit_id for unit in app.units if hasattr(unit, 'unit_id')]
                    app.next_unit_id = (max(valid_ids) + 1) if valid_ids else 1
                else:
                    app.next_unit_id = 1
            
            messagebox.showinfo("Game Loaded", "Game has been loaded successfully.")
            
        except Exception as e:
            messagebox.showerror("Error Loading Game", 
                               f"An error occurred while loading the game:\n{str(e)}")
            # Ensure app is in a valid state even if load fails
            app.next_unit_id = 1
            app.units = []