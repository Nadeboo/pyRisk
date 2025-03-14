import tkinter as tk

class SidebarManager:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Create sidebar frame
        self.sidebar = tk.Frame(parent, width=150, bg='lightgrey')
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Initialize state variables
        self.player_buttons = []
        self.resource_buttons = []
        self.resource_paint_mode = None
        self.RESOURCE_COLORS = {
            'unactivated': (0, 255, 0),
            'gold': (255, 255, 0),
            'mana': (0, 255, 255)
        }
        
        # Setup sidebar components
        self.setup_sidebar()

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
        for resource_type in ['unactivated', 'gold', 'mana']:
            btn = tk.Button(
                self.sidebar,
                text=resource_type.capitalize(),
                command=lambda t=resource_type: self.select_resource_paint(t)
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.resource_buttons.append(btn)

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

    def update_player_buttons(self):
        """Update the player buttons in the sidebar"""
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
        """Update button appearances based on selected player"""
        for btn in self.player_buttons:
            if self.app.selected_player and btn.player_name == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def toggle_mode(self):
        """Toggle between color and erase mode"""
        if self.app.mode == 'color':
            self.app.mode = 'erase'
            self.mode_button.config(text="Switch to Color Mode")
        else:
            self.app.mode = 'color'
            self.mode_button.config(text="Switch to Erase Mode")

    def toggle_unit_mode(self):
        """Toggle unit movement mode"""
        self.app.unit_mode = not self.app.unit_mode
        if self.app.unit_mode:
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_button.config(state=tk.DISABLED)
            self.app.canvas.config(cursor="crosshair")
        else:
            self.unit_mode_button.config(text="Enter Unit Move Mode")
            self.mode_button.config(state=tk.NORMAL)
            self.app.canvas.config(cursor="")
            self.app.selected_unit = None

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
                if pos in self.app.sprite_manager.placed_sprites:
                    sprite_info = self.app.sprite_manager.placed_sprites[pos]
                    sprite_info.owner = sprite_state['owner']
                    sprite_info.extra_data = sprite_state['extra_data'].copy() if sprite_state['extra_data'] else {}
                    sprite_info.name = sprite_state['name']
        
        # Make sure to get a fresh ImageDraw object
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        
        # Ensure the display is updated
        self.app.display_map_image()
        
        # Update all relevant UI elements
        self.update_player_buttons()
        
        # Update resource ownership if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.app.update_resource_ownership() 