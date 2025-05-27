# UNIX Version 7 Terminal Simulation

An authentic terminal-based simulation of UNIX Version 7 from Bell Telephone Laboratories (1976), based on historical documentation from the Bell System Technical Journal and original UNIX manuals.

## Features

- **Authentic V7 Environment**: Simulates the exact behavior and output of UNIX V7 systems
- **Historical Accuracy**: Based on Bell Labs documentation from 1976-1979
- **Complete File System**: Realistic V7 directory structure with `/bin`, `/usr`, `/etc`, etc.
- **Core Commands**: All essential UNIX V7 commands implemented
- **Manual Pages**: Authentic manual pages matching original V7 documentation
- **Bell Labs Branding**: Original copyright notices and system messages

## Available Commands

### File Operations
- `ls` - list directory contents (with `-l`, `-a` flags)
- `cat` - display file contents
- `pwd` - print working directory  
- `cd` - change directory
- `find` - find files and directories
- `wc` - word, line, character count
- `grep` - search text patterns

### System Information
- `ps` - show running processes
- `who` - show logged in users
- `date` - show current date and time
- `df` - display filesystem usage
- `du` - display directory usage

### Text Tools
- `ed` - line editor (authentic V7 behavior)

### Built-in Commands
- `help` - show available commands
- `man` - display manual pages
- `history` - show command history
- `clear` - clear screen
- `exit` / `logout` - quit the simulation

## Historical Details

The simulation includes:
- Authentic Bell Labs users: `dmr` (Dennis Ritchie), `ken` (Ken Thompson)
- Original V7 system processes: `init`, `update`, `cron`, `getty`
- Real file structure with `/bin`, `/usr/bin`, `/lib`, `/usr/lib`
- Historical C program (`hello.c`) matching K&R style
- Original copyright notices and system messages

## Usage

```bash
python3 unix_terminal.py
```

The system will automatically log you in as `root` and present the authentic V7 prompt:

```
pdp11:/root# 
```

Try these commands to explore:
```bash
ls -la          # List files in long format
cat hello.c     # View the hello world program
cat /etc/motd   # Read the message of the day
ps              # See running processes
who             # See logged in users
man ls          # Read the manual page for ls
help            # Show all available commands
```

## Historical Context

This simulation is based on:
- UNIX Programmer's Manual, Seventh Edition (January 1979)
- Bell System Technical Journal articles from 1976
- PWB/UNIX documentation from Bell Telephone Laboratories
- Original V7 source code behavior and output formats

UNIX Version 7 was a landmark release that introduced many concepts still used today, including the pipe mechanism, the shell as a user program, and the foundation for modern UNIX systems.

## Technical Implementation

- Written in Python 3 for maximum compatibility
- Simulates authentic V7 file system structure
- Implements original command syntax and behavior
- Matches historical output formats and error messages
- Uses authentic Bell Labs terminology and system organization

---

*"The number of UNIX installations has grown to over 600, and many large projects are currently under way to transport it to machines other than the PDP-11."* - Dennis M. Ritchie, 1978