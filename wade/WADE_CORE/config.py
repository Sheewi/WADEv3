# -*- coding: utf-8 -*-
"""
WADE Configuration Manager
Manages configuration for WADE.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional


class ConfigManager:
    """
    Configuration Manager for WADE.
    Manages loading, saving, and accessing configuration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger("wade.config")

        # Set default config path
        if config_path:
            self.config_path = os.path.abspath(config_path)
        else:
            self.config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "config.json"
            )

        # Load configuration
        self.config = self._load_config()

        # Set up environment variables
        self._setup_environment()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dictionary with configuration
        """
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            self.logger.info(f"Configuration loaded from {self.config_path}")
            return config

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

            # Return default configuration
            return {
                "version": "1.0.0",
                "system": {
                    "name": "WADE",
                    "description": "Weaponized Autonomous Deployment Engine",
                    "debug_mode": False,
                    "log_level": "INFO",
                },
                "paths": {
                    "runtime_dir": "../WADE_RUNTIME",
                    "logs_dir": "../WADE_RUNTIME/logs",
                    "temp_dir": "../WADE_RUNTIME/temp",
                    "data_dir": "../datasets",
                    "config_dir": ".",
                },
            }

    def _setup_environment(self):
        """Set up environment variables from configuration."""
        # Set WADE_HOME
        os.environ["WADE_HOME"] = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Set WADE_CONFIG
        os.environ["WADE_CONFIG"] = self.config_path

        # Set WADE_RUNTIME
        runtime_dir = self.get("paths", {}).get("runtime_dir", "../WADE_RUNTIME")
        os.environ["WADE_RUNTIME"] = os.path.abspath(
            os.path.join(os.path.dirname(self.config_path), runtime_dir)
        )

        # Set WADE_LOGS
        logs_dir = self.get("paths", {}).get("logs_dir", "../WADE_RUNTIME/logs")
        os.environ["WADE_LOGS"] = os.path.abspath(
            os.path.join(os.path.dirname(self.config_path), logs_dir)
        )

        # Set WADE_TEMP
        temp_dir = self.get("paths", {}).get("temp_dir", "../WADE_RUNTIME/temp")
        os.environ["WADE_TEMP"] = os.path.abspath(
            os.path.join(os.path.dirname(self.config_path), temp_dir)
        )

        # Set WADE_DATA
        data_dir = self.get("paths", {}).get("data_dir", "../datasets")
        os.environ["WADE_DATA"] = os.path.abspath(
            os.path.join(os.path.dirname(self.config_path), data_dir)
        )

    def get(self, section: str, default: Any = None) -> Any:
        """
        Get a configuration section.

        Args:
            section: Section name
            default: Default value if section not found

        Returns:
            Configuration section or default value
        """
        return self.config.get(section, default)

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: Section name
            key: Key name
            default: Default value if key not found

        Returns:
            Configuration value or default value
        """
        section_data = self.config.get(section, {})
        return section_data.get(key, default)

    def set_value(self, section: str, key: str, value: Any):
        """
        Set a configuration value.

        Args:
            section: Section name
            key: Key name
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)

            self.logger.info(f"Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._setup_environment()

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration.

        Returns:
            Dictionary with entire configuration
        """
        return self.config
