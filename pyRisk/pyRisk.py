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
    
    # Direct import when run as a script
    from custom_scrollbar import CustomScrollbar
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
    # Package import when imported as a module
    from .custom_scrollbar import CustomScrollbar
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
        
        # Global scrollbar styling
        self.master.option_add("*Scrollbar.Background", "#3C3F41")
        self.master.option_add("*Scrollbar.foreground", "#5A5D5F")
        self.master.option_add("*Scrollbar.activeBackground", "#5A5D5F")
        self.master.option_add("*Scrollbar.troughColor", "#3C3F41")
        self.master.option_add("*Scrollbar.borderWidth", "0")
        self.master.option_add("*Scrollbar.relief", "flat")
        
        # Configure global scrollbar style for dark theme
        self.master.tk_setPalette(
            background='#2B2B2B',      # Dark gray background
            foreground='#CCCCCC',      # Light gray text
            selectBackground='#4B6EAF', # Blue highlight
            selectForeground='#FFFFFF', # White highlight text
            activeBackground='#4B6EAF', # Blue active background
            activeForeground='#FFFFFF'  # White active text
        )
        
        # Style scrollbars globally
        self.master.option_add("*Scrollbar.Background", "#3C3F41")  # Dark scrollbar background
        self.master.option_add("*Scrollbar.troughColor", "#3C3F41")  # Dark scrollbar trough
        self.master.option_add("*Scrollbar.activeBackground", "#5A5D5F")  # Mid-gray active background
        self.master.option_add("*Scrollbar.highlightBackground", "#3C3F41")  # Dark highlight background
        self.master.option_add("*Scrollbar.highlightColor", "#3C3F41")  # Dark highlight color
        self.master.option_add("*Scrollbar.activeRelief", "flat")  # Flat relief when active
        self.master.option_add("*Scrollbar.borderWidth", 0)  # No border
        self.master.option_add("*Scrollbar.relief", "flat")  # Flat relief
        
        # Define theme colors for light and dark mode
        self.light_theme = {
            'bg': '#FFFFFF',  # White background
            'fg': '#000000',  # Black text
            'button_bg': '#F0F0F0',  # Light gray button background
            'button_fg': '#000000',  # Black button text
            'frame_bg': '#F5F5F5',  # Light gray frame background
            'canvas_bg': '#FFFFFF',  # White canvas background
            'highlight_bg': '#E0E0E0',  # Light gray highlight
            'highlight_fg': '#000000',  # Black highlight text
            'menu_bg': '#F0F0F0',  # Light gray menu background
            'menu_fg': '#000000',  # Black menu text
        }
        
        self.dark_theme = {
            'bg': '#2B2B2B',  # Dark gray background
            'fg': '#CCCCCC',  # Light gray text
            'button_bg': '#3C3F41',  # Mid-dark gray button background
            'button_fg': '#CCCCCC',  # Light gray button text
            'frame_bg': '#2B2B2B',  # Dark gray frame background
            'canvas_bg': '#2B2B2B',  # Dark gray canvas background
            'highlight_bg': '#4B6EAF',  # Blue highlight
            'highlight_fg': '#FFFFFF',  # White highlight text
            'menu_bg': '#3C3F41',  # Mid-dark gray menu background
            'menu_fg': '#CCCCCC',  # Light gray menu text
            'scrollbar_bg': '#2B2B2B',  # Dark gray scrollbar background (darker for better contrast)
            'scrollbar_fg': '#4A4D4F',  # Slightly lighter scrollbar slider (subtle but visible)
        }
        
        # Start with dark theme by default
        self.dark_mode = True
        self.current_theme = self.dark_theme
        
        self.setup_menu()
        self.setup_ui()
        self.initialize_variables()
        self.resource_tiles = {}
        # Resource colors for different resource types
        self.RESOURCE_COLORS = {
            'gold': (255, 255, 0),   # Yellow for gold
            'mana': (0, 0, 255)      # Blue for mana
            # Green resources are blank and not tracked
        }
        
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
        
        # View menu - Add Dark Mode toggle
        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        menubar.add_cascade(label="View", menu=viewmenu)
        
        # Debug menu
        debugmenu = tk.Menu(menubar, tearoff=0)
        debugmenu.add_command(label="Toggle Memory Monitoring", command=self.toggle_memory_monitoring)
        debugmenu.add_command(label="Print Memory Usage", command=self.print_memory_usage)
        menubar.add_cascade(label="Debug", menu=debugmenu)
        
        self.master.config(menu=menubar)
        
        # Apply theme to menus
        self.apply_theme_to_menu(menubar)

    def apply_theme_to_menu(self, menu):
        """Apply the current theme to a menu"""
        menu.config(bg=self.current_theme['menu_bg'], fg=self.current_theme['menu_fg'])
        
        # Apply to all cascaded menus
        for item_index in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
            try:
                item_type = menu.type(item_index)
                if item_type == 'cascade':
                    submenu = menu.nametowidget(menu.entrycget(item_index, 'menu'))
                    self.apply_theme_to_menu(submenu)
            except (tk.TclError, AttributeError):
                continue

    def setup_ui(self):
        self.main_frame = tk.Frame(self.master, bg=self.current_theme['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar frame
        self.toolbar = tk.Frame(self.main_frame, bg=self.current_theme['frame_bg'])
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Create single content frame
        self.content_frame = tk.Frame(self.main_frame, bg=self.current_theme['bg'])
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Apply the current theme to the root window
        self.master.configure(bg=self.current_theme['bg'])
        
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
            btn = tk.Button(self.toolbar, text=text, command=cmd,
                          bg=self.current_theme['button_bg'],
                          fg=self.current_theme['button_fg'],
                          activebackground=self.current_theme['highlight_bg'],
                          activeforeground=self.current_theme['highlight_fg'])
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.current_theme = self.dark_theme if self.dark_mode else self.light_theme
        
        # Apply the theme to all widgets
        self.apply_theme_to_all()
        
        # Update the current screen if it exists
        if self.current_screen:
            self.refresh_current_screen()
    
    def apply_theme_to_all(self):
        """Apply the current theme to all widgets in the application"""
        # Apply to root window
        self.master.configure(bg=self.current_theme['bg'])
        
        # Apply to main frame
        self.main_frame.configure(bg=self.current_theme['bg'])
        
        # Apply to toolbar
        self.toolbar.configure(bg=self.current_theme['frame_bg'])
        
        # Apply to toolbar buttons
        for widget in self.toolbar.winfo_children():
            if isinstance(widget, tk.Button):
                widget.configure(bg=self.current_theme['button_bg'], 
                                fg=self.current_theme['button_fg'],
                                activebackground=self.current_theme['highlight_bg'],
                                activeforeground=self.current_theme['highlight_fg'])
        
        # Apply to content frame
        self.content_frame.configure(bg=self.current_theme['bg'])
        
        # Apply to menus
        if hasattr(self.master, 'menubar'):
            self.apply_theme_to_menu(self.master.menubar)
        else:
            menubar = self.master.nametowidget(self.master.cget('menu'))
            self.apply_theme_to_menu(menubar)
            
    def refresh_current_screen(self):
        """Refresh the current screen with the new theme"""
        if not self.current_screen:
            return
            
        # Store the current screen class to reinitialize it
        current_screen_class = type(self.current_screen)
        
        # Destroy and recreate the current screen
        self.current_screen.destroy()
        self.current_screen = current_screen_class(self.content_frame, self)
        
        # If it's the game screen, trigger a redisplay of the map
        if hasattr(self.current_screen, 'display_map_image'):
            self.current_screen.invalidate_display_cache()
            self.current_screen.display_map_image()

    def scan_for_resource_tiles(self):
        """Scan the map for resource tiles based on color, grouping adjacent pixels"""
        if not self.map_image or self.roll_mode != 'tregonia':
            return
        
        print("\n=== Scanning for Resources ===")
        print(f"Looking for resources with colors: {self.RESOURCE_COLORS}")
            
        self.resource_tiles.clear()
        pixels = self.map_image.load()
        map_width, map_height = self.map_image.size
        
        print(f"Map dimensions: {map_width}x{map_height}")
        
        # Keep track of which pixels we've checked
        checked_pixels = set()

        # Track candidate pixels by resource type
        resource_candidates = {
            'gold': [],     # Yellow
            'mana': []      # Blue
            # Green resources are blank and not tracked
        }
        
        # Use a more efficient scanning approach
        block_size = 4  # Smaller block size for more thorough scan
        
        print("Starting first pass scan for resource pixels...")
        
        # First pass: find candidate pixels using a grid approach
        for x in range(0, map_width, block_size):
            for y in range(0, map_height, block_size):
                if (x, y) not in checked_pixels:
                    # Safely handle boundary cases
                    if x < map_width and y < map_height:
                        try:
                            pixel = pixels[x, y]
                            if len(pixel) == 4:  # RGBA
                                pixel = pixel[:3]  # Convert to RGB
                            
                            r, g, b = pixel
                            
                            # Check for each resource color with tolerance
                            if r > 200 and g > 200 and b < 100:  # Yellow (gold)
                                resource_candidates['gold'].append((x, y))
                                checked_pixels.add((x, y))
                            elif r < 100 and g < 100 and b > 200:  # Blue (mana)
                                resource_candidates['mana'].append((x, y))
                                checked_pixels.add((x, y))
                            # Green resources are blank and not tracked
                        except Exception as e:
                            print(f"Error accessing pixel at ({x}, {y}): {e}")
        
        # Report found candidate pixels
        total_candidates = sum(len(candidates) for candidates in resource_candidates.values())
        print(f"Found {total_candidates} total candidate resource pixels:")
        for resource_type, candidates in resource_candidates.items():
            print(f"- {resource_type}: {len(candidates)} candidates")
        
        if total_candidates == 0:
            print("Warning: No resource pixels found! Check map coloring.")
            return
        
        # Track structures by resource type
        all_resource_structures = []
        structure_id = 0
        
        # Second pass: process candidate pixels by resource type
        for resource_type, candidates in resource_candidates.items():
            print(f"\nProcessing {resource_type} candidates...")
            resource_color = self.RESOURCE_COLORS[resource_type]
            
            # Use a dictionary to track x,y sums for center calculation
            from collections import defaultdict
            structure_stats = defaultdict(lambda: {'count': 0, 'x_sum': 0, 'y_sum': 0})
            
            for x, y in candidates:
                # Skip if this pixel has been checked already as part of another structure
                if (x, y) in checked_pixels and (x, y) not in candidates:
                    continue
                
                # Find connected pixels of this resource type
                connected_pixels = self.find_connected_resource(
                    x, y, pixels, checked_pixels, map_width, map_height, resource_type, resource_color
                )
                
                if connected_pixels and len(connected_pixels) > 0:
                    # Only consider clusters of sufficient size (avoid noise)
                    if len(connected_pixels) >= 5:
                        # Calculate stats in a single pass through the pixels
                        for px, py in connected_pixels:
                            structure_stats[structure_id]['count'] += 1
                            structure_stats[structure_id]['x_sum'] += px
                            structure_stats[structure_id]['y_sum'] += py
                        
                        # Calculate center
                        stats = structure_stats[structure_id]
                        avg_x = stats['x_sum'] // stats['count']
                        avg_y = stats['y_sum'] // stats['count']
                        
                        # Store the center as the resource location
                        self.resource_tiles[(avg_x, avg_y)] = {
                            'type': resource_type, 
                            'owner': None, 
                            'amount': 1
                        }
                        all_resource_structures.append({
                            'type': resource_type,
                            'pixels': connected_pixels,
                            'center': (avg_x, avg_y)
                        })
                        
                        print(f"{resource_type.capitalize()} structure #{structure_id} found at ({avg_x}, {avg_y}) with {len(connected_pixels)} pixels")
                        structure_id += 1
            
        # Report on found resources
        print(f"\nIdentified {len(all_resource_structures)} distinct resource structures:")
        resource_counts = {}
        for structure in all_resource_structures:
            resource_type = structure['type']
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        for resource_type, count in resource_counts.items():
            print(f"- {resource_type}: {count} structures")
        
        # After scanning, update ownership based on territory
        if all_resource_structures:
            try:
                if hasattr(self, 'map_interaction_manager'):
                    self.map_interaction_manager.update_resource_ownership()
                else:
                    print("Warning: map_interaction_manager not available")
            except Exception as e:
                print(f"Error updating resource ownership: {e}")

    def find_connected_resource(self, x, y, pixels, checked_pixels, map_width, map_height, resource_type, resource_color):
        """Find all connected resource pixels of a specific type starting from x,y"""
        if (x, y) in checked_pixels and (x, y) not in [(x, y)]:  # Only check if not the starting point
            return set()
            
        # Pre-check if starting pixel is the right resource color
        try:
            pixel = pixels[x, y]
            if len(pixel) == 4:
                pixel = pixel[:3]
                
            # Check if this pixel is of the target resource type using color matching with tolerance
            is_matching = False
            r, g, b = pixel
            
            if resource_type == 'gold':  # Yellow
                is_matching = r > 200 and g > 200 and b < 100
            elif resource_type == 'mana':  # Blue
                is_matching = r < 100 and g < 100 and b > 200
            # Green resources are blank and not tracked
            
            if not is_matching:
                checked_pixels.add((x, y))  # Mark as checked to avoid revisiting
                return set()
        except Exception as e:
            print(f"Error checking pixel at ({x}, {y}): {e}")
            return set()
            
        # This is a resource pixel we haven't checked
        connected = set()
        stack = [(x, y)]
        
        # Pre-compute direction offsets
        directions = [(0,1), (1,0), (0,-1), (-1,0)]
        
        # Pre-compute boundary checks
        x_range = range(map_width)
        y_range = range(map_height)
        
        while stack:
            current_x, current_y = stack.pop()
            
            if (current_x, current_y) in checked_pixels and (current_x, current_y) in connected:
                continue
                
            # Add to connected set and mark as checked in one operation
            connected.add((current_x, current_y))
            checked_pixels.add((current_x, current_y))
            
            # Check adjacent pixels
            for dx, dy in directions:
                new_x, new_y = current_x + dx, current_y + dy
                
                # Use pre-computed range for faster boundary checks
                if new_x in x_range and new_y in y_range and (new_x, new_y) not in checked_pixels:
                    try:
                        new_pixel = pixels[new_x, new_y]
                        if len(new_pixel) == 4:
                            new_pixel = new_pixel[:3]
                        
                        # Check if this pixel is of the target resource type
                        r, g, b = new_pixel
                        is_matching = False
                        
                        if resource_type == 'gold':  # Yellow
                            is_matching = r > 200 and g > 200 and b < 100
                        elif resource_type == 'mana':  # Blue
                            is_matching = r < 100 and g < 100 and b > 200
                        # Green resources are blank and not tracked
                        
                        if is_matching:
                            stack.append((new_x, new_y))
                        else:
                            # Mark non-matching pixels as checked to avoid revisiting
                            checked_pixels.add((new_x, new_y))
                    except Exception as e:
                        # Handle any pixel access errors
                        checked_pixels.add((new_x, new_y))
                
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
        """Switch to a different screen class, preserving state"""
        # Store any needed state before destroying current screen
        was_game_screen = False
        if self.current_screen:
            was_game_screen = hasattr(self.current_screen, 'display_map_image')
            was_same_class = isinstance(self.current_screen, screen_class)
            self.current_screen.destroy()
            
        # Show toolbar
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.setup_toolbar_buttons()
        
        # Initialize new screen with current theme
        self.current_screen = screen_class(self.content_frame, self)
        
        # Apply theme to the new screen
        if hasattr(self.current_screen, 'apply_theme'):
            self.current_screen.apply_theme(self.current_theme)
        else:
            # Apply theme to all widgets in the content frame
            self.apply_theme_to_widgets(self.content_frame.winfo_children())
        
        # Make sure units are displayed if we're switching to the game screen
        if hasattr(self.current_screen, 'display_map_image'):
            # Clear any cached images to force a complete redraw
            if hasattr(self.current_screen, 'invalidate_display_cache'):
                self.current_screen.invalidate_display_cache()
            # Force a redraw of the map image with units
            self.current_screen.display_map_image()
        
        # Force update to ensure any visual elements are refreshed
        self.master.update_idletasks()

    def apply_theme_to_widgets(self, widgets):
        """Apply theme to a list of widgets recursively"""
        for widget in widgets:
            try:
                # Apply theme based on widget type
                if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                    widget.configure(bg=self.current_theme['bg'])
                elif isinstance(widget, tk.Button):
                    widget.configure(
                        bg=self.current_theme['button_bg'],
                        fg=self.current_theme['button_fg'],
                        activebackground=self.current_theme['highlight_bg'],
                        activeforeground=self.current_theme['highlight_fg']
                    )
                elif isinstance(widget, (tk.Label, tk.Checkbutton, tk.Radiobutton)):
                    widget.configure(
                        bg=self.current_theme['bg'],
                        fg=self.current_theme['fg']
                    )
                    # Configure additional specific attributes for checkbuttons/radiobuttons
                    if isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
                        widget.configure(
                            activebackground=self.current_theme['bg'],
                            activeforeground=self.current_theme['fg'],
                            selectcolor=self.current_theme['bg']
                        )
                elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                    widget.configure(
                        bg=self.current_theme['bg'],
                        fg=self.current_theme['fg'],
                        insertbackground=self.current_theme['fg']  # cursor color
                    )
                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=self.current_theme['canvas_bg'])
                elif isinstance(widget, tk.Listbox):
                    widget.configure(
                        bg=self.current_theme['bg'],
                        fg=self.current_theme['fg'],
                        selectbackground=self.current_theme['highlight_bg'],
                        selectforeground=self.current_theme['highlight_fg']
                    )
                elif isinstance(widget, tk.Scrollbar):
                    # More detailed scrollbar configuration
                    widget.configure(
                        bg=self.current_theme['scrollbar_bg'],
                        troughcolor=self.current_theme['scrollbar_bg'],
                        activebackground=self.current_theme['scrollbar_fg'],
                        highlightbackground=self.current_theme['scrollbar_bg']
                    )
                    # Try to set different attributes based on whether it's a ttk scrollbar or standard scrollbar
                    try:
                        widget.configure(elementborderwidth=0)
                    except tk.TclError:
                        pass
                    try:
                        # For ttk scrollbars, we need to use a style
                        import tkinter.ttk as ttk
                        if isinstance(widget, ttk.Scrollbar):
                            style = ttk.Style()
                            style.configure("Dark.Vertical.TScrollbar", 
                                           background=self.current_theme['scrollbar_fg'],
                                           troughcolor=self.current_theme['scrollbar_bg'])
                            widget.configure(style="Dark.Vertical.TScrollbar")
                    except (ImportError, tk.TclError):
                        pass
                
                # Recursively apply to children
                if widget.winfo_children():
                    self.apply_theme_to_widgets(widget.winfo_children())
            except tk.TclError:
                # Skip any widgets that we can't configure
                pass

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
                
        print("\n=== Updating Player Resources ===")
        
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
                    # Green resources are blank and not tracked
                    
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
        if self.current_screen:
            if hasattr(self.current_screen, '_cached_base_image'):
                self.current_screen._cached_base_image = None
            if hasattr(self.current_screen, '_tile_cache'):
                self.current_screen._tile_cache.clear()
            if hasattr(self.current_screen, 'tile_cache'):
                self.current_screen.tile_cache.clear()
            
        # Clear any cached images in placed sprites
        if hasattr(self, 'placed_sprites'):
            for sprite_id, sprite_info in list(self.placed_sprites.items()):
                if hasattr(sprite_info, 'extra_data') and sprite_info.extra_data:
                    if 'colored_sprite' in sprite_info.extra_data:
                        sprite_info.extra_data['colored_sprite'] = None
        
        # Force garbage collection after clearing caches
        import gc
        gc.collect()

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
    print("Starting MSPaint Risk Editor...")
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()

if __name__ == "__main__":
    main()
