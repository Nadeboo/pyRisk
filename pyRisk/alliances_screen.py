# alliances_screen.py

import tkinter as tk
from tkinter import messagebox


class AlliancesScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        tk.Label(self.frame, text="Manage Alliances and NAPs").pack(pady=5)
        player_names = [p.name for p in self.app.players]
        self.player1_var = tk.StringVar()
        self.player2_var = tk.StringVar()
        for text, var in [("Select Player 1:", self.player1_var), ("Select Player 2:", self.player2_var)]:
            tk.Label(self.frame, text=text).pack()
            if player_names:
                var.set(player_names[0])
                option_menu = tk.OptionMenu(self.frame, var, *player_names)
            else:
                var.set("No Players")
                option_menu = tk.OptionMenu(self.frame, var, "No Players")
            option_menu.pack()
        for text, cmd in [("Add Alliance", self.add_alliance),
                          ("Add NAP", self.add_nap)]:
            tk.Button(self.frame, text=text, command=cmd).pack(pady=5)
        if not player_names:
            for widget in self.frame.pack_slaves():
                if isinstance(widget, tk.Button):
                    widget.config(state=tk.DISABLED)
        # Display current alliances
        tk.Label(self.frame, text="Current Alliances:").pack(pady=5)
        self.alliances_text = tk.Text(self.frame, height=10)
        self.alliances_text.pack(fill=tk.BOTH, expand=True)
        self.update_alliances_text()
        # Display current NAPs
        tk.Label(self.frame, text="Current Non-Aggression Pacts (NAPs):").pack(pady=5)
        self.naps_text = tk.Text(self.frame, height=10)
        self.naps_text.pack(fill=tk.BOTH, expand=True)
        self.update_naps_text()

    def update_alliances_text(self):
        text_widget = self.alliances_text
        text_widget.delete(1.0, tk.END)
        alliances = []
        for player in self.app.players:
            for ally in player.allies:
                if player.name < ally.name:  # Avoid duplicates
                    alliances.append(f"{player.name} ↔ {ally.name}")
        if alliances:
            text_widget.insert(tk.END, '\n'.join(alliances))
        else:
            text_widget.insert(tk.END, "No alliances.")

    def update_naps_text(self):
        text_widget = self.naps_text
        text_widget.delete(1.0, tk.END)
        naps = []
        for player in self.app.players:
            for nap in player.naps:
                if player.name < nap.name:  # Avoid duplicates
                    naps.append(f"{player.name} ↔ {nap.name}")
        if naps:
            text_widget.insert(tk.END, '\n'.join(naps))
        else:
            text_widget.insert(tk.END, "No Non-Aggression Pacts.")

    def add_alliance(self):
        player1_name = self.player1_var.get()
        player2_name = self.player2_var.get()
        p1 = next((p for p in self.app.players if p.name == player1_name), None)
        p2 = next((p for p in self.app.players if p.name == player2_name), None)
        if p1 and p2 and p1 != p2:
            if p2 not in p1.allies:
                p1.add_ally(p2)
                p2.add_ally(p1)
                messagebox.showinfo("Alliance Added", f"{p1.name} and {p2.name} are now allies.")
                self.update_alliances_text()
            else:
                messagebox.showinfo("Already Allies", f"{p1.name} and {p2.name} are already allies.")
        else:
            messagebox.showwarning("Invalid Selection", "Please select two different players.")

    def add_nap(self):
        player1_name = self.player1_var.get()
        player2_name = self.player2_var.get()
        p1 = next((p for p in self.app.players if p.name == player1_name), None)
        p2 = next((p for p in self.app.players if p.name == player2_name), None)
        if p1 and p2 and p1 != p2:
            if p2 not in p1.naps:
                p1.add_nap(p2)
                p2.add_nap(p1)
                messagebox.showinfo("NAP Added", f"{p1.name} and {p2.name} have a Non-Aggression Pact.")
                self.update_naps_text()
            else:
                messagebox.showinfo("NAP Exists", f"{p1.name} and {p2.name} already have a NAP.")
        else:
            messagebox.showwarning("Invalid Selection", "Please select two different players.")

    def destroy(self):
        self.frame.destroy()
