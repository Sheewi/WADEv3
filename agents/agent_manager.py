# -*- coding: utf-8 -*-
"""
WADE Agent Manager
Manages the lifecycle of agents in the WADE system.
"""

import time
from typing import Dict, List, Any, Optional, Type
from .base_agent import BaseAgent

class AgentManager:
    """
    Manages the lifecycle of agents in the WADE system.
    Handles agent creation, tracking, and termination.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the agent manager.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.active_agents = {}  # agent_id -> agent_instance
        self.agent_registry = {}  # agent_type -> agent_class
        self.agent_stats = {}  # agent_id -> stats
        
        # Register built-in agent types
        self._register_built_in_agents()
    
    def _register_built_in_agents(self):
        """Register built-in agent types."""
        from .agent_types.monk_agent import MonkAgent
        from .agent_types.omen_agent import OmenAgent
        from .agent_types.jarvis_agent import JarvisAgent
        from .agent_types.forge_agent import ForgeAgent
        from .agent_types.joker_agent import JokerAgent
        from .agent_types.ghost_agent import GhostAgent
        from .agent_types.dexter_agent import DexterAgent
        from .agent_types.oracle_agent import OracleAgent
        
        self.register_agent_type('Monk', MonkAgent)
        self.register_agent_type('Omen', OmenAgent)
        self.register_agent_type('Jarvis', JarvisAgent)
        self.register_agent_type('Forge', ForgeAgent)
        self.register_agent_type('Joker', JokerAgent)
        self.register_agent_type('Ghost', GhostAgent)
        self.register_agent_type('Dexter', DexterAgent)
        self.register_agent_type('Oracle', OracleAgent)
    
    def register_agent_type(self, agent_type: str, agent_class: Type[BaseAgent]):
        """
        Register a new agent type.
        
        Args:
            agent_type: Type name of the agent
            agent_class: Class implementing the agent
        """
        self.agent_registry[agent_type] = agent_class
    
    def spawn_agent(self, agent_type: str, agent_id: Optional[str] = None) -> Optional[BaseAgent]:
        """
        Spawn a new agent of the specified type.
        
        Args:
            agent_type: Type of agent to spawn
            agent_id: Optional ID for the agent (generated if not provided)
            
        Returns:
            Agent instance or None if agent type is not registered
        """
        if agent_type not in self.agent_registry:
            self.elite_few.log_and_respond(f"Unknown agent type: {agent_type}", level="ERROR", component="AGENT_MANAGER")
            return None
        
        # Generate agent ID if not provided
        if not agent_id:
            agent_id = f"{agent_type.lower()}_{int(time.time())}"
        
        # Check if agent already exists
        if agent_id in self.active_agents:
            return self.active_agents[agent_id]
        
        # Create new agent instance
        try:
            agent_class = self.agent_registry[agent_type]
            agent = agent_class(agent_id, self.elite_few)
            
            # Initialize agent
            agent.initialize()
            
            # Store agent instance
            self.active_agents[agent_id] = agent
            
            # Initialize agent stats
            self.agent_stats[agent_id] = {
                'type': agent_type,
                'spawn_time': time.time(),
                'action_count': 0,
                'last_action_time': None,
                'status': 'active'
            }
            
            self.elite_few.log_and_respond(f"Agent {agent_type} ({agent_id}) spawned", level="DEBUG", component="AGENT_MANAGER")
            
            return agent
            
        except Exception as e:
            self.elite_few.log_and_respond(f"Error spawning agent {agent_type}: {str(e)}", level="ERROR", component="AGENT_MANAGER")
            return None
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an active agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        return self.active_agents.get(agent_id)
    
    def terminate_agent(self, agent_id: str) -> bool:
        """
        Terminate an active agent.
        
        Args:
            agent_id: ID of the agent to terminate
            
        Returns:
            True if agent was terminated, False if not found
        """
        if agent_id not in self.active_agents:
            return False
        
        # Get agent instance
        agent = self.active_agents[agent_id]
        
        # Terminate agent
        try:
            agent.terminate()
            
            # Update agent stats
            if agent_id in self.agent_stats:
                self.agent_stats[agent_id]['status'] = 'terminated'
                self.agent_stats[agent_id]['termination_time'] = time.time()
            
            # Remove from active agents
            del self.active_agents[agent_id]
            
            self.elite_few.log_and_respond(f"Agent {agent_id} terminated", level="DEBUG", component="AGENT_MANAGER")
            
            return True
            
        except Exception as e:
            self.elite_few.log_and_respond(f"Error terminating agent {agent_id}: {str(e)}", level="ERROR", component="AGENT_MANAGER")
            return False
    
    def terminate_all_agents(self):
        """Terminate all active agents."""
        agent_ids = list(self.active_agents.keys())
        
        for agent_id in agent_ids:
            self.terminate_agent(agent_id)
    
    def is_agent_available(self, agent_type: str) -> bool:
        """
        Check if an agent type is available.
        
        Args:
            agent_type: Type of agent to check
            
        Returns:
            True if agent type is registered, False otherwise
        """
        return agent_type in self.agent_registry
    
    def get_active_agents(self) -> Dict[str, BaseAgent]:
        """
        Get all active agents.
        
        Returns:
            Dictionary of agent_id -> agent_instance
        """
        return self.active_agents
    
    def get_agent_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for agents.
        
        Args:
            agent_id: Optional ID of agent to get stats for (all agents if None)
            
        Returns:
            Dictionary with agent statistics
        """
        if agent_id:
            return self.agent_stats.get(agent_id, {})
        
        return self.agent_stats
    
    def get_registered_agent_types(self) -> List[str]:
        """
        Get all registered agent types.
        
        Returns:
            List of agent type names
        """
        return list(self.agent_registry.keys())