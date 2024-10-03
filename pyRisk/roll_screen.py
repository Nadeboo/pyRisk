# roll_screen.py

import tkinter as tk
from tkinter import messagebox
from roll_table import RollTable
from PIL import ImageTk, ImageDraw
from game_screen import GameScreen  # Ensure this import exists

class RollScreen:
    MAX_ROLL_LENGTH = 20  # Max digits allowed

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        if self.app.roll_mode == 'application':
            self.setup_application_mode()
        elif self.app.roll_mode == 'external':
            self.setup_external_mode()
        else:
            messagebox.showerror("Invalid Roll Mode", f"Unknown roll mode: {self.app.roll_mode}")
            self.app.show_game_screen()

    def setup_application_mode(self):
        tk.Button(self.frame, text="Configure Roll Table", command=self.configure_roll_table).pack(pady=5)
        tk.Button(self.frame, text="Roll for All Players", command=self.roll_for_all_players).pack(pady=5)
        tk.Label(self.frame, text=f"Roll Results for Turn {self.app.current_turn}:").pack(pady=5)
        self.roll_results_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.roll_results_text.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.frame, text="All Roll Results:").pack(pady=5)
        self.all_roll_results_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.all_roll_results_text.pack(fill=tk.BOTH, expand=True)
        self.display_roll_results()
        self.display_all_roll_results()

    def setup_external_mode(self):
        tk.Label(self.frame, text="External Roll Input", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.frame, text="Enter each player's roll number below:").pack(pady=5)
        self.external_roll_entries = {}

        tk.Button(self.frame, text="Configure Roll Table", command=self.configure_roll_table).pack(pady=5)

        players_frame = tk.Frame(self.frame)
        players_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        for player in self.app.players:
            player_frame = tk.Frame(players_frame)
            player_frame.pack(fill=tk.X, pady=2)
            tk.Label(player_frame, text=player.name, width=20, anchor='w').pack(side=tk.LEFT)
            roll_var = tk.StringVar()
            roll_entry = tk.Entry(player_frame, textvariable=roll_var, width=30)
            roll_entry.pack(side=tk.LEFT, padx=5)
            roll_entry.bind("<KeyRelease>", lambda event, var=roll_var: self.limit_roll_length(var))
            self.external_roll_entries[player.name] = roll_var

        tk.Button(self.frame, text="Submit Rolls", command=self.submit_external_rolls).pack(pady=10)
        self.status_label = tk.Label(self.frame, text="", fg="green")
        self.status_label.pack(pady=5)

        tk.Label(self.frame, text=f"Roll Results for Turn {self.app.current_turn}:").pack(pady=5)
        self.roll_results_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.roll_results_text.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.frame, text="All Roll Results:").pack(pady=5)
        self.all_roll_results_text = tk.Text(self.frame, height=10, state=tk.DISABLED)
        self.all_roll_results_text.pack(fill=tk.BOTH, expand=True)
        self.display_roll_results()
        self.display_all_roll_results()

    def limit_roll_length(self, var):
        text = var.get()
        if len(text) > self.MAX_ROLL_LENGTH:
            var.set(text[:self.MAX_ROLL_LENGTH])

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
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()

    def display_roll_results(self):
        if self.roll_results_text:
            self.roll_results_text.config(state=tk.NORMAL)
            self.roll_results_text.delete(1.0, tk.END)
            for name, roll, tiles in self.app.roll_results:
                self.roll_results_text.insert(tk.END, f"{name} rolled {roll} and gets {tiles} tiles.\n")
            self.roll_results_text.config(state=tk.DISABLED)

    def display_all_roll_results(self):
        if self.all_roll_results_text:
            self.all_roll_results_text.config(state=tk.NORMAL)
            self.all_roll_results_text.delete(1.0, tk.END)
            for turn, roll_results in self.app.all_roll_results:
                self.all_roll_results_text.insert(tk.END, f"Turn {turn}:\n")
                for name, roll, tiles in roll_results:
                    self.all_roll_results_text.insert(tk.END, f"  {name} rolled {roll} and gets {tiles} tiles.\n")
                self.all_roll_results_text.insert(tk.END, "\n")
            self.all_roll_results_text.config(state=tk.DISABLED)

    def configure_roll_table(self):
        self.app.roll_table.open_configuration_window(self.app.master)

    def submit_external_rolls(self):
        all_valid = True
        player_rolls = {}
        error_messages = []

        # Validate inputs
        for player_name, roll_var in self.external_roll_entries.items():
            roll_str = roll_var.get().strip()
            if not roll_str.isdigit():
                all_valid = False
                error_messages.append(f"Invalid roll number for {player_name}. Must be digits only.")
            elif not roll_str:
                all_valid = False
                error_messages.append(f"Roll number for {player_name} cannot be empty.")
            elif len(roll_str) > self.MAX_ROLL_LENGTH:
                all_valid = False
                error_messages.append(f"Roll number for {player_name} exceeds maximum length of {self.MAX_ROLL_LENGTH}.")
            else:
                player_rolls[player_name] = roll_str

        if not all_valid:
            messagebox.showerror("Invalid Input", "\n".join(error_messages))
            return

        # Process rolls
        for player_name, roll_str in player_rolls.items():
            try:
                roll_value = int(roll_str)
                tiles = self.app.roll_table.calculate_tiles(roll_value)
            except ValueError:
                messagebox.showerror("Roll Processing Error", f"Invalid roll number for {player_name}.")
                return
            except Exception as e:
                messagebox.showerror("Roll Processing Error", f"Error processing roll for {player_name}: {e}")
                return

            self.app.player_rolls[player_name] = (roll_str, tiles, tiles)
            self.assign_tiles_to_player(player_name, tiles)

        # Record and display results
        self.app.roll_results = [(name, roll, tiles) for name, (roll, tiles, _) in self.app.player_rolls.items()]
        self.app.all_roll_results.append((self.app.current_turn, self.app.roll_results.copy()))
        self.display_roll_results()
        self.display_all_roll_results()
        self.status_label.config(text="External rolls submitted successfully.", fg="green")

        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()

        # Clear inputs
        for roll_var in self.external_roll_entries.values():
            roll_var.set("")

    def assign_tiles_to_player(self, player_name, tiles):
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before assigning tiles.")
            return
        player = next((p for p in self.app.players if p.name == player_name), None)
        if not player:
            messagebox.showerror("Player Not Found", f"Player '{player_name}' not found.")
            return
        available_tiles = [pos for pos, owner in self.app.tile_owners.items() if owner is None or owner == player_name]
        if len(available_tiles) < tiles:
            messagebox.showwarning("Insufficient Tiles", f"Not enough available tiles to assign {tiles} tiles to {player_name}.")
            tiles = len(available_tiles)
        for i in range(tiles):
            x, y = available_tiles[i]
            self.app.tile_owners[(x, y)] = player_name
            self.app.map_draw.point((x, y), fill=player.color)
        # Refresh map via GameScreen
        if isinstance(self.app.current_screen, GameScreen):
            self.app.current_screen.display_map_image()

    def destroy(self):
        self.frame.destroy()
