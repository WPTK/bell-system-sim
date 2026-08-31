```                                  
                  5555555555555555555          
              555555555555555555555555555    
           5555555552             5555555551 
         55555552                     55555555
        555555          155555           555555
      555555            2555557            555555
     55555        5555555555555555555        55555
    55555       2555555555555555555555        55555
   55555        555555           555555        55555 
   5555         55555             55555         5555
  55555         55555             55555         55555
  5555          55552             55555         15555
  5555          5555               5555          5555
  5555         55555               55555         5555   
  5555       1555555               555555        5555   
  55555    5555551                    555555    55555
  55555    555555555555555555555555555555555    55553 
   55555   555555555555555555555555555555555   55555
    55555  555555555555555555555555555555555  55555
    155555               55555               55555
      55555              55555              55555
       555555                             555555
        3555555                         555555
          555555552                 555555551
             55555555555557 75555555555555
                55555555555555555555555
                     5555555555552
       
```
# Bell System UNIX V7 Terminal Simulation

A historically accurate recreation of AT&T Bell System internal operations workstations from the transformative period of 1978-1983.

This command-line application provides an authentic terminal-based experience of Bell System operations, featuring 12 operational roles, 50+ period-accurate commands, and comprehensive Bell System workflows based on authentic AT&T documentation.

## Quick Start

```bash
# Install
git clone https://github.com/WPTK/bell-system-sim.git
cd bell-system-sim
pip install -e .

# Run
bell-system                    # Start interactive simulation
bell-system --tutorial         # Learn Bell System operations
bell-system --role 1           # Start as specific role (1-12), skipping the menu
bell-system --simple           # Simplified four-role interface
python -m bell_system          # Equivalent to `bell-system`
```

## Features

- **12 Authentic Operational Roles** from UNIX Systems Operator to Document Preparation Specialist
- **50+ Period-Accurate Commands** with comprehensive functionality and historical accuracy
- **Role-Based Access Control** with commands and workflows specific to each position
- **Event and Ticket Management** using authentic Bell System trouble ticket systems
- **Historical Documentation** based on Bell System Technical Journal and operations manuals
- **Pure Python Implementation** using only standard library modules

## Installation

### Prerequisites
- Python 3.9 or higher
- No external dependencies required

### Install from Source
```bash
git clone https://github.com/WPTK/bell-system-sim.git
cd bell-system-sim
pip install -e .
```

### Verify Installation
```bash
bell-system --version
bell-system --help
```

## Usage

1. Start the application using one of the methods above
2. Select your Bell System operational role (1-12)
3. Use authentic Bell System commands and workflows
4. Access role-specific functionality and documentation

### Available Roles

1. **UNIX Systems Operator** - System administration and monitoring
2. **Switching Station Technician** - Circuit switching and maintenance
3. **Field Support Liaison** - Customer and field coordination
4. **National NOC Analyst** - Network operations center analysis
5. **Traffic Service Position System Operator** - Call routing and management
6. **Database Administrator** - Data management and integrity
7. **Network Planning Engineer** - Network design and optimization
8. **Customer Service Interface Technician** - Customer support systems
9. **Radio/Microwave Technician** - Wireless communications maintenance
10. **Total Network Data System (TNDS) Analyst** - Network data analysis
11. **SARTS (Special Service Testing) Technician** - Service testing and validation
12. **Document Preparation Specialist** - Technical documentation

## Project Structure

```
├── src/
│   └── bell_system/                 # The installable Python package
│       ├── __init__.py              # Package exports and version
│       ├── __main__.py              # `python -m bell_system` entry point
│       ├── cli.py                   # Argument parsing and console script
│       ├── terminal.py              # Main 12-role Bell System terminal
│       ├── simple_terminal.py       # Four-role simplified terminal
│       ├── tutorial.py              # Interactive tutorial system
│       └── data/                    # Manual page text and other static data
├── tests/                           # pytest suite
├── docs/                            # Manual, command reference, and guides
├── attached_assets/                 # Historical Bell System documentation
├── pyproject.toml                   # Packaging, linting, and test configuration
├── LICENSE
└── README.md
```

## Documentation

- **User Manual**: `docs/manual.txt` - Complete operational guide
- **Command Reference**: `docs/command_reference.txt` - Quick reference for all commands
- **Architecture Overview**: `docs/overview.md` - How the package fits together
- **API Reference**: `docs/api.md` - Programmatic use of the simulation classes
- **Change Log**: `docs/changelog.md` - Version history and improvements
- **Historical Assets**: `attached_assets/` - Authentic Bell System documentation

## Development

### Running Tests

```bash
pip install -e ".[dev]"
python -m pytest tests
```

### Linting

```bash
ruff check src tests
```

### Logging

Logs and command history are written to a per-user state directory rather than
the current working directory. The location is `$BELL_SYSTEM_HOME` when set,
otherwise `$XDG_STATE_HOME/bell-system`, otherwise `~/.local/state/bell-system`:

- `bell_system.log` - Rotating application log (10 MB, 5 backups)
- `bell_system_history.txt` - Command history

## Historical Context

This simulation is based on authentic AT&T Bell System operations from 1978-1983, a transformative period in telecommunications history. The commands, workflows, and terminology are historically accurate and based on actual Bell System documentation and practices.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure that any contributions maintain historical accuracy and authentic Bell System practices.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AT&T Bell Laboratories historical documentation
- UNIX V7 system documentation and manuals
- Bell System Technical Journal archives
- Historical telecommunications engineering resources

## Disclaimer

This is a historical simulation for educational and nostalgic purposes. It is not affiliated with or endorsed by AT&T or any telecommunications company.
