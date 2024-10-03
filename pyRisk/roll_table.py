# roll_table.py

import random
import tkinter as tk
from tkinter import messagebox

class RollTable:
    def __init__(self):
        # Default values for numbers 0-9
        self.number_values = {str(i): 1 for i in range(1, 10)}  # '1'-'9' ? 1 tile each
        self.number_values['0'] = 0  # '0' ? 0 tiles
        # Configurations for repeats and palindromes
        self.repeats_config = {
            '2': {'type': 'add', 'value': 0},  # Doubles
            '3': {'type': 'add', 'value': 0},  # Triples
            # Add more repeats as needed
        }
        self.palindromes_config = {
            '2': {'type': 'add', 'value': 0},  # Palindromes of length 2
            '3': {'type': 'add', 'value': 0},  # Palindromes of length 3
            # Add more palindrome lengths as needed
        }
        self.default_tiles = 1  # Default tiles when no specific config is matched

    def calculate_tiles(self, roll_value):
        roll_str = str(roll_value)
        tiles = 0

        # Check for repeats at the end first
        repeat_length, repeat_value = self._get_longest_repeat(roll_str)
        if repeat_length >= 2:
            repeat_config = self.repeats_config.get(str(repeat_length))
            if repeat_config:
                base_tiles = self.number_values.get(repeat_value, 1) * repeat_length
                tiles += self._apply_config(base_tiles, repeat_config)
            else:
                tiles += self.default_tiles  # Use default_tiles if no specific config
            return tiles  # Return early if a repeat was processed

        # Check for palindromes at the end
        palindrome_length = self._get_end_palindrome_length(roll_str)
        if palindrome_length >= 2:
            palindrome_config = self.palindromes_config.get(str(palindrome_length))
            if palindrome_config:
                base_tiles = self.number_values.get(roll_str[-1], 1) * palindrome_length
                tiles += self._apply_config(base_tiles, palindrome_config)
            else:
                tiles += self.default_tiles  # Use default_tiles if no specific config
            return tiles  # Return early if a palindrome was processed

        # If no repeats or palindromes, just count the last digit
        last_digit = roll_str[-1]
        tiles += self.number_values.get(last_digit, self.default_tiles)  # Use default_tiles if digit not found

        return tiles

    def _get_longest_repeat(self, roll_str):
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

        if repeat_length == 1:
            return 0, ''
        else:
            return repeat_length, repeat_value

    def _get_end_palindrome_length(self, roll_str):
        for i in range(len(roll_str), 1, -1):
            if self._is_palindrome(roll_str[-i:]):
                return i
        return 0

    def _is_palindrome(self, s):
        return s == s[::-1]

    def _apply_config(self, base_tiles, config):
        config_type = config['type']
        value = config['value']
        if config_type == 'add':
            return base_tiles + value
        elif config_type == 'multiply':
            return base_tiles * value
        elif config_type == 'replace':
            return value
        else:
            return base_tiles  # Default to no change

    def roll_number(self):
        # Roll a random number (e.g., 1 to 99999)
        return random.randint(1, 99999)

    def open_configuration_window(self, master):
        roll_window = tk.Toplevel(master)
        roll_window.title("Configure Roll Table")

        # Number values (0-9)
        tk.Label(roll_window, text="Set values for numbers 0-9:").grid(row=0, column=0, columnspan=2, pady=(10, 0))
        number_vars = {}
        for i in range(0, 10):
            tk.Label(roll_window, text=str(i)).grid(row=i+1, column=0, padx=10, pady=2)
            var = tk.IntVar(value=self.number_values[str(i)])
            number_vars[str(i)] = var
            tk.Entry(roll_window, textvariable=var).grid(row=i+1, column=1, padx=10, pady=2)

        # Repeats configuration
        tk.Label(roll_window, text="Configure Repeats:").grid(row=11, column=0, columnspan=2, pady=(10, 0))
        repeats = ['2', '3']  # '2' for doubles, '3' for triples
        repeat_vars = {}
        for idx, repeat in enumerate(repeats):
            row = 12 + idx * 3
            tk.Label(roll_window, text=f"{repeat}-digit Repeats").grid(row=row, column=0, columnspan=2, pady=(5, 0))

            # Type option
            tk.Label(roll_window, text="Type:").grid(row=row+1, column=0, padx=10, pady=2)
            type_var = tk.StringVar(value=self.repeats_config.get(repeat, {'type': 'add'})['type'])
            tk.OptionMenu(roll_window, type_var, 'add', 'multiply', 'replace').grid(row=row+1, column=1, padx=10, pady=2)

            # Value
            tk.Label(roll_window, text="Value:").grid(row=row+2, column=0, padx=10, pady=2)
            value_var = tk.IntVar(value=self.repeats_config.get(repeat, {'value': 0})['value'])
            tk.Entry(roll_window, textvariable=value_var).grid(row=row+2, column=1, padx=10, pady=2)

            repeat_vars[repeat] = {'type': type_var, 'value': value_var}

        # Palindrome configuration
        tk.Label(roll_window, text="Configure Palindromes:").grid(row=18, column=0, columnspan=2, pady=(10, 0))
        palindrome_lengths = ['2', '3']
        palindrome_vars = {}
        for idx, length in enumerate(palindrome_lengths):
            row = 19 + idx * 3
            tk.Label(roll_window, text=f"Length {length} Palindromes").grid(row=row, column=0, columnspan=2, pady=(5, 0))

            # Type option
            tk.Label(roll_window, text="Type:").grid(row=row+1, column=0, padx=10, pady=2)
            type_var = tk.StringVar(value=self.palindromes_config.get(length, {'type': 'add'})['type'])
            tk.OptionMenu(roll_window, type_var, 'add', 'multiply', 'replace').grid(row=row+1, column=1, padx=10, pady=2)

            # Value
            tk.Label(roll_window, text="Value:").grid(row=row+2, column=0, padx=10, pady=2)
            value_var = tk.IntVar(value=self.palindromes_config.get(length, {'value': 0})['value'])
            tk.Entry(roll_window, textvariable=value_var).grid(row=row+2, column=1, padx=10, pady=2)

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

        tk.Button(roll_window, text="Save", command=save_roll_table).grid(row=25, column=0, pady=10)
        tk.Button(roll_window, text="Cancel", command=roll_window.destroy).grid(row=25, column=1, pady=10)
