import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox, filedialog, ttk
from PIL import Image, ImageGrab
from pyRisk.player import Player
from pyRisk.custom_scrollbar import CustomScrollbar

class ResourceTooltip:
    """Tooltip widget that shows resource source breakdown"""
    def __init__(self, widget, player, resource_type):
        self.widget = widget
        self.player = player
        self.resource_type = resource_type
        self.tooltip_window = None
        
        # Bind events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.update_position)
    
    def show_tooltip(self, event=None):
        """Show the tooltip with resource breakdown"""
        # Get resource sources
        sources = self.player.get_resource_sources(self.resource_type)
        if not sources:
            return
            
        # Create tooltip window
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create frame with border
        frame = tk.Frame(self.tooltip_window, background="#ffffe0", borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        
        # Add title
        title = f"{self.resource_type.upper()} Sources"
        tk.Label(frame, text=title, background="#ffffe0", font=("Courier", 10, "bold")).pack(anchor="w", padx=5, pady=2)
        
        # Add separator
        separator = tk.Frame(frame, height=1, background="black")
        separator.pack(fill="x", padx=5, pady=2)
        
        # Add source breakdown
        total = 0
        
        # Group sources by type
        base_sources = []
        race_sources = []
        tile_sources = []
        other_sources = []
        
        for amount, description in sources:
            total += amount
            if "race bonus" in description.lower():
                race_sources.append((amount, description))
            elif "base income" in description.lower():
                base_sources.append((amount, description))
            elif "tile" in description.lower():
                tile_sources.append((amount, description))
            else:
                other_sources.append((amount, description))
        
        # Display base income first
        for amount, description in base_sources:
            source_text = f"+{amount}: {description}"
            tk.Label(frame, text=source_text, background="#ffffe0", font=("Courier", 9)).pack(anchor="w", padx=5, pady=1)
        
        # Display race bonuses with highlight
        if race_sources:
            race_frame = tk.Frame(frame, background="#ffffc0")  # Slightly different background
            race_frame.pack(fill="x", padx=2, pady=2)
            
            for amount, description in race_sources:
                source_text = f"+{amount}: {description}"
                tk.Label(race_frame, text=source_text, background="#ffffc0", font=("Courier", 9, "bold")).pack(anchor="w", padx=5, pady=1)
        
        # Display tile sources
        for amount, description in tile_sources:
            source_text = f"+{amount}: {description}"
            tk.Label(frame, text=source_text, background="#ffffe0", font=("Courier", 9)).pack(anchor="w", padx=5, pady=1)
        
        # Display other sources
        for amount, description in other_sources:
            source_text = f"+{amount}: {description}"
            tk.Label(frame, text=source_text, background="#ffffe0", font=("Courier", 9)).pack(anchor="w", padx=5, pady=1)
        
        # Add total
        separator = tk.Frame(frame, height=1, background="black")
        separator.pack(fill="x", padx=5, pady=2)
        tk.Label(frame, text=f"Total: +{total}/turn", background="#ffffe0", font=("Courier", 10, "bold")).pack(anchor="w", padx=5, pady=2)
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def update_position(self, event=None):
        """Update tooltip position if mouse moves"""
        if self.tooltip_window:
            x, y = event.x_root + 15, event.y_root + 10
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

class ResourceCounter(tk.Frame):
    def __init__(self, parent, name, get_value, set_value, get_per_turn, set_per_turn, player=None):
        super().__init__(parent, bg='white')
        self.name = name
        self.get_value = get_value
        self.set_value = set_value
        self.get_per_turn = get_per_turn
        self.set_per_turn = set_per_turn
        self.player = player
        self.resource_type = name.lower()  # Convert name to lowercase for resource type
        
        # Resource name and current value
        name_frame = tk.Frame(self, bg='white')
        name_frame.pack(fill=tk.X)
        tk.Label(name_frame, text=f"{name}:", font=("Courier", 12), bg='white').pack(side=tk.LEFT)
        
        # Counter controls
        counter_frame = tk.Frame(self, bg='white')
        counter_frame.pack(fill=tk.X)
        
        tk.Button(counter_frame, text="-", command=self.decrement).pack(side=tk.LEFT)
        self.value_label = tk.Label(counter_frame, text=str(self.get_value()), width=5, font=("Courier", 12), bg='white')
        self.value_label.pack(side=tk.LEFT)
        tk.Button(counter_frame, text="+", command=self.increment).pack(side=tk.LEFT)
        
        # Per turn display (read-only)
        per_turn_frame = tk.Frame(self, bg='white')
        per_turn_frame.pack(fill=tk.X)
        per_turn_label_text = tk.Label(per_turn_frame, text="/turn:", font=("Courier", 10), bg='white')
        per_turn_label_text.pack(side=tk.LEFT)
        self.per_turn_label = tk.Label(per_turn_frame, text="0", font=("Courier", 10), bg='white')
        self.per_turn_label.pack(side=tk.LEFT)
        
        # Race bonus indicator
        self.race_indicator = tk.Label(per_turn_frame, text="", font=("Courier", 10), bg='white', fg='blue')
        self.race_indicator.pack(side=tk.LEFT, padx=(5, 0))
        
        # Add tooltip if player is provided
        if player:
            # Create tooltip for the per-turn label
            self.tooltip = ResourceTooltip(self.per_turn_label, player, self.resource_type)
        
        # Initial update
        self.update_display()
        
    def validate_per_turn(self, new_value):
        if new_value == "":
            return True
        try:
            value = int(new_value)
            return True
        except ValueError:
            return False
            
    def on_per_turn_change(self, *args):
        try:
            value = int(self.per_turn_var.get())
            self.set_per_turn(value)
        except ValueError:
            pass
            
    def increment(self):
        self.set_value(self.get_value() + 1)
        self.update_display()
        
    def decrement(self):
        self.set_value(self.get_value() - 1)
        self.update_display()

    def update_per_turn_display(self):
        """Update the display of the calculated per-turn value"""
        calculated = self.get_per_turn()
        if calculated > 0:
            self.per_turn_display.config(text=f"(+{calculated} from tiles)")
        else:
            self.per_turn_display.config(text="")
        
    def update_display(self):
        """Update both the current value and per-turn displays"""
        self.value_label.config(text=str(self.get_value()))
        per_turn = self.get_per_turn()
        self.per_turn_label.config(text=str(per_turn))
        
        # Update tooltip color based on value
        if per_turn > 0:
            # Make the label more noticeable for positive values
            self.per_turn_label.config(fg="green", font=("Courier", 10, "bold"))
        else:
            # Reset to default for zero or negative values
            self.per_turn_label.config(fg="black", font=("Courier", 10))
            
        # Check if there's a race bonus for this resource
        if self.player:
            has_race_bonus = False
            for amount, description in self.player.get_resource_sources(self.resource_type):
                if "race bonus" in description.lower():
                    has_race_bonus = True
                    self.race_indicator.config(text="(Race)", fg="blue")
                    break
            
            if not has_race_bonus:
                self.race_indicator.config(text="")

class PlayersScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_theme = app.current_theme
        
        self.frame = tk.Frame(parent, bg=self.current_theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_widgets()
        
    def setup_widgets(self):
        # Title
        title_frame = tk.Frame(self.frame, bg=self.current_theme['bg'])
        title_frame.pack(pady=20)
        title_label = tk.Label(
            title_frame, 
            text="Player Management", 
            font=("Arial", 24), 
            bg=self.current_theme['bg'],
            fg=self.current_theme['fg']
        )
        title_label.pack()
        
        # Players container with scrollbar
        self.container_frame = tk.Frame(self.frame, bg=self.current_theme['bg'])
        self.container_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(
            self.container_frame, 
            bg=self.current_theme['bg'],
            highlightthickness=0,
            bd=0
        )
        
        # Add custom scrollbar
        self.scrollbar = CustomScrollbar(
            self.container_frame,
            orientation="vertical",
            command=self.canvas.yview,
            bg=self.current_theme.get('scrollbar_bg', self.current_theme['bg']),
            fg=self.current_theme.get('scrollbar_fg', self.current_theme['button_bg']),
            width=12
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame inside canvas for players
        self.players_frame = tk.Frame(self.canvas, bg=self.current_theme['bg'])
        self.canvas_frame = self.canvas.create_window(
            (0, 0), 
            window=self.players_frame, 
            anchor=tk.NW
        )
        
        # Add player button
        self.add_btn = tk.Button(
            self.frame, 
            text="Add Player", 
            command=self.add_player,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            activebackground=self.current_theme['highlight_bg'],
            activeforeground=self.current_theme['highlight_fg']
        )
        self.add_btn.pack(pady=20)
        
        # Configure canvas scrolling
        self.players_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Display existing players
        self.display_players()
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_mousewheel(self, event):
        # Respond to mouse wheel in canvas only if the mouse is over the canvas
        if event.widget == self.canvas:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def add_player(self):
        """Add a new player to the game"""
        player_num = len(self.app.players) + 1
        default_name = f"Player {player_num}"
        
        # Get player name
        name = simpledialog.askstring("Player Name", "Enter player name:", initialvalue=default_name)
        if not name:
            return
            
        # Choose player color
        color_rgb, color_hex = colorchooser.askcolor(title="Choose Player Color")
        if not color_rgb:
            return
        
        # Choose faction
        factions = ["HUMAN", "WIZARD", "UNDEAD", "NONE"]
        faction_dialog = tk.Toplevel(self.frame)
        faction_dialog.title("Choose Faction")
        faction_dialog.transient(self.frame)
        faction_dialog.grab_set()
        
        # Apply theme
        faction_dialog.configure(bg=self.current_theme['bg'])
        
        faction_var = tk.StringVar()
        faction_var.set(factions[0])  # Default to first faction
        
        faction_label = tk.Label(
            faction_dialog, 
            text="Select faction:", 
            bg=self.current_theme['bg'],
            fg=self.current_theme['fg']
        )
        faction_label.pack(pady=10)
        
        # Create styled radio buttons
        for faction in factions:
            radio = tk.Radiobutton(
                faction_dialog, 
                text=faction, 
                variable=faction_var, 
                value=faction,
                bg=self.current_theme['bg'],
                fg=self.current_theme['fg'],
                activebackground=self.current_theme['highlight_bg'],
                activeforeground=self.current_theme['highlight_fg'],
                selectcolor=self.current_theme['bg']  # Background of the radio button when selected
            )
            radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(faction_dialog, bg=self.current_theme['bg'])
        buttons_frame.pack(pady=15)
        
        def on_ok():
            faction_dialog.selected_faction = faction_var.get()
            faction_dialog.destroy()
            
        def on_cancel():
            faction_dialog.selected_faction = None
            faction_dialog.destroy()
        
        # OK and Cancel buttons
        ok_button = tk.Button(
            buttons_frame, 
            text="OK", 
            command=on_ok,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            activebackground=self.current_theme['highlight_bg'],
            activeforeground=self.current_theme['highlight_fg']
        )
        ok_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(
            buttons_frame, 
            text="Cancel", 
            command=on_cancel,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            activebackground=self.current_theme['highlight_bg'],
            activeforeground=self.current_theme['highlight_fg']
        )
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # Center the dialog
        self.frame.update_idletasks()
        width = faction_dialog.winfo_width()
        height = faction_dialog.winfo_height()
        x = (faction_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (faction_dialog.winfo_screenheight() // 2) - (height // 2)
        faction_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Wait for dialog to close
        faction_dialog.wait_window()
        
        # If dialog was cancelled
        if not hasattr(faction_dialog, 'selected_faction') or faction_dialog.selected_faction is None:
            return
            
        faction = faction_dialog.selected_faction
        
        try:
            # Validate player data
            name, color_rgb, faction = self.app.validate_player_data(name, color_rgb, faction)
            
            # Add player
            self.app.players.append(Player(name, color_rgb, faction))
            self.display_players()
        except ValueError as e:
            tk.messagebox.showerror("Invalid Data", str(e))
    
    def display_players(self):
        """Display all players"""
        # Clear existing player frames
        for widget in self.players_frame.winfo_children():
            widget.destroy()
            
        # Create frame for each player
        for i, player in enumerate(self.app.players):
            # Create player frame
            player_frame = tk.Frame(
                self.players_frame,
                borderwidth=2,
                relief="raised",
                bg=self.current_theme['bg'],  # <-- ONLY change: use theme bg color instead of white
                padx=10,
                pady=10
            )
            player_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # Left side
            left_frame = tk.Frame(player_frame, bg=self.current_theme['bg'])  # <-- ONLY change: use theme bg
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Player name label
            name_label = tk.Label(
                left_frame, 
                text=player.name, 
                font=("Arial", 16, "bold"),
                bg=self.current_theme['bg'],  # <-- ONLY change: use theme bg
                fg=self.current_theme['fg']   # <-- ONLY change: use theme fg
            )
            name_label.pack(anchor=tk.W)
            
            # Player faction
            faction_label = tk.Label(
                left_frame, 
                text=f"Faction: {player.faction}" if player.faction else "Faction: None",
                bg=self.current_theme['bg'],  # <-- ONLY change: use theme bg
                fg=self.current_theme['fg']   # <-- ONLY change: use theme fg
            )
            faction_label.pack(anchor=tk.W)
            
            # Player resources (if in Tregonia mode)
            if self.app.roll_mode == 'tregonia':
                resources_frame = tk.Frame(left_frame, bg=self.current_theme['bg'])  # <-- ONLY change: use theme bg
                resources_frame.pack(anchor=tk.W, pady=(10, 0))
                
                resources = [
                    ("Gold", player.gold_per_turn),
                    ("Research", player.research_per_turn),
                    ("Mana", player.mana_per_turn),
                    ("Influence", player.influence_per_turn)
                ]
                
                for resource, value in resources:
                    resource_frame = tk.Frame(resources_frame, bg=self.current_theme['bg'])  # <-- ONLY change: use theme bg
                    resource_frame.pack(side=tk.LEFT, padx=(0, 15))
                    
                    resource_name = tk.Label(
                        resource_frame, 
                        text=resource, 
                        font=("Arial", 10),
                        bg=self.current_theme['bg'],  # <-- ONLY change: use theme bg
                        fg=self.current_theme['fg']   # <-- ONLY change: use theme fg
                    )
                    resource_name.pack(anchor=tk.W)
                    
                    resource_value = tk.Label(
                        resource_frame, 
                        text=f"+{value}/turn",
                        font=("Arial", 12, "bold"),
                        bg=self.current_theme['bg'],  # <-- ONLY change: use theme bg
                        fg=self.current_theme['fg']   # <-- ONLY change: use theme fg
                    )
                    resource_value.pack(anchor=tk.W)
            
            # Right side
            right_frame = tk.Frame(player_frame, bg=self.current_theme['bg'])  # <-- ONLY change: use theme bg
            right_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Color display
            color_frame = tk.Frame(
                right_frame, 
                width=50, 
                height=50, 
                bg='#%02x%02x%02x' % tuple(int(c) for c in player.color)
            )
            color_frame.pack(side=tk.TOP, pady=(0, 5))
            
            # Edit/Delete buttons
            buttons_frame = tk.Frame(right_frame, bg=self.current_theme['bg'])  # <-- ONLY change: use theme bg
            buttons_frame.pack(side=tk.BOTTOM)
            
            edit_btn = tk.Button(
                buttons_frame, 
                text="Edit",
                command=lambda p=player: self.edit_player(p),
                bg=self.current_theme['button_bg'],
                fg=self.current_theme['button_fg'],
                activebackground=self.current_theme['highlight_bg'],
                activeforeground=self.current_theme['highlight_fg'],
                padx=5
            )
            edit_btn.pack(side=tk.LEFT, padx=2)
            
            delete_btn = tk.Button(
                buttons_frame, 
                text="Delete",
                command=lambda p=player: self.delete_player(p),
                bg=self.current_theme['button_bg'],
                fg=self.current_theme['button_fg'],
                activebackground=self.current_theme['highlight_bg'],
                activeforeground=self.current_theme['highlight_fg'],
                padx=5
            )
            delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def get_contrasting_text_color(self, bg_color):
        """Return a contrasting text color (black/white) based on background color"""
        # For a theme background, just use the theme's foreground color
        return self.current_theme['fg']
    
    def edit_player(self, player):
        """Edit an existing player"""
        # Get player name
        name = simpledialog.askstring("Player Name", "Enter player name:", initialvalue=player.name)
        if not name:
            return
            
        # Choose player color
        initial_color = '#%02x%02x%02x' % tuple(int(c) for c in player.color)
        color_rgb, color_hex = colorchooser.askcolor(title="Choose Player Color", initialcolor=initial_color)
        if not color_rgb:
            return
        
        # Choose faction
        factions = ["HUMAN", "WIZARD", "UNDEAD", "NONE"]
        faction_dialog = tk.Toplevel(self.frame)
        faction_dialog.title("Choose Faction")
        faction_dialog.transient(self.frame)
        faction_dialog.grab_set()
        
        # Apply theme
        faction_dialog.configure(bg=self.current_theme['bg'])
        
        faction_var = tk.StringVar()
        faction_var.set(player.faction if player.faction else "NONE")  # Default to player's current faction
        
        faction_label = tk.Label(
            faction_dialog, 
            text="Select faction:", 
            bg=self.current_theme['bg'],
            fg=self.current_theme['fg']
        )
        faction_label.pack(pady=10)
        
        # Create styled radio buttons
        for faction in factions:
            radio = tk.Radiobutton(
                faction_dialog, 
                text=faction, 
                variable=faction_var, 
                value=faction,
                bg=self.current_theme['bg'],
                fg=self.current_theme['fg'],
                activebackground=self.current_theme['highlight_bg'],
                activeforeground=self.current_theme['highlight_fg'],
                selectcolor=self.current_theme['bg']  # Background of the radio button when selected
            )
            radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(faction_dialog, bg=self.current_theme['bg'])
        buttons_frame.pack(pady=15)
        
        def on_ok():
            faction_dialog.selected_faction = faction_var.get()
            faction_dialog.destroy()
            
        def on_cancel():
            faction_dialog.selected_faction = None
            faction_dialog.destroy()
        
        # OK and Cancel buttons
        ok_button = tk.Button(
            buttons_frame, 
            text="OK", 
            command=on_ok,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            activebackground=self.current_theme['highlight_bg'],
            activeforeground=self.current_theme['highlight_fg']
        )
        ok_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(
            buttons_frame, 
            text="Cancel", 
            command=on_cancel,
            bg=self.current_theme['button_bg'],
            fg=self.current_theme['button_fg'],
            activebackground=self.current_theme['highlight_bg'],
            activeforeground=self.current_theme['highlight_fg']
        )
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # Center the dialog
        self.frame.update_idletasks()
        width = faction_dialog.winfo_width()
        height = faction_dialog.winfo_height()
        x = (faction_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (faction_dialog.winfo_screenheight() // 2) - (height // 2)
        faction_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Wait for dialog to close
        faction_dialog.wait_window()
        
        # If dialog was cancelled
        if not hasattr(faction_dialog, 'selected_faction') or faction_dialog.selected_faction is None:
            return
            
        faction = faction_dialog.selected_faction
        if faction == "NONE":
            faction = None
        
        try:
            # Check if the name is different from the current name
            if name != player.name:
                # Check if the name is already taken by another player
                for p in self.app.players:
                    if p != player and p.name.lower() == name.lower():
                        raise ValueError(f"Player name '{name}' is already taken.")
            
            # Update player data
            player.name = name
            player.color = color_rgb
            player.faction = faction
            
            # Redisplay players
            self.display_players()
            
            # Update resource tiles if in Tregonia mode
            if self.app.roll_mode == 'tregonia':
                self.app.update_player_resources()
                self.display_players()  # Refresh display to show updated resources
                
        except ValueError as e:
            tk.messagebox.showerror("Invalid Data", str(e))
    
    def delete_player(self, player):
        """Delete a player"""
        # Ask for confirmation
        confirm = tk.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete player {player.name}?")
        if not confirm:
            return
            
        # Remove the player
        self.app.players.remove(player)
        
        # Redisplay players
        self.display_players()
        
        # Update resource tiles if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.app.update_player_resources()
    
    def destroy(self):
        """Clean up resources when the screen is destroyed"""
        self.canvas.unbind_all("<MouseWheel>")
        self.frame.destroy()
        
    def update_player_list(self):
        """Update the player list - can be called from other screens
        to refresh player resource information"""
        try:
            # Redisplay all players with updated information
            self.display_players()
            print("Updated player list to show current resource information")
        except Exception as e:
            print(f"Error updating player list: {e}")
        
    def apply_theme(self, theme):
        """Apply a theme to all widgets in this screen"""
        self.current_theme = theme
        
        # Apply to main frame
        self.frame.configure(bg=theme['bg'])
        
        # Apply to all child widgets recursively
        self.apply_theme_to_widgets(self.frame)
        
        # Redisplay players with new theme
        self.display_players()
        
    def apply_theme_to_widgets(self, parent):
        """Apply theme to all widgets in the given parent widget"""
        for widget in parent.winfo_children():
            try:
                if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                    # Don't change color display frames
                    if widget.winfo_width() != 50 or widget.winfo_height() != 50:
                        widget.configure(bg=self.current_theme['bg'])
                elif isinstance(widget, tk.Button):
                    widget.configure(
                        bg=self.current_theme['button_bg'],
                        fg=self.current_theme['button_fg'],
                        activebackground=self.current_theme['highlight_bg'],
                        activeforeground=self.current_theme['highlight_fg']
                    )
                elif isinstance(widget, tk.Label):
                    widget.configure(
                        bg=self.current_theme['bg'],
                        fg=self.current_theme['fg']
                    )
                elif isinstance(widget, tk.Canvas):
                    widget.configure(
                        bg=self.current_theme['bg'],
                        highlightbackground=self.current_theme['bg']
                    )
                # Apply to custom scrollbar
                if hasattr(widget, 'canvas') and hasattr(widget, 'set'):
                    try:
                        widget.config(
                            bg=self.current_theme.get('scrollbar_bg', self.current_theme['bg']),
                            fg=self.current_theme.get('scrollbar_fg', self.current_theme['button_bg'])
                        )
                    except (tk.TclError, AttributeError):
                        pass
            except (tk.TclError, AttributeError):
                # Skip widgets that can't be configured
                pass
            
            # Apply to all children of this widget
            if widget.winfo_children():
                self.apply_theme_to_widgets(widget)