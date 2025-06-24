# -*- coding: utf-8 -*-
"""
WADE System Monitor
Comprehensive system monitoring and alerting.
"""

import os
import psutil
import time
import threading
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import socket
import requests
from collections import deque


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    level: str  # info, warning, error, critical
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SystemMonitor:
    """
    Comprehensive system monitoring for WADE.
    Monitors CPU, memory, disk, network, processes, and custom metrics.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the system monitor."""
        self.config = config or self._default_config()
        self.running = False
        self.monitor_thread = None
        self.metrics_history = {}
        self.active_alerts = {}
        self.alert_callbacks = []
        self.custom_metrics = {}
        
        # Database for storing metrics
        self.db_path = self.config.get('db_path', '/var/lib/wade/monitoring.db')
        self._init_database()
        
        # Metrics buffer for performance
        self.metrics_buffer = deque(maxlen=1000)
        
        # Process monitoring
        self.monitored_processes = {}
        
        # Network monitoring
        self.network_baseline = self._get_network_baseline()
    
    def _default_config(self) -> Dict:
        """Get default monitoring configuration."""
        return {
            'interval': 30,  # seconds
            'retention_days': 30,
            'db_path': '/var/lib/wade/monitoring.db',
            'thresholds': {
                'cpu_percent': {'warning': 70, 'critical': 90},
                'memory_percent': {'warning': 80, 'critical': 95},
                'disk_percent': {'warning': 85, 'critical': 95},
                'load_average': {'warning': 2.0, 'critical': 4.0},
                'response_time': {'warning': 1000, 'critical': 5000},  # ms
                'error_rate': {'warning': 5, 'critical': 10}  # percent
            },
            'alerts': {
                'enabled': True,
                'cooldown': 300,  # seconds
                'escalation_time': 1800  # seconds
            },
            'processes': {
                'wade': {'min_instances': 1, 'max_memory_mb': 512},
                'wade-agent': {'min_instances': 1, 'max_memory_mb': 256}
            },
            'network': {
                'monitor_ports': [8080, 9090],
                'external_checks': [
                    {'url': 'https://httpbin.org/status/200', 'timeout': 5}
                ]
            },
            'custom_metrics': {
                'enabled': True,
                'endpoint': '/metrics'
            }
        }
    
    def _init_database(self):
        """Initialize monitoring database."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        tags TEXT,
                        host TEXT DEFAULT 'localhost'
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        metric TEXT NOT NULL,
                        value REAL NOT NULL,
                        threshold REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                    ON metrics(timestamp)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_name 
                    ON metrics(metric_name)
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Error initializing monitoring database: {e}")
    
    def start_monitoring(self):
        """Start the monitoring service."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print("System monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Collect process metrics
                process_metrics = self._collect_process_metrics()
                metrics.update(process_metrics)
                
                # Collect network metrics
                network_metrics = self._collect_network_metrics()
                metrics.update(network_metrics)
                
                # Collect custom metrics
                custom_metrics = self._collect_custom_metrics()
                metrics.update(custom_metrics)
                
                # Store metrics
                self._store_metrics(metrics)
                
                # Check thresholds and generate alerts
                self._check_thresholds(metrics)
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep until next collection
                time.sleep(self.config['interval'])
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics."""
        metrics = {}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_percent'] = cpu_percent
            
            cpu_count = psutil.cpu_count()
            metrics['cpu_count'] = cpu_count
            
            # Load average (Unix only)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                metrics['load_average_1m'] = load_avg[0]
                metrics['load_average_5m'] = load_avg[1]
                metrics['load_average_15m'] = load_avg[2]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['memory_total'] = memory.total
            metrics['memory_available'] = memory.available
            metrics['memory_used'] = memory.used
            metrics['memory_percent'] = memory.percent
            
            # Swap metrics
            swap = psutil.swap_memory()
            metrics['swap_total'] = swap.total
            metrics['swap_used'] = swap.used
            metrics['swap_percent'] = swap.percent
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            metrics['disk_total'] = disk_usage.total
            metrics['disk_used'] = disk_usage.used
            metrics['disk_free'] = disk_usage.free
            metrics['disk_percent'] = (disk_usage.used / disk_usage.total) * 100
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics['disk_read_bytes'] = disk_io.read_bytes
                metrics['disk_write_bytes'] = disk_io.write_bytes
                metrics['disk_read_count'] = disk_io.read_count
                metrics['disk_write_count'] = disk_io.write_count
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics['network_bytes_sent'] = network_io.bytes_sent
                metrics['network_bytes_recv'] = network_io.bytes_recv
                metrics['network_packets_sent'] = network_io.packets_sent
                metrics['network_packets_recv'] = network_io.packets_recv
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            metrics['uptime_seconds'] = uptime
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def _collect_process_metrics(self) -> Dict[str, float]:
        """Collect process-specific metrics."""
        metrics = {}
        
        try:
            for process_name, config in self.config['processes'].items():
                processes = []
                
                # Find processes by name
                for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                    try:
                        if process_name in proc.info['name']:
                            processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Count instances
                metrics[f'process_{process_name}_count'] = len(processes)
                
                # Aggregate metrics
                total_memory = 0
                total_cpu = 0
                
                for proc in processes:
                    try:
                        memory_info = proc.memory_info()
                        total_memory += memory_info.rss
                        total_cpu += proc.cpu_percent()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                metrics[f'process_{process_name}_memory_mb'] = total_memory / (1024 * 1024)
                metrics[f'process_{process_name}_cpu_percent'] = total_cpu
                
        except Exception as e:
            print(f"Error collecting process metrics: {e}")
        
        return metrics
    
    def _collect_network_metrics(self) -> Dict[str, float]:
        """Collect network-related metrics."""
        metrics = {}
        
        try:
            # Port connectivity checks
            for port in self.config['network']['monitor_ports']:
                is_open = self._check_port(port)
                metrics[f'port_{port}_open'] = 1 if is_open else 0
            
            # External connectivity checks
            for check in self.config['network']['external_checks']:
                response_time = self._check_url(check['url'], check.get('timeout', 5))
                url_key = check['url'].replace('https://', '').replace('http://', '').replace('/', '_')
                metrics[f'external_{url_key}_response_time'] = response_time
                metrics[f'external_{url_key}_available'] = 1 if response_time > 0 else 0
            
            # Network connections
            connections = psutil.net_connections()
            established_count = len([c for c in connections if c.status == 'ESTABLISHED'])
            metrics['network_connections_established'] = established_count
            
        except Exception as e:
            print(f"Error collecting network metrics: {e}")
        
        return metrics
    
    def _collect_custom_metrics(self) -> Dict[str, float]:
        """Collect custom application metrics."""
        metrics = {}
        
        try:
            # Collect from custom metrics registry
            for name, value in self.custom_metrics.items():
                if callable(value):
                    try:
                        metrics[f'custom_{name}'] = float(value())
                    except Exception as e:
                        print(f"Error collecting custom metric {name}: {e}")
                else:
                    metrics[f'custom_{name}'] = float(value)
            
        except Exception as e:
            print(f"Error collecting custom metrics: {e}")
        
        return metrics
    
    def _check_port(self, port: int, host: str = 'localhost') -> bool:
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_url(self, url: str, timeout: int = 5) -> float:
        """Check URL response time."""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            end_time = time.time()
            
            if response.status_code == 200:
                return (end_time - start_time) * 1000  # Convert to milliseconds
            else:
                return -1  # Indicate failure
                
        except Exception:
            return -1
    
    def _get_network_baseline(self) -> Dict:
        """Get network baseline for comparison."""
        try:
            network_io = psutil.net_io_counters()
            return {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'timestamp': time.time()
            }
        except Exception:
            return {'bytes_sent': 0, 'bytes_recv': 0, 'timestamp': time.time()}
    
    def _store_metrics(self, metrics: Dict[str, float]):
        """Store metrics in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for metric_name, value in metrics.items():
                    conn.execute('''
                        INSERT INTO metrics (metric_name, value)
                        VALUES (?, ?)
                    ''', (metric_name, value))
                conn.commit()
                
            # Also store in memory buffer for quick access
            timestamp = datetime.now()
            self.metrics_buffer.append({
                'timestamp': timestamp,
                'metrics': metrics
            })
            
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    def _check_thresholds(self, metrics: Dict[str, float]):
        """Check metrics against thresholds and generate alerts."""
        if not self.config['alerts']['enabled']:
            return
        
        try:
            for metric_name, value in metrics.items():
                # Check if we have thresholds for this metric
                threshold_config = None
                
                # Direct match
                if metric_name in self.config['thresholds']:
                    threshold_config = self.config['thresholds'][metric_name]
                else:
                    # Pattern match (e.g., cpu_percent matches cpu_*)
                    for pattern, config in self.config['thresholds'].items():
                        if pattern in metric_name:
                            threshold_config = config
                            break
                
                if not threshold_config:
                    continue
                
                # Check thresholds
                alert_level = None
                threshold_value = None
                
                if 'critical' in threshold_config and value >= threshold_config['critical']:
                    alert_level = 'critical'
                    threshold_value = threshold_config['critical']
                elif 'warning' in threshold_config and value >= threshold_config['warning']:
                    alert_level = 'warning'
                    threshold_value = threshold_config['warning']
                
                if alert_level:
                    self._create_alert(metric_name, value, threshold_value, alert_level)
                else:
                    # Check if we need to resolve an existing alert
                    self._resolve_alert(metric_name)
                    
        except Exception as e:
            print(f"Error checking thresholds: {e}")
    
    def _create_alert(self, metric: str, value: float, threshold: float, level: str):
        """Create or update an alert."""
        try:
            alert_id = f"{metric}_{level}"
            
            # Check cooldown period
            if alert_id in self.active_alerts:
                last_alert = self.active_alerts[alert_id]
                cooldown = self.config['alerts']['cooldown']
                
                if (datetime.now() - last_alert.timestamp).total_seconds() < cooldown:
                    return  # Still in cooldown
            
            # Create alert
            alert = Alert(
                id=alert_id,
                level=level,
                message=f"{metric} is {value:.2f}, exceeding {level} threshold of {threshold:.2f}",
                metric=metric,
                value=value,
                threshold=threshold,
                timestamp=datetime.now()
            )
            
            self.active_alerts[alert_id] = alert
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO alerts 
                    (id, level, message, metric, value, threshold)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (alert.id, alert.level, alert.message, alert.metric, alert.value, alert.threshold))
                conn.commit()
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Error in alert callback: {e}")
            
            print(f"ALERT [{level.upper()}]: {alert.message}")
            
        except Exception as e:
            print(f"Error creating alert: {e}")
    
    def _resolve_alert(self, metric: str):
        """Resolve alerts for a metric."""
        try:
            alerts_to_resolve = []
            
            for alert_id, alert in self.active_alerts.items():
                if alert.metric == metric and not alert.resolved:
                    alerts_to_resolve.append(alert_id)
            
            for alert_id in alerts_to_resolve:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE alerts 
                        SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (alert_id,))
                    conn.commit()
                
                print(f"RESOLVED: Alert for {alert.metric}")
                
        except Exception as e:
            print(f"Error resolving alert: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and alerts."""
        try:
            retention_days = self.config['retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Clean up old metrics
                conn.execute('''
                    DELETE FROM metrics 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean up old resolved alerts
                conn.execute('''
                    DELETE FROM alerts 
                    WHERE resolved = TRUE AND resolved_at < ?
                ''', (cutoff_date,))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get the most recent metrics."""
        if self.metrics_buffer:
            return self.metrics_buffer[-1]['metrics']
        return {}
    
    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict]:
        """
        Get historical data for a metric.
        
        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to retrieve
            
        Returns:
            List of metric data points
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, value 
                    FROM metrics 
                    WHERE metric_name = ? AND timestamp > ?
                    ORDER BY timestamp
                ''', (metric_name, cutoff_time))
                
                return [
                    {'timestamp': row[0], 'value': row[1]}
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            print(f"Error getting metric history: {e}")
            return []
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_system_health(self) -> Dict:
        """Get overall system health summary."""
        try:
            current_metrics = self.get_current_metrics()
            active_alerts = self.get_active_alerts()
            
            # Calculate health score (0-100)
            health_score = 100
            
            # Deduct points for active alerts
            for alert in active_alerts:
                if alert.level == 'critical':
                    health_score -= 20
                elif alert.level == 'warning':
                    health_score -= 10
            
            # Deduct points for high resource usage
            cpu_percent = current_metrics.get('cpu_percent', 0)
            memory_percent = current_metrics.get('memory_percent', 0)
            disk_percent = current_metrics.get('disk_percent', 0)
            
            if cpu_percent > 80:
                health_score -= 10
            if memory_percent > 80:
                health_score -= 10
            if disk_percent > 80:
                health_score -= 10
            
            health_score = max(0, health_score)
            
            # Determine status
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 70:
                status = 'good'
            elif health_score >= 50:
                status = 'warning'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'health_score': health_score,
                'active_alerts': len(active_alerts),
                'critical_alerts': len([a for a in active_alerts if a.level == 'critical']),
                'warning_alerts': len([a for a in active_alerts if a.level == 'warning']),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'uptime_hours': current_metrics.get('uptime_seconds', 0) / 3600,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add a callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def register_custom_metric(self, name: str, value_func: Callable[[], float]):
        """
        Register a custom metric.
        
        Args:
            name: Metric name
            value_func: Function that returns the metric value
        """
        self.custom_metrics[name] = value_func
    
    def set_custom_metric(self, name: str, value: float):
        """
        Set a custom metric value.
        
        Args:
            name: Metric name
            value: Metric value
        """
        self.custom_metrics[name] = value
    
    def export_metrics(self, format: str = 'prometheus') -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ('prometheus', 'json')
            
        Returns:
            Formatted metrics string
        """
        try:
            current_metrics = self.get_current_metrics()
            
            if format == 'prometheus':
                lines = []
                for metric_name, value in current_metrics.items():
                    # Convert metric name to Prometheus format
                    prom_name = metric_name.replace('.', '_').replace('-', '_')
                    lines.append(f"wade_{prom_name} {value}")
                return '\n'.join(lines)
            
            elif format == 'json':
                return json.dumps(current_metrics, indent=2)
            
            else:
                return f"Unsupported format: {format}"
                
        except Exception as e:
            return f"Error exporting metrics: {e}"