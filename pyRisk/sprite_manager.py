# sprite_manager.py

from PIL import Image
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import os

@dataclass
class SpriteInfo:
    """Stores information about a placed sprite"""
    sprite_type: str
    position: Tuple[int, int]
    owner: Optional[str] = None
    extra_data: Dict = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

class SpriteManager:
    def __init__(self, app, sprite_folder="sprites"):
        self.app = app
        self.sprite_folder = sprite_folder
        self.sprites: Dict[str, Image.Image] = {}
        self.load_sprites()

    def load_sprites(self):
        """Load all sprites from the sprites folder"""
        if not os.path.exists(self.sprite_folder):
            os.makedirs(self.sprite_folder)
            print(f"Created sprites folder: {self.sprite_folder}")
            return

        for filename in os.listdir(self.sprite_folder):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                sprite_name = os.path.splitext(filename)[0]
                try:
                    sprite_path = os.path.join(self.sprite_folder, filename)
                    sprite_image = Image.open(sprite_path).convert('RGBA')
                    self.sprites[sprite_name] = sprite_image
                    print(f"Loaded sprite: {sprite_name}")
                except Exception as e:
                    print(f"Error loading sprite {filename}: {e}")

    def add_sprite(self, sprite_type: str, position: Tuple[int, int], owner: Optional[str] = None, 
                  extra_data: Dict = None) -> bool:
        """Add a sprite to the map"""
        if sprite_type not in self.sprites:
            print(f"Sprite type {sprite_type} not found")
            return False

        self.app.placed_sprites[position] = SpriteInfo(
            sprite_type=sprite_type,
            position=position,
            owner=owner,
            extra_data=extra_data
        )
        return True

    def remove_sprite(self, position: Tuple[int, int]) -> bool:
        """Remove a sprite from the given position"""
        return self.app.placed_sprites.pop(position, None) is not None

    def get_sprite(self, position: Tuple[int, int]) -> Optional[SpriteInfo]:
        """Get sprite information at the given position"""
        return self.app.placed_sprites.get(position)

    def get_sprites_in_area(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> Dict[Tuple[int, int], SpriteInfo]:
        """Get all sprites within a rectangular area"""
        x1, y1 = top_left
        x2, y2 = bottom_right
        return {
            pos: info for pos, info in self.app.placed_sprites.items()
            if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2
        }

    def clear_sprites(self):
        """Remove all placed sprites"""
        self.app.placed_sprites.clear()

    @property
    def placed_sprites(self):
        """Access the app's placed sprites"""
        return self.app.placed_sprites