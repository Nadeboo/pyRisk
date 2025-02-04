# start_screen.py

import tkinter as tk


class StartScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        tk.Label(self.frame, text="Roll Mode", font=("Arial", 24)).pack(pady=50)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=20)
        
        # Create buttons for each mode
        modes = [
            ("External", self.set_external_mode),
            ("Application", self.set_application_mode),
            ("Tregonia", self.set_tregonia_mode)
        ]
        
        for text, command in modes:
            tk.Button(btn_frame, text=text, width=20, height=2, command=command).pack(pady=10)

    def set_external_mode(self):
        self.app.roll_mode = 'external'
        self.app.show_game_screen()

    def set_application_mode(self):
        self.app.roll_mode = 'application'
        self.app.show_game_screen()
        
    def set_tregonia_mode(self):
        self.app.roll_mode = 'tregonia'
        self.app.show_game_screen()

    def destroy(self):
        self.frame.destroy()