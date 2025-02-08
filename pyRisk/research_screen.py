import tkinter as tk
from tkinter import ttk, messagebox

class ResearchScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.setup_widgets()

    def setup_widgets(self):
        # Main title
        title_frame = tk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=20)
        tk.Label(title_frame, text="Research Management", font=("Arial", 24)).pack(expand=True)

        # Placeholder message
        placeholder_frame = tk.Frame(self.frame)
        placeholder_frame.pack(expand=True)
        tk.Label(
            placeholder_frame,
            text="Research system coming soon...",
            font=("Arial", 14)
        ).pack(pady=20)

    def destroy(self):
        """Clean up the screen when switching away"""
        self.frame.destroy()