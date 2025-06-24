# Simple Wade - Phind with OpenHands for Kali Linux

This project provides a simple integration of the Phind-CodeLlama model with OpenHands for Kali Linux. It creates a desktop application that allows you to interact with the LLM locally.

## Features

- Local LLM using Ollama and Phind-CodeLlama
- Simple web-based interface
- Pre-installed in the custom Kali ISO
- No GPU required (though performance will be better with one)

## Files in this Repository

- `setup-simple.sh`: Script to install Simple Wade on an existing Kali Linux system
- `01-install-simple-wade.chroot`: Hook script for Kali ISO build process
- `simple-wade.list.chroot`: Package list for Kali ISO build
- `kali-iso-integration.md`: Detailed instructions for creating a custom Kali ISO
- `README.md`: This file

## Creating a Custom Kali ISO

Follow these steps to create a custom Kali Linux ISO with Simple Wade pre-installed:

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
   cp /path/to/simple-wade/01-install-simple-wade.chroot kali-config/common/hooks/live/
   chmod +x kali-config/common/hooks/live/01-install-simple-wade.chroot
   ```

5. Copy the package list:
   ```bash
   cp /path/to/simple-wade/simple-wade.list.chroot kali-config/variant-default/package-lists/
   ```

6. Build the ISO:
   ```bash
   ./build.sh --distribution kali-rolling --verbose
   ```

The build process may take several hours depending on your system. Once complete, you'll find the ISO in the `images` directory.

## Installing on an Existing System

If you already have Kali Linux installed and just want to add Simple Wade:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/simple-wade.git
   ```

2. Run the setup script:
   ```bash
   cd simple-wade
   chmod +x setup-simple.sh
   ./setup-simple.sh
   ```

3. Start Simple Wade:
   ```bash
   simple-wade
   ```

## Usage

1. Start Simple Wade from the application menu or by running `simple-wade` in a terminal
2. The web interface will open in your browser
3. Type your queries in the input field and press Enter or click Send
4. The LLM will process your query and display the response

## Notes

- The Phind-CodeLlama model will be downloaded during the first boot, which may take some time depending on your internet connection
- Performance will depend on your system's CPU and RAM
- At least 8GB of RAM is recommended, 16GB or more is ideal
- The web interface runs locally on port 8080

## Customization

You can customize Simple Wade by editing the files in `~/.simple-wade/web/`. For example:

- Modify `index.html` to change the appearance
- Edit `app.py` to add new features to the backend
- Change the model by editing the `launch.sh` script

## License

This project is licensed under the MIT License.