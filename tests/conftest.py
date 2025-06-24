# -*- coding: utf-8 -*-
"""
WADE Test Configuration
Pytest fixtures and configuration for WADE testing.
"""

import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Add WADE modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wade'))

from WADE_CORE.config_manager import ConfigManager
from security.auth_manager import AuthManager
from security.secret_manager import SecretManager
from security.cert_handler import CertificateHandler
from system.monitor import SystemMonitor
from system.log_rotator import LogRotator
from system.backup_manager import BackupManager


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="wade_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 8080,
            "ssl": {
                "enabled": False
            }
        },
        "security": {
            "encryption_key": "test_key_12345678901234567890123456789012",
            "session_timeout": 3600,
            "max_login_attempts": 3
        },
        "agents": {
            "max_concurrent": 2,
            "timeout": 60
        },
        "logging": {
            "level": "DEBUG",
            "file": "/tmp/wade_test.log"
        },
        "monitoring": {
            "enabled": False
        }
    }


@pytest.fixture
def config_manager(temp_dir, test_config):
    """Create a test configuration manager."""
    config_file = os.path.join(temp_dir, "test_config.json")
    
    # Create config manager with test config
    manager = ConfigManager(config_path=config_file)
    manager.config = test_config
    manager.save_config()
    
    yield manager
    
    # Cleanup
    if manager.watching:
        manager.stop_watching()


@pytest.fixture
def auth_manager():
    """Create a test authentication manager."""
    manager = AuthManager(secret_key="test_secret_key_12345678901234567890")
    yield manager


@pytest.fixture
def secret_manager(temp_dir):
    """Create a test secret manager."""
    manager = SecretManager()
    manager.vault_path = os.path.join(temp_dir, "test_vault.json")
    manager.set_master_key("test_master_key")
    yield manager


@pytest.fixture
def cert_handler(temp_dir):
    """Create a test certificate handler."""
    cert_dir = os.path.join(temp_dir, "certs")
    handler = CertificateHandler(cert_dir=cert_dir)
    yield handler


@pytest.fixture
def system_monitor(temp_dir):
    """Create a test system monitor."""
    config = {
        'interval': 1,
        'db_path': os.path.join(temp_dir, 'test_monitoring.db'),
        'thresholds': {
            'cpu_percent': {'warning': 70, 'critical': 90},
            'memory_percent': {'warning': 80, 'critical': 95}
        },
        'alerts': {'enabled': True, 'cooldown': 1}
    }
    monitor = SystemMonitor(config=config)
    yield monitor
    
    if monitor.running:
        monitor.stop_monitoring()


@pytest.fixture
def log_rotator(temp_dir):
    """Create a test log rotator."""
    config = {
        'log_dir': os.path.join(temp_dir, 'logs'),
        'max_file_size': 1024,  # 1KB for testing
        'retention_days': 1,
        'compression': False,  # Disable for easier testing
        'logs': {
            'test.log': {
                'level': 'INFO',
                'format': '%(asctime)s - %(message)s',
                'max_size': 1024,
                'backup_count': 2
            }
        }
    }
    rotator = LogRotator(config=config)
    yield rotator
    
    if rotator.running:
        rotator.stop_rotation_service()


@pytest.fixture
def backup_manager(temp_dir):
    """Create a test backup manager."""
    config = {
        'backup_dir': os.path.join(temp_dir, 'backups'),
        'retention_policy': {'daily': 2, 'weekly': 1, 'monthly': 1},
        'compression': False,  # Disable for easier testing
        'backup_targets': {
            'test_data': {
                'path': os.path.join(temp_dir, 'test_data'),
                'enabled': True,
                'priority': 'high'
            }
        }
    }
    
    # Create test data
    test_data_dir = os.path.join(temp_dir, 'test_data')
    os.makedirs(test_data_dir, exist_ok=True)
    with open(os.path.join(test_data_dir, 'test_file.txt'), 'w') as f:
        f.write("Test data for backup")
    
    manager = BackupManager(config=config)
    yield manager
    
    if manager.running:
        manager.stop_scheduled_backups()


