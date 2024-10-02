# utils/utils.py

from PIL import Image
from typing import Tuple


def flood_fill(image: Image.Image, x: int, y: int, target_color: Tuple[int, int, int, int], replacement_color: Tuple[int, int, int, int]) -> None:
    """
    Perform a flood fill on the given image starting from (x, y).

    Args:
        image (Image.Image): The image to be modified.
        x (int): X-coordinate of the starting pixel.
        y (int): Y-coordinate of the starting pixel.
        target_color (tuple): The color to be replaced (RGBA).
        replacement_color (tuple): The new color (RGBA).
    """
    if target_color == replacement_color:
        return

    pixels = image.load()
    width, height = image.size
    queue = [(x, y)]

    while queue:
        nx, ny = queue.pop(0)
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        current_color = pixels[nx, ny]
        if current_color != target_color:
            continue
        pixels[nx, ny] = replacement_color
        queue.extend([(nx + 1, ny), (nx - 1, ny), (nx, ny + 1), (nx, ny - 1)])
