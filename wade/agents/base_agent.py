# -*- coding: utf-8 -*-
"""
WADE Base Agent
Abstract base class for WADE agents.
"""

import os
import sys
import time
import json
import logging
import abc
from typing import Dict, List, Any, Optional


class BaseAgent(abc.ABC):
    """
    Base Agent for WADE.
    Abstract base class for WADE agents.
    """

    def __init__(self, agent_id: str, agent_type: str, elite_few):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique ID for the agent
            agent_type: Type of agent
            elite_few: Reference to the EliteFew instance
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.elite_few = elite_few
        self.logger = logging.getLogger(f"wade.agent.{agent_type}.{agent_id}")

        # Initialize agent state
        self.state = {
            "created": time.time(),
            "last_active": time.time(),
            "is_active": True,
            "tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
        }

        # Initialize agent memory
        self.memory = {}

        self.logger.info(f"Agent {agent_id} ({agent_type}) initialized")

    @abc.abstractmethod
    def process_task(self, task: str) -> Optional[str]:
        """
        Process a task.

        Args:
            task: Task to process

        Returns:
            Response or None if task couldn't be processed
        """
        pass

    def update_state(self, updates: Dict[str, Any]):
        """
        Update agent state.

        Args:
            updates: Dictionary with updates to apply
        """
        self.state.update(updates)
        self.state["last_active"] = time.time()

    def get_state(self) -> Dict[str, Any]:
        """
        Get agent state.

        Returns:
            Dictionary with agent state
        """
        return self.state

    def store_memory(self, key: str, value: Any) -> bool:
        """
        Store a value in agent memory.

        Args:
            key: Key to store value under
            value: Value to store

        Returns:
            True if successful, False otherwise
        """
        try:
            self.memory[key] = value
            return True
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            return False

    def retrieve_memory(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from agent memory.

        Args:
            key: Key to retrieve value for

        Returns:
            Value or None if not found
        """
        return self.memory.get(key)

    def activate(self):
        """Activate the agent."""
        self.state["is_active"] = True
        self.state["last_active"] = time.time()
        self.logger.info(f"Agent {self.agent_id} activated")

    def deactivate(self):
        """Deactivate the agent."""
        self.state["is_active"] = False
        self.logger.info(f"Agent {self.agent_id} deactivated")

    def is_active(self) -> bool:
        """
        Check if agent is active.

        Returns:
            True if agent is active, False otherwise
        """
        return self.state["is_active"]

    def shutdown(self):
        """Shutdown the agent."""
        self.deactivate()
        self.logger.info(f"Agent {self.agent_id} shutdown complete")
