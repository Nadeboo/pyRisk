# utils.py

from PIL import Image

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB(A) colors"""
    # Convert to RGB if RGBA
    c1 = color1[:3]
    c2 = color2[:3]
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

# In utils.py, modify flood_fill to track affected coordinates:
def flood_fill(image, x, y, target_color, replacement_color, tolerance=5):
    """
    Flood fill algorithm with color tolerance.
    Returns set of all coordinates that were filled.
    """
    pixels = image.load()
    width, height = image.size
    
    if x < 0 or x >= width or y < 0 or y >= height:
        return set()
        
    visited = set()
    stack = [(x, y)]
    filled_coords = set()
    
    while stack:
        cx, cy = stack.pop()
        
        if (cx, cy) in visited:
            continue
            
        if cx < 0 or cx >= width or cy < 0 or cy >= height:
            continue
            
        current_color = pixels[cx, cy]
        
        if color_distance(current_color, target_color) <= tolerance:
            pixels[cx, cy] = replacement_color
            visited.add((cx, cy))
            filled_coords.add((cx, cy))
            
            stack.extend([
                (cx + 1, cy),
                (cx - 1, cy),
                (cx, cy + 1),
                (cx, cy - 1)
            ])
    
    return filled_coords