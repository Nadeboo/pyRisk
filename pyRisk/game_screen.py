# game_screen.py


import tkinter as tk
from tkinter import ttk, messagebox  # Add ttk here
from PIL import ImageTk, ImageDraw, Image, ImageFont
from utils import flood_fill
from players_screen import PlayersScreen
from utils import check_territory_in_radius
class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize state variables first
        self.selected_unit = None
        self.unit_mode = False
        self.zoom_level = 1.0
        self.resource_paint_mode = None
        self.RESOURCE_COLORS = {
            'unactivated': (0, 255, 0),
            'gold': (255, 255, 0),
            'mana': (0, 255, 255)
        }
        self.player_buttons = []  # Initialize this before setup_sidebar uses it

        # Create main layout container
        self.main_container = tk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create all container frames first
        self.sidebar = tk.Frame(self.main_container, width=150, bg='lightgrey')
        self.map_container = tk.Frame(self.main_container)
        self.mirror_container = tk.Frame(self.main_container, width=300)

        # Then pack them in order
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self.map_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.mirror_container.pack(side=tk.RIGHT, fill=tk.Y)
        self.mirror_container.pack_propagate(False)

        # Now setup the components
        self.setup_canvas()
        self.setup_sidebar()
        self.setup_mirror_panels()

        # Final initialization steps
        if self.app.map_image:
            self.display_map_image()
        self.bind_events()
        self.resource_paint_mode = None
        self.RESOURCE_COLORS = {
            'unactivated': (0, 255, 0),
            'gold': (255, 255, 0),
            'mana': (0, 255, 255)
        }

    def setup_mirror_panels(self):
        """Setup the mirrored players, alliances, and armies panels"""
        # Players overview
        tk.Label(self.mirror_container, text="Players", font=("Arial", 8, "bold")).pack(pady=(2,0))
        self.players_mirror = tk.Frame(self.mirror_container)
        self.players_mirror.pack(fill=tk.X)
        
        # Separator
        ttk.Separator(self.mirror_container, orient='horizontal').pack(fill='x', pady=2)
        
        # Research overview
        tk.Label(self.mirror_container, text="Research", font=("Arial", 8, "bold")).pack(pady=(2,0))
        self.research_mirror = tk.Frame(self.mirror_container)
        self.research_mirror.pack(fill=tk.X)
        
        # Separator
        ttk.Separator(self.mirror_container, orient='horizontal').pack(fill='x', pady=2)
        
        # Alliances overview
        tk.Label(self.mirror_container, text="Alliances", font=("Arial", 8, "bold")).pack(pady=(2,0))
        self.alliances_mirror = tk.Frame(self.mirror_container)
        self.alliances_mirror.pack(fill=tk.X)
        
        # Only show armies in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            ttk.Separator(self.mirror_container, orient='horizontal').pack(fill='x', pady=2)
            tk.Label(self.mirror_container, text="Armies", font=("Arial", 8, "bold")).pack(pady=(2,0))
            self.armies_mirror = tk.Frame(self.mirror_container)
            self.armies_mirror.pack(fill=tk.X)
        
        self.update_mirror_panels()

    def update_mirror_panels(self):
        """Update the contents of mirror panels"""
        # Clear existing content
        for widget in self.players_mirror.winfo_children():
            widget.destroy()
        for widget in self.research_mirror.winfo_children():
            widget.destroy()
        for widget in self.alliances_mirror.winfo_children():
            widget.destroy()
        if hasattr(self, 'armies_mirror'):
            for widget in self.armies_mirror.winfo_children():
                widget.destroy()

        # Update players mirror with minimal layout
        for player in self.app.players:
            player_frame = tk.Frame(self.players_mirror)
            player_frame.pack(fill=tk.X, pady=1)
            
            # Color indicator and name
            color_box = tk.Frame(player_frame, bg='#{:02x}{:02x}{:02x}'.format(*player.color), 
                            width=8, height=8)
            color_box.pack(side=tk.LEFT, padx=1)
            color_box.pack_propagate(False)
            
            tk.Label(player_frame, text=player.name, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
            
            # Create resources frame
            resources_frame = tk.Frame(player_frame)
            resources_frame.pack(side=tk.RIGHT, padx=1)

            # Compact resource displays
            resources = [
                (f"G:{player.gold}+{player.gold_per_turn}", "Gold"),
                (f"R:{player.research}+{player.research_per_turn}", "Research"),
                (f"M:{player.mana}+{player.mana_per_turn}", "Mana"),
                (f"I:{player.influence}+{player.influence_per_turn}", "Influence")
            ]

            for resource_text, tooltip in resources:
                resource_label = tk.Label(resources_frame, text=resource_text, font=("Arial", 7))
                resource_label.pack(side=tk.RIGHT, padx=2)
                self.create_tooltip(resource_label, tooltip)

        # Update research mirror with path separation
        for player in self.app.players:
            research_frame = tk.Frame(self.research_mirror, bg='white')
            research_frame.pack(fill=tk.X, pady=1)
            
            # Player name with color indicator
            name_frame = tk.Frame(research_frame, bg='white')
            name_frame.pack(anchor=tk.W)
            
            color_box = tk.Frame(
                name_frame,
                bg='#{:02x}{:02x}{:02x}'.format(*player.color),
                width=6,
                height=6
            )
            color_box.pack(side=tk.LEFT, padx=1)
            color_box.pack_propagate(False)
            
            tk.Label(
                name_frame,
                text=player.name,
                font=("Arial", 7),
                bg='white'
            ).pack(side=tk.LEFT, padx=1)
            
            # Research list - now separated by path
            completed = player.get_completed_research()
            
            # Steel Path Research
            steel_research = sorted(
                [r for r in completed if r.path == 'steel'],
                key=lambda x: (x.tier.value, x.display_name)
            )
            
            if steel_research:
                steel_text = "Steel: " + ", ".join(r.display_name for r in steel_research)
                tk.Label(
                    research_frame,
                    text=steel_text,
                    font=("Arial", 7),
                    bg='white',
                    wraplength=280,
                    justify=tk.LEFT
                ).pack(anchor=tk.W, padx=10)

            # Magic Path Research
            magic_research = sorted(
                [r for r in completed if r.path == 'magic'],
                key=lambda x: (x.tier.value, x.display_name)
            )
            
            if magic_research:
                magic_text = "Magic: " + ", ".join(r.display_name for r in magic_research)
                tk.Label(
                    research_frame,
                    text=magic_text,
                    font=("Arial", 7),
                    bg='white',
                    wraplength=280,
                    justify=tk.LEFT
                ).pack(anchor=tk.W, padx=10)

            if not (steel_research or magic_research):
                tk.Label(
                    research_frame,
                    text="No research",
                    font=("Arial", 7),
                    bg='white'
                ).pack(anchor=tk.W, padx=10)

        # Alliances in minimal format
        alliances = []
        for player in self.app.players:
            for ally in player.allies:
                if player.name < ally.name:
                    tk.Label(self.alliances_mirror, 
                            text=f"{player.name}↔{ally.name}", 
                            font=("Arial", 7)).pack(anchor=tk.W)

        if not self.alliances_mirror.winfo_children():
            tk.Label(self.alliances_mirror, text="No alliances", 
                    font=("Arial", 7)).pack()

        # NAPs
        naps = []
        for player in self.app.players:
            for nap in player.naps:
                if player.name < nap.name:
                    naps.append(f"{player.name}↔{nap.name}")
        
        if naps:
            ttk.Separator(self.alliances_mirror, orient='horizontal').pack(fill='x', pady=2)
            tk.Label(self.alliances_mirror, text="NAPs:", 
                    font=("Arial", 7, "bold")).pack(anchor=tk.W)
            for nap in naps:
                tk.Label(self.alliances_mirror, text=nap, 
                        font=("Arial", 7)).pack(anchor=tk.W)

        # Update armies mirror (only in Tregonia mode)
        if self.app.roll_mode == 'tregonia' and hasattr(self, 'armies_mirror'):
            # Get all sub-units to exclude them from top-level display
            all_sub_units = set()
            for unit in self.app.units:
                for sub_unit in unit.sub_units:
                    all_sub_units.add(sub_unit.unit_id)
                        
            # Display only top-level armies
            for unit in self.app.units:
                if unit.unit_id not in all_sub_units:
                    # Create frame for this army
                    army_frame = tk.Frame(self.armies_mirror, bg='white')
                    army_frame.pack(fill=tk.X, pady=1, padx=2)
                    
                    # Left side: Army ID and position indicator
                    info_frame = tk.Frame(army_frame, bg='white')
                    info_frame.pack(side=tk.LEFT)
                    
                    id_label = tk.Label(info_frame, 
                                    text=f"#{unit.unit_id}", 
                                    font=("Arial", 7),
                                    bg='white')
                    id_label.pack(side=tk.LEFT)
                    
                    # Add a small dot to indicate if army is placed on map
                    dot_color = 'green' if unit.position else 'red'
                    dot = tk.Frame(info_frame, 
                                width=4, height=4, 
                                bg=dot_color)
                    dot.pack(side=tk.LEFT, padx=2)
                    dot.pack_propagate(False)
                    
                    # Right side: Unit composition
                    if unit.is_army:
                        # Count units by type
                        unit_counts = {}
                        for sub_unit in unit.sub_units:
                            unit_type = sub_unit.unit_type.shorthand
                            unit_counts[unit_type] = unit_counts.get(unit_type, 0) + 1
                        
                        # Display unit counts
                        composition = ' '.join(f"{count}{type}" 
                                            for type, count in sorted(unit_counts.items()))
                    else:
                        composition = "Empty"
                    
                    tk.Label(army_frame, 
                            text=composition,
                            font=("Arial", 7),
                            bg='white').pack(side=tk.RIGHT)
                    
                    # Owner label in center
                    tk.Label(army_frame,
                            text=unit.owner,
                            font=("Arial", 7),
                            bg='white').pack(side=tk.LEFT, padx=4)
            
            if not self.armies_mirror.winfo_children():
                tk.Label(self.armies_mirror,
                        text="No armies",
                        font=("Arial", 7)).pack()

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "8", "normal"))
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def setup_sidebar(self):
        # Turn information
        self.turn_label = tk.Label(self.sidebar, text=f"Turn: {self.app.current_turn}")
        self.turn_label.pack(pady=5)
        
        # Core game buttons
        self.next_turn_button = tk.Button(self.sidebar, text="Next Turn", command=self.on_next_turn)
        self.next_turn_button.pack(pady=5)
        
        self.mode_button = tk.Button(self.sidebar, text="Switch to Erase Mode", command=self.toggle_mode)
        self.mode_button.pack(pady=5)
        
        self.undo_button = tk.Button(self.sidebar, text="Undo", command=self.undo)
        self.undo_button.pack(pady=5)
        
        # Add unit mode toggle if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.unit_mode_button = tk.Button(
                self.sidebar,
                text="Enter Unit Move Mode",
                command=self.toggle_unit_mode
            )
            self.unit_mode_button.pack(pady=5)

        # Player selection section
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.update_player_buttons()

        # Resource painting section
        tk.Label(self.sidebar, text="Resource Painting:").pack(pady=5)
        self.resource_buttons = []
        for resource_type in ['unactivated', 'gold', 'mana']:
            btn = tk.Button(
                self.sidebar,
                text=resource_type.capitalize(),
                command=lambda t=resource_type: self.select_resource_paint(t)
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.resource_buttons.append(btn)

    def select_resource_paint(self, resource_type):
        """Handle resource paint button selection"""
        # If this resource type is already selected, deselect it
        if self.resource_paint_mode == resource_type:
            self.resource_paint_mode = None
        else:
            self.resource_paint_mode = resource_type
            # Deselect player when entering resource paint mode
            self.app.selected_player = None
            
        # Update button appearances
        self.highlight_selected_player_button()  # Unhighlight player buttons
        self.highlight_resource_button()

    def highlight_resource_button(self):
        """Update button appearances based on selected resource type"""
        for btn in self.resource_buttons:
            if btn['text'].lower() == self.resource_paint_mode:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def setup_canvas(self):
        self.canvas_frame = tk.Frame(self.map_container)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
    def toggle_unit_mode(self):
        """Toggle between unit movement mode and regular map editing mode"""
        self.unit_mode = not self.unit_mode
        if self.unit_mode:
            self.unit_mode_button.config(text="Exit Unit Move Mode")
            self.mode_button.config(state=tk.DISABLED)
            self.canvas.config(cursor="crosshair")
        else:
            self.unit_mode_button.config(text="Enter Unit Move Mode")
            self.mode_button.config(state=tk.NORMAL)
            self.canvas.config(cursor="")
            self.selected_unit = None

    def on_canvas_right_click(self, event):
        """Handle right-click on canvas"""
        if not self.app.roll_mode == 'tregonia':
            return
            
        # Convert canvas coordinates to map coordinates
        x = int(self.canvas.canvasx(event.x) / self.zoom_level)
        y = int(self.canvas.canvasy(event.y) / self.zoom_level)
        
        # Check if we clicked on any unit
        clicked_unit = None
        for unit in self.app.units:
            if unit.position:
                unit_x, unit_y = unit.position
                # Define a click radius
                if abs(unit_x - x) < 20 and abs(unit_y - y) < 20:
                    clicked_unit = unit
                    break
        
        if clicked_unit:
            # Create popup menu
            popup = tk.Menu(self.canvas, tearoff=0)
            
            # Add "Remove from Map" option at the top
            popup.add_command(
                label="Remove from Map",
                command=lambda: self.remove_unit_from_map(clicked_unit)
            )
            popup.add_separator()
            
            if clicked_unit.is_army:
                # Create submenu for removing individual units
                units_menu = tk.Menu(popup, tearoff=0)
                if clicked_unit.sub_units:
                    for unit in clicked_unit.sub_units:
                        units_menu.add_command(
                            label=f"Remove {unit.unit_type.value} #{unit.unit_id}",
                            command=lambda u=unit: self.remove_unit_from_army(clicked_unit, u)
                        )
                else:
                    units_menu.add_command(label="No units in army", state=tk.DISABLED)
                
                popup.add_cascade(label="Remove Unit", menu=units_menu)
                popup.add_separator()
                popup.add_command(
                    label="Delete Entire Army",
                    command=lambda: self.delete_unit(clicked_unit)
                )
            else:
                # Single unit deletion
                popup.add_command(
                    label="Delete Unit",
                    command=lambda: self.delete_unit(clicked_unit)
                )
            
            # Display the popup menu at mouse position
            popup.tk_popup(event.x_root, event.y_root)

    def update_resource_ownership(self):
        """Update ownership of all resources based on surrounding territory"""
        if not self.app.map_image or self.app.roll_mode != 'tregonia':
            print("Resource ownership update skipped - no map or wrong mode")
            return
            
        print("\n=== Starting Resource Ownership Update ===")
        print(f"Total resources to check: {len(self.app.resource_tiles)}")
        print(f"Current tile owners count: {len(self.app.tile_owners)}")
        
        changes_made = False
        for pos, resource_info in self.app.resource_tiles.items():
            x, y = pos
            print(f"\nChecking resource at position {pos}")
            print(f"Current resource info: {resource_info}")
            
            # Check territory in radius around resource
            dominant_player, territory_count = check_territory_in_radius(
                self.app.map_image,
                self.app.tile_owners,
                x, y,
                radius=100
            )
            
            current_owner = resource_info.get('owner')
            print(f"Current owner: {current_owner}")
            print(f"Detected dominant player: {dominant_player}")
            
            if dominant_player != current_owner:
                print(f"Ownership change detected!")
                resource_info['owner'] = dominant_player
                changes_made = True
                if dominant_player:
                    print(f"Resource at {pos} claimed by {dominant_player} with {territory_count} surrounding tiles")
                else:
                    print(f"Resource at {pos} no longer controlled by any player")
        
        print("\n=== Resource Update Summary ===")
        print(f"Changes made: {changes_made}")
        
        if changes_made:
            print("Updating player resources and display...")
            self.app.update_player_resources()
            self.display_map_image()
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()


    def remove_unit_from_army(self, army, unit):
        """Remove a single unit from an army"""
        if unit in army.sub_units:
            army.sub_units.remove(unit)
            self.app.units.remove(unit)
            
            # Refresh displays
            self.display_map_image()
            if hasattr(self.app.current_screen, 'update_army_list'):
                self.app.current_screen.update_army_list()

    def remove_unit_from_map(self, unit):
        """Remove a unit from the map without deleting it from the game"""
        unit.position = None
        if unit.is_army:
            # If it's an army, remove all sub-units from map too
            for sub_unit in unit.sub_units:
                sub_unit.position = None
        self.display_map_image()

    def delete_unit(self, unit):
        """Delete a unit from both the map and the units list"""
        # First remove any sub-units if this is an army
        if unit.sub_units:
            for sub_unit in unit.sub_units[:]:  # Create a copy of the list to avoid modification while iterating
                self.app.units.remove(sub_unit)
        
        # Remove the unit itself
        self.app.units.remove(unit)
        
        # Refresh displays
        self.display_map_image()
        if hasattr(self.app.current_screen, 'update_army_list'):
            self.app.current_screen.update_army_list()

    def display_map_image(self):
        if self.app.map_image is None:
            return

        # Create display image at original size
        display_image = self.app.map_image.copy()
        draw = ImageDraw.Draw(display_image)
        
        # Draw owned tiles
        for (x, y), owner in self.app.tile_owners.items():
            if owner:
                player = next((p for p in self.app.players if p.name == owner), None)
                if player:
                    draw.point((x, y), fill=player.color)

        # Apply zoom
        if self.zoom_level != 1.0:
            new_size = (
                int(display_image.width * self.zoom_level),
                int(display_image.height * self.zoom_level)
            )
            display_image = display_image.resize(new_size, Image.Resampling.NEAREST)

        # Render units if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            unit_overlay = Image.new('RGBA', display_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(unit_overlay)
            
            # Create font scaled to zoom level
            try:
                unit_font = ImageFont.truetype("arial.ttf", int(16 * self.zoom_level))
            except IOError:
                unit_font = ImageFont.load_default()

            for unit in self.app.units:
                if unit.position:
                    x, y = [int(coord * self.zoom_level) for coord in unit.position]
                    owner = next((p for p in self.app.players if p.name == unit.owner), None)
                    owner_color = owner.color if owner else (128, 128, 128)
                    
                    draw.rectangle([x - 3, y - 3, x + 23, y + 23], fill='black')
                    draw.rectangle([x - 2, y - 2, x + 22, y + 22], fill='white')
                    draw.text((x + 1, y + 1), str(unit.unit_id), font=unit_font, fill='black')
                    draw.rectangle([x - 3, y + 24, x + 23, y + 28], fill='black')
                    draw.rectangle([x - 2, y + 25, x + 22, y + 27], fill=owner_color + (255,))

            display_image = Image.alpha_composite(display_image.convert('RGBA'), unit_overlay)

        # Update PhotoImage
        self.app.map_photo = ImageTk.PhotoImage(display_image)
        self.canvas.delete("all")
        
        # Center image in canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = display_image.width
        image_height = display_image.height
        
        x = max(0, (canvas_width - image_width) // 2)
        y = max(0, (canvas_height - image_height) // 2)
        
        self.map_item = self.canvas.create_image(x, y, image=self.app.map_photo, anchor=tk.NW)
        
        # Set scroll region with padding
        padding = 100
        self.canvas.config(scrollregion=(
            -padding,
            -padding,
            image_width + padding,
            image_height + padding
        ))

    def update_player_buttons(self):
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Button) and hasattr(widget, 'player_name'):
                widget.destroy()

        self.player_buttons = []
        for player in self.app.players:
            roll_info = self.app.player_rolls.get(player.name, ("", 0, 0))
            remaining_tiles = roll_info[2]
            
            if self.app.roll_mode == 'external':
                btn_text = f"{player.name}"
            else:
                btn_text = f"{player.name} ({remaining_tiles})"
                
            btn = tk.Button(
                self.sidebar,
                text=btn_text,
                command=lambda p=player: self.select_player(p)
            )
            btn.player_name = player.name
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.player_buttons.append(btn)
            
        self.highlight_selected_player_button()

    def select_player(self, player):
        """Handle player selection"""
        # If selecting a player, disable resource paint mode
        if self.resource_paint_mode is not None:
            self.resource_paint_mode = None
            self.highlight_resource_button()
            
        self.app.selected_player = player
        self.highlight_selected_player_button()

    def highlight_selected_player_button(self):
        for btn in self.player_buttons:
            if self.app.selected_player and btn.player_name == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right click
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down

    def on_mousewheel(self, event):
        if hasattr(self, '_zoom_after'):
            self.canvas.after_cancel(self._zoom_after)
        
        # Get mouse position relative to canvas
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # Get current image position
        bbox = self.canvas.bbox(self.map_item)
        if not bbox:
            return
            
        # Calculate relative position within the image
        image_x, image_y = bbox[0], bbox[1]
        rel_x = (mouse_x - image_x) / (bbox[2] - bbox[0])
        rel_y = (mouse_y - image_y) / (bbox[3] - bbox[1])
        
        # Update zoom level with finer control
        old_zoom = self.zoom_level
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        
        # Schedule the update
        self._zoom_after = self.canvas.after(50, lambda: self._update_zoom(rel_x, rel_y))

    def _update_zoom(self, rel_x, rel_y):
        # Update display
        self.display_map_image()
        
        # Get new image bbox
        bbox = self.canvas.bbox(self.map_item)
        if not bbox:
            return
            
        # Calculate new scroll position
        new_x = bbox[0] + (bbox[2] - bbox[0]) * rel_x
        new_y = bbox[1] + (bbox[3] - bbox[1]) * rel_y
        
        # Adjust scroll position
        self.canvas.xview_moveto((new_x - self.canvas.winfo_width()/2) / self.canvas.bbox(tk.ALL)[2])
        self.canvas.yview_moveto((new_y - self.canvas.winfo_height()/2) / self.canvas.bbox(tk.ALL)[3])

    def invalidate_display_cache(self):
        """Clear the cached display image to force a redraw"""
        if hasattr(self, 'current_display_image'):
            del self.current_display_image

    def on_canvas_click(self, event):
        if self.app.map_image is None:
            return

        # Convert canvas coordinates to original image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get the actual image position on the canvas
        bbox = self.canvas.bbox(self.map_item)
        if not bbox:
            return
            
        # Calculate offset from image origin
        image_x = canvas_x - bbox[0]
        image_y = canvas_y - bbox[1]
        
        # Convert to original image coordinates
        x = int(image_x / self.zoom_level)
        y = int(image_y / self.zoom_level)

        # Handle unit movement if in unit mode
        if self.app.roll_mode == 'tregonia' and self.unit_mode:
            self.handle_unit_placement(x, y)
            return

        # Check if click is within image bounds
        if x >= self.app.map_image.width or y >= self.app.map_image.height:
            return

        # Handle map coloring
        self.handle_map_coloring(x, y)

    def handle_map_coloring(self, x, y):
        """Handle map coloring using region-based approach"""
        # Save current state before modification
        self.app.map_history.append({
            'image': self.app.map_image.copy(),
            'tile_owners': self.app.tile_owners.copy(),
            'resource_tiles': self.app.resource_tiles.copy() if hasattr(self.app, 'resource_tiles') else {}
        })
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)

        # Get current pixel color
        target_color = self.app.map_image.getpixel((x, y))
        if len(target_color) == 4:
            target_color = target_color[:3]

        if self.resource_paint_mode:
            print(f"Resource paint mode active: {self.resource_paint_mode}")  # Debug
            replacement_color = self.RESOURCE_COLORS[self.resource_paint_mode]
            print(f"Painting with color: {replacement_color}")  # Debug
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                print(f"Found region with center: {region['center']}")  # Debug
                center = region['center']
                self.app.resource_tiles[center] = {
                    'type': self.resource_paint_mode,
                    'owner': None
                }
                print(f"Added resource tile at {center}: {self.app.resource_tiles[center]}")  # Debug
                
                # Update ownership immediately for the new resource
                if self.app.roll_mode == 'tregonia':
                    self.update_resource_ownership()
                    
            self.display_map_image()
            
            # Update any relevant displays
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()
            self.update_mirror_panels()
            return

        if self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

            replacement_color = tuple(int(c) for c in self.app.selected_player.color)

            if self.app.roll_mode == 'application':
                roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
                if roll_info[2] <= 0:
                    messagebox.showwarning("No Tiles Left",
                                        f"{self.app.selected_player.name} has no tiles left to place.")
                    return
                self.update_player_tiles(self.app.selected_player.name, -1)

            # Check for previous owner of this region
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                # Remove previous ownership if it exists
                for pos in region['boundary']:
                    previous_owner = self.app.tile_owners.get(pos)
                    if previous_owner and previous_owner != self.app.selected_player.name:
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(previous_owner, 1)
                        del self.app.tile_owners[pos]
                
                # Set new ownership for the entire region
                for pos in region['boundary']:
                    self.app.tile_owners[pos] = self.app.selected_player.name

        elif self.app.mode == 'erase':
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if len(replacement_color) == 4:
                replacement_color = replacement_color[:3]
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                for pos in region['boundary']:
                    if pos in self.app.tile_owners:
                        player_name = self.app.tile_owners.pop(pos)
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(player_name, 1)

        # Always update resource ownership
        if self.app.roll_mode == 'tregonia':
            self.update_resource_ownership()
            
            # Update displays
            for widget in self.app.master.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, PlayersScreen):
                            child.update_player_boxes()
                            break

        self.display_map_image()
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
            self.update_player_buttons()
        self.update_mirror_panels()  # Update mirrors after map changes

    def update_player_tiles(self, player_name, change):
        if player_name in self.app.player_rolls:
            roll_value, total_tiles, remaining_tiles = self.app.player_rolls[player_name]
            new_remaining = remaining_tiles + change
            self.app.player_rolls[player_name] = (roll_value, total_tiles, new_remaining)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def toggle_mode(self):
        if self.app.mode == 'color':
            self.app.mode = 'erase'
            self.mode_button.config(text="Switch to Color Mode")
        else:
            self.app.mode = 'color'
            self.mode_button.config(text="Switch to Erase Mode")

    def undo(self):
        """Undo the last map change"""
        if not self.app.map_history:
            messagebox.showinfo("Undo", "No actions to undo.")
            return
            
        # Pop and restore previous state
        previous_state = self.app.map_history.pop()
        
        # Important: Make sure we get a fresh copy of the previous image
        self.app.map_image = previous_state['image'].copy()
        self.app.tile_owners = previous_state['tile_owners'].copy()
        if 'resource_tiles' in previous_state:
            self.app.resource_tiles = previous_state['resource_tiles'].copy()
        
        # Make sure to get a fresh ImageDraw object
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        
        # Ensure the display is updated
        self.invalidate_display_cache()
        self.display_map_image()
        
        # Update all relevant UI elements
        self.update_player_buttons()
        self.update_mirror_panels()
        
        # Update resource ownership if in Tregonia mode
        if self.app.roll_mode == 'tregonia':
            self.update_resource_ownership()

    def on_next_turn(self):
            """Handle next turn button click"""
            if self.app.map_image is None:
                messagebox.showwarning("No Map Loaded", "Please import a map before proceeding to the next turn.")
                return
                
            # Apply resource increases for all players
            for player in self.app.players:
                player.apply_turn_increases()
                
            self.app.current_turn += 1
            self.app.save_current_map_state()
            self.app.map_history.clear()
            if self.app.roll_mode != 'external':
                self.app.player_rolls.clear()
                
            self.turn_label.config(text=f"Turn: {self.app.current_turn}")
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()
            self.update_player_buttons()
            self.update_mirror_panels()  # Update mirrors after turn change

    def destroy(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Button-3>")  # Unbind right click
        self.canvas.unbind("<MouseWheel>")
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.frame.destroy()