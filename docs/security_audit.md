# Bell System UNIX V7 Terminal Simulation - Security Audit

## Executive Summary
Comprehensive security analysis of the Bell System terminal simulation codebase with actionable recommendations for hardening.

## 1. INPUT VALIDATION ANALYSIS

### Current Vulnerabilities
```python
# RISK: Direct string splitting without validation
def execute_command(self, command_line: str) -> str:
    parts = command_line.strip().split()  # No length validation
    command = parts[0].lower()            # No bounds checking
```

### Recommended Fixes
```python
def secure_execute_command(self, command_line: str) -> str:
    """Secure command execution with input validation"""
    # Input sanitization
    if not isinstance(command_line, str):
        return "Error: Invalid input type"
    
    # Length validation
    if len(command_line) > 1000:
        return "Error: Command too long (max 1000 characters)"
    
    # Character validation
    if not all(ord(c) < 128 for c in command_line):
        return "Error: Non-ASCII characters not allowed"
    
    # Safe splitting with bounds checking
    parts = command_line.strip().split()
    if not parts:
        return "Error: Empty command"
    
    if len(parts) > 20:  # Reasonable argument limit
        return "Error: Too many arguments"
    
    command = parts[0].lower()
    
    # Command whitelist validation
    if command not in self.get_allowed_commands():
        return f"Error: Command '{command}' not authorized"
    
    return self._execute_validated_command(command, parts[1:])
```

## 2. INJECTION VULNERABILITY ASSESSMENT

### String Interpolation Risks
```python
# RISK: Potential injection in ticket generation
def generate_ticket_id(self, prefix: str) -> str:
    # Current implementation may allow injection
    return f"{prefix}-{random.randint(10000, 99999)}"

# SECURE: Validated prefix generation
def secure_generate_ticket_id(self, ticket_type: str) -> str:
    """Generate secure ticket ID with validated prefix"""
    # Whitelist valid prefixes
    valid_prefixes = {'T', 'EV', 'WO', 'ALM'}
    
    if ticket_type not in valid_prefixes:
        raise ValueError(f"Invalid ticket type: {ticket_type}")
    
    # Use secure random number generation
    import secrets
    ticket_number = secrets.randbelow(90000) + 10000
    
    return f"{ticket_type}-{ticket_number:05d}"
```

### Path Traversal Prevention
```python
# RISK: File operations without path validation
def load_manual_page(self, page_name: str) -> str:
    # INSECURE: Direct file access
    # filename = f"/manual/{page_name}.txt"
    
    # SECURE: Path validation and sanitization
    import os
    
    # Sanitize input
    safe_name = ''.join(c for c in page_name if c.isalnum() or c in '_-')
    
    # Prevent path traversal
    if '..' in page_name or '/' in page_name:
        return "Error: Invalid manual page name"
    
    # Use safe path joining
    manual_dir = "/app/manual"  # Fixed base directory
    filename = os.path.join(manual_dir, f"{safe_name}.txt")
    
    # Verify path is within allowed directory
    if not filename.startswith(manual_dir):
        return "Error: Path traversal attempt detected"
    
    return filename
```

## 3. ERROR HANDLING SECURITY

### Information Disclosure Prevention
```python
def secure_error_handler(self, error: Exception, command: str) -> str:
    """Secure error handling that doesn't leak system information"""
    
    # Log full error details securely (not to user)
    import logging
    logging.error(f"Command '{command}' failed: {str(error)}", 
                 extra={'user_role': self.current_role, 'timestamp': time.time()})
    
    # Return sanitized error to user
    if isinstance(error, ValueError):
        return "Bell System Terminal: Invalid command parameter"
    elif isinstance(error, KeyError):
        return "Bell System Terminal: Requested resource not found"
    elif isinstance(error, PermissionError):
        return "Bell System Terminal: Insufficient privileges for operation"
    else:
        # Generic error message - don't expose system details
        return "Bell System Terminal: Operation failed. Contact system administrator."
```

## 4. SESSION SECURITY

### Session Management
```python
class SecureBellSystemTerminal:
    """Enhanced terminal with session security"""
    
    def __init__(self):
        self.session_id = self._generate_secure_session_id()
        self.session_start_time = time.time()
        self.failed_command_attempts = 0
        self.max_failed_attempts = 10
        self.session_timeout = 3600  # 1 hour
        
    def _generate_secure_session_id(self) -> str:
        """Generate cryptographically secure session ID"""
        import secrets
        return secrets.token_hex(16)
    
    def _check_session_security(self) -> bool:
        """Validate session security status"""
        current_time = time.time()
        
        # Check session timeout
        if current_time - self.session_start_time > self.session_timeout:
            self._terminate_session("Session timeout")
            return False
        
        # Check failed attempt threshold
        if self.failed_command_attempts >= self.max_failed_attempts:
            self._terminate_session("Too many failed commands")
            return False
        
        return True
    
    def _terminate_session(self, reason: str):
        """Secure session termination"""
        logging.warning(f"Session {self.session_id} terminated: {reason}")
        print(f"Bell System Terminal: Session terminated ({reason})")
        sys.exit(0)
```

