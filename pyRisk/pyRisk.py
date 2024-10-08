# pyRisk.py

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw
import os
import json
import zipfile
import io
import base64

from player import Player
from game_state import GameState
from roll_table import RollTable

# Import the screen classes
from game_screen import GameScreen
from players_screen import PlayersScreen
from alliances_screen import AlliancesScreen
from roll_screen import RollScreen
from start_screen import StartScreen  # Import StartScreen class
from rules_screen import RulesScreen, Rule
from rule_manager import RuleManager, setup_fortification_rule


class MSPaintRiskEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("MSPaint Risk Editor")
        self.master.geometry("1024x768")
        self.is_saving = False  # New flag to track saving state
        self.setup_menu()
        self.setup_ui()
        self.initialize_variables()
        self.show_start_screen()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)  # Bind closing event

    def initialize_variables(self):
        self.game_name = "Untitled Game"
        self.current_turn = 0
        self.players = []
        self.game_states = []
        self.roll_table = RollTable()
        self.all_roll_results = []
        self.map_image = None
        self.map_photo = None
        self.map_draw = None
        self.original_map_image = None
        self.map_history = []
        self.max_history = 10
        self.temp_dir = "temp_maps"
        self.current_screen = None
        self.player_rolls = {}
        self.roll_results = []
        self.tile_owners = {}  # Initialize tile ownership
        self.mode = 'color'
        self.selected_player = None
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        self.fortified_tiles = {}
        self.rule_manager = RuleManager()
        setup_fortification_rule(self.rule_manager)
            
    def setup_menu(self):
        self.menu_bar = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.import_map_item = self.file_menu.add_command(label="Import Map", command=self.import_map, state="disabled")
        self.file_menu.add_command(label="Export Map", command=self.export_map)
        self.file_menu.add_command(label="Export GIF", command=self.export_gif)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save Game", command=self.save_game)
        self.file_menu.add_command(label="Load Game", command=self.load_game)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.master.config(menu=self.menu_bar)

    def setup_ui(self):
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.toolbar = tk.Frame(self.main_frame)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self.setup_toolbar_buttons()

    def setup_toolbar_buttons(self):
        # Remove existing toolbar buttons
        for widget in self.toolbar.winfo_children():
            widget.destroy()
        # Create toolbar buttons
        for text, cmd in [("Game", self.show_game_screen),
                          ("Players", self.show_players_screen),
                          ("Alliances", self.show_alliances_screen),
                          ("Roll", self.show_roll_screen),
                          ("Rules", self.show_rules_screen)]:  # Add Rules button
            btn = tk.Button(self.toolbar, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def show_rules_screen(self):
        self.switch_screen(RulesScreen)

    def show_start_screen(self):
        self.switch_screen(StartScreen)

    def show_game_screen(self):
        self.switch_screen(GameScreen)

    def show_players_screen(self):
        self.switch_screen(PlayersScreen)

    def show_alliances_screen(self):
        self.switch_screen(AlliancesScreen)

    def show_roll_screen(self):
        self.switch_screen(RollScreen)
        
    def enable_import_map(self):
        self.file_menu.entryconfig("Import Map", state="normal")

    def switch_screen(self, screen_class):
        # Destroy current screen if it exists
        if self.current_screen:
            self.current_screen.destroy()
        # Show or hide toolbar based on screen
        if screen_class == StartScreen:
            self.toolbar.pack_forget()
        else:
            self.toolbar.pack(side=tk.TOP, fill=tk.X)
            self.setup_toolbar_buttons()
        # Initialize new screen
        self.current_screen = screen_class(self.content_frame, self)

    # Shared methods for menu actions
    def import_map(self):
        if not self.roll_mode:
            messagebox.showwarning("Roll Mode Not Selected", "Please select a roll mode before importing a map.")
            return
    
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.map_image = Image.open(file_path).convert("RGBA")
            self.map_draw = ImageDraw.Draw(self.map_image)
            self.original_map_image = self.map_image.copy()
            width, height = self.map_image.size
            self.tile_owners = {(x, y): None for x in range(width) for y in range(height)}
            if isinstance(self.current_screen, GameScreen):
                self.current_screen.display_map_image()
            else:
                self.show_game_screen()
            self.save_current_map_state()
            self.map_history.clear()


    def save_current_map_state(self):
        if self.map_image is None:
            return  # No map to save
        filename = f"{self.temp_dir}/map_turn_{self.current_turn}.png"
        self.map_image.save(filename)
        game_state = GameState(self.current_turn, filename)
        self.game_states.append(game_state)

    def save_game(self):
        if not self.map_image:
            messagebox.showwarning("No Map", "Please import or create a map before saving.")
            return
    
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if not file_path:
            return  # User cancelled the save operation
    
        try:
            self.is_saving = True
        
            # Convert current map image to base64
            buffered = io.BytesIO()
            self.map_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            game_data = {
                "game_name": self.game_name,
                "current_turn": self.current_turn,
                "players": [{
                    "name": player.name,
                    "color": player.color,
                    "faction": player.faction,
                    "allies": [ally.name for ally in player.allies],
                    "naps": [nap.name for nap in player.naps]
                } for player in self.players],
                "roll_table": {
                    "number_values": self.roll_table.number_values,
                    "repeats_config": self.roll_table.repeats_config,
                    "palindromes_config": self.roll_table.palindromes_config
                },
                "all_roll_results": self.all_roll_results,
                "roll_mode": self.roll_mode,
                "tile_owners": {f"{x},{y}": owner for (x, y), owner in self.tile_owners.items()},
                "player_rolls": self.player_rolls,
                "current_map_image": img_str
            }

            # Convert original map image to base64
            if self.original_map_image:
                buffered = io.BytesIO()
                self.original_map_image.save(buffered, format="PNG")
                original_img_str = base64.b64encode(buffered.getvalue()).decode()
                game_data["original_map_image"] = original_img_str

            # Use json.dumps with ensure_ascii=False to properly handle non-ASCII characters
            json_data = json.dumps(game_data, ensure_ascii=False, indent=4)

            # Write the JSON data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            messagebox.showinfo("Game Saved", f"Game has been saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Game", f"An error occurred while saving the game:\n{e}")
            print(f"Detailed error: {e}")  # This will print to console for debugging
        finally:
            self.is_saving = False

    def load_game(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return  # User cancelled the load operation

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)

            self.game_name = game_data.get("game_name", "Untitled Game")
            self.current_turn = game_data.get("current_turn", 0)
            self.players = []
            name_to_player = {}
            for pdata in game_data.get("players", []):
                player_color = tuple(pdata["color"])
                player = Player(pdata["name"], player_color, pdata.get("faction"))
                self.players.append(player)
                name_to_player[player.name] = player

            for pdata, player in zip(game_data.get("players", []), self.players):
                player.allies = [name_to_player[name] for name in pdata.get("allies", []) if name in name_to_player]
                player.naps = [name_to_player[name] for name in pdata.get("naps", []) if name in name_to_player]

            roll_table_data = game_data.get("roll_table", {})
            self.roll_table.number_values = roll_table_data.get("number_values", self.roll_table.number_values)
            self.roll_table.repeats_config = roll_table_data.get("repeats_config", self.roll_table.repeats_config)
            self.roll_table.palindromes_config = roll_table_data.get("palindromes_config", self.roll_table.palindromes_config)

            self.all_roll_results = game_data.get("all_roll_results", [])
            self.roll_mode = game_data.get("roll_mode", "application")
            self.player_rolls = game_data.get("player_rolls", {})

            # Load tile ownership
            self.tile_owners = {}
            for pos_str, owner in game_data.get("tile_owners", {}).items():
                x, y = map(int, pos_str.split(','))
                self.tile_owners[(x, y)] = owner

            # Load current map image
            if "current_map_image" in game_data:
                img_data = base64.b64decode(game_data["current_map_image"])
                self.map_image = Image.open(io.BytesIO(img_data)).convert("RGBA")
                self.map_draw = ImageDraw.Draw(self.map_image)

            # Load original map image
            if "original_map_image" in game_data:
                original_img_data = base64.b64decode(game_data["original_map_image"])
                self.original_map_image = Image.open(io.BytesIO(original_img_data)).convert("RGBA")

            self.update_all_screens()

            messagebox.showinfo("Game Loaded", "Game has been loaded successfully.")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Decode Error", f"The game file is corrupted or in an invalid format.\nError details: {str(e)}")
            print(f"Detailed JSON error: {e}")
        except Exception as e:
            messagebox.showerror("Error Loading Game", f"An error occurred while loading the game:\n{e}")
            print(f"Detailed error: {e}")

    def update_all_screens(self):
        if isinstance(self.current_screen, GameScreen):
            self.current_screen.display_map_image()
        elif isinstance(self.current_screen, PlayersScreen):
            self.current_screen.update_player_list()
        elif isinstance(self.current_screen, RollScreen):
            self.current_screen.display_roll_results()
            self.current_screen.display_all_roll_results()
        self.show_game_screen()  # Ensure the game screen is shown after loading

        def update_all_screens(self):
            if isinstance(self.current_screen, GameScreen):
                self.current_screen.display_map_image()
            elif isinstance(self.current_screen, PlayersScreen):
                self.current_screen.update_player_list()
            elif isinstance(self.current_screen, RollScreen):
                self.current_screen.display_roll_results()
                self.current_screen.display_all_roll_results()
            # Add other screen updates as necessary
            self.show_game_screen()  # Ensure the game screen is shown after loading

    def update_all_screens(self):
        if isinstance(self.current_screen, GameScreen):
            self.current_screen.display_map_image()
        elif isinstance(self.current_screen, PlayersScreen):
            self.current_screen.update_player_list()
        elif isinstance(self.current_screen, RollScreen):
            self.current_screen.display_roll_results()
            self.current_screen.display_all_roll_results()
        # Add other screen updates as necessary
        self.show_game_screen()  # Ensure the game screen is shown after loading

    def export_map(self):
        if self.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before exporting.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            self.map_image.save(file_path)
            messagebox.showinfo("Map Exported", "Map has been exported successfully.")

    def export_gif(self):
        if not self.game_states:
            messagebox.showwarning("No Game States", "No game states to export.")
            return
        frames = [Image.open(state.map_image_path) for state in self.game_states]
        file_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
        if file_path:
            frames[0].save(file_path, save_all=True, append_images=frames[1:], duration=500, loop=0)
            messagebox.showinfo("GIF Exported", "Game progression GIF has been exported successfully.")

    def on_closing(self):
        self.cleanup()
        self.master.quit()

    def cleanup(self):
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
                
    def on_closing(self):
        if self.is_saving:
            if messagebox.askokcancel("Saving in Progress", "The game is currently being saved. Are you sure you want to exit?"):
                self.master.destroy()
        else:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.cleanup()
                self.master.destroy()
                
    def on_closing(self):
        self.on_closing()
        
    def validate_player_data(self, name, color, faction):
        """
        Validates the player data.
        
        Args:
            name (str): Player's name.
            color (tuple): Player's color as an (R, G, B) tuple.
            faction (str or None): Player's faction.
        
        Returns:
            tuple: (validated_name, color, faction)
        
        Raises:
            ValueError: If any validation fails.
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Player name cannot be empty.")
        name = name.strip()
        for player in self.players:
            if player.name.lower() == name.lower():
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
    
    def capture_tile(self, x, y, new_owner):
        old_owner = self.tile_owners.get((x, y))
        if old_owner and old_owner != new_owner:
            if (x, y) in self.fortified_tiles:
                # Capturing a fortified tile costs 2 tiles
                self.update_player_tiles(new_owner, -2)
                del self.fortified_tiles[(x, y)]
            else:
                # Normal capture costs 1 tile
                self.update_player_tiles(new_owner, -1)
        self.tile_owners[(x, y)] = new_owner

if __name__ == "__main__":
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
