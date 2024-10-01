# utils.py

from PIL import Image

def flood_fill(image, x, y, target_color, replacement_color):
    pixels = image.load()
    width, height = image.size
    stack = [(x, y)]
    while stack:
        nx, ny = stack.pop()
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        current_color = pixels[nx, ny]
        if current_color == target_color:
            pixels[nx, ny] = replacement_color
            stack.extend([(nx + 1, ny), (nx - 1, ny), (nx, ny + 1), (nx, ny - 1)])
