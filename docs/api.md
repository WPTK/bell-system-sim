# Bell System UNIX V7 Terminal Simulation - API Reference

## Importing

The simulation is an installable package. After `pip install -e .` the three
public classes are available directly from the top-level package:

```python
from bell_system import BellSystemTerminal, SimpleTerminal, BellSystemTutorial
```

They can also be imported from the modules that define them:

```python
from bell_system.terminal import BellSystemTerminal
from bell_system.simple_terminal import SimpleTerminal
from bell_system.tutorial import BellSystemTutorial
```

## Core Classes

### `BellSystemTerminal`
Main terminal simulation class providing full 12-role Bell System experience.
Defined in `bell_system/terminal.py`.

```python
from bell_system import BellSystemTerminal

terminal = BellSystemTerminal()
terminal.run()
```

**Methods:**
- `run(role: Optional[int] = None)` - Start an interactive terminal session. Pass
  a role number 1-12 to skip the selection menu (this is what `--role` uses).
- `execute_command(command_line: str) -> str` - Execute a Bell System command and
  return its output as a string.
- `select_role(preselected: Optional[int] = None)` - Select the operational role,
  either interactively or from a role number 1-12.

**Attributes:**
- `role` - Short role key for the active role (for example `"sysop"`), or `None`
  before a role is selected.
- `role_name` - Full role title (for example `"UNIX Systems Operator"`).
- `command_history` - A bounded `deque` of the commands entered this session.

### `SimpleTerminal`
Simplified four-role interface for educational purposes. Defined in
`bell_system/simple_terminal.py` and reached from the CLI with `--simple`.

```python
from bell_system import SimpleTerminal

terminal = SimpleTerminal()
terminal.run()
```

**Methods:**
- `run()` - Start the interactive four-role session.
- `execute_command(command_line: str) -> str` - Execute a command and return its
  output.

### `BellSystemTutorial`
Interactive tutorial system for learning Bell System operations. Defined in
`bell_system/tutorial.py` and reached from the CLI with `--tutorial`.

```python
from bell_system import BellSystemTutorial

tutorial = BellSystemTutorial()
tutorial.run()
```

## Command Line Entry Point

`bell_system/cli.py` provides `main()`, which is installed as the `bell-system`
console script and invoked by `python -m bell_system`.

```python
from bell_system.cli import main

# Same as running: bell-system --role 5
exit_status = main(['--role', '5'])
```

`main()` accepts an argument list (defaulting to `sys.argv[1:]`) and returns a
process exit status.

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
    11: ("sarts", "SARTS (Switched Access Remote Test) Technician"),
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
from bell_system import BellSystemTerminal

terminal = BellSystemTerminal()
terminal.run(role=1)  # Start as UNIX Systems Operator, no menu
```

#### Executing Commands Programmatically
```python
from bell_system import BellSystemTerminal

terminal = BellSystemTerminal()
terminal.select_role(1)  # Configure the session without entering the loop

# Show running Bell System processes
print(terminal.execute_command("ps"))

# Open the trouble ticket dashboard
print(terminal.execute_command("trouble"))

# Read a manual page
print(terminal.execute_command("man trunk"))
```

#### Inspecting the Session
```python
print(terminal.role)          # 'sysop'
print(terminal.role_name)     # 'UNIX Systems Operator'
print(list(terminal.command_history))

# The 'help' command lists the commands available to the active role
print(terminal.execute_command("help"))
```

## Logging and State

Logging is built into `BellSystemTerminal`: a rotating file handler (10 MB, five
backups) writes `bell_system.log`, and readline command history is persisted to
`bell_system_history.txt`. Both live in a per-user state directory rather than
the working directory.

```python
from bell_system.terminal import state_dir

# $BELL_SYSTEM_HOME, else $XDG_STATE_HOME/bell-system,
# else ~/.local/state/bell-system. Created if missing.
print(state_dir())
```

Setting `BELL_SYSTEM_HOME` is the supported way to redirect that state, and is
how the test suite keeps runs isolated from a developer's real state directory.

## Configuration Constants

### Bell System Practices (BSP) Categories
```python
BSP_CATEGORIES = {
    "000": "General Information and Master Indexes",
    "100": "Test Equipment",
    "309": "Switched Services Networks",
    "620": "Outside Plant - General",
    "660": "Test Center Operation",
    "795": "Common Language",
    "800": "Equipment Design Requirements",
    "900": "Outside Plant Engineering",
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

`execute_command()` does not raise for bad input - it reports errors in its
return value, the same way the interactive terminal shows them. Unknown commands
come back as an error string, with close matches suggested where the simulation
can find them:

```python
result = terminal.execute_command("hlep")
print(result)
# Error: hlep: command not found
#
# Did you mean:
#   • help

# Repeated failures of the same command add a pointer to 'help' and 'man'.
# The 'errors' command summarises recent failures for the session.
print(terminal.execute_command("errors"))
```

Errors are also recorded to the session log described under
[Logging and State](#logging-and-state).

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