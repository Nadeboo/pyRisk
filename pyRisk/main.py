# main.py

import tkinter as tk
from controllers.application_controller import ApplicationController


def main():
    root = tk.Tk()
    root.title("MSPaint Risk Editor")
    root.geometry("1024x768")
    app = ApplicationController(root)
    root.protocol("WM_DELETE_WINDOW", app.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
