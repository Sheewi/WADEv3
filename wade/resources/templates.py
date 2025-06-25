# -*- coding: utf-8 -*-
"""
WADE Templates
Provides HTML and text templates for WADE.
"""

from typing import Dict, List, Any, Optional

# HTML templates for GUI
HTML_TEMPLATES = {
    "index": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WADE - Weaponized Autonomous Deployment Engine</title>
    <style>
        :root {
            --primary-color: #1a1a1a;
            --secondary-color: #2a2a2a;
            --accent-color: #00ff00;
            --text-color: #f0f0f0;
            --border-color: #444;
            --hover-color: #333;
        }

        body {
            font-family: 'Courier New', monospace;
            background-color: var(--primary-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        header {
            background-color: var(--secondary-color);
            padding: 10px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: var(--accent-color);
        }

        .status {
            font-size: 14px;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--accent-color);
            margin-right: 5px;
        }

        main {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 200px;
            background-color: var(--secondary-color);
            border-right: 1px solid var(--border-color);
            padding: 10px;
            overflow-y: auto;
        }

        .sidebar-section {
            margin-bottom: 20px;
        }

        .sidebar-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: var(--accent-color);
        }

        .sidebar-item {
            padding: 5px 10px;
            cursor: pointer;
            border-radius: 3px;
        }

        .sidebar-item:hover {
            background-color: var(--hover-color);
        }

        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .output {
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            background-color: var(--primary-color);
            border-bottom: 1px solid var(--border-color);
        }

        .message {
            margin-bottom: 10px;
            padding: 5px;
            border-radius: 3px;
        }

        .message-info {
            border-left: 3px solid #3498db;
        }

        .message-success {
            border-left: 3px solid #2ecc71;
        }

        .message-warning {
            border-left: 3px solid #f39c12;
        }

        .message-error {
            border-left: 3px solid #e74c3c;
        }

        .message-time {
            font-size: 12px;
            color: #888;
        }

        .input-area {
            padding: 10px;
            background-color: var(--secondary-color);
            display: flex;
        }

        .input-field {
            flex: 1;
            padding: 8px;
            border: 1px solid var(--border-color);
            border-radius: 3px;
            background-color: var(--primary-color);
            color: var(--text-color);
            font-family: 'Courier New', monospace;
        }

        .input-field:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        .send-button {
            margin-left: 10px;
            padding: 8px 15px;
            background-color: var(--accent-color);
            color: var(--primary-color);
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-weight: bold;
        }

        .send-button:hover {
            background-color: #00cc00;
        }

        footer {
            padding: 5px 10px;
            background-color: var(--secondary-color);
            border-top: 1px solid var(--border-color);
            font-size: 12px;
            text-align: center;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
        }

        .modal-content {
            background-color: var(--secondary-color);
            margin: 10% auto;
            padding: 20px;
            border: 1px solid var(--border-color);
            width: 60%;
            max-width: 600px;
            border-radius: 5px;
        }

        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: var(--accent-color);
        }

        .modal-title {
            margin-top: 0;
            color: var(--accent-color);
        }

        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--border-color);
        }

        .tab {
            padding: 10px 15px;
            cursor: pointer;
            background-color: var(--secondary-color);
        }

        .tab.active {
            background-color: var(--primary-color);
            border-bottom: 2px solid var(--accent-color);
        }

        .tab-content {
            display: none;
            padding: 10px;
        }

        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">WADE</div>
        <div class="status">
            <span class="status-indicator"></span>
            <span id="status-text">Online</span>
        </div>
    </header>

    <main>
        <div class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">Agents</div>
                <div id="agent-list">
                    <div class="sidebar-item">Monk</div>
                    <div class="sidebar-item">Sage</div>
                    <div class="sidebar-item">Warrior</div>
                    <div class="sidebar-item">Diplomat</div>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Tools</div>
                <div id="tool-list">
                    <div class="sidebar-item">System Info</div>
                    <div class="sidebar-item">Network</div>
                    <div class="sidebar-item">File Browser</div>
                    <div class="sidebar-item">Process Manager</div>
                </div>
            </div>
        </div>

        <div class="content">
            <div class="output" id="output">
                <div class="message message-info">
                    <div class="message-time">12:34:56</div>
                    <div class="message-content">WADE system initialized.</div>
                </div>
                <div class="message message-success">
                    <div class="message-time">12:35:01</div>
                    <div class="message-content">All agents loaded successfully.</div>
                </div>
                <div class="message message-warning">
                    <div class="message-time">12:35:10</div>
                    <div class="message-content">Network connection unstable.</div>
                </div>
                <div class="message message-error">
                    <div class="message-time">12:35:15</div>
                    <div class="message-content">Failed to load external resources.</div>
                </div>
            </div>

            <div class="input-area">
                <input type="text" class="input-field" id="input-field" placeholder="Enter command...">
                <button class="send-button" id="send-button">Send</button>
            </div>
        </div>
    </main>

    <footer>
        WADE v1.0.0 | Weaponized Autonomous Deployment Engine
    </footer>

    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" id="modal-close">&times;</span>
            <h2 class="modal-title" id="modal-title">Modal Title</h2>
            <div id="modal-body">
                Modal content goes here.
            </div>
        </div>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();

        // DOM elements
        const outputElement = document.getElementById('output');
        const inputField = document.getElementById('input-field');
        const sendButton = document.getElementById('send-button');
        const statusText = document.getElementById('status-text');
        const modal = document.getElementById('modal');
        const modalClose = document.getElementById('modal-close');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        // Connect to server
        socket.on('connect', () => {
            addMessage('Connected to WADE server.', 'success');
            statusText.textContent = 'Online';
            document.querySelector('.status-indicator').style.backgroundColor = '#2ecc71';
        });

        // Disconnect from server
        socket.on('disconnect', () => {
            addMessage('Disconnected from WADE server.', 'error');
            statusText.textContent = 'Offline';
            document.querySelector('.status-indicator').style.backgroundColor = '#e74c3c';
        });

        // Receive message from server
        socket.on('message', (data) => {
            addMessage(data.content, data.level || 'info');
        });

        // Send message to server
        function sendMessage() {
            const message = inputField.value.trim();

            if (message) {
                socket.emit('command', { command: message });
                inputField.value = '';
                addMessage(`> ${message}`, 'command');
            }
        }

        // Add message to output
        function addMessage(content, level = 'info') {
            const messageElement = document.createElement('div');
            messageElement.className = `message message-${level}`;

            const timeElement = document.createElement('div');
            timeElement.className = 'message-time';
            timeElement.textContent = new Date().toLocaleTimeString();

            const contentElement = document.createElement('div');
            contentElement.className = 'message-content';
            contentElement.textContent = content;

            messageElement.appendChild(timeElement);
            messageElement.appendChild(contentElement);

            outputElement.appendChild(messageElement);
            outputElement.scrollTop = outputElement.scrollHeight;
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);

        inputField.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });

        modalClose.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });

        // Show modal
        function showModal(title, content) {
            modalTitle.textContent = title;
            modalBody.innerHTML = content;
            modal.style.display = 'block';
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            // Add event listeners for sidebar items
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.addEventListener('click', () => {
                    showModal(item.textContent, `Content for ${item.textContent}`);
                });
            });
        });
    </script>
