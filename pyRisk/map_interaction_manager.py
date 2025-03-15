import tkinter as tk
from tkinter import messagebox
from PIL import ImageDraw
from pyRisk.utils import flood_fill, check_territory_in_radius

class MapInteractionManager:
    def __init__(self, app):
        self.app = app

    def handle_map_coloring(self, x, y):
        """Handle map coloring at the given coordinates"""
        print(f"\n=== Map Coloring Debug ===")
        print(f"Click coordinates: ({x}, {y})")
        print(f"Current mode: {self.app.mode}")
        print(f"Selected player: {self.app.selected_player.name if self.app.selected_player else None}")
        
        # First check if we clicked on a city sprite
        sprite_result = self.app.sprite_manager.get_sprite_at_position(x, y)
        clicked_sprite = None
        sprite_pos = None
        if sprite_result is not None:
            sprite_pos, clicked_sprite = sprite_result
            print(f"Found sprite at {sprite_pos}: type={clicked_sprite.sprite_type}, owner={clicked_sprite.owner}")
            
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            print("Processing city sprite...")
            if self.app.mode == 'erase':
                print("Attempting to erase city coloring...")
                # Instead of removing the sprite, flood fill with transparency
                sprite_image = self.app.sprite_manager.sprites.get(clicked_sprite.sprite_type)
                if sprite_image:
                    # Use a fully transparent color for erasing
                    transparent_color = (0, 0, 0, 0)
                    if self.flood_fill_sprite(clicked_sprite, x, y, transparent_color):
                        print("Successfully erased city coloring")
                        self.app.current_screen.display_map_image()
                    else:
                        print("Failed to erase city coloring")
                    return
            elif self.app.selected_player:
                print(f"Attempting to color city for player: {self.app.selected_player.name}")
                # Try to flood fill the sprite
                if self.flood_fill_sprite(clicked_sprite, x, y, self.app.selected_player.color):
                    print("Successfully colored city")
                    clicked_sprite.owner = self.app.selected_player.name
                    self.app.current_screen.display_map_image()
                    return
                else:
                    print("Failed to color city")
            elif self.app.selected_player is None and self.app.mode != 'erase':
                print("No player selected for coloring")
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

        # Get current pixel color for territory painting
        target_color = self.app.map_image.getpixel((x, y))
        if len(target_color) == 4:
            target_color = target_color[:3]

        # Get resource paint mode from current screen
        resource_paint_mode = None
        if hasattr(self.app.current_screen, 'resource_paint_mode'):
            resource_paint_mode = self.app.current_screen.resource_paint_mode
            
        if resource_paint_mode:
            print(f"Resource paint mode active: {resource_paint_mode}")  # Debug
            replacement_color = self.app.current_screen.RESOURCE_COLORS[resource_paint_mode]
            print(f"Painting with color: {replacement_color}")  # Debug
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                print(f"Found region with center: {region['center']}")  # Debug
                center = region['center']
                self.app.resource_tiles[center] = {
                    'type': resource_paint_mode,
                    'owner': None
                }
                print(f"Added resource tile at {center}: {self.app.resource_tiles[center]}")  # Debug
                
                # Update ownership immediately for the new resource
                if self.app.roll_mode == 'tregonia':
                    self.update_resource_ownership()
                    
            self.app.current_screen.display_map_image()
            
            # Update any relevant displays
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()
            return

        if self.app.mode == 'color':
            if self.app.selected_player is None:
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

            replacement_color = tuple(int(c) for c in self.app.selected_player.color)

            if self.app.roll_mode == 'application':
                roll_info = self.app.player_rolls.get(self.app.selected_player.name, ("", 0, 0))
                if roll_info[2] <= 0:
                    messagebox.showwarning("No Tiles Left",
                                        f"{self.app.selected_player.name} has no tiles left to place.")
                    return
                self.update_player_tiles(self.app.selected_player.name, -1)

            # Check for previous owner of this region
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                # Remove previous ownership if it exists
                for pos in region['boundary']:
                    previous_owner = self.app.tile_owners.get(pos)
                    if previous_owner and previous_owner != self.app.selected_player.name:
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(previous_owner, 1)
                        del self.app.tile_owners[pos]
                    
                    # Set new ownership for the entire region
                    for pos in region['boundary']:
                        self.app.tile_owners[pos] = self.app.selected_player.name

        elif self.app.mode == 'erase':
            replacement_color = self.app.original_map_image.getpixel((x, y))
            if len(replacement_color) == 4:
                replacement_color = replacement_color[:3]
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                for pos in region['boundary']:
                    if pos in self.app.tile_owners:
                        player_name = self.app.tile_owners.pop(pos)
                        if self.app.roll_mode == 'application':
                            self.update_player_tiles(player_name, 1)

        # Always update resource ownership
        if self.app.roll_mode == 'tregonia':
            self.update_resource_ownership()

        self.app.current_screen.display_map_image()
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
            if hasattr(self.app.current_screen, 'update_player_buttons'):
                self.app.current_screen.update_player_buttons()

    def update_player_tiles(self, player_name, change):
        """Update the number of tiles a player has left"""
        if player_name in self.app.player_rolls:
            roll_value, total_tiles, remaining_tiles = self.app.player_rolls[player_name]
            new_remaining = remaining_tiles + change
            self.app.player_rolls[player_name] = (roll_value, total_tiles, new_remaining)

    def update_resource_ownership(self):
        """Update ownership of all resources based on surrounding territory"""
        if not self.app.map_image or self.app.roll_mode != 'tregonia':
            print("Resource ownership update skipped - no map or wrong mode")
            return
            
        print("\n=== Starting Resource Ownership Update ===")
        print(f"Total resources to check: {len(self.app.resource_tiles)}")
        print(f"Current tile owners count: {len(self.app.tile_owners)}")
        
        changes_made = False
        for pos, resource_info in self.app.resource_tiles.items():
            x, y = pos
            print(f"\nChecking resource at position {pos}")
            print(f"Current resource info: {resource_info}")
            
            # Check territory in radius around resource
            dominant_player, territory_count = check_territory_in_radius(
                self.app.map_image,
                self.app.tile_owners,
                x, y,
                radius=100
            )
            
            current_owner = resource_info.get('owner')
            print(f"Current owner: {current_owner}")
            print(f"Detected dominant player: {dominant_player}")
            
            if dominant_player != current_owner:
                print(f"Ownership change detected!")
                resource_info['owner'] = dominant_player
                changes_made = True
                if dominant_player:
                    print(f"Resource at {pos} claimed by {dominant_player} with {territory_count} surrounding tiles")
                else:
                    print(f"Resource at {pos} no longer controlled by any player")
        
        print("\n=== Resource Update Summary ===")
        print(f"Changes made: {changes_made}")
        
        if changes_made:
            print("Updating player resources and display...")
            self.app.update_player_resources()
            self.app.display_map_image()
            if hasattr(self.app.current_screen, 'update_player_list'):
                self.app.current_screen.update_player_list()

    def flood_fill_sprite(self, sprite_info, click_x, click_y, player_color):
        """Flood fill a sprite with a player's color"""
        print(f"\n=== Flood Fill Debug ===")
        print(f"Attempting to flood fill sprite at click position: ({click_x}, {click_y})")
        print(f"Player color to apply: {player_color}")
        
        # Get the original sprite image
        sprite_image = self.app.sprite_manager.sprites.get(sprite_info.sprite_type)
        if not sprite_image:
            print("Error: No sprite image found")
            return False
            
        # Convert sprite to RGBA if it isn't already
        sprite_image = sprite_image.convert('RGBA')
        
        # Get sprite position and calculate click position relative to sprite
        sprite_x, sprite_y = sprite_info.position
        sprite_width, sprite_height = sprite_image.size
        
        # Calculate sprite bounds
        sprite_left = sprite_x - sprite_width // 2
        sprite_top = sprite_y - sprite_height // 2
        
        # Calculate click position relative to sprite's top-left corner
        local_x = click_x - sprite_left
        local_y = click_y - sprite_top
        
        print(f"Sprite position: ({sprite_x}, {sprite_y})")
        print(f"Sprite bounds: left={sprite_left}, top={sprite_top}, width={sprite_width}, height={sprite_height}")
        print(f"Local click position: ({local_x}, {local_y})")
        
        # Check if click is within sprite bounds
        if not (0 <= local_x < sprite_width and 0 <= local_y < sprite_height):
            print("Error: Click outside sprite bounds")
            return False
        
        # Create working copy of sprite
        if 'colored_sprite' in sprite_info.extra_data:
            print("Using existing colored sprite as base")
            working_image = sprite_info.extra_data['colored_sprite'].copy()
        else:
            print("Creating new working image from original sprite")
            working_image = sprite_image.copy()
        
        # Get target color at click position
        target_color = working_image.getpixel((local_x, local_y))
        print(f"Target color at click position: {target_color}")
        
        # Skip if clicked on a fully transparent pixel
        if len(target_color) == 4 and target_color[3] == 0:
            print("Clicked on transparent pixel")
            return False
        
        # Determine fill color - always use RGBA
        if isinstance(player_color, tuple) and len(player_color) == 3:
            # Convert RGB to RGBA with full opacity
            fill_color = (*player_color, 255)
        elif isinstance(player_color, tuple) and len(player_color) == 4:
            # Already RGBA
            fill_color = player_color
        else:
            print(f"Invalid player color format: {player_color}")
            return False
            
        print(f"Using fill color: {fill_color}")
        
        # Function to check if a pixel should be filled (similar color)
        def is_similar_color(c1, c2, tolerance=30):
            # If either color is transparent, they're not similar
            if (len(c1) == 4 and c1[3] == 0) or (len(c2) == 4 and c2[3] == 0):
                return False
                
            # Compare RGB components only
            return all(abs(a - b) <= tolerance for a, b in zip(c1[:3], c2[:3]))
        
        # Flood fill using stack-based approach
        stack = [(local_x, local_y)]
        filled = set()
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in filled or not (0 <= x < sprite_width and 0 <= y < sprite_height):
                continue
            
            current_color = working_image.getpixel((x, y))
            
            # Skip fully transparent pixels
            if len(current_color) == 4 and current_color[3] == 0:
                continue
            
            # Only fill if color is similar to target
            if is_similar_color(current_color, target_color):
                # Set the pixel to the fill color
                working_image.putpixel((x, y), fill_color)
                filled.add((x, y))
                
                # Add 4-connected neighbors
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    new_x, new_y = x + dx, y + dy
                    if (new_x, new_y) not in filled:
                        stack.append((new_x, new_y))
        
        print(f"Filled {len(filled)} pixels")
        
        # Only save if we actually filled some pixels
        if filled:
            # Store the modified image in the sprite's extra_data
            sprite_info.extra_data['colored_sprite'] = working_image
            sprite_info.owner = self.app.selected_player.name if self.app.selected_player else None
            print("Saved colored sprite and updated owner")
            return True
        
        return False 