#!/bin/bash
# WADE Docker Health Check Script

set -e

# Configuration
HEALTH_CHECK_URL="http://localhost:8080/health"
METRICS_URL="http://localhost:9090/metrics"
TIMEOUT=10
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[HEALTH] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[HEALTH] WARNING: $1${NC}" >&2
}

error() {
    echo -e "${RED}[HEALTH] ERROR: $1${NC}" >&2
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    log "Checking $description at $url"
    
    local response
    local status_code
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        if response=$(curl -s -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null); then
            status_code="${response: -3}"
            response_body="${response%???}"
            
            if [[ "$status_code" == "$expected_status" ]]; then
                log "$description is healthy (HTTP $status_code)"
                return 0
            else
                warn "$description returned HTTP $status_code (expected $expected_status)"
            fi
        else
            warn "$description check failed (attempt $attempt/$MAX_RETRIES)"
        fi
        
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            sleep 2
        fi
    done
    
    error "$description is unhealthy after $MAX_RETRIES attempts"
    return 1
}

# Function to check process
check_process() {
    local process_name=$1
    local description=$2
    
    log "Checking $description process"
    
    if pgrep -f "$process_name" > /dev/null; then
        log "$description process is running"
        return 0
    else
        error "$description process is not running"
        return 1
    fi
}

# Function to check file system
check_filesystem() {
    log "Checking file system health"
    
    # Check critical directories
    local directories=(
        "/var/log/wade"
        "/var/lib/wade"
        "/var/run/wade"
        "/tmp/wade"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error "Critical directory missing: $dir"
            return 1
        fi
        
        if [[ ! -w "$dir" ]]; then
            error "Critical directory not writable: $dir"
            return 1
        fi
    done
    
    # Check disk space
    local disk_usage
    disk_usage=$(df /var/lib/wade | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt 90 ]]; then
        error "Disk usage too high: ${disk_usage}%"
        return 1
    elif [[ $disk_usage -gt 80 ]]; then
        warn "Disk usage high: ${disk_usage}%"
    fi
    
    log "File system is healthy"
    return 0
}

