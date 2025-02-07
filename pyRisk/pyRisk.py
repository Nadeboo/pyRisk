
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw
import os
import json

from player import Player
from game_state import GameState
from roll_table import RollTable
from unit import Unit, UnitType
from save_load_manager import SaveLoadManager

# Import the screen classes
from game_screen import GameScreen
from players_screen import PlayersScreen
from alliances_screen import AlliancesScreen
from roll_screen import RollScreen
from start_screen import StartScreen
from units_screen import UnitsScreen


class MSPaintRiskEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("MSPaint Risk Editor")
        self.master.geometry("1024x768")
        self.roll_mode = None  # Will be set by the StartScreen
        self.map_photo = None  # Initialize map_photo as None
        self.setup_menu()
        self.setup_ui()
        self.initialize_variables()
        self.show_start_screen()  # Start with the StartScreen
        self.resource_tiles = {}
        self.RESOURCE_COLOR = (255, 255, 0)  # RGB for #45AD22

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
        self.mode = 'color'
        self.selected_player = None
        self.units = []  # Initialize empty units list
        self.next_unit_id = 1  # Start unit IDs at 1
        
        # Initialize Tregonia-specific variables here if needed
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
    def setup_menu(self):
        self.menu_bar = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Import Map", command=self.import_map)
        self.file_menu.add_command(label="Export Map", command=self.export_map)
        self.file_menu.add_command(label="Export GIF", command=self.export_gif)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save Game", command=self.save_game)
        self.file_menu.add_command(label="Load Game", command=self.load_game)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_exit)
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
        buttons = [
            ("Game", self.show_game_screen),
            ("Players", self.show_players_screen),
            ("Alliances", self.show_alliances_screen),
            ("Roll", self.show_roll_screen),
            ("Armies", self.show_units_screen)
        ]
        for text, cmd in buttons:
            btn = tk.Button(self.toolbar, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)


    def scan_for_resource_tiles(self):
        """Scan the map for resource tiles based on color, grouping adjacent pixels"""
        if not self.map_image or self.roll_mode != 'tregonia':
            return
            
        self.resource_tiles.clear()
        pixels = self.map_image.load()
        map_width, map_height = self.map_image.size
        
        # Keep track of which pixels we've checked
        checked_pixels = set()

        # Find all resource structures
        resource_structures = []
        for x in range(map_width):
            for y in range(map_height):
                if (x, y) not in checked_pixels:
                    pixel = pixels[x, y]
                    if len(pixel) == 4:
                        pixel = pixel[:3]
                    
                    if pixel == self.RESOURCE_COLOR:
                        # Found a new resource structure
                        connected_pixels = self.find_connected_resource(x, y, pixels, checked_pixels, map_width, map_height)
                        if connected_pixels:
                            # Calculate the center of the structure
                            avg_x = sum(x for x, _ in connected_pixels) // len(connected_pixels)
                            avg_y = sum(y for _, y in connected_pixels) // len(connected_pixels)
                            # Store the center as the resource location
                            self.resource_tiles[(avg_x, avg_y)] = {'type': 'gold', 'amount': 1}
                            resource_structures.append(connected_pixels)
        
        print(f"Found {len(resource_structures)} distinct resource structures")

    def find_connected_resource(self, x, y, pixels, checked_pixels, map_width, map_height):
        """Find all connected resource pixels starting from x,y"""
        if (x, y) in checked_pixels:
            return set()
            
        pixel = pixels[x, y]
        if len(pixel) == 4:
            pixel = pixel[:3]
            
        if pixel != self.RESOURCE_COLOR:
            return set()
            
        # This is a resource pixel we haven't checked
        connected = {(x, y)}
        checked_pixels.add((x, y))
        
        # Check adjacent pixels
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < map_width and 0 <= new_y < map_height:
                connected.update(self.find_connected_resource(new_x, new_y, pixels, checked_pixels, map_width, map_height))
                
        return connected

    def show_start_screen(self):
        self.switch_screen(StartScreen)

    def show_game_screen(self):
        self.switch_screen(GameScreen)

    def show_players_screen(self):
        self.switch_screen(PlayersScreen)

    def show_alliances_screen(self):
        self.switch_screen(AlliancesScreen)

    def show_roll_screen(self):
        if self.roll_mode == 'external':
            messagebox.showinfo("Disabled", "Rolling is disabled in external roll mode.")
            return
        self.switch_screen(RollScreen)

    def show_units_screen(self):
        if self.roll_mode != 'tregonia':
            messagebox.showinfo("Feature Unavailable", "Units management is only available in Tregonia mode.")
            return
        self.switch_screen(UnitsScreen)

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

    def import_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            try:
                # Load image
                img = Image.open(file_path)
                self.map_image = img.convert("RGBA")
                self.map_draw = ImageDraw.Draw(self.map_image)
                self.original_map_image = self.map_image.copy()
                self.tile_owners = {}
                
                # Scan for resource tiles if in Tregonia mode
                if self.roll_mode == 'tregonia':
                    self.scan_for_resource_tiles()
                
                if isinstance(self.current_screen, GameScreen):
                    self.current_screen.display_map_image()
                else:
                    self.show_game_screen()
                    
                self.save_current_map_state()
                self.map_history.clear()
                
            except Exception as e:
                messagebox.showerror("Error Loading Image", str(e))


    def save_current_map_state(self):
        if self.map_image is None:
            return  # No map to save
            
        filename = f"{self.temp_dir}/map_turn_{self.current_turn}.png"
        
        # Create temporary image with units rendered
        if self.current_screen and hasattr(self.current_screen, 'display_map_image'):
            # Store current zoom
            current_zoom = self.current_screen.zoom_level
            # Set zoom to 1.0 for saving
            self.current_screen.zoom_level = 1.0
            self.current_screen.invalidate_display_cache()
            # Generate the image
            self.current_screen.display_map_image()
            # Get and save the complete image with units
            export_image = ImageTk.getimage(self.app.map_photo)
            export_image.save(filename)
            # Restore zoom
            self.current_screen.zoom_level = current_zoom
            self.current_screen.display_map_image()
        else:
            # Fallback if no display screen
            self.map_image.save(filename)
            
        # Create game state and save unit positions
        game_state = GameState(self.current_turn, filename)
        if self.roll_mode == 'tregonia':
            game_state.save_unit_state(self.units)
        self.game_states.append(game_state)

    def update_player_resources(self):
        """Update resource gains for all players based on controlled tiles"""
        if self.roll_mode != 'tregonia':
            return
                
        print("\nUpdating player resources:")
        
        # Reset resource gains for all players
        for player in self.players:
            player.gold_per_turn = 0
            player.mana_per_turn = 0
            print(f"Reset {player.name}'s resources to 0")
            
        # Check each resource tile
        print(f"Processing {len(self.resource_tiles)} resource tiles")
        for pos, resource_info in self.resource_tiles.items():
            owner = resource_info.get('owner')
            resource_type = resource_info.get('type')
            
            print(f"Resource at {pos}: type={resource_type}, owner={owner}")
            
            if owner and resource_type:
                player = next((p for p in self.players if p.name == owner), None)
                if player:
                    if resource_type == 'gold':
                        player.gold_per_turn += 1
                        print(f"Added 1 gold/turn to {player.name}")
                    elif resource_type == 'mana':
                        player.mana_per_turn += 1
                        print(f"Added 1 mana/turn to {player.name}")
                    print(f"{player.name} now has {player.gold_per_turn} gold/turn and {player.mana_per_turn} mana/turn")

    def load_game_state(self, state):
        """Load a specific game state"""
        if os.path.exists(state.map_image_path):
            self.map_image = Image.open(state.map_image_path)
            self.map_draw = ImageDraw.Draw(self.map_image)
            
            # Restore unit positions for this turn
            if self.roll_mode == 'tregonia':
                state.restore_unit_state(self)
                
            # Update display
            if self.current_screen and hasattr(self.current_screen, 'display_map_image'):
                self.current_screen.invalidate_display_cache()
                self.current_screen.display_map_image()

    def save_game(self):
        if not self.game_states:
            messagebox.showwarning("No Game to Save", "No game data to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".mprg",
                                                 filetypes=[("MSPaint Risk Game files", "*.mprg")])
        if file_path:
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
                "game_states": [state.map_image_path for state in self.game_states],
                "roll_table": {
                    "number_values": self.roll_table.number_values,
                    "repeats_config": self.roll_table.repeats_config,
                    "palindromes_config": self.roll_table.palindromes_config
                },
                "all_roll_results": self.all_roll_results,
                "roll_mode": self.roll_mode,
                "tile_owners": {f"{x},{y}": owner for (x, y), owner in self.tile_owners.items()}
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(game_data, f)
                messagebox.showinfo("Game Saved", "Game has been saved successfully.")
            except Exception as e:
                messagebox.showerror("Error Saving Game", f"An error occurred while saving the game:\n{e}")
                
    def load_game(self):
        file_path = filedialog.askopenfilename(filetypes=[("MSPaint Risk Game files", "*.mprg")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)
                self.game_name = game_data.get("game_name", "Untitled Game")
                self.current_turn = game_data.get("current_turn", 0)
                self.players = []
                name_to_player = {}
                for pdata in game_data.get("players", []):
                    player = Player(pdata["name"], pdata["color"], pdata.get("faction"))
                    self.players.append(player)
                    name_to_player[player.name] = player
                for pdata, player in zip(game_data.get("players", []), self.players):
                    player.allies = [name_to_player[name] for name in pdata.get("allies", []) if name in name_to_player]
                    player.naps = [name_to_player[name] for name in pdata.get("naps", []) if name in name_to_player]
                self.game_states = []
                for path in game_data.get("game_states", []):
                    turn_number = int(os.path.splitext(os.path.basename(path))[0].split('_')[-1])
                    state = GameState(turn_number, path)
                    self.game_states.append(state)
                if self.game_states:
                    last_state = self.game_states[-1]
                    self.map_image = Image.open(last_state.map_image_path).convert("RGBA")
                    self.map_draw = ImageDraw.Draw(self.map_image)
                    self.original_map_image = self.map_image.copy()
                    if isinstance(self.current_screen, GameScreen):
                        self.current_screen.display_map_image()
                    else:
                        self.show_game_screen()
                roll_table_data = game_data.get("roll_table", {})
                if roll_table_data:
                    self.roll_table.number_values = roll_table_data.get("number_values", self.roll_table.number_values)
                    self.roll_table.repeats_config = roll_table_data.get("repeats_config", self.roll_table.repeats_config)
                    self.roll_table.palindromes_config = game_data.get("roll_table", {}).get("palindromes_config",
                                                                                             self.roll_table.palindromes_config)
                self.all_roll_results = game_data.get("all_roll_results", [])
                self.roll_mode = game_data.get("roll_mode", "application")
                # Load tile ownership
                tile_owners_data = game_data.get("tile_owners", {})
                self.tile_owners = {}
                for pos_str, owner in tile_owners_data.items():
                    x, y = map(int, pos_str.split(','))
                    self.tile_owners[(x, y)] = owner
                messagebox.showinfo("Game Loaded", "Game has been loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error Loading Game", f"An error occurred while loading the game:\n{e}")



    def export_map(self):
            if self.map_image is None:
                messagebox.showwarning("No Map Loaded", "Please import a map before exporting.")
                return

            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if file_path:
                if hasattr(self.current_screen, 'zoom_level'):
                    # Store current zoom level
                    original_zoom = self.current_screen.zoom_level
                    # Set zoom to 1.0 for export
                    self.current_screen.zoom_level = 1.0
                    # Clear the display cache to force a redraw
                    self.current_screen.invalidate_display_cache()
                    # Call display_map_image but get the image instead of displaying it
                    self.current_screen.display_map_image()
                    # Get the final composed image from the PhotoImage
                    export_image = ImageTk.getimage(self.map_photo)
                    # Save it
                    export_image.save(file_path)
                    # Restore original zoom
                    self.current_screen.zoom_level = original_zoom
                    # Restore the display
                    self.current_screen.display_map_image()
                else:
                    # If no current screen with zoom, just save the map image directly
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

    def on_exit(self):
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


if __name__ == "__main__":
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()
