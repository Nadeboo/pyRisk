# units_screen.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pyRisk.unit import Unit, UnitType, UnitClass
from pyRisk.custom_scrollbar import CustomScrollbar


class UnitsScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Verify we're in Tregonia mode
        if self.app.roll_mode != 'tregonia':
            messagebox.showwarning("Invalid Mode", "Army management is only available in Tregonia mode")
            self.app.show_game_screen()
            return
            
        self.frame = tk.Frame(parent, bg=app.current_theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Store current theme reference
        self.current_theme = app.current_theme
        
        self.setup_widgets()

    def setup_widgets(self):
            # Main title
            title_frame = tk.Frame(self.frame, bg=self.current_theme['bg'])
            title_frame.pack(fill=tk.X, pady=20)
            tk.Label(title_frame, text="Army Management", font=("Arial", 24), 
                   bg=self.current_theme['bg'], fg=self.current_theme['fg']).pack(expand=True)

            # Army Creation Frame
            creation_frame = tk.Frame(self.frame, bg=self.current_theme['bg'])
            creation_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # Configure ttk style for the Treeview and Combobox
            self.setup_ttk_styles()
            
            # Player Selection
            player_frame = tk.Frame(creation_frame, bg=self.current_theme['bg'])
            player_frame.pack(fill=tk.X, pady=5)
            tk.Label(player_frame, text="Owner:", bg=self.current_theme['bg'], 
                   fg=self.current_theme['fg']).pack(side=tk.LEFT, padx=5)
            self.player_var = tk.StringVar()
            self.player_dropdown = ttk.Combobox(
                player_frame, 
                textvariable=self.player_var,
                state='readonly',
                style='Dark.TCombobox'
            )
            self.player_dropdown.pack(side=tk.LEFT, padx=5)
            self.update_player_list()
            
            # Create Button
            tk.Button(
                creation_frame,
                text="Create Army",
                command=self.create_army,
                bg=self.current_theme['button_bg'],
                fg=self.current_theme['button_fg'],
                activebackground=self.current_theme['highlight_bg'],
                activeforeground=self.current_theme['highlight_fg']
            ).pack(pady=10)
            
            # Split the main area into two columns
            main_frame = tk.Frame(self.frame, bg=self.current_theme['bg'])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Left side: Army List
            list_frame = tk.Frame(main_frame, bg=self.current_theme['bg'])
            list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Create and configure the Treeview
            columns = ('ID', 'Owner', 'Units', 'Move', 'Attack', 'Casualty', 'Wall', 'Wall Bonus', 'Capacity', 'Special Properties')
            self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15, style='Dark.Treeview')
            
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
                'Capacity': 80,
                'Special Properties': 150
            }
            
            for col in columns:
                self.tree.heading(col, text=col, anchor=tk.CENTER)
                self.tree.column(col, width=column_widths[col], anchor=tk.CENTER)
            
            # Add scrollbars - Use custom scrollbars
            # Get scrollbar colors from theme
            scroll_bg = self.current_theme.get('scrollbar_bg', self.current_theme['button_bg'])
            scroll_fg = self.current_theme.get('scrollbar_fg', self.current_theme['highlight_bg'])
            
            # Create vertical custom scrollbar
            y_scrollbar = CustomScrollbar(
                list_frame, 
                orientation="vertical", 
                command=self.tree.yview,
                bg=scroll_bg,
                fg=scroll_fg,
                width=12
            )
            
            # Create horizontal custom scrollbar
            x_scrollbar = CustomScrollbar(
                list_frame, 
                orientation="horizontal", 
                command=self.tree.xview,
                bg=scroll_bg,
                fg=scroll_fg,
                width=12
            )
            
            self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
            
            # Pack everything - make sure the scrollbars are properly positioned
            self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
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

    def setup_ttk_styles(self):
        """Setup enhanced styling for ttk widgets to properly apply dark theme"""
        style = ttk.Style()
        
        # Create a new theme to modify
        try:
            # Try to create our theme - this might fail if it already exists
            style.theme_create("dark_theme", parent="alt", 
                             settings={
                                 "TCombobox": {
                                     "configure": {
                                         "selectbackground": self.current_theme['highlight_bg'],
                                         "fieldbackground": self.current_theme['bg'],
                                         "background": self.current_theme['bg'],
                                         "foreground": self.current_theme['fg']
                                     }
                                 },
                                 "Treeview": {
                                     "configure": {
                                         "background": self.current_theme['bg'],
                                         "foreground": self.current_theme['fg'],
                                         "fieldbackground": self.current_theme['bg'],
                                         "borderwidth": 0,
                                         "rowheight": 40
                                     },
                                     "map": {
                                         "background": [("selected", self.current_theme['highlight_bg'])],
                                         "foreground": [("selected", self.current_theme['highlight_fg'])]
                                     }
                                 },
                                 "Treeview.Heading": {
                                     "configure": {
                                         "background": self.current_theme['button_bg'],
                                         "foreground": self.current_theme['button_fg'],
                                         "relief": "flat"
                                     },
                                     "map": {
                                         "background": [("active", self.current_theme['highlight_bg'])],
                                         "foreground": [("active", self.current_theme['highlight_fg'])]
                                     }
                                 }
                             })
        except tk.TclError:
            # Theme already exists, just use it
            pass
        
        # Use our theme
        style.theme_use("dark_theme")
        
        # Create specific widget styles
        
        # For Treeview
        style.configure("Dark.Treeview",
                      background=self.current_theme['bg'],
                      foreground=self.current_theme['fg'],
                      fieldbackground=self.current_theme['bg'],
                      borderwidth=0)
                      
        style.map("Dark.Treeview",
                background=[("selected", self.current_theme['highlight_bg'])],
                foreground=[("selected", self.current_theme['highlight_fg'])])
                
        # For Treeview headings
        style.configure("Dark.Treeview.Heading",
                      background=self.current_theme['button_bg'],
                      foreground=self.current_theme['button_fg'],
                      relief="flat")
                      
        style.map("Dark.Treeview.Heading",
                background=[("active", self.current_theme['highlight_bg'])],
                foreground=[("active", self.current_theme['highlight_fg'])])
                
        # For Combobox
        style.configure("Dark.TCombobox",
                      selectbackground=self.current_theme['highlight_bg'],
                      selectforeground=self.current_theme['highlight_fg'],
                      fieldbackground=self.current_theme['bg'],
                      background=self.current_theme['bg'],
                      foreground=self.current_theme['fg'],
                      arrowcolor=self.current_theme['button_fg'])
                      
        style.map("Dark.TCombobox",
                 fieldbackground=[("readonly", self.current_theme['bg'])],
                 background=[("readonly", self.current_theme['button_bg'])],
                 foreground=[("readonly", self.current_theme['button_fg'])])
                 
        # Fix Combobox dropdown styling - need to configure the dropdown specifically
        self.app.master.option_add('*TCombobox*Listbox.background', self.current_theme['bg'])
        self.app.master.option_add('*TCombobox*Listbox.foreground', self.current_theme['fg'])
        self.app.master.option_add('*TCombobox*Listbox.selectBackground', self.current_theme['highlight_bg'])
        self.app.master.option_add('*TCombobox*Listbox.selectForeground', self.current_theme['highlight_fg'])

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
        
        # Apply the theme to the dialog
        dialog.configure(bg=self.current_theme['bg'])
        
        # Create a frame for the checkboxes
        props_frame = tk.Frame(dialog, bg=self.current_theme['bg'])
        props_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add a label
        tk.Label(props_frame, text="Available Special Properties", 
              font=("Arial", 12, "bold"),
              bg=self.current_theme['bg'],
              fg=self.current_theme['fg']).pack(pady=(0, 10))
        
        # Add checkboxes for available properties
        checkbox_vars = {}
        available_properties = army.available_special_properties
        
        if not available_properties:
            tk.Label(props_frame, text="No special properties available",
                   bg=self.current_theme['bg'],
                   fg=self.current_theme['fg']).pack(pady=10)
        
        for prop in available_properties:
            var = tk.BooleanVar(value=prop in army.special_properties)
            checkbox_vars[prop] = var
            
            cb = tk.Checkbutton(
                props_frame,
                text=prop.title(),
                variable=var,
                bg=self.current_theme['bg'],
                fg=self.current_theme['fg'],
                activebackground=self.current_theme['bg'],
                activeforeground=self.current_theme['fg'],
                selectcolor=self.current_theme['bg']
            )
            cb.pack(anchor=tk.W, pady=2)
        
        # Add buttons
        button_frame = tk.Frame(dialog, bg=self.current_theme['bg'])
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_properties():
            # Update the army's special properties
            for prop, var in checkbox_vars.items():
                if var.get():
                    # Add property to army
                    army.special_properties.add(prop)
                    # Add property to all relevant sub-units
                    for sub_unit in army.sub_units:
                        if prop in sub_unit.unit_type.special_properties:
                            sub_unit.special_properties.add(prop)
                else:
                    # Remove property from army
                    army.special_properties.discard(prop)
                    # Remove property from all sub-units
                    for sub_unit in army.sub_units:
                        sub_unit.special_properties.discard(prop)
            
            # Update the display
            self.update_army_list()
            dialog.destroy()
        
        tk.Button(button_frame, text="Save", 
               command=save_properties,
               bg=self.current_theme['button_bg'],
               fg=self.current_theme['button_fg'],
               activebackground=self.current_theme['highlight_bg'],
               activeforeground=self.current_theme['highlight_fg']).pack(side=tk.RIGHT, padx=5)
               
        tk.Button(button_frame, text="Cancel", 
               command=dialog.destroy,
               bg=self.current_theme['button_bg'],
               fg=self.current_theme['button_fg'],
               activebackground=self.current_theme['highlight_bg'],
               activeforeground=self.current_theme['highlight_fg']).pack(side=tk.RIGHT, padx=5)

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
                # Try to merge using the static method from Unit class
                if Unit.merge_armies(source_army, target_army):
                    # Successfully merged
                    self.update_army_list()
                    if not isinstance(self.app.current_screen, type(self)):
                        self.app.current_screen.display_map_image()
                else:
                    # Check why the merge might have failed
                    if not source_army.is_army or not target_army.is_army:
                        messagebox.showwarning("Merge Failed", "Both units must be armies to merge.")
                    elif source_army.owner != target_army.owner:
                        messagebox.showwarning("Merge Failed", "Can only merge armies from the same player.")
                    elif not target_army.can_merge_army(source_army):
                        messagebox.showwarning(
                            "Army Size Limit", 
                            f"Cannot merge. Target army ({target_army.current_army_size}/{target_army.max_army_size}) "
                            f"doesn't have capacity for source army ({source_army.current_army_size} slots)."
                        )
        
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
        
        # Ask for custom max army size (default is the DEFAULT_MAX_ARMY_SIZE)
        from pyRisk.unit import DEFAULT_MAX_ARMY_SIZE
        max_size = simpledialog.askinteger(
            "Army Size Limit", 
            f"Enter the maximum size for this army (default is {DEFAULT_MAX_ARMY_SIZE}):",
            initialvalue=DEFAULT_MAX_ARMY_SIZE,
            minvalue=1, 
            maxvalue=100
        )
        
        # If user cancels, use the default size
        if max_size is None:
            max_size = DEFAULT_MAX_ARMY_SIZE
        
        # Create army as a special unit that will contain sub-units
        army = Unit(
            owner=owner,
            unit_type=UnitType.INFANTRY,  # Default type, doesn't matter for armies
            unit_id=self.app.next_unit_id,
            position=None,  # No position - must be placed on map manually
            max_army_size=max_size  # Set the custom max size
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
        popup = tk.Menu(self.tree, tearoff=0,
                     bg=self.current_theme['menu_bg'],
                     fg=self.current_theme['menu_fg'],
                     activebackground=self.current_theme['highlight_bg'],
                     activeforeground=self.current_theme['highlight_fg'])
        
        # Create submenus for different unit classes
        land_menu = tk.Menu(popup, tearoff=0,
                         bg=self.current_theme['menu_bg'],
                         fg=self.current_theme['menu_fg'],
                         activebackground=self.current_theme['highlight_bg'],
                         activeforeground=self.current_theme['highlight_fg'])
                         
        naval_menu = tk.Menu(popup, tearoff=0,
                          bg=self.current_theme['menu_bg'],
                          fg=self.current_theme['menu_fg'],
                          activebackground=self.current_theme['highlight_bg'],
                          activeforeground=self.current_theme['highlight_fg'])
        
        # Add land units to land submenu
        for unit_type in UnitType:
            if hasattr(unit_type, 'unit_class') and unit_type.unit_class == UnitClass.LAND:
                land_menu.add_command(
                    label=f"Add {unit_type.value}",
                    command=lambda t=unit_type: self.add_unit_to_army(army, t)
                )
        
        # Add naval units to naval submenu
        for unit_type in UnitType:
            if hasattr(unit_type, 'unit_class') and unit_type.unit_class == UnitClass.NAVAL:
                naval_menu.add_command(
                    label=f"Add {unit_type.value} (Capacity: {unit_type.carrying_capacity})",
                    command=lambda t=unit_type: self.add_unit_to_army(army, t)
                )
        
        # Add submenus to main popup
        popup.add_cascade(label="Add Land Unit", menu=land_menu)
        popup.add_cascade(label="Add Naval Unit", menu=naval_menu)
        
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
        # For Gravelord, prompt for dice count
        custom_params = {}
        if unit_type == UnitType.GRAVELORD:
            dice_count = simpledialog.askinteger(
                "Gravelord Dice Count", 
                "Enter the dice count for the Gravelord (1-20):",
                minvalue=1, maxvalue=20
            )
            if dice_count is None:  # User cancelled
                return
                
            custom_params = {"dice_count": dice_count}
            
        # Check if unit can be added to army based on size limits
        if not army.can_add_unit(unit_type, custom_params):
            slots_needed = unit_type.get_slots_used(custom_params)
            messagebox.showwarning(
                "Army Size Limit", 
                f"Cannot add {unit_type.value} (needs {slots_needed} slots). "
                f"Army is at {army.current_army_size}/{army.max_army_size} slots."
            )
            return
            
        unit = Unit(
            owner=army.owner,
            unit_type=unit_type,
            unit_id=self.app.next_unit_id,
            position=None,
            custom_params=custom_params
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
                            
                    active_props = [f"{prop}: units {','.join(map(str, units))}" 
                                 for prop, units in unit_props.items()]
                else:
                    active_props = list(unit.special_properties)
                    
                # Show size for armies
                size_info = ""
                if unit.is_army:
                    size_info = f" ({unit.current_army_size}/{unit.max_army_size})"
                
                # Get carrying capacity for naval units
                capacity_info = "-"
                if hasattr(unit, 'is_naval_army') and unit.is_naval_army:
                    capacity_info = str(unit.total_carrying_capacity)
                elif hasattr(unit.unit_type, 'unit_class') and unit.unit_type.unit_class == UnitClass.NAVAL:
                    capacity_info = str(unit.unit_type.carrying_capacity)
                
                # Add row with all unit data
                self.tree.insert(
                    '', 'end', text=str(unit.unit_id),
                    values=(
                        unit.unit_id,
                        unit.owner,
                        unit.shorthand + size_info,  # Add size info to display
                        str(unit.movement_speed),
                        unit.attack_dice,
                        unit.casualty_dice,
                        unit.wall_dice,
                        f"+{unit.wall_bonus}",
                        capacity_info,  # Add carrying capacity
                        ", ".join(active_props) if active_props else "None"
                    )
                )

    def destroy(self):
        """Clean up the screen when switching away"""
        if hasattr(self, 'frame'):
            self.frame.destroy()

    def apply_theme(self, theme):
        """Apply the current theme to all widgets"""
        self.current_theme = theme
        
        # Apply to main frame
        self.frame.configure(bg=theme['bg'])
        
        # Apply to all child widgets recursively
        self.apply_theme_to_widget(self.frame, theme)
        
        # Re-setup the ttk styles with new theme colors
        self.setup_ttk_styles()
        
        # Update the army list to reflect the new theme
        self.update_army_list()
        
    def apply_theme_to_widget(self, widget, theme):
        """Apply theme to a single widget and all its children"""
        try:
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                widget.configure(bg=theme['bg'])
            elif isinstance(widget, tk.Button):
                widget.configure(
                    bg=theme['button_bg'],
                    fg=theme['button_fg'],
                    activebackground=theme['highlight_bg'],
                    activeforeground=theme['highlight_fg']
                )
            elif isinstance(widget, (tk.Label, tk.Checkbutton, tk.Radiobutton)):
                widget.configure(
                    bg=theme['bg'],
                    fg=theme['fg']
                )
                # Configure additional specific attributes for checkbuttons/radiobuttons
                if isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
                    widget.configure(
                        activebackground=theme['bg'],
                        activeforeground=theme['fg'],
                        selectcolor=theme['bg']
                    )
            elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                widget.configure(
                    bg=theme['bg'],
                    fg=theme['fg'],
                    insertbackground=theme['fg']  # cursor color
                )
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=theme['canvas_bg'])
            elif isinstance(widget, tk.Menu):
                widget.configure(
                    bg=theme['menu_bg'],
                    fg=theme['menu_fg'],
                    activebackground=theme['highlight_bg'],
                    activeforeground=theme['highlight_fg']
                )
            # Handle our CustomScrollbar class
            elif hasattr(widget, 'canvas') and hasattr(widget, 'set') and hasattr(widget, 'config'):
                # This might be a CustomScrollbar instance
                try:
                    widget.config(
                        bg=theme['scrollbar_bg'] if 'scrollbar_bg' in theme else theme['button_bg'],
                        fg=theme['scrollbar_fg'] if 'scrollbar_fg' in theme else theme['highlight_bg']
                    )
                except (tk.TclError, AttributeError):
                    pass
        except tk.TclError:
            # Skip widgets that can't be configured
            pass
            
        # Process children recursively
        for child in widget.winfo_children():
            self.apply_theme_to_widget(child, theme)