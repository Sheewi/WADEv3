# -*- coding: utf-8 -*-
"""
WADE GUI Overlay
Renders Xbox Game Bar-style visual interface.
"""

import os
import sys
import time
import json
import threading
import webbrowser
from typing import Dict, List, Any, Optional

# Flask imports for web-based GUI
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_socketio import SocketIO
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

class GUIOverlay:
    """
    GUI Overlay for WADE.
    Provides a web-based interface for interacting with WADE.
    """
    
    def __init__(self, elite_few, cli_handler, host: str = '0.0.0.0', port: int = 8080):
        """
        Initialize the GUI overlay.
        
        Args:
            elite_few: Reference to the EliteFew instance
            cli_handler: Reference to the CLIHandler instance
            host: Host to bind the web server to
            port: Port to bind the web server to
        """
        self.elite_few = elite_few
        self.cli_handler = cli_handler
        self.host = host
        self.port = port
        self.app = None
        self.socketio = None
        self.thread = None
        self.clients = set()
        self.is_running = False
        self.message_queue = []
        self.message_lock = threading.Lock()
    
    def initialize(self):
        """Initialize the GUI overlay."""
        if not FLASK_AVAILABLE:
            print("Flask not available. GUI overlay will not be started.")
            return False
        
        try:
            # Create Flask app
            self.app = Flask(__name__, 
                            static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
            CORS(self.app)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            
            # Set up routes
            self._setup_routes()
            
            # Set up Socket.IO events
            self._setup_socketio_events()
            
            return True
            
        except Exception as e:
            print(f"Error initializing GUI overlay: {e}")
            return False
    
    def _setup_routes(self):
        """Set up Flask routes."""
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'online',
                'version': getattr(self.elite_few.wade_core, 'version', 'unknown'),
                'uptime': time.time() - getattr(self.elite_few.wade_core, 'start_time', time.time())
            })
        
        @self.app.route('/api/command', methods=['POST'])
        def command():
            data = request.json
            command = data.get('command', '')
            
            if command:
                # Queue command for processing
                self.elite_few.process_user_command(command)
                
                return jsonify({
                    'status': 'success',
                    'message': f"Command '{command}' queued for processing"
                })
            
            return jsonify({
                'status': 'error',
                'message': "No command provided"
            })
        
        @self.app.route('/api/history')
        def history():
            return jsonify({
                'commands': self.cli_handler.get_command_history(),
                'outputs': self.cli_handler.get_output_buffer()
            })
    
    def _setup_socketio_events(self):
        """Set up Socket.IO events."""
        @self.socketio.on('connect')
        def handle_connect():
            client_id = request.sid
            self.clients.add(client_id)
            print(f"Client connected: {client_id}")
            
            # Send initial status
            self.socketio.emit('status', {
                'status': 'connected',
                'client_id': client_id,
                'server_time': time.time()
            }, room=client_id)
            
            # Send queued messages
            with self.message_lock:
                for message in self.message_queue:
                    self.socketio.emit('message', message, room=client_id)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = request.sid
            if client_id in self.clients:
                self.clients.remove(client_id)
            print(f"Client disconnected: {client_id}")
        
        @self.socketio.on('command')
        def handle_command(data):
            command = data.get('command', '')
            
            if command:
                # Queue command for processing
                self.elite_few.process_user_command(command)
                
                self.socketio.emit('command_received', {
                    'status': 'success',
                    'command': command,
                    'timestamp': time.time()
                }, room=request.sid)
    
    def start(self):
        """Start the GUI overlay in a separate thread."""
        if not self.app or not self.socketio:
            if not self.initialize():
                return False
        
        if self.is_running:
            return True
        
        # Start Flask app in a separate thread
        self.thread = threading.Thread(target=self._run_app)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for app to start
        for _ in range(10):
            if self.is_running:
                break
            time.sleep(0.5)
        
        return self.is_running
    
    def _run_app(self):
        """Run the Flask app."""
        try:
            self.is_running = True
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"Error running GUI overlay: {e}")
        finally:
            self.is_running = False
    
    def send_message_to_gui(self, message: Dict[str, Any]):
        """
        Send a message to all connected GUI clients.
        
        Args:
            message: Message to send
        """
        if not self.is_running or not self.socketio:
            # Queue message for later
            with self.message_lock:
                self.message_queue.append(message)
            return
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = time.time()
        
        # Send to all clients
        self.socketio.emit('message', message)
        
        # Also queue for new clients
        with self.message_lock:
            self.message_queue.append(message)
            
            # Keep only last 100 messages
            if len(self.message_queue) > 100:
                self.message_queue = self.message_queue[-100:]
    
    def stop(self):
        """Stop the GUI overlay."""
        if self.is_running and self.socketio:
            # Notify clients
            self.socketio.emit('server_shutdown', {
                'message': 'Server shutting down',
                'timestamp': time.time()
            })
            
            # Stop Socket.IO and Flask
            self.socketio.stop()
            self.is_running = False
    
    def open_in_browser(self):
        """Open the GUI in a web browser."""
        if self.is_running:
            url = f"http://{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}"
            webbrowser.open(url)
            return True
        return False

def initialize_gui(elite_few, cli_handler, host: str = '0.0.0.0', port: int = 8080) -> Optional[GUIOverlay]:
    """
    Initialize and start the GUI overlay.
    
    Args:
        elite_few: Reference to the EliteFew instance
        cli_handler: Reference to the CLIHandler instance
        host: Host to bind the web server to
        port: Port to bind the web server to
        
    Returns:
        GUIOverlay instance or None if initialization failed
    """
    gui = GUIOverlay(elite_few, cli_handler, host, port)
    
    if gui.initialize() and gui.start():
        return gui
    
    return None

def run_gui(elite_few, cli_handler, host: str = '0.0.0.0', port: int = 8080):
    """
    Run the GUI overlay (blocking).
    
    Args:
        elite_few: Reference to the EliteFew instance
        cli_handler: Reference to the CLIHandler instance
        host: Host to bind the web server to
        port: Port to bind the web server to
    """
    gui = GUIOverlay(elite_few, cli_handler, host, port)
    
    if gui.initialize():
        # Run in current thread (blocking)
        gui._run_app()
    else:
        print("Failed to initialize GUI overlay.")