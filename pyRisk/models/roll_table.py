# models/roll_table.py

import random
from typing import Dict, Any
import tkinter as tk
from tkinter import messagebox


class RollTable:
    def __init__(self):
        """
        Initialize a RollTable instance with default configurations.
        """
        # Default values for numbers 1-9
        self.number_values: Dict[str, int] = {str(i): 1 for i in range(1, 10)}  # Default to 1 tile per number
        
        # Configurations for repeats and palindromes
        self.repeats_config: Dict[str, Dict[str, Any]] = {
            '2': {'type': 'add', 'value': 0},  # Doubles
            '3': {'type': 'add', 'value': 0},  # Triples
            # Add more repeats as needed
        }
        self.palindromes_config: Dict[str, Dict[str, Any]] = {
            '2': {'type': 'add', 'value': 0},  # Palindromes of length 2
            '3': {'type': 'add', 'value': 0},  # Palindromes of length 3
            # Add more palindrome lengths as needed
        }

    def calculate_tiles(self, roll_value: int) -> int:
        """
        Calculate the number of tiles based on the roll value.

        Args:
            roll_value (int): The rolled number.

        Returns:
            int: Number of tiles allocated.
        """
        roll_str = str(roll_value)
        tiles = 0

        # Check for repeats at the end first
        repeat_length, repeat_value = self._get_longest_repeat(roll_str)
        if repeat_length >= 2:
            repeat_config = self.repeats_config.get(str(repeat_length))
            if repeat_config:
                base_tiles = self.number_values.get(repeat_value, 1) * repeat_length
                tiles += self._apply_config(base_tiles, repeat_config)
            return tiles  # Return early if a repeat was found

        # Check for palindromes at the end
        palindrome_length = self._get_end_palindrome_length(roll_str)
        if palindrome_length >= 2:
            palindrome_config = self.palindromes_config.get(str(palindrome_length))
            if palindrome_config:
                base_tiles = self.number_values.get(roll_str[-1], 1) * palindrome_length
                tiles += self._apply_config(base_tiles, palindrome_config)
            return tiles  # Return early if a palindrome was found

        # If no repeats or palindromes, just count the last digit
        tiles += self.number_values.get(roll_str[-1], 1)  # Default to 1 if the digit is not in number_values

        return tiles

    def _get_longest_repeat(self, roll_str: str) -> (int, str):
        """
        Get the longest sequence of repeating digits at the end of the roll string.

        Args:
            roll_str (str): The rolled number as a string.

        Returns:
            tuple: (repeat_length, repeat_value)
        """
        if not roll_str:
            return 0, ''

        # Start from the end of the string
        repeat_value = roll_str[-1]
        repeat_length = 1

        # Count backwards from the end
        for i in range(len(roll_str) - 2, -1, -1):
            if roll_str[i] == repeat_value:
                repeat_length += 1
            else:
                break  # Stop as soon as a non-repeating digit is found

        # If the repeat length is 1, no repeat was found
        if repeat_length == 1:
            return 0, ''
        else:
            return repeat_length, repeat_value

    def _get_end_palindrome_length(self, roll_str: str) -> int:
        """
        Determine the length of the palindrome at the end of the roll string.

        Args:
            roll_str (str): The rolled number as a string.

        Returns:
            int: Length of the palindrome, or 0 if none found.
        """
        for i in range(len(roll_str), 1, -1):
            if self._is_palindrome(roll_str[-i:]):
                return i
        return 0

    def _is_palindrome(self, s: str) -> bool:
        """
        Check if a string is a palindrome.

        Args:
            s (str): The string to check.

        Returns:
            bool: True if palindrome, False otherwise.
        """
        return s == s[::-1]

    def _apply_config(self, base_tiles: int, config: Dict[str, Any]) -> int:
        """
        Apply the configuration to the base tile count.

        Args:
            base_tiles (int): The base number of tiles.
            config (dict): Configuration dictionary with 'type' and 'value'.

        Returns:
            int: The adjusted number of tiles.
        """
        config_type = config.get('type', 'add')
        value = config.get('value', 0)
        if config_type == 'add':
            return base_tiles + value
        elif config_type == 'multiply':
            return base_tiles * value
        elif config_type == 'replace':
            return value
        else:
            return base_tiles  # Default to no change

    def roll_number(self) -> int:
        """
        Simulate rolling a random number.

        Returns:
            int: A random number between 1 and 99999.
        """
        return random.randint(1, 99999)

    def open_configuration_window(self, master: tk.Tk) -> None:
        """
        Open a GUI window to configure the roll table settings.

        Args:
            master (tk.Tk): The parent Tkinter window.
        """
        roll_window = tk.Toplevel(master)
        roll_window.title("Configure Roll Table")

        # Number values (1-9)
        tk.Label(roll_window, text="Set values for numbers 1-9:").grid(row=0, column=0, columnspan=2)
        number_vars = {}
        for i in range(1, 10):
            tk.Label(roll_window, text=str(i)).grid(row=i, column=0)
            var = tk.IntVar(value=self.number_values[str(i)])
            number_vars[str(i)] = var
            tk.Entry(roll_window, textvariable=var).grid(row=i, column=1)

        # Repeats configuration
        tk.Label(roll_window, text="Configure Repeats:").grid(row=10, column=0, columnspan=2, pady=(10, 0))
        repeats = ['2', '3']  # '2' for doubles, '3' for triples
        repeat_vars = {}
        for idx, repeat in enumerate(repeats):
            row = 11 + idx * 3
            tk.Label(roll_window, text=f"{repeat}-digit Repeats").grid(row=row, column=0, columnspan=2)

            # Type option
            tk.Label(roll_window, text="Type:").grid(row=row + 1, column=0)
            type_var = tk.StringVar(value=self.repeats_config.get(repeat, {'type': 'add'})['type'])
            tk.OptionMenu(roll_window, type_var, 'add', 'multiply', 'replace').grid(row=row + 1, column=1)

            # Value
            tk.Label(roll_window, text="Value:").grid(row=row + 2, column=0)
            value_var = tk.IntVar(value=self.repeats_config.get(repeat, {'value': 0})['value'])
            tk.Entry(roll_window, textvariable=value_var).grid(row=row + 2, column=1)

            repeat_vars[repeat] = {'type': type_var, 'value': value_var}

        # Palindrome configuration
        tk.Label(roll_window, text="Configure Palindromes:").grid(row=20, column=0, columnspan=2, pady=(10, 0))
        palindrome_lengths = ['2', '3']
        palindrome_vars = {}
        for idx, length in enumerate(palindrome_lengths):
            row = 21 + idx * 3
            tk.Label(roll_window, text=f"Length {length} Palindromes").grid(row=row, column=0, columnspan=2)

            # Type option
            tk.Label(roll_window, text="Type:").grid(row=row + 1, column=0)
            type_var = tk.StringVar(value=self.palindromes_config.get(length, {'type': 'add'})['type'])
            tk.OptionMenu(roll_window, type_var, 'add', 'multiply', 'replace').grid(row=row + 1, column=1)

            # Value
            tk.Label(roll_window, text="Value:").grid(row=row + 2, column=0)
            value_var = tk.IntVar(value=self.palindromes_config.get(length, {'value': 0})['value'])
            tk.Entry(roll_window, textvariable=value_var).grid(row=row + 2, column=1)

            palindrome_vars[length] = {'type': type_var, 'value': value_var}

        def save_roll_table():
            # Save number values
            for num_str, var in number_vars.items():
                self.number_values[num_str] = var.get()

            # Save repeats configuration
            for repeat, vars_dict in repeat_vars.items():
                config_type = vars_dict['type'].get()
                value = vars_dict['value'].get()
                self.repeats_config[repeat] = {'type': config_type, 'value': value}

            # Save palindromes configuration
            for length, vars_dict in palindrome_vars.items():
                config_type = vars_dict['type'].get()
                value = vars_dict['value'].get()
                self.palindromes_config[length] = {'type': config_type, 'value': value}

            messagebox.showinfo("Roll Table Saved", "Roll table configurations have been saved.")
            roll_window.destroy()

        tk.Button(roll_window, text="Save", command=save_roll_table).grid(row=30, column=0, pady=10)
        tk.Button(roll_window, text="Cancel", command=roll_window.destroy).grid(row=30, column=1, pady=10)
