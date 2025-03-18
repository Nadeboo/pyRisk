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
    name: Optional[str] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}
            
    @property
    def slots(self):
        """Get city slots for compatibility with overlay"""
        return self.extra_data.get('slots', [])

    @property
    def improvements(self):
        """Get city improvements for compatibility with overlay"""
        return self.extra_data.get('improvements', [])

class SpriteManager:
    def __init__(self, app, sprite_folder="sprites"):
        self.app = app
        self.sprite_folder = sprite_folder
        self.sprites: Dict[str, Image.Image] = {}
        self.load_sprites()

    def load_sprites(self):
        """Load all sprites from the sprites folder"""
        # Print current working directory and full sprite folder path for debugging
        import os
        current_dir = os.getcwd()
        full_path = os.path.abspath(self.sprite_folder)
        print(f"Current working directory: {current_dir}")
        print(f"Loading sprites from: {full_path}")
        
        # Try alternative sprite folder locations if specified folder doesn't exist
        if not os.path.exists(self.sprite_folder):
            print(f"Sprite folder {self.sprite_folder} doesn't exist")
            
            # Try alternate locations
            alternate_folders = [
                "sprites",                 # Root sprites folder
                "pyRisk/sprites",          # Package sprites folder
                "../sprites",              # Parent directory sprites folder
                "../../sprites",           # Grandparent directory sprites folder
                "/mnt/c/Users/glugg/source/repos/Nadeboo/pyRisk/pyRisk/sprites",  # Full path to sprites
                os.path.join(current_dir, "sprites"),  # Sprites in current dir
                os.path.join(current_dir, "pyRisk/sprites")  # Sprites in pyRisk subfolder
            ]
            
            print(f"Searching for sprite folder in alternate locations:")
            for alt_folder in alternate_folders:
                print(f"  Checking {alt_folder}...")
                if os.path.exists(alt_folder):
                    print(f"  Found sprite folder: {alt_folder}")
                    self.sprite_folder = alt_folder
                    break
            else:
                # If no alternate folders found, create the specified one
                try:
                    os.makedirs(self.sprite_folder)
                    print(f"Created sprites folder: {self.sprite_folder}")
                except Exception as e:
                    print(f"Failed to create sprites folder: {e}")
                return

        print(f"Loading sprites from: {self.sprite_folder}")
        try:
            sprite_files = os.listdir(self.sprite_folder)
            print(f"Found {len(sprite_files)} files in sprite folder")
            
            if not sprite_files:
                print(f"WARNING: Sprite folder {self.sprite_folder} is empty!")
                # Try to debug why this is happening
                dirs_to_check = [
                    current_dir,
                    os.path.join(current_dir, "pyRisk"),
                    os.path.join(current_dir, "sprites"),
                    "/mnt/c/Users/glugg/source/repos/Nadeboo/pyRisk",
                    "/mnt/c/Users/glugg/source/repos/Nadeboo/pyRisk/pyRisk",
                    "/mnt/c/Users/glugg/source/repos/Nadeboo/pyRisk/sprites"
                ]
                print("Listing directories to help debug sprite loading issues:")
                for d in dirs_to_check:
                    if os.path.exists(d):
                        print(f"  Contents of {d}:")
                        try:
                            for item in os.listdir(d)[:10]:  # Show first 10 items
                                print(f"    {item}")
                            if len(os.listdir(d)) > 10:
                                print(f"    ... and {len(os.listdir(d)) - 10} more items")
                        except Exception as e:
                            print(f"    Error listing directory: {e}")
                    else:
                        print(f"  Directory {d} does not exist")
        except Exception as e:
            print(f"Error listing sprite folder {self.sprite_folder}: {e}")
            return

        for filename in sprite_files:
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                sprite_name = os.path.splitext(filename)[0]
                try:
                    sprite_path = os.path.join(self.sprite_folder, filename)
                    sprite_image = Image.open(sprite_path).convert('RGBA')
                    self.sprites[sprite_name] = sprite_image
                    print(f"Loaded sprite: {sprite_name}")
                except Exception as e:
                    print(f"Error loading sprite {filename}: {e}")
                    
        print(f"Successfully loaded {len(self.sprites)} sprites")

    def add_sprite(self, sprite_type: str, position: Tuple[int, int], owner: Optional[str] = None, 
                  extra_data: Dict = None) -> bool:
        """Add a sprite to the map"""
        if sprite_type not in self.sprites:
            print(f"Sprite type {sprite_type} not found")
            return False

        # Add the sprite
        self.app.placed_sprites[position] = SpriteInfo(
            sprite_type=sprite_type,
            position=position,
            owner=owner or (self.app.selected_player.name if self.app.selected_player else None),
            extra_data=extra_data
        )
        
        # Update the display if we have a current screen
        if hasattr(self.app, 'current_screen'):
            self.app.current_screen.display_map_image()
        return True

    def remove_sprite(self, position: Tuple[int, int]) -> bool:
        """Remove a sprite from the given position"""
        result = self.app.placed_sprites.pop(position, None) is not None
        # Update the display if we have a current screen
        if result and hasattr(self.app, 'current_screen'):
            self.app.current_screen.display_map_image()
        return result

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

    def get_sprite_at_position(self, click_x: int, click_y: int, radius: int = 10) -> Optional[Tuple[Tuple[int, int], SpriteInfo]]:
        """Find a sprite near the clicked position within a given radius"""
        for pos, sprite_info in self.placed_sprites.items():
            sprite_x, sprite_y = pos
            if abs(sprite_x - click_x) <= radius and abs(sprite_y - click_y) <= radius:
                return pos, sprite_info
        return None

    def get_visible_sprite_bounds(self, sprite_position: Tuple[int, int], sprite_image: Image.Image) -> Tuple[int, int, int, int]:
        """Calculate the visible bounds of a sprite"""
        sprite_x, sprite_y = sprite_position
        sprite_width, sprite_height = sprite_image.size
        return (
            sprite_x - sprite_width // 2,
            sprite_y - sprite_height // 2,
            sprite_x + sprite_width // 2,
            sprite_y + sprite_height // 2
        )

    def recolor_sprite_from_data(self, sprite_image: Image.Image, color_data: Dict[Tuple[int, int], Tuple[int, int, int]]) -> Image.Image:
        """Recolor a sprite based on color data"""
        recolored = sprite_image.copy()
        pixels = recolored.load()
        for pos, color in color_data.items():
            pixels[pos[0], pos[1]] = color + (pixels[pos[0], pos[1]][3],)  # Preserve alpha
        return recolored
        
    def available_sprites(self) -> list:
        """Return a list of all available sprite types"""
        sprites = list(self.sprites.keys())
        print(f"Available sprites: {sprites}")
        return sprites
        
    def place_sprite(self, x: int, y: int, sprite_type: str, owner: str = None) -> bool:
        """Place a sprite on the map at the specified position
        
        Args:
            x: X-coordinate on the map
            y: Y-coordinate on the map
            sprite_type: Type of sprite to place
            owner: Name of the player who owns this sprite
            
        Returns:
            True if the sprite was placed successfully, False otherwise
        """
        # Check if the sprite type exists
        if sprite_type not in self.sprites:
            print(f"Error: Sprite type '{sprite_type}' not found")
            return False
            
        # Create the position tuple
        position = (x, y)
        
        # Add the sprite to the placed_sprites dictionary
        self.app.placed_sprites[position] = SpriteInfo(
            sprite_type=sprite_type,
            position=position,
            owner=owner
        )
        
        # Update the display
        if hasattr(self.app, 'current_screen') and hasattr(self.app.current_screen, 'display_map_image'):
            self.app.current_screen.display_map_image()
            
        return True