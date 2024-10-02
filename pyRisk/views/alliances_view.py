# views/alliances_view.py

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
from models.player import Player


class AlliancesView:
    def __init__(self, parent: tk.Frame, controller: Callable):
        """
        Initialize the AlliancesView.

        Args:
            parent (tk.Frame): The parent Tkinter frame.
            controller (Callable): The controller callback to handle user actions.
        """
        self.parent = parent
        self.controller = controller
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.selected_player1: Optional[Player] = None
        self.selected_player2: Optional[Player] = None
        self.setup_widgets()

    def setup_widgets(self):
        """
        Set up the widgets for the AlliancesView.
        """
        title_label = tk.Label(
            self.frame, text="Manage Alliances and NAPs", font=("Arial", 16)
        )
        title_label.pack(pady=10)

        players = self.controller("get_players")
        player_names = [player.name for player in players]

        # Player 1 Selection
        self.player1_var = tk.StringVar()
        self.player1_var.set(player_names[0] if player_names else "No Players")
        tk.Label(self.frame, text="Select Player 1:").pack()
        self.player1_menu = tk.OptionMenu(
            self.frame, self.player1_var, *player_names
        )
        self.player1_menu.pack()

        # Player 2 Selection
        self.player2_var = tk.StringVar()
        self.player2_var.set(player_names[0] if player_names else "No Players")
        tk.Label(self.frame, text="Select Player 2:").pack()
        self.player2_menu = tk.OptionMenu(
            self.frame, self.player2_var, *player_names
        )
        self.player2_menu.pack()

        # Buttons
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=5)

        add_alliance_btn = tk.Button(
            btn_frame, text="Add Alliance",
            command=lambda: self.controller("add_alliance",
                                            self.player1_var.get(),
                                            self.player2_var.get())
        )
        add_alliance_btn.pack(side=tk.LEFT, padx=5)

        add_nap_btn = tk.Button(
            btn_frame, text="Add NAP",
            command=lambda: self.controller("add_nap",
                                            self.player1_var.get(),
                                            self.player2_var.get())
        )
        add_nap_btn.pack(side=tk.LEFT, padx=5)

        # Disable buttons if no players
        if not player_names:
            add_alliance_btn.config(state=tk.DISABLED)
            add_nap_btn.config(state=tk.DISABLED)

        # Alliances Display
        tk.Label(self.frame, text="Current Alliances:", font=("Arial", 14)).pack(pady=10)
        self.alliances_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.alliances_text.pack(fill=tk.BOTH, expand=True, padx=10)

        # NAPs Display
        tk.Label(self.frame, text="Current Non-Aggression Pacts (NAPs):", font=("Arial", 14)).pack(pady=10)
        self.naps_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.naps_text.pack(fill=tk.BOTH, expand=True, padx=10)

        self.update_displays()

    def update_displays(self):
        """
        Update the alliances and NAPs display areas.
        """
        self.update_alliances_text()
        self.update_naps_text()

    def update_alliances_text(self):
        """
        Update the alliances display text widget.
        """
        self.alliances_text.config(state=tk.NORMAL)
        self.alliances_text.delete(1.0, tk.END)
        alliances = []
        players = self.controller("get_players")
        for player in players:
            for ally in player.allies:
                if player.name < ally.name:
                    alliances.append(f"{player.name} ↔ {ally.name}")
        if alliances:
            self.alliances_text.insert(tk.END, '\n'.join(alliances))
        else:
            self.alliances_text.insert(tk.END, "No alliances.")
        self.alliances_text.config(state=tk.DISABLED)

    def update_naps_text(self):
        """
        Update the NAPs display text widget.
        """
        self.naps_text.config(state=tk.NORMAL)
        self.naps_text.delete(1.0, tk.END)
        naps = []
        players = self.controller("get_players")
        for player in players:
            for nap in player.naps:
                if player.name < nap.name:
                    naps.append(f"{player.name} ↔ {nap.name}")
        if naps:
            self.naps_text.insert(tk.END, '\n'.join(naps))
        else:
            self.naps_text.insert(tk.END, "No Non-Aggression Pacts.")
        self.naps_text.config(state=tk.DISABLED)

    def refresh(self):
        """
        Refresh the alliances and NAPs displays.
        """
        self.update_displays()

    def destroy(self):
        """
        Destroy the AlliancesView frame.
        """
        self.frame.destroy()
