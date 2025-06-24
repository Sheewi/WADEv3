# -*- coding: utf-8 -*-
"""
WADE Utilities
Helper functions for WADE.
"""

import os
import sys
import time
import logging
import json
import hashlib
import base64
import random
import string
from typing import Dict, List, Any, Optional

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging for WADE.
    
    Args:
        log_level: Logging level
        
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.environ.get('WADE_LOGS', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'WADE_RUNTIME', 'logs'))
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up logging
    log_file = os.path.join(logs_dir, f"wade_{time.strftime('%Y%m%d')}.log")
    
    # Convert log level string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create logger
    logger = logging.getLogger('wade')
    
    return logger

def create_directories(paths: Dict[str, str]):
    """
    Create required directories.
    
    Args:
        paths: Dictionary with path configurations
    """
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create runtime directory
    runtime_dir = os.path.abspath(os.path.join(base_dir, paths.get('runtime_dir', 'WADE_RUNTIME')))
    os.makedirs(runtime_dir, exist_ok=True)
    
    # Create logs directory
    logs_dir = os.path.abspath(os.path.join(base_dir, paths.get('logs_dir', 'WADE_RUNTIME/logs')))
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create temp directory
    temp_dir = os.path.abspath(os.path.join(base_dir, paths.get('temp_dir', 'WADE_RUNTIME/temp')))
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create data directory
    data_dir = os.path.abspath(os.path.join(base_dir, paths.get('data_dir', 'datasets')))
    os.makedirs(data_dir, exist_ok=True)

def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID
    """
    # Generate random string
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Generate timestamp
    timestamp = int(time.time())
    
    # Combine prefix, timestamp, and random string
    if prefix:
        return f"{prefix}_{timestamp}_{random_str}"
    else:
        return f"{timestamp}_{random_str}"

def hash_string(s: str) -> str:
    """
    Hash a string using SHA-256.
    
    Args:
        s: String to hash
        
    Returns:
        Hashed string
    """
    return hashlib.sha256(s.encode()).hexdigest()

def encode_base64(s: str) -> str:
    """
    Encode a string as base64.
    
    Args:
        s: String to encode
        
    Returns:
        Base64-encoded string
    """
    return base64.b64encode(s.encode()).decode()

def decode_base64(s: str) -> str:
    """
    Decode a base64-encoded string.
    
    Args:
        s: Base64-encoded string
        
    Returns:
        Decoded string
    """
    return base64.b64decode(s.encode()).decode()

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary with JSON data
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")
        return False

def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp.
    
    Args:
        timestamp: Timestamp to format
        format_str: Format string
        
    Returns:
        Formatted timestamp
    """
    return time.strftime(format_str, time.localtime(timestamp))

def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> float:
    """
    Parse a timestamp string.
    
    Args:
        timestamp_str: Timestamp string to parse
        format_str: Format string
        
    Returns:
        Timestamp as float
    """
    return time.mktime(time.strptime(timestamp_str, format_str))

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename

def get_file_extension(filename: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        filename: Filename
        
    Returns:
        File extension
    """
    return os.path.splitext(filename)[1].lower()

def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logging.error(f"Error getting file size for {file_path}: {e}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Human-readable file size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"