# -*- coding: utf-8 -*-
"""
WADE Base Agent
Abstract base class for all WADE agents.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseAgent(ABC):
    """
    Abstract base class for all WADE agents.
    Defines the interface that all agents must implement.
    """

    def __init__(self, agent_id: str, elite_few):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for the agent
            elite_few: Reference to the EliteFew instance
        """
        self.agent_id = agent_id
        self.elite_few = elite_few
        self.agent_type = self.__class__.__name__
        self.state = {}
        self.action_history = []
        self.initialized = False

    def initialize(self):
        """Initialize the agent. Called after creation."""
        if not self.initialized:
            self._initialize_impl()
            self.initialized = True

    @abstractmethod
    def _initialize_impl(self):
        """Implementation of agent initialization. Must be overridden by subclasses."""
        pass

    def terminate(self):
        """Terminate the agent. Called before destruction."""
        self._terminate_impl()

    def _terminate_impl(self):
        """Implementation of agent termination. Can be overridden by subclasses."""
        pass

    def execute_action(
        self, action: str, params: Dict[str, Any], wade_core
    ) -> Dict[str, Any]:
        """
        Execute an action with the given parameters.

        Args:
            action: Name of the action to execute
            params: Parameters for the action
            wade_core: Reference to the WADE_OS_Core instance

        Returns:
            Dictionary with action results
        """
        # Record action start
        start_time = time.time()

        # Check if action is supported
        if not hasattr(self, f"action_{action}") or not callable(
            getattr(self, f"action_{action}")
        ):
            return {
                "status": "error",
                "message": f"Action '{action}' not supported by agent {self.agent_type}",
            }

        # Execute action
        try:
            action_method = getattr(self, f"action_{action}")
            result = action_method(params, wade_core)

            # Ensure result has required fields
            if not isinstance(result, dict):
                result = {"status": "success", "data": result}

            if "status" not in result:
                result["status"] = "success"

            # Record action in history
            self.action_history.append(
                {
                    "action": action,
                    "params": params,
                    "result_status": result.get("status"),
                    "start_time": start_time,
                    "end_time": time.time(),
                    "duration": time.time() - start_time,
                }
            )

            return result

        except Exception as e:
            # Record action failure
            self.action_history.append(
                {
                    "action": action,
                    "params": params,
                    "result_status": "error",
                    "error": str(e),
                    "start_time": start_time,
                    "end_time": time.time(),
                    "duration": time.time() - start_time,
                }
            )

            return {
                "status": "error",
                "message": f"Error executing action '{action}': {str(e)}",
            }

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent.

        Returns:
            Dictionary with agent state
        """
        return self.state

    def set_state(self, state: Dict[str, Any]):
        """
        Set the state of the agent.

        Args:
            state: New state for the agent
        """
        self.state = state

    def update_state(self, state_update: Dict[str, Any]):
        """
        Update the state of the agent.

        Args:
            state_update: Partial state update
        """
        self.state.update(state_update)

    def get_action_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the action history of the agent.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of action records, most recent first
        """
        return sorted(
            self.action_history, key=lambda x: x.get("start_time", 0), reverse=True
        )[:limit]

    def clear_action_history(self):
        """Clear the action history of the agent."""
        self.action_history = []

    def get_capabilities(self) -> List[str]:
        """
        Get the capabilities of the agent.

        Returns:
            List of action names supported by the agent
        """
        return [
            method[7:]
            for method in dir(self)
            if method.startswith("action_") and callable(getattr(self, method))
        ]

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.

        Returns:
            Dictionary with agent information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "initialized": self.initialized,
            "capabilities": self.get_capabilities(),
            "action_count": len(self.action_history),
        }
