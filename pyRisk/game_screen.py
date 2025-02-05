# game_screen.py

import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, ImageDraw, Image, ImageFont
from utils import flood_fill
class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.selected_unit = None  # Track which unit is being moved
        self.unit_mode = False  # Track if we're in unit movement mode
        self.zoom_level = 1.0  # Initialize zoom level
        self.zoom_cache = {}  # Cache for zoomed images
        self.max_cache_size = 5  # Limit cache size to prevent memory issues
        self.setup_sidebar()
        self.setup_canvas()
        if self.app.map_image:
            self.display_map_image()
        self.bind_events()

    def setup_sidebar(self):
        self.sidebar = tk.Frame(self.frame, width=200, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.turn_label = tk.Label(self.sidebar, text=f"Turn: {self.app.current_turn}")
        self.turn_label.pack(pady=5)
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

        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.update_player_buttons()

    def setup_canvas(self):
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

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

    def display_map_image(self):
        if self.app.map_image is None:
            return
                
        # Only create the base image once per state change
        if not hasattr(self, 'current_display_image'):
            self.current_display_image = self.app.map_image.copy()
            draw = ImageDraw.Draw(self.current_display_image)
            
            # Draw tile ownership
            for (x, y), owner in self.app.tile_owners.items():
                if owner:
                    player = next((p for p in self.app.players if p.name == owner), None)
                    if player:
                        draw.point((x, y), fill=player.color)

        # Check zoom cache first
        cache_key = f"zoom_{self.zoom_level}"
        if cache_key in self.zoom_cache:
            display_image = self.zoom_cache[cache_key]
        else:
            display_image = self.current_display_image.copy()
            
            # Apply zoom if needed
            if self.zoom_level != 1.0:
                new_size = (
                    int(display_image.width * self.zoom_level),
                    int(display_image.height * self.zoom_level)
                )
                display_image = display_image.resize(new_size, Image.Resampling.NEAREST)
                
                # Cache the zoomed image
                self.zoom_cache[cache_key] = display_image
                
                # Remove oldest cache entry if cache is too large
                if len(self.zoom_cache) > self.max_cache_size:
                    oldest_key = next(iter(self.zoom_cache))
                    del self.zoom_cache[oldest_key]
        
        # Draw units on a separate layer if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            # Create a transparent overlay for units
            unit_overlay = Image.new('RGBA', display_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(unit_overlay)
            
            try:
                if not hasattr(self, 'unit_font'):
                    self.unit_font = ImageFont.truetype("arial.ttf", int(16 * self.zoom_level))
            except IOError:
                if not hasattr(self, 'unit_font'):
                    self.unit_font = ImageFont.load_default()

            for unit in self.app.units:
                if unit.position:
                    x, y = [int(coord * self.zoom_level) for coord in unit.position]
                    text_id = str(unit.unit_id)
                    text_type = unit.unit_type.value
                    
                    draw.rectangle(
                        [x - 2, y - 2, x + 20, y + 35],
                        fill='white'
                    )
                    draw.text((x, y), text_id, font=self.unit_font, fill='black')
                    draw.text((x, y + 20), text_type, font=self.unit_font, fill='black')
            
            # Composite the unit overlay onto the display image
            display_image = Image.alpha_composite(display_image.convert('RGBA'), unit_overlay)

        self.app.map_photo = ImageTk.PhotoImage(display_image)
        self.canvas.delete("all")
        
        # Calculate center position
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = display_image.width
        image_height = display_image.height
        
        x = max(0, (canvas_width - image_width) // 2)
        y = max(0, (canvas_height - image_height) // 2)
        
        self.map_item = self.canvas.create_image(x, y, image=self.app.map_photo, anchor=tk.NW)
        
        # Set scroll region with padding
        padding = 100
        self.canvas.config(scrollregion=(
            -padding,
            -padding,
            image_width + padding,
            image_height + padding
        ))

    def clear_zoom_cache(self):
        """Clear the zoom cache when the base image changes"""
        self.zoom_cache.clear()

    def invalidate_display_cache(self):
        """Clear all caches when the display needs to be fully refreshed"""
        if hasattr(self, 'current_display_image'):
            del self.current_display_image
        self.clear_zoom_cache()

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
        self.app.selected_player = player
        self.highlight_selected_player_button()

    def highlight_selected_player_button(self):
        for btn in self.player_buttons:
            if self.app.selected_player and btn.player_name == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down

    def on_mousewheel(self, event):
        if hasattr(self, '_zoom_after'):
            self.canvas.after_cancel(self._zoom_after)
        
        # Get mouse position relative to canvas
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # Get current image position
        bbox = self.canvas.bbox(self.map_item)
        if not bbox:
            return
            
        image_x, image_y = bbox[0], bbox[1]
        
        # Calculate relative position within the image
        rel_x = (mouse_x - image_x) / (bbox[2] - bbox[0])
        rel_y = (mouse_y - image_y) / (bbox[3] - bbox[1])
        
        # Update zoom level
        old_zoom = self.zoom_level
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        
        # Schedule the update with the calculated positions
        self._zoom_after = self.canvas.after(50, lambda: self._update_zoom(rel_x, rel_y))

    def _update_zoom(self, rel_x, rel_y):
        self.display_map_image()
        
        # Get new image position and size
        bbox = self.canvas.bbox(self.map_item)
        if not bbox:
            return
            
        # Calculate new scroll position to maintain relative mouse position
        new_x = bbox[0] + (bbox[2] - bbox[0]) * rel_x
        new_y = bbox[1] + (bbox[3] - bbox[1]) * rel_y
        
        # Adjust scroll position
        self.canvas.xview_moveto((new_x - self.canvas.winfo_width()/2) / self.canvas.bbox(tk.ALL)[2])
        self.canvas.yview_moveto((new_y - self.canvas.winfo_height()/2) / self.canvas.bbox(tk.ALL)[3])

    def invalidate_display_cache(self):
        """Clear the cached display image to force a redraw"""
        if hasattr(self, 'current_display_image'):
            del self.current_display_image

    def on_canvas_click(self, event):
        if self.app.map_image is None:
            return

        x, y = int(self.canvas.canvasx(event.x) / self.zoom_level), int(self.canvas.canvasy(event.y) / self.zoom_level)
        
        # Handle unit movement if in unit mode
        if self.app.roll_mode == 'tregonia' and self.unit_mode:
            if self.selected_unit is None:
                # Try to select a unit near the click
                for unit in self.app.units:
                    if unit.position:
                        unit_x, unit_y = unit.position
                        # Define a click radius for unit selection
                        if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                            self.selected_unit = unit
                            break
            else:
                # Move the selected unit to the new position
                self.selected_unit.position = (x, y)
                self.selected_unit = None
                self.display_map_image()
            return

        # Handle map coloring
        if x >= self.app.map_image.width or y >= self.app.map_image.height:
            return
            
        self.app.map_history.append(self.app.map_image.copy())
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)
            
        if self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return
                
            target_color = self.app.map_image.getpixel((x, y))
            replacement_color = (
                int(self.app.selected_player.color[0]),
                int(self.app.selected_player.color[1]),
                int(self.app.selected_player.color[2]),
                255
            )
            
            if self.app.roll_mode != 'external':
                roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
                if roll_info[2] <= 0:
                    messagebox.showwarning("No Tiles Left",
                                        f"{self.app.selected_player.name} has no tiles left to place.")
                    return
                self.update_player_tiles(self.app.selected_player.name, -1)
                
            previous_owner = self.app.tile_owners.get((x, y))
            if previous_owner and previous_owner != self.app.selected_player.name:
                self.update_player_tiles(previous_owner, 1)
            self.app.tile_owners[(x, y)] = self.app.selected_player.name
            
        elif self.app.mode == 'erase':
            target_color = self.app.map_image.getpixel((x, y))
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if (x, y) in self.app.tile_owners:
                player_name = self.app.tile_owners.pop((x, y))
                if self.app.roll_mode != 'external':
                    self.update_player_tiles(player_name, 1)

        flood_fill(self.app.map_image, x, y, target_color, replacement_color)
        self.invalidate_display_cache()
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
        if not self.app.map_history:
            messagebox.showinfo("Undo", "No actions to undo.")
            return
        self.app.map_image = self.app.map_history.pop()
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        self.invalidate_display_cache()
        self.display_map_image()
        self.update_player_buttons()

    def on_next_turn(self):
        """Handle next turn button click"""
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before proceeding to the next turn.")
            return
            
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
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.frame.destroy()