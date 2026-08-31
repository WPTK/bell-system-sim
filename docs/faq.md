# Frequently Asked Questions

## Installation and Setup

### Q: What are the system requirements?
**A:** Python 3.9 or higher. No runtime dependencies required - the simulation uses only Python standard library modules.

### Q: How do I install the Bell System simulation?
**A:** Clone the repository and install in development mode:
```bash
git clone https://github.com/WPTK/bell-system-sim.git
cd bell-system-sim
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
- `bell-system --role 1` - Start as a specific role (1-12), skipping the menu
- `bell-system --simple` - Simplified four-role interface
- `bell-system --version` - Print the version and exit

`python -m bell_system` accepts the same options and is equivalent to
`bell-system`; it is useful when the console script is not on your `PATH`.

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
- `help` - Overview of the commands available to your role
- `help <command>` - Summary for a single command
- `man <command>` - Detailed manual page
- `?` or `h` - Aliases for `help`

## Historical Accuracy

### Q: How historically accurate is this simulation?
**A:** The simulation is based on authentic Bell System documentation from 1978-1983, including:
- Bell System Technical Journal articles
- AT&T Engineering and Operations manuals
- UNIX V7 system documentation
- Bell System Practices (BSP) documents

### Q: Why doesn't `help` list every command?
**A:** `help` shows the command set belonging to your operational role, just as an actual Bell System position would have had its own responsibilities and tools. The listing is role-specific; commands outside it are not blocked, so `man <command>` will document any command and you can still run it if you want to explore another role's work.

### Q: Are the error messages authentic?
**A:** Yes, error messages and system responses are modeled after actual Bell System and UNIX V7 patterns from the period.

## Technical Issues

### Q: The simulation crashes or shows import errors
**A:** Verify your Python installation and the package install, then try:
```bash
python3 -c "import sys; print(sys.version)"
python3 -c "import bell_system; print(bell_system.__version__)"
bell-system --version
```

### Q: Where are the log and command history files?
**A:** In a per-user state directory, not in the directory you ran from. The
location is `$BELL_SYSTEM_HOME` if set, otherwise `$XDG_STATE_HOME/bell-system`,
otherwise `~/.local/state/bell-system`:
```bash
ls "${BELL_SYSTEM_HOME:-${XDG_STATE_HOME:-$HOME/.local/state}/bell-system}"
# bell_system.log            Rotating application log (10 MB, 5 backups)
# bell_system_history.txt    Command history
```

### Q: Can I keep the simulation's files somewhere else?
**A:** Yes. Set `BELL_SYSTEM_HOME` to any directory you like; it is created if it
does not exist:
```bash
export BELL_SYSTEM_HOME=~/bell-system-state
bell-system
```

### Q: How do I see the debug log?
**A:** Everything at DEBUG level and above, including per-command execution
times, is already written to `bell_system.log` in the state directory. Only
warnings and errors are echoed to the terminal.
```bash
tail -f "${BELL_SYSTEM_HOME:-$HOME/.local/state/bell-system}/bell_system.log"
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
**A:** Install the development extras and run pytest:
```bash
pip install -e ".[dev]"
python -m pytest tests              # Full suite
python -m pytest tests/test_cli.py  # A single file
```
The suite redirects logs and history to a temporary directory, so it will not
write to your real state directory.

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

### Common Error: "Permission denied" writing logs
```bash
# Check that the state directory is writable
ls -ld "${BELL_SYSTEM_HOME:-$HOME/.local/state/bell-system}"

# Or point it somewhere you can write
export BELL_SYSTEM_HOME=/tmp/bell-system
```

### Common Error: "Command not found: bell-system"
```bash
# Verify installation
pip show bell-system-unix-v7

# Check PATH
echo $PATH
which bell-system

# Works without the console script on PATH
python -m bell_system --version
```

### Performance Issues
- Use the simplified interface: `bell-system --simple`
- Check available memory and disk space
- Per-command execution times are recorded in `bell_system.log`

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