# -*- coding: utf-8 -*-
"""
WADE_CORE utilities module.
Contains helper functions and utilities used across the WADE system.
"""

import os
import sys
import time
import json
import hashlib
import random
import string
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union

def generate_unique_id(prefix: str = "wade") -> str:
    """Generate a unique ID with optional prefix."""
    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_str}"

def hash_data(data: Union[str, bytes, Dict, List]) -> str:
    """Create a SHA-256 hash of the provided data."""
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True)
    
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    return hashlib.sha256(data).hexdigest()

def execute_command(command: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """
    Execute a system command with timeout.
    
    Args:
        command: List of command and arguments
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    
    except subprocess.TimeoutExpired:
        process.kill()
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", f"Error executing command: {str(e)}"

def is_valid_path(path: str) -> bool:
    """Check if a path is valid and accessible."""
    try:
        return os.path.exists(path)
    except:
        return False

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback to default."""
    try:
        return json.loads(json_str)
    except:
        return default

def safe_file_read(file_path: str, default: str = "") -> str:
    """Safely read file with fallback to default."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except:
        return default

def safe_file_write(file_path: str, content: str) -> bool:
    """Safely write to file with error handling."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except:
        return False

def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    import platform
    
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }
    
    # Add more system info as needed
    
    return info

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters or sequences
    sanitized = input_str.replace(';', '')
    sanitized = sanitized.replace('&&', '')
    sanitized = sanitized.replace('||', '')
    sanitized = sanitized.replace('`', '')
    sanitized = sanitized.replace('$(', '')
    sanitized = sanitized.replace('${', '')
    
    return sanitized