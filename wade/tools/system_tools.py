# -*- coding: utf-8 -*-
"""
WADE System Tools
Provides system-related tools for WADE.
"""

import os
import sys
import subprocess
import platform
import psutil
import time
from typing import Dict, List, Any, Optional


def tool_get_system_info(elite_few) -> Dict[str, Any]:
    """
    Get detailed system information.

    Returns:
        Dictionary with system information
    """
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": {
            "total": psutil.disk_usage("/").total,
            "used": psutil.disk_usage("/").used,
            "free": psutil.disk_usage("/").free,
            "percent": psutil.disk_usage("/").percent,
        },
        "boot_time": psutil.boot_time(),
        "uptime": time.time() - psutil.boot_time(),
    }

    return {"status": "success", "data": info}


def tool_execute_command(
    elite_few, command: str, timeout: int = 30, shell: bool = False
) -> Dict[str, Any]:
    """
    Execute a system command.

    Args:
        command: Command to execute
        timeout: Timeout in seconds
        shell: Whether to use shell

    Returns:
        Dictionary with execution results
    """
    try:
        # Split command into args if not using shell
        if shell:
            args = command
        else:
            args = command.split()

        # Execute command
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, text=True
        )

        # Wait for process to complete with timeout
        stdout, stderr = process.communicate(timeout=timeout)

        return {
            "status": "success",
            "return_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": f"Command timed out after {timeout} seconds",
            "return_code": -1,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing command: {str(e)}",
            "return_code": -1,
        }


def tool_get_process_list(elite_few) -> Dict[str, Any]:
    """
    Get list of running processes.

    Returns:
        Dictionary with process information
    """
    processes = []

    for proc in psutil.process_iter(
        [
            "pid",
            "name",
            "username",
            "cmdline",
            "cpu_percent",
            "memory_percent",
            "create_time",
        ]
    ):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return {"status": "success", "data": processes}


def tool_get_network_info(elite_few) -> Dict[str, Any]:
    """
    Get network information.

    Returns:
        Dictionary with network information
    """
    network_info = {
        "interfaces": psutil.net_if_addrs(),
        "stats": psutil.net_if_stats(),
        "connections": [conn._asdict() for conn in psutil.net_connections(kind="inet")],
    }

    return {"status": "success", "data": network_info}


def tool_get_file_info(elite_few, path: str) -> Dict[str, Any]:
    """
    Get information about a file or directory.

    Args:
        path: Path to file or directory

    Returns:
        Dictionary with file information
    """
    if not os.path.exists(path):
        return {"status": "error", "message": f"Path not found: {path}"}

    try:
        stat_info = os.stat(path)

        info = {
            "path": path,
            "exists": True,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "is_link": os.path.islink(path),
            "size": stat_info.st_size,
            "mode": stat_info.st_mode,
            "uid": stat_info.st_uid,
            "gid": stat_info.st_gid,
            "atime": stat_info.st_atime,
            "mtime": stat_info.st_mtime,
            "ctime": stat_info.st_ctime,
        }

        if os.path.isdir(path):
            info["contents"] = os.listdir(path)

        return {"status": "success", "data": info}

    except Exception as e:
        return {"status": "error", "message": f"Error getting file info: {str(e)}"}


def tool_read_file(elite_few, path: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
    """
    Read a file.

    Args:
        path: Path to file
        max_size: Maximum file size to read (in bytes)

    Returns:
        Dictionary with file contents
    """
    if not os.path.exists(path):
        return {"status": "error", "message": f"File not found: {path}"}

    if not os.path.isfile(path):
        return {"status": "error", "message": f"Not a file: {path}"}

    try:
        # Check file size
        file_size = os.path.getsize(path)

        if file_size > max_size:
            return {
                "status": "error",
                "message": f"File too large: {file_size} bytes (max: {max_size} bytes)",
            }

        # Read file
        with open(path, "r") as f:
            content = f.read()

        return {
            "status": "success",
            "data": {"path": path, "size": file_size, "content": content},
        }

    except Exception as e:
        return {"status": "error", "message": f"Error reading file: {str(e)}"}


def tool_write_file(
    elite_few, path: str, content: str, mode: str = "w"
) -> Dict[str, Any]:
    """
    Write to a file.

    Args:
        path: Path to file
        content: Content to write
        mode: File mode ('w' for write, 'a' for append)

    Returns:
        Dictionary with write status
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Write to file
        with open(path, mode) as f:
            f.write(content)

        return {
            "status": "success",
            "data": {"path": path, "size": len(content), "mode": mode},
        }

    except Exception as e:
        return {"status": "error", "message": f"Error writing to file: {str(e)}"}
