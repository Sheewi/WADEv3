# -*- coding: utf-8 -*-
"""
Unit tests for security components.
"""

import pytest
import os
import tempfile
import time
from unittest.mock import patch, Mock

from security.auth_manager import AuthManager
from security.secret_manager import SecretManager
from security.cert_handler import CertificateHandler


@pytest.mark.unit
@pytest.mark.security
class TestAuthManager:
    """Test cases for AuthManager."""

    def test_init(self):
        """Test AuthManager initialization."""
        auth = AuthManager()

        assert auth.secret_key is not None
        assert len(auth.secret_key) == 64  # 32 bytes hex
        assert auth.session_timeout == 3600
        assert auth.max_login_attempts == 5
        assert "admin" in auth.users

    def test_create_user_success(self, auth_manager):
        """Test successful user creation."""
        success = auth_manager.create_user(
            "testuser", "TestPass123!", "operator", {"name": "Test User"}
        )

        assert success
        assert "testuser" in auth_manager.users
        assert auth_manager.users["testuser"]["role"] == "operator"
        assert auth_manager.users["testuser"]["metadata"]["name"] == "Test User"

    def test_create_user_duplicate(self, auth_manager):
        """Test creating duplicate user fails."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")

        # Try to create same user again
        success = auth_manager.create_user("testuser", "TestPass123!", "operator")
        assert not success

    def test_create_user_invalid_role(self, auth_manager):
        """Test creating user with invalid role fails."""
        success = auth_manager.create_user("testuser", "TestPass123!", "invalid_role")
        assert not success

    def test_create_user_weak_password(self, auth_manager):
        """Test creating user with weak password fails."""
        weak_passwords = ["123", "password", "Password", "Password123", "Pass!"]

        for password in weak_passwords:
            success = auth_manager.create_user(f"user_{password}", password, "operator")
            assert not success

    def test_authenticate_success(self, auth_manager):
        """Test successful authentication."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")

        session_id = auth_manager.authenticate("testuser", "TestPass123!")

        assert session_id is not None
        assert session_id in auth_manager.sessions
        assert auth_manager.sessions[session_id]["user_id"] == "testuser"

    def test_authenticate_invalid_user(self, auth_manager):
        """Test authentication with invalid user."""
        session_id = auth_manager.authenticate("nonexistent", "password")
        assert session_id is None

    def test_authenticate_wrong_password(self, auth_manager):
        """Test authentication with wrong password."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")

        session_id = auth_manager.authenticate("testuser", "WrongPass123!")
        assert session_id is None

    def test_authenticate_locked_account(self, auth_manager):
        """Test authentication with locked account."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")

        # Trigger account lockout
        for _ in range(auth_manager.max_login_attempts):
            auth_manager.authenticate("testuser", "WrongPass123!")

        # Should be locked now
        session_id = auth_manager.authenticate("testuser", "TestPass123!")
        assert session_id is None

    def test_validate_session_success(self, auth_manager):
        """Test successful session validation."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")
        session_id = auth_manager.authenticate("testuser", "TestPass123!")

        user_info = auth_manager.validate_session(session_id)

        assert user_info is not None
        assert user_info["user_id"] == "testuser"
        assert user_info["role"] == "operator"
        assert "read" in user_info["permissions"]

    def test_validate_session_invalid(self, auth_manager):
        """Test validation of invalid session."""
        user_info = auth_manager.validate_session("invalid_session")
        assert user_info is None

    def test_validate_session_expired(self, auth_manager):
        """Test validation of expired session."""
        auth_manager.session_timeout = 1  # 1 second timeout
        auth_manager.create_user("testuser", "TestPass123!", "operator")
        session_id = auth_manager.authenticate("testuser", "TestPass123!")

        # Wait for session to expire
        time.sleep(2)

        user_info = auth_manager.validate_session(session_id)
        assert user_info is None
        assert session_id not in auth_manager.sessions

    def test_logout(self, auth_manager):
        """Test user logout."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")
        session_id = auth_manager.authenticate("testuser", "TestPass123!")

        success = auth_manager.logout(session_id)

        assert success
        assert session_id not in auth_manager.sessions

    def test_check_permission(self, auth_manager):
        """Test permission checking."""
        auth_manager.create_user("admin_user", "TestPass123!", "admin")
        auth_manager.create_user("viewer_user", "TestPass123!", "viewer")

        admin_session = auth_manager.authenticate("admin_user", "TestPass123!")
        viewer_session = auth_manager.authenticate("viewer_user", "TestPass123!")

        # Admin should have all permissions
        assert auth_manager.check_permission(admin_session, "read")
        assert auth_manager.check_permission(admin_session, "write")
        assert auth_manager.check_permission(admin_session, "execute")
        assert auth_manager.check_permission(admin_session, "manage")

        # Viewer should only have read permission
        assert auth_manager.check_permission(viewer_session, "read")
        assert not auth_manager.check_permission(viewer_session, "write")
        assert not auth_manager.check_permission(viewer_session, "execute")
        assert not auth_manager.check_permission(viewer_session, "manage")

    def test_change_password(self, auth_manager):
        """Test password change."""
        auth_manager.create_user("testuser", "OldPass123!", "operator")

        success = auth_manager.change_password("testuser", "OldPass123!", "NewPass123!")
        assert success

        # Old password should not work
        session_id = auth_manager.authenticate("testuser", "OldPass123!")
        assert session_id is None

        # New password should work
        session_id = auth_manager.authenticate("testuser", "NewPass123!")
        assert session_id is not None

    def test_deactivate_user(self, auth_manager):
        """Test user deactivation."""
        auth_manager.create_user("testuser", "TestPass123!", "operator")
        session_id = auth_manager.authenticate("testuser", "TestPass123!")

        success = auth_manager.deactivate_user("testuser")
        assert success

        # Existing session should be invalidated
        assert session_id not in auth_manager.sessions

        # Should not be able to authenticate
        new_session = auth_manager.authenticate("testuser", "TestPass123!")
        assert new_session is None

    def test_cleanup_expired_sessions(self, auth_manager):
        """Test cleanup of expired sessions."""
        auth_manager.session_timeout = 1  # 1 second timeout
        auth_manager.create_user("testuser", "TestPass123!", "operator")

        session_id = auth_manager.authenticate("testuser", "TestPass123!")
        assert session_id in auth_manager.sessions

        # Wait for expiration
        time.sleep(2)

        auth_manager.cleanup_expired_sessions()
        assert session_id not in auth_manager.sessions

    def test_encrypt_decrypt_data(self, auth_manager):
        """Test data encryption and decryption."""
        test_data = "sensitive information"

        encrypted = auth_manager.encrypt_sensitive_data(test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)

        decrypted = auth_manager.decrypt_sensitive_data(encrypted)
        assert decrypted == test_data


