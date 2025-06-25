# -*- coding: utf-8 -*-
"""
WADE Long-Term Memory Module
Provides persistent knowledge storage for WADE.
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class LongTermMemory:
    """
    Long-term memory for WADE.
    Stores persistent knowledge and historical data.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize long-term memory.

        Args:
            storage_dir: Directory to store memory files (defaults to WADE_RUNTIME/memory)
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # Default to WADE_RUNTIME/memory
            wade_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            self.storage_dir = Path(os.path.join(wade_root, "WADE_RUNTIME", "memory"))

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)

        # Initialize memory categories
        self.categories = {
            "knowledge": self._load_category("knowledge"),
            "history": self._load_category("history"),
            "models": self._load_category("models"),
            "user_profiles": self._load_category("user_profiles"),
        }

    def _load_category(self, category: str) -> Dict[str, Any]:
        """
        Load a memory category from disk.

        Args:
            category: Category name

        Returns:
            Dictionary containing category data
        """
        category_file = self.storage_dir / f"{category}.json"

        if category_file.exists():
            try:
                with open(category_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, start with empty category
                return {}

        return {}

    def _save_category(self, category: str):
        """
        Save a memory category to disk.

        Args:
            category: Category name
        """
        category_file = self.storage_dir / f"{category}.json"

        with open(category_file, "w") as f:
            json.dump(self.categories[category], f, indent=2)

    def add_entry(
        self, category: str, data: Dict[str, Any], entry_id: Optional[str] = None
    ) -> str:
        """
        Add an entry to long-term memory.

        Args:
            category: Category to add entry to
            data: Data to store
            entry_id: Optional ID for the entry (generated if not provided)

        Returns:
            ID of the added entry
        """
        if category not in self.categories:
            self.categories[category] = {}

        # Generate entry ID if not provided
        if not entry_id:
            timestamp = int(time.time() * 1000)
            data_hash = hashlib.md5(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()[:8]
            entry_id = f"{category}_{timestamp}_{data_hash}"

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = time.time()

        # Store entry
        self.categories[category][entry_id] = data

        # Save category to disk
        self._save_category(category)

        return entry_id

    def get_entry(self, category: str, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entry from long-term memory.

        Args:
            category: Category to retrieve entry from
            entry_id: ID of the entry to retrieve

        Returns:
            Entry data or None if not found
        """
        if category not in self.categories or entry_id not in self.categories[category]:
            return None

        return self.categories[category][entry_id]

    def update_entry(self, category: str, entry_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing entry in long-term memory.

        Args:
            category: Category containing the entry
            entry_id: ID of the entry to update
            data: New data for the entry

        Returns:
            True if entry was updated, False if not found
        """
        if category not in self.categories or entry_id not in self.categories[category]:
            return False

        # Preserve timestamp if not provided in new data
        if (
            "timestamp" not in data
            and "timestamp" in self.categories[category][entry_id]
        ):
            data["timestamp"] = self.categories[category][entry_id]["timestamp"]

        # Update entry
        self.categories[category][entry_id] = data

        # Save category to disk
        self._save_category(category)

        return True

    def delete_entry(self, category: str, entry_id: str) -> bool:
        """
        Delete an entry from long-term memory.

        Args:
            category: Category containing the entry
            entry_id: ID of the entry to delete

        Returns:
            True if entry was deleted, False if not found
        """
        if category not in self.categories or entry_id not in self.categories[category]:
            return False

        # Delete entry
        del self.categories[category][entry_id]

        # Save category to disk
        self._save_category(category)

        return True

    def query_knowledge(
        self, category: str, query: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query long-term memory for entries matching criteria.

        Args:
            category: Category to query
            query: Dictionary of key-value pairs to match
            limit: Maximum number of results to return

        Returns:
            List of matching entries
        """
        if category not in self.categories:
            return []

        results = []

        for entry_id, entry_data in self.categories[category].items():
            match = True

            for key, value in query.items():
                if key not in entry_data or entry_data[key] != value:
                    match = False
                    break

            if match:
                results.append({"id": entry_id, **entry_data})

        # Sort by timestamp (most recent first) and limit results
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        return results[:limit]

    def get_all_entries(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all entries in a category.

        Args:
            category: Category to retrieve entries from

        Returns:
            Dictionary of entry_id -> entry_data
        """
        if category not in self.categories:
            return {}

        return self.categories[category]

    def clear_category(self, category: str):
        """
        Clear all entries in a category.

        Args:
            category: Category to clear
        """
        if category in self.categories:
            self.categories[category] = {}
            self._save_category(category)

    def get_categories(self) -> List[str]:
        """
        Get all categories in long-term memory.

        Returns:
            List of category names
        """
        return list(self.categories.keys())

    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each category.

        Returns:
            Dictionary with category statistics
        """
        stats = {}

        for category in self.categories:
            stats[category] = {
                "count": len(self.categories[category]),
                "size_bytes": len(json.dumps(self.categories[category])),
            }

        return stats
