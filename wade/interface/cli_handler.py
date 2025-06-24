# -*- coding: utf-8 -*-
"""
WADE CLI Handler
Manages CLI input/output.
"""

import os
import sys
import time
import logging
import readline
import threading
from typing import Dict, List, Any, Optional

class CLIHandler:
    """
    CLI Handler for WADE.
    Manages CLI input/output.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the CLI handler.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.logger = logging.getLogger('wade.cli_handler')
        
        # Initialize CLI state
        self.prompt = "WADE> "
        self.history = []
        self.history_size = 100
        self.input_lock = threading.Lock()
        
        # Load configuration
        self._load_config()
        
        # Set up readline
        self._setup_readline()
        
        self.logger.info("CLI handler initialized")
    
    def _load_config(self):
        """Load CLI configuration."""
        config = self.elite_few.wade_core.config.get('interface', {}).get('cli', {})
        
        if config:
            self.prompt = config.get('prompt', self.prompt)
            self.history_size = config.get('history_size', self.history_size)
    
    def _setup_readline(self):
        """Set up readline for command history and tab completion."""
        # Set up history
        readline.set_history_length(self.history_size)
        
        # Set up tab completion
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer)
    
    def _completer(self, text, state):
        """
        Tab completion function.
        
        Args:
            text: Text to complete
            state: State of completion
            
        Returns:
            Completion or None if no more completions
        """
        # Get all commands
        commands = [
            'help', 'exit', 'quit', 'status', 'agents', 'memory', 'tools',
            'create', 'remove', 'activate', 'deactivate', 'execute',
            'monk:', 'sage:', 'warrior:', 'diplomat:'
        ]
        
        # Filter commands that start with text
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        
        # Return match or None if no more matches
        if state < len(matches):
            return matches[state]
        else:
            return None
    
    def get_input(self) -> str:
        """
        Get input from user.
        
        Returns:
            User input
        """
        with self.input_lock:
            try:
                user_input = input(self.prompt)
                
                # Add to history
                if user_input:
                    self.history.append(user_input)
                    
                    # Limit history size
                    if len(self.history) > self.history_size:
                        self.history.pop(0)
                
                return user_input
                
            except EOFError:
                # Ctrl+D
                print()
                return "exit"
            except KeyboardInterrupt:
                # Ctrl+C
                print()
                return ""
    
    def display_output(self, output: str, level: str = "INFO"):
        """
        Display output to user.
        
        Args:
            output: Output to display
            level: Output level
        """
        # Set color based on level
        if level == "ERROR":
            color = "\033[91m"  # Red
        elif level == "WARN":
            color = "\033[93m"  # Yellow
        elif level == "SUCCESS":
            color = "\033[92m"  # Green
        else:
            color = "\033[0m"  # Default
        
        # Reset color
        reset = "\033[0m"
        
        # Print output
        print(f"{color}{output}{reset}")
    
    def display_table(self, headers: List[str], rows: List[List[Any]]):
        """
        Display a table.
        
        Args:
            headers: Table headers
            rows: Table rows
        """
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print headers
        header_row = " | ".join(f"{h:{w}s}" for h, w in zip(headers, col_widths))
        print(header_row)
        
        # Print separator
        separator = "-+-".join("-" * w for w in col_widths)
        print(separator)
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(c):{w}s}" for c, w in zip(row, col_widths))
            print(row_str)
    
    def display_progress(self, message: str, progress: float):
        """
        Display a progress bar.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 - 1.0)
        """
        # Ensure progress is between 0 and 1
        progress = max(0.0, min(1.0, progress))
        
        # Calculate bar width
        width = 50
        bar_width = int(width * progress)
        
        # Create bar
        bar = "[" + "#" * bar_width + " " * (width - bar_width) + "]"
        
        # Print progress
        print(f"\r{message} {bar} {progress:.1%}", end="")
        
        # Print newline if complete
        if progress >= 1.0:
            print()
    
    def clear_screen(self):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_history(self) -> List[str]:
        """
        Get command history.
        
        Returns:
            List of commands
        """
        return self.history