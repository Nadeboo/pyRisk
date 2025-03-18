import tkinter as tk
from tkinter import messagebox
from PIL import ImageDraw
from pyRisk.utils import flood_fill, check_territory_in_radius

class MapInteractionManager:
    def __init__(self, app):
        self.app = app
        
    def paint_territory(self, map_image, position, color, player_name, map_data, adjacency_map, update_callback=None):
        """Paint territory at the given position with the player's color.
        
        Args:
            map_image: The PIL Image to paint on
            position: (x, y) tuple of position to paint
            color: The color to use for painting (RGB tuple)
            player_name: The name of the player who owns this territory
            map_data: The map data dictionary
            adjacency_map: Map of territory adjacencies
            update_callback: Function to call to update the display
        """
        self.app.mode = 'color'
        self.app.selected_player = next((p for p in self.app.players if p.name == player_name), self.app.selected_player)
        x, y = position
        self.handle_map_coloring(x, y)
        
    def erase_territory(self, map_image, position, map_data, update_callback=None):
        """Erase territory at the given position.
        
        Args:
            map_image: The PIL Image to erase from
            position: (x, y) tuple of position to erase
            map_data: The map data dictionary
            update_callback: Function to call to update the display
        """
        self.app.mode = 'erase'
        x, y = position
        self.handle_map_coloring(x, y)

    def handle_map_coloring(self, x, y):
        """Handle map coloring at the given coordinates with optimized performance"""
        # Minimize debug prints to reduce overhead
        
        # First check if we clicked on a city sprite
        sprite_result = self.app.sprite_manager.get_sprite_at_position(x, y)
        clicked_sprite = None
        sprite_pos = None
        if sprite_result is not None:
            sprite_pos, clicked_sprite = sprite_result
            
        if clicked_sprite and clicked_sprite.sprite_type == 'city':
            if self.app.mode == 'erase':
                # Instead of removing the sprite, flood fill with transparency
                sprite_image = self.app.sprite_manager.sprites.get(clicked_sprite.sprite_type)
                if sprite_image:
                    # Use a fully transparent color for erasing
                    transparent_color = (0, 0, 0, 0)
                    if self.flood_fill_sprite(clicked_sprite, x, y, transparent_color):
                        self.app.current_screen.display_map_image()
                    return
            elif self.app.selected_player:
                # Try to flood fill the sprite
                if self.flood_fill_sprite(clicked_sprite, x, y, self.app.selected_player.color):
                    clicked_sprite.owner = self.app.selected_player.name
                    self.app.current_screen.display_map_image()
                    return
            elif self.app.selected_player is None and self.app.mode != 'erase':
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
            replacement_color = self.app.current_screen.RESOURCE_COLORS[resource_paint_mode]
            
            # Use try/except to handle any potential errors in flood fill
            try:
                region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
                if region:
                    center = region['center']
                    self.app.resource_tiles[center] = {
                        'type': resource_paint_mode,
                        'owner': None
                    }
                    
                    # Update ownership immediately for the new resource
                    if self.app.roll_mode == 'tregonia':
                        self.update_resource_ownership()
                        
                self.app.current_screen.display_map_image()
                
                # Update any relevant displays
                if hasattr(self.app.current_screen, 'update_player_list'):
                    self.app.current_screen.update_player_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to color resource: {str(e)}")
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

            # Use try/except to handle any potential errors in flood fill
            try:
                # Check for previous owner of this region
                region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
                if region:
                    # Process the region more efficiently
                    previous_owners = set()
                    boundary_points = set(region['boundary'])
                    
                    # First collect all previous owners
                    for pos in boundary_points:
                        previous_owner = self.app.tile_owners.get(pos)
                        if previous_owner and previous_owner != self.app.selected_player.name:
                            previous_owners.add(previous_owner)
                            if self.app.roll_mode == 'application':
                                self.update_player_tiles(previous_owner, 1)
                    
                    # Then update ownership in a batch operation
                    for pos in boundary_points:
                        self.app.tile_owners[pos] = self.app.selected_player.name
                    
                    # Always check resources after territory change
                    if self.app.roll_mode == 'tregonia':
                        self.update_resource_ownership()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to color territory: {str(e)}")

        elif self.app.mode == 'erase':
            try:
                replacement_color = self.app.original_map_image.getpixel((x, y))
                if len(replacement_color) == 4:
                    replacement_color = replacement_color[:3]
                
                region = flood_fill(self.app.map_image, x, y, target_color, replacement_color)
                if region:
                    boundary_points = set(region['boundary'])
                    for pos in boundary_points:
                        if pos in self.app.tile_owners:
                            player_name = self.app.tile_owners.pop(pos)
                            if self.app.roll_mode == 'application':
                                self.update_player_tiles(player_name, 1)
                    
                    # Always check resources after territory change
                    if self.app.roll_mode == 'tregonia':
                        self.update_resource_ownership()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to erase territory: {str(e)}")

        # Always update resource ownership and player resources after any map changes
        if self.app.roll_mode == 'tregonia':
            # Update resource ownership
            self.update_resource_ownership()
            
            # Update player resources directly to ensure they're current
            self.app.update_player_resources()

        # Update display
        self.app.current_screen.display_map_image()
        
        # Update player list if that screen function exists
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
        """Update ownership of all resources based on surrounding territory with optimized performance"""
        if not self.app.map_image or self.app.roll_mode != 'tregonia':
            return
        
        print("\n=== Updating Resource Ownership ===")
        changes_made = False
        
        # Process resources in batches to improve performance
        try:
            resource_items = list(self.app.resource_tiles.items())
            print(f"Checking ownership for {len(resource_items)} resources")
            
            for pos, resource_info in resource_items:
                x, y = pos
                
                # Check territory in radius around resource
                dominant_player, territory_count = check_territory_in_radius(
                    self.app.map_image,
                    self.app.tile_owners,
                    x, y,
                    radius=100
                )
                
                current_owner = resource_info.get('owner')
                
                print(f"Resource at {pos}: Current owner={current_owner}, Dominant player={dominant_player} with {territory_count} territories")
                
                if dominant_player != current_owner:
                    resource_info['owner'] = dominant_player
                    print(f"Ownership changed: {current_owner} -> {dominant_player}")
                    changes_made = True
                else:
                    print(f"No ownership change needed")
        except Exception as e:
            # Catch any errors to prevent freezing
            error_msg = f"Error updating resource ownership: {str(e)}"
            print(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)
            import traceback
            traceback.print_exc()
            return
        
        print(f"Changes made: {changes_made}")
        
        # Always update player resources regardless of ownership changes
        # This ensures resources are updated even if ownership didn't change
        try:
            print("Updating player resources")
            self.app.update_player_resources()
            
            if hasattr(self.app, 'current_screen') and hasattr(self.app.current_screen, 'display_map_image'):
                print("Updating display")
                self.app.current_screen.display_map_image()
                
            if hasattr(self.app.current_screen, 'update_player_list'):
                print("Updating player list")
                self.app.current_screen.update_player_list()
        except Exception as e:
            # Catch any errors in display update
            error_msg = f"Error updating display after resource changes: {str(e)}"
            print(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)
            import traceback
            traceback.print_exc()

    def flood_fill_sprite(self, sprite_info, click_x, click_y, player_color):
        """Flood fill a sprite with a player's color - optimized for performance"""
        try:
            # Get the original sprite image
            sprite_image = self.app.sprite_manager.sprites.get(sprite_info.sprite_type)
            if not sprite_image:
                return False
                
            # Convert sprite to RGBA if it isn't already
            sprite_image = sprite_image.convert('RGBA')
            
            # Get sprite position and calculate click position relative to sprite
            sprite_x, sprite_y = sprite_info.position
            sprite_width, sprite_height = sprite_image.size
            
            # Calculate sprite bounds
            sprite_left = sprite_x - sprite_width // 2
            sprite_top = sprite_y - sprite_height // 2
            
            # Calculate local coordinates within sprite
            local_x = click_x - sprite_left
            local_y = click_y - sprite_top
            
            # Check if click is within sprite bounds
            if not (0 <= local_x < sprite_width and 0 <= local_y < sprite_height):
                return False
            
            # Create working copy of sprite - reuse existing for efficiency
            if hasattr(sprite_info, 'extra_data') and sprite_info.extra_data and 'colored_sprite' in sprite_info.extra_data:
                working_image = sprite_info.extra_data['colored_sprite'].copy()
            else:
                working_image = sprite_image.copy()
                if not hasattr(sprite_info, 'extra_data') or sprite_info.extra_data is None:
                    sprite_info.extra_data = {}
            
            # Get target color at click position
            target_color = working_image.getpixel((local_x, local_y))
            
            # Skip if clicked on a fully transparent pixel
            if len(target_color) == 4 and target_color[3] == 0:
                return False
            
            # Determine fill color - always use RGBA
            if isinstance(player_color, tuple) and len(player_color) == 3:
                # Convert RGB to RGBA with full opacity
                fill_color = (*player_color, 255)
            elif isinstance(player_color, tuple) and len(player_color) == 4:
                # Already RGBA
                fill_color = player_color
            else:
                return False
            
            # Faster color comparison function
            def is_similar_color(c1, c2, tolerance_squared=900):  # 30^2 = 900
                # If either color is transparent, they're not similar
                if (len(c1) == 4 and c1[3] == 0) or (len(c2) == 4 and c2[3] == 0):
                    return False
                
                # Use squared distance for faster comparison (avoids sqrt)
                return sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])) <= tolerance_squared
            
            # Use an efficient deque for better performance with stack operations
            from collections import deque
            stack = deque([(local_x, local_y)])
            filled = set()
            
            # Use a safety limit to prevent infinite loops or excessive processing
            max_iterations = min(sprite_width * sprite_height, 50000)
            iterations = 0
            
            # Pre-compute directions for better performance
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            while stack and iterations < max_iterations:
                iterations += 1
                x, y = stack.pop()
                
                # Skip if already processed or out of bounds
                if (x, y) in filled or not (0 <= x < sprite_width and 0 <= y < sprite_height):
                    continue
                
                # Get current pixel color safely
                try:
                    current_color = working_image.getpixel((x, y))
                except IndexError:
                    continue
                
                # Skip fully transparent pixels
                if len(current_color) == 4 and current_color[3] == 0:
                    continue
                
                # Only fill if color is similar to target
                if is_similar_color(current_color, target_color):
                    # Set the pixel to the fill color
                    working_image.putpixel((x, y), fill_color)
                    filled.add((x, y))
                    
                    # Add 4-connected neighbors efficiently
                    for dx, dy in directions:
                        new_x, new_y = x + dx, y + dy
                        if (new_x, new_y) not in filled:
                            stack.append((new_x, new_y))
            
            # Only save if we actually filled some pixels
            if filled:
                # Store the modified image
                sprite_info.extra_data['colored_sprite'] = working_image
                sprite_info.owner = self.app.selected_player.name if self.app.selected_player else None
                return True
            
            return False
            
        except Exception as e:
            # Catch any errors to prevent application freeze
            messagebox.showerror("Error", f"Failed to fill sprite: {str(e)}")
            return False
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