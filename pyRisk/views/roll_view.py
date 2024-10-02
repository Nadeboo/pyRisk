# views/roll_view.py

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
from models.roll_table import RollTable


class RollView:
    def __init__(self, parent: tk.Frame, controller: Callable):
        """
        Initialize the RollView.

        Args:
            parent (tk.Frame): The parent Tkinter frame.
            controller (Callable): The controller callback to handle user actions.
        """
        self.parent = parent
        self.controller = controller
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.roll_table: Optional[RollTable] = None
        self.setup_widgets()

    def setup_widgets(self):
        """
        Set up the widgets for the RollView.
        """
        title_label = tk.Label(
            self.frame, text="Rolling Mechanism", font=("Arial", 16)
        )
        title_label.pack(pady=10)

        config_btn = tk.Button(
            self.frame, text="Configure Roll Table",
            command=lambda: self.controller("configure_roll_table")
        )
        config_btn.pack(pady=5)

        roll_btn = tk.Button(
            self.frame, text="Roll for All Players",
            command=lambda: self.controller("roll_for_all_players")
        )
        roll_btn.pack(pady=5)

        # Current Turn's Roll Results
        self.current_roll_label = tk.Label(
            self.frame, text="Roll Results for Turn 0:", font=("Arial", 14)
        )
        self.current_roll_label.pack(pady=10)

        self.roll_results_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.roll_results_text.pack(fill=tk.BOTH, expand=True, padx=10)

        # All Roll Results
        self.all_rolls_label = tk.Label(
            self.frame, text="All Roll Results:", font=("Arial", 14)
        )
        self.all_rolls_label.pack(pady=10)

        self.all_rolls_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.all_rolls_text.pack(fill=tk.BOTH, expand=True, padx=10)

        self.update_roll_displays()

    def update_roll_displays(self):
        """
        Update the current and all roll results displays.
        """
        self.update_current_roll()
        self.update_all_rolls()

    def update_current_roll(self):
        """
        Update the current turn's roll results.
        """
        turn, roll_results = self.controller("get_current_roll")
        self.current_roll_label.config(text=f"Roll Results for Turn {turn}:")
        self.roll_results_text.config(state=tk.NORMAL)
        self.roll_results_text.delete(1.0, tk.END)
        for name, roll, tiles in roll_results:
            self.roll_results_text.insert(tk.END, f"{name} rolled {roll} and gets {tiles} tiles.\n")
        self.roll_results_text.config(state=tk.DISABLED)

    def update_all_rolls(self):
        """
        Update the all roll results display.
        """
        all_rolls = self.controller("get_all_rolls")
        self.all_rolls_text.config(state=tk.NORMAL)
        self.all_rolls_text.delete(1.0, tk.END)
        for turn, roll_results in all_rolls:
            self.all_rolls_text.insert(tk.END, f"Turn {turn}:\n")
            for name, roll, tiles in roll_results:
                self.all_rolls_text.insert(tk.END, f"  {name} rolled {roll} and gets {tiles} tiles.\n")
            self.all_rolls_text.insert(tk.END, "\n")
        self.all_rolls_text.config(state=tk.DISABLED)

    def refresh(self):
        """
        Refresh the roll results displays.
        """
        self.update_roll_displays()

    def destroy(self):
        """
        Destroy the RollView frame.
        """
        self.frame.destroy()
