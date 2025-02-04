# units_screen.py

import tkinter as tk
from tkinter import ttk, messagebox
from unit import Unit, UnitType


class UnitsScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Verify we're in Tregonia mode
        if self.app.roll_mode != 'tregonia':
            messagebox.showwarning("Invalid Mode", "Units screen is only available in Tregonia mode")
            self.app.show_game_screen()
            return
            
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        # Main title
        title_frame = tk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=20)
        tk.Label(
            title_frame, 
            text="Units Management", 
            font=("Arial", 24)
        ).pack(expand=True)

        # Unit Creation Frame
        creation_frame = tk.Frame(self.frame)
        creation_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Player Selection
        player_frame = tk.Frame(creation_frame)
        player_frame.pack(fill=tk.X, pady=5)
        tk.Label(player_frame, text="Owner:").pack(side=tk.LEFT, padx=5)
        self.player_var = tk.StringVar()
        self.player_dropdown = ttk.Combobox(
            player_frame, 
            textvariable=self.player_var,
            state='readonly'
        )
        self.player_dropdown.pack(side=tk.LEFT, padx=5)
        self.update_player_list()
        
        # Unit Type Selection
        type_frame = tk.Frame(creation_frame)
        type_frame.pack(fill=tk.X, pady=5)
        tk.Label(type_frame, text="Unit Type:").pack(side=tk.LEFT, padx=5)
        self.type_var = tk.StringVar(value=UnitType.INFANTRY.value)
        self.type_dropdown = ttk.Combobox(
            type_frame,
            textvariable=self.type_var,
            values=[ut.value for ut in UnitType],
            state='readonly'
        )
        self.type_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Create Button
        tk.Button(
            creation_frame,
            text="Create Unit",
            command=self.create_unit
        ).pack(pady=10)
        
        # Unit List
        list_frame = tk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create and configure the Treeview
        columns = ('ID', 'Owner', 'Type', 'Attack', 'Casualty', 'Wall', 'Wall Bonus')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15  # Show approximately 15 rows at once
        )
        
        # Configure columns
        column_widths = {
            'ID': 50,
            'Owner': 150,
            'Type': 100,
            'Attack': 100,
            'Casualty': 100,
            'Wall': 100,
            'Wall Bonus': 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=column_widths[col], anchor=tk.CENTER)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack everything
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.update_unit_list()

    def update_player_list(self):
        """Update the player dropdown with current players"""
        players = [p.name for p in self.app.players]
        self.player_dropdown['values'] = players
        if players:
            self.player_dropdown.set(players[0])
        else:
            self.player_dropdown.set('')

    def create_unit(self):
        """Create a new unit with the selected properties"""
        if not self.app.players:
            messagebox.showwarning("No Players", "Please add players before creating units.")
            return
            
        owner = self.player_var.get()
        unit_type = UnitType(self.type_var.get())
        
        # Get next unit ID
        next_id = self.app.next_unit_id
        
        # Create the unit
        unit = Unit(owner=owner, unit_type=unit_type, unit_id=next_id)
        
        # Add to the app's units list
        if not hasattr(self.app, 'units'):
            self.app.units = []
        self.app.units.append(unit)
        
        # Increment the next unit ID
        self.app.next_unit_id += 1
        
        # Update the display
        self.update_unit_list()

    def update_unit_list(self):
        """Update the treeview with current units"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add units if they exist
        if hasattr(self.app, 'units'):
            for unit in self.app.units:
                self.tree.insert('', 'end', values=(
                    unit.unit_id,
                    unit.owner,
                    unit.unit_type.value,
                    unit.attack_dice,
                    unit.casualty_dice,
                    unit.wall_dice,
                    f"+{unit.wall_bonus}" if unit.wall_bonus > 0 else unit.wall_bonus
                ))

    def destroy(self):
        """Clean up the screen when switching away"""
        if hasattr(self, 'frame'):
            self.frame.destroy()