# utils.py

from PIL import Image

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB(A) colors"""
    # Convert to RGB if RGBA
    c1 = color1[:3]
    c2 = color2[:3]
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def flood_fill(image, x, y, target_color, replacement_color, tolerance=5):
    """
    Flood fill algorithm with color tolerance.
    
    Args:
        image: PIL Image to modify
        x, y: Starting coordinates
        target_color: Color to replace
        replacement_color: New color
        tolerance: How much color variation to allow (Euclidean distance)
    """
    pixels = image.load()
    width, height = image.size
    
    # Ensure coordinates are within bounds
    if x < 0 or x >= width or y < 0 or y >= height:
        return
        
    # Use a set for visited pixels to avoid duplicates
    visited = set()
    # Use a list as a stack for flood fill
    stack = [(x, y)]
    
    while stack:
        cx, cy = stack.pop()
        
        if (cx, cy) in visited:
            continue
            
        if cx < 0 or cx >= width or cy < 0 or cy >= height:
            continue
            
        current_color = pixels[cx, cy]
        
        # Check if current color is within tolerance of target color
        if color_distance(current_color, target_color) <= tolerance:
            pixels[cx, cy] = replacement_color
            visited.add((cx, cy))
            
            # Add adjacent pixels to stack
            stack.extend([
                (cx + 1, cy),
                (cx - 1, cy),
                (cx, cy + 1),
                (cx, cy - 1)
            ])