# game_screen.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import ImageTk, ImageDraw, Image, ImageFont
from pyRisk.utils import flood_fill, check_territory_in_radius
from pyRisk.players_screen import PlayersScreen
from pyRisk.game_screen_overlay import GameScreenOverlay
from pyRisk.sprite_manager import SpriteManager, SpriteInfo
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
from pyRisk.canvas_manager import CanvasManager
from pyRisk.sidebar_manager import SidebarManager
from pyRisk.map_interaction_manager import MapInteractionManager
from pyRisk.unit import UnitType

class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize state variables
        self.selected_unit = None
        self.unit_mode = False
        self.resource_paint_mode = None
        self.RESOURCE_COLORS = {
            'unactivated': (0, 255, 0),
            'gold': (255, 255, 0),
            'mana': (0, 255, 255)
        }
        self.player_buttons = []
        self.dragged_item = None
        self.map_photo = None
        self.map_item = None

        # Initialize sprite manager with app reference
        self.sprite_manager = SpriteManager(app)

        # Initialize overlay drawer
        self.overlay_drawer = GameScreenOverlay()

        # Initialize managers
        self.map_interaction_manager = MapInteractionManager(app)
        
        # Create single main layout container
        self.main_container = tk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create sidebar and map container
        self.sidebar = tk.Frame(self.main_container, width=150, bg='lightgrey')
        self.map_container = tk.Frame(self.main_container)

        # Pack frames
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self.map_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Setup components
        self.setup_canvas()
        self.setup_sidebar()

        # Initialize zoom parameters
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_update_id = None

        # Configure canvas
        self.canvas.configure(
            scrollregion=(0, 0, 1, 1),
            insertwidth=0,
            highlightthickness=0,
            xscrollincrement=1,
            yscrollincrement=1,
            takefocus=True
        )

        # Initialize tile cache
        self.tile_cache = {}
        self.tile_size = 256

        # Display map if exists
        if self.app.map_image:
            self.display_map_image()
            
        # Bind events
        self.bind_events()
        
        # Store references in app
        self.app.sprite_manager = self.sprite_manager
        self.app.map_interaction_manager = self.map_interaction_manager

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "8", "normal"))
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def setup_sidebar(self):
        # Turn information
        self.turn_label = tk.Label(self.sidebar, text=f"Turn: {self.app.current_turn}")
        self.turn_label.pack(pady=5)
        
        # Core game buttons
        self.next_turn_button = tk.Button(self.sidebar, text="Next Turn", command=self.on_next_turn)
        self.next_turn_button.pack(pady=5)
        
        self.mode_button = tk.Button(self.sidebar, text="Switch to Erase Mode", command=self.toggle_mode)
        self.mode_button.pack(pady=5)
        
        self.undo_button = tk.Button(self.sidebar, text="Undo", command=self.undo)
        self.undo_button.pack(pady=5)
        
        # Add unit mode toggle if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.unit_mode_button = tk.Button(
                self.sidebar,
                text="Enter Unit Move Mode",
                command=self.toggle_unit_mode
            )
            self.unit_mode_button.pack(pady=5)
            
            # Initially disable the button if there are no units
            if not hasattr(self.app, 'units') or len(self.app.units) == 0:
                self.unit_mode_button.config(state=tk.DISABLED)

        # Player selection section
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.update_player_buttons()

        # Resource painting section
        tk.Label(self.sidebar, text="Resource Painting:").pack(pady=5)
        self.resource_buttons = []
        for resource_type in ['unactivated', 'gold', 'mana']:
            btn = tk.Button(
                self.sidebar,
                text=resource_type.capitalize(),
                command=lambda t=resource_type: self.select_resource_paint(t)
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.resource_buttons.append(btn)

    def select_resource_paint(self, resource_type):
        """Handle resource paint button selection"""
        # If this resource type is already selected, deselect it
        if self.resource_paint_mode == resource_type:
            self.resource_paint_mode = None
        else:
            self.resource_paint_mode = resource_type
            # Deselect player when entering resource paint mode
            self.app.selected_player = None
            
        # Update button appearances
        self.highlight_selected_player_button()  # Unhighlight player buttons
        self.highlight_resource_button()

    def highlight_resource_button(self):
        """Update button appearances based on selected resource type"""
        for btn in self.resource_buttons:
            if btn['text'].lower() == self.resource_paint_mode:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def setup_canvas(self):
        """Setup canvas with sliders and zoom controls"""
        # Create main canvas frame
        self.canvas_frame = tk.Frame(self.map_container)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for zoom controls
        zoom_frame = tk.Frame(self.canvas_frame)
        zoom_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Add zoom buttons
        self.zoom_out_btn = tk.Button(zoom_frame, text="-", command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5)
        
        self.zoom_in_btn = tk.Button(zoom_frame, text="+", command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5)
        
        # Create zoom level label
        self.zoom_label = tk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        # Create canvas and scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.h_scrollbar = tk.Scale(self.canvas_frame, orient=tk.HORIZONTAL, 
                                from_=0, to=100, command=self.on_h_scroll)
        self.v_scrollbar = tk.Scale(self.canvas_frame, orient=tk.VERTICAL, 
                                from_=0, to=100, command=self.on_v_scroll)
        
        # Pack canvas and scrollbars
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def toggle_unit_mode(self):
        """Toggle between unit movement mode and regular map editing mode"""
        # Check if there are any units to move
        if not hasattr(self.app, 'units') or len(self.app.units) == 0:
            messagebox.showinfo("No Units", "There are no units on the map to move. Create units first.")
            return
            
        self.unit_mode = not self.unit_mode
        print(f"\n=== Unit Mode Toggled ===")
        print(f"Unit mode is now: {'ON' if self.unit_mode else 'OFF'}")
        
        if self.unit_mode:
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_button.config(state=tk.DISABLED)
            self.canvas.config(cursor="crosshair")
        else:
            self.unit_mode_button.config(text="Enter Unit Move Mode")
            self.mode_button.config(state=tk.NORMAL)
            self.canvas.config(cursor="")
            self.selected_unit = None

    def get_visible_region(self):
        """Get the currently visible region of the map"""
        if not self.app.map_image:
            return None
            
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Get scroll position
        x_view = self.canvas.xview()
        y_view = self.canvas.yview()
        
        # Calculate visible coordinates based on scroll position and zoom
        x1 = int(x_view[0] * self.app.map_image.width * self.zoom_level)
        y1 = int(y_view[0] * self.app.map_image.height * self.zoom_level)
        x2 = int(x_view[1] * self.app.map_image.width * self.zoom_level)
        y2 = int(y_view[1] * self.app.map_image.height * self.zoom_level)
        
        return (x1, y1, x2, y2)
    
    def get_required_tiles(self, visible_region):
        """Calculate which tiles are needed for the current view"""
        if not visible_region or not self.app.map_image:
            return set()
            
        x1, y1, x2, y2 = visible_region
        
        # Convert to tile coordinates with proper rounding
        start_tile_x = max(0, int(x1 / (self.tile_size * self.zoom_level)))
        start_tile_y = max(0, int(y1 / (self.tile_size * self.zoom_level)))
        end_tile_x = min(
            self.app.map_image.width // self.tile_size,
            int(x2 / (self.tile_size * self.zoom_level)) + 1
        )
        end_tile_y = min(
            self.app.map_image.height // self.tile_size,
            int(y2 / (self.tile_size * self.zoom_level)) + 1
        )
        
        return {(x, y) for x in range(start_tile_x, end_tile_x + 1)
                    for y in range(start_tile_y, end_tile_y + 1)}
    
    def render_tile(self, tile_x, tile_y):
        """Render a single map tile"""
        if not self.app.map_image:
            return None
            
        # Calculate tile boundaries
        x1 = tile_x * self.tile_size
        y1 = tile_y * self.tile_size
        x2 = min(x1 + self.tile_size, self.app.map_image.width)
        y2 = min(y1 + self.tile_size, self.app.map_image.height)
        
        # Create tile image
        tile = Image.new('RGBA', (self.tile_size, self.tile_size), (0, 0, 0, 0))
        
        # Copy base map portion
        map_region = self.app.map_image.crop((x1, y1, x2, y2))
        tile.paste(map_region, (0, 0))
        
        # Draw owned territories
        draw = ImageDraw.Draw(tile)
        for (x, y), owner in self.app.tile_owners.items():
            if (x1 <= x < x2) and (y1 <= y < y2):
                if owner:
                    player = next((p for p in self.app.players if p.name == owner), None)
                    if player:
                        draw.point((x - x1, y - y1), fill=player.color)
        
        # Draw sprites
        for pos, sprite_info in self.sprite_manager.placed_sprites.items():
            sprite_x, sprite_y = pos
            if (x1 <= sprite_x < x2) and (y1 <= sprite_y < y2):
                sprite_image = self.sprite_manager.sprites.get(sprite_info.sprite_type)
                if sprite_image:
                    paste_x = sprite_x - x1 - sprite_image.width // 2
                    paste_y = sprite_y - y1 - sprite_image.height // 2
                    tile.paste(sprite_image, (paste_x, paste_y), sprite_image)
        
        return tile

    def on_canvas_right_click(self, event):
        """Handle right-click on canvas"""
        if not self.app.map_image:
            return

        # Convert canvas coordinates to original image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate image coordinates without relying on bbox
        x = int(canvas_x / self.zoom_level)
        y = int(canvas_y / self.zoom_level)
        
        # Check if click is within image bounds
        if (x < 0 or y < 0 or 
            x >= self.app.map_image.width or 
            y >= self.app.map_image.height):
            return

        # Check for unit at this location first (if in Tregonia mode)
        if self.app.roll_mode == 'tregonia':
            clicked_unit = None
            for unit in self.app.units:
                if unit.position:
                    unit_x, unit_y = unit.position
                    # Define a click radius
                    if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                        clicked_unit = unit
                        break
            
            if clicked_unit:
                self.show_unit_popup(event, clicked_unit)
                return

        # Check for existing sprite at this location with radius check
        sprite_result = self.sprite_manager.get_sprite_at_position(x, y)
        existing_sprite = None
        sprite_pos = None
        if sprite_result is not None:
            sprite_pos, existing_sprite = sprite_result
        
        # Create popup menu
        popup = tk.Menu(self.canvas, tearoff=0)
        
        if existing_sprite:
            # Options for existing sprite
            popup.add_command(
                label=f"Remove {existing_sprite.sprite_type}",
                command=lambda: self.sprite_manager.remove_sprite(sprite_pos)
            )
        else:
            # Add army placement option if in Tregonia mode
            if self.app.roll_mode == 'tregonia':
                if self.app.players:
                    # Create a cascading menu for placing armies
                    armies_menu = tk.Menu(popup, tearoff=0)
                    popup.add_cascade(label="Place Army", menu=armies_menu)
                    
                    # Add an option for each player
                    for player in self.app.players:
                        armies_menu.add_command(
                            label=f"For {player.name}",
                            command=lambda p=player, pos=(x, y): self.place_army_at_position(p, pos)
                        )
                else:
                    popup.add_command(
                        label="Place Army (Add players first)",
                        state=tk.DISABLED
                    )
            
            # Add sprite placement options
            if self.app.selected_player:
                # Create cascading menu for different sprite categories
                structures_menu = tk.Menu(popup, tearoff=0)
                popup.add_cascade(label="Place Structure", menu=structures_menu)
                
                # Cities and Infrastructure
                structures_menu.add_command(label="City", 
                    command=lambda: self.place_city(x, y))
                structures_menu.add_command(label="Trading Post", 
                    command=lambda: self.sprite_manager.add_sprite('trading_post', (x, y)))
                structures_menu.add_command(label="Embassy", 
                    command=lambda: self.sprite_manager.add_sprite('embassy', (x, y)))
                
                # Resource Buildings
                resources_menu = tk.Menu(popup, tearoff=0)
                structures_menu.add_cascade(label="Resource Buildings", menu=resources_menu)
                resources_menu.add_command(label="Farm", 
                    command=lambda: self.sprite_manager.add_sprite('farm', (x, y)))
                resources_menu.add_command(label="Mine", 
                    command=lambda: self.sprite_manager.add_sprite('mine', (x, y)))
                resources_menu.add_command(label="Workshop", 
                    command=lambda: self.sprite_manager.add_sprite('workshop', (x, y)))
                
                # Military Structures
                military_menu = tk.Menu(popup, tearoff=0)
                structures_menu.add_cascade(label="Military Structures", menu=military_menu)
                military_menu.add_command(label="Fort (Stage 1)", 
                    command=lambda: self.sprite_manager.add_sprite('fort_1', (x, y)))
                military_menu.add_command(label="Fort (Stage 2)", 
                    command=lambda: self.sprite_manager.add_sprite('fort_2', (x, y)))
                military_menu.add_command(label="Fort (Stage 3)", 
                    command=lambda: self.sprite_manager.add_sprite('fort_3', (x, y)))
                military_menu.add_command(label="Wall (Stage 1)", 
                    command=lambda: self.sprite_manager.add_sprite('wall_1', (x, y)))
                military_menu.add_command(label="Wall (Stage 2)", 
                    command=lambda: self.sprite_manager.add_sprite('wall_2', (x, y)))
                
                # Magical/Religious Structures
                magical_menu = tk.Menu(popup, tearoff=0)
                structures_menu.add_cascade(label="Magical/Religious", menu=magical_menu)
                magical_menu.add_command(label="Shrine (Stage 1)", 
                    command=lambda: self.sprite_manager.add_sprite('shrine_1', (x, y)))
                magical_menu.add_command(label="Shrine (Stage 2)", 
                    command=lambda: self.sprite_manager.add_sprite('shrine_2', (x, y)))
                magical_menu.add_command(label="Monastery", 
                    command=lambda: self.sprite_manager.add_sprite('monastery', (x, y)))
                magical_menu.add_command(label="Observatory", 
                    command=lambda: self.sprite_manager.add_sprite('observatory', (x, y)))
                magical_menu.add_command(label="Research Lab", 
                    command=lambda: self.sprite_manager.add_sprite('research_lab', (x, y)))
                magical_menu.add_command(label="Henge", 
                    command=lambda: self.sprite_manager.add_sprite('henge', (x, y)))
                
                # Transport/Infrastructure
                transport_menu = tk.Menu(popup, tearoff=0)
                structures_menu.add_cascade(label="Transport", menu=transport_menu)
                transport_menu.add_command(label="Bridge", 
                    command=lambda: self.sprite_manager.add_sprite('bridge', (x, y)))
                transport_menu.add_command(label="Tunnel (Stage 1)", 
                    command=lambda: self.sprite_manager.add_sprite('tunnel_1', (x, y)))
                transport_menu.add_command(label="Tunnel (Stage 2)", 
                    command=lambda: self.sprite_manager.add_sprite('tunnel_2', (x, y)))
                transport_menu.add_command(label="Waystone", 
                    command=lambda: self.sprite_manager.add_sprite('waystone', (x, y)))
            else:
                popup.add_command(
                    label="Place Structure (Select a player first)",
                    state=tk.DISABLED
                )
        
        popup.tk_popup(event.x_root, event.y_root)

    def place_city(self, x, y):
        """Place a city with a name prompt and color it with the player's color"""
        city_name = simpledialog.askstring("New City", "Enter city name:")
        if city_name:
            # Create the city with the provided name
            success = self.sprite_manager.add_sprite('city', (x, y), extra_data={'name': city_name})
            if not success:
                print("Failed to create city")
                return
            
            # Get the sprite info for the newly created city
            sprite_result = self.sprite_manager.get_sprite_at_position(x, y)
            if sprite_result is None:
                print("Could not find placed city")
                return
            
            sprite_pos, sprite_info = sprite_result
            
            # Color the city with the player's color if a player is selected
            if self.app.selected_player and sprite_info:
                # Get the sprite image
                sprite_image = self.sprite_manager.sprites.get('city')
                if sprite_image:
                    # Create a working copy and ensure it's in RGBA mode
                    working_image = sprite_image.convert('RGBA')
                    pixels = working_image.load()
                    width, height = working_image.size
                    
                    # Color all gray pixels with player color
                    target_gray = (211, 211, 211)  # The gray color used in city sprites
                    player_color = (*self.app.selected_player.color[:3], 255)  # Fully opaque player color
                    
                    print(f"Coloring city with color: {player_color}")
                    colored_pixels = 0
                    
                    for x in range(width):
                        for y in range(height):
                            pixel = pixels[x, y]
                            # Check if pixel is the target gray (allowing some tolerance)
                            if all(abs(a - b) <= 5 for a, b in zip(pixel[:3], target_gray)):
                                pixels[x, y] = player_color
                                colored_pixels += 1
                    
                    print(f"Colored {colored_pixels} pixels in the city sprite")
                    
                    # Convert back to RGB to ensure full opacity
                    working_image = working_image.convert('RGB')
                    
                    # Store the colored sprite
                    if not sprite_info.extra_data:
                        sprite_info.extra_data = {}
                    sprite_info.extra_data['colored_sprite'] = working_image
                    sprite_info.owner = self.app.selected_player.name
                    
                    # Update display
                    self.display_map_image()

    def display_map_image(self):
        """Display the map image with current zoom level and overlay"""
        if self.app.map_image is None:
            return

        # Check if we need to regenerate the full image
        regenerate_full_image = (
            not hasattr(self, '_last_map_state') or
            not hasattr(self, '_cached_base_image') or
            self._last_map_state != {
                'map_id': id(self.app.map_image),
                'tile_owners': frozenset(self.app.tile_owners.items()),
                'sprites': frozenset((pos, sprite.sprite_type, sprite.owner, id(sprite.extra_data)) 
                                    for pos, sprite in self.sprite_manager.placed_sprites.items())
            }
        )
        
        if regenerate_full_image:
            # Create working copy of the map
            display_image = self.app.map_image.copy()
            
            # Draw territory
            draw = ImageDraw.Draw(display_image)
            for (x, y), owner in self.app.tile_owners.items():
                if owner:
                    player = next((p for p in self.app.players if p.name == owner), None)
                    if player:
                        draw.point((x, y), fill=player.color)
            
            # Load font for city names
            try:
                name_font = ImageFont.truetype("arial.ttf", 12)
            except IOError:
                name_font = ImageFont.load_default()
            
            # Draw sprites (including cities)
            for pos, sprite_info in self.sprite_manager.placed_sprites.items():
                sprite_x, sprite_y = pos
                sprite_image = self.sprite_manager.sprites.get(sprite_info.sprite_type)
                if sprite_image:
                    # Check if we have a pre-colored sprite
                    if 'colored_sprite' in sprite_info.extra_data:
                        sprite_to_draw = sprite_info.extra_data['colored_sprite']
                    else:
                        # Use original sprite
                        sprite_to_draw = sprite_image.copy()
                    
                    # Calculate paste position
                    paste_x = sprite_x - sprite_to_draw.width // 2
                    paste_y = sprite_y - sprite_to_draw.height // 2
                    
                    # Ensure sprite is in RGBA mode for proper transparency
                    if sprite_to_draw.mode != 'RGBA':
                        sprite_to_draw = sprite_to_draw.convert('RGBA')
                    
                    # Paste the sprite with transparency mask
                    display_image.paste(sprite_to_draw, (paste_x, paste_y), sprite_to_draw)
                    
                    # Draw name if it's a city
                    if sprite_info.sprite_type == 'city':
                        # Get city name from extra_data
                        city_name = sprite_info.extra_data.get('name', 'Unnamed City')
                        
                        # Calculate text size for centering
                        text_bbox = draw.textbbox((0, 0), city_name, font=name_font)
                        text_width = text_bbox[2] - text_bbox[0]
                        
                        # Position text centered below the sprite
                        text_x = sprite_x - text_width // 2
                        text_y = paste_y + sprite_image.height + 2
                        
                        # Draw text outline (black)
                        outline_positions = [
                            (-1, -1), (0, -1), (1, -1),
                            (-1, 0),           (1, 0),
                            (-1, 1),  (0, 1),  (1, 1)
                        ]
                        for dx, dy in outline_positions:
                            draw.text((text_x + dx, text_y + dy), city_name, 
                                    font=name_font, fill=(0, 0, 0))
                        
                        # Draw main text (white)
                        draw.text((text_x, text_y), city_name, 
                                font=name_font, fill=(255, 255, 255))
            
            # Cache the base image without units and overlay
            self._cached_base_image = display_image.copy()
            
            # Update the state tracking
            self._last_map_state = {
                'map_id': id(self.app.map_image),
                'tile_owners': frozenset(self.app.tile_owners.items()),
                'sprites': frozenset((pos, sprite.sprite_type, sprite.owner, id(sprite.extra_data)) 
                                    for pos, sprite in self.sprite_manager.placed_sprites.items())
            }
        else:
            # Use the cached base image
            display_image = self._cached_base_image.copy()
        
        # Draw units if in Tregonia mode - always do this part as units move frequently
        if self.app.roll_mode == 'tregonia':
            draw = ImageDraw.Draw(display_image)
            try:
                unit_font = ImageFont.truetype("arial.ttf", int(16))
            except IOError:
                unit_font = ImageFont.load_default()
                    
            for unit in self.app.units:
                if unit.position:
                    x, y = unit.position
                    owner = next((p for p in self.app.players if p.name == unit.owner), None)
                    owner_color = owner.color if owner else (128, 128, 128)
                    
                    # Draw unit directly on canvas
                    # Check if unit is rooted
                    is_rooted = False
                    if unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties:
                        is_rooted = True
                    elif unit.is_army:
                        for sub_unit in unit.sub_units:
                            if sub_unit.unit_type == UnitType.TREANT and "rooted" in sub_unit.special_properties:
                                is_rooted = True
                                break
                    
                    # Use dark gray for rooted units, white for others
                    fill_color = (128, 128, 128) if is_rooted else (255, 255, 255)
                    
                    # Draw unit rectangle
                    draw.rectangle(
                        [x - 3, y - 3, x + 23, y + 23],
                        fill=fill_color, outline='black'
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
        
        # Get cities for the overlay
        cities = [sprite_info for sprite_info in self.sprite_manager.placed_sprites.values() 
                if sprite_info.sprite_type == 'city']
        
        # Add the overlay before zooming
        display_image = self.overlay_drawer.draw_overlay(
            display_image,
            self.app.players,
            self.app.current_turn,
            cities
        )
        
        # Apply zoom if needed
        if self.zoom_level != 1.0:
            new_size = (
                int(round(display_image.width * self.zoom_level)),
                int(round(display_image.height * self.zoom_level))
            )
            resampling = Image.Resampling.LANCZOS if self.zoom_level > 1.0 else Image.Resampling.BILINEAR
            display_image = display_image.resize(new_size, resampling)

        # Update the display
        self.map_photo = ImageTk.PhotoImage(display_image)
        
        # Clear canvas and create new image
        self.canvas.delete("all")
        self.map_item = self.canvas.create_image(0, 0, image=self.map_photo, anchor=tk.NW)

        # Update scroll region
        self.canvas.config(scrollregion=(0, 0, display_image.width, display_image.height))

    def recolor_sprite_from_data(self, sprite_image, color_data):
        """Apply color data to a sprite image.
        
        Args:
            sprite_image: PIL Image to recolor
            color_data: Dictionary mapping target colors to replacement colors
            
        Returns:
            Modified copy of the sprite image
        """
        # Create a copy of the sprite to modify
        sprite_to_draw = sprite_image.copy()
        pixels = sprite_to_draw.load()
        width, height = sprite_to_draw.size
        
        # For each pixel in the sprite
        for x in range(width):
            for y in range(height):
                pixel = pixels[x, y]
                # Check if this pixel's color should be replaced
                if pixel[:3] in color_data:
                    new_color = color_data[pixel[:3]]
                    if len(pixel) == 4:  # RGBA
                        pixels[x, y] = (*new_color, pixel[3])  # Preserve alpha
                    else:  # RGB
                        pixels[x, y] = new_color
                        
        return sprite_to_draw

    def draw_units(self):
        """Draw units separately to avoid including them in tile cache"""
        visible_region = self.get_visible_region()
        if not visible_region:
            return
            
        x1, y1, x2, y2 = visible_region
        
        try:
            unit_font = ImageFont.truetype("arial.ttf", int(16 * self.zoom_level))
        except IOError:
            unit_font = ImageFont.load_default()

        for unit in self.app.units:
            if unit.position:
                x, y = [int(coord * self.zoom_level) for coord in unit.position]
                
                # Skip if unit is not in visible region
                if not (x1 <= x <= x2 and y1 <= y <= y2):
                    continue
                    
                owner = next((p for p in self.app.players if p.name == unit.owner), None)
                owner_color = owner.color if owner else (128, 128, 128)
                
                # Draw unit directly on canvas
                # Check if unit is rooted
                is_rooted = False
                if unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties:
                    is_rooted = True
                elif unit.is_army:
                    for sub_unit in unit.sub_units:
                        if sub_unit.unit_type == UnitType.TREANT and "rooted" in sub_unit.special_properties:
                            is_rooted = True
                            break
                
                # Use dark gray for rooted units, white for others
                fill_color = (128, 128, 128) if is_rooted else (255, 255, 255)
                
                # Draw unit rectangle
                draw.rectangle(
                    [x - 3, y - 3, x + 23, y + 23],
                    fill=fill_color, outline='black'
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

    def update_player_buttons(self):
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Button) and hasattr(widget, 'player_name'):
                widget.destroy()

        self.player_buttons = []
        for player in self.app.players:
            roll_info = self.app.player_rolls.get(player.name, ("", 0, 0))
            remaining_tiles = roll_info[2]
            
            if self.app.roll_mode == 'external':
                btn_text = f"{player.name}"
            else:
                btn_text = f"{player.name} ({remaining_tiles})"
                
            btn = tk.Button(
                self.sidebar,
                text=btn_text,
                command=lambda p=player: self.select_player(p)
            )
            btn.player_name = player.name
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.player_buttons.append(btn)
            
        self.highlight_selected_player_button()

    def select_player(self, player):
        """Handle player selection"""
        # If selecting a player, disable resource paint mode
        if self.resource_paint_mode is not None:
            self.resource_paint_mode = None
            self.highlight_resource_button()
            
        self.app.selected_player = player
        self.highlight_selected_player_button()

    def highlight_selected_player_button(self):
        for btn in self.player_buttons:
            if self.app.selected_player and btn.player_name == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def bind_events(self):
        """Bind required events"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right click

    def on_h_scroll(self, value):
        """Handle horizontal scroll events"""
        if not self.app.map_image or not hasattr(self, 'map_item'):
            return
            
        # Convert percentage to actual position
        value = float(value) / 100
        self.canvas.xview_moveto(value)

    def on_v_scroll(self, value):
        """Handle vertical scroll events"""
        if not self.app.map_image or not hasattr(self, 'map_item'):
            return
            
        # Convert percentage to actual position
        value = float(value) / 100
        self.canvas.yview_moveto(value)

    def zoom_in(self):
        """Handle zoom in button click"""
        if not self.app.map_image:
            return
            
        old_zoom = self.zoom_level
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
        
        if old_zoom != self.zoom_level:
            # Update zoom label
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")
            
            # Update display
            self.display_map_image()

    def zoom_out(self):
        """Handle zoom out button click"""
        if not self.app.map_image:
            return
            
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
        
        if old_zoom != self.zoom_level:
            # Update zoom label
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")
            
            # Update display
            self.display_map_image()

    def invalidate_display_cache(self):
        """Force a redraw of the display"""
        self.display_map_image()

    def on_canvas_click(self, event):
        if self.app.map_image is None:
            return

        # Convert canvas coordinates to original image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate image coordinates without relying on bbox
        x = int(canvas_x / self.zoom_level)
        y = int(canvas_y / self.zoom_level)

        # Handle unit movement if in unit mode
        if self.app.roll_mode == 'tregonia' and self.unit_mode:
            self.handle_unit_placement(x, y)
            return  # Important: return here to prevent other handlers from running

        # Check if click is within image bounds
        if x < 0 or y < 0 or x >= self.app.map_image.width or y >= self.app.map_image.height:
            return

        # Handle map coloring through the map interaction manager
        self.map_interaction_manager.handle_map_coloring(x, y)

    def handle_unit_placement(self, x, y):
        """Handle unit selection and placement on the map.
        If no unit is selected, try to select one at the clicked position.
        If a unit is already selected, move it to the clicked position."""
        
        print(f"\n=== Unit Placement Debug ===")
        print(f"Click coordinates: ({x}, {y})")
        print(f"Selected unit: {self.selected_unit.unit_id if self.selected_unit else None}")
        print(f"Total units: {len(self.app.units)}")
        
        # Check if click is within image bounds
        if x < 0 or y < 0 or x >= self.app.map_image.width or y >= self.app.map_image.height:
            print("Click outside image bounds")
            return
            
        # If we already have a selected unit, move it to the new position
        if self.selected_unit:
            # Check if the unit can be moved (not rooted)
            from pyRisk.unit import UnitType
            
            # Check if this is a rooted Treant
            is_rooted = False
            
            # Check if this is a Treant with rooted property
            if self.selected_unit.unit_type == UnitType.TREANT and "rooted" in self.selected_unit.special_properties:
                is_rooted = True
            
            # Check if this is an army containing a rooted Treant
            elif self.selected_unit.is_army:
                for sub_unit in self.selected_unit.sub_units:
                    if sub_unit.unit_type == UnitType.TREANT and "rooted" in sub_unit.special_properties:
                        is_rooted = True
                        break
            
            # If unit is rooted, show a message and don't move it
            if is_rooted:
                print(f"Unit {self.selected_unit.unit_id} is rooted and cannot be moved")
                messagebox.showinfo("Cannot Move", "This unit is rooted and cannot be moved.")
                self.selected_unit = None
                self.canvas.config(cursor="crosshair")  # Reset cursor to crosshair
                return
            
            print(f"Moving unit {self.selected_unit.unit_id} to position ({x}, {y})")
            self.selected_unit.position = (x, y)
            
            # If this is an army, update positions of all sub-units
            if hasattr(self.selected_unit, 'sub_units') and self.selected_unit.sub_units:
                print(f"Updating positions of {len(self.selected_unit.sub_units)} sub-units")
                for sub_unit in self.selected_unit.sub_units:
                    sub_unit.position = (x, y)
                    
            # Deselect the unit after moving
            self.selected_unit = None
            self.canvas.config(cursor="crosshair")  # Reset cursor to crosshair
            
            # Update the display
            self.display_map_image()
            return
            
        # If no unit is selected, try to select one at the clicked position
        clicked_unit = None
        for unit in self.app.units:
            if unit.position:
                unit_x, unit_y = unit.position
                # Define a click radius for selection (20 pixels)
                if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                    clicked_unit = unit
                    print(f"Found unit {unit.unit_id} at position ({unit_x}, {unit_y})")
                    break
                    
        if clicked_unit:
            print(f"Selected unit {clicked_unit.unit_id}")
            self.selected_unit = clicked_unit
            self.canvas.config(cursor="fleur")  # Change cursor to indicate movement
        else:
            print("No unit found at clicked position")
            # List all units and their positions for debugging
            print("All units:")
            for unit in self.app.units:
                print(f"  Unit {unit.unit_id}: position={unit.position}, owner={unit.owner}, type={unit.unit_type}")
            
            # Do NOT create a new army here - just inform the user that no unit was found
            # This is the fix for the issue where a new army is created when clicking in an empty area
            messagebox.showinfo("No Unit Found", "No unit found at this position. Please click on an existing unit to move it.")

    def handle_map_coloring(self, x, y):
        """Handle map coloring using region-based approach"""
        print(f"handle_map_coloring called at coordinates: ({x}, {y})")  # Debug
        
        # Save current state before modification
        current_sprites_data = {}
        for pos, sprite_info in self.sprite_manager.placed_sprites.items():
            sprite_state = {
                'position': pos,
                'type': sprite_info.sprite_type,
                'owner': sprite_info.owner,
                'extra_data': sprite_info.extra_data.copy() if sprite_info.extra_data else None,
                'name': sprite_info.name
            }
            current_sprites_data[pos] = sprite_state

        self.app.map_history.append({
            'image': self.app.map_image.copy(),
            'tile_owners': self.app.tile_owners.copy(),
            'resource_tiles': self.app.resource_tiles.copy() if hasattr(self.app, 'resource_tiles') else {},
            'sprites_data': current_sprites_data
        })
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)

        # First check if we clicked on a city sprite
        sprite_result = self.sprite_manager.get_sprite_at_position(x, y)
        print(f"Sprite at position: {sprite_result}")  # Debug
        
        clicked_sprite = None
        sprite_pos = None
        if sprite_result is not None:
            sprite_pos, clicked_sprite = sprite_result
            print(f"Found sprite: type={clicked_sprite.sprite_type}, owner={clicked_sprite.owner}")  # Debug
            
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            print("Clicked on a city sprite")  # Debug
            if self.app.mode == 'erase':
                print("In erase mode")  # Debug
                # Instead of removing the sprite, flood fill with transparency
                sprite_image = self.sprite_manager.sprites.get(clicked_sprite.sprite_type)
                if sprite_image:
                    # Use a fully transparent color for erasing
                    transparent_color = (0, 0, 0, 0)
                    if self.map_interaction_manager.flood_fill_sprite(clicked_sprite, x, y, transparent_color):
                        print("Erased city coloring")  # Debug
                        self.display_map_image()
                    return
            elif self.app.selected_player:
                print(f"Attempting to color city for player: {self.app.selected_player.name}")  # Debug
                # Try to flood fill the sprite
                if self.map_interaction_manager.flood_fill_sprite(clicked_sprite, x, y, self.app.selected_player.color):
                    print("Successfully colored city")  # Debug
                    clicked_sprite.owner = self.app.selected_player.name
                    self.display_map_image()
                    return
                else:
                    print("Failed to color city")  # Debug
            elif self.app.selected_player is None and self.app.mode != 'erase':
                print("No player selected")  # Debug
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

        # Get current pixel color for territory painting
        target_color = self.app.map_image.getpixel((x, y))
        if len(target_color) == 4:
            target_color = target_color[:3]

        if self.resource_paint_mode:
            print(f"Resource paint mode active: {self.resource_paint_mode}")  # Debug
            replacement_color = self.RESOURCE_COLORS[self.resource_paint_mode]
            print(f"Painting with color: {replacement_color}")  # Debug
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                print(f"Found region with center: {region['center']}")  # Debug
                center = region['center']
                self.app.resource_tiles[center] = {
                    'type': self.resource_paint_mode,
                    'owner': None
                }
                print(f"Added resource tile at {center}: {self.app.resource_tiles[center]}")  # Debug
                
                # Update ownership immediately for the new resource
                if self.app.roll_mode == 'tregonia':
                    self.update_resource_ownership()
                    
            self.display_map_image()
            
            # Update any relevant displays
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()
            return

        if self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

            replacement_color = tuple(int(c) for c in self.app.selected_player.color)

            if self.app.roll_mode == 'application':
                roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
                if roll_info[2] <= 0:
                    messagebox.showwarning("No Tiles Left",
                                        f"{self.app.selected_player.name} has no tiles left to place.")
                    return
                self.update_player_tiles(self.app.selected_player.name, -1)

            # Check for previous owner of this region
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                # Remove previous ownership if it exists
                for pos in region['boundary']:
                    previous_owner = self.app.tile_owners.get(pos)
                    if previous_owner and previous_owner != self.app.selected_player.name:
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(previous_owner, 1)
                        del self.app.tile_owners[pos]
                    
                    # Set new ownership for the entire region
                    for pos in region['boundary']:
                        self.app.tile_owners[pos] = self.app.selected_player.name

        elif self.app.mode == 'erase':
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if len(replacement_color) == 4:
                replacement_color = replacement_color[:3]
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                for pos in region['boundary']:
                    if pos in self.app.tile_owners:
                        player_name = self.app.tile_owners.pop(pos)
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(player_name, 1)

        # Always update resource ownership
        if self.app.roll_mode == 'tregonia':
            self.update_resource_ownership()
            
            # Update displays
            for widget in self.app.master.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, PlayersScreen):
                            child.update_player_boxes()
                            break

        self.display_map_image()
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
            self.update_player_buttons()

    def update_player_tiles(self, player_name, change):
        if player_name in self.app.player_rolls:
            roll_value, total_tiles, remaining_tiles = self.app.player_rolls[player_name]
            new_remaining = remaining_tiles + change
            self.app.player_rolls[player_name] = (roll_value, total_tiles, new_remaining)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def toggle_mode(self):
        if self.app.mode == 'color':
            self.app.mode = 'erase'
            self.mode_button.config(text="Switch to Color Mode")
        else:
            self.app.mode = 'color'
            self.mode_button.config(text="Switch to Erase Mode")

    def undo(self):
        """Undo the last map change"""
        if not self.app.map_history:
            messagebox.showinfo("Undo", "No actions to undo.")
            return
                
        # Pop and restore previous state
        previous_state = self.app.map_history.pop()
        
        # Important: Make sure we get a fresh copy of the previous image
        self.app.map_image = previous_state['image'].copy()
        self.app.tile_owners = previous_state['tile_owners'].copy()
        if 'resource_tiles' in previous_state:
            self.app.resource_tiles = previous_state['resource_tiles'].copy()

        # Restore sprite states
        if 'sprites_data' in previous_state:
            for pos, sprite_state in previous_state['sprites_data'].items():
                if pos in self.sprite_manager.placed_sprites:
                    sprite_info = self.sprite_manager.placed_sprites[pos]
                    sprite_info.owner = sprite_state['owner']
                    sprite_info.extra_data = sprite_state['extra_data'].copy() if sprite_state['extra_data'] else {}
                    sprite_info.name = sprite_state['name']
        
        # Make sure to get a fresh ImageDraw object
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        
        # Ensure the display is updated
        self.invalidate_display_cache()
        self.display_map_image()
        
        # Update all relevant UI elements
        self.update_player_buttons()
        
        # Update resource ownership if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.update_resource_ownership()

    def on_next_turn(self):
        """Handle next turn button click"""
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before proceeding to the next turn.")
            return
                
        # Apply resource increases for all players
        for player in self.app.players:
            player.apply_turn_increases()
                
        self.app.current_turn += 1
        self.app.save_current_map_state()
        self.app.map_history.clear()
        if self.app.roll_mode != 'external':
            self.app.player_rolls.clear()
                
        self.turn_label.config(text=f"Turn: {self.app.current_turn}")
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
        self.update_player_buttons()
        
        # Update unit move button state
        if hasattr(self, 'unit_mode_button'):
            if not hasattr(self.app, 'units') or len(self.app.units) == 0:
                self.unit_mode_button.config(state=tk.DISABLED)
            else:
                self.unit_mode_button.config(state=tk.NORMAL)

    def destroy(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Button-3>")  # Unbind right click
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.frame.destroy()

    def place_army_at_position(self, player, position):
        """Place an existing army or create a new one for the specified player at the given position.
        
        Args:
            player: The Player object who will own the army
            position: A tuple (x, y) where the army should be placed
        """
        from pyRisk.unit import Unit, UnitType
        
        # Check if there's already an army at this position
        x, y = position
        existing_army_at_position = None
        for unit in self.app.units:
            if unit.position:
                unit_x, unit_y = unit.position
                # Define a radius for checking (20 pixels)
                if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                    existing_army_at_position = unit
                    break
        
        # If there's already an army at this position, don't place another one
        if existing_army_at_position:
            print(f"Army already exists at position {position} (Unit #{existing_army_at_position.unit_id})")
            messagebox.showinfo("Army Exists", f"An army (#{existing_army_at_position.unit_id}) already exists at this position.")
            return
        
        # Find unplaced armies for this player
        unplaced_armies = [unit for unit in self.app.units 
                          if unit.owner == player.name and unit.position is None]
        
        # If there are unplaced armies, let the user select one to place
        selected_army = None
        if unplaced_armies:
            # If there's only one unplaced army, use it
            if len(unplaced_armies) == 1:
                selected_army = unplaced_armies[0]
                print(f"Placing existing army #{selected_army.unit_id} for {player.name} at position {position}")
            else:
                # If there are multiple unplaced armies, show a dialog to select one
                options = []
                for army in unplaced_armies:
                    # Include information about sub-units if any
                    sub_units_info = ""
                    if hasattr(army, 'sub_units') and army.sub_units:
                        sub_units_info = f" ({len(army.sub_units)} units)"
                    options.append(f"Army #{army.unit_id}{sub_units_info}")
                options.append("Create new army")
                
                # Create a simple dialog to select an option
                from tkinter import simpledialog
                message = f"Select an army to place for {player.name}:"
                title = "Select Army"
                
                # Show a dialog with radio buttons for each option
                dialog = tk.Toplevel(self.parent)
                dialog.title(title)
                dialog.transient(self.parent)
                dialog.grab_set()
                dialog.resizable(False, False)
                
                tk.Label(dialog, text=message, justify=tk.LEFT).pack(padx=20, pady=10)
                
                var = tk.StringVar(dialog)
                var.set(options[0])  # Default to first option
                
                for option in options:
                    tk.Radiobutton(dialog, text=option, variable=var, value=option).pack(anchor=tk.W, padx=20)
                
                # Add OK and Cancel buttons
                button_frame = tk.Frame(dialog)
                button_frame.pack(pady=10)
                
                result = {"value": None}
                
                def on_ok():
                    result["value"] = var.get()
                    dialog.destroy()
                
                def on_cancel():
                    dialog.destroy()
                
                tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
                tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)
                
                # Center the dialog
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry(f"{width}x{height}+{x}+{y}")
                
                # Wait for the dialog to close
                self.parent.wait_window(dialog)
                
                # Process the result
                if result["value"]:
                    selected_option = result["value"]
                    if selected_option == "Create new army":
                        selected_army = None
                    else:
                        # Extract the army ID from the option string
                        import re
                        match = re.search(r"Army #(\d+)", selected_option)
                        if match:
                            army_id = int(match.group(1))
                            selected_army = next((a for a in unplaced_armies if a.unit_id == army_id), None)
                            if selected_army:
                                print(f"Placing existing army #{selected_army.unit_id} for {player.name} at position {position}")
                else:
                    # User cancelled
                    return
        
        # If no existing army was selected, create a new one
        if selected_army is None:
            print(f"Creating new army for {player.name} at position {position}")
            
            # Create army as a special unit that will contain sub-units
            selected_army = Unit(
                owner=player.name,
                unit_type=UnitType.INFANTRY,  # Default type, doesn't matter for armies
                unit_id=self.app.next_unit_id,
                position=None  # Will set position below
            )
            
            # Add to app's units list
            self.app.units.append(selected_army)
            self.app.next_unit_id += 1
        
        # Set the position of the selected army
        selected_army.position = position
        
        # If this is an army with sub-units, update their positions too
        if hasattr(selected_army, 'sub_units') and selected_army.sub_units:
            for sub_unit in selected_army.sub_units:
                sub_unit.position = position
        
        # Update the display
        self.display_map_image()
        
        # Enable the unit move mode button if it was disabled
        if hasattr(self, 'unit_mode_button') and self.unit_mode_button['state'] == tk.DISABLED:
            self.unit_mode_button.config(state=tk.NORMAL)

    def show_unit_popup(self, event, clicked_unit):
        """Show a popup menu for managing a unit when right-clicked on the map.
        
        Args:
            event: The mouse event that triggered this
            clicked_unit: The Unit object that was clicked
        """
        # Create popup menu
        popup = tk.Menu(self.canvas, tearoff=0)
        
        # Add unit information
        popup.add_command(
            label=f"Unit #{clicked_unit.unit_id} ({clicked_unit.owner})",
            state=tk.DISABLED
        )
        
        # Add separator
        popup.add_separator()
        
        # Check if unit is rooted
        from pyRisk.unit import UnitType
        is_rooted = False
        
        # Check if this is a Treant with rooted property
        if clicked_unit.unit_type == UnitType.TREANT and "rooted" in clicked_unit.special_properties:
            is_rooted = True
        
        # Check if this is an army containing a rooted Treant
        elif clicked_unit.is_army:
            for sub_unit in clicked_unit.sub_units:
                if sub_unit.unit_type == UnitType.TREANT and "rooted" in sub_unit.special_properties:
                    is_rooted = True
                    break
        
        # Add option to move the unit (disabled if rooted)
        if is_rooted:
            popup.add_command(
                label="Move Unit (Rooted)",
                state=tk.DISABLED
            )
        else:
            popup.add_command(
                label="Move Unit",
                command=lambda: self.start_unit_movement(clicked_unit)
            )
        
        # Add option to view unit details
        popup.add_command(
            label="View Details",
            command=lambda: self.show_unit_details(clicked_unit)
        )
        
        # Add special options for Treants
        has_treant = clicked_unit.unit_type == UnitType.TREANT
        treant_sub_units = []
        
        if clicked_unit.is_army:
            for sub_unit in clicked_unit.sub_units:
                if sub_unit.unit_type == UnitType.TREANT:
                    has_treant = True
                    treant_sub_units.append(sub_unit)
        
        if has_treant:
            # If it's a single Treant
            if clicked_unit.unit_type == UnitType.TREANT:
                is_rooted = "rooted" in clicked_unit.special_properties
                popup.add_command(
                    label=f"{'Uproot' if is_rooted else 'Take Root'}",
                    command=lambda: self.toggle_treant_rooted(clicked_unit)
                )
            # If it's an army with Treants
            elif treant_sub_units:
                # Create a submenu for each Treant
                treants_menu = tk.Menu(popup, tearoff=0)
                popup.add_cascade(label="Treant Actions", menu=treants_menu)
                
                for treant in treant_sub_units:
                    is_rooted = "rooted" in treant.special_properties
                    treants_menu.add_command(
                        label=f"{'Uproot' if is_rooted else 'Take Root'} Treant #{treant.unit_id}",
                        command=lambda t=treant: self.toggle_treant_rooted(t)
                    )
        
        # Add option to delete the unit
        popup.add_command(
            label="Delete Unit",
            command=lambda: self.delete_unit(clicked_unit)
        )
        
        # Show the popup menu
        popup.tk_popup(event.x_root, event.y_root)
        
    def start_unit_movement(self, unit):
        """Start moving the specified unit.
        
        Args:
            unit: The Unit object to move
        """
        self.unit_mode = True
        self.selected_unit = unit
        self.canvas.config(cursor="fleur")  # Change cursor to indicate movement
        
        # Update UI to reflect unit movement mode
        if hasattr(self, 'unit_mode_button'):
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_button.config(state=tk.DISABLED)

    def show_unit_details(self, unit):
        """Show detailed information about a unit.
        
        Args:
            unit: The Unit object to show details for
        """
        from pyRisk.unit import UnitType
        
        # Build the details message
        details = f"Unit #{unit.unit_id}\n"
        details += f"Owner: {unit.owner}\n"
        details += f"Type: {unit.unit_type.value}\n"
        details += f"Position: {unit.position}\n\n"
        
        # Check if unit is rooted
        is_rooted = False
        if unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties:
            is_rooted = True
            details += "Status: ROOTED (cannot move)\n\n"
        
        if unit.is_army:
            details += f"Contains {len(unit.sub_units)} units:\n"
            has_rooted_treant = False
            
            for sub_unit in unit.sub_units:
                sub_status = ""
                if sub_unit.unit_type == UnitType.TREANT and "rooted" in sub_unit.special_properties:
                    sub_status = " (ROOTED)"
                    has_rooted_treant = True
                details += f"- {sub_unit.unit_type.value} #{sub_unit.unit_id}{sub_status}\n"
            
            if has_rooted_treant:
                details += "\nThis army contains a rooted Treant and cannot move.\n\n"
        
        details += f"Movement: {unit.movement_speed}\n"
        details += f"Attack: {unit.attack_dice}"
        if unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties:
            details += " (+2 when rooted)"
        details += f"\nCasualty: {unit.casualty_dice}\n"
        details += f"Wall: {unit.wall_dice}\n"
        details += f"Wall Bonus: +{unit.wall_bonus}" if unit.wall_bonus > 0 else f"Wall Bonus: {unit.wall_bonus}"
        
        # Show the details in a message box
        messagebox.showinfo(f"Unit #{unit.unit_id} Details", details)
        
    def delete_unit(self, unit):
        """Delete a unit from the map.
        
        Args:
            unit: The Unit object to delete
        """
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete unit #{unit.unit_id}?"):
            # Check if this is an army with sub-units
            if hasattr(unit, 'sub_units') and unit.sub_units:
                if not messagebox.askyesno("Delete Sub-units", 
                                        f"This army contains {len(unit.sub_units)} units. Delete them too?"):
                    return
                
                # Remove all sub-units
                for sub_unit in unit.sub_units[:]:
                    if sub_unit in self.app.units:
                        self.app.units.remove(sub_unit)
                
                # Clear the sub-units list
                unit.sub_units.clear()
            
            # Remove the unit itself
            if unit in self.app.units:
                self.app.units.remove(unit)
                
            # Update the display
            self.display_map_image()
            
            # Disable the unit move mode button if there are no more units
            if hasattr(self, 'unit_mode_button') and len(self.app.units) == 0:
                self.unit_mode_button.config(state=tk.DISABLED)
                # Also exit unit mode if we're in it
                if self.unit_mode:
                    self.unit_mode = False
                    self.unit_mode_button.config(text="Enter Unit Move Mode")
                    self.mode_button.config(state=tk.NORMAL)
                    self.canvas.config(cursor="")
                    self.selected_unit = None

    def toggle_treant_rooted(self, unit):
        """Toggle the rooted state for a Treant unit.
        
        Args:
            unit: The Unit object to toggle rooted state for
        """
        from pyRisk.unit import UnitType
        
        # Verify this is a Treant
        if unit.unit_type != UnitType.TREANT:
            messagebox.showinfo("Not a Treant", 
                              f"Unit #{unit.unit_id} is not a Treant and cannot be rooted.")
            return
            
        if "rooted" in unit.special_properties:
            unit.special_properties.remove("rooted")
            messagebox.showinfo("Treant Uprooted", 
                              f"Unit #{unit.unit_id} has been uprooted and can now move normally.")
        else:
            unit.special_properties.add("rooted")
            messagebox.showinfo("Treant Rooted", 
                              f"Unit #{unit.unit_id} has taken root. It gains +2 to attack but cannot move.")
        
        # Update the display
        self.display_map_image()
