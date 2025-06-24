# -*- coding: utf-8 -*-
"""
WADE Error Handler
Comprehensive error handling and recovery system.
"""

import os
import sys
import traceback
import logging
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Type
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import signal
import psutil


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Error categories."""
    SYSTEM = "system"
    SECURITY = "security"
    NETWORK = "network"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    AGENT = "agent"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Error context information."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    traceback_info: str
    component: str
    function: str
    line_number: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    system_info: Optional[Dict] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_actions: List[str] = None


class WADEException(Exception):
    """Base exception class for WADE."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 component: str = None, recoverable: bool = True):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.component = component
        self.recoverable = recoverable
        self.timestamp = datetime.now()


class SecurityException(WADEException):
    """Security-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH):
        super().__init__(message, ErrorCategory.SECURITY, severity, recoverable=False)


class ConfigurationException(WADEException):
    """Configuration-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message, ErrorCategory.CONFIGURATION, severity)


class NetworkException(WADEException):
    """Network-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message, ErrorCategory.NETWORK, severity)


class DatabaseException(WADEException):
    """Database-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH):
        super().__init__(message, ErrorCategory.DATABASE, severity)


class AgentException(WADEException):
    """Agent-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message, ErrorCategory.AGENT, severity)


class ResourceException(WADEException):
    """Resource-related exceptions."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH):
        super().__init__(message, ErrorCategory.RESOURCE, severity)


