#!/usr/bin/env python3
"""
import bell
import json
import logging
import os
import sys
import time
import traceback

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

Bell System UNIX V7 Terminal Simulation - Logging and Diagnostics System
========================================================================

Comprehensive error logging, diagnostics, and changelog management system
specifically designed for the Bell System terminal simulation.

This module provides structured logging, automatic changelog updates, and
diagnostic tools while maintaining compatibility with terminal environments.
"""


class BellSystemLogger:
    """Advanced logging system for Bell System terminal simulation"""

    def __init__(self, log_dir: str = "logs", changelog_file: str = "changelog.txt"):
        self.log_dir = Path(log_dir)
        self.changelog_file = Path(changelog_file)
        self.session_id = self._generate_session_id()

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)

        # Initialize logging subsystems
        self._setup_loggers()
        self._setup_log_rotation()

        # Verbosity levels
        self.verbosity_levels = {
            'QUIET': logging.ERROR,
            'NORMAL': logging.WARNING,
            'VERBOSE': logging.INFO,
            'DEBUG': logging.DEBUG
        }
        self.current_verbosity = 'NORMAL'

    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        return f"BELL-{int(time.time())}-{os.getpid()}"

    def _setup_loggers(self):
        """Configure multiple specialized loggers"""

        # Main application logger
        self.app_logger = logging.getLogger('bell_system_app')
        self.app_logger.setLevel(logging.DEBUG)

        # Security audit logger
        self.security_logger = logging.getLogger('bell_system_security')
        self.security_logger.setLevel(logging.INFO)

        # Performance logger
        self.performance_logger = logging.getLogger('bell_system_performance')
        self.performance_logger.setLevel(logging.INFO)

        # User activity logger
        self.activity_logger = logging.getLogger('bell_system_activity')
        self.activity_logger.setLevel(logging.INFO)

        # Configure formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | Session:%(session_id)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup file handlers
        self._add_file_handler(self.app_logger, 'bell_system_app.log', detailed_formatter)
        self._add_file_handler(self.security_logger, 'bell_system_security.log', detailed_formatter)
        self._add_file_handler(self.performance_logger, 'bell_system_performance.log', simple_formatter)
        self._add_file_handler(self.activity_logger, 'bell_system_activity.log', detailed_formatter)

    def _add_file_handler(self, logger, filename: str, formatter):
        """Add file handler to logger with rotation"""
        handler = logging.FileHandler(self.log_dir / filename)
        handler.setFormatter(formatter)

        # Add session ID to log records
        class SessionFilter(logging.Filter):
            def __init__(self, session_id):
                self.session_id = session_id

            def filter(self, record):
                record.session_id = self.session_id
                return True

        handler.addFilter(SessionFilter(self.session_id))
        logger.addHandler(handler)

    def _setup_log_rotation(self):
        """Configure log rotation to prevent disk space issues"""
        from logging.handlers import RotatingFileHandler

        # Rotate logs when they exceed 10MB, keep 5 backup files
        max_bytes = 10 * 1024 * 1024  # 10MB
        backup_count = 5

        for logger_name, filename in [
            ('bell_system_app', 'bell_system_app.log'),
            ('bell_system_security', 'bell_system_security.log'),
            ('bell_system_performance', 'bell_system_performance.log'),
            ('bell_system_activity', 'bell_system_activity.log')
        ]:
            logger = logging.getLogger(logger_name)

            # Remove existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # Add rotating handler
            rotating_handler = RotatingFileHandler(
                self.log_dir / filename,
                maxBytes=max_bytes,
                backupCount=backup_count
            )

            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            rotating_handler.setFormatter(formatter)
            logger.addHandler(rotating_handler)

    def set_verbosity(self, level: str):
        """Set logging verbosity level"""
        if level.upper() in self.verbosity_levels:
            self.current_verbosity = level.upper()
            log_level = self.verbosity_levels[level.upper()]

            # Update all loggers
            for logger_name in ['bell_system_app', 'bell_system_security',
                              'bell_system_performance', 'bell_system_activity']:
                logging.getLogger(logger_name).setLevel(log_level)

            self.app_logger.info(f"Logging verbosity set to {level.upper()}")
        else:
            self.app_logger.error(f"Invalid verbosity level: {level}")

    def log_command_execution(self, user_role: str, command: str, args: List[str],
                            success: bool, execution_time: float, error_msg: str = None):
        """Log command execution with comprehensive context"""

        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'user_role': user_role,
            'command': command,
            'arguments': args,
            'success': success,
            'execution_time_ms': round(execution_time * 1000, 2),
            'error_message': error_msg
        }

        if success:
            self.activity_logger.info(f"Command executed: {json.dumps(log_data)}")
        else:
            self.activity_logger.error(f"Command failed: {json.dumps(log_data)}")

        # Performance logging for slow commands
        if execution_time > 1.0:  # Commands taking over 1 second
            self.performance_logger.warning(
                f"Slow command detected: {command} took {execution_time:.2f}s"
            )

    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log security-related events"""

        security_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'source': 'bell_system_terminal'
        }

        log_message = f"Security event: {json.dumps(security_event)}"

        if severity == 'CRITICAL':
            self.security_logger.critical(log_message)
        elif severity == 'HIGH':
            self.security_logger.error(log_message)
        elif severity == 'MEDIUM':
            self.security_logger.warning(log_message)
        else:
            self.security_logger.info(log_message)

    def log_system_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log system errors with full traceback and context"""

        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }

        self.app_logger.error(f"System error: {json.dumps(error_data, indent=2)}")

        # Update changelog for significant errors
        if isinstance(error, (SystemError, MemoryError, OSError)):
            self.update_changelog(
                'ERROR',
                f"System error: {type(error).__name__}: {str(error)}"
            )

    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics and statistics"""

        performance_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'metrics': metrics
        }

        self.performance_logger.info(f"Performance metrics: {json.dumps(performance_data)}")

        # Alert on performance degradation
        if 'startup_time' in metrics and metrics['startup_time'] > 5.0:
            self.app_logger.warning(f"Slow startup detected: {metrics['startup_time']:.2f}s")

        if 'memory_usage_mb' in metrics and metrics['memory_usage_mb'] > 100:
            self.app_logger.warning(f"High memory usage: {metrics['memory_usage_mb']:.1f}MB")

    def update_changelog(self, change_type: str, description: str,
                        version: str = None, priority: str = 'NORMAL'):
        """Automatically update changelog.txt with significant events"""

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_version = version or self._get_current_version()

        changelog_entry = f"""
