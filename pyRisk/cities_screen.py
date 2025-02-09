class CitiesScreen:
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
        tk.Label(title_frame, text="Cities Management", font=("Arial", 24)).pack(expand=True)

    def destroy(self):
        self.frame.destroy()