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
            
            # Right side: Special Properties
            properties_frame = tk.Frame(main_frame)
            properties_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
            tk.Label(properties_frame, text="Special Properties", font=("Arial", 12, "bold")).pack(pady=(0, 10))
            
            # Special properties checkboxes will be created dynamically
            self.properties_vars = {}
            self.properties_frame = properties_frame
            
            # Create and configure the Treeview
            columns = ('ID', 'Owner', 'Units', 'Move', 'Attack', 'Casualty', 'Wall', 'Wall Bonus')
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
            
            # Bind tree selection to update special properties
            self.tree.bind('<<TreeviewSelect>>', self.on_army_select)
            
            # Bind mouse events for drag and drop
            self.tree.bind('<Button-3>', self.show_unit_popup)
            self.tree.bind('<ButtonPress-1>', self.on_drag_start)
            self.tree.bind('<B1-Motion>', self.on_drag_motion)
            self.tree.bind('<ButtonRelease-1>', self.on_drag_release)
            
            self.dragged_item = None
            self.update_army_list()

    def on_army_select(self, event):
        """Update special properties when an army is selected"""
        selection = self.tree.selection()
        if not selection:
            # Clear and disable all properties
            for var in self.properties_vars.values():
                var.set(False)
            return
            
        # Get the selected army
        army_id = int(self.tree.item(selection[0])['values'][0])
        army = next((u for u in self.app.units if u.unit_id == army_id), None)
        
        if not army:
            return
            
        # Update available properties
        self.update_special_properties(army)

    def update_special_properties(self, army):
        """Update the special properties checkboxes for the selected army"""
        # Clear existing checkboxes
        for widget in self.properties_frame.winfo_children():
            if isinstance(widget, tk.Checkbutton):
                widget.destroy()
        self.properties_vars.clear()
        
        # Add checkboxes for available properties
        available_properties = army.available_special_properties
        for prop in available_properties:
            var = tk.BooleanVar(value=prop in army.special_properties)
            self.properties_vars[prop] = var
            
            cb = tk.Checkbutton(
                self.properties_frame,
                text=prop.title(),
                variable=var,
                command=lambda a=army, p=prop: self.toggle_property(a, p)
            )
            cb.pack(anchor=tk.W, pady=2)

    def toggle_property(self, army, property_name):
        """Toggle a special property for an army"""
        if self.properties_vars[property_name].get():
            army.special_properties.add(property_name)
        else:
            army.special_properties.discard(property_name)
        
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
            unit_id=self.app.next_unit_id
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
            
        # Add separator and unit management submenu
        popup.add_separator()
        
        # Create submenu for managing existing units
        units_menu = tk.Menu(popup, tearoff=0)
        if army.sub_units:
            for unit in army.sub_units:
                units_menu.add_command(
                    label=f"Remove {unit.unit_type.value} #{unit.unit_id}",
                    command=lambda u=unit: self.remove_unit_from_army(army, u)
                )
        else:
            units_menu.add_command(label="No units in army", state=tk.DISABLED)
        
        popup.add_cascade(label="Remove Unit", menu=units_menu)
        
        # Add delete army option
        popup.add_separator()
        popup.add_command(
            label="Delete Entire Army",
            command=lambda: self.delete_army(army)
        )
        
        # Show the popup menu
        popup.tk_popup(event.x_root, event.y_root)

    def remove_unit_from_army(self, army, unit):
        """Remove a single unit from an army"""
        if unit in army.sub_units:
            army.sub_units.remove(unit)
            self.app.units.remove(unit)
            
            # Update displays
            self.update_army_list()
            if not isinstance(self.app.current_screen, type(self)):
                # If we're in the game screen, refresh the map
                self.app.current_screen.display_map_image()

    def delete_army(self, army):
        """Delete an army and all its units"""
        if messagebox.askyesno("Confirm Delete", 
                            f"Are you sure you want to delete this army and all its units?"):
            # First remove any sub-units from app.units
            if army.sub_units:
                # Create a copy of sub_units to avoid modification during iteration
                for sub_unit in army.sub_units[:]:
                    # Check if the sub_unit is still in app.units before trying to remove it
                    if sub_unit in self.app.units:
                        self.app.units.remove(sub_unit)
            
            # Clear the army's sub_units list
            army.sub_units.clear()
            
            # Remove the army itself if it's still in app.units
            if army in self.app.units:
                self.app.units.remove(army)
            
            # Update displays
            self.update_army_list()
            if not isinstance(self.app.current_screen, type(self)):
                # If we're in the game screen, refresh the map
                self.app.current_screen.display_map_image()

    def add_unit_to_army(self, army, unit_type):
        """Add a new unit to the specified army"""
        unit = Unit(
            owner=army.owner,
            unit_type=unit_type,
            unit_id=self.app.next_unit_id,
            position=army.position  # New unit inherits army's position
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
                self.tree.insert('', 'end', values=(
                    unit.unit_id,
                    unit.owner,
                    unit.shorthand if unit.is_army else "Empty",
                    unit.movement_speed,
                    unit.attack_dice,
                    unit.casualty_dice,
                    unit.wall_dice,
                    f"+{unit.wall_bonus}" if unit.wall_bonus > 0 else unit.wall_bonus
                ))

    def destroy(self):
        """Clean up the screen when switching away"""
        if hasattr(self, 'frame'):
            self.frame.destroy()