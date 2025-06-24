# -*- coding: utf-8 -*-
"""
WADE Configuration Manager
Centralized configuration management with validation and hot-reloading.
"""

import os
import json
import yaml
import secrets
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError


class ConfigManager:
    """
    Centralized configuration manager for WADE.
    Handles configuration loading, validation, hot-reloading, and environment-specific settings.
    """
    
    def __init__(self, config_path: str = None, environment: str = None):
        """Initialize the configuration manager."""
        self.config_path = config_path or self._get_default_config_path()
        self.environment = environment or os.getenv('WADE_ENV', 'production')
        self.config = {}
        self.schema = self._get_config_schema()
        self.watchers = []
        self.reload_callbacks = []
        self.lock = threading.RLock()
        self.last_modified = 0
        self.watch_thread = None
        self.watching = False
        
        # Load initial configuration
        self.load_config()
        
        # Start file watching if enabled
        if self.get('config.hot_reload', True):
            self.start_watching()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Check environment variable first
        if 'WADE_CONFIG' in os.environ:
            return os.environ['WADE_CONFIG']
        
        # Check common locations
        locations = [
            '/etc/wade/config.json',
            '/etc/wade/config.yaml',
            './config.json',
            './config.yaml',
            os.path.expanduser('~/.wade/config.json'),
            os.path.expanduser('~/.wade/config.yaml')
        ]
        
        for location in locations:
            if os.path.exists(location):
                return location
        
        # Default to /etc/wade/config.json
        return '/etc/wade/config.json'
    
    def _get_config_schema(self) -> Dict:
        """Get JSON schema for configuration validation."""
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "ssl": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "cert_file": {"type": "string"},
                                "key_file": {"type": "string"}
                            },
                            "required": ["enabled"]
                        }
                    },
                    "required": ["host", "port"]
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "encryption_key": {"type": "string", "minLength": 32},
                        "session_timeout": {"type": "integer", "minimum": 300},
                        "max_login_attempts": {"type": "integer", "minimum": 1},
                        "lockout_duration": {"type": "integer", "minimum": 60}
                    },
                    "required": ["encryption_key"]
                },
                "agents": {
                    "type": "object",
                    "properties": {
                        "max_concurrent": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "integer", "minimum": 30},
                        "auto_restart": {"type": "boolean"},
                        "heartbeat_interval": {"type": "integer", "minimum": 5}
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                        "file": {"type": "string"},
                        "max_size": {"type": "string"},
                        "backup_count": {"type": "integer", "minimum": 1}
                    }
                },
                "monitoring": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "metrics_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "health_check_interval": {"type": "integer", "minimum": 10}
                    }
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["sqlite", "postgresql", "mysql"]},
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                        "name": {"type": "string"},
                        "user": {"type": "string"},
                        "password": {"type": "string"}
                    }
                }
            },
            "required": ["server", "security"]
        }
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "ssl": {
                    "enabled": True,
                    "cert_file": "/etc/wade/certs/server.crt",
                    "key_file": "/etc/wade/certs/server.key"
                }
            },
            "security": {
                "encryption_key": self._generate_encryption_key(),
                "session_timeout": 3600,
                "max_login_attempts": 5,
                "lockout_duration": 900
            },
            "agents": {
                "max_concurrent": 10,
                "timeout": 300,
                "auto_restart": True,
                "heartbeat_interval": 30
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/wade/wade.log",
                "max_size": "100MB",
                "backup_count": 5
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 9090,
                "health_check_interval": 30
            },
            "database": {
                "type": "sqlite",
                "name": "/var/lib/wade/wade.db"
            },
            "config": {
                "hot_reload": True,
                "backup_on_change": True,
                "validation_strict": True
            },
            "features": {
                "evolution_engine": True,
                "auto_learning": True,
                "plugin_system": True
            },
            "limits": {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80,
                "max_disk_usage_percent": 90
            }
        }
    
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key."""
        return secrets.token_hex(32)
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with self.lock:
                if not os.path.exists(self.config_path):
                    # Create default configuration
                    self.config = self._get_default_config()
                    self.save_config()
                    print(f"Created default configuration at {self.config_path}")
                    return True
                
                # Load configuration file
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        self.config = yaml.safe_load(f)
                    else:
                        self.config = json.load(f)
                
                # Merge with defaults for missing keys
                default_config = self._get_default_config()
                self.config = self._merge_configs(default_config, self.config)
                
                # Apply environment-specific overrides
                self._apply_environment_overrides()
                
                # Validate configuration
                if self.get('config.validation_strict', True):
                    self.validate_config()
                
                # Update last modified time
                self.last_modified = os.path.getmtime(self.config_path)
                
                print(f"Configuration loaded from {self.config_path}")
                return True
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Fall back to default configuration
            self.config = self._get_default_config()
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self.lock:
                # Create backup if enabled
                if self.get('config.backup_on_change', True):
                    self._backup_config()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Save configuration
                with open(self.config_path, 'w') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        yaml.dump(self.config, f, default_flow_style=False, indent=2)
                    else:
                        json.dump(self.config, f, indent=2)
                
                # Update last modified time
                self.last_modified = os.path.getmtime(self.config_path)
                
                print(f"Configuration saved to {self.config_path}")
                return True
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def _backup_config(self):
        """Create a backup of the current configuration."""
        try:
            if os.path.exists(self.config_path):
                backup_dir = os.path.join(os.path.dirname(self.config_path), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"config_backup_{timestamp}.json"
                backup_path = os.path.join(backup_dir, backup_name)
                
                import shutil
                shutil.copy2(self.config_path, backup_path)
                
        except Exception as e:
            print(f"Error creating config backup: {e}")
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries."""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides."""
        env_config_path = self.config_path.replace('.json', f'.{self.environment}.json')
        env_config_path = env_config_path.replace('.yaml', f'.{self.environment}.yaml')
        
        if os.path.exists(env_config_path):
            try:
                with open(env_config_path, 'r') as f:
                    if env_config_path.endswith('.yaml') or env_config_path.endswith('.yml'):
                        env_config = yaml.safe_load(f)
                    else:
                        env_config = json.load(f)
                
                self.config = self._merge_configs(self.config, env_config)
                print(f"Applied environment overrides from {env_config_path}")
                
            except Exception as e:
                print(f"Error loading environment config: {e}")
        
        # Apply environment variables
        self._apply_env_variables()
    
    def _apply_env_variables(self):
        """Apply environment variable overrides."""
        env_mappings = {
            'WADE_HOST': 'server.host',
            'WADE_PORT': 'server.port',
            'WADE_SSL_ENABLED': 'server.ssl.enabled',
            'WADE_LOG_LEVEL': 'logging.level',
            'WADE_MAX_AGENTS': 'agents.max_concurrent',
            'WADE_SESSION_TIMEOUT': 'security.session_timeout',
            'WADE_ENCRYPTION_KEY': 'security.encryption_key'
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if config_path.endswith('.port') or config_path.endswith('.timeout') or config_path.endswith('.max_concurrent'):
                    value = int(value)
                elif config_path.endswith('.enabled'):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self.set(config_path, value)
    
    def validate_config(self) -> bool:
        """
        Validate configuration against schema.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            validate(instance=self.config, schema=self.schema)
            return True
        except ValidationError as e:
            print(f"Configuration validation error: {e.message}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'server.port')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        with self.lock:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'server.port')
            value: Value to set
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            with self.lock:
                keys = key.split('.')
                config = self.config
                
                # Navigate to parent
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                # Set value
                config[keys[-1]] = value
                
                # Validate if strict mode is enabled
                if self.get('config.validation_strict', True):
                    if not self.validate_config():
                        # Revert change
                        self.load_config()
                        return False
                
                # Notify watchers
                self._notify_watchers(key, value)
                
                return True
                
        except Exception as e:
            print(f"Error setting configuration: {e}")
            return False
    
    def update(self, updates: Dict) -> bool:
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if all updates successful, False otherwise
        """
        try:
            with self.lock:
                # Store original config for rollback
                original_config = json.loads(json.dumps(self.config))
                
                # Apply updates
                for key, value in updates.items():
                    if not self.set(key, value):
                        # Rollback on failure
                        self.config = original_config
                        return False
                
                return True
                
        except Exception as e:
            print(f"Error updating configuration: {e}")
            return False
    
    def reload(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reloaded successfully, False otherwise
        """
        old_config = json.loads(json.dumps(self.config))
        
        if self.load_config():
            # Notify reload callbacks
            for callback in self.reload_callbacks:
                try:
                    callback(old_config, self.config)
                except Exception as e:
                    print(f"Error in reload callback: {e}")
            
            return True
        
        return False
    
    def start_watching(self):
        """Start watching configuration file for changes."""
        if self.watching:
            return
        
        self.watching = True
        self.watch_thread = threading.Thread(target=self._watch_file, daemon=True)
        self.watch_thread.start()
        print("Started configuration file watching")
    
    def stop_watching(self):
        """Stop watching configuration file for changes."""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=5)
        print("Stopped configuration file watching")
    
    def _watch_file(self):
        """Background thread to watch for file changes."""
        while self.watching:
            try:
                if os.path.exists(self.config_path):
                    current_mtime = os.path.getmtime(self.config_path)
                    
                    if current_mtime > self.last_modified:
                        print("Configuration file changed, reloading...")
                        self.reload()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error watching configuration file: {e}")
                time.sleep(5)  # Wait longer on error
    
    def add_watcher(self, key: str, callback: Callable[[str, Any], None]):
        """
        Add a watcher for configuration changes.
        
        Args:
            key: Configuration key to watch
            callback: Function to call when key changes
        """
        self.watchers.append((key, callback))
    
    def remove_watcher(self, key: str, callback: Callable[[str, Any], None]):
        """
        Remove a configuration watcher.
        
        Args:
            key: Configuration key
            callback: Callback function to remove
        """
        self.watchers = [(k, c) for k, c in self.watchers if not (k == key and c == callback)]
    
    def add_reload_callback(self, callback: Callable[[Dict, Dict], None]):
        """
        Add a callback for configuration reloads.
        
        Args:
            callback: Function to call on reload (old_config, new_config)
        """
        self.reload_callbacks.append(callback)
    
    def _notify_watchers(self, key: str, value: Any):
        """Notify watchers of configuration changes."""
        for watch_key, callback in self.watchers:
            if key == watch_key or key.startswith(f"{watch_key}."):
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"Error in watcher callback: {e}")
    
    def get_all(self) -> Dict:
        """
        Get all configuration values.
        
        Returns:
            Complete configuration dictionary
        """
        with self.lock:
            return json.loads(json.dumps(self.config))
    
    def get_section(self, section: str) -> Dict:
        """
        Get a configuration section.
        
        Args:
            section: Section name (e.g., 'server', 'security')
            
        Returns:
            Section configuration dictionary
        """
        return self.get(section, {})
    
    def has_key(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key
            
        Returns:
            True if key exists, False otherwise
        """
        return self.get(key) is not None
    
    def delete_key(self, key: str) -> bool:
        """
        Delete a configuration key.
        
        Args:
            key: Configuration key to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self.lock:
                keys = key.split('.')
                config = self.config
                
                # Navigate to parent
                for k in keys[:-1]:
                    if k not in config:
                        return False
                    config = config[k]
                
                # Delete key
                if keys[-1] in config:
                    del config[keys[-1]]
                    return True
                
                return False
                
        except Exception as e:
            print(f"Error deleting configuration key: {e}")
            return False
    
    def export_config(self, format: str = 'json') -> str:
        """
        Export configuration in specified format.
        
        Args:
            format: Export format ('json' or 'yaml')
            
        Returns:
            Configuration as string
        """
        try:
            with self.lock:
                if format.lower() == 'yaml':
                    return yaml.dump(self.config, default_flow_style=False, indent=2)
                else:
                    return json.dumps(self.config, indent=2)
                    
        except Exception as e:
            return f"Error exporting configuration: {e}"
    
    def import_config(self, config_str: str, format: str = 'json') -> bool:
        """
        Import configuration from string.
        
        Args:
            config_str: Configuration as string
            format: Import format ('json' or 'yaml')
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with self.lock:
                if format.lower() == 'yaml':
                    new_config = yaml.safe_load(config_str)
                else:
                    new_config = json.loads(config_str)
                
                # Validate new configuration
                old_config = self.config
                self.config = new_config
                
                if self.get('config.validation_strict', True):
                    if not self.validate_config():
                        self.config = old_config
                        return False
                
                return True
                
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False