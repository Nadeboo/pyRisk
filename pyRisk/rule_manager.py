# rule_manager.py

from utils import flood_fill

class Rule:
    def __init__(self, name, description, action):
        self.name = name
        self.description = description
        self.action = action
        self.is_active = False

    def toggle(self):
        self.is_active = not self.is_active

    def apply(self, app, x, y):
        if self.is_active:
            self.action(app, x, y)

class RuleManager:
    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        if not any(r.name == rule.name for r in self.rules):
            self.rules.append(rule)

    def get_rule(self, name):
        return next((rule for rule in self.rules if rule.name == name), None)

    def toggle_rule(self, name):
        rule = self.get_rule(name)
        if rule:
            rule.toggle()

    def is_rule_active(self, name):
        rule = self.get_rule(name)
        return rule.is_active if rule else False

    def apply_rule(self, name, app, x, y):
        rule = self.get_rule(name)
        if rule:
            rule.apply(app, x, y)

# Define the fortification rule
def setup_fortification_rule(rule_manager):
    def fortification_action(app, x, y):
        if (x, y) in app.tile_owners and (x, y) not in app.fortified_tiles:
            # Get the current color of the tile
            current_color = app.map_image.getpixel((x, y))
        
            # Calculate the darkened color
            darkened = tuple(int(c * 0.7) for c in current_color[:3]) + (current_color[3],)
        
            # Darken only the single clicked tile
            app.map_image.putpixel((x, y), darkened)
        
            # Mark only this tile as fortified
            app.fortified_tiles[(x, y)] = app.tile_owners.get((x, y))
        
            # Refresh the display
            if hasattr(app.current_screen, 'display_map_image'):
                app.current_screen.display_map_image()

    # Check if Fortification rule already exists
    if not rule_manager.get_rule("Fortification"):
        fortification_rule = Rule(
            "Fortification",
            "Allows players to fortify their tiles, making them harder to capture.",
            fortification_action
        )
        rule_manager.add_rule(fortification_rule)
