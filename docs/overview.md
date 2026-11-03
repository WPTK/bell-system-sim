# Bell System UNIX V7 Terminal Simulation - Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                         │
│              bell-system  ==  python -m bell_system             │
│                  bell_system/cli.py  ->  main()                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
      ┌───────────────┴───────────────┐
      │                               │
      │ (default)                     │ --simple
      │                               │
┌─────▼───────────────────────────────▼───────────────────────────┐
│                           Core Modules                          │
│            terminal.py              simple_terminal.py          │
│            (12 positions)               (4 roles)               │
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
  two interfaces below
- **Flags**: `--role N` (1-12), `--simple`, `--version`
- **Installed As**: The `bell-system` console script; `src/bell_system/__main__.py`
  makes `python -m bell_system` equivalent

### Terminal and Screens (`src/bell_system/terminal.py`, `screens/`)
- **Terminal**: `BellSystemTerminal` is dispatch and session only. Every screen
  lives in `screens/`, one module per subsystem, mixed into the terminal.
  `screens/dispatch.py` holds the command table and the aliases;
  `screens/session.py` declares every attribute and cross-mixin method the
  mixins share
- **12 positions**: Each works the same board but gets different work on it
- **Commands**: About 160 in the dispatch table, from the repair bureau to the
  Seventh Edition shell and text tools
- **Qualification gates commands**: A command you are not signed off on is
  refused by the wire chief. `help` marks them and `qual` shows how to earn them
- **Session**: Command history, rotating logs, readline support, and near-miss
  suggestions on unknown commands
- **Static data**: Reference tables and manual page text live in `data/`

### Repair Service Bureau (`src/bell_system/reports.py`)

Owns the pending board of customer trouble reports and the rules for working
it: report generation with a hidden electrical fault, commitment intervals that
lengthen with the backlog, dispatch to a repair force, and close out against
disposition code 5 or 8. It knows nothing about the terminal - it returns
state, and the terminal renders it.

### Loop and Transmission Testing (`src/bell_system/loop_testing.py`)

Turns a fault into readings. Insulation resistance and loop resistance are kept
strictly apart, because they are different measurements taken different ways
and only one of them is what the 1300-ohm design limit applies to. Readings are
seeded from the line's own number, so a pair measures the same every time it is
tested rather than re-rolling under a retest. Also holds the far-end test line
series and single frequency supervision states.

### Progression (`src/bell_system/progression.py`)

Difficulty profiles, the qualification ladder, the service index and the
persistent career record. Qualification is the progression mechanic because it
is what actually governed what a craftsperson could touch. The index is scored
against the network switching performance measurement plan weights.

### The Other Craft (`src/bell_system/npc.py`)

The people on the other end of the four messaging channels - `write(1)`,
`mail(1)`, the order wire and the maintenance teletype - and the traffic they
generate. Rate is set by the active difficulty; `set game.ambience off` silences
it entirely.

### Alternative Interface (`src/bell_system/simple_terminal.py`)
- **Simplified Version**: Four-role Bell System interface (`SimpleTerminal`)
- **Core Commands**: Essential UNIX and Bell System operations
- **Educational Focus**: Streamlined for learning purposes

### Teaching
There is no tutorial mode. The first tour opens with one report on the board
and the wire chief walks the player through the loop over `write(1)`. After that
`help` opens on what to do now, `hint` asks somebody, and `training unix` is the
annual refresher on the machine.

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
- A manual page for every command
- Error handling with period-appropriate messages and command suggestions

### Role Definitions
```python
BELL_SYSTEM_ROLES = {
    1: ("sysop", "UNIX Systems Operator"),
    2: ("switch", "Switching Station Technician"),
    # ... 12 total roles
}  # constants.py
```

### Historical Authenticity
- Commands based on actual Bell System procedures (1978-1983)
- Terminology from Bell System Technical Journal
- Authentic operational workflows and troubleshooting
- Period-accurate error messages and system responses

## Configuration

### Environment Variables
- `BELL_SYSTEM_HOME`: Overrides the directory used for logs, command history,
  settings, the career record and the saved tour
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
│   ├── terminal.py          # Dispatch and session
│   ├── simple_terminal.py   # 4-role simulation
│   ├── screens/             # One mixin per subsystem
│   ├── data/                # Reference tables and manual pages
│   ├── reports.py           # The repair bureau's board
│   ├── loop_testing.py      # Faults turned into readings
│   ├── progression.py       # Difficulty, qualification, career
│   ├── npc.py               # The other craft
│   └── save.py              # The saved tour
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