[{timestamp}] {change_type} - Priority: {priority}
Version: {current_version}
Description: {description}
Session: {self.session_id}
{'=' * 80}
"""

        try:
            # Read existing changelog
            existing_content = ""
            if self.changelog_file.exists():
                with open(self.changelog_file, 'r') as f:
                    existing_content = f.read()

            # Prepend new entry
            with open(self.changelog_file, 'w') as f:
                f.write(changelog_entry)
                f.write(existing_content)

            self.app_logger.info(f"Changelog updated: {change_type} - {description}")

        except Exception as e:
            self.app_logger.error(f"Failed to update changelog: {e}")

    def _get_current_version(self) -> str:
        """Extract current version from application"""
        try:
            # Try to import main module and get version
            return getattr(bell, '__version__', '2.0')
        except:
            return '2.0'

    def generate_diagnostic_report(self) -> str:
        """Generate comprehensive diagnostic report"""

        report = f"""
BELL SYSTEM UNIX V7 TERMINAL SIMULATION - DIAGNOSTIC REPORT
===========================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {self.session_id}

SYSTEM INFORMATION:
- Python Version: {sys.version}
- Platform: {sys.platform}
- Working Directory: {os.getcwd()}
- Log Directory: {self.log_dir.absolute()}

LOGGING STATUS:
- Current Verbosity: {self.current_verbosity}
- App Logger Level: {self.app_logger.level}
- Security Logger Level: {self.security_logger.level}
- Performance Logger Level: {self.performance_logger.level}

