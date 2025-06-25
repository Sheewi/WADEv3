#!/bin/bash
# Simple setup script for Phind model with OpenHands on Kali Linux

set -e

echo "Setting up Simple Wade - Phind model with OpenHands"
echo "=================================================="

# Create directories
mkdir -p ~/.simple-wade/{models,logs,config}

# Install dependencies
echo "Installing dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip curl wget git nodejs npm
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy --noconfirm python python-pip curl wget git nodejs npm
else
    echo "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user flask flask-cors requests websockets

# Install Ollama
echo "Installing Ollama..."
if [ ! -f /usr/local/bin/ollama ]; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Give Ollama time to start
sleep 5

# Pull the Phind model
echo "Pulling Phind-CodeLlama model (this may take a while)..."
ollama pull phind-codellama:latest

# Create a simple web interface
echo "Creating web interface..."
mkdir -p ~/.simple-wade/web
cat > ~/.simple-wade/web/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Simple Wade - Phind with OpenHands</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 20px;
      background-color: #1e1e1e;
      color: #f0f0f0;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
      background-color: #2d2d2d;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    h1 {
      color: #ff5722;
      text-align: center;
    }

    .chat-container {
      height: 400px;
      overflow-y: auto;
      border: 1px solid #444;
      border-radius: 5px;
      padding: 10px;
      margin-bottom: 20px;
      background-color: #333;
    }

    .input-container {
      display: flex;
      gap: 10px;
    }

    .input-field {
      flex: 1;
      padding: 10px;
      border: 1px solid #444;
      border-radius: 5px;
      background-color: #333;
      color: white;
    }

    .send-button {
      padding: 10px 20px;
      background-color: #ff5722;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }

    .send-button:hover {
      background-color: #e64a19;
    }

    .message {
      margin-bottom: 10px;
      padding: 10px;
      border-radius: 5px;
    }

    .user-message {
      background-color: #0b93f6;
      color: white;
      align-self: flex-end;
      margin-left: 20%;
    }

    .assistant-message {
      background-color: #444;
      color: white;
      align-self: flex-start;
      margin-right: 20%;
    }

    .code-block {
      background-color: #1e1e1e;
      padding: 10px;
      border-radius: 5px;
      font-family: monospace;
      white-space: pre-wrap;
      margin: 10px 0;
    }

    .system-message {
      color: #888;
      font-style: italic;
      text-align: center;
      margin: 10px 0;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Simple Wade - Phind with OpenHands</h1>

    <div class="chat-container" id="chat-container">
      <div class="system-message">System initialized. Ready to assist.</div>
    </div>

    <div class="input-container">
      <input type="text" class="input-field" id="input-field" placeholder="Type your message...">
      <button class="send-button" id="send-button">Send</button>
    </div>
  </div>

  <script>
    const chatContainer = document.getElementById('chat-container');
    const inputField = document.getElementById('input-field');
    const sendButton = document.getElementById('send-button');

    // Add message to chat
    function addMessage(text, sender) {
      const messageDiv = document.createElement('div');
      messageDiv.classList.add('message');
      messageDiv.classList.add(sender === 'user' ? 'user-message' : 'assistant-message');

      // Process markdown-like formatting
      let processedText = text;

      // Code blocks
      processedText = processedText.replace(/```([^`]+)```/g, (match, code) => {
        return `<div class="code-block">${code}</div>`;
      });

      // Inline code
      processedText = processedText.replace(/`([^`]+)`/g, (match, code) => {
        return `<code>${code}</code>`;
      });

      messageDiv.innerHTML = processedText;
      chatContainer.appendChild(messageDiv);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Add system message
    function addSystemMessage(text) {
      const messageDiv = document.createElement('div');
      messageDiv.classList.add('system-message');
      messageDiv.textContent = text;
      chatContainer.appendChild(messageDiv);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Send message to backend
    async function sendMessage() {
      const message = inputField.value.trim();
      if (!message) return;

      // Add user message to chat
      addMessage(message, 'user');

      // Clear input field
      inputField.value = '';

      // Add typing indicator
      addSystemMessage('Thinking...');

      try {
        // Send to backend
        const response = await fetch('/api/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: message })
        });

        const data = await response.json();

        // Remove typing indicator
        chatContainer.removeChild(chatContainer.lastChild);

        // Add assistant response
        addMessage(data.response, 'assistant');
      } catch (error) {
        // Remove typing indicator
        chatContainer.removeChild(chatContainer.lastChild);

        // Add error message
        addSystemMessage(`Error: ${error.message}`);
      }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);

    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });

    // Focus input field on load
    window.addEventListener('load', () => {
      inputField.focus();
    });
  </script>
</body>
</html>
EOF

# Create Flask backend
cat > ~/.simple-wade/web/app.py << 'EOF'
#!/usr/bin/env python3
import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    prompt = data.get('prompt', '')

    try:
        # Query Ollama
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'phind-codellama',
            'prompt': prompt,
            'stream': False
        })

        result = response.json()
        return jsonify({'response': result.get('response', 'No response')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

chmod +x ~/.simple-wade/web/app.py

# Create launcher script
echo "Creating launcher script..."
cat > ~/.simple-wade/launch.sh << 'EOF'
#!/bin/bash

# Start Ollama service
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
sleep 2

# Start web interface
cd ~/.simple-wade/web
python3 app.py &
WEB_PID=$!

# Open browser
xdg-open http://localhost:8080 &

# Wait for termination
echo "Simple Wade is running. Press Ctrl+C to stop."
trap "kill $OLLAMA_PID $WEB_PID; exit" INT TERM
wait
EOF

chmod +x ~/.simple-wade/launch.sh

# Create desktop entry
echo "Creating desktop entry..."
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/simple-wade.desktop << 'EOF'
[Desktop Entry]
Name=Simple Wade
Comment=Phind model with OpenHands
Exec=bash -c "~/.simple-wade/launch.sh"
Icon=terminal
Terminal=false
Type=Application
Categories=Utility;
Keywords=AI;Assistant;Wade;
EOF

# Create symlink to launcher
echo "Creating symlink to launcher..."
sudo ln -sf ~/.simple-wade/launch.sh /usr/local/bin/simple-wade

# Clean up
if [ -n "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID
fi

echo "=================================================="
echo "Simple Wade setup complete!"
echo ""
echo "To start Simple Wade, run: simple-wade"
echo "Or use the desktop shortcut in your application menu"
echo ""
echo "The web interface will be available at: http://localhost:8080"
echo ""
echo "Enjoy your new AI assistant!"
