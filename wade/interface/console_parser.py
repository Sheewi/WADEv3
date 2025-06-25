# -*- coding: utf-8 -*-
"""
WADE Console Parser
Integrates GUI/CLI output, allows live editing.
"""

import os
import sys
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Callable


class ConsoleParser:
    """
    Console Parser for WADE.
    Integrates GUI/CLI output and allows live editing of commands.
    """

    def __init__(self, elite_few, cli_handler):
        """
        Initialize the console parser.

        Args:
            elite_few: Reference to the EliteFew instance
            cli_handler: Reference to the CLIHandler instance
        """
        self.elite_few = elite_few
        self.cli_handler = cli_handler
        self.command_handlers = {}
        self.command_aliases = {}
        self.help_text = {}

        # Register built-in commands
        self._register_built_in_commands()

    def _register_built_in_commands(self):
        """Register built-in commands."""
        self.register_command(
            "help", self._cmd_help, "Display help information", ["?", "h"]
        )
        self.register_command("exit", self._cmd_exit, "Exit WADE", ["quit", "q"])
        self.register_command("clear", self._cmd_clear, "Clear the screen", ["cls"])
        self.register_command(
            "history", self._cmd_history, "Show command history", ["hist"]
        )
        self.register_command("status", self._cmd_status, "Show WADE status", ["stat"])
        self.register_command(
            "version", self._cmd_version, "Show WADE version", ["ver"]
        )
        self.register_command(
            "reload", self._cmd_reload, "Reload WADE configuration", ["refresh"]
        )
        self.register_command(
            "agents", self._cmd_agents, "List available agents", ["agent"]
        )
        self.register_command(
            "tools", self._cmd_tools, "List available tools", ["tool"]
        )

    def register_command(
        self,
        command: str,
        handler: Callable,
        help_text: str,
        aliases: Optional[List[str]] = None,
    ):
        """
        Register a command handler.

        Args:
            command: Command name
            handler: Function to handle the command
            help_text: Help text for the command
            aliases: Optional list of command aliases
        """
        self.command_handlers[command] = handler
        self.help_text[command] = help_text

        if aliases:
            for alias in aliases:
                self.command_aliases[alias] = command

    def parse_input(self, input_str: str) -> Tuple[bool, Optional[str]]:
        """
        Parse user input and execute commands.

        Args:
            input_str: User input string

        Returns:
            Tuple of (handled, response)
            - handled: Whether the input was handled as a command
            - response: Optional response message
        """
        if not input_str.strip():
            return False, None

        # Parse command and arguments
        parts = input_str.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Check if command is registered
        if cmd in self.command_handlers:
            return True, self.command_handlers[cmd](args)

        # Check if command is an alias
        if cmd in self.command_aliases:
            return True, self.command_handlers[self.command_aliases[cmd]](args)

        # Not a registered command
        return False, None

    def _cmd_help(self, args: str) -> str:
        """
        Handle the 'help' command.

        Args:
            args: Command arguments

        Returns:
            Help text
        """
        if args:
            # Help for specific command
            cmd = args.strip().lower()

            if cmd in self.help_text:
                return f"{cmd}: {self.help_text[cmd]}"

            if cmd in self.command_aliases:
                cmd = self.command_aliases[cmd]
                return f"{cmd}: {self.help_text[cmd]}"

            return f"Unknown command: {cmd}"

        # General help
        help_lines = ["Available commands:"]

        for cmd in sorted(self.command_handlers.keys()):
            aliases = [
                alias for alias, target in self.command_aliases.items() if target == cmd
            ]
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            help_lines.append(f"  {cmd}{alias_str}: {self.help_text[cmd]}")

        return "\n".join(help_lines)

    def _cmd_exit(self, args: str) -> str:
        """
        Handle the 'exit' command.

        Args:
            args: Command arguments

        Returns:
            Exit message
        """
        # Signal to exit
        self.elite_few.wade_core.is_running = False
        return "Exiting WADE..."

    def _cmd_clear(self, args: str) -> str:
        """
        Handle the 'clear' command.

        Args:
            args: Command arguments

        Returns:
            Empty string
        """
        self.cli_handler.clear_screen()
        return ""

    def _cmd_history(self, args: str) -> str:
        """
        Handle the 'history' command.

        Args:
            args: Command arguments

        Returns:
            Command history
        """
        try:
            limit = int(args) if args else 10
        except ValueError:
            limit = 10

        history = self.cli_handler.get_command_history(limit)

        if not history:
            return "No command history."

        history_lines = ["Command history:"]
        for i, cmd in enumerate(history, 1):
            history_lines.append(f"  {i}. {cmd}")

        return "\n".join(history_lines)

    def _cmd_status(self, args: str) -> str:
        """
        Handle the 'status' command.

        Args:
            args: Command arguments

        Returns:
            WADE status
        """
        # Get agent status
        agent_manager = self.elite_few.agent_manager
        active_agents = agent_manager.get_active_agents()

        # Get memory status
        stm_stats = self.elite_few.stm.get_category_stats()
        ltm_stats = self.elite_few.ltm.get_category_stats()

        # Format status
        status_lines = ["WADE Status:"]
        status_lines.append(f"  Active agents: {len(active_agents)}")
        status_lines.append(f"  Short-term memory categories: {len(stm_stats)}")
        status_lines.append(f"  Long-term memory categories: {len(ltm_stats)}")

        # Add agent details
        if active_agents:
            status_lines.append("\nActive agents:")
            for agent_id, agent in active_agents.items():
                status_lines.append(f"  {agent.agent_type} ({agent_id})")

        return "\n".join(status_lines)

    def _cmd_version(self, args: str) -> str:
        """
        Handle the 'version' command.

        Args:
            args: Command arguments

        Returns:
            WADE version
        """
        from WADE_CORE import __version__

        return f"WADE version {__version__}"

    def _cmd_reload(self, args: str) -> str:
        """
        Handle the 'reload' command.

        Args:
            args: Command arguments

        Returns:
            Reload status
        """
        try:
            self.elite_few.wade_core.load_configuration()
            return "Configuration reloaded successfully."
        except Exception as e:
            return f"Error reloading configuration: {e}"

    def _cmd_agents(self, args: str) -> str:
        """
        Handle the 'agents' command.

        Args:
            args: Command arguments

        Returns:
            List of available agents
        """
        agent_manager = self.elite_few.agent_manager
        agent_types = agent_manager.get_registered_agent_types()
        active_agents = agent_manager.get_active_agents()

        if not agent_types:
            return "No agent types registered."

        agent_lines = ["Available agent types:"]
        for agent_type in sorted(agent_types):
            active_count = sum(
                1 for agent in active_agents.values() if agent.agent_type == agent_type
            )
            active_str = f" ({active_count} active)" if active_count > 0 else ""
            agent_lines.append(f"  {agent_type}{active_str}")

        return "\n".join(agent_lines)

    def _cmd_tools(self, args: str) -> str:
        """
        Handle the 'tools' command.

        Args:
            args: Command arguments

        Returns:
            List of available tools
        """
        tool_manager = self.elite_few.tool_manager
        tools = tool_manager.get_available_tools()

        if not tools:
            return "No tools available."

        tool_lines = ["Available tools:"]
        for tool_name, tool_info in sorted(tools.items()):
            tool_lines.append(
                f"  {tool_name}: {tool_info.get('description', 'No description')}"
            )

        return "\n".join(tool_lines)

    def process_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Process a command string.

        Args:
            command: Command string

        Returns:
            Tuple of (handled, response)
        """
        return self.parse_input(command)
