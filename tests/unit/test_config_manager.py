# -*- coding: utf-8 -*-
"""
Unit tests for ConfigManager.
"""

import pytest
import os
import json
import tempfile
import time
from unittest.mock import patch, mock_open

from WADE_CORE.config_manager import ConfigManager


@pytest.mark.unit
class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_init_with_default_config(self, temp_dir):
        """Test initialization with default configuration."""
        config_path = os.path.join(temp_dir, "config.json")
        manager = ConfigManager(config_path=config_path)
        
        assert manager.config_path == config_path
        assert manager.environment == "production"
        assert isinstance(manager.config, dict)
        assert "server" in manager.config
        assert "security" in manager.config
    
    def test_init_with_custom_environment(self, temp_dir):
        """Test initialization with custom environment."""
        config_path = os.path.join(temp_dir, "config.json")
        manager = ConfigManager(config_path=config_path, environment="test")
        
        assert manager.environment == "test"
    
    def test_load_nonexistent_config_creates_default(self, temp_dir):
        """Test that loading non-existent config creates default."""
        config_path = os.path.join(temp_dir, "new_config.json")
        manager = ConfigManager(config_path=config_path)
        
        assert os.path.exists(config_path)
        assert manager.get("server.host") is not None
        assert manager.get("security.encryption_key") is not None
    
    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        config_path = os.path.join(temp_dir, "test_config.json")
        manager = ConfigManager(config_path=config_path)
        
        # Modify config
        manager.set("server.port", 9090)
        manager.set("test.value", "test_data")
        
        # Save config
        assert manager.save_config()
        
        # Create new manager and load
        manager2 = ConfigManager(config_path=config_path)
        
        assert manager2.get("server.port") == 9090
        assert manager2.get("test.value") == "test_data"
    
    def test_get_configuration_values(self, config_manager):
        """Test getting configuration values."""
        # Test existing values
        assert config_manager.get("server.host") == "127.0.0.1"
        assert config_manager.get("server.port") == 8080
        assert config_manager.get("security.session_timeout") == 3600
        
        # Test default values
        assert config_manager.get("nonexistent.key", "default") == "default"
        assert config_manager.get("nonexistent.key") is None
        
        # Test nested access
        assert config_manager.get("server.ssl.enabled") is False
    
    def test_set_configuration_values(self, config_manager):
        """Test setting configuration values."""
        # Set simple value
        assert config_manager.set("test.simple", "value")
        assert config_manager.get("test.simple") == "value"
        
        # Set nested value
        assert config_manager.set("test.nested.deep", 42)
        assert config_manager.get("test.nested.deep") == 42
        
        # Set existing value
        assert config_manager.set("server.port", 9090)
        assert config_manager.get("server.port") == 9090
    
    def test_update_multiple_values(self, config_manager):
        """Test updating multiple configuration values."""
        updates = {
            "server.port": 9090,
            "test.value1": "data1",
            "test.value2": 123
        }
        
        assert config_manager.update(updates)
        
        assert config_manager.get("server.port") == 9090
        assert config_manager.get("test.value1") == "data1"
        assert config_manager.get("test.value2") == 123
    
    def test_has_key(self, config_manager):
        """Test checking if configuration key exists."""
        assert config_manager.has_key("server.host")
        assert config_manager.has_key("security.encryption_key")
        assert not config_manager.has_key("nonexistent.key")
        assert not config_manager.has_key("server.nonexistent")
    
    def test_delete_key(self, config_manager):
        """Test deleting configuration keys."""
        # Set a test value
        config_manager.set("test.delete_me", "value")
        assert config_manager.has_key("test.delete_me")
        
        # Delete it
        assert config_manager.delete_key("test.delete_me")
        assert not config_manager.has_key("test.delete_me")
        
        # Try to delete non-existent key
        assert not config_manager.delete_key("nonexistent.key")
    
    def test_get_section(self, config_manager):
        """Test getting configuration sections."""
        server_config = config_manager.get_section("server")
        assert isinstance(server_config, dict)
        assert "host" in server_config
        assert "port" in server_config
        
        security_config = config_manager.get_section("security")
        assert isinstance(security_config, dict)
        assert "encryption_key" in security_config
        
        # Non-existent section
        empty_config = config_manager.get_section("nonexistent")
        assert empty_config == {}
    
    def test_get_all_config(self, config_manager):
        """Test getting all configuration."""
        all_config = config_manager.get_all()
        assert isinstance(all_config, dict)
        assert "server" in all_config
        assert "security" in all_config
        
        # Ensure it's a copy, not reference
        all_config["test"] = "value"
        assert not config_manager.has_key("test")
    
    def test_config_validation(self, temp_dir):
        """Test configuration validation."""
        config_path = os.path.join(temp_dir, "invalid_config.json")
        
        # Create invalid config
        invalid_config = {
            "server": {
                "host": "localhost"
                # Missing required port
            },
            "security": {
                "encryption_key": "short"  # Too short
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        # Should fall back to default config
        manager = ConfigManager(config_path=config_path)
        
        # Should have valid config now
        assert manager.validate_config()
        assert manager.get("server.port") is not None
        assert len(manager.get("security.encryption_key")) >= 32
    
    def test_environment_variable_overrides(self, temp_dir):
        """Test environment variable overrides."""
        config_path = os.path.join(temp_dir, "env_config.json")
        
        with patch.dict(os.environ, {
            'WADE_HOST': '0.0.0.0',
            'WADE_PORT': '8888',
            'WADE_LOG_LEVEL': 'DEBUG'
        }):
            manager = ConfigManager(config_path=config_path)
            
            assert manager.get("server.host") == "0.0.0.0"
            assert manager.get("server.port") == 8888
            assert manager.get("logging.level") == "DEBUG"
    
    def test_config_watchers(self, config_manager):
        """Test configuration change watchers."""
        callback_called = []
        
        def test_callback(key, value):
            callback_called.append((key, value))
        
        # Add watcher
        config_manager.add_watcher("test.watched", test_callback)
        
        # Change watched value
        config_manager.set("test.watched", "new_value")
        
        assert len(callback_called) == 1
        assert callback_called[0] == ("test.watched", "new_value")
        
        # Remove watcher
        config_manager.remove_watcher("test.watched", test_callback)
        
        # Change value again
        config_manager.set("test.watched", "another_value")
        
        # Should not have been called again
        assert len(callback_called) == 1
    
    def test_reload_callbacks(self, config_manager):
        """Test configuration reload callbacks."""
        callback_called = []
        
        def reload_callback(old_config, new_config):
            callback_called.append((old_config, new_config))
        
        # Add reload callback
        config_manager.add_reload_callback(reload_callback)
        
        # Trigger reload
        config_manager.reload()
        
        assert len(callback_called) == 1
        old_config, new_config = callback_called[0]
        assert isinstance(old_config, dict)
        assert isinstance(new_config, dict)
    
    def test_export_import_config(self, config_manager):
        """Test exporting and importing configuration."""
        # Set some test values
        config_manager.set("test.export", "value")
        config_manager.set("test.number", 42)
        
        # Export as JSON
        json_export = config_manager.export_config('json')
        assert isinstance(json_export, str)
        assert "test.export" in json_export
        
        # Export as YAML
        yaml_export = config_manager.export_config('yaml')
        assert isinstance(yaml_export, str)
        assert "test:" in yaml_export
        
        # Import JSON
        new_config = '{"imported": {"value": "test"}}'
        assert config_manager.import_config(new_config, 'json')
        assert config_manager.get("imported.value") == "test"
    
    def test_file_watching(self, temp_dir):
        """Test configuration file watching."""
        config_path = os.path.join(temp_dir, "watched_config.json")
        
        # Create manager with file watching enabled
        manager = ConfigManager(config_path=config_path)
        manager.config['config']['hot_reload'] = True
        manager.save_config()
        
        # Start watching
        manager.start_watching()
        assert manager.watching
        
        # Modify file externally
        time.sleep(0.1)  # Ensure different timestamp
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config_data['test'] = {'external_change': True}
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Wait for file watcher to detect change
        time.sleep(1.5)
        
        # Check if change was detected
        assert manager.get("test.external_change") is True
        
        # Stop watching
        manager.stop_watching()
        assert not manager.watching
    
    def test_config_backup(self, temp_dir):
        """Test configuration backup functionality."""
        config_path = os.path.join(temp_dir, "backup_config.json")
        manager = ConfigManager(config_path=config_path)
        
        # Enable backup on change
        manager.set("config.backup_on_change", True)
        
        # Make a change that triggers backup
        manager.set("test.backup", "value")
        manager.save_config()
        
        # Check if backup was created
        backup_dir = os.path.join(os.path.dirname(config_path), 'backups')
        if os.path.exists(backup_dir):
            backup_files = os.listdir(backup_dir)
            assert len(backup_files) > 0
            assert any(f.startswith('config_backup_') for f in backup_files)
    
    def test_merge_configs(self, config_manager):
        """Test configuration merging."""
        default_config = {
            "section1": {"key1": "default1", "key2": "default2"},
            "section2": {"key3": "default3"}
        }
        
        override_config = {
            "section1": {"key1": "override1"},
            "section3": {"key4": "new4"}
        }
        
        merged = config_manager._merge_configs(default_config, override_config)
        
        # Check merged values
        assert merged["section1"]["key1"] == "override1"  # Overridden
        assert merged["section1"]["key2"] == "default2"   # Preserved
        assert merged["section2"]["key3"] == "default3"   # Preserved
        assert merged["section3"]["key4"] == "new4"       # Added
    
    def test_encryption_key_generation(self, temp_dir):
        """Test encryption key generation."""
        config_path = os.path.join(temp_dir, "key_config.json")
        manager = ConfigManager(config_path=config_path)
        
        encryption_key = manager.get("security.encryption_key")
        
        # Should be a hex string of appropriate length
        assert isinstance(encryption_key, str)
        assert len(encryption_key) == 64  # 32 bytes * 2 (hex)
        
        # Should be different each time
        manager2 = ConfigManager(config_path=os.path.join(temp_dir, "key_config2.json"))
        encryption_key2 = manager2.get("security.encryption_key")
        
        assert encryption_key != encryption_key2
    
    @pytest.mark.slow
    def test_concurrent_access(self, config_manager):
        """Test concurrent access to configuration."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    # Set value
                    config_manager.set(f"worker_{worker_id}.iteration", i)
                    
                    # Get value
                    value = config_manager.get(f"worker_{worker_id}.iteration")
                    results.append((worker_id, i, value))
                    
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 workers * 10 iterations
        
        # Verify all values were set correctly
        for worker_id, iteration, value in results:
            assert value == iteration