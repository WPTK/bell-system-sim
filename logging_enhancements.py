#!/usr/bin/env python3
"""
Bell System Terminal - Advanced Logging and Diagnostics Module
==============================================================

Professional logging system with structured output, rotation, verbosity control,
and automatic changelog generation for the Bell System simulation.

Features:
- Multi-level structured logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic log rotation with size limits
- Dynamic verbosity control at runtime
- Automatic changelog generation
- Error aggregation and reporting
- Performance monitoring integration
- Session tracking and analytics

Author: Bell System Operations Simulation Project
Version: 2.1
Date: January 2025
"""

import logging
import logging.handlers
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import threading
import queue
import gzip

class BellSystemLogger:
    """
    Advanced logging system for Bell System terminal simulation.
    
    Provides comprehensive logging with rotation, structured output,
    and automatic changelog generation.
    """
    
    def __init__(self, log_dir: str = 'logs'):
        """Initialize the advanced logging system."""
        self.log_dir = log_dir
        self.session_id = f"BELL-{int(time.time())}"
        self.session_start = datetime.now()
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logging components
        self._setup_main_logger()
        self._setup_error_tracking()
        self._setup_performance_monitoring()
        self._setup_changelog_system()
        
        # Background processing
        self._log_queue = queue.Queue()
        self._processing_thread = None
        self._shutdown_event = threading.Event()
        
        self.logger.info(f"Bell System Advanced Logging initialized - Session {self.session_id}")
    
    def _setup_main_logger(self) -> None:
        """Setup the main logging system with multiple handlers."""
        # Main logger
        self.logger = logging.getLogger('BellSystem')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Main rotating file handler
        main_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'bell_system_main.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        main_handler.setLevel(logging.DEBUG)
        
        # Error-only handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'bell_system_errors.log'),
            maxBytes=5*1024*1024,   # 5MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Session-specific handler
        session_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'session_{self.session_id}.log')
        )
        session_handler.setLevel(logging.INFO)
        
        # Console handler for critical issues
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        
        # Structured formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        
        # JSON formatter for structured logs
        json_formatter = JSONFormatter()
        
        main_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        session_handler.setFormatter(json_formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(session_handler)
        self.logger.addHandler(console_handler)
        
        # Store handlers for dynamic level changes
        self.handlers = {
            'main': main_handler,
            'error': error_handler,
            'session': session_handler,
            'console': console_handler
        }
        
        self.current_verbosity = 'INFO'
    
    def _setup_error_tracking(self) -> None:
        """Setup error tracking and aggregation."""
        self.error_counts = defaultdict(int)
        self.recent_errors = deque(maxlen=100)
        self.error_patterns = defaultdict(int)
        
        # Error categories
        self.error_categories = {
            'COMMAND': 'Command execution errors',
            'SYSTEM': 'System-level errors',
            'NETWORK': 'Network operation errors',
            'DATABASE': 'Database operation errors',
            'PERMISSION': 'Permission and access errors',
            'VALIDATION': 'Input validation errors'
        }
    
    def _setup_performance_monitoring(self) -> None:
        """Setup performance monitoring integration."""
        self.performance_metrics = {
            'command_times': defaultdict(list),
            'session_stats': {
                'commands_executed': 0,
                'errors_encountered': 0,
                'session_duration': 0
            },
            'system_stats': {
                'memory_usage': [],
                'cpu_usage': [],
                'disk_usage': []
            }
        }
    
    def _setup_changelog_system(self) -> None:
        """Setup automatic changelog generation."""
        self.changelog_file = 'changelog_auto.txt'
        self.significant_events = deque(maxlen=1000)
        
        # Event types that trigger changelog entries
        self.changelog_triggers = {
            'ERROR': {'threshold': 5, 'description': 'Multiple errors detected'},
            'PERFORMANCE': {'threshold': 10, 'description': 'Performance degradation'},
            'FEATURE': {'threshold': 1, 'description': 'New feature usage'},
            'CONFIG': {'threshold': 1, 'description': 'Configuration change'},
            'SESSION': {'threshold': 1, 'description': 'Session event'}
        }
    
    def set_verbosity(self, level: str) -> bool:
        """Dynamically change logging verbosity."""
        level = level.upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if level not in valid_levels:
            return False
        
        try:
            # Update main handler level
            numeric_level = getattr(logging, level)
            self.handlers['main'].setLevel(numeric_level)
            
            # Update session handler if not DEBUG (to avoid noise)
            if level != 'DEBUG':
                self.handlers['session'].setLevel(numeric_level)
            
            self.current_verbosity = level
            self.logger.info(f"Logging verbosity changed to {level}")
            self.log_event('CONFIG', f"Verbosity changed to {level}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set verbosity: {e}")
            return False
    
    def log_command(self, command: str, args: List[str], execution_time: float, 
                   success: bool, output_size: int = 0) -> None:
        """Log command execution with detailed metrics."""
        self.performance_metrics['command_times'][command].append(execution_time)
        self.performance_metrics['session_stats']['commands_executed'] += 1
        
        if not success:
            self.performance_metrics['session_stats']['errors_encountered'] += 1
        
        # Log with structured data
        log_data = {
            'command': command,
            'args': args,
            'execution_time': execution_time,
            'success': success,
            'output_size': output_size,
            'session_id': self.session_id
        }
        
        if success:
            self.logger.info(f"Command executed: {command}", extra=log_data)
        else:
            self.logger.warning(f"Command failed: {command}", extra=log_data)
    
    def log_error(self, error_type: str, command: str, error_msg: str, 
                 category: str = 'COMMAND') -> None:
        """Log errors with categorization and pattern detection."""
        error_entry = {
            'type': error_type,
            'command': command,
            'message': error_msg,
            'category': category,
            'timestamp': datetime.now(),
            'session_id': self.session_id
        }
        
        self.recent_errors.append(error_entry)
        self.error_counts[command] += 1
        self.error_patterns[error_type] += 1
        
        # Log with appropriate level
        self.logger.error(f"Error in {command}: {error_msg}", extra=error_entry)
        
        # Check for error threshold triggers
        if self.error_counts[command] >= self.changelog_triggers['ERROR']['threshold']:
            self.log_event('ERROR', f"Multiple errors ({self.error_counts[command]}) for command: {command}")
    
    def log_event(self, event_type: str, description: str, 
                 severity: str = 'INFO') -> None:
        """Log significant events for changelog generation."""
        event = {
            'type': event_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now(),
            'session_id': self.session_id
        }
        
        self.significant_events.append(event)
        
        # Log the event
        log_level = getattr(logging, severity.upper(), logging.INFO)
        self.logger.log(log_level, f"Event: {event_type} - {description}", extra=event)
        
        # Check if this should trigger a changelog entry
        self._update_changelog_if_needed(event)
    
    def _update_changelog_if_needed(self, event: Dict[str, Any]) -> None:
        """Update changelog based on event significance."""
        event_type = event['type']
        
        if event_type in self.changelog_triggers:
            trigger = self.changelog_triggers[event_type]
            
            # Count recent events of this type
            recent_count = sum(1 for e in self.significant_events 
                             if e['type'] == event_type and 
                             (datetime.now() - e['timestamp']).seconds < 3600)  # Last hour
            
            if recent_count >= trigger['threshold']:
                self._write_changelog_entry(event)
    
    def _write_changelog_entry(self, event: Dict[str, Any]) -> None:
        """Write entry to changelog file."""
        try:
            timestamp = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            entry = f"[{timestamp}] {event['type']}: {event['description']}\n"
            
            with open(self.changelog_file, 'a', encoding='utf-8') as f:
                f.write(entry)
                
            self.logger.debug(f"Changelog updated: {event['type']} - {event['description']}")
            
        except Exception as e:
            self.logger.error(f"Failed to update changelog: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Generate comprehensive error summary."""
        now = datetime.now()
        
        # Recent errors (last hour)
        recent_errors = [e for e in self.recent_errors 
                        if (now - e['timestamp']).seconds < 3600]
        
        # Error distribution by category
        category_counts = defaultdict(int)
        for error in recent_errors:
            category_counts[error['category']] += 1
        
        # Top error patterns
        pattern_summary = dict(sorted(self.error_patterns.items(), 
                                    key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'total_errors': len(self.recent_errors),
            'recent_errors': len(recent_errors),
            'category_distribution': dict(category_counts),
            'top_patterns': pattern_summary,
            'most_problematic_commands': dict(sorted(self.error_counts.items(), 
                                                   key=lambda x: x[1], reverse=True)[:5])
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance metrics summary."""
        command_stats = {}
        for command, times in self.performance_metrics['command_times'].items():
            if times:
                command_stats[command] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times)
                }
        
        return {
            'session_stats': self.performance_metrics['session_stats'],
            'command_performance': command_stats,
            'session_duration': (datetime.now() - self.session_start).total_seconds()
        }
    
    def generate_session_report(self) -> str:
        """Generate comprehensive session report."""
        error_summary = self.get_error_summary()
        perf_summary = self.get_performance_summary()
        
        report = f"""
BELL SYSTEM SESSION REPORT
===========================
Session ID: {self.session_id}
Start Time: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {perf_summary['session_duration']:.1f} seconds

COMMAND STATISTICS:
------------------
Commands Executed: {perf_summary['session_stats']['commands_executed']}
Errors Encountered: {perf_summary['session_stats']['errors_encountered']}
Success Rate: {((perf_summary['session_stats']['commands_executed'] - perf_summary['session_stats']['errors_encountered']) / max(1, perf_summary['session_stats']['commands_executed']) * 100):.1f}%

TOP COMMANDS BY USAGE:
---------------------
"""
        
        for command, stats in list(perf_summary['command_performance'].items())[:5]:
            report += f"{command}: {stats['count']} times (avg: {stats['avg_time']:.3f}s)\n"
        
        report += f"""
ERROR SUMMARY:
--------------
Total Errors: {error_summary['total_errors']}
Recent Errors: {error_summary['recent_errors']}

TOP ERROR PATTERNS:
------------------
"""
        
        for pattern, count in list(error_summary['top_patterns'].items())[:5]:
            report += f"{pattern}: {count} occurrences\n"
        
        return report
    
    def cleanup(self) -> None:
        """Cleanup logging system and generate final reports."""
        try:
            # Generate final session report
            final_report = self.generate_session_report()
            
            # Write session report
            report_file = os.path.join(self.log_dir, f'session_report_{self.session_id}.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(final_report)
            
            # Compress old session logs
            self._compress_old_logs()
            
            # Final changelog entry
            self.log_event('SESSION', f"Session ended - {self.session_id}")
            
            self.logger.info(f"Session cleanup completed - Report saved to {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _compress_old_logs(self) -> None:
        """Compress old log files to save space."""
        try:
            for filename in os.listdir(self.log_dir):
                if filename.startswith('session_') and filename.endswith('.log'):
                    filepath = os.path.join(self.log_dir, filename)
                    
                    # Check if file is older than 24 hours
                    file_age = time.time() - os.path.getctime(filepath)
                    if file_age > 86400:  # 24 hours
                        # Compress the file
                        with open(filepath, 'rb') as f_in:
                            with gzip.open(filepath + '.gz', 'wb') as f_out:
                                f_out.write(f_in.read())
                        
                        # Remove original
                        os.remove(filepath)
                        self.logger.debug(f"Compressed old log: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Error compressing logs: {e}")

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_obj['session_id'] = record.session_id
        if hasattr(record, 'command'):
            log_obj['command'] = record.command
        if hasattr(record, 'execution_time'):
            log_obj['execution_time'] = record.execution_time
        
        return json.dumps(log_obj)

# Example usage and testing
if __name__ == "__main__":
    # Test the logging system
    logger_system = BellSystemLogger()
    
    # Test various logging scenarios
    logger_system.set_verbosity('DEBUG')
    logger_system.log_command('trunk', ['status'], 0.123, True, 256)
    logger_system.log_error('INVALID_COMMAND', 'trunks', 'Command not found', 'COMMAND')
    logger_system.log_event('FEATURE', 'User accessed enhanced logging features')
    
    print("Logging system test completed. Check logs/ directory for output.")
    
    # Generate and display reports
    print("\nError Summary:")
    print(logger_system.get_error_summary())
    
    print("\nPerformance Summary:")
    print(logger_system.get_performance_summary())
    
    # Cleanup
    logger_system.cleanup()