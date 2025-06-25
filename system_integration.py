#!/usr/bin/env python3
"""
WADE System Integration - IPC mechanisms for Kali Linux integration
"""

import os
import subprocess
import json
import logging
import time
import socket
import threading
import queue
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable

logger = logging.getLogger("WADE.integration")

class SystemIntegration:
    """System integration for WADE with Kali Linux"""
    
    def __init__(self, memory_dir: Path = None):
        """Initialize system integration"""
        self.memory_dir = memory_dir or Path(os.path.expanduser("~/.wade/memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Command queue for background processing
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Start background worker
        self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
        self.worker_thread.start()
        
        logger.info("System integration initialized")
        
    def _command_worker(self):
        """Background worker for command execution"""
        while True:
            try:
                cmd, callback = self.command_queue.get()
                if cmd is None:
                    break
                    
                logger.info(f"Executing command: {cmd}")
                result = self.execute_command(cmd)
                
                if callback:
                    callback(result)
                    
                self.result_queue.put(result)
                self.command_queue.task_done()
            except Exception as e:
                logger.error(f"Error in command worker: {e}")
                
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command and return the result"""
        try:
            start_time = time.time()
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=60)
            
            execution_time = time.time() - start_time
            
            return {
                "command": command,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "execution_time": execution_time,
                "success": process.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "error": "Command timed out after 60 seconds",
                "success": False
            }
        except Exception as e:
            return {
                "command": command,
                "error": str(e),
                "success": False
            }
            
    def execute_command_async(self, command: str, callback: Callable = None) -> None:
        """Execute a command asynchronously"""
        self.command_queue.put((command, callback))
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        system_info = {}
        
        # Get OS information
        os_info = self.execute_command("cat /etc/os-release")
        if os_info["success"]:
            system_info["os"] = os_info["stdout"]
            
        # Get kernel information
        kernel_info = self.execute_command("uname -a")
        if kernel_info["success"]:
            system_info["kernel"] = kernel_info["stdout"]
            
        # Get CPU information
        cpu_info = self.execute_command("cat /proc/cpuinfo | grep 'model name' | head -1")
        if cpu_info["success"]:
            system_info["cpu"] = cpu_info["stdout"]
            
        # Get memory information
        mem_info = self.execute_command("free -h")
        if mem_info["success"]:
            system_info["memory"] = mem_info["stdout"]
            
        # Get disk information
        disk_info = self.execute_command("df -h")
        if disk_info["success"]:
            system_info["disk"] = disk_info["stdout"]
            
        return system_info
        
    def check_kali_tools(self) -> Dict[str, bool]:
        """Check if common Kali tools are installed"""
        tools = [
            "nmap",
            "metasploit-framework",
            "hydra",
            "sqlmap",
            "aircrack-ng",
            "wireshark",
            "john",
            "hashcat",
            "burpsuite",
            "zaproxy"
        ]
        
        tool_status = {}
        
        for tool in tools:
            result = self.execute_command(f"which {tool}")
            tool_status[tool] = result["success"]
            
        return tool_status
        
    def setup_file_monitoring(self, directory: str, callback: Callable) -> None:
        """Set up file system monitoring for a directory"""
        try:
            import pyinotify
            
            wm = pyinotify.WatchManager()
            mask = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY
            
            class EventHandler(pyinotify.ProcessEvent):
                def process_default(self, event):
                    callback(event)
                    
            handler = EventHandler()
            notifier = pyinotify.ThreadedNotifier(wm, handler)
            notifier.start()
            
            wm.add_watch(directory, mask, rec=True)
            logger.info(f"File monitoring set up for {directory}")
            
            return notifier
        except ImportError:
            logger.error("pyinotify not installed, file monitoring not available")
            return None
        except Exception as e:
            logger.error(f"Error setting up file monitoring: {e}")
            return None
            
    def create_network_socket(self, host: str, port: int) -> socket.socket:
        """Create a network socket for IPC"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.listen(5)
            logger.info(f"Socket created on {host}:{port}")
            return sock
        except Exception as e:
            logger.error(f"Error creating socket: {e}")
            return None
            
    def start_socket_server(self, host: str, port: int, callback: Callable) -> threading.Thread:
        """Start a socket server for IPC"""
        sock = self.create_network_socket(host, port)
        if not sock:
            return None
            
        def server_thread():
            while True:
                try:
                    client, addr = sock.accept()
                    logger.info(f"Connection from {addr}")
                    
                    data = client.recv(4096)
                    if data:
                        callback(data, client)
                except Exception as e:
                    logger.error(f"Error in socket server: {e}")
                    break
                    
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        return thread
        
    def send_to_socket(self, host: str, port: int, data: bytes) -> bool:
        """Send data to a socket"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(data)
            sock.close()
            return True
        except Exception as e:
            logger.error(f"Error sending to socket: {e}")
            return False
            
    def create_named_pipe(self, pipe_name: str) -> str:
        """Create a named pipe for IPC"""
        pipe_path = f"/tmp/{pipe_name}"
        try:
            if not os.path.exists(pipe_path):
                os.mkfifo(pipe_path)
            return pipe_path
        except Exception as e:
            logger.error(f"Error creating named pipe: {e}")
            return None
            
    def read_from_pipe(self, pipe_path: str, callback: Callable) -> threading.Thread:
        """Read from a named pipe"""
        def pipe_reader():
            while True:
                try:
                    with open(pipe_path, "r") as pipe:
                        data = pipe.read()
                        if data:
                            callback(data)
                except Exception as e:
                    logger.error(f"Error reading from pipe: {e}")
                    break
                    
        thread = threading.Thread(target=pipe_reader, daemon=True)
        thread.start()
        return thread
        
    def write_to_pipe(self, pipe_path: str, data: str) -> bool:
        """Write to a named pipe"""
        try:
            with open(pipe_path, "w") as pipe:
                pipe.write(data)
            return True
        except Exception as e:
            logger.error(f"Error writing to pipe: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources"""
        # Stop command worker
        self.command_queue.put((None, None))
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1)
            
        logger.info("System integration cleaned up")


# Create singleton instance
system_integration = SystemIntegration()