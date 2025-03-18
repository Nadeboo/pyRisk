import tkinter as tk

class CustomScrollbar:
    """A canvas-based custom scrollbar implementation with full control over appearance"""
    
    def __init__(self, parent, orientation="vertical", command=None, width=16, bg="#3C3F41", fg="#5A5D5F"):
        """Initialize a new custom scrollbar
        
        Args:
            parent: Parent widget
            orientation: 'vertical' or 'horizontal'
            command: Command to execute when scrollbar is moved (typically a xview or yview)
            width: Width of the scrollbar
            bg: Background color
            fg: Foreground color (thumb color)
        """
        self.parent = parent
        self.orientation = orientation
        self.command = command
        self.width = width
        self.bg = bg  # Background/trough color
        self.fg = fg  # Foreground/thumb color
        
        # Create canvas for drawing the scrollbar
        if orientation == "vertical":
            self.canvas = tk.Canvas(parent, width=width, height=10, bg=bg, 
                                   highlightthickness=0, bd=0)
        else:
            self.canvas = tk.Canvas(parent, width=10, height=width, bg=bg,
                                   highlightthickness=0, bd=0)
        
        # Initial state
        self.start = 0.0
        self.end = 1.0
        self.thumb = None  # Canvas item ID for the thumb/slider
        self._drag_data = {"y": 0, "x": 0, "item": None, "current_start": 0.0}
        
        # Bind events
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        # Bind mouse wheel events
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        
        # Draw initial scrollbar
        self._draw_scrollbar()
    
    def _on_configure(self, event):
        """Handle resize events"""
        self._draw_scrollbar()
    
    def _draw_scrollbar(self):
        """Draw or redraw the scrollbar"""
        self.canvas.delete("all")  # Clear canvas
        
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            # Canvas not visible yet
            return
        
        # Draw the trough (background) - actually already the canvas bg
        
        # Calculate thumb position and size
        if self.orientation == "vertical":
            thumb_height = max(height * (self.end - self.start), 30)  # Minimum thumb size
            thumb_y1 = height * self.start
            thumb_y2 = thumb_y1 + thumb_height
            
            self.thumb = self.canvas.create_rectangle(
                2, thumb_y1, width-2, thumb_y2,
                fill=self.fg, outline="", width=0, tags="thumb"
            )
        else:
            thumb_width = max(width * (self.end - self.start), 30)  # Minimum thumb size
            thumb_x1 = width * self.start
            thumb_x2 = thumb_x1 + thumb_width
            
            self.thumb = self.canvas.create_rectangle(
                thumb_x1, 2, thumb_x2, height-2,
                fill=self.fg, outline="", width=0, tags="thumb"
            )
    
    def _on_click(self, event):
        """Handle mouse clicks on the scrollbar"""
        if not self.thumb:
            return
            
        # Check if click is on thumb first
        x, y = event.x, event.y
        closest = self.canvas.find_closest(x, y)[0]
        
        if closest == self.thumb:
            # User clicked on the thumb - prepare for dragging
            self._drag_data["item"] = self.thumb
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            self._drag_data["current_start"] = self.start
            return
            
        # User clicked elsewhere on the scrollbar - jump to position
        if self.orientation == "vertical":
            total = self.canvas.winfo_height()
            pos = event.y / total
        else:
            total = self.canvas.winfo_width()
            pos = event.x / total
        
        # Calculate thumb size
        thumb_size = self.end - self.start
        
        # Move directly to clicked position
        if pos < self.start:
            # Page up
            new_start = max(0, pos)
            new_end = min(1.0, new_start + thumb_size)
            self.set(new_start, new_end)
            if self.command:
                self.command("moveto", new_start)
        elif pos > self.end:
            # Page down
            new_start = min(pos - thumb_size, 1.0 - thumb_size)
            new_end = min(1.0, new_start + thumb_size)
            self.set(new_start, new_end)
            if self.command:
                self.command("moveto", new_start)
    
    def _on_drag(self, event):
        """Handle dragging the thumb"""
        if not self._drag_data["item"]:
            return
            
        # Calculate how far the mouse has moved
        if self.orientation == "vertical":
            delta_y = event.y - self._drag_data["y"]
            total = self.canvas.winfo_height()
            delta_pos = delta_y / total
        else:
            delta_x = event.x - self._drag_data["x"]
            total = self.canvas.winfo_width()
            delta_pos = delta_x / total
        
        # Calculate new positions
        new_start = max(0, min(self._drag_data["current_start"] + delta_pos, 1.0 - (self.end - self.start)))
        new_end = new_start + (self.end - self.start)
        
        # Update the display
        self.set(new_start, new_end)
        
        # Execute the command with the new position
        if self.command:
            self.command("moveto", new_start)
    
    def _on_release(self, event):
        """Handle release of mouse button"""
        # Reset the drag data
        self._drag_data = {"y": 0, "x": 0, "item": None, "current_start": 0.0}
    
    def _on_mousewheel(self, event):
        """Handle mousewheel events for scrolling"""
        # Determine scroll direction and amount
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # Scroll up
            amount = -1
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # Scroll down
            amount = 1
        else:
            return
        
        # Execute the scroll command
        if self.command:
            self.command("scroll", amount, "units")
    
    def set(self, *args):
        """Set the thumb position.
        
        This method handles various Tkinter scrollbar set patterns:
        - set(start, end): Direct setting of thumb position (0.0-1.0)
        - set('moveto', fraction): Move to a specific position
        - set('scroll', amount, 'units'/'pages'): Scroll by amount
        """
        if not args:
            return
            
        # Case 1: Standard (start, end) setting
        if len(args) == 2 and all(isinstance(arg, (int, float, str)) for arg in args):
            start, end = args
            
            # Convert string values to float
            if isinstance(start, str):
                try:
                    start = float(start)
                except ValueError:
                    start = 0.0
                    
            if isinstance(end, str):
                try:
                    end = float(end)
                except ValueError:
                    end = 1.0
                    
            # Update thumb position
            self.start = max(0.0, min(float(start), 1.0))
            self.end = max(0.0, min(float(end), 1.0))
            
            # Ensure minimum thumb size
            min_size = 0.1
            if self.end - self.start < min_size:
                self.end = min(1.0, self.start + min_size)
                
            # Redraw scrollbar
            self._draw_scrollbar()
            return
            
        # Case 2: Command patterns like ('moveto', fraction) or ('scroll', amount, 'units'/'pages')
        if args and isinstance(args[0], str):
            command = args[0]
            
            if command == 'moveto' and len(args) >= 2:
                fraction = args[1]
                if isinstance(fraction, str):
                    try:
                        fraction = float(fraction)
                    except ValueError:
                        return
                
                # Calculate thumb size
                thumb_size = self.end - self.start
                
                # Calculate new position
                new_start = max(0.0, min(float(fraction), 1.0 - thumb_size))
                new_end = new_start + thumb_size
                
                # Update position
                self.start = new_start
                self.end = new_end
                
                # Redraw scrollbar
                self._draw_scrollbar()
                
                # Execute the actual view command if it exists
                if self.command:
                    self.command('moveto', fraction)
                return
                
            elif command == 'scroll' and len(args) >= 3:
                amount = args[1]
                unit = args[2]  # 'units' or 'pages'
                
                if isinstance(amount, str):
                    try:
                        amount = int(amount)
                    except ValueError:
                        return
                
                # Calculate thumb size
                thumb_size = self.end - self.start
                
                # Calculate scroll amount based on unit
                if unit == 'units':
                    delta = 0.05 * amount  # Scroll by 5% per unit
                elif unit == 'pages':
                    delta = 0.2 * amount  # Scroll by 20% per page
                else:
                    return
                
                # Calculate new position
                new_start = max(0.0, min(self.start + delta, 1.0 - thumb_size))
                new_end = new_start + thumb_size
                
                # Update position
                self.start = new_start
                self.end = new_end
                
                # Redraw scrollbar
                self._draw_scrollbar()
                
                # Execute the actual view command if it exists
                if self.command:
                    self.command('scroll', amount, unit)
                return
    
    def get(self):
        """Get current thumb position
        
        Returns:
            (start, end) tuple
        """
        return (self.start, self.end)
    
    def pack(self, **kwargs):
        """Pack the scrollbar"""
        self.canvas.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Place the scrollbar in a grid"""
        self.canvas.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the scrollbar"""
        self.canvas.place(**kwargs)
    
    def config(self, **kwargs):
        """Configure the scrollbar
        
        Args:
            bg: Background color
            fg: Foreground color
            command: Command to execute
        """
        if "bg" in kwargs:
            self.bg = kwargs["bg"]
            self.canvas.config(bg=self.bg)
        if "fg" in kwargs:
            self.fg = kwargs["fg"]
        if "command" in kwargs:
            self.command = kwargs["command"]
        if "width" in kwargs:
            self.width = kwargs["width"]
            if self.orientation == "vertical":
                self.canvas.config(width=self.width)
            else:
                self.canvas.config(height=self.width)
                
        self._draw_scrollbar()
        
    # Alias for config
    configure = config 