LOG FILE STATUS:
"""

        # Check log files
        for log_file in self.log_dir.glob('*.log'):
            try:
                size = log_file.stat().st_size
                modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                report += f"- {log_file.name}: {size:,} bytes, modified {modified}\n"
            except Exception as e:
                report += f"- {log_file.name}: ERROR - {e}\n"

        # Recent errors summary
        report += "\nRECENT ERRORS (Last 24 hours):\n"
        try:
            app_log_file = self.log_dir / 'bell_system_app.log'
            if app_log_file.exists():
                with open(app_log_file, 'r') as f:
                    lines = f.readlines()

                error_count = sum(1 for line in lines if 'ERROR' in line)
                warning_count = sum(1 for line in lines if 'WARNING' in line)

                report += f"- Errors: {error_count}\n"
                report += f"- Warnings: {warning_count}\n"
            else:
                report += "- No application log file found\n"
        except Exception as e:
            report += f"- Error reading log files: {e}\n"

        # Performance summary
        report += "\nPERFORMANCE SUMMARY:\n"
        try:
            perf_log_file = self.log_dir / 'bell_system_performance.log'
            if perf_log_file.exists():
                with open(perf_log_file, 'r') as f:
                    lines = f.readlines()

                slow_commands = sum(1 for line in lines if 'Slow command' in line)
                report += f"- Slow commands detected: {slow_commands}\n"
            else:
                report += "- No performance log file found\n"
        except Exception as e:
            report += f"- Error reading performance logs: {e}\n"

        report += f"\nReport generated by Bell System Logging System v2.0\n"
        report += "=" * 70

        return report

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days"""

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_files = []

        for log_file in self.log_dir.glob('*.log*'):
            try:
                file_modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_modified < cutoff_date:
                    log_file.unlink()
                    cleaned_files.append(log_file.name)
            except Exception as e:
                self.app_logger.error(f"Error cleaning log file {log_file}: {e}")

        if cleaned_files:
            self.app_logger.info(f"Cleaned up {len(cleaned_files)} old log files")
            self.update_changelog('MAINTENANCE', f"Cleaned {len(cleaned_files)} old log files")

        return cleaned_files

# Integration decorator for automatic logging
def log_command_execution(logger: BellSystemLogger):
    """Decorator to automatically log command execution"""
    def decorator(func):
        def wrapper(self, args):
            start_time = time.time()
            success = True
            error_msg = None

            try:
                result = func(self, args)
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.log_system_error(e, {
                    'command': func.__name__,
                    'arguments': args,
                    'user_role': getattr(self, 'current_role', 'unknown')
                })
                raise
            finally:
                execution_time = time.time() - start_time
                logger.log_command_execution(
                    user_role=getattr(self, 'current_role', 'unknown'),
                    command=func.__name__.replace('cmd_', ''),
                    args=args,
                    success=success,
                    execution_time=execution_time,
                    error_msg=error_msg
                )
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    print("Bell System Logging and Diagnostics System Test")
    print("=" * 50)

    # Initialize logger
    logger = BellSystemLogger()

    # Test different logging functions
    logger.log_command_execution(
        user_role='radio',
        command='radio',
        args=['status'],
        success=True,
        execution_time=0.125
    )

    logger.log_security_event(
        event_type='AUTHENTICATION',
        severity='MEDIUM',
        details={'user_role': 'radio', 'login_time': time.time()}
    )

    logger.log_performance_metrics({
        'startup_time': 1.2,
        'memory_usage_mb': 45.7,
        'commands_executed': 15
    })

    logger.update_changelog(
        'ENHANCEMENT',
        'Added comprehensive logging and diagnostics system',
        priority='HIGH'
    )

    # Generate diagnostic report
    report = logger.generate_diagnostic_report()
    print("Diagnostic Report Generated:")
    print(report)

    print("\n✅ Logging system test completed successfully!")
    print(f"Check logs in: {logger.log_dir.absolute()}")
