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
        tk.Button(btn_frame, text="External", width=20, height=2, command=self.set_external_mode).pack(pady=10)
        tk.Button(btn_frame, text="Application", width=20, height=2, command=self.set_application_mode).pack(pady=10)

    def set_external_mode(self):
        self.app.roll_mode = 'external'
        self.app.show_game_screen()

    def set_application_mode(self):
        self.app.roll_mode = 'application'
        self.app.show_game_screen()

    def destroy(self):
        self.frame.destroy()
