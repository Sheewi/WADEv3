# Wade with Crew AI - Multi-agent System for Kali Linux

This project provides an advanced integration of the Phind-CodeLlama model with Crew AI for Kali Linux. It creates a multi-agent system that can handle various security tasks through specialized agents.

## Features

- Local LLM using Ollama and Phind-CodeLlama
- Multi-agent system using Crew AI
- Specialized agents for different security tasks
- Advanced web-based interface
- Pre-installed in the custom Kali ISO
- No GPU required (though performance will be better with one)

## Specialized Agents

Wade includes the following specialized agents:

1. **Offensive Security Specialist** - Finds and exploits vulnerabilities in target systems
2. **Defensive Security Specialist** - Protects systems from attacks and ensures security compliance
3. **Intelligence Researcher** - Gathers and analyzes information from various sources
4. **System Customization Specialist** - Enhances and personalizes the Kali Linux environment
5. **Tool Developer** - Creates and modifies tools and scripts for specific tasks
6. **Continuous Learning Specialist** - Improves the system's knowledge and capabilities over time

## Files in this Repository

- `setup-crew-wade.sh`: Script to install Wade with Crew AI on an existing Kali Linux system
- `01-install-crew-wade.chroot`: Hook script for Kali ISO build process
- `crew-wade.list.chroot`: Package list for Kali ISO build
- `README-crew.md`: This file

## Creating a Custom Kali ISO

Follow these steps to create a custom Kali Linux ISO with Wade and Crew AI pre-installed:

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
   cp /path/to/simple-wade/01-install-crew-wade.chroot kali-config/common/hooks/live/
   chmod +x kali-config/common/hooks/live/01-install-crew-wade.chroot
   ```

5. Copy the package list:
   ```bash
   cp /path/to/simple-wade/crew-wade.list.chroot kali-config/variant-default/package-lists/
   ```

6. Build the ISO:
   ```bash
   ./build.sh --distribution kali-rolling --verbose
   ```

The build process may take several hours depending on your system. Once complete, you'll find the ISO in the `images` directory.

## Installing on an Existing System

If you already have Kali Linux installed and just want to add Wade with Crew AI:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/wade-crew-ai.git
   ```

2. Run the setup script:
   ```bash
   cd wade-crew-ai
   chmod +x setup-crew-wade.sh
   ./setup-crew-wade.sh
   ```

3. Start Wade:
   ```bash
   wade
   ```

## Usage

1. Start Wade from the application menu or by running `wade` in a terminal
2. The web interface will open in your browser
3. You'll see the list of specialized agents in the sidebar
4. Type your queries in the input field and press Enter or click Send
5. The system will automatically route your query to the most appropriate agent
6. The agent will process your query and display the response

## Notes

- The Phind-CodeLlama model will be downloaded during the first boot, which may take some time depending on your internet connection
- Performance will depend on your system's CPU and RAM
- At least 8GB of RAM is recommended, 16GB or more is ideal
- The web interface runs locally on port 8080

## Customization

You can customize Wade by editing the files in `~/.wade/`:

- Modify the agent definitions in `~/.wade/core/crew_ai_integration.py`
- Edit the interface in `~/.wade/interface/index.html`
- Add new tools in the `~/.wade/tools/` directory

## License

This project is licensed under the MIT License.