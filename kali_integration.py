#!/usr/bin/env python3
"""
Wade CrewAI - Kali Linux Integration Script
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def create_kali_hook():
    """Create Kali live-build hook for Wade integration"""
    
    hook_script = '''#!/bin/bash
# Wade CrewAI Kali Integration Hook
# Place in config/hooks/normal/

set -e

echo "Installing Wade CrewAI..."

# Install system dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv curl wget git \\
    nodejs npm build-essential libssl-dev libffi-dev \\
    tor proxychains steghide exiftool binwalk foremost

# Create wade user if building for live system
if [ ! -d "/home/wade" ]; then
    useradd -m -s /bin/bash wade
    echo "wade:wade" | chpasswd
    usermod -aG sudo wade
fi

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create Wade directories
mkdir -p /opt/wade-crew-ai
mkdir -p /home/wade/.wade/{models,logs,config,tools,payloads,exploits,memory,research}

# Copy Wade CrewAI files (assumes they're in the build directory)
if [ -d "/tmp/wade-crew-ai" ]; then
    cp -r /tmp/wade-crew-ai/* /opt/wade-crew-ai/
fi

# Set up Python environment
cd /opt/wade-crew-ai
python3 -m venv wade_env
source wade_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create wade command
cat > /usr/local/bin/wade << 'EOF'
#!/bin/bash
cd /opt/wade-crew-ai
source wade_env/bin/activate
python3 main.py "$@"
EOF

chmod +x /usr/local/bin/wade

# Create desktop entry
mkdir -p /usr/share/applications
cat > /usr/share/applications/wade-crew-ai.desktop << 'EOF'
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

# Create autostart entry for Wade service
mkdir -p /etc/systemd/system
cat > /etc/systemd/system/wade-crew.service << 'EOF'
[Unit]
Description=Wade CrewAI Service
After=network.target

[Service]
Type=simple
User=wade
WorkingDirectory=/opt/wade-crew-ai
Environment=PATH=/opt/wade-crew-ai/wade_env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/wade-crew-ai/wade_env/bin/python main.py --mode web --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable Wade service
systemctl enable wade-crew.service

# Set permissions
chown -R wade:wade /home/wade/.wade
chown -R wade:wade /opt/wade-crew-ai

# Configure Tor for research capabilities
echo "HiddenServiceStatistics 0" >> /etc/tor/torrc
echo "ExitPolicy reject *:*" >> /etc/tor/torrc

# Add Wade to sudoers for system operations
echo "wade ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/wade

echo "Wade CrewAI installation complete"
'''
    
    return hook_script

def create_package_list():
    """Create package list for Kali build"""
    
    packages = [
        # Core system
        'python3',
        'python3-pip', 
        'python3-venv',
        'curl',
        'wget',
        'git',
        'nodejs',
        'npm',
        'build-essential',
        'libssl-dev',
        'libffi-dev',
        
        # Penetration testing tools
        'nmap',
        'metasploit-framework',
        'sqlmap',
        'nikto',
        'dirb',
        'gobuster',
        'hydra',
        'john',
        'hashcat',
        'wireshark',
        'tcpdump',
        'netcat-traditional',
        'socat',
        
        # Network tools
        'proxychains',
        'tor',
        'torsocks',
        'macchanger',
        'aircrack-ng',
        'reaver',
        'hostapd',
        
        # Forensics tools
        'steghide',
        'exiftool',
        'binwalk',
        'foremost',
        'volatility',
        'autopsy',
        
        # Development tools
        'gcc',
        'g++',
        'make',
        'cmake',
        'gdb',
        'radare2',
        'ghidra',
        
        # Web tools
        'burpsuite',
        'zaproxy',
        'wfuzz',
        'ffuf',
        
        # Social engineering
        'set',
        'maltego',
        
        # Additional utilities
        'vim',
        'tmux',
        'screen',
        'htop',
        'tree',
        'jq'
    ]
    
    return '\n'.join(packages)

def create_preseed():
    """Create preseed configuration for automated installation"""
    
    preseed = '''# Wade CrewAI Kali Preseed Configuration

# Locale and keyboard
d-i debian-installer/locale string en_US.UTF-8
d-i keyboard-configuration/xkb-keymap select us

# Network configuration
d-i netcfg/choose_interface select auto
d-i netcfg/get_hostname string wade-kali
d-i netcfg/get_domain string local

# User configuration
d-i passwd/user-fullname string Wade User
d-i passwd/username string wade
d-i passwd/user-password password wade
d-i passwd/user-password-again password wade
d-i user-setup/allow-password-weak boolean true

# Partitioning
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true

# Package selection
tasksel tasksel/first multiselect standard, desktop
d-i pkgsel/include string kali-linux-default wade-crew-ai

# Boot loader
d-i grub-installer/only_debian boolean true
d-i grub-installer/bootdev string default

# Finish installation
d-i finish-install/reboot_in_progress note
'''
    
    return preseed

def create_build_script():
    """Create automated build script for Kali ISO"""
    
    build_script = '''#!/bin/bash
# Wade CrewAI Kali ISO Build Script

set -e

echo "Wade CrewAI Kali ISO Builder"
echo "==========================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root for ISO building"
   exit 1
fi

# Install live-build if not present
if ! command -v lb &> /dev/null; then
    echo "Installing live-build..."
    apt-get update
    apt-get install -y live-build
fi

# Create build directory
BUILD_DIR="/tmp/wade-kali-build"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Initialize live-build configuration
lb config \\
    --distribution kali-rolling \\
    --archive-areas "main contrib non-free" \\
    --architectures amd64 \\
    --linux-flavours amd64 \\
    --debian-installer live \\
    --bootappend-live "boot=live components username=wade hostname=wade-kali" \\
    --iso-application "Wade CrewAI Kali Linux" \\
    --iso-publisher "Wade CrewAI Project" \\
    --iso-volume "Wade-Kali-$(date +%Y%m%d)"

# Create directories
mkdir -p config/hooks/normal
mkdir -p config/package-lists
mkdir -p config/includes.chroot/tmp

# Copy Wade CrewAI files
cp -r /path/to/wade-crew-ai config/includes.chroot/tmp/

# Create package list
cat > config/package-lists/wade.list.chroot << 'EOF'
# Wade CrewAI Dependencies
python3
python3-pip
python3-venv
curl
wget
git
nodejs
npm
build-essential
libssl-dev
libffi-dev

# Penetration Testing Tools
nmap
metasploit-framework
sqlmap
nikto
dirb
gobuster
hydra
john
hashcat
wireshark
tcpdump
netcat-traditional
socat

# Network Tools
proxychains
tor
torsocks
macchanger
aircrack-ng

# Forensics Tools
steghide
exiftool
binwalk
foremost

# Development Tools
gcc
g++
make
cmake
gdb
radare2

# Additional Tools
vim
tmux
htop
tree
jq
EOF

# Create installation hook
cat > config/hooks/normal/01-install-wade.hook.chroot << 'HOOK_EOF'
#!/bin/bash
set -e

echo "Installing Wade CrewAI..."

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create Wade directories
mkdir -p /opt/wade-crew-ai
mkdir -p /home/wade/.wade

# Copy Wade files
if [ -d "/tmp/wade-crew-ai" ]; then
    cp -r /tmp/wade-crew-ai/* /opt/wade-crew-ai/
fi

# Set up Python environment
cd /opt/wade-crew-ai
python3 -m venv wade_env
source wade_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create wade command
cat > /usr/local/bin/wade << 'CMD_EOF'
#!/bin/bash
cd /opt/wade-crew-ai
source wade_env/bin/activate
python3 main.py "$@"
CMD_EOF

chmod +x /usr/local/bin/wade

# Create desktop entry
mkdir -p /usr/share/applications
cat > /usr/share/applications/wade-crew-ai.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=Wade CrewAI
Comment=Uncensored AI Assistant
Exec=wade --mode web
Icon=terminal
Terminal=false
Type=Application
Categories=Development;Security;
DESKTOP_EOF

# Set permissions
chown -R 1000:1000 /opt/wade-crew-ai
chown -R 1000:1000 /home/wade/.wade

echo "Wade CrewAI installation complete"
HOOK_EOF

chmod +x config/hooks/normal/01-install-wade.hook.chroot

# Build the ISO
echo "Building Wade CrewAI Kali ISO..."
lb build

# Move ISO to output directory
OUTPUT_DIR="/opt/wade-kali-iso"
mkdir -p $OUTPUT_DIR
mv *.iso $OUTPUT_DIR/
mv *.log $OUTPUT_DIR/

echo "Build complete!"
echo "ISO location: $OUTPUT_DIR"
ls -la $OUTPUT_DIR/
'''
    
    return build_script

def main():
    """Main integration function"""
    
    print("Wade CrewAI - Kali Linux Integration")
    print("===================================")
    
    # Create integration files
    integration_dir = Path("kali_integration")
    integration_dir.mkdir(exist_ok=True)
    
    # Create hook script
    hook_file = integration_dir / "01-install-wade-crew-ai.hook.chroot"
    with open(hook_file, 'w') as f:
        f.write(create_kali_hook())
    hook_file.chmod(0o755)
    
    # Create package list
    package_file = integration_dir / "wade-crew-ai.list.chroot"
    with open(package_file, 'w') as f:
        f.write(create_package_list())
    
    # Create preseed
    preseed_file = integration_dir / "wade.preseed"
    with open(preseed_file, 'w') as f:
        f.write(create_preseed())
    
    # Create build script
    build_file = integration_dir / "build_wade_kali.sh"
    with open(build_file, 'w') as f:
        f.write(create_build_script())
    build_file.chmod(0o755)
    
    # Create instructions
    instructions = f"""
Wade CrewAI Kali Integration Files Created
=========================================

Files created in {integration_dir}/:
- 01-install-wade-crew-ai.hook.chroot  (Installation hook)
- wade-crew-ai.list.chroot             (Package list)
- wade.preseed                         (Preseed configuration)
- build_wade_kali.sh                   (Build script)

To build Wade Kali ISO:
1. Copy these files to your Kali live-build directory
2. Run: sudo ./build_wade_kali.sh
3. Wait for build to complete
4. Boot from generated ISO

The resulting ISO will include:
- Wade CrewAI pre-installed
- All penetration testing tools
- Automatic Wade service startup
- Desktop integration
- Uncensored AI capabilities

Boot the ISO and Wade will be available at:
- Command line: wade
- Web interface: http://localhost:8080
- Desktop application: Wade CrewAI
"""
    
    instructions_file = integration_dir / "INTEGRATION_INSTRUCTIONS.txt"
    with open(instructions_file, 'w') as f:
        f.write(instructions)
    
    print(f"Integration files created in: {integration_dir}")
    print("\nFiles:")
    for file in integration_dir.iterdir():
        print(f"  - {file.name}")
    
    print(f"\nRead {instructions_file} for build instructions")

if __name__ == '__main__':
    main()