# Function to check memory usage
check_memory() {
    log "Checking memory usage"
    
    local memory_usage
    memory_usage=$(python3 -c "
import psutil
mem = psutil.virtual_memory()
print(int(mem.percent))
" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        warn "Could not check memory usage"
        return 0
    fi
    
    if [[ $memory_usage -gt 95 ]]; then
        error "Memory usage critical: ${memory_usage}%"
        return 1
    elif [[ $memory_usage -gt 85 ]]; then
        warn "Memory usage high: ${memory_usage}%"
    fi
    
    log "Memory usage is acceptable: ${memory_usage}%"
    return 0
}

# Function to check configuration
check_configuration() {
    log "Checking configuration"
    
    local config_file="${WADE_CONFIG:-/etc/wade/config.json}"
    
    if [[ ! -f "$config_file" ]]; then
        error "Configuration file not found: $config_file"
        return 1
    fi
    
    # Validate JSON
    if ! python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
        error "Invalid JSON in configuration file: $config_file"
        return 1
    fi
    
    log "Configuration is valid"
    return 0
}

# Function to check database connectivity
check_database() {
    log "Checking database connectivity"
    
    local config_file="${WADE_CONFIG:-/etc/wade/config.json}"
    
    if [[ ! -f "$config_file" ]]; then
        warn "Configuration file not found, skipping database check"
        return 0
    fi
    
    local db_type
    db_type=$(python3 -c "
import json
try:
    config = json.load(open('$config_file'))
    print(config.get('database', {}).get('type', 'sqlite'))
except:
    print('sqlite')
" 2>/dev/null)
    
    case "$db_type" in
        "postgresql")
            local db_host db_port db_name db_user
            db_host=$(python3 -c "
import json
config = json.load(open('$config_file'))
print(config.get('database', {}).get('host', 'localhost'))
" 2>/dev/null)
            db_port=$(python3 -c "
import json
config = json.load(open('$config_file'))
print(config.get('database', {}).get('port', 5432))
" 2>/dev/null)
            
            if command -v pg_isready >/dev/null 2>&1; then
                if pg_isready -h "$db_host" -p "$db_port" -t $TIMEOUT >/dev/null 2>&1; then
                    log "PostgreSQL database is accessible"
                else
                    error "PostgreSQL database is not accessible"
                    return 1
                fi
            else
                warn "pg_isready not available, skipping PostgreSQL check"
            fi
            ;;
        "mysql")
            warn "MySQL health check not implemented"
            ;;
        "sqlite")
            local db_path
            db_path=$(python3 -c "
import json
config = json.load(open('$config_file'))
print(config.get('database', {}).get('name', '/var/lib/wade/wade.db'))
" 2>/dev/null)
            
            if [[ -f "$db_path" ]]; then
                log "SQLite database file exists"
            else
                warn "SQLite database file not found: $db_path"
            fi
            ;;
    esac
    
    return 0
}

# Function to check SSL certificates
check_ssl() {
    log "Checking SSL certificates"
    
    local cert_dir="/etc/wade/certs"
    local server_cert="$cert_dir/server.crt"
    local server_key="$cert_dir/server.key"
    
    if [[ ! -f "$server_cert" ]]; then
        warn "Server certificate not found: $server_cert"
        return 0
    fi
    
    if [[ ! -f "$server_key" ]]; then
        warn "Server private key not found: $server_key"
        return 0
    fi
    
    # Check certificate expiry
    local expiry_date
    if command -v openssl >/dev/null 2>&1; then
        expiry_date=$(openssl x509 -in "$server_cert" -noout -enddate 2>/dev/null | cut -d= -f2)
        if [[ -n "$expiry_date" ]]; then
            local expiry_epoch
            expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
            local current_epoch
            current_epoch=$(date +%s)
            local days_until_expiry
            days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [[ $days_until_expiry -lt 0 ]]; then
                error "SSL certificate has expired"
                return 1
            elif [[ $days_until_expiry -lt 30 ]]; then
                warn "SSL certificate expires in $days_until_expiry days"
            else
                log "SSL certificate is valid (expires in $days_until_expiry days)"
            fi
        fi
    else
        warn "OpenSSL not available, skipping certificate expiry check"
    fi
    
    return 0
}

# Function to perform comprehensive health check
comprehensive_health_check() {
    log "Starting comprehensive health check"
    
    local checks_passed=0
    local total_checks=0
    
    # Configuration check
    ((total_checks++))
    if check_configuration; then
        ((checks_passed++))
    fi
    
    # File system check
    ((total_checks++))
    if check_filesystem; then
        ((checks_passed++))
    fi
    
    # Memory check
    ((total_checks++))
    if check_memory; then
        ((checks_passed++))
    fi
    
    # Database check
    ((total_checks++))
    if check_database; then
        ((checks_passed++))
    fi
    
    # SSL check
    ((total_checks++))
    if check_ssl; then
        ((checks_passed++))
    fi
    
    # Process check (if not running in standalone mode)
    if [[ -z "$HEALTH_CHECK_STANDALONE" ]]; then
        ((total_checks++))
        if check_process "python.*wade" "WADE main"; then
            ((checks_passed++))
        fi
    fi
    
    # HTTP endpoint checks (if not running in standalone mode)
    if [[ -z "$HEALTH_CHECK_STANDALONE" ]]; then
        # Main application health endpoint
        ((total_checks++))
        if check_http_endpoint "$HEALTH_CHECK_URL" "Main application health"; then
            ((checks_passed++))
        fi
        
        # Metrics endpoint
        ((total_checks++))
        if check_http_endpoint "$METRICS_URL" "Metrics endpoint"; then
            ((checks_passed++))
        fi
    fi
    
    # Calculate health percentage
    local health_percentage
    health_percentage=$(( (checks_passed * 100) / total_checks ))
    
    log "Health check completed: $checks_passed/$total_checks checks passed ($health_percentage%)"
    
    # Determine overall health status
    if [[ $health_percentage -eq 100 ]]; then
        log "System is healthy"
        return 0
    elif [[ $health_percentage -ge 80 ]]; then
        warn "System is degraded but functional"
        return 0
    else
        error "System is unhealthy"
        return 1
    fi
}

# Main execution
main() {
    case "${1:-comprehensive}" in
        "quick")
            log "Running quick health check"
            check_http_endpoint "$HEALTH_CHECK_URL" "Quick health check"
            ;;
        "process")
            check_process "python.*wade" "WADE process"
            ;;
        "config")
            check_configuration
            ;;
        "filesystem")
            check_filesystem
            ;;
        "memory")
            check_memory
            ;;
        "database")
            check_database
            ;;
        "ssl")
            check_ssl
            ;;
        "comprehensive"|*)
            comprehensive_health_check
            ;;
    esac
}

# Run main function
main "$@"