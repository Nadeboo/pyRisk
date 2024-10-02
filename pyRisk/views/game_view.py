# views/game_view.py

import tkinter as tk
from tkinter import messagebox, colorchooser
from PIL import ImageTk
from typing import Callable, Optional
from utils.utils import flood_fill


class GameView:
    def __init__(self, parent: tk.Frame, controller: Callable):
        """
        Initialize the GameView.

        Args:
            parent (tk.Frame): The parent Tkinter frame.
            controller (Callable): The controller callback to handle user actions.
        """
        self.parent = parent
        self.controller = controller
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.map_photo = None  # To keep a reference to the PhotoImage
        self.setup_sidebar()
        self.setup_canvas()

    def setup_sidebar(self):
        """
        Set up the sidebar containing turn information, player selection, and control buttons.
        """
        self.sidebar = tk.Frame(self.frame, width=200, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)

        # Turn Label
        self.turn_label = tk.Label(
            self.sidebar, text="Turn: 0", font=("Arial", 14)
        )
        self.turn_label.pack(pady=10)

        # Next Turn Button
        self.next_turn_button = tk.Button(
            self.sidebar, text="Next Turn", command=lambda: self.controller("next_turn")
        )
        self.next_turn_button.pack(pady=5)

        # Mode Toggle Button
        self.mode_button = tk.Button(
            self.sidebar, text="Switch to Erase Mode",
            command=lambda: self.controller("toggle_mode")
        )
        self.mode_button.pack(pady=5)

        # Undo Button
        self.undo_button = tk.Button(
            self.sidebar, text="Undo", command=lambda: self.controller("undo")
        )
        self.undo_button.pack(pady=5)

        # Player Selection
        self.select_player_label = tk.Label(
            self.sidebar, text="Select Player:", font=("Arial", 12)
        )
        self.select_player_label.pack(pady=10)

        self.player_buttons = []
        self.selected_player = None

    def setup_canvas(self):
        """
        Set up the canvas for displaying and interacting with the game map.
        """
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        # Bind resize event
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        # Bind click event
        self.canvas.bind("<Button-1>", lambda event: self.controller("canvas_click", event))

    def display_map_image(self, map_image: Optional['PIL.Image.Image'] = None):
        """
        Display the map image on the canvas.

        Args:
            map_image (PIL.Image.Image, optional): The map image to display. Defaults to None.
        """
        if map_image:
            self.map_photo = ImageTk.PhotoImage(map_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.map_photo, anchor=tk.NW)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            self.canvas.config(width=800, height=600)

    def update_turn_label(self, turn: int):
        """
        Update the turn label with the current turn number.

        Args:
            turn (int): The current turn number.
        """
        self.turn_label.config(text=f"Turn: {turn}")

    def update_mode_button(self, current_mode: str):
        """
        Update the mode toggle button text based on the current mode.

        Args:
            current_mode (str): The current mode ('color' or 'erase').
        """
        if current_mode == 'color':
            self.mode_button.config(text="Switch to Erase Mode")
        else:
            self.mode_button.config(text="Switch to Color Mode")

    def update_player_buttons(self, players: list, selected_player: Optional['Player'] = None):
        """
        Update the player selection buttons based on the current list of players.

        Args:
            players (list): List of Player objects.
            selected_player (Player, optional): The currently selected player. Defaults to None.
        """
        # Clear existing buttons
        for btn in self.player_buttons:
            btn.destroy()
        self.player_buttons.clear()

        for player in players:
            btn_text = f"{player.name}"
            btn = tk.Button(
                self.sidebar, text=btn_text, width=18,
                command=lambda p=player: self.controller("select_player", p)
            )
            btn.pack(pady=2)
            self.player_buttons.append(btn)
            if selected_player and player.name == selected_player.name:
                btn.config(relief=tk.SUNKEN)

    def on_canvas_configure(self, event):
        """
        Update the scroll region of the canvas when it's resized.

        Args:
            event: The Tkinter event object.
        """
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def highlight_selected_player_button(self, player_name: Optional[str]):
        """
        Highlight the selected player's button.

        Args:
            player_name (str, optional): The name of the selected player. Defaults to None.
        """
        for btn in self.player_buttons:
            if player_name and btn['text'] == player_name:
                btn.config(relief=tk.SUNKEN)
            else:
                btn.config(relief=tk.RAISED)

    def get_canvas_click_coordinates(self, event) -> tuple:
        """
        Get the (x, y) coordinates of a click event on the canvas.

        Args:
            event: The Tkinter event object.

        Returns:
            tuple: (x, y) coordinates adjusted for canvas scrolling.
        """
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        return x, y

    def destroy(self):
        """
        Destroy the GameView frame.
        """
        self.canvas.unbind("<Button-1>")
        self.frame.destroy()
