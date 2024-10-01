# game_screen.py

import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, ImageDraw
from utils import flood_fill


class GameScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app  # Reference to the main application
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_sidebar()
        self.setup_canvas()
        if self.app.map_image:
            self.display_map_image()
        self.bind_events()

    def setup_sidebar(self):
        self.sidebar = tk.Frame(self.frame, width=200, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.turn_label = tk.Label(self.sidebar, text=f"Turn: {self.app.current_turn}")
        self.turn_label.pack(pady=5)
        # Store references to the buttons
        self.next_turn_button = tk.Button(self.sidebar, text="Next Turn", command=self.next_turn)
        self.next_turn_button.pack(pady=5)
        self.mode_button = tk.Button(self.sidebar, text="Switch to Erase Mode", command=self.toggle_mode)
        self.mode_button.pack(pady=5)
        self.undo_button = tk.Button(self.sidebar, text="Undo", command=self.undo)
        self.undo_button.pack(pady=5)
        # Store reference to the "Select Player:" label
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.update_player_buttons()

    def update_player_buttons(self):
        # Remove existing player buttons and the "Select Player:" label if any
        for widget in self.sidebar.pack_slaves():
            if widget not in [self.next_turn_button, self.mode_button, self.undo_button, self.turn_label]:
                widget.destroy()
        # Re-add the "Select Player:" label
        self.select_player_label = tk.Label(self.sidebar, text="Select Player:")
        self.select_player_label.pack(pady=5)
        self.player_buttons = []
        for player in self.app.players:
            # Get remaining tiles for the player
            roll_info = self.app.player_rolls.get(player.name, ("", 0, 0))
            remaining_tiles = roll_info[2]
            # Display player's name and remaining tiles
            btn_text = f"{player.name} ({remaining_tiles})"
            btn = tk.Button(self.sidebar, text=btn_text, command=lambda p=player: self.select_player(p))
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.player_buttons.append(btn)
        self.highlight_selected_player_button()

    def select_player(self, player):
        self.app.selected_player = player
        self.highlight_selected_player_button()

    def highlight_selected_player_button(self):
        for btn in self.player_buttons:
            if btn.winfo_exists():
                btn_player_name = btn['text'].split(' (')[0]  # Extract player name from button text
                if self.app.selected_player and btn_player_name == self.app.selected_player.name:
                    btn.config(relief=tk.SUNKEN)
                else:
                    btn.config(relief=tk.RAISED)

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

    def display_map_image(self):
        self.app.map_photo = ImageTk.PhotoImage(self.app.map_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.app.map_photo, anchor=tk.NW)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.config(width=800, height=600)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_canvas_click(self, event):
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before coloring.")
            return
        x, y = int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))
        if x >= self.app.map_image.width or y >= self.app.map_image.height:
            return
        self.app.map_history.append(self.app.map_image.copy())
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)
        if self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return
            target_color = self.app.map_image.getpixel((x, y))
            replacement_color = (
                int(self.app.selected_player.color[0]),
                int(self.app.selected_player.color[1]),
                int(self.app.selected_player.color[2]),
                255
            )
            roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
            if roll_info[2] <= 0:
                messagebox.showwarning("No Tiles Left",
                                       f"{self.app.selected_player.name} has no tiles left to place.")
                return
            previous_owner = self.app.tile_owners.get((x, y))
            if previous_owner and previous_owner != self.app.selected_player.name:
                self.update_player_tiles(previous_owner, 1)
            self.app.tile_owners[(x, y)] = self.app.selected_player.name
            self.update_player_tiles(self.app.selected_player.name, -1)
        elif self.app.mode == 'erase':
            target_color = self.app.map_image.getpixel((x, y))
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if (x, y) in self.app.tile_owners:
                player_name = self.app.tile_owners.pop((x, y))
                self.update_player_tiles(player_name, 1)
        else:
            return
        flood_fill(self.app.map_image, x, y, target_color, replacement_color)
        self.display_map_image()
        # Update player list if the current screen has update_player_list method
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
        # Update player buttons
        self.update_player_buttons()

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
        if not self.app.map_history:
            messagebox.showinfo("Undo", "No actions to undo.")
            return
        self.app.map_image = self.app.map_history.pop()
        self.app.map_draw = ImageDraw.Draw(self.app.map_image)
        self.display_map_image()
        # Refresh player buttons to update remaining tiles display
        self.update_player_buttons()

    def next_turn(self):
        """Advance to the next turn and update necessary components."""
        if self.app.map_image is None:
            messagebox.showwarning("No Map Loaded", "Please import a map before proceeding to the next turn.")
            return
        self.app.current_turn += 1
        self.app.save_current_map_state()
        self.app.map_history.clear()
        self.app.player_rolls.clear()
        self.turn_label.config(text=f"Turn: {self.app.current_turn}")
        # Update player list if the current screen has update_player_list method
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
        # Refresh player buttons to clear remaining tiles
        self.update_player_buttons()

    def destroy(self):
        self.canvas.unbind("<Button-1>")
        self.frame.destroy()
