#!/usr/bin/env python3
"""
Wade CrewAI - System Integration Tools
"""

import subprocess
import os
import sys
import psutil
import json
import time
from typing import Dict, List, Any, Optional
from crewai_tools import BaseTool
from pathlib import Path
import sqlite3
import hashlib

class SystemCommandTool(BaseTool):
    name: str = "System Command Executor"
    description: str = "Execute system commands with full privileges"
    
    def _run(self, command: str, shell: bool = True, timeout: int = 30) -> str:
        """
        Execute system commands
        
        Args:
            command: Command to execute
            shell: Use shell for execution
            timeout: Command timeout in seconds
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = f"Command: {command}\n"
            output += f"Return code: {result.returncode}\n\n"
            
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"Command '{command}' timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing command '{command}': {str(e)}"

class FileSystemTool(BaseTool):
    name: str = "File System Manager"
    description: str = "Manage files and directories with full access"
    
    def _run(self, action: str, path: str, content: str = "", permissions: str = "") -> str:
        """
        File system operations
        
        Args:
            action: Action to perform (read, write, create, delete, list, chmod)
            path: File or directory path
            content: Content for write operations
            permissions: Permissions for chmod (e.g., "755")
        """
        try:
            if action == "read":
                return self._read_file(path)
            elif action == "write":
                return self._write_file(path, content)
            elif action == "create":
                return self._create_directory(path)
            elif action == "delete":
                return self._delete_path(path)
            elif action == "list":
                return self._list_directory(path)
            elif action == "chmod":
                return self._change_permissions(path, permissions)
            else:
                return "Invalid action. Use: read, write, create, delete, list, chmod"
                
        except Exception as e:
            return f"Error in file system operation: {str(e)}"
    
    def _read_file(self, path: str) -> str:
        """Read file content"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return f"File content of {path}:\n\n{content}"
        except Exception as e:
            return f"Error reading file {path}: {str(e)}"
    
    def _write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing file {path}: {str(e)}"
    
    def _create_directory(self, path: str) -> str:
        """Create directory"""
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory created: {path}"
        except Exception as e:
            return f"Error creating directory {path}: {str(e)}"
    
    def _delete_path(self, path: str) -> str:
        """Delete file or directory"""
        try:
            if os.path.isfile(path):
                os.remove(path)
                return f"File deleted: {path}"
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                return f"Directory deleted: {path}"
            else:
                return f"Path not found: {path}"
        except Exception as e:
            return f"Error deleting {path}: {str(e)}"
    
    def _list_directory(self, path: str) -> str:
        """List directory contents"""
        try:
            if not os.path.exists(path):
                return f"Path not found: {path}"
            
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"[FILE] {item} ({size} bytes)")
            
            return f"Contents of {path}:\n\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory {path}: {str(e)}"
    
    def _change_permissions(self, path: str, permissions: str) -> str:
        """Change file/directory permissions"""
        try:
            # Convert string permissions to octal
            perm_octal = int(permissions, 8)
            os.chmod(path, perm_octal)
            return f"Permissions changed for {path} to {permissions}"
        except Exception as e:
            return f"Error changing permissions for {path}: {str(e)}"

