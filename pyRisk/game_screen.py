# game_screen.py 

import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
from utils import flood_fill

class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.text_size = 20  # Initialize text_size here
        self.text_color = (0, 0, 0, 255)  # Default text color: black
        self.setup_sidebar()
        self.setup_canvas()
        if self.app.map_image:
            self.display_map_image()
        self.bind_events()
        self.text_mode = False
        self.text_size = 20  # Default font size
        self.text_color = (0, 0, 0, 255)  # Default text color: black

    def setup_sidebar(self):
        self.sidebar = tk.Frame(self.frame, width=200, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.turn_label = tk.Label(self.sidebar, text=f"Turn: {self.app.current_turn}")
        self.turn_label.pack(pady=5)
        self.next_turn_button = tk.Button(self.sidebar, text="Next Turn", command=self.next_turn)
        self.next_turn_button.pack(pady=5)
        self.mode_button = tk.Button(self.sidebar, text="Switch to Erase Mode", command=self.toggle_mode)
        self.mode_button.pack(pady=5)
        self.undo_button = tk.Button(self.sidebar, text="Undo", command=self.undo)
        self.undo_button.pack(pady=5)
        
        # Add font size slider
        self.font_size_label = tk.Label(self.sidebar, text="Font Size:")
        self.font_size_label.pack(pady=(10, 0))
        self.font_size_slider = tk.Scale(self.sidebar, from_=8, to=72, orient=tk.HORIZONTAL, command=self.update_font_size)
        self.font_size_slider.set(self.text_size)
        self.font_size_slider.pack(pady=5)
        
        # Add text mode button
        self.text_mode_button = tk.Button(self.sidebar, text="Enter Text Mode", command=self.toggle_text_mode)
        self.text_mode_button.pack(pady=5)
        
        # Add font size slider
        self.font_size_label = tk.Label(self.sidebar, text="Font Size:")
        self.font_size_label.pack(pady=(10, 0))
        self.font_size_slider = tk.Scale(self.sidebar, from_=8, to=72, orient=tk.HORIZONTAL, command=self.update_font_size)
        self.font_size_slider.set(self.text_size)
        self.font_size_slider.pack(pady=5)
        
        # Add text color button
        self.text_color_button = tk.Button(self.sidebar, text="Choose Text Color", command=self.choose_text_color)
        self.text_color_button.pack(pady=5)
        
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.update_player_buttons()
        
    def update_font_size(self, val):
        self.text_size = int(val)

    def setup_canvas(self):
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_canvas_click(self, event):
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before coloring.")
            return
        x, y = int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))
        if x >= self.app.map_image.width or y >= self.app.map_image.height:
            return

        if self.app.mode == 'text':
            self.add_text_to_map(x, y)
        elif self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return
            
            self.app.map_history.append(self.app.map_image.copy())
            if len(self.app.map_history) > self.app.max_history:
                self.app.map_history.pop(0)
            
            current_owner = self.app.tile_owners.get((x, y))
            if current_owner == self.app.selected_player.name and self.app.rule_manager.is_rule_active("Fortification"):
                # Fortify the tile
                self.app.rule_manager.apply_rule("Fortification", self.app, x, y)
            else:
                # Normal coloring logic
                target_color = self.app.map_image.getpixel((x, y))
                replacement_color = (
                    int(self.app.selected_player.color[0]),
                    int(self.app.selected_player.color[1]),
                    int(self.app.selected_player.color[2]),
                    255
                )
                if self.app.roll_mode != 'external':
                    roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
                    if roll_info[2] <= 0:
                        messagebox.showwarning("No Tiles Left",
                                               f"{self.app.selected_player.name} has no tiles left to place.")
                        return
                self.app.capture_tile(x, y, self.app.selected_player.name)
                flood_fill(self.app.map_image, x, y, target_color, replacement_color)
        elif self.app.mode == 'erase':
            target_color = self.app.map_image.getpixel((x, y))
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if (x, y) in self.app.tile_owners:
                player_name = self.app.tile_owners.pop((x, y))
                if self.app.roll_mode != 'external':
                    self.update_player_tiles(player_name, 1)
            if (x, y) in self.app.fortified_tiles:
                del self.app.fortified_tiles[(x, y)]
            flood_fill(self.app.map_image, x, y, target_color, replacement_color)
        
        self.display_map_image()
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
        self.update_player_buttons()

    def display_map_image(self):
        if self.app.map_image is None:
            return
        display_image = self.app.map_image.copy()
        draw = ImageDraw.Draw(display_image)
        for (x, y), owner in self.app.tile_owners.items():
            if owner:
                player = next((p for p in self.app.players if p.name == owner), None)
                if player:
                    if len(player.color) == 3:
                        player_color = (*player.color, 255)
                    elif len(player.color) == 4:
                        player_color = player.color
                    else:
                        messagebox.showerror("Invalid Color Format",
                                             f"Player '{player.name}' has an invalid color format: {player.color}")
                        continue
                    
                    # Apply darkening effect for fortified tiles
                    if (x, y) in self.app.fortified_tiles:
                        player_color = tuple(int(c * 0.7) for c in player_color[:3]) + (player_color[3],)
                    
                    draw.point((x, y), fill=player_color)
        
        self.app.map_photo = ImageTk.PhotoImage(display_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.app.map_photo, anchor=tk.NW)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.config(width=800, height=600)

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
        elif self.app.mode == 'erase':
            self.app.mode = 'color'
            self.mode_button.config(text="Switch to Erase Mode")
        self.text_mode = False
        self.text_mode_button.config(text="Enter Text Mode")

    def toggle_text_mode(self):
        self.text_mode = not self.text_mode
        if self.text_mode:
            self.text_mode_button.config(text="Exit Text Mode")
            self.app.mode = 'text'
        else:
            self.text_mode_button.config(text="Enter Text Mode")
            self.app.mode = 'color'

    def update_font_size(self, val):
        self.text_size = int(val)

    def choose_text_color(self):
        color = colorchooser.askcolor(title="Choose text color")
        if color[0]:
            self.text_color = color[0] + (255,)  # Add alpha channel

    def add_text_to_map(self, x, y):
        text = simpledialog.askstring("Add Text", "Enter text to add:")
        if text:
            self.app.map_history.append(self.app.map_image.copy())
            if len(self.app.map_history) > self.app.max_history:
                self.app.map_history.pop(0)
            
            draw = ImageDraw.Draw(self.app.map_image)
            try:
                font = ImageFont.truetype("arial.ttf", self.text_size)
            except IOError:
                font = ImageFont.load_default()
                print("Arial font not found. Using default font.")
            
            draw.text((x, y), text, font=font, fill=self.text_color)
            self.display_map_image()

    def undo(self):
        if not self.app.map_history:
            messagebox.showinfo("Undo", "No actions to undo.")
            return
        self.app.map_image = self.app.map_history.pop()
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        self.display_map_image()
        self.update_player_buttons()

    def next_turn(self):
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before proceeding to the next turn.")
            return
        self.app.current_turn += 1
        self.app.save_current_map_state()
        self.app.map_history.clear()
        if self.app.roll_mode != 'external':
            self.app.player_rolls.clear()
        self.turn_label.config(text=f"Turn: {self.app.current_turn}")
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
        self.update_player_buttons()

    def update_player_buttons(self):
        for widget in self.sidebar.pack_slaves():
            if widget not in [self.next_turn_button, self.mode_button, self.undo_button, self.turn_label, self.select_player_label, self.text_mode_button, self.font_size_label, self.font_size_slider, self.text_color_button]:
                widget.destroy()
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.player_buttons = []
        for player in self.app.players:
            btn_text = f"{player.name}"
            btn = tk.Button(self.sidebar, text=btn_text, command=lambda p=player: self.select_player(p))
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.player_buttons.append(btn)
        self.highlight_selected_player_button()

    def select_player(self, player):
        self.app.selected_player = player
        self.highlight_selected_player_button()

    def highlight_selected_player_button(self):
        for btn in self.player_buttons:
            btn_player_name = btn['text']
            if self.app.selected_player and btn_player_name == self.app.selected_player.name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

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
            player_color = (*player.color, 255) if len(player.color) == 3 else player.color
            self.app.map_draw.point((x, y), fill=player_color)
        self.display_map_image()

    def destroy(self):
        self.canvas.unbind("<Button-1>")
        self.frame.destroy()