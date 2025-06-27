# Bell System UNIX V7 Terminal Simulation - Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                            │
│                   bin/bell-system                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Core Modules                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ bell.py     │  │ main.py     │  │ tutorial.py │            │
│  │ (Main)      │  │ (Alt)       │  │ (Learn)     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Support Modules                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ logging     │  │ performance │  │ ux_enhance  │            │
│  │ _enhance.py │  │ _profile.py │  │ ments.py    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│               Historical Assets & Documentation                │
│                  attached_assets/                              │
└─────────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### Core Simulation Engine (`src/bell.py`)
- **Primary Interface**: Main Bell System terminal simulation
- **12 Operational Roles**: Full authentic Bell System positions
- **50+ Commands**: Complete command system with historical accuracy
- **Authentication**: Role-based access control
- **Session Management**: Command history and state persistence

### Alternative Interface (`src/unix_terminal.py`)
- **Simplified Version**: Four-role Bell System interface
- **Core Commands**: Essential UNIX and Bell System operations
- **Educational Focus**: Streamlined for learning purposes

### Tutorial System (`src/bell_system_tutorial.py`)
- **Interactive Learning**: Guided Bell System operations training
- **Step-by-step Instruction**: Historical context and procedures
- **Practice Environment**: Safe learning without system impact

### Enhancement Modules
- **Logging (`src/logging_enhancements.py`)**: Professional logging with rotation
- **Performance (`src/performance_profiling.py`)**: Optimization and analysis tools
- **UX Improvements (`src/ux_command_enhancements.py`)**: User experience enhancements

## Data Flow

```
User Input → CLI Parser → Role Authentication → Command Processing → Output
     ↓              ↓              ↓                    ↓           ↓
  Validation → Module Selection → Permission Check → Execution → Logging
```

### Session Flow
1. **Initialization**: CLI argument parsing and module selection
2. **Authentication**: Role selection from 12 authentic Bell System positions
3. **Command Loop**: Interactive command processing with historical accuracy
4. **State Management**: Session persistence and command history
5. **Logging**: Comprehensive operation tracking and diagnostics

## Design Patterns

### Command Pattern
Each Bell System command is implemented as a discrete method with:
- Historical accuracy validation
- Role-based permission checking
- Comprehensive help documentation
- Error handling with period-appropriate messages

### Role-Based Access Control
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
- `BELL_SYSTEM_LOG_LEVEL`: Control logging verbosity
- `BELL_SYSTEM_ROLE`: Default role selection
- `BELL_SYSTEM_HISTORY`: Command history file location

### File Structure
```
bell-system-unix-v7/
├── bin/bell-system          # CLI entry point
├── src/                     # Source code modules
├── tests/                   # Test suites
├── docs/                    # Documentation
├── examples/                # Usage examples
└── attached_assets/         # Historical documentation
```

## Dependencies

**Zero External Dependencies**: Pure Python 3.6+ implementation using only standard library:
- `os`, `sys`, `time` - System operations
- `logging` - Professional logging
- `readline` - Command history (optional)
- `json`, `datetime` - Data handling
- `collections`, `typing` - Data structures

This design ensures maximum compatibility and historical accuracy while maintaining modern software engineering practices.