# views/players_view.py

import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
from typing import Callable, Optional
from models.player import Player


class PlayersView:
    def __init__(self, parent: tk.Frame, controller: Callable):
        """
        Initialize the PlayersView.

        Args:
            parent (tk.Frame): The parent Tkinter frame.
            controller (Callable): The controller callback to handle user actions.
        """
        self.parent = parent
        self.controller = controller
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.selected_player: Optional[Player] = None
        self.selected_player_label: Optional[tk.Label] = None
        self.setup_widgets()

    def setup_widgets(self):
        """
        Set up the widgets for the PlayersView.
        """
        # Title Label
        title_label = tk.Label(
            self.frame, text="Players", font=("Arial", 16)
        )
        title_label.pack(pady=10)

        # Players List Frame
        self.player_list_frame = tk.Frame(self.frame)
        self.player_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Buttons Frame
        buttons_frame = tk.Frame(self.frame)
        buttons_frame.pack(pady=5)

        add_btn = tk.Button(
            buttons_frame, text="Add Player", width=15,
            command=lambda: self.controller("add_player")
        )
        add_btn.pack(side=tk.LEFT, padx=5)

        edit_btn = tk.Button(
            buttons_frame, text="Edit Player", width=15,
            command=lambda: self.controller("edit_player", self.selected_player)
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        remove_btn = tk.Button(
            buttons_frame, text="Remove Player", width=15,
            command=lambda: self.controller("remove_player", self.selected_player)
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

        self.update_player_list()

    def update_player_list(self, players: list = []):
        """
        Update the list of players displayed.

        Args:
            players (list, optional): List of Player objects. Defaults to [].
        """
        # Clear existing widgets
        for widget in self.player_list_frame.winfo_children():
            widget.destroy()

        # If no players are provided, request from controller
        if not players:
            players = self.controller("get_players")

        if not players:
            no_players_label = tk.Label(
                self.player_list_frame, text="No players added.", font=("Arial", 12)
            )
            no_players_label.pack()
            return

        # Define a larger font for player entries
        large_font = ('TkDefaultFont', 12)

        for player in players:
            # Create a frame for each player
            player_entry = tk.Frame(self.player_list_frame)
            player_entry.pack(anchor='w', padx=10, pady=5)

            # Player Information
            roll_info = self.controller("get_player_roll_info", player.name)
            roll_value, total_tiles, remaining_tiles = roll_info

            display_text = f"{player.name} - Roll: {roll_value}, Tiles: {remaining_tiles}/{total_tiles}"

            # Player Label
            player_label = tk.Label(
                player_entry, text=display_text, font=large_font
            )
            player_label.pack(anchor='w')
            player_label.bind(
                '<Button-1>',
                lambda e, p=player, l=player_label: self.on_player_select(p, l)
            )

            # Faction Label in red if exists
            if player.faction:
                faction_label = tk.Label(
                    player_entry, text=player.faction, font=large_font, fg='red'
                )
                faction_label.pack(anchor='w', padx=20)

    def on_player_select(self, player: Player, label: tk.Label):
        """
        Handle the selection of a player.

        Args:
            player (Player): The selected Player object.
            label (tk.Label): The label widget associated with the player.
        """
        # Deselect previous selection
        if self.selected_player_label:
            self.selected_player_label.config(bg=self.player_list_frame.cget('bg'))

        # Select new player
        self.selected_player = player
        self.selected_player_label = label
        label.config(bg='lightblue')  # Highlight selected player

    def add_player_dialog(self) -> Optional[dict]:
        """
        Open dialogs to gather information for a new player.

        Returns:
            dict, optional: Dictionary containing 'name', 'color', and 'faction' if added. None otherwise.
        """
        name = simpledialog.askstring("Player Name", "Enter player name:")
        if not name:
            return None

        # Choose color
        color = colorchooser.askcolor(title="Choose player color")
        if not color[0]:
            return None
        color_tuple = tuple(int(c) for c in color[0])

        # Optional faction
        faction = simpledialog.askstring("Faction", "Enter faction name (optional):")
        if faction:
            faction = faction.strip()
            if not faction:
                faction = None
        else:
            faction = None

        return {"name": name, "color": color_tuple, "faction": faction}

    def edit_player_dialog(self, player: Player) -> Optional[dict]:
        """
        Open dialogs to edit an existing player's information.

        Args:
            player (Player): The Player object to edit.

        Returns:
            dict, optional: Dictionary containing updated 'name', 'color', and 'faction' if edited. None otherwise.
        """
        if not player:
            messagebox.showwarning("No Selection", "Please select a player to edit.")
            return None

        name = simpledialog.askstring("Edit Player Name", "Edit player name:", initialvalue=player.name)
        if not name:
            return None

        # Choose color
        color = colorchooser.askcolor(title="Choose player color", initialcolor=player.color)
        if not color[0]:
            return None
        color_tuple = tuple(int(c) for c in color[0])

        # Optional faction
        faction = simpledialog.askstring("Edit Faction", "Edit faction name (optional):",
                                         initialvalue=player.faction)
        if faction:
            faction = faction.strip()
            if not faction:
                faction = None
        else:
            faction = None

        return {"name": name, "color": color_tuple, "faction": faction}

    def destroy(self):
        """
        Destroy the PlayersView frame.
        """
        self.frame.destroy()
