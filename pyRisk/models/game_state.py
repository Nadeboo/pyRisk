# models/game_state.py

class GameState:
    def __init__(self, turn_number: int, map_image_path: str):
        """
        Initialize a GameState instance.

        Args:
            turn_number (int): The current turn number.
            map_image_path (str): Path to the map image for this turn.
        """
        self.turn_number = turn_number
        self.map_image_path = map_image_path
