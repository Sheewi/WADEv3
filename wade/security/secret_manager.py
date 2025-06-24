# -*- coding: utf-8 -*-
"""
WADE Secret Manager
Manages secrets and credentials securely.
"""

import os
import sys
import json
import base64
import hashlib
import time
from typing import Dict, List, Any, Optional

class SecretManager:
    """
    Secret Manager for WADE.
    Manages secrets and credentials securely.
    """
    
    def __init__(self):
        """Initialize the secret manager."""
        self.secrets = {}
        self.vault_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WADE_RUNTIME', 'vault.json'))
        self.master_key = None
        
        # Create vault directory if it doesn't exist
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        
        # Load secrets
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from vault."""
        if not os.path.exists(self.vault_path):
            self.secrets = {}
            return
        
        try:
            with open(self.vault_path, 'r') as f:
                encrypted_data = json.load(f)
            
            if not self.master_key:
                # Cannot decrypt without master key
                self.secrets = {}
                return
            
            # Decrypt secrets
            decrypted_data = self._decrypt_data(encrypted_data)
            self.secrets = decrypted_data
            
        except Exception as e:
            print(f"Error loading secrets: {e}")
            self.secrets = {}
    
    def _save_secrets(self):
        """Save secrets to vault."""
        try:
            if not self.master_key:
                # Cannot encrypt without master key
                return
            
            # Encrypt secrets
            encrypted_data = self._encrypt_data(self.secrets)
            
            with open(self.vault_path, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
        except Exception as e:
            print(f"Error saving secrets: {e}")
    
    def _encrypt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt data using master key.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        # Simple encryption for demonstration purposes
        # In a real implementation, use a proper encryption library
        if not self.master_key:
            return {}
        
        try:
            # Convert data to JSON string
            data_str = json.dumps(data)
            
            # Encrypt data
            key = hashlib.sha256(self.master_key.encode()).digest()
            encrypted = []
            
            for i, char in enumerate(data_str):
                key_char = key[i % len(key)]
                encrypted.append(chr((ord(char) + key_char) % 256))
            
            encrypted_str = ''.join(encrypted)
            
            # Encode as base64
            encoded = base64.b64encode(encrypted_str.encode()).decode()
            
            return {
                'encrypted': encoded,
                'timestamp': time.time()
            }
            
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return {}
    
    def _decrypt_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt data using master key.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        # Simple decryption for demonstration purposes
        # In a real implementation, use a proper encryption library
        if not self.master_key:
            return {}
        
        try:
            # Get encrypted data
            encoded = encrypted_data.get('encrypted', '')
            
            # Decode from base64
            encrypted_str = base64.b64decode(encoded).decode()
            
            # Decrypt data
            key = hashlib.sha256(self.master_key.encode()).digest()
            decrypted = []
            
            for i, char in enumerate(encrypted_str):
                key_char = key[i % len(key)]
                decrypted.append(chr((ord(char) - key_char) % 256))
            
            decrypted_str = ''.join(decrypted)
            
            # Parse JSON
            return json.loads(decrypted_str)
            
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return {}
    
    def set_master_key(self, key: str):
        """
        Set the master key for encryption/decryption.
        
        Args:
            key: Master key
        """
        self.master_key = key
        
        # Reload secrets with new key
        self._load_secrets()
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret by key.
        
        Args:
            key: Secret key
            
        Returns:
            Secret value or None if not found
        """
        return self.secrets.get(key)
    
    def set_secret(self, key: str, value: str):
        """
        Set a secret.
        
        Args:
            key: Secret key
            value: Secret value
        """
        self.secrets[key] = value
        self._save_secrets()
    
    def delete_secret(self, key: str):
        """
        Delete a secret.
        
        Args:
            key: Secret key
        """
        if key in self.secrets:
            del self.secrets[key]
            self._save_secrets()
    
    def list_secrets(self) -> List[str]:
        """
        List all secret keys.
        
        Returns:
            List of secret keys
        """
        return list(self.secrets.keys())
    
    def clear_secrets(self):
        """Clear all secrets."""
        self.secrets = {}
        self._save_secrets()
    
    def is_initialized(self) -> bool:
        """
        Check if the secret manager is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self.master_key is not None