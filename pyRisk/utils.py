# utils.py

from collections import deque
import logging
import math

def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))

def flood_fill(image, x, y, target_color, replacement_color, tolerance=30, max_pixels=10000):
    """
    Performs a flood fill on the given image starting from (x, y), allowing for color variations.
    """
    pixels = image.load()
    width, height = image.size

    # Initialize deque for BFS and set for visited pixels
    queue = deque([(x, y)])
    visited = set()
    filled_pixels = 0
    logging.debug(f"Starting flood fill at ({x}, {y}) with tolerance {tolerance}")

    while queue and filled_pixels < max_pixels:
        nx, ny = queue.popleft()

        # Skip if already visited
        if (nx, ny) in visited:
            continue

        # Boundary check
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue

        current_color = pixels[nx, ny]

        # Calculate color distance (ignore alpha)
        distance = color_distance(current_color, target_color)
        if distance <= tolerance:
            pixels[nx, ny] = replacement_color
            logging.debug(f"Filling pixel at ({nx}, {ny}) with {replacement_color}")
            filled_pixels += 1

            # Mark as visited
            visited.add((nx, ny))

            # Append neighboring pixels
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                new_x, new_y = nx + dx, ny + dy
                if (new_x, new_y) not in visited:
                    queue.append((new_x, new_y))

    if filled_pixels >= max_pixels:
        logging.warning("Maximum fill limit reached. Fill may be incomplete.")