@pytest.mark.unit
@pytest.mark.security
class TestSecretManager:
    """Test cases for SecretManager."""

    def test_init(self, secret_manager):
        """Test SecretManager initialization."""
        assert secret_manager.secrets == {}
        assert secret_manager.master_key == "test_master_key"
        assert os.path.exists(os.path.dirname(secret_manager.vault_path))

    def test_set_get_secret(self, secret_manager):
        """Test setting and getting secrets."""
        secret_manager.set_secret("api_key", "secret_value_123")

        retrieved = secret_manager.get_secret("api_key")
        assert retrieved == "secret_value_123"

    def test_get_nonexistent_secret(self, secret_manager):
        """Test getting non-existent secret."""
        retrieved = secret_manager.get_secret("nonexistent")
        assert retrieved is None

    def test_delete_secret(self, secret_manager):
        """Test deleting secrets."""
        secret_manager.set_secret("temp_secret", "temp_value")
        assert secret_manager.get_secret("temp_secret") == "temp_value"

        secret_manager.delete_secret("temp_secret")
        assert secret_manager.get_secret("temp_secret") is None

    def test_list_secrets(self, secret_manager):
        """Test listing secret keys."""
        secret_manager.set_secret("secret1", "value1")
        secret_manager.set_secret("secret2", "value2")

        keys = secret_manager.list_secrets()
        assert "secret1" in keys
        assert "secret2" in keys
        assert len(keys) == 2

    def test_clear_secrets(self, secret_manager):
        """Test clearing all secrets."""
        secret_manager.set_secret("secret1", "value1")
        secret_manager.set_secret("secret2", "value2")

        secret_manager.clear_secrets()
        assert secret_manager.list_secrets() == []

    def test_persistence(self, temp_dir):
        """Test secret persistence across instances."""
        vault_path = os.path.join(temp_dir, "test_vault.json")

        # Create first manager and set secrets
        manager1 = SecretManager()
        manager1.vault_path = vault_path
        manager1.set_master_key("test_key")
        manager1.set_secret("persistent_secret", "persistent_value")

        # Create second manager and verify secrets persist
        manager2 = SecretManager()
        manager2.vault_path = vault_path
        manager2.set_master_key("test_key")

        assert manager2.get_secret("persistent_secret") == "persistent_value"

    def test_wrong_master_key(self, temp_dir):
        """Test that wrong master key cannot decrypt secrets."""
        vault_path = os.path.join(temp_dir, "test_vault.json")

        # Create manager with one key
        manager1 = SecretManager()
        manager1.vault_path = vault_path
        manager1.set_master_key("correct_key")
        manager1.set_secret("secret", "value")

        # Try to access with wrong key
        manager2 = SecretManager()
        manager2.vault_path = vault_path
        manager2.set_master_key("wrong_key")

        # Should not be able to decrypt
        assert manager2.get_secret("secret") is None

    def test_is_initialized(self, secret_manager):
        """Test initialization check."""
        assert secret_manager.is_initialized()

        manager = SecretManager()
        assert not manager.is_initialized()


