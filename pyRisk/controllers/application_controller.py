# controllers/application_controller.py

import tkinter as tk
from typing import Any
from models.player import Player
from models.game_state import GameState
from models.roll_table import RollTable
from utils.utils import flood_fill
from views.start_view import StartView
from views.game_view import GameView
from views.players_view import PlayersView
from views.alliances_view import AlliancesView
from views.roll_view import RollView
from PIL import Image, ImageDraw
import os
import json
import messagebox


class ApplicationController:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_view: Any = None
        self.model = self.initialize_model()
        self.setup_start_view()

    def initialize_model(self):
        # Initialize your model components here
        return {
            "game_name": "Untitled Game",
            "current_turn": 0,
            "players": [],
            "game_states": [],
            "roll_table": RollTable(),
            "map_image": None,
            "original_map_image": None,
            "map_history": [],
            "max_history": 10,
            "mode": 'color',
            "selected_player": None,
            "tile_owners": {},
            "roll_mode": None,  # Set by StartView
            "all_roll_results": []
        }

    def setup_start_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = StartView(self.root, self.handle_start_view_actions)

    def handle_start_view_actions(self, action: str):
        if action in ["external", "application"]:
            self.model["roll_mode"] = action
            self.setup_game_view()

    def setup_game_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = GameView(self.root, self.handle_game_view_actions)
        # Additional setup if necessary

    def handle_game_view_actions(self, action: str, data=None):
        if action == "next_turn":
            self.advance_turn()
        elif action == "toggle_mode":
            self.toggle_mode()
        elif action == "undo":
            self.undo_action()
        elif action == "select_player":
            self.select_player(data)
        elif action == "canvas_click":
            self.handle_canvas_click(data)
        elif action == "import_map":
            self.import_map()
        elif action == "export_map":
            self.export_map()
        elif action == "export_gif":
            self.export_gif()
        elif action == "save_game":
            self.save_game()
        elif action == "load_game":
            self.load_game()
        # Handle other actions as needed

    def setup_players_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = PlayersView(self.root, self.handle_players_view_actions)

    def handle_players_view_actions(self, action: str, data=None):
        if action == "add_player":
            self.add_player()
        elif action == "edit_player":
            self.edit_player(data)
        elif action == "remove_player":
            self.remove_player(data)
        elif action == "get_players":
            return self.model["players"]
        elif action == "get_player_roll_info":
            player_name = data
            # Placeholder for actual roll info
            return ("", 0, 0)
        # Handle other actions as needed

    def setup_alliances_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = AlliancesView(self.root, self.handle_alliances_view_actions)

    def handle_alliances_view_actions(self, action: str, *args):
        if action == "add_alliance":
            player1_name, player2_name = args
            self.add_alliance(player1_name, player2_name)
        elif action == "add_nap":
            player1_name, player2_name = args
            self.add_nap(player1_name, player2_name)
        elif action == "get_players":
            return self.model["players"]
        # Handle other actions as needed

    def setup_roll_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = RollView(self.root, self.handle_roll_view_actions)

    def handle_roll_view_actions(self, action: str, *args):
        if action == "configure_roll_table":
            self.configure_roll_table()
        elif action == "roll_for_all_players":
            self.roll_for_all_players()
        elif action == "get_current_roll":
            turn = self.model["current_turn"]
            roll_results = self.model["all_roll_results"][-1][1] if self.model["all_roll_results"] else []
            return (turn, roll_results)
        elif action == "get_all_rolls":
            return self.model["all_roll_results"]
        # Handle other actions as needed

    def advance_turn(self):
        self.model["current_turn"] += 1
        self.current_view.update_turn_label(self.model["current_turn"])
        self.save_current_map_state()
        self.model["map_history"].clear()
        if self.model["roll_mode"] != 'external':
            self.model["roll_table"].number_values.clear()
        self.current_view.refresh()

    def toggle_mode(self):
        if self.model["mode"] == 'color':
            self.model["mode"] = 'erase'
        else:
            self.model["mode"] = 'color'
        self.current_view.update_mode_button(self.model["mode"])

    def undo_action(self):
        if self.model["map_history"]:
            self.model["map_image"] = self.model["map_history"].pop()
            self.current_view.display_map_image(self.model["map_image"])
        else:
            messagebox.showinfo("Undo", "No actions to undo.")

    def select_player(self, player: Player):
        self.model["selected_player"] = player
        self.current_view.highlight_selected_player_button(player.name)

    def handle_canvas_click(self, event):
        x, y = self.current_view.get_canvas_click_coordinates(event)
        if not self.model["map_image"]:
            messagebox.showwarning("No Map Loaded", "Please import a map before coloring.")
            return
        if x >= self.model["map_image"].width or y >= self.model["map_image"].height:
            return

        # Save current state for undo
        if len(self.model["map_history"]) >= self.model["max_history"]:
            self.model["map_history"].pop(0)
        self.model["map_history"].append(self.model["map_image"].copy())

        if self.model["mode"] == 'color':
            if not self.model["selected_player"]:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return
            target_color = self.model["map_image"].getpixel((x, y))
            replacement_color = self.model["selected_player"].color + (255,)  # Assuming RGBA

            # Example: Decrement remaining tiles if applicable

            previous_owner = self.model["tile_owners"].get((x, y))
            if previous_owner and previous_owner != self.model["selected_player"].name:
                self.update_player_tiles(previous_owner, 1)

            self.model["tile_owners"][(x, y)] = self.model["selected_player"].name
            flood_fill(self.model["map_image"], x, y, target_color, replacement_color)
            self.current_view.display_map_image(self.model["map_image"])
        
        elif self.model["mode"] == 'erase':
            original_color = self.model["map_image"].getpixel((x, y))
            # Assuming there's an original map to revert to
            replacement_color = self.model["original_map_image"].getpixel((x, y))
            if (x, y) in self.model["tile_owners"]:
                player_name = self.model["tile_owners"].pop((x, y))
                self.update_player_tiles(player_name, 1)
            flood_fill(self.model["map_image"], x, y, original_color, replacement_color)
            self.current_view.display_map_image(self.model["map_image"])

    def update_player_tiles(self, player_name: str, change: int):
        # Placeholder for updating player tiles
        pass

    def add_player(self):
        name = simpledialog.askstring("Player Name", "Enter player name:")
        if name:
            color = colorchooser.askcolor(title="Choose player color")
            if color[0]:
                faction = simpledialog.askstring("Faction", "Enter faction name (optional):")
                try:
                    name, color_rgb, faction = self.validate_player_data(name, color[0], faction)
                    player = Player(name, color_rgb, faction)
                    self.model["players"].append(player)
                    self.current_view.refresh()
                except ValueError as e:
                    messagebox.showerror("Invalid Input", str(e))

    def edit_player(self, player: Optional[Player]):
        if player:
            name = simpledialog.askstring("Player Name", "Edit player name:", initialvalue=player.name)
            if name:
                color = colorchooser.askcolor(title="Choose player color", initialcolor=player.color)
                if color[0]:
                    faction = simpledialog.askstring("Faction", "Edit faction name (optional):", initialvalue=player.faction)
                    try:
                        name, color_rgb, faction = self.validate_player_data(name, color[0], faction, editing=True, current_player=player)
                        player.name = name
                        player.color = color_rgb
                        player.faction = faction
                        self.current_view.refresh()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", str(e))
        else:
            messagebox.showwarning("No Selection", "Please select a player to edit.")

    def remove_player(self, player: Optional[Player]):
        if player:
            # Remove alliances and NAPs
            for p in self.model["players"]:
                if player in p.allies:
                    p.allies.remove(player)
                if player in p.naps:
                    p.naps.remove(player)
            self.model["players"].remove(player)
            self.current_view.refresh()
        else:
            messagebox.showwarning("No Selection", "Please select a player to remove.")

    def add_alliance(self, player1_name: str, player2_name: str):
        if player1_name == player2_name:
            messagebox.showwarning("Invalid Selection", "Please select two different players.")
            return
        p1 = self.get_player_by_name(player1_name)
        p2 = self.get_player_by_name(player2_name)
        if p1 and p2:
            if p2 not in p1.allies:
                p1.add_ally(p2)
                p2.add_ally(p1)
                messagebox.showinfo("Alliance Added", f"{p1.name} and {p2.name} are now allies.")
                self.current_view.refresh()
            else:
                messagebox.showinfo("Already Allies", f"{p1.name} and {p2.name} are already allies.")
        else:
            messagebox.showwarning("Invalid Selection", "Please select valid players.")

    def add_nap(self, player1_name: str, player2_name: str):
        if player1_name == player2_name:
            messagebox.showwarning("Invalid Selection", "Please select two different players.")
            return
        p1 = self.get_player_by_name(player1_name)
        p2 = self.get_player_by_name(player2_name)
        if p1 and p2:
            if p2 not in p1.naps:
                p1.add_nap(p2)
                p2.add_nap(p1)
                messagebox.showinfo("NAP Added", f"{p1.name} and {p2.name} have a Non-Aggression Pact.")
                self.current_view.refresh()
            else:
                messagebox.showinfo("NAP Exists", f"{p1.name} and {p2.name} already have a NAP.")
        else:
            messagebox.showwarning("Invalid Selection", "Please select valid players.")

    def get_player_by_name(self, name: str) -> Optional[Player]:
        for player in self.model["players"]:
            if player.name == name:
                return player
        return None

    def validate_player_data(self, name: str, color: tuple, faction: Optional[str], editing=False, current_player: Optional[Player]=None):
        """
        Validates the player data.

        Args:
            name (str): Player's name.
            color (tuple): Player's color as an (R, G, B) tuple.
            faction (str or None): Player's faction.
            editing (bool): Whether this is an edit operation.
            current_player (Player, optional): The player being edited.

        Returns:
            tuple: (validated_name, color, faction)

        Raises:
            ValueError: If any validation fails.
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Player name cannot be empty.")
        name = name.strip()
        for player in self.model["players"]:
            if player.name.lower() == name.lower():
                if editing and current_player and player == current_player:
                    continue
                raise ValueError(f"Player name '{name}' is already taken.")

        # Validate color
        if not isinstance(color, tuple) or len(color) != 3:
            raise ValueError("Color must be a tuple of 3 integers (R, G, B).")
        for component in color:
            if not isinstance(component, int) or not (0 <= component <= 255):
                raise ValueError("Each color component must be an integer between 0 and 255.")

        # Validate faction
        if faction:
            faction = faction.strip()
            if not faction:
                faction = None
        else:
            faction = None

        return name, color, faction

    def configure_roll_table(self):
        self.model["roll_table"].open_configuration_window(self.root)

    def roll_for_all_players(self):
        if not self.model["players"]:
            messagebox.showwarning("No Players", "Please add players before rolling.")
            return
        self.model["roll_table"].roll_number()
        roll_results = []
        for player in self.model["players"]:
            roll_value = self.model["roll_table"].roll_number()
            tiles = self.model["roll_table"].calculate_tiles(roll_value)
            roll_results.append((player.name, roll_value, tiles))
        self.model["all_roll_results"].append((self.model["current_turn"], roll_results))
        self.current_view.refresh()

    def get_current_roll(self):
        turn = self.model["current_turn"]
        roll_results = self.model["all_roll_results"][-1][1] if self.model["all_roll_results"] else []
        return (turn, roll_results)

    def get_all_rolls(self):
        return self.model["all_roll_results"]

    def import_map(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.model["map_image"] = Image.open(file_path).convert("RGBA")
            self.model["original_map_image"] = self.model["map_image"].copy()
            self.current_view.display_map_image(self.model["map_image"])
            self.save_current_map_state()
            self.model["map_history"].clear()

    def save_current_map_state(self):
        if self.model["map_image"] is None:
            return
        temp_dir = "temp_maps"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        filename = f"{temp_dir}/map_turn_{self.model['current_turn']}.png"
        self.model["map_image"].save(filename)
        game_state = GameState(self.model["current_turn"], filename)
        self.model["game_states"].append(game_state)

    def export_map(self):
        from tkinter import filedialog
        if self.model["map_image"] is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before exporting.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            self.model["map_image"].save(file_path)
            messagebox.showinfo("Map Exported", "Map has been exported successfully.")

    def export_gif(self):
        from tkinter import filedialog
        if not self.model["game_states"]:
            messagebox.showwarning("No Game States", "No game states to export.")
            return
        frames = [Image.open(state.map_image_path) for state in self.model["game_states"]]
        file_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
        if file_path:
            frames[0].save(file_path, save_all=True, append_images=frames[1:], duration=500, loop=0)
            messagebox.showinfo("GIF Exported", "Game progression GIF has been exported successfully.")

    def save_game(self):
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".mprg",
                                                 filetypes=[("MSPaint Risk Game files", "*.mprg")])
        if file_path:
            game_data = {
                "game_name": self.model["game_name"],
                "current_turn": self.model["current_turn"],
                "players": [{
                    "name": player.name,
                    "color": player.color,
                    "faction": player.faction,
                    "allies": [ally.name for ally in player.allies],
                    "naps": [nap.name for nap in player.naps]
                } for player in self.model["players"]],
                "game_states": [state.map_image_path for state in self.model["game_states"]],
                "roll_table": {
                    "number_values": self.model["roll_table"].number_values,
                    "repeats_config": self.model["roll_table"].repeats_config,
                    "palindromes_config": self.model["roll_table"].palindromes_config
                },
                "all_roll_results": self.model["all_roll_results"],
                "roll_mode": self.model["roll_mode"]
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(game_data, f)
                messagebox.showinfo("Game Saved", "Game has been saved successfully.")
            except Exception as e:
                messagebox.showerror("Error Saving Game", f"An error occurred while saving the game:\n{e}")

    def load_game(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("MSPaint Risk Game files", "*.mprg")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                self.model["game_name"] = game_data.get("game_name", "Untitled Game")
                self.model["current_turn"] = game_data.get("current_turn", 0)
                self.model["players"] = []
                name_to_player = {}
                for pdata in game_data.get("players", []):
                    player = Player(pdata["name"], tuple(pdata["color"]), pdata.get("faction"))
                    self.model["players"].append(player)
                    name_to_player[player.name] = player
                for pdata, player in zip(game_data.get("players", []), self.model["players"]):
                    player.allies = [name_to_player[name] for name in pdata.get("allies", []) if name in name_to_player]
                    player.naps = [name_to_player[name] for name in pdata.get("naps", []) if name in name_to_player]
                self.model["game_states"] = []
                for path in game_data.get("game_states", []):
                    turn_number = int(os.path.splitext(os.path.basename(path))[0].split('_')[-1])
                    state = GameState(turn_number, path)
                    self.model["game_states"].append(state)
                if self.model["game_states"]:
                    last_state = self.model["game_states"][-1]
                    self.model["map_image"] = Image.open(last_state.map_image_path)
                    self.model["original_map_image"] = self.model["map_image"].copy()
                    self.current_view.display_map_image(self.model["map_image"])
                self.model["roll_table"].number_values = game_data.get("roll_table", {}).get("number_values", self.model["roll_table"].number_values)
                self.model["roll_table"].repeats_config = game_data.get("roll_table", {}).get("repeats_config", self.model["roll_table"].repeats_config)
                self.model["roll_table"].palindromes_config = game_data.get("roll_table", {}).get("palindromes_config", self.model["roll_table"].palindromes_config)
                self.model["all_roll_results"] = game_data.get("all_roll_results", [])
                self.model["roll_mode"] = game_data.get("roll_mode", "application")
                messagebox.showinfo("Game Loaded", "Game has been loaded successfully.")
                self.current_view.refresh()
            except Exception as e:
                messagebox.showerror("Error Loading Game", f"An error occurred while loading the game:\n{e}")

    def destroy(self):
        if self.current_view:
            self.current_view.destroy()
