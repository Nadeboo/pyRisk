# game_screen.py


import tkinter as tk
from tkinter import ttk, messagebox  # Add ttk here
from PIL import ImageTk, ImageDraw, Image, ImageFont
from utils import flood_fill
from players_screen import PlayersScreen
from utils import check_territory_in_radius
from game_screen_overlay import GameScreenOverlay  # Add this line
from sprite_manager import SpriteManager
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
        existing_sprite, sprite_pos = self.get_sprite_at_position(x, y)
        
        # Create popup menu
        popup = tk.Menu(self.canvas, tearoff=0)
        
        if existing_sprite:
            # Options for existing sprite
            popup.add_command(
                label=f"Remove {existing_sprite.sprite_type}",
                command=lambda: self.remove_sprite(sprite_pos)
            )
        else:
            # Add sprite placement options
            if self.app.selected_player:
                popup.add_command(
                    label="Place City",
                    command=lambda: self.add_sprite('city', x, y)
                )
            else:
                popup.add_command(
                    label="Place City (Select a player first)",
                    state=tk.DISABLED
                )
        
        popup.tk_popup(event.x_root, event.y_root)


    def add_sprite(self, sprite_type, x, y):
        """Add a sprite to the map"""
        if self.app.selected_player:
            owner = self.app.selected_player.name
        else:
            return
            
        if self.sprite_manager.add_sprite(sprite_type, (x, y), owner):
            self.display_map_image()

    def remove_sprite(self, position):
        """Remove a sprite from the map"""
        if self.sprite_manager.remove_sprite(position):
            self.display_map_image()

    def get_sprite_at_position(self, click_x, click_y, radius=10):
            """Find a sprite near the clicked position within a radius"""
            for pos, sprite_info in self.sprite_manager.placed_sprites.items():
                sprite_x, sprite_y = pos
                if abs(sprite_x - click_x) <= radius and abs(sprite_y - click_y) <= radius:
                    return sprite_info, pos
            return None, None

    def update_resource_ownership(self):
        """Update ownership of all resources based on surrounding territory"""
        if not self.app.map_image or self.app.roll_mode != 'tregonia':
            print("Resource ownership update skipped - no map or wrong mode")
            return
            
        print("\n=== Starting Resource Ownership Update ===")
        print(f"Total resources to check: {len(self.app.resource_tiles)}")
        print(f"Current tile owners count: {len(self.app.tile_owners)}")
        
        changes_made = False
        for pos, resource_info in self.app.resource_tiles.items():
            x, y = pos
            print(f"\nChecking resource at position {pos}")
            print(f"Current resource info: {resource_info}")
            
            # Check territory in radius around resource
            dominant_player, territory_count = check_territory_in_radius(
                self.app.map_image,
                self.app.tile_owners,
                x, y,
                radius=100
            )
            
            current_owner = resource_info.get('owner')
            print(f"Current owner: {current_owner}")
            print(f"Detected dominant player: {dominant_player}")
            
            if dominant_player != current_owner:
                print(f"Ownership change detected!")
                resource_info['owner'] = dominant_player
                changes_made = True
                if dominant_player:
                    print(f"Resource at {pos} claimed by {dominant_player} with {territory_count} surrounding tiles")
                else:
                    print(f"Resource at {pos} no longer controlled by any player")
        
        print("\n=== Resource Update Summary ===")
        print(f"Changes made: {changes_made}")
        
        if changes_made:
            print("Updating player resources and display...")
            self.app.update_player_resources()
            self.display_map_image()
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()


    def remove_unit_from_army(self, army, unit):
        """Remove a single unit from an army"""
        if unit in army.sub_units:
            army.sub_units.remove(unit)
            self.app.units.remove(unit)
            
            # Refresh displays
            self.display_map_image()
            if hasattr(self.app.current_screen, 'update_army_list'):
                self.app.current_screen.update_army_list()

    def remove_unit_from_map(self, unit):
        """Remove a unit from the map without deleting it from the game"""
        unit.position = None
        if unit.is_army:
            # If it's an army, remove all sub-units from map too
            for sub_unit in unit.sub_units:
                sub_unit.position = None
        self.display_map_image()

    def delete_unit(self, unit):
        """Delete a unit from both the map and the units list"""
        # First remove any sub-units if this is an army
        if unit.sub_units:
            for sub_unit in unit.sub_units[:]:  # Create a copy of the list to avoid modification while iterating
                self.app.units.remove(sub_unit)
        
        # Remove the unit itself
        self.app.units.remove(unit)
        
        # Refresh displays
        self.display_map_image()
        if hasattr(self.app.current_screen, 'update_army_list'):
            self.app.current_screen.update_army_list()

    def get_viewport_bounds(self):
        """Get the current viewport bounds in original image coordinates"""
        if not self.app.map_image:
            return None

        # Get canvas dimensions and scroll position
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_view = self.canvas.xview()
        y_view = self.canvas.yview()

        # Calculate visible coordinates
        x1 = int(x_view[0] * self.app.map_image.width * self.zoom_level)
        y1 = int(y_view[0] * self.app.map_image.height * self.zoom_level)
        x2 = int(x_view[1] * self.app.map_image.width * self.zoom_level)
        y2 = int(y_view[1] * self.app.map_image.height * self.zoom_level)

        # Convert to original image coordinates
        x1 = max(0, int(x1 / self.zoom_level))
        y1 = max(0, int(y1 / self.zoom_level))
        x2 = min(self.app.map_image.width, int(x2 / self.zoom_level))
        y2 = min(self.app.map_image.height, int(y2 / self.zoom_level))

        return (x1, y1, x2, y2)

    def get_visible_sprite_bounds(self, sprite_position, sprite_image):
        """Check if a sprite is visible in the current viewport"""
        if not self.app.map_image:
            return None

        viewport = self.get_viewport_bounds()
        if not viewport:
            return None

        x, y = sprite_position
        sprite_width = sprite_image.width
        sprite_height = sprite_image.height

        # Calculate sprite bounds
        sprite_x1 = x - sprite_width // 2
        sprite_y1 = y - sprite_height // 2
        sprite_x2 = sprite_x1 + sprite_width
        sprite_y2 = sprite_y1 + sprite_height

        # Check if sprite intersects viewport
        if (sprite_x2 < viewport[0] or sprite_x1 > viewport[2] or
            sprite_y2 < viewport[1] or sprite_y1 > viewport[3]):
            return None

        return (sprite_x1, sprite_y1, sprite_x2, sprite_y2)

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
        
        # Draw sprites (including cities)
        for pos, sprite_info in self.sprite_manager.placed_sprites.items():
            sprite_x, sprite_y = pos
            sprite_image = self.sprite_manager.sprites.get(sprite_info.sprite_type)
            if sprite_image:
                # Create a copy of the sprite to color if needed
                sprite_to_draw = sprite_image.copy()
                if sprite_info.extra_data and 'color' in sprite_info.extra_data:
                    # Create a solid color overlay
                    overlay = Image.new('RGBA', sprite_image.size, (*sprite_info.extra_data['color'], 128))
                    # Composite the overlay onto the sprite
                    sprite_to_draw = Image.alpha_composite(sprite_to_draw.convert('RGBA'), overlay)
                
                paste_x = sprite_x - sprite_image.width // 2
                paste_y = sprite_y - sprite_image.height // 2
                display_image.paste(sprite_to_draw, (paste_x, paste_y), sprite_to_draw)
        
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
                    
                    draw.rectangle(
                        [x - 3, y - 3, x + 23, y + 23],
                        fill='white', outline='black'
                    )
                    draw.text(
                        (x + 10, y + 10),
                        str(unit.unit_id),
                        font=unit_font,
                        fill='black',
                        anchor='mm'
                    )
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
        self.handle_map_coloring(x, y)

    def handle_map_coloring(self, x, y):
        """Handle map coloring using region-based approach"""
        # Save current state before modification
        self.app.map_history.append({
            'image': self.app.map_image.copy(),
            'tile_owners': self.app.tile_owners.copy(),
            'resource_tiles': self.app.resource_tiles.copy() if hasattr(self.app, 'resource_tiles') else {}
        })
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)

        # First check if we clicked on a city sprite
        clicked_sprite, sprite_pos = self.get_sprite_at_position(x, y)
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            if self.app.selected_player:
                # Color the city sprite
                clicked_sprite.extra_data['color'] = self.app.selected_player.color
                clicked_sprite.owner = self.app.selected_player.name
                self.display_map_image()
                return
            else:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

        # Get current pixel color for territory painting
        target_color = self.app.map_image.getpixel((x, y))
        if len(target_color) == 4:
            target_color = target_color[:3]

        if self.resource_paint_mode:
            print(f"Resource paint mode active: {self.resource_paint_mode}")
            replacement_color = self.RESOURCE_COLORS[self.resource_paint_mode]
            print(f"Painting with color: {replacement_color}")
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                print(f"Found region with center: {region['center']}")
                center = region['center']
                self.app.resource_tiles[center] = {
                    'type': self.resource_paint_mode,
                    'owner': None
                }
                print(f"Added resource tile at {center}: {self.app.resource_tiles[center]}")
                
                if self.app.roll_mode == 'tregonia':
                    self.update_resource_ownership()
                    
            self.display_map_image()
            
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