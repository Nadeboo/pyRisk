import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
from player import Player  # Import the Player class

class PlayersScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        tk.Label(self.frame, text="Players:").pack(pady=5)
        self.player_frame = tk.Frame(self.frame)
        self.player_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=5)
        for text, cmd in [("Add Player", self.add_player), ("Edit Player", self.edit_player),
                          ("Remove Player", self.remove_player)]:
            tk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)
        self.selected_player = None
        self.selected_player_label = None
        self.update_player_list()

    def update_player_list(self):
        # Clear existing widgets
        for widget in self.player_frame.winfo_children():
            widget.destroy()
        # Define a larger font (increase size by 4x)
        large_font = ('TkDefaultFont', 36)  # Adjust the size as needed
        self.selected_player_label = None  # Reset selection
        for player in self.app.players:
            # Create a frame for each player
            player_entry = tk.Frame(self.player_frame)
            player_entry.pack(anchor='w', padx=10, pady=5)
            # Player information
            roll_info = self.app.player_rolls.get(player.name, ("", 0, 0))
            roll_value, total_tiles, remaining_tiles = roll_info
            display_text = f"{player.name} - Roll: {roll_value}, Tiles: {remaining_tiles}/{total_tiles}"
            # Player label
            player_label = tk.Label(player_entry, text=display_text, font=large_font)
            player_label.pack(anchor='w')
            player_label.bind('<Button-1>', lambda e, p=player, l=player_label: self.on_player_select(p, l))
            # Faction label in red
            if player.faction:
                faction_label = tk.Label(player_entry, text=player.faction, font=large_font, fg='red')
                faction_label.pack(anchor='w', padx=20)

    def on_player_select(self, player, label):
        # Deselect previous selection
        if self.selected_player_label:
            self.selected_player_label.config(bg=self.player_frame.cget('bg'))
        # Select new player
        self.selected_player = player
        self.selected_player_label = label
        label.config(bg='lightblue')  # Highlight selected player

    def add_player(self):
        name = simpledialog.askstring("Player Name", "Enter player name:")
        if name:
            color = colorchooser.askcolor(title="Choose player color")
            if color[0]:
                faction = simpledialog.askstring("Faction", "Enter faction name (optional):")
                try:
                    name, color, faction = self.app.validate_player_data(name, color[0], faction)
                    player = Player(name, color, faction)
                    self.app.players.append(player)
                    self.update_player_list()
                    if hasattr(self.app.current_screen, 'update_player_buttons'):
                        self.app.current_screen.update_player_buttons()
                except ValueError as e:
                    messagebox.showerror("Invalid Input", str(e))

    def edit_player(self):
        if self.selected_player:
            player = self.selected_player
            name = simpledialog.askstring("Player Name", "Edit player name:", initialvalue=player.name)
            if name:
                color = colorchooser.askcolor(title="Choose player color", initialcolor=player.color)
                if color[0]:
                    faction = simpledialog.askstring("Faction", "Edit faction name (optional):",
                                                     initialvalue=player.faction)
                    try:
                        name, color, faction = self.app.validate_player_data(name, color[0], faction)
                        player.name = name
                        player.color = color
                        player.faction = faction
                        self.update_player_list()
                        if hasattr(self.app.current_screen, 'update_player_buttons'):
                            self.app.current_screen.update_player_buttons()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", str(e))
        else:
            messagebox.showwarning("No Selection", "Please select a player to edit.")

    def remove_player(self):
        if self.selected_player:
            # Remove the player from other players' allies and naps
            for player in self.app.players:
                if self.selected_player in player.allies:
                    player.allies.remove(self.selected_player)
                if self.selected_player in player.naps:
                    player.naps.remove(self.selected_player)
            self.app.players.remove(self.selected_player)
            self.selected_player = None
            self.selected_player_label = None
            self.update_player_list()
            if hasattr(self.app.current_screen, 'update_player_buttons'):
                self.app.current_screen.update_player_buttons()
        else:
            messagebox.showwarning("No Selection", "Please select a player to remove.")

    def destroy(self):
        """Destroy the screen's widgets and perform any necessary cleanup."""
        self.frame.destroy()