# -*- coding: utf-8 -*-
"""
WADE Core Logic
EliteFew reasoning engine.
"""

import os
import sys
import time
import json
import threading
import logging
from typing import Dict, List, Any, Optional

class EliteFew:
    """
    EliteFew reasoning engine for WADE.
    Provides core reasoning and decision-making capabilities.
    """
    
    def __init__(self, wade_core):
        """
        Initialize the EliteFew reasoning engine.
        
        Args:
            wade_core: Reference to the WADE_OS_Core instance
        """
        self.wade_core = wade_core
        self.logger = logging.getLogger('wade.elite_few')
        
        # Initialize components (will be set by WADE_OS_Core)
        self.stm = None  # Short-term memory
        self.ltm = None  # Long-term memory
        self.agent_manager = None  # Agent manager
        self.tool_manager = None  # Tool manager
        self.evolution_engine = None  # Evolution engine
        self.cli_handler = None  # CLI handler
        self.console_parser = None  # Console parser
        self.gui = None  # GUI overlay
        self.intrusion_detection = None  # Intrusion detection
        self.sandbox_manager = None  # Sandbox manager
        self.agent_messaging = None  # Agent messaging
        self.network_stack = None  # Network stack
        
        # Initialize reasoning state
        self.reasoning_state = {
            'current_task': None,
            'task_queue': [],
            'context': {},
            'last_response': None,
            'last_command': None,
            'last_activity': time.time()
        }
        
        self.logger.info("EliteFew reasoning engine initialized")
    
    def log_and_respond(self, message: str, level: str = "INFO", component: str = "ELITE_FEW"):
        """
        Log a message and respond to the user.
        
        Args:
            message: Message to log and respond with
            level: Log level
            component: Component name
        """
        # Log message
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{component}] {message}")
        
        # Respond to user
        if self.cli_handler:
            self.cli_handler.display_output(message, level)
        
        # Send to GUI if available
        if self.gui:
            self.gui.send_message_to_gui({
                'level': level,
                'component': component,
                'message': message
            })
    
    def process_user_command(self, command: str):
        """
        Process a user command.
        
        Args:
            command: User command
        """
        if not command:
            return
        
        # Update reasoning state
        self.reasoning_state['last_command'] = command
        self.reasoning_state['last_activity'] = time.time()
        
        # Try to parse as a console command
        if self.console_parser:
            handled, response = self.console_parser.process_command(command)
            
            if handled:
                if response:
                    self.log_and_respond(response)
                return
        
        # Process as a task
        self._process_task(command)
    
    def _process_task(self, task: str):
        """
        Process a task.
        
        Args:
            task: Task to process
        """
        # Update reasoning state
        self.reasoning_state['current_task'] = task
        
        # Store in short-term memory
        if self.stm:
            self.stm.store('user_input', task)
        
        # Log task
        self.log_and_respond(f"Processing task: {task}", level="INFO", component="TASK")
        
        # Route task to appropriate handler
        if self.wade_core.task_router:
            result = self.wade_core.task_router.route_task(task)
            
            if result:
                self.reasoning_state['last_response'] = result
                self.log_and_respond(result, level="INFO", component="RESPONSE")
            else:
                self.log_and_respond("I'm not sure how to handle that task.", level="WARN", component="RESPONSE")
        else:
            # Fallback to direct agent processing
            self._process_with_agents(task)
    
    def _process_with_agents(self, task: str):
        """
        Process a task with agents.
        
        Args:
            task: Task to process
        """
        if not self.agent_manager:
            self.log_and_respond("Agent manager not available.", level="ERROR", component="AGENTS")
            return
        
        # Get active agents
        active_agents = self.agent_manager.get_active_agents()
        
        if not active_agents:
            self.log_and_respond("No active agents available.", level="WARN", component="AGENTS")
            return
        
        # Process with each agent
        responses = []
        
        for agent_id, agent in active_agents.items():
            try:
                response = agent.process_task(task)
                
                if response:
                    responses.append({
                        'agent_id': agent_id,
                        'agent_type': agent.agent_type,
                        'response': response
                    })
            except Exception as e:
                self.log_and_respond(f"Error processing task with agent {agent_id}: {str(e)}", level="ERROR", component="AGENTS")
        
        # Combine responses
        if responses:
            combined_response = self._combine_agent_responses(responses)
            self.reasoning_state['last_response'] = combined_response
            self.log_and_respond(combined_response, level="INFO", component="RESPONSE")
        else:
            self.log_and_respond("No agent was able to process the task.", level="WARN", component="RESPONSE")
    
    def _combine_agent_responses(self, responses: List[Dict[str, Any]]) -> str:
        """
        Combine responses from multiple agents.
        
        Args:
            responses: List of agent responses
            
        Returns:
            Combined response
        """
        if not responses:
            return ""
        
        if len(responses) == 1:
            return responses[0]['response']
        
        # Combine responses
        combined = "I've consulted multiple agents:\n\n"
        
        for response in responses:
            combined += f"[{response['agent_type']}]: {response['response']}\n\n"
        
        return combined
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Dictionary with execution results
        """
        if not self.tool_manager:
            return {
                'status': 'error',
                'message': "Tool manager not available."
            }
        
        return self.tool_manager.execute_tool(tool_name, params, self.wade_core)
    
    def get_reasoning_state(self) -> Dict[str, Any]:
        """
        Get the current reasoning state.
        
        Returns:
            Dictionary with reasoning state
        """
        return self.reasoning_state
    
    def update_reasoning_state(self, updates: Dict[str, Any]):
        """
        Update the reasoning state.
        
        Args:
            updates: Dictionary with updates to apply
        """
        self.reasoning_state.update(updates)