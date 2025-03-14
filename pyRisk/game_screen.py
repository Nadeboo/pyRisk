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

        # Create main layout container
        self.main_container = tk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create container frames
        self.sidebar = tk.Frame(self.main_container, width=150, bg='lightgrey')
        self.map_container = tk.Frame(self.main_container)

        # Pack frames
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self.map_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Setup components
        self.setup_canvas()
        self.setup_sidebar()

        # Initialize zoom parameters with optimized defaults
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_update_id = None

        # Optimized canvas configuration
        self.canvas.configure(
            scrollregion=(0, 0, 1, 1),  # Will be updated when image is loaded
            insertwidth=0,              # Remove cursor indicator
            highlightthickness=0        # Remove highlight border
        )

        # Buffer for storing rendered tiles
        self.tile_cache = {}
        self.tile_size = 256  # Standard tile size for efficient rendering

        # Performance optimizations
        self.canvas.configure(
            xscrollincrement=1,    # Smooth scrolling
            yscrollincrement=1,
            takefocus=True         # Enable keyboard focus for better event handling
        )

        # Display map if exists
        if self.app.map_image:
            self.display_map_image()
            
        # Bind events
        self.bind_events()
        
        # Initialize managers
        self.sidebar_manager = SidebarManager(self.main_container, app)
        self.canvas_manager = CanvasManager(self.main_container, app)
        self.map_interaction_manager = MapInteractionManager(app)
        
        # Store references in app for access from other components
        self.app.sprite_manager = self.sprite_manager
        self.app.sidebar_manager = self.sidebar_manager
        self.app.canvas_manager = self.canvas_manager
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
        self.unit_mode = not self.unit_mode
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
        existing_sprite, sprite_pos = self.sprite_manager.get_sprite_at_position(x, y)
        
        # Create popup menu
        popup = tk.Menu(self.canvas, tearoff=0)
        
        if existing_sprite:
            # Options for existing sprite
            popup.add_command(
                label=f"Remove {existing_sprite.sprite_type}",
                command=lambda: self.sprite_manager.remove_sprite(sprite_pos)
            )
        else:
            # Add sprite placement options
            if self.app.selected_player:
                # Create cascading menu for different sprite categories
                structures_menu = tk.Menu(popup, tearoff=0)
                popup.add_cascade(label="Place Structure", menu=structures_menu)
                
                # Cities and Infrastructure
                structures_menu.add_command(label="City", 
                    command=lambda: self.sprite_manager.add_sprite('city', (x, y)))
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

    def display_map_image(self):
        """Display the map image with current zoom level and overlay"""
        if self.app.map_image is None:
            return

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
        TARGET_GRAY = (211, 211, 211)  # The specific gray color to replace in fort_3 and city
        
        for pos, sprite_info in self.sprite_manager.placed_sprites.items():
            sprite_x, sprite_y = pos
            sprite_image = self.sprite_manager.sprites.get(sprite_info.sprite_type)
            if sprite_image:
                # Handle fort_3 and city color replacement
                if sprite_info.sprite_type in ['fort_3', 'city']:
                    # Create a copy of the sprite to modify
                    sprite_to_draw = sprite_image.copy()
                    pixels = sprite_to_draw.load()
                    width, height = sprite_to_draw.size
                    
                    # Find the owner's color
                    owner = next((p for p in self.app.players if p.name == sprite_info.owner), None)
                    if owner:
                        # Replace the specific gray color with owner's color
                        for x in range(width):
                            for y in range(height):
                                pixel = pixels[x, y]
                                if len(pixel) == 4:  # RGBA
                                    if pixel[:3] == TARGET_GRAY:
                                        pixels[x, y] = (*owner.color, pixel[3])  # Preserve alpha
                                elif pixel == TARGET_GRAY:  # RGB
                                    pixels[x, y] = owner.color
                else:
                    # For all other sprites, use as-is
                    sprite_to_draw = sprite_image
                
                # Apply any stored color data
                if 'color_data' in sprite_info.extra_data:
                    sprite_to_draw = self.recolor_sprite_from_data(
                        sprite_to_draw,
                        sprite_info.extra_data['color_data']
                    )
                
                # Calculate paste position
                paste_x = sprite_x - sprite_to_draw.width // 2
                paste_y = sprite_y - sprite_to_draw.height // 2
                
                # Paste the sprite
                display_image.paste(sprite_to_draw, (paste_x, paste_y), sprite_to_draw)
                
                # Draw name if it's a city
                if sprite_info.sprite_type == 'city' and sprite_info.name:
                    # Calculate text size for centering
                    text_bbox = draw.textbbox((0, 0), sprite_info.name, font=name_font)
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
                        draw.text((text_x + dx, text_y + dy), sprite_info.name, 
                                font=name_font, fill=(0, 0, 0))
                    
                    # Draw main text (white)
                    draw.text((text_x, text_y), sprite_info.name, 
                            font=name_font, fill=(255, 255, 255))

        # Draw units if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            try:
                unit_font = ImageFont.truetype("arial.ttf", int(16))
            except IOError:
                unit_font = ImageFont.load_default()
                    
            for unit in self.app.units:
                if unit.position:
                    x, y = unit.position
                    owner = next((p for p in self.app.players if p.name == unit.owner), None)
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
                self.canvas.create_rectangle(
                    x - 3, y - 3, x + 23, y + 23,
                    fill='white', outline='black'
                )
                self.canvas.create_text(
                    x + 10, y + 10,
                    text=str(unit.unit_id),
                    font=unit_font
                )
                self.canvas.create_rectangle(
                    x - 3, y + 24, x + 23, y + 28,
                    fill='#{:02x}{:02x}{:02x}'.format(*owner_color),
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
            return

        # Check if click is within image bounds
        if x >= self.app.map_image.width or y >= self.app.map_image.height:
            return

        # Handle map coloring
        self.map_interaction_manager.handle_map_coloring(x, y)

    def handle_map_coloring(self, x, y):
        """Handle map coloring using region-based approach"""
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
        clicked_sprite, sprite_pos = self.sprite_manager.get_sprite_at_position(x, y)
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            if self.app.mode == 'erase':
                # Instead of removing the sprite, flood fill with transparency
                sprite_image = self.sprite_manager.sprites.get(clicked_sprite.sprite_type)
                if sprite_image:
                    # Use a fully transparent color for erasing
                    transparent_color = (0, 0, 0, 0)
                    if self.flood_fill_sprite(clicked_sprite, x, y, transparent_color):
                        self.display_map_image()
                    return
            elif self.app.selected_player:
                # Try to flood fill the sprite
                if self.flood_fill_sprite(clicked_sprite, x, y, self.app.selected_player.color):
                    clicked_sprite.owner = self.app.selected_player.name
                    self.display_map_image()
                    return
            elif self.app.selected_player is None and self.app.mode != 'erase':
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

    def destroy(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Button-3>")  # Unbind right click
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.frame.destroy()