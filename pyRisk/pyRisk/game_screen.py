    def toggle_unit_mode(self):
        """Toggle between normal and unit placement mode"""
        self.unit_mode = not self.unit_mode
        
        if self.unit_mode:
            self.toggle_unit_btn.config(text="Exit Unit Move Mode")
            self.mode_toggle_btn.config(state=tk.DISABLED)
            self.canvas.config(cursor="crosshair")
        else:
            self.toggle_unit_btn.config(text="Enter Unit Move Mode")
            self.mode_toggle_btn.config(state=tk.NORMAL)
            self.canvas.config(cursor="")
            self.selected_unit = None 