#!/bin/bash
# -*- coding: utf-8 -*-
"""
WADE Service Installer
Systemd/launchd integration for WADE services.
"""

set -e

# Configuration
WADE_USER="wade"
WADE_GROUP="wade"
WADE_HOME="/opt/wade"
WADE_CONFIG="/etc/wade"
WADE_LOGS="/var/log/wade"
WADE_DATA="/var/lib/wade"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v systemctl &> /dev/null; then
            OS="systemd"
        else
            OS="sysv"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        error "Unsupported operating system: $OSTYPE"
    fi
    log "Detected OS: $OS"
}

# Create user and group
create_user() {
    log "Creating WADE user and group..."

    if ! getent group "$WADE_GROUP" > /dev/null 2>&1; then
        groupadd --system "$WADE_GROUP"
        log "Created group: $WADE_GROUP"
    fi

    if ! getent passwd "$WADE_USER" > /dev/null 2>&1; then
        useradd --system --gid "$WADE_GROUP" --home-dir "$WADE_HOME" \
                --shell /bin/false --comment "WADE Service User" "$WADE_USER"
        log "Created user: $WADE_USER"
    fi
}

# Create directories
create_directories() {
    log "Creating WADE directories..."

    directories=("$WADE_HOME" "$WADE_CONFIG" "$WADE_LOGS" "$WADE_DATA")

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done

    # Set ownership
    chown -R "$WADE_USER:$WADE_GROUP" "$WADE_HOME" "$WADE_LOGS" "$WADE_DATA"
    chown -R root:root "$WADE_CONFIG"
    chmod 755 "$WADE_CONFIG"
    chmod 750 "$WADE_LOGS" "$WADE_DATA"
}

# Install systemd service
install_systemd_service() {
    log "Installing systemd service..."

    cat > /etc/systemd/system/wade.service << 'EOF'
[Unit]
Description=WADE - Weaponized Autonomous Deployment Engine
Documentation=https://github.com/wade/wade
After=network.target
Wants=network.target

[Service]
Type=notify
User=wade
Group=wade
WorkingDirectory=/opt/wade
ExecStart=/opt/wade/bin/wade --config /etc/wade/config.json
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/wade /var/log/wade
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Environment
Environment=WADE_CONFIG=/etc/wade/config.json
Environment=WADE_LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
EOF

    # Create wade-agent service
    cat > /etc/systemd/system/wade-agent.service << 'EOF'
[Unit]
Description=WADE Agent Service
Documentation=https://github.com/wade/wade
After=wade.service
Requires=wade.service

[Service]
Type=simple
User=wade
Group=wade
WorkingDirectory=/opt/wade
ExecStart=/opt/wade/bin/wade-agent --config /etc/wade/agent.json
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/wade /var/log/wade

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    log "Systemd services installed"
}

# Install macOS launchd service
install_launchd_service() {
    log "Installing launchd service..."

    cat > /Library/LaunchDaemons/com.wade.service.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wade.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/wade/bin/wade</string>
        <string>--config</string>
        <string>/etc/wade/config.json</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>UserName</key>
    <string>wade</string>
    <key>GroupName</key>
    <string>wade</string>
    <key>WorkingDirectory</key>
    <string>/opt/wade</string>
    <key>StandardOutPath</key>
    <string>/var/log/wade/wade.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/wade/wade.error.log</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

    # Set permissions
    chown root:wheel /Library/LaunchDaemons/com.wade.service.plist
    chmod 644 /Library/LaunchDaemons/com.wade.service.plist

    log "Launchd service installed"
}