class ErrorHandler:
    """
    Comprehensive error handling and recovery system for WADE.
    Handles error logging, notification, recovery, and system protection.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the error handler."""
        self.config = config or self._default_config()
        self.error_log = []
        self.error_callbacks = {}
        self.recovery_strategies = {}
        self.circuit_breakers = {}
        self.error_counts = {}
        self.last_errors = {}
        self.shutdown_handlers = []
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Error tracking
        self.error_lock = threading.RLock()
        
        # Recovery thread
        self.recovery_thread = None
        self.recovery_running = False
        
        # System protection
        self.protection_enabled = self.config.get('protection', {}).get('enabled', True)
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def _default_config(self) -> Dict:
        """Get default error handler configuration."""
        return {
            'logging': {
                'file': '/var/log/wade/error.log',
                'level': 'ERROR',
                'max_size': 100 * 1024 * 1024,  # 100MB
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'notifications': {
                'enabled': True,
                'email': {
                    'enabled': False,
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'recipients': []
                },
                'webhook': {
                    'enabled': False,
                    'url': None,
                    'timeout': 10
                }
            },
            'recovery': {
                'enabled': True,
                'max_attempts': 3,
                'retry_delay': 5,
                'escalation_delay': 300
            },
            'circuit_breaker': {
                'enabled': True,
                'failure_threshold': 5,
                'recovery_timeout': 60,
                'half_open_max_calls': 3
            },
            'protection': {
                'enabled': True,
                'memory_threshold': 90,  # percent
                'cpu_threshold': 95,     # percent
                'disk_threshold': 95,    # percent
                'emergency_shutdown': True
            },
            'rate_limiting': {
                'enabled': True,
                'max_errors_per_minute': 100,
                'max_errors_per_hour': 1000
            }
        }
    
    def _setup_logging(self):
        """Setup error logging."""
        try:
            log_config = self.config['logging']
            
            # Create logger
            self.logger = logging.getLogger('wade.error')
            self.logger.setLevel(getattr(logging, log_config['level']))
            
            # Create file handler
            log_file = log_config['file']
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config['max_size'],
                backupCount=log_config['backup_count']
            )
            
            # Create formatter
            formatter = logging.Formatter(log_config['format'])
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
            
        except Exception as e:
            print(f"Error setting up error logging: {e}")
            # Fall back to console logging
            logging.basicConfig(level=logging.ERROR)
            self.logger = logging.getLogger('wade.error')
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, 'SIGHUP'):
                signal.signal(signal.SIGHUP, self._signal_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received signal {signal_name}, initiating graceful shutdown")
        
        # Execute shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                self.logger.error(f"Error in shutdown handler: {e}")
        
        # Exit gracefully
        sys.exit(0)
    
    def handle_error(self, error: Exception, context: Dict = None) -> ErrorContext:
        """
        Handle an error with comprehensive logging and recovery.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            ErrorContext object with error details
        """
        try:
            with self.error_lock:
                # Create error context
                error_context = self._create_error_context(error, context)
                
                # Log error
                self._log_error(error_context)
                
                # Store error
                self.error_log.append(error_context)
                
                # Update error counts
                self._update_error_counts(error_context)
                
                # Check rate limiting
                if self._is_rate_limited(error_context):
                    self.logger.warning("Error rate limit exceeded, suppressing notifications")
                    return error_context
                
                # Trigger notifications
                self._notify_error(error_context)
                
                # Attempt recovery
                if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
                    self._attempt_recovery(error_context)
                
                # Check system protection
                if self.protection_enabled:
                    self._check_system_protection(error_context)
                
                # Update circuit breakers
                self._update_circuit_breaker(error_context)
                
                return error_context
                
        except Exception as e:
            # Error in error handler - log to console and continue
            print(f"CRITICAL: Error in error handler: {e}")
            traceback.print_exc()
            return None
    
    def _create_error_context(self, error: Exception, context: Dict = None) -> ErrorContext:
        """Create error context from exception."""
        context = context or {}
        
        # Get traceback information
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            last_frame = tb[-1]
            function = last_frame.name
            line_number = last_frame.lineno
            component = os.path.basename(last_frame.filename)
        else:
            function = "unknown"
            line_number = 0
            component = "unknown"
        
        # Determine error category and severity
        if isinstance(error, WADEException):
            category = error.category
            severity = error.severity
        else:
            category = self._categorize_error(error)
            severity = self._assess_severity(error)
        
        # Generate error ID
        error_id = f"{category.value}_{int(time.time())}_{hash(str(error)) % 10000}"
        
        # Collect system information
        system_info = self._collect_system_info() if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL] else None
        
        return ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            exception_type=type(error).__name__,
            traceback_info=traceback.format_exc(),
            component=component,
            function=function,
            line_number=line_number,
            user_id=context.get('user_id'),
            session_id=context.get('session_id'),
            request_id=context.get('request_id'),
            system_info=system_info,
            recovery_actions=[]
        )
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message."""
        error_type = type(error).__name__.lower()
        error_msg = str(error).lower()
        
        if any(keyword in error_type or keyword in error_msg for keyword in 
               ['permission', 'auth', 'login', 'token', 'credential', 'security']):
            return ErrorCategory.SECURITY
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['network', 'connection', 'socket', 'timeout', 'dns', 'http']):
            return ErrorCategory.NETWORK
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['database', 'sql', 'db', 'sqlite', 'postgres', 'mysql']):
            return ErrorCategory.DATABASE
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['config', 'setting', 'parameter', 'option']):
            return ErrorCategory.CONFIGURATION
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['agent', 'task', 'execution', 'worker']):
            return ErrorCategory.AGENT
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['memory', 'disk', 'cpu', 'resource', 'limit', 'quota']):
            return ErrorCategory.RESOURCE
        
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['validation', 'invalid', 'format', 'parse']):
            return ErrorCategory.VALIDATION
        
        else:
            return ErrorCategory.SYSTEM
    
    def _assess_severity(self, error: Exception) -> ErrorSeverity:
        """Assess error severity based on type and impact."""
        error_type = type(error).__name__.lower()
        error_msg = str(error).lower()
        
        # Fatal errors
        if any(keyword in error_type or keyword in error_msg for keyword in 
               ['fatal', 'critical', 'system', 'memory', 'corruption']):
            return ErrorSeverity.FATAL
        
        # Critical errors
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['security', 'breach', 'unauthorized', 'database', 'connection']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['error', 'exception', 'failed', 'timeout']):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        elif any(keyword in error_type or keyword in error_msg for keyword in 
                ['warning', 'deprecated', 'invalid']):
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        else:
            return ErrorSeverity.LOW
    
    def _collect_system_info(self) -> Dict:
        """Collect system information for critical errors."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'process_count': len(psutil.pids()),
                'uptime': time.time() - psutil.boot_time(),
                'python_version': sys.version,
                'platform': sys.platform
            }
        except Exception:
            return {'error': 'Could not collect system info'}
    
    def _log_error(self, error_context: ErrorContext):
        """Log error to file and console."""
        log_message = (
            f"[{error_context.error_id}] {error_context.severity.value.upper()} "
            f"in {error_context.component}:{error_context.function}:{error_context.line_number} - "
            f"{error_context.message}"
        )
        
        if error_context.severity == ErrorSeverity.FATAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log full traceback for high severity errors
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            self.logger.error(f"Traceback for {error_context.error_id}:\n{error_context.traceback_info}")
    
    def _update_error_counts(self, error_context: ErrorContext):
        """Update error counts for monitoring."""
        key = f"{error_context.category.value}_{error_context.severity.value}"
        
        if key not in self.error_counts:
            self.error_counts[key] = {'count': 0, 'last_occurrence': None}
        
        self.error_counts[key]['count'] += 1
        self.error_counts[key]['last_occurrence'] = error_context.timestamp
        
        # Store last error for each category
        self.last_errors[error_context.category.value] = error_context
    
    def _is_rate_limited(self, error_context: ErrorContext) -> bool:
        """Check if error notifications should be rate limited."""
        if not self.config['rate_limiting']['enabled']:
            return False
        
        now = datetime.now()
        category = error_context.category.value
        
        # Count errors in the last minute and hour
        minute_ago = now.timestamp() - 60
        hour_ago = now.timestamp() - 3600
        
        minute_count = sum(1 for err in self.error_log 
                          if err.category.value == category and 
                          err.timestamp.timestamp() > minute_ago)
        
        hour_count = sum(1 for err in self.error_log 
                        if err.category.value == category and 
                        err.timestamp.timestamp() > hour_ago)
        
        max_per_minute = self.config['rate_limiting']['max_errors_per_minute']
        max_per_hour = self.config['rate_limiting']['max_errors_per_hour']
        
        return minute_count > max_per_minute or hour_count > max_per_hour
    
    def _notify_error(self, error_context: ErrorContext):
        """Send error notifications."""
        if not self.config['notifications']['enabled']:
            return
        
        # Only notify for medium severity and above
        if error_context.severity in [ErrorSeverity.LOW]:
            return
        
        # Call registered callbacks
        category_callbacks = self.error_callbacks.get(error_context.category, [])
        general_callbacks = self.error_callbacks.get('all', [])
        
        for callback in category_callbacks + general_callbacks:
            try:
                callback(error_context)
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
        
        # Send email notifications
        if self.config['notifications']['email']['enabled']:
            self._send_email_notification(error_context)
        
        # Send webhook notifications
        if self.config['notifications']['webhook']['enabled']:
            self._send_webhook_notification(error_context)
    
    def _send_email_notification(self, error_context: ErrorContext):
        """Send email notification for error."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            email_config = self.config['notifications']['email']
            
            msg = MIMEMultipart()
            msg['From'] = 'wade@localhost'
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"WADE {error_context.severity.value.upper()} Error: {error_context.error_id}"
            
            body = f"""
