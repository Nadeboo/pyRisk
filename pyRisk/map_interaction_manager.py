import tkinter as tk
from tkinter import messagebox
from PIL import ImageDraw
from pyRisk.utils import flood_fill, check_territory_in_radius

class MapInteractionManager:
    def __init__(self, app):
        self.app = app

    def handle_map_coloring(self, x, y):
        """Handle map coloring using region-based approach"""
        # Save current state before modification
        current_sprites_data = {}
        for pos, sprite_info in self.app.sprite_manager.placed_sprites.items():
            sprite_state = {
                'position': pos,
                'type': sprite_info.sprite_type,
                'owner': sprite_info.owner,
                'extra_data': sprite_info.extra_data.copy() if sprite_info.extra_data else None,
                'name': sprite_info.name
            }
            current_sprites_data[pos] = sprite_state

        self.app.map_history.append({
            'image': self.app.map_image.copy(),
            'tile_owners': self.app.tile_owners.copy(),
            'resource_tiles': self.app.resource_tiles.copy() if hasattr(self.app, 'resource_tiles') else {},
            'sprites_data': current_sprites_data
        })
        if len(self.app.map_history) > self.app.max_history:
            self.app.map_history.pop(0)

        # First check if we clicked on a city sprite
        clicked_sprite, sprite_pos = self.app.sprite_manager.get_sprite_at_position(x, y)
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            if self.app.mode == 'erase':
                # Instead of removing the sprite, flood fill with transparency
                sprite_image = self.app.sprite_manager.sprites.get(clicked_sprite.sprite_type)
                if sprite_image:
                    # Use a fully transparent color for erasing
                    transparent_color = (0, 0, 0, 0)
                    if self.flood_fill_sprite(clicked_sprite, x, y, transparent_color):
                        self.app.display_map_image()
                    return
            elif self.app.selected_player:
                # Try to flood fill the sprite
                if self.flood_fill_sprite(clicked_sprite, x, y, self.app.selected_player.color):
                    clicked_sprite.owner = self.app.selected_player.name
                    self.app.display_map_image()
                    return
            elif self.app.selected_player is None and self.app.mode != 'erase':
                messagebox.showwarning("No Player Selected", "Please select a player before coloring.")
                return

        # Get current pixel color for territory painting
        target_color = self.app.map_image.getpixel((x, y))
        if len(target_color) == 4:
            target_color = target_color[:3]

        if self.app.sidebar_manager.resource_paint_mode:
            print(f"Resource paint mode active: {self.app.sidebar_manager.resource_paint_mode}")  # Debug
            replacement_color = self.app.sidebar_manager.RESOURCE_COLORS[self.app.sidebar_manager.resource_paint_mode]
            print(f"Painting with color: {replacement_color}")  # Debug
            
            region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
            if region:
                print(f"Found region with center: {region['center']}")  # Debug
                center = region['center']
                self.app.resource_tiles[center] = {
                    'type': self.app.sidebar_manager.resource_paint_mode,
                    'owner': None
                }
                print(f"Added resource tile at {center}: {self.app.resource_tiles[center]}")  # Debug
                
                # Update ownership immediately for the new resource
                if self.app.roll_mode == 'tregonia':
                    self.update_resource_ownership()
                    
            self.app.display_map_image()
            
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

        self.app.display_map_image()
        if hasattr(self.app.current_screen, 'update_player_list'):
            self.app.current_screen.update_player_list()
            self.app.sidebar_manager.update_player_buttons()

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
        sprite_image = self.app.sprite_manager.sprites.get(sprite_info.sprite_type)
        if not sprite_image:
            return None
            
        # Create a copy of the sprite to modify
        sprite_to_modify = sprite_image.copy()
        
        # Get sprite position and calculate click position relative to sprite
        sprite_x, sprite_y = sprite_info.position
        local_x = click_x - (sprite_x - sprite_image.width // 2)
        local_y = click_y - (sprite_y - sprite_image.height // 2)
        
        # Check if click is within sprite bounds
        if (0 <= local_x < sprite_image.width and 
            0 <= local_y < sprite_image.height):
            
            # Get target color at click position
            target_pixel = sprite_to_modify.getpixel((local_x, local_y))
            if len(target_pixel) == 4 and target_pixel[3] == 0:  # Skip transparent pixels
                return None
                
            # Determine fill color based on whether we're erasing or coloring
            if len(player_color) == 4 and player_color[3] == 0:
                # We're erasing - use full transparency
                fill_color = (0, 0, 0, 0)
            else:
                # We're coloring - use semi-transparent color
                fill_color = (*player_color, 128)
            
            # If sprite doesn't have color data initialized, create it
            if 'color_data' not in sprite_info.extra_data:
                sprite_info.extra_data['color_data'] = {}
            
            # Store the flood fill region in the sprite's color data
            region = flood_fill(sprite_to_modify, local_x, local_y, target_pixel, fill_color)
            if region:
                # Store color data for each affected pixel
                for px, py in region['boundary']:
                    key = f"{px},{py}"
                    if fill_color[3] == 0:  # If erasing
                        sprite_info.extra_data['color_data'].pop(key, None)  # Remove the color data
                    else:
                        sprite_info.extra_data['color_data'][key] = fill_color
                    
                return True
        
        return None 