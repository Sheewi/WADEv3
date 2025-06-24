# -*- coding: utf-8 -*-
"""
WADE Task Router
Routes tasks to appropriate handlers.
"""

import os
import sys
import re
import time
import logging
from typing import Dict, List, Any, Optional, Callable

class TaskRouter:
    """
    Task Router for WADE.
    Routes tasks to appropriate handlers based on content and context.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the task router.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.logger = logging.getLogger('wade.task_router')
        
        # Initialize task handlers
        self.task_handlers = {}
        self.task_patterns = []
        
        # Register built-in task handlers
        self._register_built_in_handlers()
    
    def _register_built_in_handlers(self):
        """Register built-in task handlers."""
        # System information tasks
        self.register_task_handler(
            r'(?i)(?:what|show|tell|give).*(?:system|computer|machine).*(?:info|information|status|specs|specification)',
            self._handle_system_info_task,
            'system_info'
        )
        
        # File operations tasks
        self.register_task_handler(
            r'(?i)(?:list|show|display).*(?:files|directories|folder)',
            self._handle_file_list_task,
            'file_list'
        )
        
        self.register_task_handler(
            r'(?i)(?:read|open|show|display|cat).*(?:file|content)',
            self._handle_file_read_task,
            'file_read'
        )
        
        # Network tasks
        self.register_task_handler(
            r'(?i)(?:show|display|list).*(?:network|connection|ip|interface)',
            self._handle_network_task,
            'network_info'
        )
        
        # Process tasks
        self.register_task_handler(
            r'(?i)(?:show|display|list).*(?:process|running)',
            self._handle_process_task,
            'process_list'
        )
        
        # Agent tasks
        self.register_task_handler(
            r'(?i)(?:create|add|spawn).*(?:agent|monk|sage|warrior|diplomat)',
            self._handle_agent_creation_task,
            'agent_creation'
        )
        
        # Memory tasks
        self.register_task_handler(
            r'(?i)(?:remember|store|save).*(?:this|that|it|information|data)',
            self._handle_memory_store_task,
            'memory_store'
        )
        
        self.register_task_handler(
            r'(?i)(?:recall|retrieve|get|what).*(?:did you remember|did I tell you|do you know about)',
            self._handle_memory_recall_task,
            'memory_recall'
        )
        
        # Tool execution tasks
        self.register_task_handler(
            r'(?i)(?:run|execute|use).*(?:tool|command)',
            self._handle_tool_execution_task,
            'tool_execution'
        )
    
    def register_task_handler(self, pattern: str, handler: Callable, task_type: str):
        """
        Register a task handler.
        
        Args:
            pattern: Regular expression pattern to match tasks
            handler: Function to handle matching tasks
            task_type: Type of task
        """
        self.task_patterns.append((re.compile(pattern), task_type))
        self.task_handlers[task_type] = handler
        
        self.logger.debug(f"Registered task handler for {task_type}")
    
    def route_task(self, task: str) -> Optional[str]:
        """
        Route a task to the appropriate handler.
        
        Args:
            task: Task to route
            
        Returns:
            Response from handler or None if no handler matched
        """
        # Check for exact command matches first
        if self.elite_few.console_parser:
            handled, response = self.elite_few.console_parser.parse_input(task)
            
            if handled:
                return response
        
        # Check for pattern matches
        for pattern, task_type in self.task_patterns:
            if pattern.search(task):
                self.logger.debug(f"Task matched pattern for {task_type}")
                
                if task_type in self.task_handlers:
                    try:
                        return self.task_handlers[task_type](task)
                    except Exception as e:
                        self.logger.error(f"Error handling task {task_type}: {e}")
                        return f"I encountered an error while processing your request: {str(e)}"
        
        # No handler matched, use agents
        return self._route_to_agents(task)
    
    def _route_to_agents(self, task: str) -> Optional[str]:
        """
        Route a task to agents.
        
        Args:
            task: Task to route
            
        Returns:
            Combined response from agents or None if no response
        """
        if not self.elite_few.agent_manager:
            return None
        
        # Get active agents
        active_agents = self.elite_few.agent_manager.get_active_agents()
        
        if not active_agents:
            return "No active agents available to process your request."
        
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
                self.logger.error(f"Error processing task with agent {agent_id}: {str(e)}")
        
        # Combine responses
        if responses:
            return self._combine_agent_responses(responses)
        
        return None
    
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
    
    def _handle_system_info_task(self, task: str) -> str:
        """
        Handle system information task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with system information
        """
        # Execute system_info tool
        result = self.elite_few.execute_tool('get_system_info', {})
        
        if result.get('status') == 'success':
            info = result.get('data', {})
            
            response = "System Information:\n"
            response += f"Platform: {info.get('platform')} {info.get('platform_release')}\n"
            response += f"Architecture: {info.get('architecture')}\n"
            response += f"Processor: {info.get('processor')}\n"
            response += f"CPU Cores: {info.get('cpu_count')} (Physical), {info.get('cpu_count_logical')} (Logical)\n"
            response += f"Memory: {info.get('memory_total') / (1024**3):.2f} GB Total, {info.get('memory_available') / (1024**3):.2f} GB Available\n"
            response += f"Disk: {info.get('disk_usage', {}).get('total') / (1024**3):.2f} GB Total, {info.get('disk_usage', {}).get('free') / (1024**3):.2f} GB Free\n"
            response += f"Python Version: {info.get('python_version')}\n"
            response += f"Uptime: {info.get('uptime') / 3600:.2f} hours\n"
            
            return response
        else:
            return "Sorry, I couldn't retrieve system information."
    
    def _handle_file_list_task(self, task: str) -> str:
        """
        Handle file list task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with file list
        """
        # Extract path from task
        path_match = re.search(r'(?i)(?:in|at|from)\s+([^\s]+)', task)
        
        if path_match:
            path = path_match.group(1)
        else:
            path = os.getcwd()
        
        # Execute tool
        result = self.elite_few.execute_tool('get_file_info', {'path': path})
        
        if result.get('status') == 'success':
            info = result.get('data', {})
            
            if info.get('is_dir'):
                contents = info.get('contents', [])
                
                response = f"Contents of {path}:\n"
                
                for item in sorted(contents):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        response += f"📁 {item}/\n"
                    else:
                        response += f"📄 {item}\n"
                
                return response
            else:
                return f"{path} is not a directory."
        else:
            return f"Sorry, I couldn't list files in {path}. {result.get('message', '')}"
    
    def _handle_file_read_task(self, task: str) -> str:
        """
        Handle file read task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with file contents
        """
        # Extract path from task
        path_match = re.search(r'(?i)(?:file|content of|read)\s+([^\s]+)', task)
        
        if not path_match:
            return "Please specify a file to read."
        
        path = path_match.group(1)
        
        # Execute tool
        result = self.elite_few.execute_tool('read_file', {'path': path})
        
        if result.get('status') == 'success':
            info = result.get('data', {})
            
            response = f"Contents of {path}:\n\n"
            response += info.get('content', '')
            
            return response
        else:
            return f"Sorry, I couldn't read {path}. {result.get('message', '')}"
    
    def _handle_network_task(self, task: str) -> str:
        """
        Handle network task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with network information
        """
        # Execute tool
        result = self.elite_few.execute_tool('get_network_info', {})
        
        if result.get('status') == 'success':
            info = result.get('data', {})
            
            response = "Network Information:\n\n"
            
            # Interfaces
            response += "Network Interfaces:\n"
            for interface, addresses in info.get('interfaces', {}).items():
                response += f"- {interface}:\n"
                for addr in addresses:
                    response += f"  - {addr.family}: {addr.address}\n"
            
            # Stats
            response += "\nInterface Statistics:\n"
            for interface, stats in info.get('stats', {}).items():
                response += f"- {interface}: {'Up' if stats.isup else 'Down'}, Speed: {stats.speed} Mbps\n"
            
            # Connections
            response += "\nActive Connections:\n"
            for conn in info.get('connections', [])[:10]:  # Limit to 10 connections
                response += f"- {conn.get('laddr', {}).get('ip', '')}:{conn.get('laddr', {}).get('port', '')} -> {conn.get('raddr', {}).get('ip', '')}:{conn.get('raddr', {}).get('port', '')}\n"
            
            return response
        else:
            return "Sorry, I couldn't retrieve network information."
    
    def _handle_process_task(self, task: str) -> str:
        """
        Handle process task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with process information
        """
        # Execute tool
        result = self.elite_few.execute_tool('get_process_list', {})
        
        if result.get('status') == 'success':
            processes = result.get('data', [])
            
            response = "Running Processes:\n\n"
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            # Show top 20 processes
            for proc in processes[:20]:
                response += f"- PID {proc.get('pid')}: {proc.get('name')} (CPU: {proc.get('cpu_percent', 0):.1f}%, MEM: {proc.get('memory_percent', 0):.1f}%)\n"
            
            return response
        else:
            return "Sorry, I couldn't retrieve process information."
    
    def _handle_agent_creation_task(self, task: str) -> str:
        """
        Handle agent creation task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with agent creation result
        """
        if not self.elite_few.agent_manager:
            return "Agent manager not available."
        
        # Extract agent type from task
        agent_types = ['monk', 'sage', 'warrior', 'diplomat', 'explorer', 'architect', 'scholar', 'artisan', 'mentor', 'sentinel']
        
        agent_type = None
        for t in agent_types:
            if t in task.lower():
                agent_type = t
                break
        
        if not agent_type:
            return "Please specify a valid agent type to create."
        
        # Create agent
        agent_id = self.elite_few.agent_manager.create_agent(agent_type)
        
        if agent_id:
            return f"Created {agent_type} agent with ID {agent_id}."
        else:
            return f"Failed to create {agent_type} agent."
    
    def _handle_memory_store_task(self, task: str) -> str:
        """
        Handle memory store task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with memory store result
        """
        if not self.elite_few.stm:
            return "Short-term memory not available."
        
        # Extract key and value from task
        key_match = re.search(r'(?i)(?:remember|store|save)\s+(?:that|this|it)?\s*(?:as|with key|with name)?\s*["\']?([^"\']+)["\']?', task)
        
        if key_match:
            key = key_match.group(1).strip()
        else:
            key = f"memory_{int(time.time())}"
        
        # Extract value
        value_match = re.search(r'(?i)(?:remember|store|save)\s+(?:that|this|it)?\s*["\']?([^"\']+)["\']?', task)
        
        if value_match:
            value = value_match.group(1).strip()
        else:
            value = task
        
        # Store in memory
        self.elite_few.stm.store(key, value)
        
        return f"I've remembered that as '{key}'."
    
    def _handle_memory_recall_task(self, task: str) -> str:
        """
        Handle memory recall task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with memory recall result
        """
        if not self.elite_few.stm:
            return "Short-term memory not available."
        
        # Extract key from task
        key_match = re.search(r'(?i)(?:recall|retrieve|get|what).*(?:about|regarding|concerning|on)\s+["\']?([^"\']+)["\']?', task)
        
        if key_match:
            key = key_match.group(1).strip()
        else:
            return "Please specify what you'd like me to recall."
        
        # Retrieve from memory
        value = self.elite_few.stm.retrieve(key)
        
        if value:
            return f"I remember about '{key}': {value}"
        else:
            return f"I don't have any memory about '{key}'."
    
    def _handle_tool_execution_task(self, task: str) -> str:
        """
        Handle tool execution task.
        
        Args:
            task: Task to handle
            
        Returns:
            Response with tool execution result
        """
        if not self.elite_few.tool_manager:
            return "Tool manager not available."
        
        # Extract tool name from task
        tool_match = re.search(r'(?i)(?:run|execute|use)\s+(?:tool|command)?\s*["\']?([^"\']+)["\']?', task)
        
        if not tool_match:
            return "Please specify a tool to execute."
        
        tool_name = tool_match.group(1).strip()
        
        # Extract parameters from task
        params = {}
        param_matches = re.findall(r'(?i)(?:with|using)\s+([^\s]+)\s*=\s*["\']?([^"\']+)["\']?', task)
        
        for param_name, param_value in param_matches:
            params[param_name] = param_value
        
        # Execute tool
        result = self.elite_few.execute_tool(tool_name, params)
        
        if result.get('status') == 'success':
            return f"Tool '{tool_name}' executed successfully: {result.get('data', '')}"
        else:
            return f"Failed to execute tool '{tool_name}': {result.get('message', '')}"