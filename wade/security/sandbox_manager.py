# -*- coding: utf-8 -*-
"""
WADE Sandbox Manager
Manages sandboxed execution environments.
"""

import os
import sys
import subprocess
import time
import uuid
from typing import Dict, List, Any, Optional

class SandboxManager:
    """
    Sandbox Manager for WADE.
    Manages sandboxed execution environments for secure operations.
    """
    
    def __init__(self):
        """Initialize the sandbox manager."""
        self.active_sandboxes = {}  # id -> sandbox_info
        self.sandbox_stats = {}  # id -> stats
    
    def create_sandbox(self, sandbox_type: str = 'default', name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new sandbox.
        
        Args:
            sandbox_type: Type of sandbox to create
            name: Optional name for the sandbox
            
        Returns:
            Dictionary with sandbox information
        """
        # Generate sandbox ID
        sandbox_id = str(uuid.uuid4())
        
        # Generate sandbox name if not provided
        if not name:
            name = f"sandbox_{int(time.time())}"
        
        # Create sandbox based on type
        if sandbox_type == 'default':
            sandbox_info = self._create_default_sandbox(sandbox_id, name)
        elif sandbox_type == 'docker':
            sandbox_info = self._create_docker_sandbox(sandbox_id, name)
        elif sandbox_type == 'chroot':
            sandbox_info = self._create_chroot_sandbox(sandbox_id, name)
        else:
            return {
                'status': 'error',
                'message': f"Unknown sandbox type: {sandbox_type}"
            }
        
        if sandbox_info.get('status') == 'error':
            return sandbox_info
        
        # Store sandbox information
        self.active_sandboxes[sandbox_id] = sandbox_info
        
        # Initialize sandbox stats
        self.sandbox_stats[sandbox_id] = {
            'creation_time': time.time(),
            'execution_count': 0,
            'last_execution': None
        }
        
        return {
            'status': 'success',
            'sandbox_id': sandbox_id,
            'sandbox_info': sandbox_info
        }
    
    def _create_default_sandbox(self, sandbox_id: str, name: str) -> Dict[str, Any]:
        """
        Create a default sandbox (simple directory isolation).
        
        Args:
            sandbox_id: ID of the sandbox
            name: Name of the sandbox
            
        Returns:
            Dictionary with sandbox information
        """
        # Create sandbox directory
        sandbox_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WADE_RUNTIME', 'temp', f"sandbox_{sandbox_id}"))
        
        try:
            os.makedirs(sandbox_dir, exist_ok=True)
            
            # Create sandbox information
            sandbox_info = {
                'id': sandbox_id,
                'name': name,
                'type': 'default',
                'directory': sandbox_dir,
                'status': 'active',
                'creation_time': time.time()
            }
            
            return sandbox_info
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error creating default sandbox: {str(e)}"
            }
    
    def _create_docker_sandbox(self, sandbox_id: str, name: str) -> Dict[str, Any]:
        """
        Create a Docker sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            name: Name of the sandbox
            
        Returns:
            Dictionary with sandbox information
        """
        # Check if Docker is available
        try:
            result = subprocess.run(['docker', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': "Docker not available"
                }
            
            # Create Docker container
            container_name = f"wade_sandbox_{sandbox_id}"
            
            result = subprocess.run(
                ['docker', 'run', '-d', '--name', container_name, '-it', 'alpine:latest', 'sh'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f"Error creating Docker container: {result.stderr}"
                }
            
            container_id = result.stdout.strip()
            
            # Create sandbox information
            sandbox_info = {
                'id': sandbox_id,
                'name': name,
                'type': 'docker',
                'container_id': container_id,
                'container_name': container_name,
                'status': 'active',
                'creation_time': time.time()
            }
            
            return sandbox_info
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error creating Docker sandbox: {str(e)}"
            }
    
    def _create_chroot_sandbox(self, sandbox_id: str, name: str) -> Dict[str, Any]:
        """
        Create a chroot sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            name: Name of the sandbox
            
        Returns:
            Dictionary with sandbox information
        """
        # Check if running as root
        if os.geteuid() != 0:
            return {
                'status': 'error',
                'message': "Root privileges required for chroot sandbox"
            }
        
        # Create chroot directory
        chroot_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WADE_RUNTIME', 'temp', f"chroot_{sandbox_id}"))
        
        try:
            os.makedirs(chroot_dir, exist_ok=True)
            
            # Create minimal filesystem
            os.makedirs(os.path.join(chroot_dir, 'bin'), exist_ok=True)
            os.makedirs(os.path.join(chroot_dir, 'lib'), exist_ok=True)
            os.makedirs(os.path.join(chroot_dir, 'lib64'), exist_ok=True)
            os.makedirs(os.path.join(chroot_dir, 'usr', 'bin'), exist_ok=True)
            os.makedirs(os.path.join(chroot_dir, 'usr', 'lib'), exist_ok=True)
            
            # Copy essential binaries
            for binary in ['sh', 'ls', 'cat', 'echo']:
                binary_path = subprocess.run(['which', binary], stdout=subprocess.PIPE, text=True).stdout.strip()
                if binary_path:
                    os.system(f"cp {binary_path} {os.path.join(chroot_dir, 'bin')}")
            
            # Create sandbox information
            sandbox_info = {
                'id': sandbox_id,
                'name': name,
                'type': 'chroot',
                'directory': chroot_dir,
                'status': 'active',
                'creation_time': time.time()
            }
            
            return sandbox_info
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error creating chroot sandbox: {str(e)}"
            }
    
    def execute_in_sandbox(self, sandbox_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in a sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        if sandbox_id not in self.active_sandboxes:
            return {
                'status': 'error',
                'message': f"Sandbox not found: {sandbox_id}"
            }
        
        sandbox_info = self.active_sandboxes[sandbox_id]
        
        # Update sandbox stats
        if sandbox_id in self.sandbox_stats:
            self.sandbox_stats[sandbox_id]['execution_count'] += 1
            self.sandbox_stats[sandbox_id]['last_execution'] = time.time()
        
        # Execute command based on sandbox type
        if sandbox_info['type'] == 'default':
            return self._execute_in_default_sandbox(sandbox_info, command, timeout)
        elif sandbox_info['type'] == 'docker':
            return self._execute_in_docker_sandbox(sandbox_info, command, timeout)
        elif sandbox_info['type'] == 'chroot':
            return self._execute_in_chroot_sandbox(sandbox_info, command, timeout)
        else:
            return {
                'status': 'error',
                'message': f"Unknown sandbox type: {sandbox_info['type']}"
            }
    
    def _execute_in_default_sandbox(self, sandbox_info: Dict[str, Any], command: str, timeout: int) -> Dict[str, Any]:
        """
        Execute a command in a default sandbox.
        
        Args:
            sandbox_info: Sandbox information
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Change to sandbox directory
            os.chdir(sandbox_info['directory'])
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for process to complete with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            return {
                'status': 'success',
                'return_code': process.returncode,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': f"Command timed out after {timeout} seconds",
                'return_code': -1
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error executing command in default sandbox: {str(e)}",
                'return_code': -1
            }
    
    def _execute_in_docker_sandbox(self, sandbox_info: Dict[str, Any], command: str, timeout: int) -> Dict[str, Any]:
        """
        Execute a command in a Docker sandbox.
        
        Args:
            sandbox_info: Sandbox information
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Execute command in Docker container
            result = subprocess.run(
                ['docker', 'exec', sandbox_info['container_name'], 'sh', '-c', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            return {
                'status': 'success',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': f"Command timed out after {timeout} seconds",
                'return_code': -1
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error executing command in Docker sandbox: {str(e)}",
                'return_code': -1
            }
    
    def _execute_in_chroot_sandbox(self, sandbox_info: Dict[str, Any], command: str, timeout: int) -> Dict[str, Any]:
        """
        Execute a command in a chroot sandbox.
        
        Args:
            sandbox_info: Sandbox information
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Check if running as root
            if os.geteuid() != 0:
                return {
                    'status': 'error',
                    'message': "Root privileges required for chroot sandbox",
                    'return_code': -1
                }
            
            # Execute command in chroot
            result = subprocess.run(
                ['chroot', sandbox_info['directory'], 'sh', '-c', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            return {
                'status': 'success',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': f"Command timed out after {timeout} seconds",
                'return_code': -1
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error executing command in chroot sandbox: {str(e)}",
                'return_code': -1
            }
    
    def destroy_sandbox(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Destroy a sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            Dictionary with destruction status
        """
        if sandbox_id not in self.active_sandboxes:
            return {
                'status': 'error',
                'message': f"Sandbox not found: {sandbox_id}"
            }
        
        sandbox_info = self.active_sandboxes[sandbox_id]
        
        # Destroy sandbox based on type
        if sandbox_info['type'] == 'default':
            result = self._destroy_default_sandbox(sandbox_info)
        elif sandbox_info['type'] == 'docker':
            result = self._destroy_docker_sandbox(sandbox_info)
        elif sandbox_info['type'] == 'chroot':
            result = self._destroy_chroot_sandbox(sandbox_info)
        else:
            return {
                'status': 'error',
                'message': f"Unknown sandbox type: {sandbox_info['type']}"
            }
        
        if result.get('status') == 'success':
            # Remove sandbox from active sandboxes
            del self.active_sandboxes[sandbox_id]
            
            # Keep stats for reference
            if sandbox_id in self.sandbox_stats:
                self.sandbox_stats[sandbox_id]['destruction_time'] = time.time()
        
        return result
    
    def _destroy_default_sandbox(self, sandbox_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Destroy a default sandbox.
        
        Args:
            sandbox_info: Sandbox information
            
        Returns:
            Dictionary with destruction status
        """
        try:
            # Remove sandbox directory
            import shutil
            shutil.rmtree(sandbox_info['directory'])
            
            return {
                'status': 'success',
                'message': f"Default sandbox {sandbox_info['id']} destroyed"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error destroying default sandbox: {str(e)}"
            }
    
    def _destroy_docker_sandbox(self, sandbox_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Destroy a Docker sandbox.
        
        Args:
            sandbox_info: Sandbox information
            
        Returns:
            Dictionary with destruction status
        """
        try:
            # Stop and remove Docker container
            subprocess.run(['docker', 'stop', sandbox_info['container_name']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['docker', 'rm', sandbox_info['container_name']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return {
                'status': 'success',
                'message': f"Docker sandbox {sandbox_info['id']} destroyed"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error destroying Docker sandbox: {str(e)}"
            }
    
    def _destroy_chroot_sandbox(self, sandbox_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Destroy a chroot sandbox.
        
        Args:
            sandbox_info: Sandbox information
            
        Returns:
            Dictionary with destruction status
        """
        try:
            # Remove chroot directory
            import shutil
            shutil.rmtree(sandbox_info['directory'])
            
            return {
                'status': 'success',
                'message': f"Chroot sandbox {sandbox_info['id']} destroyed"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error destroying chroot sandbox: {str(e)}"
            }
    
    def get_active_sandboxes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active sandboxes.
        
        Returns:
            Dictionary of sandbox_id -> sandbox_info
        """
        return self.active_sandboxes
    
    def get_sandbox_info(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            Dictionary with sandbox information or None if not found
        """
        return self.active_sandboxes.get(sandbox_id)
    
    def get_sandbox_stats(self, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for sandboxes.
        
        Args:
            sandbox_id: Optional ID of sandbox to get stats for (all sandboxes if None)
            
        Returns:
            Dictionary with sandbox statistics
        """
        if sandbox_id:
            return self.sandbox_stats.get(sandbox_id, {})
        
        return self.sandbox_stats
    
    def is_sandbox_active(self) -> bool:
        """
        Check if any sandbox is active.
        
        Returns:
            True if at least one sandbox is active, False otherwise
        """
        return len(self.active_sandboxes) > 0