WADE Error Report

Error ID: {error_context.error_id}
Timestamp: {error_context.timestamp}
Severity: {error_context.severity.value.upper()}
Category: {error_context.category.value}
Component: {error_context.component}
Function: {error_context.function}
Line: {error_context.line_number}

Message: {error_context.message}

Traceback:
{error_context.traceback_info}
"""
            
            if error_context.system_info:
                body += f"\nSystem Info:\n{json.dumps(error_context.system_info, indent=2)}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    def _send_webhook_notification(self, error_context: ErrorContext):
        """Send webhook notification for error."""
        try:
            import requests
            
            webhook_config = self.config['notifications']['webhook']
            
            payload = {
                'error_id': error_context.error_id,
                'timestamp': error_context.timestamp.isoformat(),
                'severity': error_context.severity.value,
                'category': error_context.category.value,
                'message': error_context.message,
                'component': error_context.component,
                'function': error_context.function,
                'line_number': error_context.line_number
            }
            
            if error_context.system_info:
                payload['system_info'] = error_context.system_info
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                timeout=webhook_config['timeout']
            )
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
    
    def _attempt_recovery(self, error_context: ErrorContext):
        """Attempt to recover from error."""
        if not self.config['recovery']['enabled']:
            return
        
        recovery_strategy = self.recovery_strategies.get(error_context.category)
        if not recovery_strategy:
            return
        
        max_attempts = self.config['recovery']['max_attempts']
        retry_delay = self.config['recovery']['retry_delay']
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Attempting recovery for {error_context.error_id}, attempt {attempt + 1}")
                
                success = recovery_strategy(error_context)
                
                if success:
                    error_context.recovery_attempted = True
                    error_context.recovery_successful = True
                    error_context.recovery_actions.append(f"Recovery successful on attempt {attempt + 1}")
                    self.logger.info(f"Recovery successful for {error_context.error_id}")
                    return
                
                if attempt < max_attempts - 1:
                    time.sleep(retry_delay)
                    
            except Exception as e:
                error_context.recovery_actions.append(f"Recovery attempt {attempt + 1} failed: {str(e)}")
                self.logger.error(f"Recovery attempt {attempt + 1} failed for {error_context.error_id}: {e}")
        
        error_context.recovery_attempted = True
        error_context.recovery_successful = False
        self.logger.error(f"All recovery attempts failed for {error_context.error_id}")
    
    def _check_system_protection(self, error_context: ErrorContext):
        """Check if system protection measures should be triggered."""
        if not self.protection_enabled:
            return
        
        protection_config = self.config['protection']
        
        try:
            # Check resource usage
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            critical_resource = False
            
            if cpu_percent > protection_config['cpu_threshold']:
                self.logger.critical(f"CPU usage critical: {cpu_percent}%")
                critical_resource = True
            
            if memory_percent > protection_config['memory_threshold']:
                self.logger.critical(f"Memory usage critical: {memory_percent}%")
                critical_resource = True
            
            if disk_percent > protection_config['disk_threshold']:
                self.logger.critical(f"Disk usage critical: {disk_percent}%")
                critical_resource = True
            
            # Emergency shutdown if resources are critical and we have fatal errors
            if (critical_resource and 
                error_context.severity == ErrorSeverity.FATAL and 
                protection_config['emergency_shutdown']):
                
                self.logger.critical("Initiating emergency shutdown due to critical resource usage and fatal error")
                self._emergency_shutdown()
                
        except Exception as e:
            self.logger.error(f"Error in system protection check: {e}")
    
    def _emergency_shutdown(self):
        """Perform emergency shutdown."""
        self.logger.critical("EMERGENCY SHUTDOWN INITIATED")
        
        # Execute shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                self.logger.error(f"Error in emergency shutdown handler: {e}")
        
        # Force exit
        os._exit(1)
    
    def _update_circuit_breaker(self, error_context: ErrorContext):
        """Update circuit breaker state."""
        if not self.config['circuit_breaker']['enabled']:
            return
        
        component = error_context.component
        
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = {
                'state': 'closed',
                'failure_count': 0,
                'last_failure': None,
                'half_open_calls': 0
            }
        
        breaker = self.circuit_breakers[component]
        config = self.config['circuit_breaker']
        
        # Increment failure count
        breaker['failure_count'] += 1
        breaker['last_failure'] = datetime.now()
        
        # Check if we should open the circuit
        if (breaker['state'] == 'closed' and 
            breaker['failure_count'] >= config['failure_threshold']):
            
            breaker['state'] = 'open'
            self.logger.warning(f"Circuit breaker opened for component: {component}")
    
    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies[ErrorCategory.NETWORK] = self._recover_network_error
        self.recovery_strategies[ErrorCategory.DATABASE] = self._recover_database_error
        self.recovery_strategies[ErrorCategory.CONFIGURATION] = self._recover_config_error
        self.recovery_strategies[ErrorCategory.AGENT] = self._recover_agent_error
    
    def _recover_network_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from network errors."""
        try:
            # Wait and retry
            time.sleep(2)
            
            # Test basic connectivity
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            
            return result == 0
            
        except Exception:
            return False
    
    def _recover_database_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from database errors."""
        try:
            # Basic database recovery - would need specific implementation
            # For now, just wait and return True to indicate recovery attempt
            time.sleep(1)
            return True
            
        except Exception:
            return False
    
    def _recover_config_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from configuration errors."""
        try:
            # Reload configuration
            # This would need integration with ConfigManager
            return True
            
        except Exception:
            return False
    
    def _recover_agent_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from agent errors."""
        try:
            # Restart agent - would need integration with AgentManager
            return True
            
        except Exception:
            return False
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable[[ErrorContext], None]):
        """Register error notification callback."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable[[ErrorContext], bool]):
        """Register recovery strategy for error category."""
        self.recovery_strategies[category] = strategy
    
    def register_shutdown_handler(self, handler: Callable[[], None]):
        """Register shutdown handler."""
        self.shutdown_handlers.append(handler)
    
    def get_error_stats(self) -> Dict:
        """Get error statistics."""
        with self.error_lock:
            total_errors = len(self.error_log)
            
            # Count by severity
            severity_counts = {}
            for severity in ErrorSeverity:
                severity_counts[severity.value] = sum(
                    1 for err in self.error_log if err.severity == severity
                )
            
            # Count by category
            category_counts = {}
            for category in ErrorCategory:
                category_counts[category.value] = sum(
                    1 for err in self.error_log if err.category == category
                )
            
            # Recent errors (last hour)
            hour_ago = datetime.now().timestamp() - 3600
            recent_errors = [
                err for err in self.error_log 
                if err.timestamp.timestamp() > hour_ago
            ]
            
            return {
                'total_errors': total_errors,
                'recent_errors': len(recent_errors),
                'severity_counts': severity_counts,
                'category_counts': category_counts,
                'circuit_breakers': self.circuit_breakers,
                'last_errors': {k: asdict(v) for k, v in self.last_errors.items()}
            }
    
    def clear_error_log(self):
        """Clear error log (use with caution)."""
        with self.error_lock:
            self.error_log.clear()
            self.error_counts.clear()
            self.last_errors.clear()


def error_handler(category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 recoverable: bool = True):
    """
    Decorator for automatic error handling.
    
    Args:
        category: Error category
        severity: Error severity
        recoverable: Whether error is recoverable
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance (would need to be injected)
                error_handler_instance = getattr(wrapper, '_error_handler', None)
                
                if error_handler_instance:
                    context = {
                        'function': func.__name__,
                        'args': str(args)[:100],  # Truncate for safety
                        'kwargs': str(kwargs)[:100]
                    }
                    error_handler_instance.handle_error(e, context)
                
                if not recoverable:
                    raise
                
                return None
        
        return wrapper
    return decorator


def retry_on_error(max_attempts: int = 3, delay: float = 1.0, 
                  backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions on error.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


# Global error handler instance
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_error_handler(handler: ErrorHandler):
    """Set global error handler instance."""
    global _global_error_handler
    _global_error_handler = handler