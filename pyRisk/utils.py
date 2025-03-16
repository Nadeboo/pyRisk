# utils.py

from PIL import Image

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB(A) colors"""
    # Convert to RGB if RGBA
    c1 = color1[:3]
    c2 = color2[:3]
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def find_connected_region(pixels, start_x, start_y, target_color, width, height, tolerance=5):
    """Find a connected region of similar colors starting from a point using an iterative approach"""
    if start_x < 0 or start_x >= width or start_y < 0 or start_y >= height:
        return set()
        
    visited = {(start_x, start_y)}
    stack = [(start_x, start_y)]
    region = {(start_x, start_y)}
    
    # Pre-compute the valid coordinate ranges for faster boundary checking
    x_range = range(width)
    y_range = range(height)
    
    # Convert target color to RGB if it's RGBA
    if len(target_color) == 4:
        target_color = target_color[:3]
    
    while stack:
        x, y = stack.pop()
        
        # Check 4-connected neighbors
        for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if (nx, ny) in visited or nx not in x_range or ny not in y_range:
                continue
                
            visited.add((nx, ny))
            current_color = pixels[nx, ny]
            if len(current_color) == 4:
                current_color = current_color[:3]
                
            if color_distance(current_color, target_color) <= tolerance:
                stack.append((nx, ny))
                region.add((nx, ny))
                
    return region

def check_territory_in_radius(image, tile_owners, center_x, center_y, radius=100):
    """
    Check for player territory within a radius of a point.
    Handles territory regions instead of individual pixels.
    
    Args:
        image: PIL Image object
        tile_owners: Dictionary mapping (x,y) to player names
        center_x, center_y: Center coordinates to check around
        radius: Radius to check (default 100 pixels)
        
    Returns:
        tuple: (dominant_player, territory_count)
        where dominant_player is the name of the player with most territory regions,
        or None if no player has territory in the radius
    """
    player_regions = {}  # Count of regions per player
    
    # Get all unique regions in the radius
    checked_coords = set()
    width, height = image.size
    
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            x = center_x + dx
            y = center_y + dy
            
            if x < 0 or x >= width or y < 0 or y >= height:
                continue
                
            if (dx*dx + dy*dy) > radius*radius:
                continue
                
            if (x, y) in checked_coords:
                continue
                
            # Check if this point is part of a territory
            region_owner = tile_owners.get((x, y))
            if region_owner:
                # Count each connected region once
                if (x, y) not in checked_coords:
                    region = find_connected_region(
                        image.load(), x, y,
                        image.getpixel((x, y))[:3],
                        width, height
                    )
                    checked_coords.update(region)
                    player_regions[region_owner] = player_regions.get(region_owner, 0) + 1
    
    # Find player with most regions
    if not player_regions:
        return None, 0
        
    dominant_player = max(player_regions.items(), key=lambda x: x[1])
    return dominant_player[0], dominant_player[1]

def flood_fill(image, x, y, target_color, replacement_color, tolerance=5):
    """
    Region-based flood fill algorithm with optimized performance.
    Returns the region information for territory tracking.
    
    Args:
        image: PIL Image object
        x, y: Starting coordinates
        target_color: Color to replace
        replacement_color: New color
        tolerance: Color matching tolerance
        
    Returns:
        dict: Region information containing center and boundary points,
        or None if no region was filled
    """
    pixels = image.load()
    width, height = image.size
    
    if x < 0 or x >= width or y < 0 or y >= height:
        return None

    # Convert colors to RGB tuples for consistent comparison
    if len(target_color) == 4:
        target_color = target_color[:3]
    
    if len(replacement_color) == 4:
        replacement_rgb = replacement_color[:3]
        replacement_alpha = replacement_color[3]
    else:
        replacement_rgb = replacement_color
        replacement_alpha = 255
    
    # Use a more efficient data structure for the region
    region = find_connected_region(pixels, x, y, target_color, width, height, tolerance)
    
    # If no region found, return None
    if not region:
        return None
    
    # Batch process all pixels in the region
    for px, py in region:
        pixels[px, py] = replacement_rgb if len(replacement_color) == 3 else replacement_rgb
    
    # Calculate region statistics more efficiently
    x_coords = [x for x, _ in region]
    y_coords = [y for _, y in region]
    
    min_x = min(x_coords)
    max_x = max(x_coords)
    min_y = min(y_coords)
    max_y = max(y_coords)
    center = ((min_x + max_x) // 2, (min_y + max_y) // 2)
    
    return {
        'center': center,
        'boundary': region
    }