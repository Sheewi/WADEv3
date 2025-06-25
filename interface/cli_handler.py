# -*- coding: utf-8 -*-
"""
WADE CLI Handler
Manages CLI input/output and command parsing.
"""

import os
import sys
import time
import readline
import threading
from typing import Dict, List, Any, Optional


class CLIHandler:
    """
    CLI Handler for WADE.
    Manages command-line interface input/output and command parsing.
    """

    def __init__(self, elite_few):
        """
        Initialize the CLI handler.

        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.command_history = []
        self.max_history = 100
        self.output_buffer = []
        self.output_lock = threading.Lock()
        self.input_prompt = "WADE> "

        # Set up readline for command history
        self._setup_readline()

    def _setup_readline(self):
        """Set up readline for command history and tab completion."""
        # Set up command history file
        history_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "WADE_RUNTIME", "cli_history"
        )
        try:
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            readline.read_history_file(history_file)
            readline.set_history_length(self.max_history)
        except FileNotFoundError:
            pass

        # Save history on exit
        import atexit

        atexit.register(readline.write_history_file, history_file)

    def get_input(self, prompt: Optional[str] = None) -> str:
        """
        Get input from the user.

        Args:
            prompt: Optional prompt to display

        Returns:
            User input string
        """
        if prompt:
            self.input_prompt = prompt

        try:
            user_input = input(self.input_prompt)

            # Add to command history
            if user_input.strip():
                self.command_history.append(user_input)
                if len(self.command_history) > self.max_history:
                    self.command_history = self.command_history[-self.max_history :]

            return user_input

        except EOFError:
            # Handle Ctrl+D
            print("\nEOF detected. Exiting...")
            return "exit"
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print("\nKeyboard interrupt detected.")
            return ""

    def display_output(self, message: str, level: str = "INFO"):
        """
        Display output to the user.

        Args:
            message: Message to display
            level: Message level (INFO, WARN, ERROR, etc.)
        """
        # Format message based on level
        if level == "ERROR":
            formatted_message = f"\033[91m{message}\033[0m"  # Red
        elif level == "WARN" or level == "WARNING":
            formatted_message = f"\033[93m{message}\033[0m"  # Yellow
        elif level == "SUCCESS":
            formatted_message = f"\033[92m{message}\033[0m"  # Green
        elif level == "DEBUG":
            formatted_message = f"\033[94m{message}\033[0m"  # Blue
        elif level == "CRITICAL":
            formatted_message = f"\033[91m\033[1m{message}\033[0m"  # Bold Red
        elif level == "ALERT":
            formatted_message = f"\033[93m\033[1m{message}\033[0m"  # Bold Yellow
        elif level == "CHALLENGE":
            formatted_message = f"\033[95m{message}\033[0m"  # Purple
        elif level == "CLARIFY":
            formatted_message = f"\033[96m{message}\033[0m"  # Cyan
        else:
            formatted_message = message

        # Add to output buffer
        with self.output_lock:
            self.output_buffer.append(formatted_message)
            print(formatted_message)

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parse a command string into components.

        Args:
            command: Command string to parse

        Returns:
            Dictionary with parsed command components
        """
        # Simple command parsing
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        return {"command": cmd, "args": args, "raw": command}

    def get_command_history(self, limit: int = 10) -> List[str]:
        """
        Get command history.

        Args:
            limit: Maximum number of commands to return

        Returns:
            List of recent commands
        """
        return self.command_history[-limit:]

    def get_output_buffer(self, clear: bool = False) -> List[str]:
        """
        Get the output buffer.

        Args:
            clear: Whether to clear the buffer after retrieval

        Returns:
            List of output messages
        """
        with self.output_lock:
            buffer = list(self.output_buffer)
            if clear:
                self.output_buffer = []

        return buffer
