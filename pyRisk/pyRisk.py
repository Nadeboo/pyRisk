import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import json
import base64
import io
import shutil

from player import Player
from game_state import GameState
from roll_table import RollTable

# Import the screen classes
from game_screen import GameScreen
from players_screen import PlayersScreen
from alliances_screen import AlliancesScreen
from roll_screen import RollScreen

class MSPaintRiskEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("MSPaint Risk Editor")
        # Initialize shared data
        self.map_image = self.original_map_image = self.map_photo = self.map_draw = None
        self.players = []
        self.game_states = []
        self.roll_results = []
        self.all_roll_results = []
        self.current_turn = 0
        self.selected_player = None
        self.game_name = "Untitled Game"
        self.mode = 'color'
        self.map_history = []
        self.max_history = 20
        self.roll_table = RollTable()
        self.player_rolls = {}
        self.tile_owners = {}
        self.temp_dir = "temp_images"
        os.makedirs(self.temp_dir, exist_ok=True)
        # Setup GUI
        self.setup_menu()
        self.setup_topbar()
        self.content_frame = tk.Frame(self.master)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        # Initialize current screen
        self.current_screen = None
        self.show_game_screen()

    def setup_menu(self):
        menu_bar = tk.Menu(self.master)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        for label, cmd in [("Import Map", self.import_map), ("Save Game", self.save_game), ("Load Game", self.load_game),
                           ("Export Map as PNG", self.export_map), ("Export GIF of Game Progression", self.export_gif),
                           ("Exit", self.on_exit)]:
            file_menu.add_command(label=label, command=cmd)
            if label in ["Load Game", "Export GIF of Game Progression"]:
                file_menu.add_separator()
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.master.config(menu=menu_bar)

    def setup_topbar(self):
        self.topbar = tk.Frame(self.master)
        self.topbar.pack(side=tk.TOP, fill=tk.X)
        for text, cmd in [("Game", self.show_game_screen), ("Players", self.show_players_screen),
                          ("Alliances", self.show_alliances_screen), ("Roll", self.show_roll_screen)]:
            tk.Button(self.topbar, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

    def show_game_screen(self):
        self.switch_screen(GameScreen)

    def show_players_screen(self):
        self.switch_screen(PlayersScreen)

    def show_alliances_screen(self):
        self.switch_screen(AlliancesScreen)

    def show_roll_screen(self):
        self.switch_screen(RollScreen)

    def switch_screen(self, screen_class):
        # Destroy current screen if it exists
        if self.current_screen:
            self.current_screen.destroy()
        # Initialize new screen
        self.current_screen = screen_class(self.content_frame, self)

    def import_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.bmp;*.jpg;*.jpeg")])
        if file_path:
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in ['.jpg', '.jpeg']:
                response = messagebox.askokcancel("Warning", "JPEG files may cause artifacts due to compression. It's recommended to use PNG or BMP files. Do you want to continue?")
                if not response:
                    return
            self.map_image = Image.open(file_path).convert("RGBA")
            self.map_draw = ImageDraw.Draw(self.map_image)
            self.original_map_image = self.map_image.copy()
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
                "game_states": [],
                "roll_table": {
                    "number_values": self.roll_table.number_values,
                    "repeats_config": self.roll_table.repeats_config,
                    "palindromes_config": self.roll_table.palindromes_config
                },
                "all_roll_results": self.all_roll_results
            }

            # Save map images as base64 encoded strings
            for state in self.game_states:
                try:
                    with open(state.map_image_path, "rb") as img_file:
                        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                        game_data["game_states"].append({
                            "turn_number": state.turn_number,
                            "image_data": encoded_string
                        })
                except FileNotFoundError:
                    messagebox.showwarning("Image Not Found", f"Map image for turn {state.turn_number} not found. This turn's map will not be saved.")

            # Save the game data
            with open(file_path, 'w') as f:
                json.dump(game_data, f)
            messagebox.showinfo("Game Saved", "Game has been saved successfully.")

    def load_game(self):
        file_path = filedialog.askopenfilename(filetypes=[("MSPaint Risk Game files", "*.mprg")])
        if not file_path:
            return  # User cancelled file selection
        try:
            game_data = self.load_json_with_limit(file_path)
        
            # Load game metadata
            self.game_name = game_data.get("game_name", "Untitled Game")
            self.current_turn = game_data.get("current_turn", 0)
        
            # Load players
            self.players = []
            name_to_player = {}
            for pdata in game_data.get("players", []):
                player = Player(pdata["name"], tuple(pdata["color"]), pdata.get("faction"))
                self.players.append(player)
                name_to_player[player.name] = player
        
            # Set up alliances and NAPs
            for pdata, player in zip(game_data.get("players", []), self.players):
                player.allies = [name_to_player[name] for name in pdata.get("allies", [])]
                player.naps = [name_to_player[name] for name in pdata.get("naps", [])]
        
            # Load game states (map images)
            self.game_states = []
            for state_data in game_data.get("game_states", []):
                turn_number = state_data["turn_number"]
                try:
                    image_data = base64.b64decode(state_data["image_data"])
                
                    # Validate image data before processing
                    if not self.is_valid_image(image_data):
                        raise ValueError("Invalid image data")

                    image = Image.open(io.BytesIO(image_data))
                
                    # Additional validation after opening
                    if image.format not in ['PNG', 'BMP']:
                        raise ValueError(f"Unsupported image format: {image.format}")

                    temp_path = os.path.join(self.temp_dir, f"map_turn_{turn_number}.png")
                    image.save(temp_path, format='PNG')  # Force save as PNG
                    state = GameState(turn_number, temp_path)
                    self.game_states.append(state)
                except (ValueError, IOError, SyntaxError) as e:
                    messagebox.showwarning("Invalid Image Data", f"Map image for turn {turn_number} could not be loaded: {str(e)}")
        
            # Load the current map state
            if self.game_states:
                last_state = self.game_states[-1]
                self.map_image = Image.open(last_state.map_image_path)
                self.map_draw = ImageDraw.Draw(self.map_image)
                if isinstance(self.current_screen, GameScreen):
                    self.current_screen.display_map_image()
                else:
                    self.show_game_screen()
            else:
                messagebox.showwarning("No Map Data", "No valid map data found in the save file.")
        
            # Load roll table configuration
            roll_table_data = game_data.get("roll_table", {})
            if roll_table_data:
                self.roll_table.number_values = roll_table_data.get("number_values", self.roll_table.number_values)
                self.roll_table.repeats_config = roll_table_data.get("repeats_config", self.roll_table.repeats_config)
                self.roll_table.palindromes_config = roll_table_data.get("palindromes_config", self.roll_table.palindromes_config)
        
            # Load roll results history
            self.all_roll_results = game_data.get("all_roll_results", [])
        
            # Update UI elements
            if hasattr(self, 'update_player_buttons'):
                self.update_player_buttons()
        
            messagebox.showinfo("Game Loaded", "Game has been loaded successfully.")
    
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except json.JSONDecodeError:
            messagebox.showerror("Error", "The selected file is not a valid MPRG file.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while loading the game: {str(e)}")

    def load_json_with_limit(self, file_path, max_size=10 * 1024 * 1024):  # 10 MB limit
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise ValueError(f"File size exceeds the maximum allowed size of {max_size} bytes")
        with open(file_path, 'r') as f:
            return json.load(f)

    def is_valid_image(self, data):
        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
            return True
        except:
            return False

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
                print(f"Error deleting {file_path}: {e}")
    
        # Optionally, you can remove the temp_dir itself if it's empty
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass  # Directory not empty or other error, ignore

    def validate_player_data(self, name, color, faction):
        if not isinstance(name, str) or len(name) > 50:
            raise ValueError("Invalid player name")
        if not isinstance(color, tuple) or len(color) != 3 or not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
            raise ValueError("Invalid color format")
        if faction and (not isinstance(faction, str) or len(faction) > 50):
            raise ValueError("Invalid faction name")
        return name, color, faction

if __name__ == "__main__":
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()