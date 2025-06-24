# -*- coding: utf-8 -*-
"""
WADE Tool Manager
Manages tool lifecycle, discovery, and execution.
"""

import os
import sys
import importlib
import inspect
import time
from typing import Dict, List, Any, Optional, Type, Callable

class ToolManager:
    """
    Tool Manager for WADE.
    Manages the lifecycle, discovery, and execution of tools.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the tool manager.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.tools = {}  # name -> tool_info
        self.tool_modules = {}  # name -> module
        self.tool_stats = {}  # name -> stats
        
        # Discover built-in tools
        self._discover_tools()
    
    def _discover_tools(self):
        """Discover available tools."""
        # Get tools directory
        tools_dir = os.path.dirname(__file__)
        
        # Get all Python files in tools directory
        for filename in os.listdir(tools_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                
                try:
                    # Import module
                    module = importlib.import_module(f"tools.{module_name}")
                    
                    # Look for tool functions
                    for name, obj in inspect.getmembers(module):
                        if name.startswith('tool_') and callable(obj):
                            tool_name = name[5:]  # Remove 'tool_' prefix
                            
                            # Get tool metadata
                            tool_info = {
                                'name': tool_name,
                                'module': module_name,
                                'function': name,
                                'description': obj.__doc__ or f"Tool: {tool_name}",
                                'parameters': self._get_function_parameters(obj)
                            }
                            
                            # Register tool
                            self.tools[tool_name] = tool_info
                            self.tool_modules[tool_name] = module
                            self.tool_stats[tool_name] = {
                                'usage_count': 0,
                                'last_used': None,
                                'avg_execution_time': 0
                            }
                    
                except Exception as e:
                    print(f"Error loading tool module {module_name}: {e}")
    
    def _get_function_parameters(self, func: Callable) -> List[Dict[str, Any]]:
        """
        Get parameters of a function.
        
        Args:
            func: Function to get parameters for
            
        Returns:
            List of parameter information
        """
        params = []
        signature = inspect.signature(func)
        
        for name, param in signature.parameters.items():
            if name == 'self' or name == 'elite_few' or name == 'wade_core':
                continue
            
            param_info = {
                'name': name,
                'required': param.default == inspect.Parameter.empty,
                'default': None if param.default == inspect.Parameter.empty else param.default,
                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any'
            }
            
            params.append(param_info)
        
        return params
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any], wade_core) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            wade_core: Reference to the WADE_OS_Core instance
            
        Returns:
            Dictionary with execution results
        """
        if tool_name not in self.tools:
            return {
                'status': 'error',
                'message': f"Tool '{tool_name}' not found"
            }
        
        tool_info = self.tools[tool_name]
        module = self.tool_modules[tool_name]
        
        # Get tool function
        func = getattr(module, tool_info['function'])
        
        # Record execution start
        start_time = time.time()
        
        try:
            # Execute tool
            result = func(self.elite_few, **params)
            
            # Update stats
            self.tool_stats[tool_name]['usage_count'] += 1
            self.tool_stats[tool_name]['last_used'] = start_time
            
            # Update average execution time
            exec_time = time.time() - start_time
            avg_time = self.tool_stats[tool_name]['avg_execution_time']
            count = self.tool_stats[tool_name]['usage_count']
            
            if count > 1:
                self.tool_stats[tool_name]['avg_execution_time'] = (avg_time * (count - 1) + exec_time) / count
            else:
                self.tool_stats[tool_name]['avg_execution_time'] = exec_time
            
            # Ensure result is a dictionary with status
            if not isinstance(result, dict):
                result = {
                    'status': 'success',
                    'data': result
                }
            
            if 'status' not in result:
                result['status'] = 'success'
            
            return result
            
        except Exception as e:
            # Record execution failure
            self.tool_stats[tool_name]['usage_count'] += 1
            self.tool_stats[tool_name]['last_used'] = start_time
            
            return {
                'status': 'error',
                'message': f"Error executing tool '{tool_name}': {str(e)}"
            }
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available tools.
        
        Returns:
            Dictionary of tool_name -> tool_info
        """
        return self.tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool information or None if not found
        """
        return self.tools.get(tool_name)
    
    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for tools.
        
        Args:
            tool_name: Optional name of tool to get stats for (all tools if None)
            
        Returns:
            Dictionary with tool statistics
        """
        if tool_name:
            return self.tool_stats.get(tool_name, {})
        
        return self.tool_stats
    
    def is_tool_available(self, tool_name: str) -> bool:
        """
        Check if a tool is available.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool is available, False otherwise
        """
        return tool_name in self.tools
    
    def reload_tools(self):
        """Reload all tool modules and discover new tools."""
        # Clear existing tools
        self.tools = {}
        self.tool_modules = {}
        
        # Keep stats
        old_stats = self.tool_stats
        self.tool_stats = {}
        
        # Discover tools
        self._discover_tools()
        
        # Restore stats for existing tools
        for tool_name in self.tools:
            if tool_name in old_stats:
                self.tool_stats[tool_name] = old_stats[tool_name]