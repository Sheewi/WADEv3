# -*- coding: utf-8 -*-
"""
WADE GUI Overlay
Renders web-based visual interface.
"""

import os
import sys
import time
import json
import logging
import threading
import webbrowser
from typing import Dict, List, Any, Optional

try:
    from flask import Flask, render_template, request, jsonify
    from flask_socketio import SocketIO
    from flask_cors import CORS
except ImportError:
    logging.warning(
        "Flask, Flask-SocketIO, or Flask-CORS not installed. GUI will not be available."
    )


class GUIOverlay:
    """
    GUI Overlay for WADE.
    Renders web-based visual interface.
    """

    def __init__(self, elite_few, cli_handler, host: str = "0.0.0.0", port: int = 8080):
        """
        Initialize the GUI overlay.

        Args:
            elite_few: Reference to the EliteFew instance
            cli_handler: Reference to the CLI handler
            host: Host to bind to
            port: Port to bind to
        """
        self.elite_few = elite_few
        self.cli_handler = cli_handler
        self.logger = logging.getLogger("wade.gui_overlay")
        self.host = host
        self.port = port
        self.app = None
        self.socketio = None
        self.thread = None
        self.is_running = False

        # Initialize GUI state
        self.state = {
            "messages": [],
            "agents": {},
            "system_info": {},
            "memory_stats": {},
            "tools": [],
        }

        # Set up Flask app
        self._setup_app()

        self.logger.info("GUI overlay initialized")

    def _setup_app(self):
        """Set up Flask app."""
        try:
            # Create Flask app
            self.app = Flask(__name__)
            CORS(self.app)

            # Create SocketIO instance
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")

            # Set up routes
            self._setup_routes()

            # Set up SocketIO events
            self._setup_socketio_events()

        except Exception as e:
            self.logger.error(f"Error setting up Flask app: {e}")
            self.app = None
            self.socketio = None

    def _setup_routes(self):
        """Set up Flask routes."""
        if not self.app:
            return

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/api/state")
        def get_state():
            return jsonify(self.state)

        @self.app.route("/api/command", methods=["POST"])
        def execute_command():
            data = request.json
            command = data.get("command", "")

            if not command:
                return jsonify({"status": "error", "message": "No command provided"})

            # Process command
            self.elite_few.process_user_command(command)

            return jsonify({"status": "success", "message": "Command executed"})

    def _setup_socketio_events(self):
        """Set up SocketIO events."""
        if not self.socketio:
            return

        @self.socketio.on("connect")
        def handle_connect():
            self.logger.info("Client connected to SocketIO")

            # Send initial state
            self.socketio.emit("state_update", self.state)

        @self.socketio.on("disconnect")
        def handle_disconnect():
            self.logger.info("Client disconnected from SocketIO")

        @self.socketio.on("command")
        def handle_command(data):
            command = data.get("command", "")

            if not command:
                return {"status": "error", "message": "No command provided"}

            # Process command
            self.elite_few.process_user_command(command)

            return {"status": "success", "message": "Command executed"}

    def start(self):
        """Start the GUI overlay."""
        if not self.app or not self.socketio:
            self.logger.error("Flask app not initialized. GUI will not be available.")
            return False

        if self.is_running:
            return True

        # Start in a separate thread
        self.thread = threading.Thread(target=self._run_app)
        self.thread.daemon = True
        self.thread.start()

        self.is_running = True

        self.logger.info(f"GUI overlay started at http://{self.host}:{self.port}")

        # Open browser
        webbrowser.open(f"http://localhost:{self.port}")

        return True

    def _run_app(self):
        """Run Flask app."""
        try:
            self.socketio.run(self.app, host=self.host, port=self.port)
        except Exception as e:
            self.logger.error(f"Error running Flask app: {e}")

    def stop(self):
        """Stop the GUI overlay."""
        if not self.is_running:
            return True

        # Stop SocketIO
        if self.socketio:
            self.socketio.stop()

        self.is_running = False

        self.logger.info("GUI overlay stopped")

        return True

    def update_state(self, updates: Dict[str, Any]):
        """
        Update GUI state.

        Args:
            updates: Dictionary with updates to apply
        """
        self.state.update(updates)

        # Emit state update
        if self.socketio and self.is_running:
            self.socketio.emit("state_update", self.state)

    def send_message_to_gui(self, message: Dict[str, Any]):
        """
        Send a message to the GUI.

        Args:
            message: Message to send
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = time.time()

        # Add to messages
        self.state["messages"].append(message)

        # Limit messages to 100
        if len(self.state["messages"]) > 100:
            self.state["messages"] = self.state["messages"][-100:]

        # Emit message
        if self.socketio and self.is_running:
            self.socketio.emit("message", message)

    def update_agents(self, agents: Dict[str, Any]):
        """
        Update agent information.

        Args:
            agents: Dictionary with agent information
        """
        self.state["agents"] = agents

        # Emit agent update
        if self.socketio and self.is_running:
            self.socketio.emit("agents_update", agents)

    def update_system_info(self, system_info: Dict[str, Any]):
        """
        Update system information.

        Args:
            system_info: Dictionary with system information
        """
        self.state["system_info"] = system_info

        # Emit system info update
        if self.socketio and self.is_running:
            self.socketio.emit("system_info_update", system_info)

    def update_memory_stats(self, memory_stats: Dict[str, Any]):
        """
        Update memory statistics.

        Args:
            memory_stats: Dictionary with memory statistics
        """
        self.state["memory_stats"] = memory_stats

        # Emit memory stats update
        if self.socketio and self.is_running:
            self.socketio.emit("memory_stats_update", memory_stats)

    def update_tools(self, tools: List[Dict[str, Any]]):
        """
        Update tool information.

        Args:
            tools: List of tool information
        """
        self.state["tools"] = tools

        # Emit tools update
        if self.socketio and self.is_running:
            self.socketio.emit("tools_update", tools)


def initialize_gui(
    elite_few, cli_handler, host: str = "0.0.0.0", port: int = 8080
) -> Optional[GUIOverlay]:
    """
    Initialize the GUI overlay.

    Args:
        elite_few: Reference to the EliteFew instance
        cli_handler: Reference to the CLI handler
        host: Host to bind to
        port: Port to bind to

    Returns:
        GUI overlay instance or None if initialization failed
    """
    try:
        # Create GUI overlay
        gui = GUIOverlay(elite_few, cli_handler, host, port)

        # Start GUI
        if gui.start():
            return gui
        else:
            return None

    except Exception as e:
        logging.error(f"Error initializing GUI: {e}")
        return None