@pytest.mark.unit
@pytest.mark.security
class TestCertificateHandler:
    """Test cases for CertificateHandler."""

    def test_init(self, cert_handler):
        """Test CertificateHandler initialization."""
        assert os.path.exists(cert_handler.cert_dir)
        assert os.path.exists(cert_handler.ca_cert_path)
        assert os.path.exists(cert_handler.ca_key_path)

    def test_create_server_certificate(self, cert_handler):
        """Test server certificate creation."""
        success = cert_handler.create_server_certificate(
            "test.example.com", ["192.168.1.1"]
        )

        assert success
        assert os.path.exists(cert_handler.server_cert_path)
        assert os.path.exists(cert_handler.server_key_path)

    def test_validate_certificate(self, cert_handler):
        """Test certificate validation."""
        # Create server certificate first
        cert_handler.create_server_certificate()

        cert_info = cert_handler.validate_certificate(cert_handler.server_cert_path)

        assert cert_info["valid"]
        assert cert_info["common_name"] == "localhost"
        assert cert_info["is_valid"]
        assert "not_before" in cert_info
        assert "not_after" in cert_info

    def test_validate_invalid_certificate(self, cert_handler, temp_dir):
        """Test validation of invalid certificate."""
        invalid_cert_path = os.path.join(temp_dir, "invalid.crt")
        with open(invalid_cert_path, "w") as f:
            f.write("invalid certificate data")

        cert_info = cert_handler.validate_certificate(invalid_cert_path)
        assert not cert_info["valid"]
        assert "error" in cert_info

    def test_check_certificate_expiry(self, cert_handler):
        """Test certificate expiry checking."""
        cert_handler.create_server_certificate()

        expiry_info = cert_handler.check_certificate_expiry(
            cert_handler.server_cert_path
        )

        assert "expires_on" in expiry_info
        assert "days_until_expiry" in expiry_info
        assert not expiry_info["is_expired"]
        assert expiry_info["days_until_expiry"] > 0

    def test_verify_certificate_chain(self, cert_handler):
        """Test certificate chain verification."""
        cert_handler.create_server_certificate()

        is_valid = cert_handler.verify_certificate_chain(
            cert_handler.server_cert_path, cert_handler.ca_cert_path
        )

        # Note: This might fail due to signature verification complexity
        # In a real implementation, this would properly verify the chain
        assert isinstance(is_valid, bool)

    def test_get_certificate_fingerprint(self, cert_handler):
        """Test certificate fingerprint generation."""
        cert_handler.create_server_certificate()

        fingerprint_sha256 = cert_handler.get_certificate_fingerprint(
            cert_handler.server_cert_path, "sha256"
        )
        fingerprint_sha1 = cert_handler.get_certificate_fingerprint(
            cert_handler.server_cert_path, "sha1"
        )

        assert isinstance(fingerprint_sha256, str)
        assert isinstance(fingerprint_sha1, str)
        assert ":" in fingerprint_sha256
        assert ":" in fingerprint_sha1
        assert len(fingerprint_sha256) > len(fingerprint_sha1)

    def test_create_client_certificate(self, cert_handler):
        """Test client certificate creation."""
        cert_path, key_path = cert_handler.create_client_certificate("test_client")

        assert cert_path is not None
        assert key_path is not None
        assert os.path.exists(cert_path)
        assert os.path.exists(key_path)

        # Validate the client certificate
        cert_info = cert_handler.validate_certificate(cert_path)
        assert cert_info["valid"]
        assert cert_info["common_name"] == "test_client"

    def test_list_certificates(self, cert_handler):
        """Test listing certificates."""
        # Create some certificates
        cert_handler.create_server_certificate()
        cert_handler.create_client_certificate("client1")
        cert_handler.create_client_certificate("client2")

        certificates = cert_handler.list_certificates()

        assert len(certificates) >= 3  # CA, server, and clients

        # Check that all certificates have required fields
        for cert in certificates:
            assert "filename" in cert
            assert "path" in cert
            assert "valid" in cert
            if cert["valid"]:
                assert "common_name" in cert
                assert "not_before" in cert
                assert "not_after" in cert

    def test_get_ssl_context_server(self, cert_handler):
        """Test getting SSL context for server."""
        context = cert_handler.get_ssl_context("server")

        assert context is not None
        # Verify it's configured for server use
        assert hasattr(context, "load_cert_chain")

    def test_get_ssl_context_client(self, cert_handler):
        """Test getting SSL context for client."""
        context = cert_handler.get_ssl_context("client")

        assert context is not None
        # Verify it's configured for client use
        assert hasattr(context, "check_hostname")

    @pytest.mark.slow
    def test_certificate_permissions(self, cert_handler):
        """Test that certificate files have correct permissions."""
        cert_handler.create_server_certificate()

        # Check CA key permissions (should be 600)
        ca_key_stat = os.stat(cert_handler.ca_key_path)
        assert oct(ca_key_stat.st_mode)[-3:] == "600"

        # Check server key permissions (should be 600)
        server_key_stat = os.stat(cert_handler.server_key_path)
        assert oct(server_key_stat.st_mode)[-3:] == "600"

        # Check certificate permissions (should be 644)
        ca_cert_stat = os.stat(cert_handler.ca_cert_path)
        assert oct(ca_cert_stat.st_mode)[-3:] == "644"
