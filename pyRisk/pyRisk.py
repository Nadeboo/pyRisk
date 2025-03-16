import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import json
import sys
import time

# Add parent directory to path when run as main script
if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from pyRisk.player import Player
    from pyRisk.game_state import GameState
    from pyRisk.roll_table import RollTable
    from pyRisk.unit import Unit, UnitType
    from pyRisk.save_load_manager import SaveLoadManager
    from pyRisk.game_screen import GameScreen
    from pyRisk.players_screen import PlayersScreen
    from pyRisk.alliances_screen import AlliancesScreen
    from pyRisk.roll_screen import RollScreen
    from pyRisk.units_screen import UnitsScreen
    from pyRisk.research_screen import ResearchScreen
    from pyRisk.cities_screen import CitiesScreen
else:
    from .player import Player
    from .game_state import GameState
    from .roll_table import RollTable
    from .unit import Unit, UnitType
    from .save_load_manager import SaveLoadManager
    from .game_screen import GameScreen
    from .players_screen import PlayersScreen
    from .alliances_screen import AlliancesScreen
    from .roll_screen import RollScreen
    from .units_screen import UnitsScreen
    from .research_screen import ResearchScreen
    from .cities_screen import CitiesScreen

class MSPaintRiskEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("MSPaint Risk Editor")
        self.master.geometry("1024x768")
        self.roll_mode = 'tregonia'  # Always use Tregonia mode
        self.map_photo = None  # Initialize map_photo as None
        self.setup_menu()
        self.setup_ui()
        self.initialize_variables()
        self.resource_tiles = {}
        self.RESOURCE_COLOR = (255, 255, 0)  # RGB for #45AD22
        
        # Setup memory monitoring
        self.memory_monitoring = False
        self.memory_log_file = None
        
        # Automatically load the map
        self.load_default_map()
        
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
            self.placed_sprites = {}  # Store sprite data
            
            # Initialize Tregonia-specific variables here if needed
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
            
    def setup_menu(self):
        """Setup the application menu"""
        menubar = tk.Menu(self.master)
        
        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Import Map", command=self.import_map)
        filemenu.add_command(label="Save Game", command=self.save_game)
        filemenu.add_command(label="Load Game", command=self.load_game)
        filemenu.add_command(label="Export GIF", command=self.export_gif)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        # Tools menu
        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Clear All Territory", command=self.clear_all_territory)
        toolsmenu.add_command(label="Clear Image Caches", command=self.clear_image_caches)
        menubar.add_cascade(label="Tools", menu=toolsmenu)
        
        # Debug menu
        debugmenu = tk.Menu(menubar, tearoff=0)
        debugmenu.add_command(label="Toggle Memory Monitoring", command=self.toggle_memory_monitoring)
        debugmenu.add_command(label="Print Memory Usage", command=self.print_memory_usage)
        menubar.add_cascade(label="Debug", menu=debugmenu)
        
        self.master.config(menu=menubar)

    def setup_ui(self):
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar frame
        self.toolbar = tk.Frame(self.main_frame)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Create single content frame
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.setup_toolbar_buttons()

    def setup_toolbar_buttons(self):
        # Remove existing toolbar buttons
        for widget in self.toolbar.winfo_children():
            widget.destroy()
        # Create toolbar buttons
        buttons = [
            ("Game", self.show_game_screen),
            ("Players", self.show_players_screen),
            ("Cities", self.show_cities_screen),
            ("Alliances", self.show_alliances_screen),
            ("Research", self.show_research_screen),
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
        
        # Use a more efficient scanning approach - scan in blocks
        block_size = 4  # Check every 4th pixel initially
        candidate_pixels = []
        
        # First pass: find candidate pixels using a grid approach
        for x in range(0, map_width, block_size):
            for y in range(0, map_height, block_size):
                if (x, y) not in checked_pixels:
                    pixel = pixels[x, y]
                    if len(pixel) == 4:
                        pixel = pixel[:3]
                    
                    if pixel == self.RESOURCE_COLOR:
                        candidate_pixels.append((x, y))
        
        # Second pass: process candidate pixels to find full structures
        for x, y in candidate_pixels:
            if (x, y) not in checked_pixels:
                connected_pixels = self.find_connected_resource(x, y, pixels, checked_pixels, map_width, map_height)
                if connected_pixels and len(connected_pixels) > 0:
                    # Calculate the center of the structure more efficiently
                    x_sum = sum(x for x, _ in connected_pixels)
                    y_sum = sum(y for _, y in connected_pixels)
                    count = len(connected_pixels)
                    avg_x = x_sum // count
                    avg_y = y_sum // count
                    
                    # Store the center as the resource location
                    self.resource_tiles[(avg_x, avg_y)] = {'type': 'gold', 'amount': 1}
                    resource_structures.append(connected_pixels)
        
        print(f"Found {len(resource_structures)} distinct resource structures")

    def find_connected_resource(self, x, y, pixels, checked_pixels, map_width, map_height):
        """Find all connected resource pixels starting from x,y using an iterative approach"""
        if (x, y) in checked_pixels:
            return set()
            
        pixel = pixels[x, y]
        if len(pixel) == 4:
            pixel = pixel[:3]
            
        if pixel != self.RESOURCE_COLOR:
            return set()
            
        # This is a resource pixel we haven't checked
        connected = set()
        stack = [(x, y)]
        
        while stack:
            current_x, current_y = stack.pop()
            
            if (current_x, current_y) in checked_pixels:
                continue
                
            # Add to connected set and mark as checked
            connected.add((current_x, current_y))
            checked_pixels.add((current_x, current_y))
            
            # Check adjacent pixels
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                new_x, new_y = current_x + dx, current_y + dy
                if 0 <= new_x < map_width and 0 <= new_y < map_height:
                    if (new_x, new_y) not in checked_pixels:
                        new_pixel = pixels[new_x, new_y]
                        if len(new_pixel) == 4:
                            new_pixel = new_pixel[:3]
                        
                        if new_pixel == self.RESOURCE_COLOR:
                            stack.append((new_x, new_y))
                
        return connected

    def show_game_screen(self):
        self.switch_screen(GameScreen)

    def show_players_screen(self):
        self.switch_screen(PlayersScreen)

    def show_alliances_screen(self):
        self.switch_screen(AlliancesScreen)

    def show_research_screen(self):
        self.switch_screen(ResearchScreen)

    def show_cities_screen(self):
        self.switch_screen(CitiesScreen)

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
        # Show toolbar
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.setup_toolbar_buttons()
        # Initialize new screen
        self.current_screen = screen_class(self.content_frame, self)

    def import_map(self):
        """Import and initialize a new map image with detailed error logging to file"""
        import traceback
        import datetime
        
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
            
            if not file_path:
                return
                
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
            # Only create error log when an actual error occurs
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"error_log_{timestamp}.txt"
            
            # Log the full error details
            with open(log_file, 'w') as f:
                f.write("\nERROR OCCURRED DURING MAP IMPORT:\n")
                f.write(f"Error type: {type(e).__name__}\n")
                f.write(f"Error message: {str(e)}\n")
                f.write(f"Map file: {file_path if 'file_path' in locals() else 'Not selected'}\n\n")
                f.write("Full stack trace:\n")
                traceback.print_exc(file=f)
                
                # Log additional state information
                f.write("\nApplication State:\n")
                f.write(f"Roll mode: {self.roll_mode}\n")
                f.write(f"Current turn: {self.current_turn}\n")
                f.write(f"Number of players: {len(self.players)}\n")
                f.write(f"Map image exists: {self.map_image is not None}\n")
                if hasattr(self, 'current_screen'):
                    f.write(f"Current screen type: {type(self.current_screen).__name__}\n")
            
            error_msg = f"Error loading image: {str(e)}\nCheck {log_file} for full error details."
            messagebox.showerror("Error Loading Image", error_msg)


    def save_current_map_state(self):
        """Save the current map state including any units"""
        if self.map_image is None:
            return  # No map to save
                
        filename = f"{self.temp_dir}/map_turn_{self.current_turn}.png"
        
        # Create a copy of the base map to save
        save_image = self.map_image.copy()
        draw = ImageDraw.Draw(save_image)
        
        # If in Tregonia mode and there are units, draw them onto the save image
        if self.roll_mode == 'tregonia' and hasattr(self, 'units'):
            try:
                unit_font = ImageFont.truetype("arial.ttf", 16)
            except IOError:
                unit_font = ImageFont.load_default()
                
            for unit in self.units:
                if unit.position:
                    x, y = unit.position
                    owner = next((p for p in self.players if p.name == unit.owner), None)
                    owner_color = owner.color if owner else (128, 128, 128)
                    
                    # Draw unit rectangle
                    draw.rectangle(
                        [x - 3, y - 3, x + 23, y + 23],
                        fill='white', outline='black'
                    )
                    # Draw unit ID
                    draw.text(
                        (x + 10, y + 10),
                        str(unit.unit_id),
                        font=unit_font,
                        fill='black',
                        anchor='mm'
                    )
                    # Draw owner color bar
                    draw.rectangle(
                        [x - 3, y + 24, x + 23, y + 28],
                        fill=owner_color,
                        outline='black'
                    )
        
        # Save the image with units drawn on it
        save_image.save(filename)
                
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
            # Clear previous resource sources
            player.clear_resource_sources()
            
            # Set base resource gains for all players
            player.gold_per_turn = 1  # Base 1 gold per turn
            player.research_per_turn = 2  # Base 2 research per turn
            player.mana_per_turn = 0
            player.influence_per_turn = 0
            
            # Track base resource gains
            player.add_resource_source('gold', 1, 'Base income')
            player.add_resource_source('research', 2, 'Base income')
            
            # Apply race-specific bonuses
            if player.faction == "HUMAN":
                player.influence_per_turn += 1  # Humans get +1 influence
                player.add_resource_source('influence', 1, 'Human race bonus')
                print(f"Added +1 influence/turn for {player.name} (HUMAN)")
            elif player.faction == "WIZARD":
                player.mana_per_turn += 1  # Wizards get +1 mana
                player.add_resource_source('mana', 1, 'Wizard race bonus')
                print(f"Added +1 mana/turn for {player.name} (WIZARD)")
            
            # Apply region bonus to influence
            if player.region_bonus > 0:
                player.influence_per_turn += player.region_bonus
                player.add_resource_source('influence', player.region_bonus, 'Region bonus')
                print(f"Added +{player.region_bonus} influence/turn for {player.name} (Region bonus)")
                
            print(f"Reset {player.name}'s resources to base values")
            
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
                        player.add_resource_source('gold', 1, f'Gold tile at {pos}')
                        print(f"Added 1 gold/turn to {player.name}")
                    elif resource_type == 'mana':
                        player.mana_per_turn += 1
                        player.add_resource_source('mana', 1, f'Mana tile at {pos}')
                        print(f"Added 1 mana/turn to {player.name}")
                    print(f"{player.name} now has {player.gold_per_turn} gold/turn, {player.research_per_turn} research/turn, {player.mana_per_turn} mana/turn, and {player.influence_per_turn} influence/turn")

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
        from pyRisk.save_load_manager import SaveLoadManager
        SaveLoadManager.save_game(self)

    def load_game(self):
        from pyRisk.save_load_manager import SaveLoadManager
        SaveLoadManager.load_game(self)

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
        """Clean up temporary files and release memory resources"""
        # Clean up temporary files
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        # Clear image caches
        self.clear_image_caches()
        
        # Force garbage collection
        import gc
        gc.collect()
    
    def clear_image_caches(self):
        """Clear all image caches to free up memory"""
        # Clear main image references
        if hasattr(self, 'map_photo') and self.map_photo:
            self.map_photo = None
        
        # Clear original map image if it exists
        if hasattr(self, 'original_map_image') and self.original_map_image:
            self.original_map_image = None
        
        # Clear map history
        self.map_history.clear()
        
        # Clear screen caches if they exist
        if self.current_screen and hasattr(self.current_screen, '_cached_base_image'):
            self.current_screen._cached_base_image = None
            
        # Clear any cached images in placed sprites
        if hasattr(self, 'placed_sprites'):
            for sprite_info in self.placed_sprites.values():
                if hasattr(sprite_info, 'extra_data') and sprite_info.extra_data:
                    if 'colored_sprite' in sprite_info.extra_data:
                        sprite_info.extra_data['colored_sprite'] = None

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

    def load_default_map(self):
        """Load the default map_cut.png from sprites folder with optimized performance"""
        import traceback
        import os
        
        try:
            # Construct path to map_cut.png in sprites folder
            file_path = os.path.join("sprites", "map_cut.png")
            
            if not os.path.exists(file_path):
                print(f"Warning: Default map file not found at {file_path}")
                return
            
            # Check if we already have this map loaded (avoid reloading the same map)
            if hasattr(self, '_loaded_map_path') and self._loaded_map_path == file_path and self.map_image is not None:
                print("Map already loaded, skipping reload")
                return
                
            # Load image
            img = Image.open(file_path)
            
            # Clear any existing image caches
            self.clear_image_caches()
            
            # Convert image to RGBA
            self.map_image = img.convert("RGBA")
            self.map_draw = ImageDraw.Draw(self.map_image)
            self.original_map_image = self.map_image.copy()
            self.tile_owners = {}
            
            # Store the loaded map path
            self._loaded_map_path = file_path
            
            # Scan for resource tiles
            self.scan_for_resource_tiles()
            
            # Show game screen
            self.show_game_screen()
            
            # Save initial map state
            self.save_current_map_state()
            self.map_history.clear()
                
        except Exception as e:
            # Only create error log when an actual error occurs
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"error_log_{timestamp}.txt"
            
            # Log the full error details
            with open(log_file, 'w') as f:
                f.write("\nERROR OCCURRED DURING DEFAULT MAP LOAD:\n")
                f.write(f"Error type: {type(e).__name__}\n")
                f.write(f"Error message: {str(e)}\n")
                f.write(f"Map file: {file_path if 'file_path' in locals() else 'Unknown'}\n\n")
                f.write("Full stack trace:\n")
                traceback.print_exc(file=f)
                
                # Log additional state information
                f.write("\nApplication State:\n")
                f.write(f"Roll mode: {self.roll_mode}\n")
                f.write(f"Current turn: {self.current_turn}\n")
                f.write(f"Number of players: {len(self.players)}\n")
                f.write(f"Map image exists: {self.map_image is not None}\n")
                if hasattr(self, 'current_screen'):
                    f.write(f"Current screen type: {type(self.current_screen).__name__}\n")
            
            print(f"Error loading default map: {str(e)}")
            print(f"Check {log_file} for full error details.")

    def toggle_memory_monitoring(self):
        """Toggle memory usage monitoring"""
        self.memory_monitoring = not self.memory_monitoring
        
        if self.memory_monitoring:
            # Start memory monitoring
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.memory_log_file = f"memory_log_{timestamp}.txt"
            
            with open(self.memory_log_file, 'w') as f:
                f.write("Memory Monitoring Started\n")
                f.write(f"Timestamp: {timestamp}\n\n")
                f.write("Time,Total Memory (MB),Available Memory (MB),Used Memory (MB),Action\n")
            
            # Schedule periodic memory logging
            self.log_memory_usage("Memory monitoring started")
            self.master.after(10000, self.periodic_memory_log)
            
            messagebox.showinfo("Memory Monitoring", "Memory monitoring has been enabled.")
        else:
            # Stop memory monitoring
            if self.memory_log_file:
                with open(self.memory_log_file, 'a') as f:
                    f.write("\nMemory Monitoring Stopped\n")
                self.memory_log_file = None
            messagebox.showinfo("Memory Monitoring", "Memory monitoring has been disabled.")
    
    def periodic_memory_log(self):
        """Log memory usage periodically"""
        if self.memory_monitoring:
            self.log_memory_usage("Periodic check")
            self.master.after(10000, self.periodic_memory_log)
    
    def log_memory_usage(self, action=""):
        """Log current memory usage to file"""
        if not self.memory_log_file:
            return
            
        try:
            import psutil
            import datetime
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.memory_log_file, 'a') as f:
                f.write(f"{timestamp},{system_memory.total/1024/1024:.2f},{system_memory.available/1024/1024:.2f},{memory_info.rss/1024/1024:.2f},{action}\n")
        except ImportError:
            print("psutil module not available for memory monitoring")
        except Exception as e:
            print(f"Error logging memory usage: {e}")
    
    def print_memory_usage(self):
        """Display current memory usage in a message box"""
        try:
            import psutil
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            
            message = f"Process Memory Usage: {memory_info.rss/1024/1024:.2f} MB\n"
            message += f"System Memory: {system_memory.total/1024/1024:.2f} MB total, {system_memory.available/1024/1024:.2f} MB available"
            
            messagebox.showinfo("Memory Usage", message)
            
            # Log this check
            self.log_memory_usage("Manual memory check")
        except ImportError:
            messagebox.showwarning("Memory Usage", "psutil module not available for memory monitoring")
        except Exception as e:
            messagebox.showerror("Error", f"Error getting memory usage: {e}")

    def clear_all_territory(self):
        """Clear all territory ownership from the map"""
        if not self.map_image:
            messagebox.showinfo("No Map", "No map is currently loaded.")
            return
            
        # Confirm with user
        if not messagebox.askyesno("Clear Territory", "Are you sure you want to clear all territory ownership?"):
            return
            
        # Clear tile owners
        self.tile_owners.clear()
        
        # Log this action if memory monitoring is enabled
        self.log_memory_usage("Cleared all territory")
        
        # Update the display
        if self.current_screen and hasattr(self.current_screen, 'display_map_image'):
            self.current_screen.display_map_image()
            
        messagebox.showinfo("Territory Cleared", "All territory ownership has been cleared.")

def main():
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()

if __name__ == "__main__":
    main()
