import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox, filedialog
from PIL import Image, ImageGrab
from player import Player

class ResourceCounter(tk.Frame):
    def __init__(self, parent, name, get_value, set_value, get_per_turn, set_per_turn):
        super().__init__(parent, bg='white')
        self.name = name
        self.get_value = get_value
        self.set_value = set_value
        self.get_per_turn = get_per_turn
        self.set_per_turn = set_per_turn
        
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
        
        # Per turn increase display and control
        per_turn_frame = tk.Frame(self, bg='white')
        per_turn_frame.pack(fill=tk.X)
        tk.Label(per_turn_frame, text="/turn:", font=("Courier", 10), bg='white').pack(side=tk.LEFT)
        
        self.per_turn_var = tk.StringVar(value=str(self.get_per_turn()))
        vcmd = (self.register(self.validate_per_turn), '%P')
        per_turn_entry = tk.Entry(per_turn_frame, textvariable=self.per_turn_var, width=3, 
                                validate='all', validatecommand=vcmd)
        per_turn_entry.pack(side=tk.LEFT)
        
        self.per_turn_var.trace('w', self.on_per_turn_change)
        
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
        
    def update_display(self):
        self.value_label.config(text=str(self.get_value()))

class PlayersScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.selected_player = None
        
        # Available races
        self.races = ["HUMAN", "FAE", "WIZARD", "MERFOLK", "DWARF", "GIANT", "ORC"]
        
        self.setup_widgets()

    def setup_widgets(self):
            # Button frame at the bottom
            btn_frame = tk.Frame(self.frame)
            btn_frame.pack(side=tk.BOTTOM, pady=20)
            
            # Add/Remove and Export buttons
            for text, cmd in [("Add Player", self.add_player), 
                            ("Remove Player", self.remove_player),
                            ("Export View", self.export_view)]:
                tk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)

            # Create a canvas and scrollbar for scrolling
            self.canvas = tk.Canvas(self.frame)
            scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas)

            # Configure the canvas
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
            
            # Add mousewheel scrolling
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

            # Create window in canvas
            self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

            # Configure canvas to expand with window
            self.canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            self.canvas.configure(yscrollcommand=scrollbar.set)
            
            # Create grid frame for 3-column layout and ensure it doesn't expand
            self.grid_frame = tk.Frame(self.scrollable_frame)
            self.grid_frame.pack(side="left", anchor="nw")
            
            # Bind canvas resizing
            self.canvas.bind('<Configure>', self._on_canvas_configure)

            self.update_player_list()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_canvas_configure(self, event):
        # Update the width of the frame to match the canvas
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def create_player_box(self, player, parent):
        """Create a retro-styled box for a single player"""
        # Main outer frame for this player
        outer_frame = tk.Frame(parent)
        
        # Resource counters frame (left side)
        resources_frame = tk.Frame(outer_frame, relief=tk.SOLID, bd=2, bg='white')
        resources_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create resource counters
        resources = [
            ("GOLD", 
             lambda: player.gold, 
             lambda x: setattr(player, 'gold', x),
             lambda: player.gold_per_turn,
             lambda x: setattr(player, 'gold_per_turn', x)),
            ("RESEARCH", 
             lambda: player.research, 
             lambda x: setattr(player, 'research', x),
             lambda: player.research_per_turn,
             lambda x: setattr(player, 'research_per_turn', x)),
            ("MANA", 
             lambda: player.mana, 
             lambda x: setattr(player, 'mana', x),
             lambda: player.mana_per_turn,
             lambda x: setattr(player, 'mana_per_turn', x)),
            ("INFLUENCE", 
             lambda: player.influence, 
             lambda x: setattr(player, 'influence', x),
             lambda: player.influence_per_turn,
             lambda x: setattr(player, 'influence_per_turn', x))
        ]
        
        for name, get_val, set_val, get_per_turn, set_per_turn in resources:
            counter = ResourceCounter(resources_frame, name, get_val, set_val, get_per_turn, set_per_turn)
            counter.pack(padx=5, pady=2)
            counter.bind('<Button-1>', lambda e, p=player: self.on_player_select(p))
        
        # Middle content frame
        player_frame = tk.Frame(outer_frame, relief=tk.SOLID, bd=2, bg='white')
        player_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Player name header
        name_frame = tk.Frame(player_frame, relief=tk.SOLID, bd=1, bg='white')
        name_frame.pack(fill=tk.X)
        name_label = tk.Label(name_frame, text=player.name, font=("Courier", 14, "bold"), bg='white')
        name_label.pack(pady=5)
        
        # Race selection frame
        race_frame = tk.Frame(player_frame, bg='white')
        race_frame.pack(padx=10, pady=5)
        
        # Create variables for checkboxes
        self.race_vars = {race: tk.BooleanVar(value=player.faction == race) 
                         for race in self.races}
        
        # Create checkboxes for each race
        for race in self.races:
            race_row = tk.Frame(race_frame, bg='white')
            race_row.pack()
            
            # Add race name and checkbox
            cb = tk.Checkbutton(race_row, text=race, font=("Courier", 12),
                              variable=self.race_vars[race],
                              command=lambda p=player, r=race: self.on_race_select(p, r),
                              bg='white')
            cb.pack(side=tk.RIGHT)

        # Right side color box
        color_box = tk.Frame(outer_frame, relief=tk.SOLID, bd=2, width=60, height=150)
        color_box.pack(side=tk.LEFT, padx=10)
        color_box.pack_propagate(False)
        
        # Color display inside the box
        color_display = tk.Frame(color_box, bg='#{:02x}{:02x}{:02x}'.format(*player.color))
        color_display.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Make everything clickable for selection
        for widget in [outer_frame, player_frame, name_frame, name_label, race_frame, 
                      color_box, color_display]:
            widget.bind('<Button-1>', lambda e, p=player: self.on_player_select(p))
            
        # If this is the selected player, highlight it
        if self.selected_player == player:
            for frame in [player_frame, name_frame, race_frame]:
                frame.configure(bg='lightblue')
            name_label.configure(bg='lightblue')
            for child in race_frame.winfo_children():
                child.configure(bg='lightblue')
                for subchild in child.winfo_children():
                    subchild.configure(bg='lightblue')
                    
        return outer_frame

    def update_player_list(self):
        # Clear existing player boxes
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        # Calculate grid layout
        num_players = len(self.app.players)
        current_row = 0
        current_col = 0
        
        # Create new player boxes in a grid
        for player in self.app.players:
            player_frame = self.create_player_box(player, self.grid_frame)
            player_frame.grid(row=current_row, column=current_col, padx=5, pady=5)
            
            # Move to next column or row
            current_col += 1
            if current_col >= 3:  # 3 columns
                current_col = 0
                current_row += 1

    def add_player(self):
        name = simpledialog.askstring("Player Name", "Enter player name:")
        if name:
            color = colorchooser.askcolor(title="Choose player color")
            if color[0]:
                try:
                    name, color, _ = self.app.validate_player_data(name, color[0], None)
                    player = Player(name, color)
                    self.app.players.append(player)
                    self.update_player_list()
                    if hasattr(self.app.current_screen, 'update_player_buttons'):
                        self.app.current_screen.update_player_buttons()
                except ValueError as e:
                    messagebox.showerror("Invalid Input", str(e))

    def on_player_select(self, player):
        """Handle player selection"""
        self.selected_player = player
        self.update_player_list()

    def on_race_select(self, player, selected_race):
        """Handle race selection for a player"""
        # Uncheck other races
        for race, var in self.race_vars.items():
            if race != selected_race and var.get():
                var.set(False)
        
        # Update player faction
        if self.race_vars[selected_race].get():
            player.faction = selected_race
        else:
            player.faction = None

    def remove_player(self):
        """Remove the selected player"""
        if self.selected_player:
            self.app.players.remove(self.selected_player)
            self.selected_player = None
            self.update_player_list()
            if hasattr(self.app.current_screen, 'update_player_buttons'):
                self.app.current_screen.update_player_buttons()
        else:
            messagebox.showwarning("No Selection", "Please select a player to remove.")

    def export_view(self):
        """Export the entire players view as an image"""
        try:
            # Get file save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            
            if not file_path:
                return

            # Get the total height of all content
            bbox = self.canvas.bbox("all")
            if not bbox:
                messagebox.showwarning("Export Error", "No content to export.")
                return

            # Get the total height of all content
            total_width = self.canvas.winfo_width()
            total_height = bbox[3] - bbox[1]
            
            # Create new image with white background
            image = Image.new('RGB', (total_width, total_height), 'white')
            
            # Store current scroll position
            original_scroll = self.canvas.yview()
            
            try:
                # Temporarily configure canvas
                self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
                
                # Screenshot each part and combine
                pieces = []
                for y in range(0, total_height, 1000):  # Process in chunks
                    # Move scroll to position
                    self.canvas.yview_moveto(y / total_height)
                    self.canvas.update_idletasks()  # Wait for scroll
                    
                    # Capture portion
                    x = self.canvas.winfo_rootx()
                    y_offset = self.canvas.winfo_rooty()
                    piece = ImageGrab.grab(bbox=(
                        x,
                        y_offset,
                        x + total_width,
                        min(y_offset + 1000, y_offset + (total_height - y))
                    ))
                    pieces.append((0, y, piece))
                
                # Combine all pieces
                for x, y, piece in pieces:
                    image.paste(piece, (x, y))
                
                # Save the image
                image.save(file_path)
                messagebox.showinfo("Success", "Players view exported successfully!")
                
            finally:
                # Restore original scroll position
                self.canvas.yview_moveto(original_scroll[0])
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting view: {str(e)}")

    def destroy(self):
        self.canvas.unbind_all("<MouseWheel>")  # Remove mousewheel binding
        self.frame.destroy()