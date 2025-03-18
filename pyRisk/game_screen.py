# game_screen.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
from PIL import ImageTk, ImageDraw, Image, ImageFont
from pyRisk.utils import flood_fill, check_territory_in_radius
from pyRisk.players_screen import PlayersScreen
from pyRisk.game_screen_overlay import GameScreenOverlay
from pyRisk.sprite_manager import SpriteManager, SpriteInfo
from pyRisk.player import Player
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
from pyRisk.canvas_manager import CanvasManager
from pyRisk.sidebar_manager import SidebarManager
from pyRisk.map_interaction_manager import MapInteractionManager
from pyRisk.unit import Unit, UnitType, UnitClass, DEFAULT_MAX_ARMY_SIZE
from pyRisk.custom_scrollbar import CustomScrollbar
from pyRisk.sprite_manager import SpriteInfo

class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=app.current_theme['bg'])
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
        self._unit_canvas_items = []  # Initialize empty list to track unit canvas items

        # Initialize sprite manager with app reference
        self.sprite_manager = SpriteManager(app, sprite_folder="pyRisk/sprites")

        # Initialize overlay drawer
        self.overlay_drawer = GameScreenOverlay()

        # Initialize managers
        self.map_interaction_manager = MapInteractionManager(app)
        
        # Create single main layout container
        self.main_container = tk.Frame(self.frame, bg=app.current_theme['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Store current theme reference
        self.current_theme = app.current_theme
        
        # Setup UI components
        self.setup_canvas()
        self.setup_sidebar()
        self.bind_events()
        
        # Initialize zoom level and limits
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Initialize tile cache for rendering
        self._tile_cache = {}
        self._cached_base_image = None
        
        # Display the map if available
        if app.map_image:
            self.display_map_image()
        
        # Bind events
        self.bind_events()
        
        # Store references in app
        self.app.sprite_manager = self.sprite_manager
        self.app.map_interaction_manager = self.map_interaction_manager
        
    def bind_events(self):
        """Bind event handlers to the canvas"""
        # Canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Use the more comprehensive right-click menu
        
        # Also bind to right-click on Windows platforms
        try:
            # This might fail on some platforms
            self.canvas.bind("<ButtonPress-3>", self.on_canvas_right_click)  # Alternative binding for right-click
            self.canvas.bind("<ButtonRelease-3>", lambda e: None)  # Prevent issues with release
            
            # Add Windows-specific context menu event (very important for Windows)
            self.canvas.bind("<Button-3>", lambda e: self.canvas.focus_set())  # Focus canvas on right-click
            self.master.bind("<Key-Menu>", lambda e: self.on_canvas_right_click(e))   # Context menu key
            self.master.bind("<Shift-F10>", lambda e: self.on_canvas_right_click(e))  # Shift+F10 (context menu)
            
            # Force bind the context menu event via Tcl/Tk directly for Windows
            self.canvas.bind("<<ContextMenu>>", self.on_canvas_right_click)  # Standard context menu event
            self.canvas.event_add("<<ContextMenu>>", "<Button-3>")    # Map right click to context menu
        except Exception as e:
            print(f"Could not bind additional right-click events: {e}")
        
        # Print a message to help the user
        print("\n=== Right-click on the map to place cities and structures ===\n")
        print("If right-click menu doesn't appear, try:")
        print("1. Click the right mouse button (not the middle button)")
        print("2. If that doesn't work, try Shift+Right-click")
        print("3. On Mac, try Control+Click or two-finger tap\n")
        
        # Mousewheel for zoom/scroll
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down
        
    def on_right_click(self, event):
        """Handle right-click on the canvas to show context menu"""
        if self.app.map_image is None:
            return
            
        print(f"Right-click detected at {event.x}, {event.y}")
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate image coordinates based on zoom level
        x = int(canvas_x / self.zoom_level)
        y = int(canvas_y / self.zoom_level)
        
        print(f"Converted coordinates: {x}, {y}")
        
        # Check if click is within image bounds
        if x < 0 or y < 0 or x >= self.app.map_image.width or y >= self.app.map_image.height:
            print("Click outside image bounds")
            return
            
        # Check if we clicked on a unit
        clicked_unit = None
        if self.app.roll_mode == 'tregonia':
            for unit in self.app.units:
                if unit.position:
                    unit_x, unit_y = unit.position
                    # Define a click radius for selection (20 pixels)
                    if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                        clicked_unit = unit
                        print(f"Clicked on unit: {unit.unit_id}")
                        break
                        
        if clicked_unit:
            print("Showing unit popup menu")
            # If we clicked on a unit, show unit context menu
            self.show_unit_popup(event, clicked_unit)
            return
            
        # Otherwise, show general context menu
        print("Showing general context menu")
        self._show_context_menu(event, x, y)
    
    # Rename the original show_context_menu to _show_context_menu to debug the issue
    def _show_context_menu(self, event, x, y):
        """Show context menu for map interaction.
        
        Args:
            event: The event that triggered this method
            x: X-coordinate in image space
            y: Y-coordinate in image space
        """
        print(f"Creating context menu for position {x}, {y}")
        
        # Create popup menu with theme styling
        popup = tk.Menu(self.canvas, tearoff=0,
                     bg=self.current_theme['menu_bg'],
                     fg=self.current_theme['menu_fg'],
                     activebackground=self.current_theme['highlight_bg'],
                     activeforeground=self.current_theme['highlight_fg'])
        
        # Context information
        popup.add_command(
            label=f"Position: ({x}, {y})",
            state=tk.DISABLED
        )
        
        # Add separator
        popup.add_separator()
        
        # === Territory Painting Options ===
        # Territory management section
        popup.add_command(label="Territory Management:", state=tk.DISABLED)
        
        # Add territory painting options if a player is selected
        if self.app.selected_player:
            popup.add_command(
                label=f"Paint Territory for {self.app.selected_player.name}",
                command=lambda: self.map_interaction_manager.paint_territory(
                    self.app.map_image, 
                    (x, y), 
                    self.app.selected_player.color_rgb, 
                    self.app.selected_player.name, 
                    self.app.map_data, 
                    self.app.adjacency_map,
                    update_callback=self.display_map_image
                )
            )
            print("Added 'Paint Territory' option")
            
            # Erase territory option
            popup.add_command(
                label="Erase Territory",
                command=lambda: self.map_interaction_manager.erase_territory(
                    self.app.map_image, 
                    (x, y), 
                    self.app.map_data,
                    update_callback=self.display_map_image
                )
            )
            print("Added 'Erase Territory' option")
        else:
            popup.add_command(
                label="Paint Territory (Select a player first)",
                state=tk.DISABLED
            )
        
        # Add separator
        popup.add_separator()
        
        # === Structure Placement Options ===
        # Place city option
        if self.app.selected_player:
            popup.add_command(
                label=f"Place City for {self.app.selected_player.name}",
                command=lambda: self.place_city(x, y)
            )
            print("Added 'Place City' option")
        else:
            popup.add_command(
                label="Place City (Select a player first)",
                state=tk.DISABLED
            )
            print("Added disabled 'Place City' option")
            
        # Add separator before structures
        popup.add_separator()
        popup.add_command(label="Place Structure:", state=tk.DISABLED)
        
        # Force load sprites if not already loaded
        if not hasattr(self.sprite_manager, 'sprites') or not self.sprite_manager.sprites:
            print("Reloading sprites...")
            self.sprite_manager.load_sprites()
        
        # Add structures directly to the main menu
        print("Adding structure options directly to menu:")
        
        # Get available sprites - directly access the sprites dictionary
        all_sprites = list(self.sprite_manager.sprites.keys())
        print(f"Available sprites: {all_sprites}")
        
        # Check if we have any sprites
        if not all_sprites:
            popup.add_command(
                label="No structures available",
                state=tk.DISABLED
            )
            print("No sprites available")
        else:
            for sprite_name in sorted(all_sprites):
                if sprite_name != 'city' and sprite_name != 'map_cut':  # Skip city and map sprites
                    popup.add_command(
                        label=f"   {sprite_name.title().replace('_', ' ')}",
                        command=lambda s=sprite_name: self.place_sprite(s, x, y)
                    )
                    print(f"  Added option to place {sprite_name}")
        
        # Add separator before army option
        popup.add_separator()
        
        # Add option to place army if in Tregonia mode
        if self.app.roll_mode == 'tregonia' and self.app.selected_player:
            popup.add_command(
                label=f"Place Army for {self.app.selected_player.name}",
                command=lambda: self.place_army_at_position(self.app.selected_player, (x, y))
            )
            print("Added 'Place Army' option")
            
        # Display the popup menu
        print("Showing popup menu")
        try:
            popup.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing popup: {e}")
        
    def invalidate_display_cache(self):
        """Clear the display cache to force a complete redraw on next display_map_image call"""
        self._cached_base_image = None
        self._tile_cache = {}

    def apply_theme(self, theme):
        """Apply the provided theme to all widgets in this screen"""
        self.current_theme = theme
        
        # Apply to main frame and container
        self.frame.configure(bg=theme['bg'])
        self.main_container.configure(bg=theme['bg'])
        
        # Apply to canvas if it exists
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=theme['canvas_bg'])
            
        # Apply to scrollbars if they exist
        if hasattr(self, 'h_scrollbar') and hasattr(self, 'v_scrollbar'):
            scroll_bg = theme.get('scrollbar_bg', theme['button_bg'])
            scroll_fg = theme.get('scrollbar_fg', theme['highlight_bg'])
            
            # Apply theme to custom scrollbars
            if hasattr(self.h_scrollbar, 'config'):
                self.h_scrollbar.config(
                    bg=scroll_bg,
                    fg=scroll_fg
                )
            
            if hasattr(self.v_scrollbar, 'config'):
                self.v_scrollbar.config(
                    bg=scroll_bg,
                    fg=scroll_fg
                )
            
        # Apply to sidebar frame if it exists
        if hasattr(self, 'sidebar_frame'):
            self.sidebar_frame.configure(bg=theme['frame_bg'])
            
            # Apply to all elements in the sidebar
            for widget in self.sidebar_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(bg=theme['frame_bg'])
                    # Apply theme to child widgets
                    for child in widget.winfo_children():
                        self.apply_theme_to_widget(child, theme)
                else:
                    self.apply_theme_to_widget(widget, theme)
                    
        # Apply to zoom frame if it exists
        if hasattr(self, 'zoom_label'):
            self.zoom_label.configure(bg=theme['bg'], fg=theme['fg'])
            
        # Refresh display
        self.invalidate_display_cache()
        if hasattr(self, 'display_map_image'):
            self.display_map_image()
            
    def apply_theme_to_widget(self, widget, theme):
        """Apply theme to a single widget and all its children"""
        try:
            # Handle standard tkinter widgets
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                widget.configure(bg=theme['frame_bg'])
            elif isinstance(widget, tk.Button):
                widget.configure(
                    bg=theme['button_bg'],
                    fg=theme['button_fg'],
                    activebackground=theme['highlight_bg'],
                    activeforeground=theme['highlight_fg']
                )
            elif isinstance(widget, (tk.Label, tk.Checkbutton, tk.Radiobutton)):
                widget.configure(
                    bg=theme['frame_bg'],
                    fg=theme['fg']
                )
                # Configure additional specific attributes for checkbuttons/radiobuttons
                if isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
                    widget.configure(
                        activebackground=theme['frame_bg'],
                        activeforeground=theme['fg'],
                        selectcolor=theme['bg']
                    )
            elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                widget.configure(
                    bg=theme['bg'],
                    fg=theme['fg'],
                    insertbackground=theme['fg']  # cursor color
                )
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=theme['canvas_bg'])
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    bg=theme['bg'],
                    fg=theme['fg'],
                    selectbackground=theme['highlight_bg'],
                    selectforeground=theme['highlight_fg']
                )
            elif isinstance(widget, tk.Scrollbar):
                # Handle regular scrollbars
                widget.configure(
                    bg=theme['scrollbar_bg'] if 'scrollbar_bg' in theme else theme['button_bg'],
                    troughcolor=theme['scrollbar_bg'] if 'scrollbar_bg' in theme else theme['bg'],
                    activebackground=theme['scrollbar_fg'] if 'scrollbar_fg' in theme else theme['highlight_bg'],
                    highlightbackground=theme['scrollbar_bg'] if 'scrollbar_bg' in theme else theme['bg']
                )
            # Handle our CustomScrollbar class
            elif hasattr(widget, 'canvas') and hasattr(widget, 'set') and hasattr(widget, 'config'):
                # This might be a CustomScrollbar instance
                try:
                    widget.config(
                        bg=theme['scrollbar_bg'] if 'scrollbar_bg' in theme else theme['button_bg'],
                        fg=theme['scrollbar_fg'] if 'scrollbar_fg' in theme else theme['highlight_bg']
                    )
                except (tk.TclError, AttributeError):
                    pass
        except tk.TclError:
            # Skip widgets that can't be configured
            pass
            
        # Process children recursively
        for child in widget.winfo_children():
            self.apply_theme_to_widget(child, theme)

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
        self.sidebar_frame = tk.Frame(self.main_container, width=200, bg=self.current_theme['frame_bg'])
        self.sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        # Turn label
        self.turn_label = tk.Label(self.sidebar_frame, text=f"Turn: {self.app.current_turn}",
                                  bg=self.current_theme['frame_bg'], fg=self.current_theme['fg'],
                                  font=("Arial", 14, "bold"))
        self.turn_label.pack(pady=(10, 5))
        
        # Next turn button
        next_turn_btn = tk.Button(self.sidebar_frame, text="Next Turn", command=self.on_next_turn,
                                 bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                 activebackground=self.current_theme['highlight_bg'],
                                 activeforeground=self.current_theme['highlight_fg'])
        next_turn_btn.pack(pady=(0, 10))
        
        # Mode toggle button
        self.mode_toggle_btn = tk.Button(self.sidebar_frame, text="Toggle Mode (Color/City)", command=self.toggle_mode,
                                       bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                       activebackground=self.current_theme['highlight_bg'],
                                       activeforeground=self.current_theme['highlight_fg'])
        self.mode_toggle_btn.pack(pady=5)
        
        # Undo button
        self.undo_btn = tk.Button(self.sidebar_frame, text="Undo", command=self.undo,
                                bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                activebackground=self.current_theme['highlight_bg'],
                                activeforeground=self.current_theme['highlight_fg'])
        self.undo_btn.pack(pady=5)
        
        # Create player selection section
        player_frame = tk.Frame(self.sidebar_frame, bg=self.current_theme['frame_bg'])
        player_frame.pack(pady=10, fill=tk.X)
        
        player_label = tk.Label(player_frame, text="Select Player:",
                              bg=self.current_theme['frame_bg'], fg=self.current_theme['fg'],
                              font=("Arial", 12, "bold"))
        player_label.pack(pady=(0, 5))
        
        # Player buttons
        self.player_buttons_frame = tk.Frame(player_frame, bg=self.current_theme['frame_bg'])
        self.player_buttons_frame.pack()
        
        # Add players buttons
        self.update_player_buttons()
        
        # Toggle units button
        if self.app.roll_mode == 'tregonia':
            unit_frame = tk.Frame(self.sidebar_frame, bg=self.current_theme['frame_bg'])
            unit_frame.pack(pady=10, fill=tk.X)
            
            unit_label = tk.Label(unit_frame, text="Units:",
                                bg=self.current_theme['frame_bg'], fg=self.current_theme['fg'],
                                font=("Arial", 12, "bold"))
            unit_label.pack(pady=(0, 5))
            
            # Toggle unit mode button
            self.unit_mode_button = tk.Button(unit_frame, text="Enter Unit Move Mode", command=self.toggle_unit_mode,
                                          bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                          activebackground=self.current_theme['highlight_bg'],
                                          activeforeground=self.current_theme['highlight_fg'])
            self.unit_mode_button.pack(pady=2)
            
            # Resource management (only in Tregonia mode)
            resource_frame = tk.Frame(self.sidebar_frame, bg=self.current_theme['frame_bg'])
            resource_frame.pack(pady=10, fill=tk.X)
            
            resource_label = tk.Label(resource_frame, text="Resources:",
                                   bg=self.current_theme['frame_bg'], fg=self.current_theme['fg'],
                                   font=("Arial", 12, "bold"))
            resource_label.pack(pady=(0, 5))
            
            # Resource paint buttons
            self.gold_btn = tk.Button(resource_frame, text="Gold", command=lambda: self.select_resource_paint('gold'),
                                   bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                   activebackground=self.current_theme['highlight_bg'],
                                   activeforeground=self.current_theme['highlight_fg'])
            self.gold_btn.pack(side=tk.LEFT, padx=2)
            
            self.mana_btn = tk.Button(resource_frame, text="Mana", command=lambda: self.select_resource_paint('mana'),
                                   bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                   activebackground=self.current_theme['highlight_bg'],
                                   activeforeground=self.current_theme['highlight_fg'])
            self.mana_btn.pack(side=tk.LEFT, padx=2)
            
            self.no_resource_btn = tk.Button(resource_frame, text="None", command=lambda: self.select_resource_paint(None),
                                         bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                                         activebackground=self.current_theme['highlight_bg'],
                                         activeforeground=self.current_theme['highlight_fg'])
            self.no_resource_btn.pack(side=tk.LEFT, padx=2)

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
        for btn in self.gold_btn, self.mana_btn, self.no_resource_btn:
            if btn['text'].lower() == self.resource_paint_mode:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def setup_canvas(self):
        """Setup the canvas and scrollbars"""
        canvas_frame = tk.Frame(self.main_container, bg=self.current_theme['bg'])
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, bg=self.current_theme['canvas_bg'], highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Get scrollbar colors from theme
        scroll_bg = self.current_theme.get('scrollbar_bg', self.current_theme['button_bg'])
        scroll_fg = self.current_theme.get('scrollbar_fg', self.current_theme['highlight_bg'])
        
        # Create horizontal scrollbar - using CustomScrollbar with dark styling
        self.h_scrollbar = CustomScrollbar(
            canvas_frame, 
            orientation="horizontal", 
            command=self.canvas.xview,
            bg=scroll_bg,
            fg=scroll_fg,
            width=12
        )
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Create vertical scrollbar - using CustomScrollbar with dark styling
        self.v_scrollbar = CustomScrollbar(
            canvas_frame, 
            orientation="vertical", 
            command=self.canvas.yview,
            bg=scroll_bg,
            fg=scroll_fg,
            width=12
        )
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Add zoom buttons
        zoom_frame = tk.Frame(canvas_frame, bg=self.current_theme['bg'])
        zoom_frame.pack(anchor=tk.SE, padx=5, pady=5)
        
        # Add zoom label
        self.zoom_label = tk.Label(zoom_frame, text="100%", bg=self.current_theme['bg'], fg=self.current_theme['fg'])
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        zoom_in_btn = tk.Button(zoom_frame, text="+", command=self.zoom_in,
                             bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                             activebackground=self.current_theme['highlight_bg'],
                             activeforeground=self.current_theme['highlight_fg'],
                             width=2, height=1)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_out_btn = tk.Button(zoom_frame, text="-", command=self.zoom_out,
                              bg=self.current_theme['button_bg'], fg=self.current_theme['button_fg'],
                              activebackground=self.current_theme['highlight_bg'],
                              activeforeground=self.current_theme['highlight_fg'],
                              width=2, height=1)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        # Configure canvas for scrolling
        self.canvas.configure(scrollregion=(0, 0, 1, 1))

    def on_h_scroll(self, *args):
        """Handle horizontal scroll events"""
        if len(args) == 1:
            # This is from our custom scrollbar's direct movement
            self.canvas.xview_moveto(float(args[0]))
        else:
            # This is from the standard scrollbar interface
            self.canvas.xview(*args)

    def on_v_scroll(self, *args):
        """Handle vertical scroll events"""
        if len(args) == 1:
            # This is from our custom scrollbar's direct movement
            self.canvas.yview_moveto(float(args[0]))
        else:
            # This is from the standard scrollbar interface
            self.canvas.yview(*args)

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

    def display_map_image(self):
        """Display the map image on the canvas"""
        if self.app.map_image is None:
            return
            
        print("Displaying map image")
            
        # Calculate the new dimensions based on zoom level
        width = int(self.app.map_image.width * self.zoom_level)
        height = int(self.app.map_image.height * self.zoom_level)
        
        # Get base image
        base_image = self.app.map_image.copy()
        
        # Get cities for the overlay
        cities = []
        if hasattr(self.sprite_manager, 'placed_sprites'):
            cities = [sprite_info for sprite_info in self.sprite_manager.placed_sprites.values() 
                    if sprite_info.sprite_type == 'city']
            print(f"Found {len(cities)} cities for overlay")
        
        # Add the overlay before zooming
        display_image = self.overlay_drawer.draw_overlay(
            base_image,
            self.app.players,
            self.app.current_turn,
            cities
        )
        
        # Resize with overlay included
        resized_img = display_image.resize((
            int(display_image.width * self.zoom_level),
            int(display_image.height * self.zoom_level)
        ), Image.LANCZOS)
        
        # Convert to PhotoImage
        self.map_photo = ImageTk.PhotoImage(resized_img)
        
        # Update canvas scrollregion
        self.canvas.config(scrollregion=(0, 0, resized_img.width, resized_img.height))
        
        # Clear any existing unit-related canvas items
        if hasattr(self, '_unit_canvas_items') and self._unit_canvas_items:
            print(f"Clearing {len(self._unit_canvas_items)} existing unit canvas items")
            for item_id in self._unit_canvas_items:
                self.canvas.delete(item_id)
        self._unit_canvas_items = []  # Reset unit canvas items list
        
        # Create or update the image on the canvas
        if not hasattr(self, 'map_item') or self.map_item is None:
            self.map_item = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_photo)
        else:
            self.canvas.itemconfig(self.map_item, image=self.map_photo)
        
        # Draw units if in Tregonia mode
        if self.app.roll_mode == 'tregonia' and hasattr(self.app, 'units'):
            unit_count = len(self.app.units) if self.app.units else 0
            print(f"Drawing {unit_count} units on map")
            
            # Force draw units every time
            try:
                self.draw_units()
                print("Successfully drew units on map")
            except Exception as e:
                print(f"Error drawing units: {e}")
        else:
            print("Skipping unit drawing (not in Tregonia mode or no units)")
            
        # Update unit move button state
        if hasattr(self, 'unit_mode_button'):
            if not hasattr(self.app, 'units') or len(self.app.units) == 0:
                self.unit_mode_button.config(state=tk.DISABLED)
            else:
                self.unit_mode_button.config(state=tk.NORMAL)
                
        # Force canvas update
        self.canvas.update()

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
        import tkinter.font as tkFont
        from pyRisk.unit import DEFAULT_MAX_ARMY_SIZE, UnitType
        
        # Clear any existing unit canvas items
        if hasattr(self, '_unit_canvas_items'):
            for item_id in self._unit_canvas_items:
                try:
                    self.canvas.delete(item_id)
                except:
                    pass  # Item may have been deleted already
        
        # Reinitialize unit canvas items list
        self._unit_canvas_items = []
            
        # Get visible region
        visible_region = self.get_visible_region()
        if not visible_region:
            return
            
        x1, y1, x2, y2 = visible_region
        
        # Verify all units and fix any missing attributes
        if hasattr(self.app, 'units'):
            # Debug info
            print(f"Drawing {len(self.app.units)} units")
            
            # Create proper tkinter font objects
            unit_font = tkFont.Font(family="Arial", size=int(12 * self.zoom_level))
            count_font = tkFont.Font(family="Arial", size=int(10 * self.zoom_level), weight="bold")

            # Process each unit
            for unit in self.app.units:
                # Skip units without position
                if not hasattr(unit, 'position') or unit.position is None:
                    continue
                
                # Debug info for this unit
                print(f"Processing unit {unit.unit_id} at position {unit.position}")
                
                # Set is_army property if missing
                if not hasattr(unit, 'is_army'):
                    unit.is_army = len(getattr(unit, 'sub_units', [])) > 0
                
                # Set max_army_size for armies if missing
                if getattr(unit, 'is_army', False) and not hasattr(unit, 'max_army_size'):
                    unit.max_army_size = DEFAULT_MAX_ARMY_SIZE
                    print(f"Set missing max_army_size={DEFAULT_MAX_ARMY_SIZE} for army {unit.unit_id}")
                
                # Convert unit position to canvas coordinates
                x, y = [int(coord * self.zoom_level) for coord in unit.position]
                
                # Skip if unit is not in visible region
                if not (x1 <= x <= x2 and y1 <= y <= y2):
                    continue
                
                # Get owner and color
                owner = None
                if hasattr(unit, 'owner'):
                    owner = next((p for p in self.app.players if p.name == unit.owner), None)
                owner_color = owner.color if owner else (128, 128, 128)
                
                # Check if unit is rooted
                is_rooted = False
                # Check if this is a Treant with rooted property
                if hasattr(unit, 'unit_type') and hasattr(unit, 'special_properties'):
                    if unit.unit_type == UnitType.TREANT and "rooted" in unit.special_properties:
                        is_rooted = True
                
                # Check if this is an army containing a rooted Treant
                if getattr(unit, 'is_army', False) and hasattr(unit, 'sub_units'):
                    for sub_unit in unit.sub_units:
                        if (hasattr(sub_unit, 'unit_type') and 
                            hasattr(sub_unit, 'special_properties') and
                            sub_unit.unit_type == UnitType.TREANT and 
                            "rooted" in sub_unit.special_properties):
                            is_rooted = True
                            break
                
                # Use dark gray for rooted units, white for others
                fill_color = '#808080' if is_rooted else '#FFFFFF'
                
                # Draw unit rectangle
                rect_id = self.canvas.create_rectangle(
                    x - 3, y - 3, x + 23, y + 23,
                    fill=fill_color, outline='black',
                    tags=(f"unit_{unit.unit_id}" if hasattr(unit, 'unit_id') else "unit")
                )
                self._unit_canvas_items.append(rect_id)
                
                # Draw army capacity info for armies
                if getattr(unit, 'is_army', False) and hasattr(unit, 'sub_units'):
                    # Get army size info
                    sub_unit_count = len(unit.sub_units)
                    max_size = getattr(unit, 'max_army_size', DEFAULT_MAX_ARMY_SIZE)
                    
                    # Format as n/max
                    count_text = f"{sub_unit_count}/{max_size}"
                    print(f"Army {unit.unit_id} count: {count_text}")
                    
                    # Draw white background for capacity text
                    capacity_bg_id = self.canvas.create_rectangle(
                        x - 5, y - 20, 
                        x + 25, y - 4,
                        fill="white",
                        outline="black",
                        width=1,
                        tags=f"unit_{unit.unit_id}_capacity_bg"
                    )
                    self._unit_canvas_items.append(capacity_bg_id)
                    
                    # Draw capacity text
                    capacity_text_id = self.canvas.create_text(
                        x + 10, y - 12,
                        text=count_text,
                        font=count_font,
                        fill="black",
                        tags=f"unit_{unit.unit_id}_capacity"
                    )
                    self._unit_canvas_items.append(capacity_text_id)
                
                # Draw unit ID
                if hasattr(unit, 'unit_id'):
                    # Draw white outline
                    outline_id = self.canvas.create_text(
                        x + 10, y + 10,
                        text=str(unit.unit_id),
                        font=unit_font,
                        fill="white",
                        tags=f"unit_{unit.unit_id}_outline"
                    )
                    self._unit_canvas_items.append(outline_id)
                    
                    # Draw black text on top
                    text_id = self.canvas.create_text(
                        x + 10, y + 10,
                        text=str(unit.unit_id),
                        font=unit_font,
                        fill="black",
                        tags=f"unit_{unit.unit_id}_text"
                    )
                    self._unit_canvas_items.append(text_id)
                
                # Draw owner color bar
                hex_color = '#{:02x}{:02x}{:02x}'.format(*owner_color)
                color_bar_id = self.canvas.create_rectangle(
                    x - 3, y + 24, x + 23, y + 28,
                    fill=hex_color,
                    outline='black',
                    tags=f"unit_{unit.unit_id}_color"
                )
                self._unit_canvas_items.append(color_bar_id)
                
                # Draw rooted indicator if applicable
                if is_rooted:
                    root_id = self.canvas.create_line(
                        x - 3, y + 29, x + 23, y + 29,
                        fill='brown', width=2,
                        tags=f"unit_{unit.unit_id}_root"
                    )
                    self._unit_canvas_items.append(root_id)
        
        # Update the canvas
        self.canvas.update_idletasks()

    def update_player_buttons(self):
        # Clear existing buttons
        for widget in self.player_buttons_frame.winfo_children():
            widget.destroy()
        
        # Create new buttons
        self.player_buttons = []
        for i, player in enumerate(self.app.players):
            btn = tk.Button(
                self.player_buttons_frame,
                text=player.name,
                bg=f"#{player.color[0]:02x}{player.color[1]:02x}{player.color[2]:02x}",
                fg='white' if sum(player.color) < 380 else 'black',
                command=lambda p=player: self.select_player(p),
                width=10,
                relief=tk.RAISED
            )
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2)
            self.player_buttons.append((btn, player))
        
        # Add a button to add a new player
        add_btn = tk.Button(
            self.player_buttons_frame,
            text="+",
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            command=self.add_new_player,
            width=2
        )
        add_btn.grid(row=(len(self.app.players) + 1) // 2, column=(len(self.app.players) % 2), padx=2, pady=2)
        
        # Highlight selected player if any
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
        for btn, _ in self.player_buttons:
            if self.app.selected_player and btn['text'] == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def bind_events(self):
        """Bind required events"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right click

    def on_canvas_right_click(self, event):
        """Handle right-click on canvas"""
        # Get mouse position
        x, y = event.x, event.y
        
        # Convert canvas coordinates to actual map coordinates based on scrolling and zoom
        x = int(self.canvas.canvasx(x) / self.zoom_level)
        y = int(self.canvas.canvasy(y) / self.zoom_level)
        
        print(f"Right-click detected at position ({x}, {y})")
        
        # Check if we clicked on a unit
        clicked_unit = None
        if self.app.roll_mode == 'tregonia':
            for unit in self.app.units:
                if unit.position:
                    unit_x, unit_y = unit.position
                    # Define a click radius for selection (20 pixels)
                    if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                        clicked_unit = unit
                        print(f"Clicked on unit: {unit.unit_id}")
                        break
        
        # If we clicked on a unit, show unit popup menu instead
        if clicked_unit:
            print("Showing unit popup menu")
            self.show_unit_popup(event, clicked_unit)
            return
            
        # Create context menu with theme styling
        context_menu = tk.Menu(self.canvas, tearoff=0,
                          bg=self.current_theme['menu_bg'],
                          fg=self.current_theme['menu_fg'],
                          activebackground=self.current_theme['highlight_bg'],
                          activeforeground=self.current_theme['highlight_fg'])
                          
        # Add position information
        context_menu.add_command(
            label=f"Position: ({x}, {y})",
            state=tk.DISABLED
        )
        context_menu.add_separator()
        
        # === ARMY PLACEMENT SECTION ===
        if self.app.roll_mode == 'tregonia':
            if self.app.selected_player:
                context_menu.add_command(
                    label=f"Place Army for {self.app.selected_player.name}",
                    command=lambda: self.place_army_at_position(self.app.selected_player, (x, y))
                )
                print("Added 'Place Army' option")
            else:
                context_menu.add_command(
                    label="Place Army (Select a player first)",
                    state=tk.DISABLED
                )
            
            context_menu.add_separator()
            
        # === CITY SECTION ===
        # Add city placement option
        if self.app.selected_player:
            context_menu.add_command(
                label=f"Place City for {self.app.selected_player.name}",
                command=lambda: self.place_city(x, y)
            )
            print("Added 'Place City' option")
        else:
            context_menu.add_command(
                label="Place City (Select a player first)",
                state=tk.DISABLED
            )
        
        # === STRUCTURES SECTION ===
        context_menu.add_separator()
        context_menu.add_command(label="Place Structure:", state=tk.DISABLED)
        
        # Force load sprites if not already loaded
        if not hasattr(self.sprite_manager, 'sprites') or not self.sprite_manager.sprites:
            print("Loading sprites...")
            self.sprite_manager.load_sprites()
            
        # Get all available sprites
        all_sprites = list(self.sprite_manager.sprites.keys())
        print(f"Available sprites: {all_sprites}")
        
        # Group sprites by type
        structure_sprites = []
        transport_sprites = []
        defense_sprites = []
        other_sprites = []
        
        # Categorize sprites (skip city and map_cut)
        for sprite_name in all_sprites:
            if sprite_name in ['city', 'map_cut']:
                continue
            elif sprite_name in ['bridge', 'bridge_big', 'tunnel_1', 'tunnel_2', 'waystone']:
                transport_sprites.append(sprite_name)
            elif sprite_name in ['fort_1', 'fort_2', 'fort_3', 'wall_1', 'wall_2', 'tower']:
                defense_sprites.append(sprite_name)
            elif sprite_name in ['farm', 'farm_big', 'mine', 'observatory', 'research_lab', 'trading_post', 'workshop']:
                structure_sprites.append(sprite_name)
            else:
                other_sprites.append(sprite_name)
                
        # Create structure submenu
        if structure_sprites:
            structures_menu = tk.Menu(context_menu, tearoff=0,
                              bg=self.current_theme['menu_bg'],
                              fg=self.current_theme['menu_fg'],
                              activebackground=self.current_theme['highlight_bg'],
                              activeforeground=self.current_theme['highlight_fg'])
            context_menu.add_cascade(label="Economy Structures", menu=structures_menu)
            
            for sprite in sorted(structure_sprites):
                structures_menu.add_command(
                    label=f"{sprite.title().replace('_', ' ')}",
                    command=lambda s=sprite: self.place_sprite(s, x, y)
                )
                print(f"Added option to place {sprite}")
                
        # Create defense submenu
        if defense_sprites:
            defense_menu = tk.Menu(context_menu, tearoff=0,
                              bg=self.current_theme['menu_bg'],
                              fg=self.current_theme['menu_fg'],
                              activebackground=self.current_theme['highlight_bg'],
                              activeforeground=self.current_theme['highlight_fg'])
            context_menu.add_cascade(label="Defensive Structures", menu=defense_menu)
            
            for sprite in sorted(defense_sprites):
                defense_menu.add_command(
                    label=f"{sprite.title().replace('_', ' ')}",
                    command=lambda s=sprite: self.place_sprite(s, x, y)
                )
                print(f"Added option to place {sprite}")
                
        # Create transport submenu
        if transport_sprites:
            transport_menu = tk.Menu(context_menu, tearoff=0,
                              bg=self.current_theme['menu_bg'],
                              fg=self.current_theme['menu_fg'],
                              activebackground=self.current_theme['highlight_bg'],
                              activeforeground=self.current_theme['highlight_fg'])
            context_menu.add_cascade(label="Transport Structures", menu=transport_menu)
            
            for sprite in sorted(transport_sprites):
                transport_menu.add_command(
                    label=f"{sprite.title().replace('_', ' ')}",
                    command=lambda s=sprite: self.place_sprite(s, x, y)
                )
                print(f"Added option to place {sprite}")
                
        # Add other sprites directly to menu
        if other_sprites:
            context_menu.add_separator()
            context_menu.add_command(label="Other Structures:", state=tk.DISABLED)
            
            for sprite in sorted(other_sprites):
                context_menu.add_command(
                    label=f"   {sprite.title().replace('_', ' ')}",
                    command=lambda s=sprite: self.place_sprite(s, x, y)
                )
                print(f"Added option to place {sprite}")
        
        # Show menu at mouse position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
            print("Displayed context menu")
        except Exception as e:
            print(f"Error showing context menu: {e}")

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
        """Get the tile coordinates needed to render the visible region"""
        vx1, vy1, vx2, vy2 = visible_region
        
        # Calculate tile coordinates based on visible region and tile size
        # Adjust for zoom level to get correct tile indices
        start_tile_x = max(0, int(vx1 / (self.tile_size * self.zoom_level)))
        start_tile_y = max(0, int(vy1 / (self.tile_size * self.zoom_level)))
        
        # Ensure we don't go beyond the map dimensions
        end_tile_x = min(
            self.app.map_image.width // self.tile_size,
            int(vx2 / (self.tile_size * self.zoom_level)) + 1
        )
        end_tile_y = min(
            self.app.map_image.height // self.tile_size,
            int(vy2 / (self.tile_size * self.zoom_level)) + 1
        )
        
        return (start_tile_x, start_tile_y, end_tile_x, end_tile_y)
    
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
        
        # Draw sprites with better error handling and colored sprite support
        for pos, sprite_info in self.sprite_manager.placed_sprites.items():
            sprite_x, sprite_y = pos
            if (x1 <= sprite_x < x2) and (y1 <= sprite_y < y2):
                try:
                    # Try to get a pre-colored sprite first
                    if hasattr(sprite_info, 'extra_data') and sprite_info.extra_data and 'colored_sprite' in sprite_info.extra_data:
                        sprite_image = sprite_info.extra_data['colored_sprite']
                    else:
                        # Fall back to the original sprite
                        sprite_image = self.sprite_manager.sprites.get(sprite_info.sprite_type)
                    
                    if sprite_image:
                        paste_x = sprite_x - x1 - sprite_image.width // 2
                        paste_y = sprite_y - y1 - sprite_image.height // 2
                        tile.paste(sprite_image, (paste_x, paste_y), sprite_image)
                except Exception as e:
                    print(f"Error rendering sprite at {pos}: {e}")
        
        return tile

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
            from pyRisk.unit import UnitType, DEFAULT_MAX_ARMY_SIZE
            
            # Check if this is a rooted Treant
            is_rooted = False
            
            # Check if this is a Treant with rooted property
            if self.selected_unit.unit_type == UnitType.TREANT and "rooted" in self.selected_unit.special_properties:
                is_rooted = True
            
            # Check if this is an army containing a rooted Treant
            elif hasattr(self.selected_unit, 'is_army') and self.selected_unit.is_army:
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
            
            # Store the max_army_size before moving (if it's an army)
            max_size = DEFAULT_MAX_ARMY_SIZE
            if hasattr(self.selected_unit, 'max_army_size'):
                max_size = self.selected_unit.max_army_size
                print(f"Preserving max_army_size: {max_size}")
            elif hasattr(self.selected_unit, 'is_army') and self.selected_unit.is_army:
                print(f"Army missing max_army_size attribute, setting default: {DEFAULT_MAX_ARMY_SIZE}")
                self.selected_unit.max_army_size = DEFAULT_MAX_ARMY_SIZE
                max_size = DEFAULT_MAX_ARMY_SIZE
            
            # Update position
            self.selected_unit.position = (x, y)
            
            # Ensure max_army_size is preserved
            if hasattr(self.selected_unit, 'is_army') and self.selected_unit.is_army:
                self.selected_unit.max_army_size = max_size
                print(f"Confirmed max_army_size is set to {self.selected_unit.max_army_size}")
            
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
        from pyRisk.unit import DEFAULT_MAX_ARMY_SIZE
        
        clicked_unit = None
        for unit in self.app.units:
            if unit.position:
                unit_x, unit_y = unit.position
                # Define a click radius for selection (20 pixels)
                if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                    clicked_unit = unit
                    print(f"Found unit {unit.unit_id} at position ({unit_x}, {unit_y})")
                    
                    # Check if the unit has max_army_size properly set
                    if hasattr(unit, 'is_army') and unit.is_army:
                        if not hasattr(unit, 'max_army_size'):
                            print(f"Army {unit.unit_id} missing max_army_size, adding default")
                            unit.max_army_size = DEFAULT_MAX_ARMY_SIZE
                        else:
                            print(f"Army {unit.unit_id} has max_army_size: {unit.max_army_size}")
                    
                    break
                    
        if clicked_unit:
            print(f"Selected unit {clicked_unit.unit_id}")
            self.selected_unit = clicked_unit
            
            # If it's an army, verify max_army_size is properly set
            if hasattr(clicked_unit, 'is_army') and clicked_unit.is_army:
                if not hasattr(clicked_unit, 'max_army_size'):
                    clicked_unit.max_army_size = DEFAULT_MAX_ARMY_SIZE
                    print(f"Added missing max_army_size: {DEFAULT_MAX_ARMY_SIZE}")
            
            self.canvas.config(cursor="fleur")  # Change cursor to indicate movement
        else:
            print("No unit found at clicked position")
            # List all units and their positions for debugging
            print("All units:")
            for unit in self.app.units:
                print(f"  Unit {unit.unit_id}: position={unit.position}, owner={unit.owner}, type={unit.unit_type}")
                if hasattr(unit, 'is_army') and unit.is_army:
                    print(f"    Army with {len(unit.sub_units)} units, max_size: {getattr(unit, 'max_army_size', 'MISSING')}")
            
            # Do NOT create a new army here - just inform the user that no unit was found
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

    def invalidate_display_cache(self):
        """Clear the display cache to force a complete redraw on next display_map_image call"""
        if hasattr(self, '_cached_base_image'):
            self._cached_base_image = None
        if hasattr(self, '_tile_cache'):
            self._tile_cache = {}
        if hasattr(self, 'tile_cache'):
            self.tile_cache = {}

    def toggle_mode(self):
        if self.app.mode == 'color':
            self.app.mode = 'erase'
            self.mode_toggle_btn.config(text="Switch to Erase Mode")
        else:
            self.app.mode = 'color'
            self.mode_toggle_btn.config(text="Switch to Color Mode")

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
        """Clean up resources before destruction"""
        # Clear all canvas items to prevent memory leaks
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            
        # Clear unit canvas items list
        if hasattr(self, '_unit_canvas_items'):
            self._unit_canvas_items.clear()
            
        # Destroy the frame and all its children
        if hasattr(self, 'frame'):
            self.frame.destroy()
            
        # Clear image references to help with garbage collection
        self.map_photo = None
        self.map_item = None

    def place_army_at_position(self, player, position):
        """Place an existing army or create a new one for the specified player at the given position.
        
        Args:
            player: The Player object who will own the army
            position: A tuple (x, y) where the army should be placed
        """
        # Import needed components
        from pyRisk.unit import Unit, UnitType, DEFAULT_MAX_ARMY_SIZE
        
        # Debug info
        print(f"\n=== Placing Army ===")
        print(f"Player: {player.name}")
        print(f"Position: {position}")
        print(f"DEFAULT_MAX_ARMY_SIZE: {DEFAULT_MAX_ARMY_SIZE}")
        
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
            
            # Ask for max army size
            from tkinter import simpledialog
            max_size = simpledialog.askinteger(
                "Army Size Limit", 
                f"Enter the maximum size for this army (default is {DEFAULT_MAX_ARMY_SIZE}):",
                initialvalue=DEFAULT_MAX_ARMY_SIZE,
                minvalue=1,
                maxvalue=100
            )
            
            # If user cancels, use the default
            if max_size is None:
                max_size = DEFAULT_MAX_ARMY_SIZE
            
            # Create army as a special unit that will contain sub-units
            selected_army = Unit(
                owner=player.name,
                unit_type=UnitType.INFANTRY,  # Default type, doesn't matter for armies
                unit_id=self.app.next_unit_id,
                position=None,  # Will set position below
                max_army_size=max_size  # Set the max size
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
        from pyRisk.unit import DEFAULT_MAX_ARMY_SIZE
        
        self.unit_mode = True
        self.selected_unit = unit
        
        # Check if this is an army and if max_army_size is properly set
        if hasattr(unit, 'is_army') and unit.is_army:
            if not hasattr(unit, 'max_army_size'):
                print(f"Army {unit.unit_id} missing max_army_size in start_unit_movement, adding default")
                unit.max_army_size = DEFAULT_MAX_ARMY_SIZE
            else:
                print(f"Army {unit.unit_id} has max_army_size: {unit.max_army_size}")
        
        self.canvas.config(cursor="fleur")  # Change cursor to indicate movement
        
        # Update UI to reflect unit movement mode
        if hasattr(self, 'unit_mode_button'):
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_toggle_btn.config(state=tk.DISABLED)

    def show_context_menu(self, event, x, y):
        """Redirects to _show_context_menu
        
        Args:
            event: The event that triggered this method
            x: X-coordinate in image space
            y: Y-coordinate in image space
        """
        self._show_context_menu(event, x, y)
        
    def place_sprite(self, sprite_type, x, y):
        """Place a sprite on the map at the specified coordinates.
        
        Args:
            sprite_type: Type of sprite to place (e.g., 'henge', 'farm')
            x: X-coordinate in image space
            y: Y-coordinate in image space
        """
        # Check if player is selected
        if not self.app.selected_player:
            messagebox.showwarning("No Player Selected", "Please select a player first.")
            return
            
        # Check if sprite type is available
        if sprite_type not in self.sprite_manager.sprites:
            messagebox.showwarning("Sprite Not Found", f"Sprite type '{sprite_type}' not found.")
            return
        
        try:
            # Add the sprite directly to the app's placed_sprites dictionary
            position = (x, y)
            self.app.placed_sprites[position] = SpriteInfo(
                sprite_type=sprite_type,
                position=position,
                owner=self.app.selected_player.name
            )
            
            # Update the display
            self.display_map_image()
            
            # Show confirmation
            messagebox.showinfo("Success", f"{sprite_type.title()} placed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to place sprite: {str(e)}")
        
    def place_city(self, x, y):
        """Place a city on the map for the selected player.
        
        Args:
            x: X-coordinate in image space
            y: Y-coordinate in image space
        """
        if not self.app.selected_player:
            messagebox.showwarning("No Player Selected", "Please select a player first.")
            return
            
        try:
            # Check if 'city' sprite is available
            if 'city' not in self.sprite_manager.sprites:
                messagebox.showwarning("Sprite Not Found", "City sprite not found.")
                return
                
            # Add city sprite directly to the app's placed_sprites dictionary
            position = (x, y)
            self.app.placed_sprites[position] = SpriteInfo(
                sprite_type='city',
                position=position,
                owner=self.app.selected_player.name,
                name=f"{self.app.selected_player.name}'s City"
            )
            
            # Update display
            self.display_map_image()
            
            # Show confirmation
            messagebox.showinfo("Success", "City placed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to place city: {str(e)}")

    def show_unit_details(self, unit):
        """Show detailed information about a unit.
        
        Args:
            unit: The Unit object to show details for
        """
        from pyRisk.unit import UnitType, UnitClass
        
        # Build the details message
        details = f"Unit #{unit.unit_id}\n"
        details += f"Owner: {unit.owner}\n"
        details += f"Type: {unit.unit_type.value}\n"
        details += f"Position: {unit.position}\n\n"
        
        # Show unit class if available
        if hasattr(unit.unit_type, 'unit_class'):
            details += f"Class: {unit.unit_type.unit_class.value}\n\n"
        
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
        
        # Show naval unit properties if applicable
        if hasattr(unit.unit_type, 'unit_class') and unit.unit_type.unit_class == UnitClass.NAVAL:
            details += f"\nCarrying Capacity: {unit.unit_type.carrying_capacity}"
            
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
                    self.mode_toggle_btn.config(state=tk.NORMAL)
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

    def add_new_player(self):
        """Method to add a new player from the player buttons"""
        name = simpledialog.askstring("Player Name", "Enter player name:")
        if name:
            color_tuple = colorchooser.askcolor(title="Choose player color")
            if color_tuple[0]:  # color_tuple is ((r,g,b), '#rrggbb')
                color = color_tuple[0]  # Get the RGB tuple
                try:
                    # Validate the player data
                    validated_name, validated_color, _ = self.app.validate_player_data(name, color, None)
                    player = Player(validated_name, validated_color)
                    self.app.players.append(player)
                    self.update_player_buttons()
                except ValueError as e:
                    messagebox.showerror("Invalid Player Data", str(e))

    def toggle_unit_mode(self):
        """Toggle between unit movement mode and regular map editing mode"""
        self.unit_mode = not self.unit_mode if hasattr(self, 'unit_mode') else True
        print(f"\n=== Unit Mode Toggled ===")
        print(f"Unit mode is now: {'ON' if self.unit_mode else 'OFF'}")
        
        if self.unit_mode:
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_toggle_btn.config(state=tk.DISABLED)
            self.canvas.config(cursor="crosshair")
        else:
            self.unit_mode_button.config(text="Enter Unit Move Mode")
            self.mode_toggle_btn.config(state=tk.NORMAL)
            self.canvas.config(cursor="")
            self.selected_unit = None
