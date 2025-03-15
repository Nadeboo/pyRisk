#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path so we can import pyRisk
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import and run the main function
if __name__ == "__main__":
    from pyRisk.pyRisk import MSPaintRiskEditor
    import tkinter as tk
    root = tk.Tk()
    app = MSPaintRiskEditor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop() 