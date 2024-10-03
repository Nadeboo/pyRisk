# utils.py

from PIL import Image
from collections import deque
import math
import logging

# Configure logging (optional for debugging)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def color_distance(c1, c2):
    """
    Calculates the Euclidean distance between two RGB colors.

    Args:
        c1 (tuple): First color (R, G, B).
        c2 (tuple): Second color (R, G, B).

    Returns:
        float: Distance between the two colors.
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))

def flood_fill(image, x, y, target_color, replacement_color, tolerance=30, max_pixels=10000):
    """
    Performs a flood fill on the given image starting from (x, y), allowing for color variations.

    Args:
        image (PIL.Image): The image to perform flood fill on.
        x (int): The x-coordinate to start the fill.
        y (int): The y-coordinate to start the fill.
        target_color (tuple): The color to be replaced (RGBA).
        replacement_color (tuple): The color to fill with (RGBA).
        tolerance (int): The maximum color distance to consider for filling.
        max_pixels (int): Maximum number of pixels to fill to prevent excessive processing.

    Returns:
        None. The image is modified in place.
    """
    if target_color == replacement_color:
        logging.debug("Target color and replacement color are the same. Exiting flood fill.")
        return  # Prevent infinite loop if colors are the same

    pixels = image.load()
    width, height = image.size

    # Initialize deque for BFS
    queue = deque()
    queue.append((x, y))
    filled_pixels = 0
    logging.debug(f"Starting flood fill at ({x}, {y}) with tolerance {tolerance}")

    while queue and filled_pixels < max_pixels:
        nx, ny = queue.popleft()

        # Boundary check
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            logging.debug(f"Coordinates ({nx}, {ny}) out of bounds. Skipping.")
            continue

        current_color = pixels[nx, ny]

        # Calculate color distance (ignore alpha)
        distance = color_distance(current_color, target_color)
        if distance <= tolerance:
            pixels[nx, ny] = replacement_color
            logging.debug(f"Filling pixel at ({nx}, {ny}) with {replacement_color}")
            # Append neighboring pixels
            queue.append((nx + 1, ny))
            queue.append((nx - 1, ny))
            queue.append((nx, ny + 1))
            queue.append((nx, ny - 1))
            filled_pixels += 1

    if filled_pixels >= max_pixels:
        logging.warning("Maximum fill limit reached. Fill may be incomplete.")
