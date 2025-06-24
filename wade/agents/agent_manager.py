# -*- coding: utf-8 -*-
"""
WADE Agent Manager
Manages agent lifecycle.
"""

import os
import sys
import time
import json
import logging
import importlib
from typing import Dict, List, Any, Optional

from WADE_CORE.utils import generate_id

class AgentManager:
    """
    Agent Manager for WADE.
    Manages agent lifecycle.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the agent manager.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.logger = logging.getLogger('wade.agent_manager')
        
        # Initialize agent registry
        self.agents = {}
        
        # Initialize agent type registry
        self.agent_types = {
            'monk': 'agents.monk_agent.MonkAgent',
            'sage': 'agents.sage_agent.SageAgent',
            'warrior': 'agents.warrior_agent.WarriorAgent',
            'diplomat': 'agents.diplomat_agent.DiplomatAgent',
            'explorer': 'agents.explorer_agent.ExplorerAgent',
            'architect': 'agents.architect_agent.ArchitectAgent',
            'scholar': 'agents.scholar_agent.ScholarAgent',
            'artisan': 'agents.artisan_agent.ArtisanAgent',
            'mentor': 'agents.mentor_agent.MentorAgent',
            'sentinel': 'agents.sentinel_agent.SentinelAgent'
        }
        
        self.logger.info("Agent manager initialized")
    
    def create_agent(self, agent_type: str) -> Optional[str]:
        """
        Create a new agent.
        
        Args:
            agent_type: Type of agent to create
            
        Returns:
            Agent ID or None if creation failed
        """
        try:
            # Check if agent type is valid
            if agent_type not in self.agent_types:
                self.logger.error(f"Invalid agent type: {agent_type}")
                return None
            
            # Generate agent ID
            agent_id = generate_id(agent_type)
            
            # Import agent class
            module_path, class_name = self.agent_types[agent_type].rsplit('.', 1)
            
            try:
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                self.logger.error(f"Error importing agent class: {e}")
                
                # Fallback to base agent
                from agents.base_agent import BaseAgent
                
                # Create a dynamic agent class
                agent_class = type(f"{agent_type.capitalize()}Agent", (BaseAgent,), {
                    'process_task': lambda self, task: f"I am a {self.agent_type} agent. I can't process tasks yet."
                })
            
            # Create agent instance
            agent = agent_class(agent_id, agent_type, self.elite_few)
            
            # Register agent
            self.agents[agent_id] = agent
            
            self.logger.info(f"Created agent {agent_id} of type {agent_type}")
            return agent_id
            
        except Exception as e:
            self.logger.error(f"Error creating agent: {e}")
            return None
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of agent to get
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> Dict[str, Any]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Type of agents to get
            
        Returns:
            Dictionary with agent IDs and instances
        """
        return {agent_id: agent for agent_id, agent in self.agents.items() if agent.agent_type == agent_type}
    
    def get_active_agents(self) -> Dict[str, Any]:
        """
        Get all active agents.
        
        Returns:
            Dictionary with agent IDs and instances
        """
        return {agent_id: agent for agent_id, agent in self.agents.items() if agent.is_active()}
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Get all agents.
        
        Returns:
            Dictionary with agent IDs and instances
        """
        return self.agents
    
    def activate_agent(self, agent_id: str) -> bool:
        """
        Activate an agent.
        
        Args:
            agent_id: ID of agent to activate
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        agent.activate()
        return True
    
    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent.
        
        Args:
            agent_id: ID of agent to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        agent.deactivate()
        return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent.
        
        Args:
            agent_id: ID of agent to remove
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        # Shutdown agent
        agent.shutdown()
        
        # Remove agent
        del self.agents[agent_id]
        
        self.logger.info(f"Removed agent {agent_id}")
        return True
    
    def shutdown_all_agents(self):
        """Shutdown all agents."""
        for agent_id, agent in self.agents.items():
            try:
                agent.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down agent {agent_id}: {e}")
        
        self.logger.info("All agents shutdown complete")
    
    def register_agent_type(self, agent_type: str, class_path: str) -> bool:
        """
        Register a new agent type.
        
        Args:
            agent_type: Type of agent to register
            class_path: Path to agent class
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if agent type already exists
            if agent_type in self.agent_types:
                self.logger.warning(f"Agent type {agent_type} already registered")
                return False
            
            # Register agent type
            self.agent_types[agent_type] = class_path
            
            self.logger.info(f"Registered agent type {agent_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent type: {e}")
            return False
    
    def get_agent_types(self) -> Dict[str, str]:
        """
        Get all registered agent types.
        
        Returns:
            Dictionary with agent types and class paths
        """
        return self.agent_types