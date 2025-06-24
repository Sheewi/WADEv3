#!/bin/bash
# WADE Persistence Handler
# Ensures WADE's presence and privileges

# Default settings
WADE_ROOT="/WADE"
ENCRYPTED_MEMORY_SIZE="512M"
ENCRYPTED_MEMORY_PATH="/dev/shm/wade_secure"
LOG_FILE="${WADE_ROOT}/WADE_RUNTIME/logs/persistence.log"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
    
    if [ "$level" == "ERROR" ]; then
        echo "[${timestamp}] [${level}] ${message}" >&2
    else
        echo "[${timestamp}] [${level}] ${message}"
    fi
}

# Function to check privileges
check_privileges() {
    log_message "INFO" "Checking privileges..."
    
    if [ "$(id -u)" -ne 0 ]; then
        log_message "WARN" "WADE is not running as root. Functionality will be limited."
        return 1
    else
        log_message "INFO" "WADE is running with root privileges."
        return 0
    fi
}

# Function to mount encrypted memory
mount_encrypted_memory() {
    log_message "INFO" "Setting up encrypted memory at ${ENCRYPTED_MEMORY_PATH}..."
    
    # Check if already mounted
    if mount | grep -q "${ENCRYPTED_MEMORY_PATH}"; then
        log_message "INFO" "Encrypted memory already mounted."
        return 0
    fi
    
    # Create directory if it doesn't exist
    mkdir -p "${ENCRYPTED_MEMORY_PATH}"
    
    # Create encrypted memory
    if ! modprobe cryptoloop &>/dev/null; then
        log_message "WARN" "Failed to load cryptoloop module. Encrypted memory may not be available."
    fi
    
    # Create encrypted memory using tmpfs
    mount -t tmpfs -o size=${ENCRYPTED_MEMORY_SIZE},mode=0700 tmpfs "${ENCRYPTED_MEMORY_PATH}"
    
    if [ $? -eq 0 ]; then
        log_message "INFO" "Encrypted memory mounted successfully."
        return 0
    else
        log_message "ERROR" "Failed to mount encrypted memory."
        return 1
    fi
}

# Function to ensure WADE directories exist
ensure_directories() {
    log_message "INFO" "Ensuring WADE directories exist..."
    
    mkdir -p "${WADE_ROOT}/WADE_RUNTIME/temp"
    mkdir -p "${WADE_ROOT}/WADE_RUNTIME/logs"
    mkdir -p "${WADE_ROOT}/datasets"
    
    # Set permissions
    chmod -R 700 "${WADE_ROOT}/WADE_RUNTIME"
    
    log_message "INFO" "WADE directories created and secured."
}

# Function to install WADE as a service
install_service() {
    log_message "INFO" "Installing WADE as a service..."
    
    if [ "$(id -u)" -ne 0 ]; then
        log_message "ERROR" "Root privileges required to install service."
        return 1
    fi
    
    # Copy service file
    cp "${WADE_ROOT}/system/wade.service" /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable wade.service
    
    log_message "INFO" "WADE service installed successfully."
    log_message "INFO" "Start with: sudo systemctl start wade.service"
}

# Function to uninstall WADE service
uninstall_service() {
    log_message "INFO" "Uninstalling WADE service..."
    
    if [ "$(id -u)" -ne 0 ]; then
        log_message "ERROR" "Root privileges required to uninstall service."
        return 1
    fi
    
    # Stop service if running
    systemctl stop wade.service
    
    # Disable service
    systemctl disable wade.service
    
    # Remove service file
    rm -f /etc/systemd/system/wade.service
    
    # Reload systemd
    systemctl daemon-reload
    
    log_message "INFO" "WADE service uninstalled successfully."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check-privileges)
            check_privileges
            shift
            ;;
        --mount-encrypted-memory)
            mount_encrypted_memory
            shift
            ;;
        --ensure-directories)
            ensure_directories
            shift
            ;;
        --install-service)
            install_service
            shift
            ;;
        --uninstall-service)
            uninstall_service
            shift
            ;;
        --wade-root=*)
            WADE_ROOT="${1#*=}"
            shift
            ;;
        --encrypted-memory-size=*)
            ENCRYPTED_MEMORY_SIZE="${1#*=}"
            shift
            ;;
        *)
            log_message "ERROR" "Unknown option: $1"
            echo "Usage: $0 [--check-privileges] [--mount-encrypted-memory] [--ensure-directories] [--install-service] [--uninstall-service] [--wade-root=PATH] [--encrypted-memory-size=SIZE]"
            exit 1
            ;;
    esac
done

# If no arguments provided, run all functions
if [ $# -eq 0 ]; then
    check_privileges
    ensure_directories
    mount_encrypted_memory
fi

exit 0