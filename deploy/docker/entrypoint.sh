#!/bin/bash
# WADE Docker Entrypoint Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    log "Waiting for $service_name at $host:$port..."
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "$service_name is ready!"
            return 0
        fi
        sleep 1
    done
    
    error "$service_name is not available after ${timeout}s"
}

# Function to check environment variables
check_env_vars() {
    log "Checking environment variables..."
    
    # Required environment variables
    local required_vars=(
        "WADE_HOME"
        "WADE_CONFIG"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
        fi
    done
    
    log "Environment variables check passed"
}

# Function to setup directories
setup_directories() {
    log "Setting up directories..."
    
    local directories=(
        "/var/log/wade"
        "/var/lib/wade"
        "/var/run/wade"
        "/tmp/wade"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set permissions
    chmod 755 /var/log/wade /var/lib/wade /var/run/wade /tmp/wade
    
    log "Directory setup completed"
}

# Function to setup configuration
setup_config() {
    log "Setting up configuration..."
    
    # Check if config file exists
    if [[ ! -f "$WADE_CONFIG" ]]; then
        warn "Configuration file not found at $WADE_CONFIG"
        
        # Copy default config if available
        local default_config="/etc/wade/config.default.json"
        if [[ -f "$default_config" ]]; then
            cp "$default_config" "$WADE_CONFIG"
            log "Copied default configuration to $WADE_CONFIG"
        else
            error "No configuration file found and no default available"
        fi
    fi
    
    # Validate configuration
    if ! python -c "import json; json.load(open('$WADE_CONFIG'))" 2>/dev/null; then
        error "Invalid JSON in configuration file: $WADE_CONFIG"
    fi
    
    log "Configuration setup completed"
}

# Function to setup database
setup_database() {
    log "Setting up database..."
    
    # Check if database configuration exists
    if python -c "
import json
config = json.load(open('$WADE_CONFIG'))
db_config = config.get('database', {})
if db_config.get('type') == 'postgresql':
    print('postgresql')
elif db_config.get('type') == 'mysql':
    print('mysql')
else:
    print('sqlite')
" | grep -q "postgresql"; then
        
        # PostgreSQL setup
        local db_host=$(python -c "
import json
config = json.load(open('$WADE_CONFIG'))
print(config.get('database', {}).get('host', 'localhost'))
")
        local db_port=$(python -c "
import json
config = json.load(open('$WADE_CONFIG'))
print(config.get('database', {}).get('port', 5432))
")
        
        wait_for_service "$db_host" "$db_port" "PostgreSQL" 60
        
    elif python -c "
import json
config = json.load(open('$WADE_CONFIG'))
print(config.get('database', {}).get('type', 'sqlite'))
" | grep -q "mysql"; then
        
        # MySQL setup
        local db_host=$(python -c "
import json
config = json.load(open('$WADE_CONFIG'))
print(config.get('database', {}).get('host', 'localhost'))
")
        local db_port=$(python -c "
import json
config = json.load(open('$WADE_CONFIG'))
print(config.get('database', {}).get('port', 3306))
")
        
        wait_for_service "$db_host" "$db_port" "MySQL" 60
    fi
    
    log "Database setup completed"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # This would run actual database migrations
    # For now, just create necessary tables
    python -c "
import sys
sys.path.insert(0, '/opt/wade')
from system.monitor import SystemMonitor
from system.backup_manager import BackupManager

# Initialize database schemas
try:
    monitor = SystemMonitor()
    backup_manager = BackupManager()
    print('Database schemas initialized')
except Exception as e:
    print(f'Error initializing database schemas: {e}')
    sys.exit(1)
"
    
    log "Database migrations completed"
}

# Function to setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    local cert_dir="/etc/wade/certs"
    
    if [[ ! -d "$cert_dir" ]]; then
        mkdir -p "$cert_dir"
    fi
    
    # Check if certificates exist
    if [[ ! -f "$cert_dir/server.crt" ]] || [[ ! -f "$cert_dir/server.key" ]]; then
        log "Generating self-signed certificates..."
        
        python -c "
import sys
sys.path.insert(0, '/opt/wade')
from security.cert_handler import CertificateHandler

cert_handler = CertificateHandler(cert_dir='$cert_dir')
success = cert_handler.create_server_certificate('wade.local')
if success:
    print('SSL certificates generated successfully')
else:
    print('Failed to generate SSL certificates')
    sys.exit(1)
"
    fi
    
    log "SSL setup completed"
}

# Function to setup logging
setup_logging() {
    log "Setting up logging..."
    
    # Create log files
    touch /var/log/wade/wade.log
    touch /var/log/wade/error.log
    touch /var/log/wade/security.log
    touch /var/log/wade/audit.log
    
    # Set permissions
    chmod 644 /var/log/wade/*.log
    
    log "Logging setup completed"
}

# Function to validate system requirements
validate_system() {
    log "Validating system requirements..."
    
    # Check Python version
    local python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log "Python version: $python_version"
    
    # Check available memory
    local memory_mb=$(python -c "
import psutil
print(int(psutil.virtual_memory().total / 1024 / 1024))
")
    log "Available memory: ${memory_mb}MB"
    
    if [[ $memory_mb -lt 512 ]]; then
        warn "Low memory detected: ${memory_mb}MB (recommended: 512MB+)"
    fi
    
    # Check disk space
    local disk_gb=$(df /var/lib/wade | tail -1 | awk '{print int($4/1024/1024)}')
    log "Available disk space: ${disk_gb}GB"
    
    if [[ $disk_gb -lt 1 ]]; then
        warn "Low disk space detected: ${disk_gb}GB (recommended: 1GB+)"
    fi
    
    log "System validation completed"
}

# Function to start WADE services
start_wade() {
    log "Starting WADE services..."
    
    # Start bootloader if requested
    if [[ "$1" == "bootloader" ]]; then
        log "Starting WADE bootloader..."
        exec python -m interface.bootloader --config "$WADE_CONFIG"
    fi
    
    # Start specific service if requested
    case "$1" in
        "monitor")
            log "Starting monitoring service..."
            exec python -c "
import sys
sys.path.insert(0, '/opt/wade')
from system.monitor import SystemMonitor
import json

config = json.load(open('$WADE_CONFIG'))
monitor_config = config.get('monitoring', {})
monitor = SystemMonitor(config=monitor_config)
monitor.start_monitoring()

try:
    import signal
    signal.pause()
except KeyboardInterrupt:
    monitor.stop_monitoring()
"
            ;;
        "backup")
            log "Starting backup service..."
            exec python -c "
import sys
sys.path.insert(0, '/opt/wade')
from system.backup_manager import BackupManager
import json

config = json.load(open('$WADE_CONFIG'))
backup_config = config.get('backup', {})
backup_manager = BackupManager(config=backup_config)
backup_manager.start_scheduled_backups()

try:
    import signal
    signal.pause()
except KeyboardInterrupt:
    backup_manager.stop_scheduled_backups()
"
            ;;
        "dashboard")
            log "Starting cyber dashboard..."
            exec python -m interface.cyber_dashboard --config "$WADE_CONFIG"
            ;;
        *)
            log "Starting main WADE application..."
            exec python -m WADE_CORE.main --config "$WADE_CONFIG"
            ;;
    esac
}

# Main execution
main() {
    log "WADE Docker Container Starting..."
    log "Version: ${VERSION:-unknown}"
    log "Build Date: ${BUILD_DATE:-unknown}"
    log "VCS Ref: ${VCS_REF:-unknown}"
    
    # Perform startup checks
    check_env_vars
    setup_directories
    setup_config
    setup_database
    run_migrations
    setup_ssl
    setup_logging
    validate_system
    
    log "Startup checks completed successfully"
    
    # Handle special commands
    case "$1" in
        "bash"|"sh")
            log "Starting interactive shell..."
            exec /bin/bash
            ;;
        "test")
            log "Running tests..."
            exec python -m pytest tests/ -v
            ;;
        "version")
            echo "WADE Version: ${VERSION:-unknown}"
            exit 0
            ;;
        "help")
            echo "WADE Docker Container"
            echo ""
            echo "Usage: docker run wade [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  wade          Start main WADE application (default)"
            echo "  bootloader    Start WADE bootloader"
            echo "  monitor       Start monitoring service only"
            echo "  backup        Start backup service only"
            echo "  dashboard     Start cyber dashboard"
            echo "  test          Run test suite"
            echo "  bash          Start interactive shell"
            echo "  version       Show version information"
            echo "  help          Show this help message"
            exit 0
            ;;
    esac
    
    # Start WADE
    start_wade "$@"
}

# Handle signals
trap 'log "Received SIGTERM, shutting down..."; exit 0' TERM
trap 'log "Received SIGINT, shutting down..."; exit 0' INT

# Run main function
main "$@"