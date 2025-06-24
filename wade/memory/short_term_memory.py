# -*- coding: utf-8 -*-
"""
WADE Short-Term Memory
Provides session-based context storage.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional

class ShortTermMemory:
    """
    Short-Term Memory for WADE.
    Provides session-based context storage.
    """
    
    def __init__(self, max_size: int = 1000, expiration_time: int = 3600):
        """
        Initialize the short-term memory.
        
        Args:
            max_size: Maximum number of items to store
            expiration_time: Time in seconds after which items expire
        """
        self.logger = logging.getLogger('wade.memory.stm')
        self.max_size = max_size
        self.expiration_time = expiration_time
        self.memory = {}
        self.access_times = {}
        
        self.logger.info("Short-term memory initialized")
    
    def store(self, key: str, value: Any) -> bool:
        """
        Store a value in memory.
        
        Args:
            key: Key to store value under
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if memory is full
            if len(self.memory) >= self.max_size:
                # Remove oldest item
                self._remove_oldest()
            
            # Store value
            self.memory[key] = value
            self.access_times[key] = time.time()
            
            self.logger.debug(f"Stored value for key '{key}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing value for key '{key}': {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from memory.
        
        Args:
            key: Key to retrieve value for
            
        Returns:
            Value or None if not found
        """
        try:
            # Check if key exists
            if key not in self.memory:
                self.logger.debug(f"Key '{key}' not found in memory")
                return None
            
            # Check if value has expired
            if time.time() - self.access_times[key] > self.expiration_time:
                self.logger.debug(f"Value for key '{key}' has expired")
                self._remove(key)
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            
            self.logger.debug(f"Retrieved value for key '{key}'")
            return self.memory[key]
            
        except Exception as e:
            self.logger.error(f"Error retrieving value for key '{key}': {e}")
            return None
    
    def remove(self, key: str) -> bool:
        """
        Remove a value from memory.
        
        Args:
            key: Key to remove
            
        Returns:
            True if successful, False otherwise
        """
        return self._remove(key)
    
    def _remove(self, key: str) -> bool:
        """
        Remove a value from memory.
        
        Args:
            key: Key to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if key exists
            if key not in self.memory:
                self.logger.debug(f"Key '{key}' not found in memory")
                return False
            
            # Remove value
            del self.memory[key]
            del self.access_times[key]
            
            self.logger.debug(f"Removed value for key '{key}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing value for key '{key}': {e}")
            return False
    
    def _remove_oldest(self) -> bool:
        """
        Remove the oldest value from memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find oldest key
            oldest_key = min(self.access_times, key=self.access_times.get)
            
            # Remove oldest value
            return self._remove(oldest_key)
            
        except Exception as e:
            self.logger.error(f"Error removing oldest value: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all values from memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear memory
            self.memory = {}
            self.access_times = {}
            
            self.logger.debug("Cleared memory")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing memory: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all values from memory.
        
        Returns:
            Dictionary with all values
        """
        # Remove expired values
        self._remove_expired()
        
        return self.memory
    
    def _remove_expired(self) -> int:
        """
        Remove all expired values from memory.
        
        Returns:
            Number of removed values
        """
        try:
            # Find expired keys
            current_time = time.time()
            expired_keys = [key for key, access_time in self.access_times.items() if current_time - access_time > self.expiration_time]
            
            # Remove expired values
            for key in expired_keys:
                self._remove(key)
            
            self.logger.debug(f"Removed {len(expired_keys)} expired values")
            return len(expired_keys)
            
        except Exception as e:
            self.logger.error(f"Error removing expired values: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            'size': len(self.memory),
            'max_size': self.max_size,
            'expiration_time': self.expiration_time,
            'oldest_access': min(self.access_times.values()) if self.access_times else None,
            'newest_access': max(self.access_times.values()) if self.access_times else None
        }