# Install SysV init script
install_sysv_service() {
    log "Installing SysV init script..."

    cat > /etc/init.d/wade << 'EOF'
#!/bin/bash
# wade        WADE Service
# chkconfig: 35 80 20
# description: WADE - Weaponized Autonomous Deployment Engine

. /etc/rc.d/init.d/functions

USER="wade"
DAEMON="wade"
ROOT_DIR="/opt/wade"
LOCK_FILE="/var/lock/subsys/wade"

start() {
    if [ -f $LOCK_FILE ]; then
        echo "WADE is already running"
        return 1
    fi

    echo -n "Starting $DAEMON: "
    daemon --user "$USER" --pidfile="$LOCK_FILE" \
           "$ROOT_DIR/bin/wade" --config /etc/wade/config.json
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch $LOCK_FILE
    return $RETVAL
}

stop() {
    echo -n "Shutting down $DAEMON: "
    pid=`ps -aefw | grep "$DAEMON" | grep -v " grep " | awk '{print $2}'`
    kill -9 $pid > /dev/null 2>&1
    [ $? -eq 0 ] && echo_success || echo_failure
    echo
    rm -f $LOCK_FILE
}

restart() {
    stop
    start
}

status() {
    if [ -f $LOCK_FILE ]; then
        echo "$DAEMON is running."
    else
        echo "$DAEMON is stopped."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: {start|stop|status|restart}"
        exit 1
        ;;
esac

exit $?
EOF

    chmod +x /etc/init.d/wade

    # Enable service
    if command -v chkconfig &> /dev/null; then
        chkconfig --add wade
        chkconfig wade on
    elif command -v update-rc.d &> /dev/null; then
        update-rc.d wade defaults
    fi

    log "SysV init script installed"
}

# Create default configuration
create_default_config() {
    log "Creating default configuration..."

    cat > "$WADE_CONFIG/config.json" << 'EOF'
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "ssl": {
            "enabled": true,
            "cert_file": "/etc/wade/certs/server.crt",
            "key_file": "/etc/wade/certs/server.key"
        }
    },
    "security": {
        "encryption_key": "CHANGE_THIS_KEY",
        "session_timeout": 3600,
        "max_login_attempts": 5
    },
    "agents": {
        "max_concurrent": 10,
        "timeout": 300,
        "auto_restart": true
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/wade/wade.log",
        "max_size": "100MB",
        "backup_count": 5
    },
    "monitoring": {
        "enabled": true,
        "metrics_port": 9090,
        "health_check_interval": 30
    }
}
EOF

    cat > "$WADE_CONFIG/agent.json" << 'EOF'
{
    "agent": {
        "name": "default-agent",
        "type": "general",
        "max_tasks": 5
    },
    "communication": {
        "server_url": "https://localhost:8080",
        "ssl_verify": true,
        "timeout": 30
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/wade/agent.log"
    }
}
EOF

    # Set permissions
    chmod 640 "$WADE_CONFIG"/*.json
    chown root:"$WADE_GROUP" "$WADE_CONFIG"/*.json

    log "Default configuration created"
}

# Create log rotation configuration
create_logrotate_config() {
    log "Creating log rotation configuration..."

    cat > /etc/logrotate.d/wade << 'EOF'
/var/log/wade/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 wade wade
    postrotate
        if systemctl is-active --quiet wade; then
            systemctl reload wade
        fi
    endscript
}
EOF

    log "Log rotation configured"
}

# Enable and start services
enable_services() {
    log "Enabling and starting WADE services..."

    case "$OS" in
        "systemd")
            systemctl enable wade.service
            systemctl enable wade-agent.service
            systemctl start wade.service
            systemctl start wade-agent.service
            ;;
        "macos")
            launchctl load /Library/LaunchDaemons/com.wade.service.plist
            ;;
        "sysv")
            service wade start
            ;;
    esac

    log "WADE services enabled and started"
}

# Create uninstall script
create_uninstall_script() {
    log "Creating uninstall script..."

    cat > "$WADE_HOME/uninstall.sh" << 'EOF'
#!/bin/bash
# WADE Uninstall Script

set -e

echo "Stopping WADE services..."
if command -v systemctl &> /dev/null; then
    systemctl stop wade.service wade-agent.service || true
    systemctl disable wade.service wade-agent.service || true
    rm -f /etc/systemd/system/wade*.service
    systemctl daemon-reload
elif [[ "$OSTYPE" == "darwin"* ]]; then
    launchctl unload /Library/LaunchDaemons/com.wade.service.plist || true
    rm -f /Library/LaunchDaemons/com.wade.service.plist
else
    service wade stop || true
    chkconfig wade off || true
    rm -f /etc/init.d/wade
fi

echo "Removing WADE files..."
rm -rf /opt/wade
rm -rf /etc/wade
rm -rf /var/lib/wade
rm -rf /var/log/wade
rm -f /etc/logrotate.d/wade

echo "Removing WADE user..."
userdel wade || true
groupdel wade || true

echo "WADE uninstalled successfully"
EOF

    chmod +x "$WADE_HOME/uninstall.sh"
    chown root:root "$WADE_HOME/uninstall.sh"

    log "Uninstall script created at $WADE_HOME/uninstall.sh"
}

# Main installation function
main() {
    log "Starting WADE service installation..."

    check_root
    detect_os
    create_user
    create_directories

    case "$OS" in
        "systemd")
            install_systemd_service
            ;;
        "macos")
            install_launchd_service
            ;;
        "sysv")
            install_sysv_service
            ;;
    esac

    create_default_config
    create_logrotate_config
    create_uninstall_script

    log "WADE service installation completed successfully!"
    log "Configuration files are located in: $WADE_CONFIG"
    log "Log files will be written to: $WADE_LOGS"
    log "To uninstall, run: $WADE_HOME/uninstall.sh"

    warn "Please update the encryption key in $WADE_CONFIG/config.json before starting services"

    # Ask if user wants to start services now
    read -p "Do you want to start WADE services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        enable_services
        log "WADE is now running!"
    else
        log "To start WADE services later, run:"
        case "$OS" in
            "systemd")
                log "  systemctl start wade.service"
                log "  systemctl start wade-agent.service"
                ;;
            "macos")
                log "  launchctl load /Library/LaunchDaemons/com.wade.service.plist"
                ;;
            "sysv")
                log "  service wade start"
                ;;
        esac
    fi
}

# Run main function
main "$@"
