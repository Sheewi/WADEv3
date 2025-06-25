# -*- coding: utf-8 -*-
"""
WADE Agent Messaging
Provides inter-agent communication capabilities.
"""

import time
import threading
import queue
from typing import Dict, List, Any, Optional, Callable


class AgentMessaging:
    """
    Agent Messaging for WADE.
    Provides inter-agent communication capabilities.
    """

    def __init__(self):
        """Initialize the agent messaging system."""
        self.message_queues = {}  # agent_id -> queue
        self.message_handlers = {}  # agent_id -> handler
        self.message_history = []
        self.history_lock = threading.Lock()
        self.max_history = 1000

    def register_agent(self, agent_id: str, handler: Optional[Callable] = None):
        """
        Register an agent for messaging.

        Args:
            agent_id: ID of the agent
            handler: Optional message handler function
        """
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = queue.Queue()

        if handler:
            self.message_handlers[agent_id] = handler

    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from messaging.

        Args:
            agent_id: ID of the agent
        """
        if agent_id in self.message_queues:
            del self.message_queues[agent_id]

        if agent_id in self.message_handlers:
            del self.message_handlers[agent_id]

    def send_message(
        self, from_agent: str, to_agent: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send a message from one agent to another.

        Args:
            from_agent: ID of the sending agent
            to_agent: ID of the receiving agent
            message: Message to send

        Returns:
            True if message was sent, False otherwise
        """
        if to_agent not in self.message_queues:
            return False

        # Add metadata to message
        message_with_metadata = {
            "from": from_agent,
            "to": to_agent,
            "timestamp": time.time(),
            "message_id": f"{from_agent}_{to_agent}_{int(time.time() * 1000)}",
            "content": message,
        }

        # Add to message queue
        self.message_queues[to_agent].put(message_with_metadata)

        # Add to message history
        with self.history_lock:
            self.message_history.append(message_with_metadata)

            # Limit history size
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history :]

        # Call message handler if registered
        if to_agent in self.message_handlers and self.message_handlers[to_agent]:
            try:
                self.message_handlers[to_agent](message_with_metadata)
            except Exception as e:
                print(f"Error in message handler for agent {to_agent}: {e}")

        return True

    def broadcast_message(
        self,
        from_agent: str,
        message: Dict[str, Any],
        exclude: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """
        Broadcast a message to all registered agents.

        Args:
            from_agent: ID of the sending agent
            message: Message to send
            exclude: Optional list of agent IDs to exclude

        Returns:
            Dictionary of agent_id -> success
        """
        results = {}
        exclude = exclude or []

        for agent_id in self.message_queues:
            if agent_id != from_agent and agent_id not in exclude:
                results[agent_id] = self.send_message(from_agent, agent_id, message)

        return results

    def get_messages(
        self,
        agent_id: str,
        max_messages: int = 10,
        block: bool = False,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for an agent.

        Args:
            agent_id: ID of the agent
            max_messages: Maximum number of messages to retrieve
            block: Whether to block until a message is available
            timeout: Optional timeout for blocking

        Returns:
            List of messages
        """
        if agent_id not in self.message_queues:
            return []

        messages = []
        queue = self.message_queues[agent_id]

        try:
            # Get first message (blocking if requested)
            if block:
                messages.append(queue.get(block=True, timeout=timeout))
            else:
                if not queue.empty():
                    messages.append(queue.get(block=False))

            # Get remaining messages (non-blocking)
            while len(messages) < max_messages and not queue.empty():
                messages.append(queue.get(block=False))

            return messages

        except queue.Empty:
            return messages

    def get_message_history(
        self, agent_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get message history.

        Args:
            agent_id: Optional agent ID to filter by
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages
        """
        with self.history_lock:
            if agent_id:
                # Filter by agent ID
                filtered_history = [
                    msg
                    for msg in self.message_history
                    if msg["from"] == agent_id or msg["to"] == agent_id
                ]
            else:
                filtered_history = list(self.message_history)

            # Sort by timestamp (most recent first)
            filtered_history.sort(key=lambda x: x["timestamp"], reverse=True)

            return filtered_history[:limit]

    def clear_message_history(self):
        """Clear message history."""
        with self.history_lock:
            self.message_history = []

    def shutdown(self):
        """Shutdown the messaging system."""
        # Clear all queues
        for queue in self.message_queues.values():
            while not queue.empty():
                try:
                    queue.get(block=False)
                except:
                    pass

        # Clear all handlers
        self.message_handlers = {}
