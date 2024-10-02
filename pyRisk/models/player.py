# models/player.py

from typing import List, Optional


class Player:
    def __init__(self, name: str, color: tuple, faction: Optional[str] = None):
        """
        Initialize a Player instance.

        Args:
            name (str): Unique name of the player.
            color (tuple): RGB color tuple for the player.
            faction (str, optional): Optional faction name.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Invalid player name")
        if not isinstance(color, tuple) or len(color) != 3:
            raise ValueError("Invalid color format")
        self.name = name.strip()
        self.color = color
        self.faction = faction.strip() if faction else None
        self.allies: List['Player'] = []
        self.naps: List['Player'] = []

    def add_ally(self, player: 'Player') -> None:
        """
        Add a player to the allies list.

        Args:
            player (Player): The player to ally with.
        """
        if player not in self.allies:
            self.allies.append(player)

    def add_nap(self, player: 'Player') -> None:
        """
        Add a player to the Non-Aggression Pacts (NAPs) list.

        Args:
            player (Player): The player to form a NAP with.
        """
        if player not in self.naps:
            self.naps.append(player)