@pytest.fixture
def mock_psutil():
    """Mock psutil for testing."""
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.boot_time', return_value=1000000):
        
        # Configure memory mock
        mock_memory.return_value.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value.percent = 50.0
        
        # Configure disk mock
        mock_disk.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk.return_value.used = 50 * 1024 * 1024 * 1024   # 50GB
        mock_disk.return_value.free = 50 * 1024 * 1024 * 1024   # 50GB
        
        yield


@pytest.fixture
def mock_network():
    """Mock network operations for testing."""
    with patch('socket.socket') as mock_socket, \
         patch('requests.get') as mock_requests:
        
        # Configure socket mock for port checks
        mock_socket_instance = Mock()
        mock_socket_instance.connect_ex.return_value = 0  # Port open
        mock_socket.return_value = mock_socket_instance
        
        # Configure requests mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        yield


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    from agents.base_agent import BaseAgent
    
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__("test_agent", "test")
            self.test_data = {}
        
        def execute_task(self, task):
            return {"status": "completed", "result": f"Executed: {task}"}
        
        def get_status(self):
            return {"status": "active", "tasks": 0}
    
    return TestAgent()


@pytest.fixture
def sample_tasks():
    """Provide sample tasks for testing."""
    return [
        {
            "id": "task_1",
            "type": "test",
            "description": "Test task 1",
            "priority": "high",
            "data": {"param1": "value1"}
        },
        {
            "id": "task_2",
            "type": "test",
            "description": "Test task 2",
            "priority": "medium",
            "data": {"param2": "value2"}
        }
    ]


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations."""
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield temp_dir
    
    os.chdir(original_cwd)


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


# Custom assertions
def assert_config_valid(config_dict):
    """Assert that a configuration dictionary is valid."""
    required_sections = ['server', 'security']
    for section in required_sections:
        assert section in config_dict, f"Missing required section: {section}"
    
    # Check server section
    server = config_dict['server']
    assert 'host' in server, "Missing server.host"
    assert 'port' in server, "Missing server.port"
    assert isinstance(server['port'], int), "server.port must be integer"
    assert 1 <= server['port'] <= 65535, "server.port must be valid port number"
    
    # Check security section
    security = config_dict['security']
    assert 'encryption_key' in security, "Missing security.encryption_key"
    assert len(security['encryption_key']) >= 32, "encryption_key too short"


def assert_alert_valid(alert):
    """Assert that an alert object is valid."""
    required_fields = ['id', 'level', 'message', 'metric', 'value', 'threshold', 'timestamp']
    for field in required_fields:
        assert hasattr(alert, field), f"Alert missing field: {field}"
    
    assert alert.level in ['info', 'warning', 'error', 'critical'], f"Invalid alert level: {alert.level}"
    assert isinstance(alert.value, (int, float)), "Alert value must be numeric"
    assert isinstance(alert.threshold, (int, float)), "Alert threshold must be numeric"


def assert_metrics_valid(metrics_dict):
    """Assert that a metrics dictionary is valid."""
    assert isinstance(metrics_dict, dict), "Metrics must be a dictionary"
    
    for metric_name, value in metrics_dict.items():
        assert isinstance(metric_name, str), f"Metric name must be string: {metric_name}"
        assert isinstance(value, (int, float)), f"Metric value must be numeric: {metric_name}={value}"
        assert not metric_name.startswith('_'), f"Metric name should not start with underscore: {metric_name}"


# Test utilities
class TestHelper:
    """Helper class for common test operations."""
    
    @staticmethod
    def create_test_file(path, content="test content"):
        """Create a test file with content."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return path
    
    @staticmethod
    def wait_for_condition(condition_func, timeout=5, interval=0.1):
        """Wait for a condition to become true."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        return False
    
    @staticmethod
    def generate_test_data(size_mb=1):
        """Generate test data of specified size."""
        data_size = size_mb * 1024 * 1024
        return 'x' * data_size


# Make helper available as fixture
@pytest.fixture
def test_helper():
    """Provide test helper utilities."""
    return TestHelper