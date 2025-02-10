# game_screen_overlay.py

from PIL import Image, ImageDraw, ImageFont
import os

class GameScreenOverlay:
    def __init__(self):
        self.INFO_PANEL_WIDTH = 300
        self.CITIES_PANEL_WIDTH = 300
        self.SECTION_PADDING = 10
        self.FONT_SIZE = 14
        self.SMALL_FONT_SIZE = 12
        self.TEXT_COLOR = (0, 0, 0)  # Black
        self.HEADER_COLOR = (0, 0, 0)  # Black
        self.SECTION_BG = (245, 245, 245, 255)  # Light gray for section backgrounds
        
        # Try to load Arial, fall back to default if not available
        try:
            self.font = ImageFont.truetype("arial.ttf", self.FONT_SIZE)
            self.small_font = ImageFont.truetype("arial.ttf", self.SMALL_FONT_SIZE)
            self.font_bold = ImageFont.truetype("arialbd.ttf", self.FONT_SIZE)
        except IOError:
            self.font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()

    def draw_overlay(self, image, players, current_turn, cities=None):
        """Create extended image with info panels"""
        # Create new wider image with white background
        new_width = image.width + self.INFO_PANEL_WIDTH + self.CITIES_PANEL_WIDTH
        new_image = Image.new('RGBA', (new_width, image.height), (255, 255, 255, 255))
        
        # Paste original map image on the left
        new_image.paste(image, (0, 0))
        
        # Create drawing context
        draw = ImageDraw.Draw(new_image)
        
        # Draw player info panel
        panel_start = image.width
        current_y = 10
        current_y = self._draw_turn_info(draw, panel_start, current_y, current_turn)
        
        if players:
            current_y = self._draw_players_section(draw, panel_start, current_y, players)
            current_y = self._draw_research_section(draw, panel_start, current_y, players)
            current_y = self._draw_alliances_section(draw, panel_start, current_y, players)
        else:
            draw.text(
                (panel_start + 10, current_y),
                "No Players Added",
                font=self.font,
                fill=self.TEXT_COLOR
            )

        # Draw cities panel
        cities_panel_start = image.width + self.INFO_PANEL_WIDTH
        current_y = 10
        if cities:
            current_y = self._draw_cities_section(draw, cities_panel_start, current_y, cities)
        else:
            y = self._draw_section_background(draw, cities_panel_start, current_y, 40)
            draw.text(
                (cities_panel_start + 10, y - self.SECTION_PADDING),
                "No Cities Added",
                font=self.font,
                fill=self.TEXT_COLOR
            )
        
        return new_image

    def _draw_cities_section(self, draw, x, y, cities):
        """Draw the cities panel showing all cities and their improvements"""
        # Draw section title
        title_height = 40
        y = self._draw_section_background(draw, x, y, title_height)
        draw.text(
            (x + 10, y - self.SECTION_PADDING),
            "Cities",
            font=self.font_bold,
            fill=self.TEXT_COLOR
        )
        y += title_height

        if not cities:
            y = self._draw_section_background(draw, x, y, 30)
            draw.text(
                (x + 10, y - self.SECTION_PADDING),
                "No cities built",
                font=self.font,
                fill=self.TEXT_COLOR
            )
            return y + 30

        # Draw each city
        for city in cities:
            # Calculate height needed for this city
            num_improvement_rows = (len(city.slots) + 2) // 3  # 3 improvements per row
            city_height = 30 + (num_improvement_rows * 20)
            
            y = self._draw_section_background(draw, x, y, city_height)
            
            # Draw city name and owner
            draw.text(
                (x + 10, y - self.SECTION_PADDING),
                f"{city.name} ({city.owner})",
                font=self.font_bold,
                fill=self.TEXT_COLOR
            )
            y += 20

            # Draw improvements in a grid-like format
            improvements = sorted(city.slots)
            for i in range(0, len(improvements), 3):
                row_improvements = improvements[i:i+3]
                row_text = "  ".join(row_improvements)
                draw.text(
                    (x + 20, y - self.SECTION_PADDING),
                    row_text,
                    font=self.small_font,
                    fill=self.TEXT_COLOR
                )
                y += 20

            y += 10  # Add some padding between cities

        return y

    def _draw_section_background(self, draw, x, y, height):
        """Draw a section background"""
        width = self.INFO_PANEL_WIDTH if x < (self.INFO_PANEL_WIDTH * 2) else self.CITIES_PANEL_WIDTH
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            fill=self.SECTION_BG,
            outline=(200, 200, 200, 255)  # Light gray border
        )
        return y + self.SECTION_PADDING

    def _draw_turn_info(self, draw, x, y, current_turn):
        """Draw turn information section"""
        height = 40
        y = self._draw_section_background(draw, x, y, height)
        draw.text(
            (x + 10, y - self.SECTION_PADDING),
            f"Turn: {current_turn}",
            font=self.font_bold,
            fill=self.TEXT_COLOR
        )
        return y + height

    def _draw_players_section(self, draw, x, y, players):
        """Draw players section with resources"""
        if not players:
            return y
            
        height = len(players) * 60 + 30
        y = self._draw_section_background(draw, x, y, height)
        
        draw.text(
            (x + 10, y - self.SECTION_PADDING),
            "Players",
            font=self.font_bold,
            fill=self.TEXT_COLOR
        )
        y += 20

        for player in players:
            # Color indicator
            draw.rectangle(
                [(x + 10, y), (x + 25, y + 15)],
                fill=player.color,
                outline=(0, 0, 0, 255)
            )
            
            # Player name
            draw.text(
                (x + 30, y),
                player.name,
                font=self.font,
                fill=self.TEXT_COLOR
            )
            
            # Resources
            resources = [
                f"G:{player.gold}+{player.gold_per_turn}",
                f"R:{player.research}+{player.research_per_turn}",
                f"M:{player.mana}+{player.mana_per_turn}",
                f"I:{player.influence}+{player.influence_per_turn}"
            ]
            
            for i, resource in enumerate(resources):
                draw.text(
                    (x + 30, y + 20 + i * 15),
                    resource,
                    font=self.small_font,
                    fill=self.TEXT_COLOR
                )
            
            y += 50
            
        return y + 10

    def _draw_alliances_section(self, draw, x, y, players):
        """Draw alliances section"""
        if not players:
            return y
            
        # Collect alliances and NAPs
        alliances = []
        naps = []
        for player in players:
            for ally in player.allies:
                if player.name < ally.name:
                    alliances.append(f"{player.name}↔{ally.name}")
            for nap in player.naps:
                if player.name < nap.name:
                    naps.append(f"{player.name}↔{nap.name}")

        # Calculate height
        height = 30 + (len(alliances) * 20) + (len(naps) * 20) + (40 if naps else 0)
        
        y = self._draw_section_background(draw, x, y, height)
        draw.text(
            (x + 10, y - self.SECTION_PADDING),
            "Alliances",
            font=self.font_bold,
            fill=self.TEXT_COLOR
        )
        y += 20

        if alliances:
            for alliance in alliances:
                draw.text(
                    (x + 30, y),
                    alliance,
                    font=self.small_font,
                    fill=self.TEXT_COLOR
                )
                y += 20
        else:
            draw.text(
                (x + 30, y),
                "No alliances",
                font=self.small_font,
                fill=self.TEXT_COLOR
            )
            y += 20

        if naps:
            y += 10
            draw.text(
                (x + 10, y),
                "NAPs:",
                font=self.font_bold,
                fill=self.TEXT_COLOR
            )
            y += 20
            for nap in naps:
                draw.text(
                    (x + 30, y),
                    nap,
                    font=self.small_font,
                    fill=self.TEXT_COLOR
                )
                y += 20

        return y

    def _draw_research_section(self, draw, x, y, players):
        """Draw research section"""
        if not players:
            return y
            
        # Calculate height based on content
        max_research_lines = max(
            (len(player.get_completed_research()) for player in players),
            default=0
        )
        height = (max_research_lines * 20) + (len(players) * 30) + 30
        
        y = self._draw_section_background(draw, x, y, height)
        draw.text(
            (x + 10, y - self.SECTION_PADDING),
            "Research",
            font=self.font_bold,
            fill=self.TEXT_COLOR
        )
        y += 20

        for player in players:
            # Player identifier
            draw.rectangle(
                [(x + 10, y), (x + 25, y + 15)],
                fill=player.color,
                outline=(0, 0, 0, 255)
            )
            draw.text(
                (x + 30, y),
                player.name,
                font=self.font,
                fill=self.TEXT_COLOR
            )
            y += 25

            # Research lists
            completed = player.get_completed_research()
            steel_research = sorted(
                [r for r in completed if r.path == 'steel'],
                key=lambda x: (x.tier.value, x.display_name)
            )
            magic_research = sorted(
                [r for r in completed if r.path == 'magic'],
                key=lambda x: (x.tier.value, x.display_name)
            )

            if steel_research:
                text = "Steel: " + ", ".join(r.display_name for r in steel_research)
                wrapped_text = self._wrap_text(text, self.small_font, self.INFO_PANEL_WIDTH - 40)
                for line in wrapped_text:
                    draw.text((x + 30, y), line, font=self.small_font, fill=self.TEXT_COLOR)
                    y += 15

            if magic_research:
                text = "Magic: " + ", ".join(r.display_name for r in magic_research)
                wrapped_text = self._wrap_text(text, self.small_font, self.INFO_PANEL_WIDTH - 40)
                for line in wrapped_text:
                    draw.text((x + 30, y), line, font=self.small_font, fill=self.TEXT_COLOR)
                    y += 15

            if not (steel_research or magic_research):
                draw.text(
                    (x + 30, y),
                    "No research",
                    font=self.small_font,
                    fill=self.TEXT_COLOR
                )
                y += 15

            y += 10
        
        return y

    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width"""
        if not text:
            return []
            
        words = text.split()
        if not words:
            return []
            
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = font.getlength(word + " ")
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [""]