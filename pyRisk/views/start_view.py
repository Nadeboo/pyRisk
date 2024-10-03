# views/start_view.py

import tkinter as tk
from tkinter import ttk
from typing import Callable


class StartView:
    def __init__(self, parent: tk.Frame, controller: Callable):
        """
        Initialize the StartView.

        Args:
            parent (tk.Frame): The parent Tkinter frame.
            controller (Callable): The controller callback to handle user actions.
        """
        self.parent = parent
        self.controller = controller
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        """
        Set up the widgets for the StartView.
        """
        title_label = tk.Label(
            self.frame, text="Welcome to MSPaint Risk Editor", font=("Arial", 24)
        )
        title_label.pack(pady=50)

        instruction_label = tk.Label(
            self.frame,
            text="Select Roll Mode to Begin:",
            font=("Arial", 16)
        )
        instruction_label.pack(pady=20)

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)

        external_btn = tk.Button(
            btn_frame,
            text="External Roll Mode",
            width=20,
            height=2,
            command=lambda: self.controller("external")
        )
        external_btn.pack(pady=10)

        application_btn = tk.Button(
            btn_frame,
            text="Application Roll Mode",
            width=20,
            height=2,
            command=lambda: self.controller("application")
        )
        application_btn.pack(pady=10)

    def destroy(self):
        """
        Destroy the StartView frame.
        """
        self.frame.destroy()
