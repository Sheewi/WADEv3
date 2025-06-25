# -*- coding: utf-8 -*-
"""
WADE Short-Term Memory Module
Provides session-based context storage for WADE.
"""

import time
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque


class ShortTermMemory:
    """
    Short-term memory for WADE.
    Stores session-based context and recent interactions.
    """

    def __init__(self, max_entries_per_category: int = 100):
        """
        Initialize short-term memory.

        Args:
            max_entries_per_category: Maximum number of entries to store per category
        """
        self.memory = defaultdict(lambda: deque(maxlen=max_entries_per_category))
        self.last_access = {}

    def add_entry(self, category: str, data: Any, timestamp: Optional[float] = None):
        """
        Add an entry to short-term memory.

        Args:
            category: Category of the entry (e.g., 'user_command', 'inferred_goal')
            data: Data to store
            timestamp: Optional timestamp (defaults to current time)
        """
        timestamp = timestamp or time.time()

        entry = {"timestamp": timestamp, "data": data}

        self.memory[category].append(entry)
        self.last_access[category] = timestamp

    def get_recent_entries(
        self, category: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent entries from a specific category.

        Args:
            category: Category to retrieve entries from
            limit: Maximum number of entries to retrieve

        Returns:
            List of entries, most recent first
        """
        if category not in self.memory:
            return []

        entries = list(self.memory[category])
        entries.sort(key=lambda x: x["timestamp"], reverse=True)

        return entries[:limit]

    def get_latest_entry(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent entry from a specific category.

        Args:
            category: Category to retrieve entry from

        Returns:
            Most recent entry or None if category is empty
        """
        if category not in self.memory or not self.memory[category]:
            return None

        entries = list(self.memory[category])
        entries.sort(key=lambda x: x["timestamp"], reverse=True)

        return entries[0] if entries else None

    def search_entries(
        self, category: str, query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search for entries matching query criteria.

        Args:
            category: Category to search in
            query: Dictionary of key-value pairs to match

        Returns:
            List of matching entries
        """
        if category not in self.memory:
            return []

        results = []

        for entry in self.memory[category]:
            match = True

            for key, value in query.items():
                if key == "timestamp":
                    continue

                if key not in entry["data"] or entry["data"][key] != value:
                    match = False
                    break

            if match:
                results.append(entry)

        return results

    def clear_category(self, category: str):
        """
        Clear all entries in a specific category.

        Args:
            category: Category to clear
        """
        if category in self.memory:
            self.memory[category].clear()

    def clear_all(self):
        """Clear all entries in short-term memory."""
        self.memory.clear()
        self.last_access.clear()

    def get_categories(self) -> List[str]:
        """
        Get all categories in short-term memory.

        Returns:
            List of category names
        """
        return list(self.memory.keys())

    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each category.

        Returns:
            Dictionary with category statistics
        """
        stats = {}

        for category in self.memory:
            stats[category] = {
                "count": len(self.memory[category]),
                "last_access": self.last_access.get(category, 0),
            }

        return stats
