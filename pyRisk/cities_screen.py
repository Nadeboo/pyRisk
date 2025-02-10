import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from typing import Dict, Set

@dataclass
class City:
    name: str
    owner: str
    slots: Set[str] = None

    def __post_init__(self):
        self.slots = set()

class CitiesScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize cities list if it doesn't exist
        if not hasattr(self.app, 'cities'):
            self.app.cities = []
            
        # Define the grid layout of improvements
        self.BUILDING_SLOTS = [
            ['Pasture', 'Watchtower', 'Barracks', 'Stoneworks', 'Shipyard'],
            ['Library', 'Stables', 'Academy', 'Harbor', 'Manufactory'],
            ['Armory', 'Astronomy Guild', 'Factory', 'Traders Guild', 'Townhall']
        ]
        
        self.setup_widgets()

    def setup_widgets(self):
        # Title
        title_frame = tk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=20)
        tk.Label(title_frame, text="Cities Management", font=("Arial", 24)).pack(expand=True)

        # Left Panel - City List and Creation
        left_panel = tk.Frame(self.frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)

        # City Creation Section
        creation_frame = tk.Frame(left_panel)
        creation_frame.pack(fill=tk.X, pady=10)
        
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
        self.player_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # City Name Entry
        name_frame = tk.Frame(creation_frame)
        name_frame.pack(fill=tk.X, pady=5)
        tk.Label(name_frame, text="City Name:").pack(side=tk.LEFT, padx=5)
        self.city_name_var = tk.StringVar()
        self.city_name_entry = tk.Entry(name_frame, textvariable=self.city_name_var)
        self.city_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Create Button
        tk.Button(
            creation_frame,
            text="Create City",
            command=self.create_city
        ).pack(fill=tk.X, pady=10)

        # City List
        tk.Label(left_panel, text="Cities:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10,5))
        
        # Listbox for cities
        self.city_listbox = tk.Listbox(left_panel, width=30, height=15)
        self.city_listbox.pack(fill=tk.BOTH, expand=True)
        self.city_listbox.bind('<<ListboxSelect>>', self.on_city_select)
        self.city_listbox.bind('<Button-3>', self.show_city_popup)

        # Right Panel - Building Grid
        self.right_panel = tk.Frame(self.frame)
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # City info header
        self.city_header = tk.Label(self.right_panel, text="Select a city", font=("Arial", 14, "bold"))
        self.city_header.pack(pady=(0,20))

        # Grid of building slots
        self.grid_frame = tk.Frame(self.right_panel)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the grid of buttons
        self.building_buttons = []
        for row_idx, row in enumerate(self.BUILDING_SLOTS):
            button_row = []
            for col_idx, building in enumerate(row):
                btn = tk.Button(
                    self.grid_frame,
                    text=building,
                    width=15,
                    height=2,
                    command=lambda r=row_idx, c=col_idx: self.toggle_building(r, c)
                )
                btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)
                button_row.append(btn)
            self.building_buttons.append(button_row)
        
        # Initially disable all building buttons
        self.set_buttons_state(tk.DISABLED)
        
        # Update initial state
        self.update_player_list()
        self.update_city_list()

    def set_buttons_state(self, state):
        """Enable or disable all building buttons"""
        for row in self.building_buttons:
            for btn in row:
                btn.config(state=state)

    def update_player_list(self):
        """Update the player dropdown with current players"""
        players = [p.name for p in self.app.players]
        self.player_dropdown['values'] = players
        if players:
            self.player_dropdown.set(players[0])
        else:
            self.player_dropdown.set('')

    def update_city_list(self):
        """Update the listbox with current cities"""
        self.city_listbox.delete(0, tk.END)
        for city in self.app.cities:
            self.city_listbox.insert(tk.END, f"{city.name} ({city.owner})")
        
    def create_city(self):
        """Create a new city"""
        if not self.app.players:
            messagebox.showwarning("No Players", "Please add players before creating cities.")
            return
            
        owner = self.player_var.get()
        city_name = self.city_name_var.get().strip()
        
        if not city_name:
            messagebox.showwarning("Invalid Name", "Please enter a city name.")
            return
            
        # Check for duplicate names
        if any(city.name == city_name for city in self.app.cities):
            messagebox.showwarning("Duplicate Name", "A city with this name already exists.")
            return
            
        # Create and add the new city
        city = City(name=city_name, owner=owner)
        self.app.cities.append(city)
        
        # Clear the name entry
        self.city_name_var.set("")
        
        # Update the display
        self.update_city_list()

    def on_city_select(self, event):
        """Handle city selection"""
        selection = self.city_listbox.curselection()
        if not selection:
            self.city_header.config(text="Select a city")
            self.set_buttons_state(tk.DISABLED)
            return
            
        # Get the selected city
        city_name = self.city_listbox.get(selection[0]).split(" (")[0]
        city = next((c for c in self.app.cities if c.name == city_name), None)
        if not city:
            return
            
        # Update header
        self.city_header.config(text=f"{city.name} - {city.owner}")
        
        # Enable buttons
        self.set_buttons_state(tk.NORMAL)
        
        # Update button states
        for row_idx, row in enumerate(self.BUILDING_SLOTS):
            for col_idx, building in enumerate(row):
                btn = self.building_buttons[row_idx][col_idx]
                if building in city.slots:
                    btn.config(relief=tk.SUNKEN, bg='lightgrey')
                else:
                    btn.config(relief=tk.RAISED, bg='SystemButtonFace')

    def toggle_building(self, row_idx, col_idx):
        """Toggle a building slot for the selected city"""
        selection = self.city_listbox.curselection()
        if not selection:
            return
            
        # Get the selected city
        city_name = self.city_listbox.get(selection[0]).split(" (")[0]
        city = next((c for c in self.app.cities if c.name == city_name), None)
        if not city:
            return
            
        # Toggle the building
        building = self.BUILDING_SLOTS[row_idx][col_idx]
        btn = self.building_buttons[row_idx][col_idx]
        
        if building in city.slots:
            city.slots.remove(building)
            btn.config(relief=tk.RAISED, bg='SystemButtonFace')
        else:
            city.slots.add(building)
            btn.config(relief=tk.SUNKEN, bg='lightgrey')

    def show_city_popup(self, event):
        """Show popup menu for city management"""
        # Get click coordinates relative to listbox
        index = self.city_listbox.nearest(event.y)
        if index < 0 or index >= self.city_listbox.size():
            return
            
        # Get the city name
        city_name = self.city_listbox.get(index).split(" (")[0]
        city = next((c for c in self.app.cities if c.name == city_name), None)
        if not city:
            return
        
        # Create popup menu
        popup = tk.Menu(self.city_listbox, tearoff=0)
        
        # Add delete option
        popup.add_command(
            label="Delete City",
            command=lambda: self.delete_city(city)
        )
        
        # Show the popup menu
        popup.tk_popup(event.x_root, event.y_root)

    def delete_city(self, city):
        """Delete a city"""
        if messagebox.askyesno("Confirm Delete", 
                            f"Are you sure you want to delete {city.name}?"):
            self.app.cities.remove(city)
            self.update_city_list()
            # Clear the building grid
            self.city_header.config(text="Select a city")
            self.set_buttons_state(tk.DISABLED)

    def destroy(self):
        """Clean up when closing the screen"""
        self.frame.destroy()