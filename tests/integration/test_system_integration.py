# -*- coding: utf-8 -*-
"""
Integration tests for WADE system components.
"""

import pytest
import os
import time
import threading
import tempfile
from unittest.mock import patch, Mock

from WADE_CORE.config_manager import ConfigManager
from security.auth_manager import AuthManager
from system.monitor import SystemMonitor
from system.backup_manager import BackupManager


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for core system components."""
    
    def test_config_auth_integration(self, temp_dir):
        """Test configuration manager and auth manager integration."""
        # Create config manager
        config_path = os.path.join(temp_dir, "integration_config.json")
        config_manager = ConfigManager(config_path=config_path)
        
        # Configure auth settings
        config_manager.set("security.session_timeout", 1800)
        config_manager.set("security.max_login_attempts", 3)
        
        # Create auth manager with config
        auth_config = config_manager.get_section("security")
        auth_manager = AuthManager(secret_key=auth_config["encryption_key"])
        auth_manager.session_timeout = auth_config["session_timeout"]
        auth_manager.max_login_attempts = auth_config["max_login_attempts"]
        
        # Test integration
        auth_manager.create_user("testuser", "TestPass123!", "operator")
        session_id = auth_manager.authenticate("testuser", "TestPass123!")
        
        assert session_id is not None
        assert auth_manager.session_timeout == 1800
        assert auth_manager.max_login_attempts == 3
        
        # Test config changes affect auth
        config_manager.set("security.session_timeout", 900)
        auth_manager.session_timeout = config_manager.get("security.session_timeout")
        
        assert auth_manager.session_timeout == 900
    
    def test_monitoring_backup_integration(self, temp_dir):
        """Test monitoring and backup system integration."""
        # Create monitoring system
        monitor_config = {
            'interval': 1,
            'db_path': os.path.join(temp_dir, 'monitoring.db'),
            'thresholds': {
                'cpu_percent': {'warning': 70, 'critical': 90}
            },
            'alerts': {'enabled': True, 'cooldown': 1}
        }
        monitor = SystemMonitor(config=monitor_config)
        
        # Create backup manager
        backup_config = {
            'backup_dir': os.path.join(temp_dir, 'backups'),
            'backup_targets': {
                'monitoring_db': {
                    'path': monitor_config['db_path'],
                    'enabled': True,
                    'priority': 'high'
                }
            }
        }
        backup_manager = BackupManager(config=backup_config)
        
        # Start monitoring
        monitor.start_monitoring()
        time.sleep(2)  # Let it collect some data
        
        # Create backup of monitoring data
        backup_id = backup_manager.create_backup('manual', ['monitoring_db'])
        
        # Verify backup was created
        assert backup_id is not None
        backups = backup_manager.list_backups()
        assert len(backups) > 0
        assert any(b['backup_id'] == backup_id for b in backups)
        
        # Stop monitoring
        monitor.stop_monitoring()
    
    @pytest.mark.slow
    def test_full_system_startup_shutdown(self, temp_dir):
        """Test full system startup and shutdown sequence."""
        # This would test the complete system lifecycle
        components = {}
        
        try:
            # 1. Initialize configuration
            config_path = os.path.join(temp_dir, "system_config.json")
            config_manager = ConfigManager(config_path=config_path)
            components['config'] = config_manager
            
            # 2. Initialize security
            auth_manager = AuthManager(
                secret_key=config_manager.get("security.encryption_key")
            )
            components['auth'] = auth_manager
            
            # 3. Initialize monitoring
            monitor_config = {
                'interval': 1,
                'db_path': os.path.join(temp_dir, 'system_monitoring.db')
            }
            monitor = SystemMonitor(config=monitor_config)
            monitor.start_monitoring()
            components['monitor'] = monitor
            
            # 4. Initialize backup system
            backup_config = {
                'backup_dir': os.path.join(temp_dir, 'system_backups')
            }
            backup_manager = BackupManager(config=backup_config)
            components['backup'] = backup_manager
            
            # Verify all components are running
            assert config_manager.get("server.host") is not None
            assert len(auth_manager.users) > 0  # Default admin user
            assert monitor.running
            
            # Test inter-component communication
            # Create user through auth manager
            auth_manager.create_user("systemuser", "SystemPass123!", "admin")
            session_id = auth_manager.authenticate("systemuser", "SystemPass123!")
            assert session_id is not None
            
            # Check monitoring data
            time.sleep(2)
            metrics = monitor.get_current_metrics()
            assert len(metrics) > 0
            
            # Create system backup
            backup_id = backup_manager.create_backup('integration_test')
            assert backup_id is not None
            
        finally:
            # Shutdown all components
            for name, component in components.items():
                try:
                    if hasattr(component, 'stop_monitoring'):
                        component.stop_monitoring()
                    elif hasattr(component, 'stop_watching'):
                        component.stop_watching()
                    elif hasattr(component, 'shutdown'):
                        component.shutdown()
                except Exception as e:
                    print(f"Error shutting down {name}: {e}")
    
    def test_error_propagation(self, temp_dir):
        """Test error handling across system components."""
        # Create components with error conditions
        config_path = os.path.join(temp_dir, "error_config.json")
        config_manager = ConfigManager(config_path=config_path)
        
        # Test configuration error handling
        invalid_updates = {
            "server.port": "invalid_port",  # Should be integer
            "security.encryption_key": "short"  # Too short
        }
        
        # These should fail validation
        for key, value in invalid_updates.items():
            result = config_manager.set(key, value)
            assert not result  # Should fail
        
        # Verify original values are preserved
        assert isinstance(config_manager.get("server.port"), int)
        assert len(config_manager.get("security.encryption_key")) >= 32
    
    def test_concurrent_operations(self, temp_dir):
        """Test concurrent operations across components."""
        config_path = os.path.join(temp_dir, "concurrent_config.json")
        config_manager = ConfigManager(config_path=config_path)
        
        auth_manager = AuthManager(
            secret_key=config_manager.get("security.encryption_key")
        )
        
        results = []
        errors = []
        
        def config_worker():
            try:
                for i in range(10):
                    config_manager.set(f"test.worker_config_{i}", f"value_{i}")
                    time.sleep(0.01)
                results.append("config_worker_done")
            except Exception as e:
                errors.append(f"config_worker: {e}")
        
        def auth_worker():
            try:
                for i in range(5):
                    username = f"user_{i}"
                    auth_manager.create_user(username, "TestPass123!", "operator")
                    session_id = auth_manager.authenticate(username, "TestPass123!")
                    if session_id:
                        auth_manager.logout(session_id)
                    time.sleep(0.02)
                results.append("auth_worker_done")
            except Exception as e:
                errors.append(f"auth_worker: {e}")
        
        # Start concurrent workers
        threads = [
            threading.Thread(target=config_worker),
            threading.Thread(target=auth_worker)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert "config_worker_done" in results
        assert "auth_worker_done" in results
        
        # Verify final state
        assert config_manager.get("test.worker_config_9") == "value_9"
        assert len(auth_manager.users) >= 6  # 5 created + 1 default admin


@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Integration tests for security components."""
    
    def test_auth_secret_integration(self, temp_dir):
        """Test authentication and secret management integration."""
        from security.secret_manager import SecretManager
        
        # Create secret manager
        secret_manager = SecretManager()
        secret_manager.vault_path = os.path.join(temp_dir, "auth_secrets.json")
        secret_manager.set_master_key("integration_test_key")
        
        # Store auth-related secrets
        secret_manager.set_secret("jwt_secret", "super_secret_jwt_key")
        secret_manager.set_secret("api_key", "api_key_12345")
        
        # Create auth manager using secrets
        jwt_secret = secret_manager.get_secret("jwt_secret")
        auth_manager = AuthManager(secret_key=jwt_secret)
        
        # Test that auth manager works with secret
        auth_manager.create_user("secretuser", "SecretPass123!", "admin")
        session_id = auth_manager.authenticate("secretuser", "SecretPass123!")
        
        assert session_id is not None
        assert session_id in auth_manager.sessions
        
        # Test secret rotation
        secret_manager.set_secret("jwt_secret", "new_super_secret_jwt_key")
        new_jwt_secret = secret_manager.get_secret("jwt_secret")
        
        # Create new auth manager with rotated secret
        new_auth_manager = AuthManager(secret_key=new_jwt_secret)
        
        # Old sessions should not validate with new secret
        user_info = new_auth_manager.validate_session(session_id)
        assert user_info is None  # Should fail with different secret
    
    def test_certificate_auth_integration(self, temp_dir):
        """Test certificate handler and auth manager integration."""
        from security.cert_handler import CertificateHandler
        
        # Create certificate handler
        cert_dir = os.path.join(temp_dir, "integration_certs")
        cert_handler = CertificateHandler(cert_dir=cert_dir)
        
        # Create client certificate
        cert_path, key_path = cert_handler.create_client_certificate("integration_client")
        
        assert cert_path is not None
        assert key_path is not None
        
        # Validate certificate
        cert_info = cert_handler.validate_certificate(cert_path)
        assert cert_info['valid']
        assert cert_info['common_name'] == "integration_client"
        
        # Test SSL context creation
        server_context = cert_handler.get_ssl_context('server')
        client_context = cert_handler.get_ssl_context('client')
        
        assert server_context is not None
        assert client_context is not None
    
    def test_end_to_end_security_flow(self, temp_dir):
        """Test complete security flow from authentication to authorization."""
        from security.secret_manager import SecretManager
        from security.cert_handler import CertificateHandler
        
        # 1. Setup secret management
        secret_manager = SecretManager()
        secret_manager.vault_path = os.path.join(temp_dir, "e2e_secrets.json")
        secret_manager.set_master_key("e2e_test_master_key")
        
        # Store security secrets
        secret_manager.set_secret("auth_key", "e2e_auth_secret_key")
        secret_manager.set_secret("encryption_key", "e2e_encryption_key_32_chars_long")
        
        # 2. Setup certificate management
        cert_dir = os.path.join(temp_dir, "e2e_certs")
        cert_handler = CertificateHandler(cert_dir=cert_dir)
        
        # Create server certificate
        cert_handler.create_server_certificate("e2e.test.local")
        
        # 3. Setup authentication
        auth_key = secret_manager.get_secret("auth_key")
        auth_manager = AuthManager(secret_key=auth_key)
        
        # 4. Create user with different roles
        auth_manager.create_user("admin_user", "AdminPass123!", "admin")
        auth_manager.create_user("operator_user", "OperatorPass123!", "operator")
        auth_manager.create_user("viewer_user", "ViewerPass123!", "viewer")
        
        # 5. Test authentication flow
        admin_session = auth_manager.authenticate("admin_user", "AdminPass123!")
        operator_session = auth_manager.authenticate("operator_user", "OperatorPass123!")
        viewer_session = auth_manager.authenticate("viewer_user", "ViewerPass123!")
        
        assert admin_session is not None
        assert operator_session is not None
        assert viewer_session is not None
        
        # 6. Test authorization flow
        # Admin should have all permissions
        assert auth_manager.check_permission(admin_session, "read")
        assert auth_manager.check_permission(admin_session, "write")
        assert auth_manager.check_permission(admin_session, "execute")
        assert auth_manager.check_permission(admin_session, "manage")
        
        # Operator should have read, write, execute but not manage
        assert auth_manager.check_permission(operator_session, "read")
        assert auth_manager.check_permission(operator_session, "write")
        assert auth_manager.check_permission(operator_session, "execute")
        assert not auth_manager.check_permission(operator_session, "manage")
        
        # Viewer should only have read
        assert auth_manager.check_permission(viewer_session, "read")
        assert not auth_manager.check_permission(viewer_session, "write")
        assert not auth_manager.check_permission(viewer_session, "execute")
        assert not auth_manager.check_permission(viewer_session, "manage")
        
        # 7. Test secure data handling
        sensitive_data = "highly_confidential_information"
        encrypted_data = auth_manager.encrypt_sensitive_data(sensitive_data)
        decrypted_data = auth_manager.decrypt_sensitive_data(encrypted_data)
        
        assert encrypted_data != sensitive_data
        assert decrypted_data == sensitive_data
        
        # 8. Test session management
        active_sessions = auth_manager.get_active_sessions()
        assert len(active_sessions) == 3
        
        # Logout one session
        auth_manager.logout(viewer_session)
        active_sessions = auth_manager.get_active_sessions()
        assert len(active_sessions) == 2
        
        # 9. Test certificate validation in context
        server_cert_info = cert_handler.validate_certificate(cert_handler.server_cert_path)
        assert server_cert_info['valid']
        assert server_cert_info['common_name'] == "e2e.test.local"


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance integration tests."""
    
    def test_high_load_authentication(self, temp_dir):
        """Test authentication under high load."""
        config_path = os.path.join(temp_dir, "perf_config.json")
        config_manager = ConfigManager(config_path=config_path)
        
        auth_manager = AuthManager(
            secret_key=config_manager.get("security.encryption_key")
        )
        
        # Create multiple users
        user_count = 50
        for i in range(user_count):
            auth_manager.create_user(f"perfuser_{i}", "PerfPass123!", "operator")
        
        # Test concurrent authentication
        results = []
        errors = []
        
        def auth_worker(user_id):
            try:
                start_time = time.time()
                session_id = auth_manager.authenticate(f"perfuser_{user_id}", "PerfPass123!")
                auth_time = time.time() - start_time
                
                if session_id:
                    # Validate session
                    user_info = auth_manager.validate_session(session_id)
                    if user_info:
                        results.append(auth_time)
                    auth_manager.logout(session_id)
                else:
                    errors.append(f"Auth failed for user {user_id}")
            except Exception as e:
                errors.append(f"Exception for user {user_id}: {e}")
        
        # Start concurrent authentication
        threads = []
        for i in range(user_count):
            thread = threading.Thread(target=auth_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Analyze results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == user_count
        
        avg_auth_time = sum(results) / len(results)
        max_auth_time = max(results)
        
        # Performance assertions
        assert avg_auth_time < 0.1, f"Average auth time too high: {avg_auth_time}s"
        assert max_auth_time < 0.5, f"Max auth time too high: {max_auth_time}s"
    
    def test_monitoring_data_volume(self, temp_dir):
        """Test monitoring system with high data volume."""
        monitor_config = {
            'interval': 0.1,  # Very frequent collection
            'db_path': os.path.join(temp_dir, 'volume_monitoring.db'),
            'retention_days': 1
        }
        
        monitor = SystemMonitor(config=monitor_config)
        
        # Add custom metrics
        for i in range(20):
            monitor.register_custom_metric(f"test_metric_{i}", lambda: random.uniform(0, 100))
        
        try:
            monitor.start_monitoring()
            
            # Let it collect data for a short time
            time.sleep(5)
            
            # Check data collection
            metrics = monitor.get_current_metrics()
            assert len(metrics) > 20  # Should have system + custom metrics
            
            # Check database size is reasonable
            db_size = os.path.getsize(monitor.db_path)
            assert db_size < 10 * 1024 * 1024  # Less than 10MB for short test
            
        finally:
            monitor.stop_monitoring()
    
    def test_backup_large_dataset(self, temp_dir):
        """Test backup system with larger datasets."""
        # Create test data
        test_data_dir = os.path.join(temp_dir, 'large_test_data')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Create multiple files with varying sizes
        for i in range(10):
            file_path = os.path.join(test_data_dir, f'test_file_{i}.txt')
            with open(file_path, 'w') as f:
                # Write different amounts of data
                data_size = (i + 1) * 1000  # 1KB to 10KB
                f.write('x' * data_size)
        
        backup_config = {
            'backup_dir': os.path.join(temp_dir, 'large_backups'),
            'compression': True,
            'backup_targets': {
                'large_data': {
                    'path': test_data_dir,
                    'enabled': True,
                    'priority': 'high'
                }
            }
        }
        
        backup_manager = BackupManager(config=backup_config)
        
        # Test backup creation time
        start_time = time.time()
        backup_id = backup_manager.create_backup('performance_test', ['large_data'])
        backup_time = time.time() - start_time
        
        assert backup_id is not None
        assert backup_time < 10, f"Backup took too long: {backup_time}s"
        
        # Test backup integrity
        backups = backup_manager.list_backups()
        backup_info = next(b for b in backups if b['backup_id'] == backup_id)
        
        assert backup_info['file_size'] > 0
        assert os.path.exists(backup_info['file_path'])
        
        # Test restore performance
        restore_start = time.time()
        restore_success = backup_manager.restore_backup(
            backup_id, 
            ['large_data'], 
            os.path.join(temp_dir, 'restored_data')
        )
        restore_time = time.time() - restore_start
        
        assert restore_success
        assert restore_time < 10, f"Restore took too long: {restore_time}s"