## 5. LOGGING SECURITY

### Secure Audit Logging
```python
import logging
import json
import hashlib
from datetime import datetime

class SecureAuditLogger:
    """Secure audit logging for Bell System operations"""
    
    def __init__(self, log_file: str = "/var/log/bell_system_audit.log"):
        # Configure secure logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('bell_system_audit')
    
    def log_command_execution(self, user_role: str, command: str, 
                            success: bool, session_id: str):
        """Log command execution with security context"""
        
        # Create audit record
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'user_role': user_role,
            'command': command,
            'success': success,
            'source_ip': '127.0.0.1',  # Local terminal
            'checksum': None
        }
        
        # Generate integrity checksum
        record_string = json.dumps(audit_record, sort_keys=True)
        audit_record['checksum'] = hashlib.sha256(
            record_string.encode()
        ).hexdigest()
        
        # Log securely
        self.logger.info(json.dumps(audit_record))
    
    def log_security_event(self, event_type: str, details: str, 
                          severity: str = "WARNING"):
        """Log security events"""
        security_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'system': 'bell_system_terminal'
        }
        
        if severity == "CRITICAL":
            self.logger.critical(json.dumps(security_event))
        elif severity == "WARNING":
            self.logger.warning(json.dumps(security_event))
        else:
            self.logger.info(json.dumps(security_event))
```

## 6. PRIVILEGE ESCALATION PREVENTION

### Role-Based Access Control
```python
class SecureRoleManager:
    """Secure role-based command access control"""
    
    ROLE_PERMISSIONS = {
        'sysop': ['ps', 'who', 'df', 'ls', 'help', 'man'],
        'switch': ['switch', '3a', 'trunk', 'testboard', 'help'],
        'radio': ['radio', 'microwave', 't1carrier', 'lcarrier', 'help'],
        # ... other roles
    }
    
    def __init__(self, user_role: str):
        if user_role not in self.ROLE_PERMISSIONS:
            raise ValueError(f"Invalid role: {user_role}")
        self.user_role = user_role
        self.allowed_commands = set(self.ROLE_PERMISSIONS[user_role])
    
    def check_command_permission(self, command: str) -> bool:
        """Check if user role has permission for command"""
        # Base commands allowed for all roles
        base_commands = {'help', 'man', 'quit', 'date'}
        
        return (command in base_commands or 
                command in self.allowed_commands)
    
    def get_restricted_message(self, command: str) -> str:
        """Return appropriate message for restricted command"""
        return (f"Bell System Terminal: Command '{command}' not available "
                f"for role '{self.user_role}'. Contact administrator for access.")
```

## 7. CONFIGURATION SECURITY

### Secure Configuration Management
```python
import configparser
import os
from pathlib import Path

class SecureConfig:
    """Secure configuration management"""
    
    def __init__(self, config_file: str = "bell_system.conf"):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self._load_secure_config()
    
    def _load_secure_config(self):
        """Load configuration with security validation"""
        
        # Check file permissions
        if self.config_file.exists():
            file_stat = self.config_file.stat()
            # Ensure config file is not world-readable
            if file_stat.st_mode & 0o044:
                raise PermissionError("Config file has insecure permissions")
        
        # Load with defaults
        self.config.read_dict({
            'security': {
                'session_timeout': '3600',
                'max_failed_attempts': '10',
                'enable_audit_logging': 'true'
            },
            'performance': {
                'command_cache_size': '128',
                'max_command_length': '1000'
            }
        })
        
        # Override with file if exists
        if self.config_file.exists():
            self.config.read(self.config_file)
    
    def get_security_setting(self, key: str, default=None):
        """Get security configuration value"""
        return self.config.get('security', key, fallback=default)
```

## Security Recommendations Summary

### High Priority (Implement Immediately)
1. **Input validation** for all command parameters
2. **Command whitelisting** based on user roles
3. **Session timeout** and failed attempt limits
4. **Secure audit logging** for all operations

### Medium Priority
1. **Path traversal prevention** for file operations
2. **Error message sanitization** to prevent information disclosure
3. **Configuration file security** with proper permissions
4. **Cryptographically secure** random number generation

### Low Priority
1. **Rate limiting** for command execution
2. **Integrity checking** for audit logs
3. **Security event alerting** for suspicious activity

### Implementation Checklist
- [ ] Add input validation to all command functions
- [ ] Implement role-based access control
- [ ] Add secure session management
- [ ] Configure audit logging
- [ ] Sanitize error messages
- [ ] Validate file paths and prevent traversal
- [ ] Set up security configuration management
- [ ] Test all security controls