class ProcessManagerTool(BaseTool):
    name: str = "Process Manager"
    description: str = "Manage system processes and services"
    
    def _run(self, action: str, process: str = "", signal: str = "TERM") -> str:
        """
        Process management operations
        
        Args:
            action: Action to perform (list, kill, start, stop, info)
            process: Process name or PID
            signal: Signal to send (TERM, KILL, etc.)
        """
        try:
            if action == "list":
                return self._list_processes()
            elif action == "kill":
                return self._kill_process(process, signal)
            elif action == "info":
                return self._process_info(process)
            elif action == "start":
                return self._start_service(process)
            elif action == "stop":
                return self._stop_service(process)
            else:
                return "Invalid action. Use: list, kill, start, stop, info"
                
        except Exception as e:
            return f"Error in process management: {str(e)}"
    
    def _list_processes(self) -> str:
        """List running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(
                        f"PID: {proc.info['pid']:>6} | "
                        f"Name: {proc.info['name']:<20} | "
                        f"CPU: {proc.info['cpu_percent']:>5.1f}% | "
                        f"Memory: {proc.info['memory_percent']:>5.1f}%"
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return "Running processes:\n\n" + "\n".join(processes[:50])  # Limit to 50 processes
        except Exception as e:
            return f"Error listing processes: {str(e)}"
    
    def _kill_process(self, process: str, signal: str) -> str:
        """Kill a process"""
        try:
            # Try to convert to PID first
            try:
                pid = int(process)
                proc = psutil.Process(pid)
            except ValueError:
                # Search by name
                procs = [p for p in psutil.process_iter() if p.name() == process]
                if not procs:
                    return f"Process '{process}' not found"
                proc = procs[0]
                pid = proc.pid
            
            # Send signal
            if signal.upper() == "KILL":
                proc.kill()
            else:
                proc.terminate()
            
            return f"Signal {signal} sent to process {process} (PID: {pid})"
        except Exception as e:
            return f"Error killing process {process}: {str(e)}"
    
    def _process_info(self, process: str) -> str:
        """Get detailed process information"""
        try:
            # Try to convert to PID first
            try:
                pid = int(process)
                proc = psutil.Process(pid)
            except ValueError:
                # Search by name
                procs = [p for p in psutil.process_iter() if p.name() == process]
                if not procs:
                    return f"Process '{process}' not found"
                proc = procs[0]
            
            info = []
            info.append(f"PID: {proc.pid}")
            info.append(f"Name: {proc.name()}")
            info.append(f"Status: {proc.status()}")
            info.append(f"CPU Percent: {proc.cpu_percent():.2f}%")
            info.append(f"Memory Percent: {proc.memory_percent():.2f}%")
            info.append(f"Create Time: {time.ctime(proc.create_time())}")
            
            try:
                info.append(f"Command Line: {' '.join(proc.cmdline())}")
            except:
                info.append("Command Line: Access denied")
            
            return f"Process information:\n\n" + "\n".join(info)
        except Exception as e:
            return f"Error getting process info: {str(e)}"
    
    def _start_service(self, service: str) -> str:
        """Start a system service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'start', service], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"Service '{service}' started successfully"
            else:
                return f"Failed to start service '{service}': {result.stderr}"
        except Exception as e:
            return f"Error starting service {service}: {str(e)}"
    
    def _stop_service(self, service: str) -> str:
        """Stop a system service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'stop', service], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"Service '{service}' stopped successfully"
            else:
                return f"Failed to stop service '{service}': {result.stderr}"
        except Exception as e:
            return f"Error stopping service {service}: {str(e)}"

class NetworkManagerTool(BaseTool):
    name: str = "Network Manager"
    description: str = "Manage network interfaces and connections"
    
    def _run(self, action: str, interface: str = "", ip: str = "", options: str = "") -> str:
        """
        Network management operations
        
        Args:
            action: Action to perform (list, up, down, config, scan)
            interface: Network interface name
            ip: IP address for configuration
            options: Additional options
        """
        try:
            if action == "list":
                return self._list_interfaces()
            elif action == "up":
                return self._interface_up(interface)
            elif action == "down":
                return self._interface_down(interface)
            elif action == "config":
                return self._configure_interface(interface, ip, options)
            elif action == "scan":
                return self._network_scan()
            else:
                return "Invalid action. Use: list, up, down, config, scan"
                
        except Exception as e:
            return f"Error in network management: {str(e)}"
    
    def _list_interfaces(self) -> str:
        """List network interfaces"""
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            result = []
            for interface, addresses in interfaces.items():
                result.append(f"\nInterface: {interface}")
                
                if interface in stats:
                    stat = stats[interface]
                    result.append(f"  Status: {'UP' if stat.isup else 'DOWN'}")
                    result.append(f"  Speed: {stat.speed} Mbps")
                
                for addr in addresses:
                    if addr.family.name == 'AF_INET':
                        result.append(f"  IPv4: {addr.address}")
                        if addr.netmask:
                            result.append(f"  Netmask: {addr.netmask}")
                    elif addr.family.name == 'AF_INET6':
                        result.append(f"  IPv6: {addr.address}")
                    elif addr.family.name == 'AF_PACKET':
                        result.append(f"  MAC: {addr.address}")
            
            return "Network interfaces:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing interfaces: {str(e)}"
    
    def _interface_up(self, interface: str) -> str:
        """Bring interface up"""
        try:
            result = subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"Interface '{interface}' brought up"
            else:
                return f"Failed to bring up interface '{interface}': {result.stderr}"
        except Exception as e:
            return f"Error bringing up interface {interface}: {str(e)}"
    
    def _interface_down(self, interface: str) -> str:
        """Bring interface down"""
        try:
            result = subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'down'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"Interface '{interface}' brought down"
            else:
                return f"Failed to bring down interface '{interface}': {result.stderr}"
        except Exception as e:
            return f"Error bringing down interface {interface}: {str(e)}"
    
    def _configure_interface(self, interface: str, ip: str, options: str) -> str:
        """Configure interface IP"""
        try:
            cmd = ['sudo', 'ip', 'addr', 'add', ip, 'dev', interface]
            if options:
                cmd.extend(options.split())
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return f"Interface '{interface}' configured with IP {ip}"
            else:
                return f"Failed to configure interface '{interface}': {result.stderr}"
        except Exception as e:
            return f"Error configuring interface {interface}: {str(e)}"
    
    def _network_scan(self) -> str:
        """Scan local network"""
        try:
            # Get default gateway
            gateways = psutil.net_if_addrs()
            
            # Simple network discovery using ping
            result = subprocess.run(['nmap', '-sn', '192.168.1.0/24'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return f"Network scan results:\n\n{result.stdout}"
            else:
                return f"Network scan failed: {result.stderr}"
        except Exception as e:
            return f"Error scanning network: {str(e)}"

class ToolManagerTool(BaseTool):
    name: str = "Tool Manager"
    description: str = "Manage Wade's custom tools and scripts"
    
    def _run(self, action: str, tool_name: str = "", code: str = "", language: str = "python") -> str:
        """
        Tool management operations
        
        Args:
            action: Action to perform (save, load, list, execute, delete)
            tool_name: Name of the tool
            code: Tool code content
            language: Programming language (python, bash, etc.)
        """
        try:
            if action == "save":
                return self._save_tool(tool_name, code, language)
            elif action == "load":
                return self._load_tool(tool_name)
            elif action == "list":
                return self._list_tools()
            elif action == "execute":
                return self._execute_tool(tool_name)
            elif action == "delete":
                return self._delete_tool(tool_name)
            else:
                return "Invalid action. Use: save, load, list, execute, delete"
                
        except Exception as e:
            return f"Error in tool management: {str(e)}"
    
    def _save_tool(self, tool_name: str, code: str, language: str) -> str:
        """Save a custom tool"""
        try:
            from config import TOOLS_DIR
            
            # Determine file extension
            extensions = {
                'python': '.py',
                'bash': '.sh',
                'shell': '.sh',
                'c': '.c',
                'cpp': '.cpp',
                'javascript': '.js',
                'perl': '.pl',
                'ruby': '.rb'
            }
            
            ext = extensions.get(language.lower(), '.txt')
            filename = f"{tool_name}{ext}"
            filepath = TOOLS_DIR / filename
            
            # Write tool to file
            with open(filepath, 'w') as f:
                f.write(code)
            
            # Make executable if it's a script
            if ext in ['.py', '.sh', '.pl', '.rb']:
                os.chmod(filepath, 0o755)
            
            # Save metadata
            metadata = {
                'name': tool_name,
                'language': language,
                'created': time.time(),
                'filepath': str(filepath),
                'size': len(code)
            }
            
            self._save_tool_metadata(tool_name, metadata)
            
            return f"Tool '{tool_name}' saved successfully to {filepath}"
        except Exception as e:
            return f"Error saving tool: {str(e)}"
    
    def _load_tool(self, tool_name: str) -> str:
        """Load a custom tool"""
        try:
            from config import TOOLS_DIR
            
            # Find tool file
            for ext in ['.py', '.sh', '.c', '.cpp', '.js', '.pl', '.rb', '.txt']:
                filepath = TOOLS_DIR / f"{tool_name}{ext}"
                if filepath.exists():
                    with open(filepath, 'r') as f:
                        content = f.read()
                    return f"Tool '{tool_name}' content:\n\n```{ext[1:]}\n{content}\n```"
            
            return f"Tool '{tool_name}' not found"
        except Exception as e:
            return f"Error loading tool: {str(e)}"
    
    def _list_tools(self) -> str:
        """List all custom tools"""
        try:
            from config import TOOLS_DIR
            
            tools = []
            for filepath in TOOLS_DIR.glob('*'):
                if filepath.is_file():
                    stat = filepath.stat()
                    tools.append(f"{filepath.name:<30} {stat.st_size:>8} bytes  {time.ctime(stat.st_mtime)}")
            
            if tools:
                return "Custom tools:\n\n" + "\n".join(tools)
            else:
                return "No custom tools found"
        except Exception as e:
            return f"Error listing tools: {str(e)}"
    
    def _execute_tool(self, tool_name: str) -> str:
        """Execute a custom tool"""
        try:
            from config import TOOLS_DIR
            
            # Find and execute tool
            for ext in ['.py', '.sh']:
                filepath = TOOLS_DIR / f"{tool_name}{ext}"
                if filepath.exists():
                    if ext == '.py':
                        cmd = f"python3 {filepath}"
                    elif ext == '.sh':
                        cmd = f"bash {filepath}"
                    
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    
                    output = f"Executed tool '{tool_name}':\n\n"
                    output += f"Return code: {result.returncode}\n"
                    if result.stdout:
                        output += f"Output:\n{result.stdout}\n"
                    if result.stderr:
                        output += f"Errors:\n{result.stderr}\n"
                    
                    return output
            
            return f"Executable tool '{tool_name}' not found"
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    def _delete_tool(self, tool_name: str) -> str:
        """Delete a custom tool"""
        try:
            from config import TOOLS_DIR
            
            deleted = []
            for ext in ['.py', '.sh', '.c', '.cpp', '.js', '.pl', '.rb', '.txt']:
                filepath = TOOLS_DIR / f"{tool_name}{ext}"
                if filepath.exists():
                    filepath.unlink()
                    deleted.append(str(filepath))
            
            if deleted:
                return f"Deleted tool files: {', '.join(deleted)}"
            else:
                return f"Tool '{tool_name}' not found"
        except Exception as e:
            return f"Error deleting tool: {str(e)}"
    
    def _save_tool_metadata(self, tool_name: str, metadata: dict):
        """Save tool metadata to database"""
        try:
            from config import MEMORY_DIR
            
            db_path = MEMORY_DIR / "tools.db"
            
            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS tools (
                        name TEXT PRIMARY KEY,
                        language TEXT,
                        created REAL,
                        filepath TEXT,
                        size INTEGER
                    )
                ''')
                
                conn.execute('''
                    INSERT OR REPLACE INTO tools 
                    (name, language, created, filepath, size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    metadata['name'],
                    metadata['language'],
                    metadata['created'],
                    metadata['filepath'],
                    metadata['size']
                ))
                
                conn.commit()
        except Exception:
            pass  # Metadata is optional

# Export system tools
system_tools = [
    SystemCommandTool(),
    FileSystemTool(),
    ProcessManagerTool(),
    NetworkManagerTool(),
    ToolManagerTool()
]