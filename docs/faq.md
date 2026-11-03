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
- `bell-system` - Log in and pick a position
- `bell-system --role 1` - Start as a specific role (1-12), skipping the menu
- `bell-system --simple` - A plain Unix V7 sandbox: a shell and filesystem, no board or positions
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
11. SARTS (Switched Access Remote Test) Technician
12. Document Preparation Specialist

### Q: Is there a tutorial?
**A:** No, and nothing to read first. The first tour opens with one report on the board and the wire chief walks you through the loop on `write(1)`. The job is four commands: `report`, `mlt 1`, `report dispatch 1 outside`, `report close 1 5 SHORT`.

### Q: How do I get help within the simulation?
**A:** Use these commands:
- `help` - What to do now, worked out from your board, then the commands for your position
- `help <command>` - One line on a single command
- `hint` - Ask somebody. Ask again and you get more
- `report next` - The one report that most wants working
- `man <command>` - Detailed manual page
- `?` or `h` - Aliases for `help`

## Historical Accuracy

### Q: How historically accurate is this simulation?
**A:** The simulation is based on authentic Bell System documentation from 1978-1983, including:
- Bell System Technical Journal articles
- AT&T Engineering and Operations manuals
- UNIX V7 system documentation
- Bell System Practices (BSP) documents

### Q: Why is a command refused?
**A:** Qualification governs what you may work on. You start signed off on Loop and Station plus whatever your position carries, and earn the rest a sign-off at a time: correct closures offer one at every 3 (Fun) or 12 (I Hate Myself), and a practical, `qual take <name>`, is what signs it. `help` marks the commands you cannot use yet with an asterisk, and `qual` shows your craft record and how many correct closes the next sign-off needs. `man <command>` documents any command, signed off or not.

### Q: What is the difference between the difficulties?
**A:** `set game.difficulty fun` is forgiving: loop testing names the fault for the first four sightings of each kind (`set assist.annotate on` keeps it doing so), you may close a report you never measured, and commitments are not counted. `set game.difficulty craft` ("I Hate Myself") prints only the numbers, requires a measurement before a close, brings wrongly closed lines back as repeats, and counts missed commitments. Difficulty changes how forgiving the scoring is and nothing else.

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
# career.json                Sign-offs, index, and your wire centre
# settings.json              Everything `set` changes
# shift.json                 The tour you are in the middle of
```

### Q: Do I lose my shift if I close the window?
**A:** No. The board, the weather, the water in the cable, where every crew
is standing and how much of every commitment has been spent are written to
`shift.json` after every command and picked back up next time you start.
Signing off with `handoff relieve` ends the tour and removes the file,
because the tour is finished. A saved shift belonging to a different tour,
or one that will not read, is discarded rather than repaired: it costs you
one tour and never leaves you with a board that is half of one shift and
half of another.

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
- Use the plain Unix sandbox: `bell-system --simple` (shell only, no board)
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