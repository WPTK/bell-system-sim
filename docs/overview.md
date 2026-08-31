# Bell System UNIX V7 Terminal Simulation - Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                         │
│              bell-system  ==  python -m bell_system             │
│                  bell_system/cli.py  ->  main()                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────────┐
      │               │                   │
      │ (default)     │ --simple          │ --tutorial
      │               │                   │
┌─────▼───────────────▼───────────────────▼───────────────────────┐
│                           Core Modules                          │
│       terminal.py      simple_terminal.py      tutorial.py      │
│        (12 roles)          (4 roles)             (Learn)        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
      ┌───────────────┴───────────────────┐
      │                                   │
┌─────▼───────────────────┐  ┌────────────▼───────────────────────┐
│  Per-user state dir     │  │  Historical Assets & Documentation │
│  bell_system.log        │  │  attached_assets/                  │
│  bell_system_history.txt│  │                                    │
└─────────────────────────┘  └────────────────────────────────────┘
```

## Module Breakdown

### Command Line Interface (`src/bell_system/cli.py`)
- **Single Entry Point**: Builds the argument parser and dispatches to one of the
  three interfaces below
- **Flags**: `--tutorial`, `--role N` (1-12), `--simple`, `--version`
- **Installed As**: The `bell-system` console script; `src/bell_system/__main__.py`
  makes `python -m bell_system` equivalent

### Core Simulation Engine (`src/bell_system/terminal.py`)
- **Primary Interface**: Main Bell System terminal simulation (`BellSystemTerminal`)
- **12 Operational Roles**: Full authentic Bell System positions
- **50+ Commands**: Complete command system with historical accuracy
- **Role-Specific Command Sets**: `help` and the shift briefing are tailored to the
  active role (the command set is presentational - execution is not gated)
- **Session Management**: Command history, rotating logs, and readline support
- **Command Suggestions**: Near-miss and typo suggestions on unknown commands
- **Static Data**: Manual page text lives in `src/bell_system/data/`

### Alternative Interface (`src/bell_system/simple_terminal.py`)
- **Simplified Version**: Four-role Bell System interface (`SimpleTerminal`)
- **Core Commands**: Essential UNIX and Bell System operations
- **Educational Focus**: Streamlined for learning purposes

### Tutorial System (`src/bell_system/tutorial.py`)
- **Interactive Learning**: Guided Bell System operations training (`BellSystemTutorial`)
- **Step-by-step Instruction**: Historical context and procedures
- **Practice Environment**: Safe learning without system impact

## Data Flow

```
User Input → CLI Parser → Role Selection → Command Processing → Output
     ↓              ↓             ↓                 ↓             ↓
  Parsing  → Module Selection → Alias Expansion → Dispatch → Logging
```

### Session Flow
1. **Initialization**: CLI argument parsing and module selection
2. **Role Selection**: One of 12 authentic Bell System positions, either from the
   interactive menu or from `--role N`
3. **Shift Briefing**: Role-appropriate briefing and generated shift events
4. **Command Loop**: Interactive command processing with historical accuracy
5. **State Management**: Session command history, persisted via readline
6. **Logging**: Operation tracking to the per-user state directory

## Design Patterns

### Command Pattern
Each Bell System command is implemented as a discrete method, registered in a
dispatch table built at session start, with:
- Historical accuracy validation
- Comprehensive help and manual page documentation
- Error handling with period-appropriate messages and command suggestions

### Role Definitions
```python
BELL_SYSTEM_ROLES = {
    1: ("sysop", "UNIX Systems Operator"),
    2: ("switch", "Switching Station Technician"),
    # ... 12 total roles
}
```

### Historical Authenticity
- Commands based on actual Bell System procedures (1978-1983)
- Terminology from Bell System Technical Journal
- Authentic operational workflows and troubleshooting
- Period-accurate error messages and system responses

## Configuration

### Environment Variables
- `BELL_SYSTEM_HOME`: Overrides the directory used for logs and command history
- `XDG_STATE_HOME`: Consulted when `BELL_SYSTEM_HOME` is unset; the simulation
  uses `$XDG_STATE_HOME/bell-system`, falling back to `~/.local/state/bell-system`

Nothing is written to the current working directory, so an installed
`bell-system` can be run from anywhere without leaving files behind.

### File Structure
```
bell-system-sim/
├── src/bell_system/         # The installable package
│   ├── cli.py               # CLI entry point (bell-system)
│   ├── __main__.py          # python -m bell_system
│   ├── terminal.py          # 12-role simulation
│   ├── simple_terminal.py   # 4-role simulation
│   ├── tutorial.py          # Guided tutorial
│   └── data/                # Manual page text and static data
├── tests/                   # pytest suite
├── docs/                    # Documentation
├── attached_assets/         # Historical documentation
└── pyproject.toml           # Packaging, lint, and test configuration
```

## Dependencies

**Zero Runtime Dependencies**: Pure Python 3.9+ implementation using only standard library:
- `os`, `sys`, `time` - System operations
- `argparse` - Command line parsing
- `logging`, `logging.handlers` - Logging with file rotation
- `readline` - Command history and completion (optional; absent on stock Windows)
- `csv`, `datetime`, `random` - Data handling
- `collections`, `typing` - Data structures

`pytest` and `ruff` are development-only dependencies, installed with
`pip install -e ".[dev]"`.

This design ensures maximum compatibility and historical accuracy while maintaining modern software engineering practices.