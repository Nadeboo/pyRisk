# units_screen.py

import tkinter as tk
from tkinter import ttk, messagebox
from pyRisk.unit import Unit, UnitType


class UnitsScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Verify we're in Tregonia mode
        if self.app.roll_mode != 'tregonia':
            messagebox.showwarning("Invalid Mode", "Army management is only available in Tregonia mode")
            self.app.show_game_screen()
            return
            
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
            # Main title
            title_frame = tk.Frame(self.frame)
            title_frame.pack(fill=tk.X, pady=20)
            tk.Label(title_frame, text="Army Management", font=("Arial", 24)).pack(expand=True)

            # Army Creation Frame
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
            
            # Create Button
            tk.Button(
                creation_frame,
                text="Create Army",
                command=self.create_army
            ).pack(pady=10)
            
            # Split the main area into two columns
            main_frame = tk.Frame(self.frame)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Left side: Army List
            list_frame = tk.Frame(main_frame)
            list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Create and configure the Treeview
            columns = ('ID', 'Owner', 'Units', 'Move', 'Attack', 'Casualty', 'Wall', 'Wall Bonus', 'Special Properties')
            self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
            
            # Configure row height to accommodate multiple lines
            style = ttk.Style()
            style.configure('Treeview', rowheight=40)
            
            # Configure columns
            column_widths = {
                'ID': 50,
                'Owner': 150,
                'Units': 80,
                'Move': 50,
                'Attack': 100,
                'Casualty': 100,
                'Wall': 100,
                'Wall Bonus': 100,
                'Special Properties': 150
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
            
            # Bind tree selection to update special properties
            self.tree.bind('<<TreeviewSelect>>', self.on_army_select)
            
            # Bind mouse events for drag and drop and special properties editing
            self.tree.bind('<Button-3>', self.show_unit_popup)
            self.tree.bind('<ButtonPress-1>', self.on_drag_start)
            self.tree.bind('<B1-Motion>', self.on_drag_motion)
            self.tree.bind('<ButtonRelease-1>', self.on_drag_release)
            self.tree.bind('<Double-1>', self.on_double_click)
            
            self.dragged_item = None
            self.update_army_list()

    def on_double_click(self, event):
        """Handle double-click on a cell, specifically for special properties"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        column_index = int(column[1:]) - 1  # Convert #9 to 8 (0-indexed)
        
        # Check if the Special Properties column was clicked (column index 8)
        if column_index == 8:
            item = self.tree.identify_row(event.y)
            if item:
                army_id = int(self.tree.item(item)['values'][0])
                army = next((u for u in self.app.units if u.unit_id == army_id), None)
                if army:
                    self.show_properties_dialog(army)

    def show_properties_dialog(self, army):
        """Show a dialog to edit special properties for the army"""
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Special Properties for Army #{army.unit_id}")
        dialog.geometry("300x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Create a frame for the checkboxes
        props_frame = tk.Frame(dialog)
        props_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add a label
        tk.Label(props_frame, text="Available Special Properties", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Add checkboxes for available properties
        checkbox_vars = {}
        available_properties = army.available_special_properties
        
        if not available_properties:
            tk.Label(props_frame, text="No special properties available").pack(pady=10)
        
        for prop in available_properties:
            var = tk.BooleanVar(value=prop in army.special_properties)
            checkbox_vars[prop] = var
            
            cb = tk.Checkbutton(
                props_frame,
                text=prop.title(),
                variable=var
            )
            cb.pack(anchor=tk.W, pady=2)
        
        # Add buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_properties():
            # Update the army's special properties
            for prop, var in checkbox_vars.items():
                if var.get():
                    army.special_properties.add(prop)
                else:
                    army.special_properties.discard(prop)
            
            # Update the display
            self.update_army_list()
            dialog.destroy()
        
        tk.Button(button_frame, text="Save", command=save_properties).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def on_army_select(self, event):
        """Update special properties when an army is selected"""
        # This method is kept for backward compatibility but no longer updates checkboxes
        pass

    def update_special_properties(self, army):
        """This method is kept for backward compatibility but is no longer used"""
        pass

    def toggle_property(self, army, property_name):
        """Toggle a special property for an army"""
        if property_name in army.special_properties:
            army.special_properties.discard(property_name)
        else:
            army.special_properties.add(property_name)
        
        # Update the display to show new dice values
        self.update_army_list()
        
    def on_drag_start(self, event):
        """Start dragging an army"""
        item = self.tree.identify_row(event.y)
        if item:
            self.dragged_item = item
            self.tree.selection_set(item)
    
    def on_drag_motion(self, event):
        """Update selection during drag"""
        if self.dragged_item:
            pass  # Could add visual feedback here
    
    def on_drag_release(self, event):
        """Handle dropping an army onto another"""
        if not self.dragged_item:
            return
            
        target_item = self.tree.identify_row(event.y)
        if target_item and target_item != self.dragged_item:
            # Get source and target armies
            source_id = int(self.tree.item(self.dragged_item)['values'][0])
            target_id = int(self.tree.item(target_item)['values'][0])
            
            source_army = next((u for u in self.app.units if u.unit_id == source_id), None)
            target_army = next((u for u in self.app.units if u.unit_id == target_id), None)
            
            if source_army and target_army:
                # Try to merge
                if self.app.unit.merge_armies(source_army, target_army):
                    self.update_army_list()
                    if not isinstance(self.app.current_screen, type(self)):
                        self.app.current_screen.display_map_image()
        
        self.dragged_item = None

    def update_player_list(self):
        """Update the player dropdown with current players"""
        players = [p.name for p in self.app.players]
        self.player_dropdown['values'] = players
        if players:
            self.player_dropdown.set(players[0])
        else:
            self.player_dropdown.set('')

    def create_army(self):
        """Create a new empty army"""
        if not self.app.players:
            messagebox.showwarning("No Players", "Please add players before creating armies.")
            return
            
        owner = self.player_var.get()
        
        # Create army as a special unit that will contain sub-units
        army = Unit(
            owner=owner,
            unit_type=UnitType.INFANTRY,  # Default type, doesn't matter for armies
            unit_id=self.app.next_unit_id,
            position=None  # No position - must be placed on map manually
        )
        
        # Add to app's units list
        self.app.units.append(army)
        self.app.next_unit_id += 1
        
        # Update the display
        self.update_army_list()

    def show_unit_popup(self, event):
        """Show popup menu for adding units to an army"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        # Get the army that was right-clicked
        army_id = int(self.tree.item(item)['values'][0])
        army = next((u for u in self.app.units if u.unit_id == army_id), None)
        if not army:
            return
        
        # Create popup menu
        popup = tk.Menu(self.tree, tearoff=0)
        
        # Add available unit types
        for unit_type in UnitType:
            popup.add_command(
                label=f"Add {unit_type.value}",
                command=lambda t=unit_type: self.add_unit_to_army(army, t)
            )
            
        # Add separator
        popup.add_separator()
        
        # Add option to edit special properties
        popup.add_command(
            label="Edit Special Properties",
            command=lambda: self.show_properties_dialog(army)
        )
        
        # Add option to delete army
        popup.add_command(
            label="Delete Army",
            command=lambda: self.delete_army(army)
        )
        
        # Display popup menu
        popup.tk_popup(event.x_root, event.y_root)

    def remove_unit_from_army(self, army, unit):
        """Remove a unit from an army"""
        if unit in army.sub_units:
            army.sub_units.remove(unit)
            
            # If army is now empty, delete it
            if not army.sub_units:
                self.delete_army(army)
            else:
                self.update_army_list()

    def delete_army(self, army):
        """Delete an army and all its units"""
        # Confirm deletion
        if army.is_army:
            if not messagebox.askyesno(
                "Confirm Deletion",
                f"Delete army #{army.unit_id} with {len(army.sub_units)} units?"
            ):
                return
        else:
            if not messagebox.askyesno(
                "Confirm Deletion",
                f"Delete empty army #{army.unit_id}?"
            ):
                return
                
        # Remove from app's units list
        self.app.units.remove(army)
        
        # Update the display
        self.update_army_list()
        
        # Update the map if we're in game screen
        if not isinstance(self.app.current_screen, type(self)):
            self.app.current_screen.display_map_image()

    def add_unit_to_army(self, army, unit_type):
        """Add a unit to an army"""
        unit = Unit(
            owner=army.owner,
            unit_type=unit_type,
            unit_id=self.app.next_unit_id,
            position=None
        )
        
        army.sub_units.append(unit)
        self.app.next_unit_id += 1
        
        # Update the display
        self.update_army_list()

    def update_army_list(self):
        """Update the treeview with current armies"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add all units that don't belong to another unit (i.e., top-level armies)
        all_sub_units = set()
        for unit in self.app.units:
            for sub_unit in unit.sub_units:
                all_sub_units.add(sub_unit.unit_id)
                
        # Now only display units that aren't sub-units
        for unit in self.app.units:
            if unit.unit_id not in all_sub_units:
                # Format special properties
                active_props = []
                if unit.is_army:
                    # For armies, show which units have which properties
                    unit_props = {}
                    for sub_unit in unit.sub_units:
                        for prop in sub_unit.special_properties:
                            if prop not in unit_props:
                                unit_props[prop] = []
                            unit_props[prop].append(sub_unit.unit_id)
                    
                    for prop, unit_ids in unit_props.items():
                        active_props.append(f"{prop.title()}")
                else:
                    # For individual units, just show the properties
                    active_props = [prop.title() for prop in unit.special_properties]
                
                special_props_text = ", ".join(active_props) if active_props else "None"
                
                self.tree.insert('', 'end', values=(
                    unit.unit_id,
                    unit.owner,
                    unit.shorthand if unit.is_army else "Empty",
                    unit.movement_speed,
                    unit.attack_dice,
                    unit.casualty_dice,
                    unit.wall_dice,
                    f"+{unit.wall_bonus}" if unit.wall_bonus > 0 else unit.wall_bonus,
                    special_props_text
                ))

    def destroy(self):
        """Clean up the screen when switching away"""
        if hasattr(self, 'frame'):
            self.frame.destroy()