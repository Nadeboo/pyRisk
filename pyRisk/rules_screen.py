# rules_screen.py

import tkinter as tk
from tkinter import ttk, messagebox
from rule_manager import Rule

class RulesScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()
        self.update_rules_display()

    def setup_widgets(self):
        self.title_label = tk.Label(self.frame, text="Game Rules", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.rules_frame = tk.Frame(self.frame)
        self.rules_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.checkboxes = []

    def update_rules_display(self):
        # Clear existing checkboxes
        for checkbox in self.checkboxes:
            checkbox.destroy()
        self.checkboxes.clear()

        # Create new checkboxes for each rule
        for rule in self.app.rule_manager.rules:
            var = tk.BooleanVar(value=rule.is_active)
            checkbox = ttk.Checkbutton(
                self.rules_frame, 
                text=f"{rule.name}: {rule.description}", 
                variable=var,
                command=lambda r=rule, v=var: self.toggle_rule(r.name, v)
            )
            checkbox.pack(anchor='w', pady=5)
            self.checkboxes.append(checkbox)

    def toggle_rule(self, rule_name, var):
        self.app.rule_manager.toggle_rule(rule_name)
        print(f"Rule '{rule_name}' is now {'active' if var.get() else 'inactive'}")

    def destroy(self):
        self.frame.destroy()
