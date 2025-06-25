# -*- coding: utf-8 -*-
"""
WADE Intrusion Detection
Monitors for potential intrusions and security threats.
"""

import os
import sys
import time
import threading
import hashlib
import json
from typing import Dict, List, Any, Optional, Set


class IntrusionDetection:
    """
    Intrusion Detection for WADE.
    Monitors for potential intrusions and security threats.
    """

    def __init__(self):
        """Initialize the intrusion detection system."""
        self.is_monitoring = False
        self.monitor_thread = None
        self.file_hashes = {}  # path -> hash
        self.alerts = []
        self.alert_lock = threading.Lock()
        self.max_alerts = 100
        self.monitored_paths = set()
        self.excluded_paths = set()
        self.monitoring_interval = 60  # seconds

    def start_monitoring(
        self,
        paths: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        interval: int = 60,
    ):
        """
        Start monitoring for intrusions.

        Args:
            paths: List of paths to monitor (defaults to WADE directory)
            excluded_paths: List of paths to exclude from monitoring
            interval: Monitoring interval in seconds
        """
        if self.is_monitoring:
            return

        # Set monitoring parameters
        if paths:
            self.monitored_paths = set(os.path.abspath(p) for p in paths)
        else:
            # Default to WADE directory
            wade_root = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)))
            )
            self.monitored_paths = {wade_root}

        if excluded_paths:
            self.excluded_paths = set(os.path.abspath(p) for p in excluded_paths)
        else:
            # Default excluded paths
            wade_root = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)))
            )
            self.excluded_paths = {
                os.path.join(wade_root, "WADE_RUNTIME", "temp"),
                os.path.join(wade_root, "WADE_RUNTIME", "logs"),
            }

        self.monitoring_interval = interval

        # Initialize file hashes
        self._initialize_file_hashes()

        # Start monitoring thread
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring for intrusions."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                self._check_file_integrity()
                self._check_process_integrity()
                self._check_network_integrity()

                # Sleep for monitoring interval
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self._add_alert(
                    f"Error in monitoring loop: {str(e)}", "ERROR", "MONITORING"
                )

    def _initialize_file_hashes(self):
        """Initialize file hashes for monitored paths."""
        self.file_hashes = {}

        for path in self.monitored_paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Skip excluded paths
                    if any(
                        os.path.abspath(root).startswith(excluded)
                        for excluded in self.excluded_paths
                    ):
                        continue

                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            self.file_hashes[file_path] = self._calculate_file_hash(
                                file_path
                            )
                        except:
                            pass
            elif os.path.isfile(path):
                try:
                    self.file_hashes[path] = self._calculate_file_hash(path)
                except:
                    pass

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash of the file
        """
        hash_obj = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def _check_file_integrity(self):
        """Check integrity of monitored files."""
        for path in self.monitored_paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Skip excluded paths
                    if any(
                        os.path.abspath(root).startswith(excluded)
                        for excluded in self.excluded_paths
                    ):
                        continue

                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Check if file is in hash database
                            if file_path in self.file_hashes:
                                # Calculate current hash
                                current_hash = self._calculate_file_hash(file_path)

                                # Compare with stored hash
                                if current_hash != self.file_hashes[file_path]:
                                    self._add_alert(
                                        f"File modified: {file_path}",
                                        "WARNING",
                                        "FILE_INTEGRITY",
                                    )
                                    self.file_hashes[file_path] = current_hash
                            else:
                                # New file
                                self._add_alert(
                                    f"New file detected: {file_path}",
                                    "INFO",
                                    "FILE_INTEGRITY",
                                )
                                self.file_hashes[file_path] = self._calculate_file_hash(
                                    file_path
                                )
                        except:
                            pass
            elif os.path.isfile(path):
                try:
                    # Check if file is in hash database
                    if path in self.file_hashes:
                        # Calculate current hash
                        current_hash = self._calculate_file_hash(path)

                        # Compare with stored hash
                        if current_hash != self.file_hashes[path]:
                            self._add_alert(
                                f"File modified: {path}", "WARNING", "FILE_INTEGRITY"
                            )
                            self.file_hashes[path] = current_hash
                except:
                    pass

        # Check for deleted files
        deleted_files = []
        for file_path in self.file_hashes:
            if not os.path.exists(file_path):
                self._add_alert(
                    f"File deleted: {file_path}", "WARNING", "FILE_INTEGRITY"
                )
                deleted_files.append(file_path)

        # Remove deleted files from hash database
        for file_path in deleted_files:
            del self.file_hashes[file_path]

    def _check_process_integrity(self):
        """Check integrity of WADE processes."""
        # Get current process ID
        current_pid = os.getpid()

        try:
            import psutil

            # Check if any suspicious processes are running
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    # Skip current process
                    if proc.info["pid"] == current_pid:
                        continue

                    # Check if process is accessing WADE files
                    for path in self.monitored_paths:
                        if any(path in cmd for cmd in (proc.info["cmdline"] or [])):
                            self._add_alert(
                                f"Process accessing WADE files: {proc.info['name']} (PID: {proc.info['pid']})",
                                "WARNING",
                                "PROCESS_INTEGRITY",
                            )
                except:
                    pass
        except ImportError:
            pass

    def _check_network_integrity(self):
        """Check network integrity."""
        try:
            import psutil

            # Get network connections
            connections = psutil.net_connections(kind="inet")

            # Check for suspicious connections
            for conn in connections:
                if conn.status == "ESTABLISHED" and conn.laddr.port < 1024:
                    self._add_alert(
                        f"Suspicious network connection: {conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port}",
                        "WARNING",
                        "NETWORK_INTEGRITY",
                    )
        except ImportError:
            pass

    def _add_alert(
        self, message: str, level: str = "INFO", component: str = "INTRUSION_DETECTION"
    ):
        """
        Add an alert to the alert list.

        Args:
            message: Alert message
            level: Alert level
            component: Alert component
        """
        with self.alert_lock:
            alert = {
                "timestamp": time.time(),
                "level": level,
                "component": component,
                "message": message,
            }

            self.alerts.append(alert)

            # Limit number of alerts
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts :]

    def get_alerts(
        self, limit: int = 10, level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts.

        Args:
            limit: Maximum number of alerts to return
            level: Optional level filter

        Returns:
            List of alerts
        """
        with self.alert_lock:
            if level:
                filtered_alerts = [
                    alert for alert in self.alerts if alert["level"] == level
                ]
            else:
                filtered_alerts = list(self.alerts)

            # Sort by timestamp (most recent first)
            filtered_alerts.sort(key=lambda x: x["timestamp"], reverse=True)

            return filtered_alerts[:limit]

    def clear_alerts(self):
        """Clear all alerts."""
        with self.alert_lock:
            self.alerts = []

    def is_system_safe(self) -> bool:
        """
        Check if the system is safe.

        Returns:
            True if the system is safe, False otherwise
        """
        with self.alert_lock:
            # Check for critical alerts
            critical_alerts = [
                alert
                for alert in self.alerts
                if alert["level"] in ["CRITICAL", "ERROR"]
            ]

            # System is safe if there are no critical alerts
            return len(critical_alerts) == 0
