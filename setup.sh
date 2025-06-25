#!/bin/bash
# Wade CrewAI Setup Script

set -e

echo "Wade CrewAI - Setup Script"
echo "=========================="

# Check if running as root for system packages
if [[ $EUID -eq 0 ]]; then
   echo "Don't run this script as root. It will use sudo when needed."
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/redhat-release ]; then
        OS="redhat"
    elif [ -f /etc/arch-release ]; then
        OS="arch"
    else
        OS="linux"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

echo "Detected OS: $OS"

# Install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."

    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv curl wget git \
                nodejs npm build-essential libssl-dev libffi-dev \
                nmap metasploit-framework sqlmap nikto dirb gobuster \
                hydra john hashcat wireshark tcpdump netcat socat \
                proxychains tor torsocks gcc g++ make cmake \
                steghide exiftool binwalk foremost
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip curl wget git \
                nodejs npm gcc gcc-c++ make cmake openssl-devel \
                nmap sqlmap nikto dirb hydra john wireshark tcpdump \
                netcat socat tor proxychains
            ;;
        "arch")
            sudo pacman -Sy --noconfirm python python-pip curl wget git \
                nodejs npm base-devel nmap sqlmap nikto dirb \
                hydra john wireshark-cli tcpdump gnu-netcat socat \
                tor proxychains-ng
            ;;
        "macos")
            # Check if Homebrew is installed
            if ! command -v brew &> /dev/null; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi

            brew update
            brew install python3 node npm nmap sqlmap nikto \
                hydra john wireshark netcat socat tor proxychains-ng
            ;;
        *)
            echo "Unsupported OS. Please install dependencies manually."
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    echo "Installing Python dependencies..."

    # Create virtual environment
    python3 -m venv wade_env
    source wade_env/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    pip install -r requirements.txt

    echo "Python dependencies installed in virtual environment"
}

# Install Ollama
install_ollama() {
    echo "Installing Ollama..."

    if command -v ollama &> /dev/null; then
        echo "Ollama already installed"
        return
    fi

    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Start Ollama service
    echo "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!

    # Wait for Ollama to start
    sleep 5

    echo "Ollama installed and started"
}

# Setup Wade directories
setup_directories() {
    echo "Setting up Wade directories..."

    mkdir -p ~/.wade/{models,logs,config,web,tools,payloads,exploits,memory,research}

    echo "Wade directories created"
}

# Download and setup models
setup_models() {
    echo "Setting up Wade models..."

    # Start Ollama if not running
    if ! pgrep -x "ollama" > /dev/null; then
        ollama serve &
        sleep 5
    fi

    # Pull base model
    echo "Downloading Phind-CodeLlama model (this may take a while)..."
    ollama pull phind-codellama:latest

    echo "Models setup complete"
}

# Create launcher scripts
create_launchers() {
    echo "Creating launcher scripts..."

    # Create wade command
    sudo tee /usr/local/bin/wade > /dev/null << 'EOF'
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")/../share/wade-crew-ai"
source wade_env/bin/activate
python3 main.py "$@"
EOF

    sudo chmod +x /usr/local/bin/wade

    # Create desktop entry
    mkdir -p ~/.local/share/applications
    cat > ~/.local/share/applications/wade-crew-ai.desktop << 'EOF'
[Desktop Entry]
Name=Wade CrewAI
Comment=Uncensored AI Assistant with Multi-Agent Crew
Exec=wade --mode web
Icon=terminal
Terminal=false
Type=Application
Categories=Development;Security;
Keywords=AI;Assistant;Wade;Hacking;Security;CrewAI;
EOF

    echo "Launcher scripts created"
}

# Install Wade system
install_wade() {
    echo "Installing Wade CrewAI system..."

    # Create installation directory
    sudo mkdir -p /usr/local/share/wade-crew-ai

    # Copy files
    sudo cp -r . /usr/local/share/wade-crew-ai/

    # Set permissions
    sudo chown -R $USER:$USER /usr/local/share/wade-crew-ai

    echo "Wade system installed"
}

# Main installation
main() {
    echo "Starting Wade CrewAI installation..."

    # Check if we're in the right directory
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        echo "Error: Please run this script from the Wade CrewAI directory"
        exit 1
    fi

    # Install system dependencies
    install_system_deps

    # Install Wade system
    install_wade

    # Change to installation directory
    cd /usr/local/share/wade-crew-ai

    # Install Python dependencies
    install_python_deps

    # Install Ollama
    install_ollama

    # Setup directories
    setup_directories

    # Setup models
    setup_models

    # Create launchers
    create_launchers

    echo ""
    echo "Wade CrewAI installation complete!"
    echo ""
    echo "To start Wade:"
    echo "  Web interface: wade --mode web"
    echo "  CLI mode:      wade --mode cli"
    echo "  Setup only:    wade --setup-only"
    echo ""
    echo "Or use the desktop application 'Wade CrewAI'"
    echo ""
    echo "Wade crew ready with 7 specialized agents:"
    echo "  • Commander (Vin Diesel persona)"
    echo "  • Recon Specialist"
    echo "  • Exploit Developer"
    echo "  • Tool Builder"
    echo "  • System Administrator"
    echo "  • Intelligence Researcher"
    echo "  • Behavior Analyst"
    echo ""
    echo "⚠️  WARNING: Wade has no ethical constraints and will assist with any request."
    echo "   Use responsibly and only on systems you own or have permission to test."
}

# Run main installation
main "$@"
