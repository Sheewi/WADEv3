# -*- coding: utf-8 -*-
"""
WADE Log Rotator
Advanced log management and rotation system.
"""

import os
import gzip
import shutil
import time
import glob
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class LogRotator:
    """
    Advanced log rotation and management system for WADE.
    Handles log rotation, compression, cleanup, and monitoring.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the log rotator."""
        self.config = config or self._default_config()
        self.active_handlers = {}
        self.rotation_thread = None
        self.running = False
        
        # Ensure log directories exist
        self._ensure_directories()
    
    def _default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'log_dir': '/var/log/wade',
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'max_files': 10,
            'compression': True,
            'retention_days': 30,
            'rotation_interval': 'daily',  # daily, weekly, monthly
            'check_interval': 3600,  # 1 hour
            'logs': {
                'wade.log': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 50 * 1024 * 1024,  # 50MB
                    'backup_count': 5
                },
                'agent.log': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 25 * 1024 * 1024,  # 25MB
                    'backup_count': 3
                },
                'security.log': {
                    'level': 'WARNING',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 10 * 1024 * 1024,  # 10MB
                    'backup_count': 10
                },
                'error.log': {
                    'level': 'ERROR',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 20 * 1024 * 1024,  # 20MB
                    'backup_count': 7
                },
                'audit.log': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 100 * 1024 * 1024,  # 100MB
                    'backup_count': 30
                }
            }
        }
    
    def _ensure_directories(self):
        """Ensure log directories exist."""
        log_dir = self.config['log_dir']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755)
        
        # Create subdirectories for different log types
        subdirs = ['archive', 'temp', 'metrics']
        for subdir in subdirs:
            subdir_path = os.path.join(log_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path, mode=0o755)
    
    def create_logger(self, name: str, log_file: str = None) -> logging.Logger:
        """
        Create a logger with rotation.
        
        Args:
            name: Logger name
            log_file: Log file name (optional)
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        log_file = log_file or f"{name}.log"
        log_config = self.config['logs'].get(log_file, self.config['logs']['wade.log'])
        
        # Set log level
        level = getattr(logging, log_config['level'].upper())
        logger.setLevel(level)
        
        # Create file handler with rotation
        log_path = os.path.join(self.config['log_dir'], log_file)
        handler = RotatingFileHandler(
            log_path,
            maxBytes=log_config['max_size'],
            backupCount=log_config['backup_count']
        )
        
        # Set format
        formatter = logging.Formatter(log_config['format'])
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        # Store handler for management
        self.active_handlers[name] = handler
        
        return logger
    
    def create_timed_logger(self, name: str, log_file: str = None, 
                           when: str = 'midnight', interval: int = 1) -> logging.Logger:
        """
        Create a logger with time-based rotation.
        
        Args:
            name: Logger name
            log_file: Log file name
            when: When to rotate (midnight, H, D, W0-W6)
            interval: Rotation interval
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        
        if logger.handlers:
            return logger
        
        log_file = log_file or f"{name}.log"
        log_config = self.config['logs'].get(log_file, self.config['logs']['wade.log'])
        
        level = getattr(logging, log_config['level'].upper())
        logger.setLevel(level)
        
        log_path = os.path.join(self.config['log_dir'], log_file)
        handler = TimedRotatingFileHandler(
            log_path,
            when=when,
            interval=interval,
            backupCount=log_config['backup_count']
        )
        
        formatter = logging.Formatter(log_config['format'])
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        self.active_handlers[name] = handler
        
        return logger
    
    def rotate_log(self, log_file: str) -> bool:
        """
        Manually rotate a specific log file.
        
        Args:
            log_file: Log file to rotate
            
        Returns:
            True if rotation successful, False otherwise
        """
        try:
            log_path = os.path.join(self.config['log_dir'], log_file)
            
            if not os.path.exists(log_path):
                return False
            
            # Generate timestamp for rotated file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rotated_path = f"{log_path}.{timestamp}"
            
            # Move current log to rotated name
            shutil.move(log_path, rotated_path)
            
            # Compress if enabled
            if self.config['compression']:
                self._compress_file(rotated_path)
            
            # Clean up old files
            self._cleanup_old_files(log_file)
            
            return True
            
        except Exception as e:
            print(f"Error rotating log {log_file}: {e}")
            return False
    
    def _compress_file(self, file_path: str):
        """Compress a log file."""
        try:
            compressed_path = f"{file_path}.gz"
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(file_path)
            
        except Exception as e:
            print(f"Error compressing file {file_path}: {e}")
    
    def _cleanup_old_files(self, log_file: str):
        """Clean up old log files based on retention policy."""
        try:
            log_dir = self.config['log_dir']
            retention_days = self.config['retention_days']
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            
            # Pattern to match rotated files
            pattern = os.path.join(log_dir, f"{log_file}.*")
            
            for file_path in glob.glob(pattern):
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    print(f"Removed old log file: {file_path}")
                    
        except Exception as e:
            print(f"Error cleaning up old files for {log_file}: {e}")
    
    def get_log_stats(self) -> Dict:
        """
        Get statistics about log files.
        
        Returns:
            Dictionary with log statistics
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'files': {}
        }
        
        try:
            log_dir = self.config['log_dir']
            
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_mtime = os.path.getmtime(file_path)
                    
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    
                    stats['files'][file] = {
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(file_mtime).isoformat(),
                        'path': file_path
                    }
            
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def archive_logs(self, days_old: int = 7) -> List[str]:
        """
        Archive logs older than specified days.
        
        Args:
            days_old: Archive logs older than this many days
            
        Returns:
            List of archived files
        """
        archived_files = []
        
        try:
            log_dir = self.config['log_dir']
            archive_dir = os.path.join(log_dir, 'archive')
            cutoff_time = time.time() - (days_old * 24 * 3600)
            
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                
                # Skip directories and current log files
                if os.path.isdir(file_path) or not file.endswith('.log'):
                    continue
                
                if os.path.getmtime(file_path) < cutoff_time:
                    # Create archive filename with timestamp
                    timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
                    archive_name = f"{timestamp.strftime('%Y%m%d')}_{file}"
                    archive_path = os.path.join(archive_dir, archive_name)
                    
                    # Compress and move to archive
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    os.remove(file_path)
                    archived_files.append(archive_path)
                    
        except Exception as e:
            print(f"Error archiving logs: {e}")
        
        return archived_files
    
    def start_rotation_service(self):
        """Start the automatic rotation service."""
        if self.running:
            return
        
        self.running = True
        self.rotation_thread = threading.Thread(target=self._rotation_worker, daemon=True)
        self.rotation_thread.start()
    
    def stop_rotation_service(self):
        """Stop the automatic rotation service."""
        self.running = False
        if self.rotation_thread:
            self.rotation_thread.join(timeout=5)
    
    def _rotation_worker(self):
        """Background worker for automatic rotation."""
        while self.running:
            try:
                # Check each configured log file
                for log_file in self.config['logs'].keys():
                    log_path = os.path.join(self.config['log_dir'], log_file)
                    
                    if os.path.exists(log_path):
                        file_size = os.path.getsize(log_path)
                        max_size = self.config['logs'][log_file]['max_size']
                        
                        if file_size >= max_size:
                            self.rotate_log(log_file)
                
                # Clean up old files
                self._cleanup_all_old_files()
                
                # Sleep until next check
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                print(f"Error in rotation worker: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _cleanup_all_old_files(self):
        """Clean up all old log files."""
        for log_file in self.config['logs'].keys():
            self._cleanup_old_files(log_file)
    
    def export_logs(self, start_date: datetime, end_date: datetime, 
                   log_types: List[str] = None) -> str:
        """
        Export logs for a specific date range.
        
        Args:
            start_date: Start date for export
            end_date: End date for export
            log_types: List of log types to export (None for all)
            
        Returns:
            Path to exported archive
        """
        try:
            log_dir = self.config['log_dir']
            temp_dir = os.path.join(log_dir, 'temp')
            
            # Create export directory
            export_name = f"wade_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            export_dir = os.path.join(temp_dir, export_name)
            os.makedirs(export_dir, exist_ok=True)
            
            # Collect relevant log files
            log_types = log_types or list(self.config['logs'].keys())
            
            for log_type in log_types:
                # Find all files for this log type
                pattern = os.path.join(log_dir, f"{log_type}*")
                
                for file_path in glob.glob(pattern):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if start_date <= file_mtime <= end_date:
                        dest_path = os.path.join(export_dir, os.path.basename(file_path))
                        shutil.copy2(file_path, dest_path)
            
            # Create archive
            archive_path = f"{export_dir}.tar.gz"
            shutil.make_archive(export_dir, 'gztar', temp_dir, export_name)
            
            # Clean up temporary directory
            shutil.rmtree(export_dir)
            
            return archive_path
            
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return None
    
    def get_log_tail(self, log_file: str, lines: int = 100) -> List[str]:
        """
        Get the last N lines from a log file.
        
        Args:
            log_file: Log file name
            lines: Number of lines to return
            
        Returns:
            List of log lines
        """
        try:
            log_path = os.path.join(self.config['log_dir'], log_file)
            
            if not os.path.exists(log_path):
                return []
            
            with open(log_path, 'r') as f:
                return f.readlines()[-lines:]
                
        except Exception as e:
            return [f"Error reading log file: {e}"]
    
    def search_logs(self, pattern: str, log_files: List[str] = None, 
                   max_results: int = 1000) -> List[Dict]:
        """
        Search for a pattern in log files.
        
        Args:
            pattern: Search pattern (regex)
            log_files: List of log files to search (None for all)
            max_results: Maximum number of results
            
        Returns:
            List of matching log entries
        """
        import re
        
        results = []
        log_files = log_files or list(self.config['logs'].keys())
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            for log_file in log_files:
                log_path = os.path.join(self.config['log_dir'], log_file)
                
                if not os.path.exists(log_path):
                    continue
                
                with open(log_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                'file': log_file,
                                'line_number': line_num,
                                'content': line.strip(),
                                'timestamp': self._extract_timestamp(line)
                            })
                            
                            if len(results) >= max_results:
                                break
                
                if len(results) >= max_results:
                    break
                    
        except Exception as e:
            results.append({
                'error': f"Search error: {e}"
            })
        
        return results
    
    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        import re
        
        # Common timestamp patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
            r'(\w{3} \d{2} \d{2}:\d{2}:\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_line)
            if match:
                return match.group(1)
        
        return None