</body>
</html>""",
    "error": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - WADE</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #f0f0f0;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .error-container {
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 20px;
            max-width: 600px;
            text-align: center;
        }

        .error-title {
            color: #e74c3c;
            font-size: 24px;
            margin-bottom: 10px;
        }

        .error-message {
            margin-bottom: 20px;
        }

        .error-code {
            font-family: monospace;
            background-color: #1a1a1a;
            padding: 10px;
            border-radius: 3px;
            margin-bottom: 20px;
            text-align: left;
        }

        .back-button {
            display: inline-block;
            padding: 8px 15px;
            background-color: #3498db;
            color: #fff;
            text-decoration: none;
            border-radius: 3px;
        }

        .back-button:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-title">Error</div>
        <div class="error-message">{message}</div>
        <div class="error-code">{code}</div>
        <a href="/" class="back-button">Back to Home</a>
    </div>
</body>
</html>""",
}

# Text templates for CLI
TEXT_TEMPLATES = {
    "welcome": """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                  WADE - Weaponized Autonomous Deployment Engine              ║
║                                                                              ║
║                              Version: {version}                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Welcome to WADE, {username}!

Type 'help' to see available commands.
Type 'exit' to quit.

{status_message}
""",
    "help": """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                WADE Help                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

General Commands:
  help                 Show this help message
  exit, quit           Exit WADE
  clear, cls           Clear the screen
  status               Show WADE status
  version              Show WADE version

Agent Commands:
  agents               List available agents
  agent <name> <cmd>   Send command to agent
  create <agent_type>  Create a new agent

Memory Commands:
  memory               Show memory status
  remember <key> <val> Store value in memory
  recall <key>         Retrieve value from memory
  forget <key>         Remove value from memory

Tool Commands:
  tools                List available tools
  tool <name> <args>   Execute a tool

System Commands:
  system               Show system information
  logs                 Show system logs
  config               Show configuration
  reload               Reload configuration

For more information on a specific command, type 'help <command>'.
""",
    "status": """
╔══════════════════════════════════════════════════════════════════════════════╗
║                               WADE Status                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

System:
  Version:       {version}
  Uptime:        {uptime}
  CPU Usage:     {cpu_usage}%
  Memory Usage:  {memory_usage}%
  Disk Usage:    {disk_usage}%

Agents:
  Active:        {active_agents}
  Total:         {total_agents}

Memory:
  Short-term:    {stm_entries} entries
  Long-term:     {ltm_entries} entries

Network:
  Connections:   {connections}
  Bandwidth:     {bandwidth}

Last Activity:   {last_activity}
""",
}


def get_html_template(template_name: str) -> str:
    """
    Get an HTML template.

    Args:
        template_name: Name of the template

    Returns:
        HTML template
    """
    return HTML_TEMPLATES.get(template_name, "")


def get_text_template(template_name: str) -> str:
    """
    Get a text template.

    Args:
        template_name: Name of the template

    Returns:
        Text template
    """
    return TEXT_TEMPLATES.get(template_name, "")


def render_html_template(template_name: str, **kwargs) -> str:
    """
    Render an HTML template with variables filled in.

    Args:
        template_name: Name of the template
        **kwargs: Variables to fill in the template

    Returns:
        Rendered HTML template
    """
    template = get_html_template(template_name)

    if not template:
        return ""

    return template.format(**kwargs)


def render_text_template(template_name: str, **kwargs) -> str:
    """
    Render a text template with variables filled in.

    Args:
        template_name: Name of the template
        **kwargs: Variables to fill in the template

    Returns:
        Rendered text template
    """
    template = get_text_template(template_name)

    if not template:
        return ""

    return template.format(**kwargs)
