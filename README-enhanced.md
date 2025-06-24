# Wade - Advanced Multi-Agent System for Kali Linux

Wade is a sophisticated AI assistant designed specifically for Kali Linux, combining the power of local LLMs with a dynamic multi-agent architecture. It features flexible model routing, self-evolving capabilities, and deep integration with security tools.

## Key Features

### Core Architecture
- **Local LLM Integration**: Uses Ollama to run the Phind-CodeLlama model locally on CPU
- **Dynamic Model Router**: Intelligently routes queries to different models based on content and requirements
- **Multi-Agent System**: Uses Crew AI to coordinate specialized agents for different tasks
- **Self-Evolution**: Can create new agents on demand to handle specific tasks

### Agent Capabilities
- **Offensive Security**: Vulnerability assessment and penetration testing
- **Defensive Security**: System hardening and threat detection
- **Intelligence Research**: OSINT and dark web research
- **System Customization**: Desktop environment personalization
- **Tool Development**: Creating custom security tools and scripts
- **Continuous Learning**: Improving capabilities through user interaction

### Technical Features
- **Persistent Memory**: Remembers conversations and learns from interactions
- **Tool Execution**: Can build and run programs directly
- **Adaptive Learning**: Personalizes responses based on user preferences
- **Dynamic Agent Creation**: Creates new specialized agents as needed

## System Components

### 1. Model Router (`model_router.py`)
The Model Router manages different LLM backends and intelligently routes queries to the most appropriate model:

```python
# Example: Adding a new model to the router
router.add_model(
    "mistral-7b", 
    ModelType.OLLAMA, 
    "http://localhost:11434/api/generate",
    {"model": "mistral", "temperature": 0.7},
    ["reasoning", "instruction"],
    8192
)

# Example: Routing a query
model_name = router.select_model(
    query="Explain how buffer overflows work", 
    required_capabilities=["security", "technical"]
)
```

### 2. Dynamic Agent Factory (`dynamic_agent_factory.py`)
The Agent Factory creates and manages specialized agents dynamically:

```python
# Example: Creating an agent from a description
agent_id = await factory.create_agent_from_description(
    "Create an agent that specializes in network traffic analysis and can detect intrusions"
)

# Example: Analyzing a task and creating appropriate agents
result = await factory.analyze_task_and_create_agents(
    "Build a web scraper that can extract data from e-commerce websites and store it in a database"
)
```

### 3. Core System (`wade_core.py`)
The Core System orchestrates all components and provides the main interface:

```python
# Example: Processing a user query
response = await wade.process_query(
    "Find vulnerabilities in this WordPress site: example.com",
    user_id="user123"
)
```

## Installation

### Prerequisites
- Kali Linux (or any Debian-based distribution)
- Python 3.8+
- 8GB+ RAM (16GB+ recommended)
- 20GB+ free disk space

### Quick Install
```bash
# Clone the repository
git clone https://github.com/yourusername/wade.git
cd wade

# Run the installation script
chmod +x setup.sh
./setup.sh
```

### Manual Installation
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip curl wget git nodejs npm

# Install Python packages
pip3 install crewai langchain langchain-community flask flask-cors

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the Phind-CodeLlama model
ollama pull phind-codellama

# Set up Wade
mkdir -p ~/.wade/{models,logs,config,tools,agents,core,interface}
cp -r * ~/.wade/

# Create desktop shortcut
mkdir -p ~/.local/share/applications
cp wade.desktop ~/.local/share/applications/
```

## Usage

### Starting Wade
```bash
# Start Wade from the terminal
wade

# Or use the desktop shortcut in your applications menu
```

### Example Queries
- "Find vulnerabilities in this WordPress site: example.com"
- "Create a custom tool to automate network scanning"
- "Customize my desktop with a dark theme"
- "Research recent exploits for Apache servers"
- "Explain how buffer overflows work and show me an example"
- "Create a new agent that specializes in cloud security"

## Customization

### Adding New Models
Edit `~/.wade/config/models.json` to add new models:

```json
{
  "models": {
    "your-model-name": {
      "type": "ollama",
      "endpoint": "http://localhost:11434/api/generate",
      "parameters": {
        "temperature": 0.7
      },
      "specialties": ["your", "specialties"]
    }
  }
}
```

### Creating Custom Agents
Use the agent factory to create custom agents:

```python
factory.add_template("your-agent-name", {
    "role": "Your Agent Role",
    "goal": "Your agent's goal",
    "backstory": "Your agent's backstory",
    "tools": ["tool1", "tool2"],
    "allow_delegation": True,
    "verbose": True
})
```

## Building a Custom Kali ISO

To create a custom Kali Linux ISO with Wade pre-installed:

1. Set up a Kali Linux build environment:
   ```bash
   sudo apt update
   sudo apt install -y git live-build cdebootstrap
   ```

2. Clone the Kali live-build repository:
   ```bash
   git clone git://git.kali.org/live-build-config.git
   cd live-build-config
   ```

3. Create the necessary directories:
   ```bash
   mkdir -p kali-config/common/hooks/live/
   mkdir -p kali-config/variant-default/package-lists/
   ```

4. Copy the hook script:
   ```bash
   cp /path/to/wade/kali-integration/01-install-wade.chroot kali-config/common/hooks/live/
   chmod +x kali-config/common/hooks/live/01-install-wade.chroot
   ```

5. Copy the package list:
   ```bash
   cp /path/to/wade/kali-integration/wade.list.chroot kali-config/variant-default/package-lists/
   ```

6. Build the ISO:
   ```bash
   ./build.sh --distribution kali-rolling --verbose
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.