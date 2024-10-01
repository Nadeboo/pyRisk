# roll_screen.py

import tkinter as tk
from tkinter import messagebox


class RollScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        tk.Button(self.frame, text="Configure Roll Table", command=self.configure_roll_table).pack(pady=5)
        tk.Button(self.frame, text="Roll for All Players", command=self.roll_for_all_players).pack(pady=5)
        # Current turn's roll results
        tk.Label(self.frame, text=f"Roll Results for Turn {self.app.current_turn}:").pack(pady=5)
        self.roll_results_text = tk.Text(self.frame, height=10)
        self.roll_results_text.pack(fill=tk.BOTH, expand=True)
        self.display_roll_results()
        # All previous rolls
        tk.Label(self.frame, text="All Roll Results:").pack(pady=5)
        self.all_roll_results_text = tk.Text(self.frame, height=10)
        self.all_roll_results_text.pack(fill=tk.BOTH, expand=True)
        self.display_all_roll_results()

    def roll_for_all_players(self):
        if not self.app.players:
            messagebox.showwarning("No Players", "Please add players before rolling.")
            return
        self.app.player_rolls.clear()
        self.app.roll_results.clear()
        for player in self.app.players:
            roll_value = self.app.roll_table.roll_number()
            tiles = self.app.roll_table.calculate_tiles(roll_value)
            self.app.player_rolls[player.name] = (roll_value, tiles, tiles)
            self.app.roll_results.append((player.name, roll_value, tiles))
        self.app.all_roll_results.append((self.app.current_turn, self.app.roll_results.copy()))
        self.display_roll_results()
        self.display_all_roll_results()
        # Update player list if PlayersScreen is active
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()

    def display_roll_results(self):
        self.roll_results_text.delete(1.0, tk.END)
        for name, roll, tiles in self.app.roll_results:
            self.roll_results_text.insert(tk.END, f"{name} rolled {roll} and gets {tiles} tiles.\n")

    def display_all_roll_results(self):
        self.all_roll_results_text.delete(1.0, tk.END)
        for turn, roll_results in self.app.all_roll_results:
            self.all_roll_results_text.insert(tk.END, f"Turn {turn}:\n")
            for name, roll, tiles in roll_results:
                self.all_roll_results_text.insert(tk.END, f"  {name} rolled {roll} and gets {tiles} tiles.\n")
            self.all_roll_results_text.insert(tk.END, "\n")

    def configure_roll_table(self):
        self.app.roll_table.open_configuration_window(self.app.master)

    def destroy(self):
        self.frame.destroy()
