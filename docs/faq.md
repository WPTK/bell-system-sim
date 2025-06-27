# Frequently Asked Questions

## Installation and Setup

### Q: What are the system requirements?
**A:** Python 3.6 or higher. No external dependencies required - the simulation uses only Python standard library modules.

### Q: How do I install the Bell System simulation?
**A:** Clone the repository and install in development mode:
```bash
git clone https://github.com/your-username/bell-system-unix-v7.git
cd bell-system-unix-v7
pip install -e .
```

### Q: The `bell-system` command is not found after installation
**A:** Ensure Python's script directory is in your PATH. On Linux/macOS:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Usage Questions

### Q: How do I start the simulation?
**A:** Use the `bell-system` command:
- `bell-system` - Interactive role selection
- `bell-system --tutorial` - Guided learning mode  
- `bell-system --role 1` - Start as specific role
- `bell-system --simple` - Simplified interface

### Q: What are the 12 operational roles?
**A:** The simulation includes authentic Bell System positions from 1978-1983:
1. UNIX Systems Operator
2. Switching Station Technician
3. Field Support Liaison
4. National NOC Analyst
5. Traffic Service Position System Operator
6. Database Administrator
7. Network Planning Engineer
8. Customer Service Interface Technician
9. Radio/Microwave Technician
10. Total Network Data System (TNDS) Analyst
11. SARTS (Special Service Testing) Technician
12. Document Preparation Specialist

### Q: How do I get help within the simulation?
**A:** Use these commands:
- `help` - General command overview
- `man <command>` - Detailed manual page
- `?` - Quick help
- `commands` - List available commands for your role

## Historical Accuracy

### Q: How historically accurate is this simulation?
**A:** The simulation is based on authentic Bell System documentation from 1978-1983, including:
- Bell System Technical Journal articles
- AT&T Engineering and Operations manuals
- UNIX V7 system documentation
- Bell System Practices (BSP) documents

### Q: Why can't I access certain commands?
**A:** Commands are restricted by role-based access control, just like in actual Bell System operations. Each operational role has specific responsibilities and corresponding command access.

### Q: Are the error messages authentic?
**A:** Yes, error messages and system responses are modeled after actual Bell System and UNIX V7 patterns from the period.

## Technical Issues

### Q: The simulation crashes or shows import errors
**A:** Verify your Python installation and try:
```bash
python3 -c "import sys; print(sys.version)"
bell-system --version
bell-system --test
```

### Q: Commands seem slow to respond
**A:** For performance analysis:
```bash
# Enable performance profiling
export BELL_SYSTEM_PROFILE=1
bell-system

# Or run performance tests
python3 src/performance_profiling.py
```

### Q: How do I enable debug logging?
**A:** Set the logging level:
```bash
export BELL_SYSTEM_LOG_LEVEL=DEBUG
bell-system
```

## Platform-Specific Notes

### Windows
- Use `py -3` instead of `python3` if needed
- Install with `py -3 -m pip install -e .`
- Path issues may require adding Python Scripts directory manually

### macOS
- May need to install Python 3 via Homebrew: `brew install python3`
- Use `python3` explicitly to avoid system Python 2

### Linux
- Most distributions include Python 3
- May need `python3-pip`: `sudo apt install python3-pip`
- Ensure readline support: `sudo apt install libreadline-dev`

## Development and Contributing

### Q: How do I run the test suite?
**A:** Multiple options available:
```bash
bell-system --test              # Built-in CLI test
python -m pytest tests/        # Full pytest suite
python tests/comprehensive_test_suite.py  # Direct execution
```

### Q: How do I contribute new Bell System commands?
**A:** 
1. Research authentic Bell System documentation for the command
2. Identify which operational roles would use it
3. Implement following the existing command pattern
4. Add comprehensive tests and documentation
5. Submit pull request with historical sources

### Q: Can I add commands from after 1983?
**A:** No, the simulation maintains strict historical accuracy for the 1978-1983 Bell System period. Post-divestiture commands would not be authentic.

## Troubleshooting

### Common Error: "ModuleNotFoundError"
```bash
# Ensure proper installation
pip install -e .

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Common Error: "Permission denied"
```bash
# Make CLI executable
chmod +x bin/bell-system

# Check file permissions
ls -la bin/bell-system
```

### Common Error: "Command not found: bell-system"
```bash
# Verify installation
pip show bell-system-unix-v7

# Check PATH
echo $PATH
which bell-system
```

### Performance Issues
- Disable logging: `export BELL_SYSTEM_LOG_LEVEL=ERROR`
- Use simplified interface: `bell-system --simple`
- Check available memory and disk space

## Getting More Help

### Community Resources
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions about Bell System operations
- **Documentation**: Complete guides in `docs/` directory

### Historical Research
For questions about Bell System operations and procedures, consult:
- Bell System Technical Journal archives
- AT&T Engineering and Operations documentation  
- UNIX V7 system manuals
- Historical telecommunications references in `attached_assets/`

### Reporting Issues
When reporting bugs, include:
- Python version and operating system
- Complete error message and stack trace
- Steps to reproduce the issue
- Expected vs actual behavior
- Bell System role and command being used