# -*- coding: utf-8 -*-
"""
WADE Long-Term Memory
Provides persistent knowledge storage.
"""

import os
import sys
import time
import json
import logging
import threading
from typing import Dict, List, Any, Optional


class LongTermMemory:
    """
    Long-Term Memory for WADE.
    Provides persistent knowledge storage.
    """

    def __init__(
        self,
        storage_type: str = "json",
        max_size: int = 10000,
        backup_interval: int = 3600,
    ):
        """
        Initialize the long-term memory.

        Args:
            storage_type: Type of storage to use (json, sqlite, etc.)
            max_size: Maximum number of items to store
            backup_interval: Time in seconds between backups
        """
        self.logger = logging.getLogger("wade.memory.ltm")
        self.storage_type = storage_type
        self.max_size = max_size
        self.backup_interval = backup_interval
        self.memory = {}
        self.metadata = {}
        self.is_modified = False
        self.last_backup = 0
        self.backup_thread = None
        self.is_running = True

        # Set up storage
        self._setup_storage()

        # Load memory
        self._load_memory()

        # Start backup thread
        self._start_backup_thread()

        self.logger.info("Long-term memory initialized")

    def _setup_storage(self):
        """Set up storage."""
        # Get storage path
        self.storage_path = os.environ.get(
            "WADE_RUNTIME",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "WADE_RUNTIME",
            ),
        )

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Set up storage file
        if self.storage_type == "json":
            self.storage_file = os.path.join(self.storage_path, "long_term_memory.json")
        elif self.storage_type == "sqlite":
            self.storage_file = os.path.join(self.storage_path, "long_term_memory.db")
            # TODO: Set up SQLite database
        else:
            self.logger.error(f"Unsupported storage type: {self.storage_type}")
            self.storage_type = "json"
            self.storage_file = os.path.join(self.storage_path, "long_term_memory.json")

    def _load_memory(self):
        """Load memory from storage."""
        try:
            if self.storage_type == "json":
                if os.path.exists(self.storage_file):
                    with open(self.storage_file, "r") as f:
                        data = json.load(f)
                        self.memory = data.get("memory", {})
                        self.metadata = data.get("metadata", {})
                else:
                    self.memory = {}
                    self.metadata = {
                        "created": time.time(),
                        "modified": time.time(),
                        "version": "1.0.0",
                    }
            elif self.storage_type == "sqlite":
                # TODO: Load from SQLite database
                pass

            self.logger.info(f"Loaded {len(self.memory)} items from storage")

        except Exception as e:
            self.logger.error(f"Error loading memory: {e}")
            self.memory = {}
            self.metadata = {
                "created": time.time(),
                "modified": time.time(),
                "version": "1.0.0",
            }

    def _save_memory(self):
        """Save memory to storage."""
        try:
            if not self.is_modified:
                return

            if self.storage_type == "json":
                # Update metadata
                self.metadata["modified"] = time.time()

                # Save to file
                with open(self.storage_file, "w") as f:
                    json.dump(
                        {"memory": self.memory, "metadata": self.metadata}, f, indent=2
                    )
            elif self.storage_type == "sqlite":
                # TODO: Save to SQLite database
                pass

            self.is_modified = False
            self.last_backup = time.time()

            self.logger.info(f"Saved {len(self.memory)} items to storage")

        except Exception as e:
            self.logger.error(f"Error saving memory: {e}")

    def _start_backup_thread(self):
        """Start backup thread."""
        self.backup_thread = threading.Thread(target=self._backup_loop)
        self.backup_thread.daemon = True
        self.backup_thread.start()

    def _backup_loop(self):
        """Backup loop."""
        while self.is_running:
            try:
                # Sleep for a while
                time.sleep(10)

                # Check if backup is needed
                if (
                    self.is_modified
                    and time.time() - self.last_backup > self.backup_interval
                ):
                    self._save_memory()

            except Exception as e:
                self.logger.error(f"Error in backup loop: {e}")

    def store(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a value in memory.

        Args:
            key: Key to store value under
            value: Value to store
            metadata: Optional metadata for the value

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if memory is full
            if len(self.memory) >= self.max_size:
                self.logger.warning("Memory is full, cannot store more items")
                return False

            # Store value
            self.memory[key] = {
                "value": value,
                "metadata": metadata or {},
                "created": time.time(),
                "modified": time.time(),
            }

            self.is_modified = True

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

            # Update access time
            self.memory[key]["accessed"] = time.time()

            self.logger.debug(f"Retrieved value for key '{key}'")
            return self.memory[key]["value"]

        except Exception as e:
            self.logger.error(f"Error retrieving value for key '{key}': {e}")
            return None

    def retrieve_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value with metadata from memory.

        Args:
            key: Key to retrieve value for

        Returns:
            Dictionary with value and metadata or None if not found
        """
        try:
            # Check if key exists
            if key not in self.memory:
                self.logger.debug(f"Key '{key}' not found in memory")
                return None

            # Update access time
            self.memory[key]["accessed"] = time.time()

            self.logger.debug(f"Retrieved value with metadata for key '{key}'")
            return self.memory[key]

        except Exception as e:
            self.logger.error(
                f"Error retrieving value with metadata for key '{key}': {e}"
            )
            return None

    def update(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a value in memory.

        Args:
            key: Key to update value for
            value: New value
            metadata: Optional new metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if key exists
            if key not in self.memory:
                self.logger.debug(f"Key '{key}' not found in memory")
                return False

            # Update value
            self.memory[key]["value"] = value
            self.memory[key]["modified"] = time.time()

            # Update metadata if provided
            if metadata:
                self.memory[key]["metadata"].update(metadata)

            self.is_modified = True

            self.logger.debug(f"Updated value for key '{key}'")
            return True

        except Exception as e:
            self.logger.error(f"Error updating value for key '{key}': {e}")
            return False

    def remove(self, key: str) -> bool:
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

            self.is_modified = True

            self.logger.debug(f"Removed value for key '{key}'")
            return True

        except Exception as e:
            self.logger.error(f"Error removing value for key '{key}': {e}")
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

            self.is_modified = True

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
        return {key: item["value"] for key, item in self.memory.items()}

    def get_all_with_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all values with metadata from memory.

        Returns:
            Dictionary with all values and metadata
        """
        return self.memory

    def search(self, query: str) -> Dict[str, Any]:
        """
        Search for values in memory.

        Args:
            query: Search query

        Returns:
            Dictionary with matching values
        """
        try:
            # Simple search implementation
            results = {}

            for key, item in self.memory.items():
                # Check if query is in key
                if query.lower() in key.lower():
                    results[key] = item["value"]
                    continue

                # Check if query is in value
                value_str = str(item["value"]).lower()
                if query.lower() in value_str:
                    results[key] = item["value"]
                    continue

                # Check if query is in metadata
                metadata_str = str(item["metadata"]).lower()
                if query.lower() in metadata_str:
                    results[key] = item["value"]
                    continue

            self.logger.debug(f"Search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")
            return {}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "size": len(self.memory),
            "max_size": self.max_size,
            "storage_type": self.storage_type,
            "backup_interval": self.backup_interval,
            "last_backup": self.last_backup,
            "is_modified": self.is_modified,
            "metadata": self.metadata,
        }

    def shutdown(self):
        """Shutdown the long-term memory."""
        self.is_running = False

        # Save memory
        self._save_memory()

        # Wait for backup thread to finish
        if self.backup_thread:
            self.backup_thread.join(timeout=5)

        self.logger.info("Long-term memory shutdown complete")
