# Bell System UNIX V7 Terminal Simulation - API Reference

## Core Classes

### `BellSystemTerminal`
Main terminal simulation class providing full 12-role Bell System experience.

```python
from src.bell import BellSystemTerminal

terminal = BellSystemTerminal()
terminal.run()
```

**Methods:**
- `run()` - Start interactive terminal session
- `execute_command(cmd: str) -> str` - Execute Bell System command
- `get_role_commands(role: str) -> List[str]` - Get available commands for role
- `switch_role(role_id: int)` - Change operational role

### `SimpleBellSystemTerminal`
Simplified four-role interface for educational purposes.

```python
from src.unix_terminal import BellSystemTerminal as SimpleBellSystemTerminal

terminal = SimpleBellSystemTerminal()
terminal.run()
```

### `BellSystemTutorial`
Interactive tutorial system for learning Bell System operations.

```python
from src.bell_system_tutorial import BellSystemTutorial

tutorial = BellSystemTutorial()
tutorial.run()
```

## Bell System Roles

### Available Roles (1-12)
```python
BELL_SYSTEM_ROLES = {
    1: ("sysop", "UNIX Systems Operator"),
    2: ("switch", "Switching Station Technician"),
    3: ("field", "Field Support Liaison"),
    4: ("noc", "National NOC Analyst"),
    5: ("tsps", "Traffic Service Position System Operator"),
    6: ("dba", "Database Administrator"),
    7: ("netplan", "Network Planning Engineer"),
    8: ("custserv", "Customer Service Interface Technician"),
    9: ("radio", "Radio/Microwave Technician"),
    10: ("tnds", "Total Network Data System (TNDS) Analyst"),
    11: ("sarts", "SARTS (Special Service Testing) Technician"),
    12: ("docprep", "Document Preparation Specialist")
}
```

## Command Categories

### System Commands
- `help`, `h`, `?` - Command assistance
- `man <command>` - Manual pages
- `status`, `st` - System status
- `who`, `w`, `users` - User information
- `date`, `pwd` - System information

### Bell System Operations
- `trunk <action>` - Trunk group management
- `switch <action>` - Switching system operations
- `testboard <action>` - Test board operations
- `alarm <action>` - Alarm management
- `ticket <action>` - Trouble ticket system

### Example Usage

#### Starting with Specific Role
```python
import src.bell as bell

terminal = bell.BellSystemTerminal()
terminal.current_role = "sysop"
terminal.role_name = "UNIX Systems Operator"
terminal.run()
```

#### Executing Commands Programmatically
```python
terminal = bell.BellSystemTerminal()
terminal.current_role = "switch"

# Check trunk status
result = terminal.execute_command("trunk status")
print(result)

# View alarms
result = terminal.execute_command("alarm status")
print(result)
```

#### Role-Specific Commands
```python
# Get commands available to NOC Analyst
commands = terminal.get_role_commands("noc")
for cmd in commands:
    print(f"- {cmd}")
```

## Logging and Diagnostics

### Enhanced Logging
```python
from src.logging_enhancements import BellSystemLogger

logger = BellSystemLogger()
logger.setup_logging(level="INFO")
logger.log_command("trunk status", "sysop", "success")
```

### Performance Profiling
```python
from src.performance_profiling import BellSystemProfiler

profiler = BellSystemProfiler()
with profiler.profile_command("trunk_analysis"):
    # Command execution code
    pass
```

## Configuration Constants

### Bell System Practices (BSP) Categories
```python
BSP_CATEGORIES = {
    "100": "Bell System Fundamentals",
    "200": "Switching Systems", 
    "300": "Transmission Systems",
    "400": "Network Operations",
    "500": "Customer Services",
    "600": "UNIX and Computing Systems",
    "700": "Electronic Switching (5ESS)",
    "800": "TSPS Operations",
    "900": "TNDS and Data Systems"
}
```

### Project Numbering Prefixes
```python
PROJECT_PREFIXES = {
    "NP": "Network Planning",
    "TP": "Technical/Technology", 
    "OP": "Operations",
    "AC": "Area Code Implementation",
    "RE": "Route Enhancement",
    "CP": "Capacity Planning"
}
```

## Error Handling

All commands return structured responses with error handling:

```python
try:
    result = terminal.execute_command("invalid_command")
except CommandNotFoundError as e:
    print(f"Command error: {e}")
except PermissionError as e:
    print(f"Access denied: {e}")
```

## Historical Data Access

### Bell System Documentation
```python
# Access historical assets
from pathlib import Path

assets_dir = Path("attached_assets")
manuals = list(assets_dir.glob("*.txt"))
technical_docs = list(assets_dir.glob("*.pdf"))
```

This API maintains historical accuracy while providing modern programmatic access to authentic Bell System operations and procedures from 1978-1983.