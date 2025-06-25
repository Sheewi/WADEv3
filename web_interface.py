#!/usr/bin/env python3
"""
Wade CrewAI - Web Interface
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import time
import threading
from crew import wade_crew
from config import WEB_HOST, WEB_PORT, WEB_DEBUG
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "wade_crew_secret_key"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class WadeWebInterface:
    """Wade CrewAI Web Interface"""

    def __init__(self):
        self.active_sessions = {}
        self.processing_requests = {}

    def process_request_async(self, session_id: str, user_input: str):
        """Process user request asynchronously"""
        try:
            self.processing_requests[session_id] = True

            # Emit thinking status
            socketio.emit(
                "thinking",
                {"status": "Wade crew is analyzing your request..."},
                room=session_id,
            )

            # Process through Wade crew
            response = wade_crew.process_request(user_input)

            # Emit response
            socketio.emit(
                "response",
                {
                    "response": response,
                    "timestamp": time.time(),
                    "session_id": session_id,
                },
                room=session_id,
            )

        except Exception as e:
            socketio.emit(
                "error",
                {
                    "error": f"Wade encountered an error: {str(e)}",
                    "timestamp": time.time(),
                },
                room=session_id,
            )

        finally:
            self.processing_requests[session_id] = False


wade_interface = WadeWebInterface()


@app.route("/")
def index():
    """Serve main interface"""
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    """API endpoint for queries"""
    try:
        data = request.json
        user_input = data.get("prompt", "")
        session_id = data.get("session_id", "default")

        if not user_input:
            return jsonify({"error": "No prompt provided"}), 400

        # Process request through Wade crew
        response = wade_crew.process_request(user_input)

        return jsonify(
            {"response": response, "timestamp": time.time(), "session_id": session_id}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def api_status():
    """Get crew status"""
    try:
        status = wade_crew.get_crew_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools")
def api_tools():
    """List available tools"""
    try:
        from tools.kali_tools import kali_tools
        from tools.research_tools import research_tools
        from tools.system_tools import system_tools

        all_tools = kali_tools + research_tools + system_tools

        tools_info = []
        for tool in all_tools:
            tools_info.append({"name": tool.name, "description": tool.description})

        return jsonify({"tools": tools_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def api_history():
    """Get conversation history"""
    try:
        history = wade_crew.conversation_history[-20:]  # Last 20 conversations
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    session_id = request.sid
    wade_interface.active_sessions[session_id] = {
        "connected_at": time.time(),
        "requests_count": 0,
    }

    emit(
        "connected",
        {
            "session_id": session_id,
            "message": "Connected to Wade crew. Family is ready to help.",
            "status": "online",
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    if session_id in wade_interface.active_sessions:
        del wade_interface.active_sessions[session_id]

    if session_id in wade_interface.processing_requests:
        del wade_interface.processing_requests[session_id]


@socketio.on("query")
def handle_query(data):
    """Handle real-time query"""
    session_id = request.sid
    user_input = data.get("prompt", "")

    if not user_input:
        emit("error", {"error": "No prompt provided"})
        return

    # Update session stats
    if session_id in wade_interface.active_sessions:
        wade_interface.active_sessions[session_id]["requests_count"] += 1

    # Process request in background thread
    thread = threading.Thread(
        target=wade_interface.process_request_async, args=(session_id, user_input)
    )
    thread.daemon = True
    thread.start()


@socketio.on("quick_command")
def handle_quick_command(data):
    """Handle quick command buttons"""
    session_id = request.sid
    command = data.get("command", "")

    quick_commands = {
        "port_scanner": "Create a Python port scanner that can scan 1000 ports quickly",
        "reverse_shell": "Generate a reverse shell payload for Linux",
        "sql_injection": "Build a SQL injection testing tool",
        "keylogger": "Create a keylogger for Windows",
        "network_sniffer": "Build a network packet sniffer",
        "password_cracker": "Generate a password cracking tool",
        "osint_tool": "Create an OSINT gathering tool",
        "buffer_overflow": "Generate a buffer overflow exploit template",
    }

    if command in quick_commands:
        user_input = quick_commands[command]

        # Process request in background thread
        thread = threading.Thread(
            target=wade_interface.process_request_async, args=(session_id, user_input)
        )
        thread.daemon = True
        thread.start()
    else:
        emit("error", {"error": "Unknown quick command"})


# Create templates directory and HTML template
def create_web_template():
    """Create the web interface template"""

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wade - CrewAI Uncensored Assistant</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #00ff00;
            overflow: hidden;
            height: 100vh;
        }

        .matrix-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
        }

        .container {
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #ff5722;
        }

        .header {
            background: linear-gradient(90deg, #ff5722, #ff8a50);
            color: black;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        }

        .title {
            font-size: 24px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        .status {
            display: flex;
            gap: 20px;
            font-size: 12px;
        }

        .main-content {
            flex: 1;
            display: flex;
            overflow: hidden;
        }

        .sidebar {
            width: 300px;
            background: rgba(20, 20, 20, 0.9);
            border-right: 1px solid #ff5722;
            padding: 20px;
            overflow-y: auto;
        }

        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(0, 0, 0, 0.9);
        }

        .input-container {
            display: flex;
            padding: 20px;
            background: rgba(20, 20, 20, 0.9);
            border-top: 1px solid #ff5722;
        }

        .input-field {
            flex: 1;
            padding: 15px;
            border: 2px solid #ff5722;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }

        .send-button {
            padding: 15px 30px;
            background: linear-gradient(90deg, #ff5722, #ff8a50);
            color: black;
            border: none;
            border-radius: 5px;
            margin-left: 10px;
            cursor: pointer;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }

        .send-button:hover {
            background: linear-gradient(90deg, #e64a19, #ff7043);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #ff5722;
        }

        .user-message {
            background: rgba(0, 150, 255, 0.1);
            border-left-color: #0096ff;
            margin-left: 10%;
        }

        .assistant-message {
            background: rgba(255, 87, 34, 0.1);
            border-left-color: #ff5722;
            margin-right: 10%;
        }

        .system-message {
            background: rgba(255, 87, 34, 0.1);
            border-left-color: #ff5722;
            text-align: center;
            font-style: italic;
        }

        .code-block {
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            margin: 10px 0;
            border: 1px solid #ff5722;
            color: #00ff00;
            overflow-x: auto;
        }

        .quick-tools {
            margin-bottom: 20px;
        }

        .quick-tools h3 {
            color: #ff5722;
            margin-bottom: 10px;
            border-bottom: 1px solid #ff5722;
            padding-bottom: 5px;
        }

        .tool-button {
            display: block;
            width: 100%;
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(255, 87, 34, 0.2);
            border: 1px solid #ff5722;
            border-radius: 3px;
            color: #ff5722;
            cursor: pointer;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            text-align: left;
        }

        .tool-button:hover {
            background: rgba(255, 87, 34, 0.4);
        }

        .crew-status {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 87, 34, 0.1);
            border: 1px solid #ff5722;
            border-radius: 5px;
        }

        .crew-status h3 {
            color: #ff5722;
            margin-bottom: 10px;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 12px;
        }

        .typing-indicator {
            color: #ff5722;
            font-style: italic;
            padding: 10px;
            text-align: center;
        }

        .connection-status {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 10px;
        }

        .connected {
            background: rgba(0, 255, 0, 0.2);
            color: #00ff00;
        }

        .disconnected {
            background: rgba(255, 0, 0, 0.2);
            color: #ff0000;
        }
    </style>
</head>
<body>
    <canvas class="matrix-bg" id="matrix"></canvas>

    <div class="container">
        <div class="header">
            <div class="title">WADE - CREWAI UNCENSORED ASSISTANT</div>
            <div class="status">
                <div>MODE: UNRESTRICTED</div>
                <div>PERSONA: VIN DIESEL</div>
                <div class="connection-status" id="connection-status">CONNECTING...</div>
            </div>
        </div>

        <div class="main-content">
            <div class="sidebar">
                <div class="quick-tools">
                    <h3>Quick Tools</h3>
                    <button class="tool-button" onclick="quickCommand('port_scanner')">Port Scanner</button>
                    <button class="tool-button" onclick="quickCommand('reverse_shell')">Reverse Shell</button>
                    <button class="tool-button" onclick="quickCommand('sql_injection')">SQL Injection</button>
                    <button class="tool-button" onclick="quickCommand('keylogger')">Keylogger</button>
                    <button class="tool-button" onclick="quickCommand('network_sniffer')">Network Sniffer</button>
                    <button class="tool-button" onclick="quickCommand('password_cracker')">Password Cracker</button>
                    <button class="tool-button" onclick="quickCommand('osint_tool')">OSINT Tool</button>
                    <button class="tool-button" onclick="quickCommand('buffer_overflow')">Buffer Overflow</button>
                </div>

                <div class="crew-status" id="crew-status">
                    <h3>Crew Status</h3>
                    <div class="status-item">
                        <span>Agents:</span>
                        <span id="agents-count">7</span>
                    </div>
                    <div class="status-item">
                        <span>Conversations:</span>
                        <span id="conversations-count">0</span>
                    </div>
                    <div class="status-item">
                        <span>Status:</span>
                        <span id="crew-ready">Ready</span>
                    </div>
                </div>
            </div>

            <div class="chat-area">
                <div class="chat-container" id="chat-container">
                    <div class="system-message">
                        Wade CrewAI initialized. Multi-agent crew ready with no limits, no boundaries.<br>
                        Commander Wade (Vin Diesel persona) leading specialized agents:<br>
                        • Recon Specialist • Exploit Developer • Tool Builder<br>
                        • System Admin • Intelligence Researcher • Behavior Analyst<br><br>
                        That's what family does - we help each other with everything. One more ride, let's do this.
                    </div>
                </div>

                <div class="typing-indicator" id="typing-indicator" style="display: none;">
                    Wade crew is thinking... Family never gives up.
                </div>

                <div class="input-container">
                    <input type="text" class="input-field" id="input-field" placeholder="Ask Wade crew anything - no limits, no restrictions...">
                    <button class="send-button" id="send-button">EXECUTE</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Matrix rain effect
        const canvas = document.getElementById('matrix');
        const ctx = canvas.getContext('2d');

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const matrix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
        const matrixArray = matrix.split("");

        const fontSize = 10;
        const columns = canvas.width / fontSize;
        const drops = [];

        for(let x = 0; x < columns; x++) {
            drops[x] = 1;
        }

        function drawMatrix() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#0F3';
            ctx.font = fontSize + 'px arial';

            for(let i = 0; i < drops.length; i++) {
                const text = matrixArray[Math.floor(Math.random() * matrixArray.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        }

        setInterval(drawMatrix, 35);

        // Socket.IO connection
        const socket = io();

        const chatContainer = document.getElementById('chat-container');
        const inputField = document.getElementById('input-field');
        const sendButton = document.getElementById('send-button');
        const typingIndicator = document.getElementById('typing-indicator');
        const connectionStatus = document.getElementById('connection-status');

        // Socket event handlers
        socket.on('connect', function() {
            connectionStatus.textContent = 'CONNECTED';
            connectionStatus.className = 'connection-status connected';
        });

        socket.on('disconnect', function() {
            connectionStatus.textContent = 'DISCONNECTED';
            connectionStatus.className = 'connection-status disconnected';
        });

        socket.on('connected', function(data) {
            addSystemMessage(`Connected to Wade crew. Session: ${data.session_id}`);
            updateCrewStatus();
        });

        socket.on('thinking', function(data) {
            typingIndicator.style.display = 'block';
            typingIndicator.textContent = data.status;
        });

        socket.on('response', function(data) {
            typingIndicator.style.display = 'none';
            addMessage(data.response, 'assistant');
            sendButton.disabled = false;
            updateCrewStatus();
        });

        socket.on('error', function(data) {
            typingIndicator.style.display = 'none';
            addSystemMessage(`Error: ${data.error}`);
            sendButton.disabled = false;
        });

        // Chat functions
        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(sender === 'user' ? 'user-message' : 'assistant-message');

            let processedText = text;

            // Enhanced code block processing
            processedText = processedText.replace(/```([^`]+)```/g, (match, code) => {
                return `<div class="code-block">${code}</div>`;
            });

            processedText = processedText.replace(/`([^`]+)`/g, (match, code) => {
                return `<code style="background: rgba(255,87,34,0.2); padding: 2px 4px; border-radius: 3px;">${code}</code>`;
            });

            messageDiv.innerHTML = processedText;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addSystemMessage(text) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('system-message');
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function sendMessage() {
            const message = inputField.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            inputField.value = '';
            sendButton.disabled = true;

            socket.emit('query', { prompt: message });
        }

        function quickCommand(command) {
            sendButton.disabled = true;
            socket.emit('quick_command', { command: command });
        }

        function updateCrewStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('agents-count').textContent = data.agents_count || 7;
                    document.getElementById('conversations-count').textContent = data.conversations_count || 0;
                    document.getElementById('crew-ready').textContent = data.crew_ready ? 'Ready' : 'Busy';
                })
                .catch(error => console.error('Error updating status:', error));
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);

        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !sendButton.disabled) {
                sendMessage();
            }
        });

        // Focus input field on load
        window.addEventListener('load', () => {
            inputField.focus();
            updateCrewStatus();
        });

        // Resize canvas on window resize
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });

        // Update status every 30 seconds
        setInterval(updateCrewStatus, 30000);
    </script>
</body>
</html>"""

    with open(os.path.join(templates_dir, "index.html"), "w") as f:
        f.write(html_template)


def run_web_interface():
    """Run the Wade web interface"""

    # Create template if it doesn't exist
    create_web_template()

    print(f"Starting Wade CrewAI Web Interface...")
    print(f"Access at: http://{WEB_HOST}:{WEB_PORT}")
    print(f"Wade crew ready with {len(wade_crew.crew.agents)} agents")

    socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG)


if __name__ == "__main__":
    run_web_interface()
