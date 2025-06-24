# -*- coding: utf-8 -*-
"""
WADE Authentication Manager
Comprehensive authentication and authorization system.
"""

import os
import jwt
import time
import hashlib
import secrets
import bcrypt
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class AuthManager:
    """
    Authentication and Authorization Manager for WADE.
    Handles user authentication, session management, and access control.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize the authentication manager."""
        self.secret_key = secret_key or self._generate_secret_key()
        self.sessions = {}
        self.users = {}
        self.roles = {
            'admin': ['read', 'write', 'execute', 'manage'],
            'operator': ['read', 'write', 'execute'],
            'viewer': ['read']
        }
        self.session_timeout = 3600  # 1 hour
        self.max_login_attempts = 5
        self.login_attempts = {}
        self.lockout_duration = 900  # 15 minutes
        
        # Initialize encryption
        self.cipher_suite = self._init_encryption()
        
        # Load existing users
        self._load_users()
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_hex(32)
    
    def _init_encryption(self) -> Fernet:
        """Initialize encryption for sensitive data."""
        # Derive key from secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'wade_salt_2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
        return Fernet(key)
    
    def _load_users(self):
        """Load users from storage."""
        # In production, this would load from a secure database
        # For now, create a default admin user
        if not self.users:
            self.create_user('admin', 'admin123!', 'admin', {
                'name': 'Administrator',
                'email': 'admin@wade.local',
                'created': datetime.now().isoformat()
            })
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _generate_token(self, user_id: str, role: str) -> str:
        """Generate a JWT token for a user."""
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _is_account_locked(self, user_id: str) -> bool:
        """Check if an account is locked due to failed login attempts."""
        if user_id not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[user_id]
        if attempts['count'] >= self.max_login_attempts:
            # Check if lockout period has expired
            if time.time() - attempts['last_attempt'] < self.lockout_duration:
                return True
            else:
                # Reset attempts after lockout period
                del self.login_attempts[user_id]
                return False
        
        return False
    
    def _record_failed_attempt(self, user_id: str):
        """Record a failed login attempt."""
        if user_id not in self.login_attempts:
            self.login_attempts[user_id] = {'count': 0, 'last_attempt': 0}
        
        self.login_attempts[user_id]['count'] += 1
        self.login_attempts[user_id]['last_attempt'] = time.time()
    
    def _clear_failed_attempts(self, user_id: str):
        """Clear failed login attempts for a user."""
        if user_id in self.login_attempts:
            del self.login_attempts[user_id]
    
    def create_user(self, user_id: str, password: str, role: str, metadata: Dict = None) -> bool:
        """
        Create a new user.
        
        Args:
            user_id: Unique user identifier
            password: User password
            role: User role (admin, operator, viewer)
            metadata: Additional user metadata
            
        Returns:
            True if user created successfully, False otherwise
        """
        if user_id in self.users:
            return False
        
        if role not in self.roles:
            return False
        
        # Validate password strength
        if not self._validate_password_strength(password):
            return False
        
        self.users[user_id] = {
            'password_hash': self._hash_password(password),
            'role': role,
            'metadata': metadata or {},
            'created': datetime.now().isoformat(),
            'last_login': None,
            'active': True
        }
        
        return True
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements."""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def authenticate(self, user_id: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return a session token.
        
        Args:
            user_id: User identifier
            password: User password
            
        Returns:
            Session token if authentication successful, None otherwise
        """
        # Check if account is locked
        if self._is_account_locked(user_id):
            return None
        
        # Check if user exists
        if user_id not in self.users:
            self._record_failed_attempt(user_id)
            return None
        
        user = self.users[user_id]
        
        # Check if user is active
        if not user.get('active', True):
            return None
        
        # Verify password
        if not self._verify_password(password, user['password_hash']):
            self._record_failed_attempt(user_id)
            return None
        
        # Clear failed attempts on successful login
        self._clear_failed_attempts(user_id)
        
        # Update last login
        self.users[user_id]['last_login'] = datetime.now().isoformat()
        
        # Generate session token
        token = self._generate_token(user_id, user['role'])
        
        # Store session
        session_id = secrets.token_hex(16)
        self.sessions[session_id] = {
            'user_id': user_id,
            'token': token,
            'created': time.time(),
            'last_activity': time.time(),
            'role': user['role']
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """
        Validate a session and return user information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            User information if session valid, None otherwise
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check session timeout
        if time.time() - session['last_activity'] > self.session_timeout:
            del self.sessions[session_id]
            return None
        
        # Verify token
        token_data = self._verify_token(session['token'])
        if not token_data:
            del self.sessions[session_id]
            return None
        
        # Update last activity
        session['last_activity'] = time.time()
        
        return {
            'user_id': session['user_id'],
            'role': session['role'],
            'permissions': self.roles.get(session['role'], [])
        }
    
    def logout(self, session_id: str) -> bool:
        """
        Logout a user session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if logout successful, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def check_permission(self, session_id: str, permission: str) -> bool:
        """
        Check if a session has a specific permission.
        
        Args:
            session_id: Session identifier
            permission: Permission to check
            
        Returns:
            True if permission granted, False otherwise
        """
        user_info = self.validate_session(session_id)
        if not user_info:
            return False
        
        return permission in user_info.get('permissions', [])
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User identifier
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # Verify old password
        if not self._verify_password(old_password, user['password_hash']):
            return False
        
        # Validate new password strength
        if not self._validate_password_strength(new_password):
            return False
        
        # Update password
        self.users[user_id]['password_hash'] = self._hash_password(new_password)
        
        return True
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user deactivated successfully, False otherwise
        """
        if user_id not in self.users:
            return False
        
        self.users[user_id]['active'] = False
        
        # Invalidate all sessions for this user
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session['user_id'] == user_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        return True
    
    def get_active_sessions(self) -> List[Dict]:
        """
        Get all active sessions.
        
        Returns:
            List of active session information
        """
        active_sessions = []
        current_time = time.time()
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] <= self.session_timeout:
                active_sessions.append({
                    'session_id': session_id,
                    'user_id': session['user_id'],
                    'role': session['role'],
                    'created': session['created'],
                    'last_activity': session['last_activity']
                })
        
        return active_sessions
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        encrypted = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data
        """
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher_suite.decrypt(encrypted)
        return decrypted.decode()