# -*- coding: utf-8 -*-
"""
WADE OS Core
Central orchestrator for the WADE system.
"""

import os
import sys
import time
import json
import threading
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import WADE modules
from WADE_CORE.config import ConfigManager
from WADE_CORE.core_logic import EliteFew
from WADE_CORE.task_router import TaskRouter
from WADE_CORE.utils import setup_logging, create_directories


class WADE_OS_Core:
    """
    WADE OS Core
    Central orchestrator for the WADE system.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the WADE OS Core.

        Args:
            config_path: Optional path to configuration file
        """
        self.start_time = time.time()
        self.version = "1.0.0"
        self.is_running = True

        # Set up configuration
        self.config = ConfigManager(config_path)

        # Set up logging
        self.logger = setup_logging(
            self.config.get("system", {}).get("log_level", "INFO")
        )

        # Create required directories
        create_directories(self.config.get("paths", {}))

        # Initialize components
        self._initialize_components()

        self.logger.info(f"WADE OS Core v{self.version} initialized")

    def _initialize_components(self):
        """Initialize WADE components."""
        # Initialize core logic (EliteFew)
        self.elite_few = EliteFew(self)

        # Initialize task router
        self.task_router = TaskRouter(self.elite_few)

        # Initialize memory
        from memory.short_term_memory import ShortTermMemory
        from memory.long_term_memory import LongTermMemory

        self.elite_few.stm = ShortTermMemory()
        self.elite_few.ltm = LongTermMemory()

        # Initialize agent manager
        from agents.agent_manager import AgentManager

        self.elite_few.agent_manager = AgentManager(self.elite_few)

        # Initialize tool manager
        from tools.tool_manager import ToolManager

        self.elite_few.tool_manager = ToolManager(self.elite_few)

        # Initialize evolution engine
        from evolution.evolution_engine import EvolutionEngine

        self.elite_few.evolution_engine = EvolutionEngine(self.elite_few)

        # Initialize interface
        from interface.cli_handler import CLIHandler
        from interface.console_parser import ConsoleParser

        self.elite_few.cli_handler = CLIHandler(self.elite_few)
        self.elite_few.console_parser = ConsoleParser(
            self.elite_few, self.elite_few.cli_handler
        )

        # Initialize GUI if enabled
        if self.config.get("interface", {}).get("gui", {}).get("enabled", True):
            from interface.gui_overlay import initialize_gui

            gui_config = self.config.get("interface", {}).get("gui", {})
            host = gui_config.get("host", "0.0.0.0")
            port = gui_config.get("port", 8080)

            self.elite_few.gui = initialize_gui(
                self.elite_few, self.elite_few.cli_handler, host, port
            )

        # Initialize security components if enabled
        if self.config.get("security", {}).get("intrusion_detection_enabled", True):
            from security.intrusion_detection import IntrusionDetection

            self.elite_few.intrusion_detection = IntrusionDetection()
            self.elite_few.intrusion_detection.start_monitoring()

        if self.config.get("security", {}).get("sandbox_enabled", True):
            from security.sandbox_manager import SandboxManager

            self.elite_few.sandbox_manager = SandboxManager()

        # Initialize communication components if enabled
        if self.config.get("network", {}).get("enabled", True):
            from comms.agent_messaging import AgentMessaging
            from comms.network_stack import NetworkStack

            self.elite_few.agent_messaging = AgentMessaging()
            self.elite_few.network_stack = NetworkStack()

            # Start network server if configured
            network_config = self.config.get("network", {})
            if network_config.get("enabled", True):
                host = network_config.get("host", "0.0.0.0")
                port = network_config.get("port", 8081)

                def handle_connection(connection_id, address):
                    self.logger.info(f"New connection: {connection_id} from {address}")

                self.elite_few.network_stack.start_server(port, handle_connection)

    def load_configuration(self):
        """Reload configuration."""
        self.config.reload()
        self.logger.info("Configuration reloaded")

    def run(self):
        """Run the WADE OS Core."""
        self.logger.info("Starting WADE OS Core")

        # Start evolution if enabled
        if self.config.get("evolution", {}).get("enabled", True):
            self.elite_few.evolution_engine.start_evolution()

        # Create default agents
        default_agents = self.config.get("agents", {}).get("default_agents", [])
        for agent_type in default_agents:
            self.elite_few.agent_manager.create_agent(agent_type)

        # Main loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.shutdown()

    def _main_loop(self):
        """Main execution loop."""
        self.logger.info("Entering main loop")

        # Display welcome message
        from resources.templates import render_text_template

        welcome_message = render_text_template(
            "welcome",
            version=self.version,
            username=os.getenv("USER", "User"),
            status_message="All systems operational.",
        )

        print(welcome_message)

        # Main loop
        while self.is_running:
            try:
                # Get user input
                user_input = self.elite_few.cli_handler.get_input()

                # Process user input
                self.elite_few.process_user_command(user_input)

                # Small sleep to prevent CPU hogging
                time.sleep(0.01)

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                self.is_running = False
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

    def shutdown(self):
        """Shutdown the WADE OS Core."""
        self.logger.info("Shutting down WADE OS Core")

        # Stop evolution
        if hasattr(self.elite_few, "evolution_engine"):
            self.elite_few.evolution_engine.stop_evolution()

        # Stop intrusion detection
        if hasattr(self.elite_few, "intrusion_detection"):
            self.elite_few.intrusion_detection.stop_monitoring()

        # Stop network stack
        if hasattr(self.elite_few, "network_stack"):
            self.elite_few.network_stack.shutdown()

        # Stop agent messaging
        if hasattr(self.elite_few, "agent_messaging"):
            self.elite_few.agent_messaging.shutdown()

        # Stop GUI
        if hasattr(self.elite_few, "gui"):
            self.elite_few.gui.stop()

        # Shutdown agents
        if hasattr(self.elite_few, "agent_manager"):
            self.elite_few.agent_manager.shutdown_all_agents()

        self.logger.info("WADE OS Core shutdown complete")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="WADE OS Core")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Create and run WADE OS Core
    wade_core = WADE_OS_Core(args.config)
    wade_core.run()


if __name__ == "__main__":
    main()
