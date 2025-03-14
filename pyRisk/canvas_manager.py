import tkinter as tk
from PIL import ImageTk, Image

class CanvasManager:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Initialize zoom parameters
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_update_id = None
        
        # Initialize canvas components
        self.setup_canvas()
        
        # Buffer for storing rendered tiles
        self.tile_cache = {}
        self.tile_size = 256  # Standard tile size for efficient rendering
        
        # Initialize display variables
        self.map_photo = None
        self.map_item = None

    def setup_canvas(self):
        """Setup canvas with sliders and zoom controls"""
        # Create main canvas frame
        self.canvas_frame = tk.Frame(self.parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for zoom controls
        zoom_frame = tk.Frame(self.canvas_frame)
        zoom_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Add zoom buttons
        self.zoom_out_btn = tk.Button(zoom_frame, text="-", command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5)
        
        self.zoom_in_btn = tk.Button(zoom_frame, text="+", command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5)
        
        # Create zoom level label
        self.zoom_label = tk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        # Create canvas and scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='grey')
        self.h_scrollbar = tk.Scale(self.canvas_frame, orient=tk.HORIZONTAL, 
                                from_=0, to=100, command=self.on_h_scroll)
        self.v_scrollbar = tk.Scale(self.canvas_frame, orient=tk.VERTICAL, 
                                from_=0, to=100, command=self.on_v_scroll)
        
        # Pack canvas and scrollbars
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Optimized canvas configuration
        self.canvas.configure(
            scrollregion=(0, 0, 1, 1),  # Will be updated when image is loaded
            insertwidth=0,              # Remove cursor indicator
            highlightthickness=0,       # Remove highlight border
            xscrollincrement=1,         # Smooth scrolling
            yscrollincrement=1,
            takefocus=True             # Enable keyboard focus for better event handling
        )

    def zoom_in(self):
        """Handle zoom in button click"""
        if not self.app.map_image:
            return
            
        old_zoom = self.zoom_level
        self.zoom_level = min(self.max_zoom, self.zoom_level * 1.2)
        
        if old_zoom != self.zoom_level:
            # Update zoom label
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")
            
            # Update display
            self.app.display_map_image()

    def zoom_out(self):
        """Handle zoom out button click"""
        if not self.app.map_image:
            return
            
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, self.zoom_level / 1.2)
        
        if old_zoom != self.zoom_level:
            # Update zoom label
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")
            
            # Update display
            self.app.display_map_image()

    def on_h_scroll(self, value):
        """Handle horizontal scroll events"""
        if not self.app.map_image or not hasattr(self, 'map_item'):
            return
            
        # Convert percentage to actual position
        value = float(value) / 100
        self.canvas.xview_moveto(value)

    def on_v_scroll(self, value):
        """Handle vertical scroll events"""
        if not self.app.map_image or not hasattr(self, 'map_item'):
            return
            
        # Convert percentage to actual position
        value = float(value) / 100
        self.canvas.yview_moveto(value)

    def get_visible_region(self):
        """Get the currently visible region of the map"""
        if not self.app.map_image:
            return None
            
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Get scroll position
        x_view = self.canvas.xview()
        y_view = self.canvas.yview()
        
        # Calculate visible coordinates based on scroll position and zoom
        x1 = int(x_view[0] * self.app.map_image.width * self.zoom_level)
        y1 = int(y_view[0] * self.app.map_image.height * self.zoom_level)
        x2 = int(x_view[1] * self.app.map_image.width * self.zoom_level)
        y2 = int(y_view[1] * self.app.map_image.height * self.zoom_level)
        
        return (x1, y1, x2, y2)

    def get_required_tiles(self, visible_region):
        """Calculate which tiles are needed for the current view"""
        if not visible_region or not self.app.map_image:
            return set()
            
        x1, y1, x2, y2 = visible_region
        
        # Convert to tile coordinates with proper rounding
        start_tile_x = max(0, int(x1 / (self.tile_size * self.zoom_level)))
        start_tile_y = max(0, int(y1 / (self.tile_size * self.zoom_level)))
        end_tile_x = min(
            self.app.map_image.width // self.tile_size,
            int(x2 / (self.tile_size * self.zoom_level)) + 1
        )
        end_tile_y = min(
            self.app.map_image.height // self.tile_size,
            int(y2 / (self.tile_size * self.zoom_level)) + 1
        )
        
        return {(x, y) for x in range(start_tile_x, end_tile_x + 1)
                    for y in range(start_tile_y, end_tile_y + 1)} 