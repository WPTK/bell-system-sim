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
bell-system --role 1           # Start as specific role (1-12), skipping the menu
bell-system --simple           # Simplified four-role interface
python -m bell_system          # Equivalent to `bell-system`
```

## Features

- **12 Authentic Operational Roles** from UNIX Systems Operator to Document Preparation Specialist
- **A Repair Service Bureau to Work** with customer trouble reports, mechanised
  loop testing, repair dispatch and the two published disposition codes
- **Two Difficulties** - Fun Simulation, and I Hate Myself
- **Qualification-Based Progression** that governs what you are allowed to touch,
  the way it actually did
- **The Other Craft On The Wire** reaching you on `write(1)`, `mail(1)`, the
  order wire and the maintenance teletype
- **50+ Period-Accurate Commands** with comprehensive functionality and historical accuracy
- **Role-Specific Command Sets** with shift briefings and workflows for each position
- **Event and Ticket Management** using authentic Bell System trouble ticket systems
- **Simulated 1983 Shift Clock** running from Monday 14 November 1983, advancing in real time
- **Adjustable Fidelity** via the `set` command, period-accurate by default
- **Historical Documentation** based on Bell System Technical Journal and operations manuals
- **Pure Python Implementation** using only standard library modules

## The Machine

It is a Seventh Edition UNIX system and you are logged into it. Move around,
read things, join commands together.

```
cd /usr/doc         ls -l          cat divestiture
who | wc -l         ls /usr/bin | grep test
grep 1FR /usr/lmos/board | wc -l
```

The trouble report board is a file (`/usr/lmos/board`), one report to a line,
so `grep` and `sort` and `wc` are genuinely useful on it. Your shift log is a
file. The practices are files. Reading the board with `cat` is a real
alternative to the `report` screens.

It is writable, so `ed` and `cc` and `nroff` have somewhere to put things:

```
cp /usr/src/cmd/hello.c .    cc hello.c    a.out
ed report                    tbl table | nroff
echo 'note to self' > notes  banner SHIFT 2
```

`ed` is the real one — every line goes to it until you type `q`, and it
answers mistakes with a single question mark. `cc` compiles a C program and
leaves a working `a.out`; it understands `printf` and nothing else, and says
so. `nroff` and `tbl` are real formatters, so the Document Preparation role
finally does something.

There are things to find: the notes the previous operator left, this week's
operations bulletin, C source under `/usr/src/cmd`, a scoreboard somebody has
been keeping for `moo`, the accounting logs, a nightly netnews feed under
`/usr/spool/news` with people arguing on net.unix-wizards, and a memo
explaining what happens on 1 January 1984 — which is forty-eight days after
the shift starts, and is the day the Bell System stopped existing.

`bcd` punches your text onto an 026 card. `ppt` punches it onto paper tape.
`fortune` does what it always did.

You do not need to know anything about telephony to enjoy any of that.

## The Work

You sit at a test desk. Customer trouble reports arrive on your board with
nothing on them but the customer's own words, and what is actually on the pair
is not known until you measure it.

```
report                       The pending list, nearest commitment first
report show TR-04471         The line record, the symptom, what has been done
mlt TR-04471                 Measure the loop
report dispatch TR-04471 outside plant
report close TR-04471 5 GROUND       Trouble found, and what it was
report close TR-04471 8              No trouble found
```

Codes 5 and 8 are the published Bell System dispositions, counted separately in
the network switching performance measurement plan. Closing a faulty line as
code 8 does not fail loudly. It closes - and then the customer calls back, and
the repeat is on your service index.

Mechanised loop testing gives you insulation resistance on all three
combinations, loop resistance, foreign potential and capacitance. Local cable
runs 0.083 microfarads to the mile, so the capacitance reading on an open pair
is a distance to the break. Transmission goes through the far-end test line
series - 102-type for loss, 100-type for loss and noise, 105-type for the full
two-way picture - all at 1004 Hz, because that is the frequency the loss
objectives were stated at.

### Two Difficulties

```
set game.difficulty fun      Fun Simulation
set game.difficulty craft    I Hate Myself
```

**Fun Simulation** is forgiving. Loop testing names the fault it reads, you may
close a report you never measured, a wrong call costs you little, commitments
are not counted against you, and qualification comes quickly.

**I Hate Myself** is close to the job. Loop testing prints the numbers and
nothing else, because reading them is the work. A report cannot be closed until
it has been measured. Wrongly closed lines come back as repeat reports at a
rate you will not enjoy. Missed commitments count. Qualification is four times
slower, and the rest of the building interrupts you four times as often.

A test call proves a trunk end to end:

```
testcall EO-NYC-01 EO-BOS-01        Seize, outpulse, advance, answer, release
testcall EO-NYC-01 EO-BOS-01 105    ...and measure the connection you built
```

Seizure removes the 2600 Hz supervisory tone toward the far end, the far end
returns a start signal, the address goes out in multifrequency bracketed by KP
and ST, the call advances through the hierarchy - high-usage group first,
overflowing up the homing chain to a final group - and answer supervision
comes back. Loss accumulates on every trunk in tandem, so a call that took five
measures worse than one that took three.

### Progression

What a craftsperson was allowed to work on was governed by qualification. You
start signed off on Loop and Station, plus whatever your assigned position
carries, and earn the rest a correctly closed report at a time:

```
Loop and Station              report, mlt, trouble, testboard, testline
Main Distributing Frame       cosmos, lmos
Central Office Switching      switch, alarm, crossbar, 3a
Switching Control Center      sarts, orderwire
Interoffice Trunks            trunk, routing, dialtone
Toll Network                  toll, tnds, traffic
```

Type `qual` for your craft record and `qual index` for the measurement weights
the service index is scored against. `handoff relieve` signs off the shift and
banks the index; work you did not finish carries to the next one.

Two clocks run and they are not the same clock. A report's commitment runs on
elapsed time - the customer is out of service whether or not you are doing
anything, so the repair force's hours in a manhole count against it. Your own
working day runs on your time: you are at a test desk, and while the field is
out on one report you are working the next. Eight hours of your time and the
wire chief tells you your tour is up. A shift is about twenty-five reports.

### The Other Craft

You are not alone on the system. The repair service attendant puts reports on
your board and asks what she should tell the customer. The wire chief reads your
index every morning. The cable splicer calls in from a terminal box and does not
have all day. CAROT routines the trunk groups all night and prints its
exceptions to the maintenance teletype whether anybody is reading or not.

```
who                          Who is on the system
write gvasquez <message>     Interrupt somebody's terminal, as write(1) did
mail                         What is waiting for you
orderwire                    The maintenance circuit to the control centre
set game.ambience off        Silence, if you want it
```

## Accuracy and Playability

The simulation runs period-accurate by default: a 1983 clock, the bare Bourne
shell prompt, and output restricted to the printable 7-bit ASCII a Teletype
Model 43 or DATASPEED 40 could actually render.

Where accuracy costs playability on a modern terminal, the choice is yours
rather than ours. Type `set` for the settings screen:

```
set                          Show all settings and which depart from period behaviour
set date.format iso          Dates as YYYY-MM-DD instead of UNIX date(1) order
set date.clock 12            12-hour clock
set date.seconds off         Drop seconds from timestamps
set date.source real         Use your own system clock instead of 1983
set date.epoch 1978-06-01    Run the shift on a different date
set display.charset unicode  Allow block and box-drawing glyphs
set display.prompt verbose   Add user, host and directory to the prompt
set game.difficulty craft    Work the shift the hard way
set game.ambience off        Stop the other craft interrupting you
set reset                    Restore period-accurate defaults
```

Settings persist between sessions, and the screen marks any that depart from
1978-1983 behaviour. See `man set` for the full reference.

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

> **If you cloned before 31 August 2026:** the history was rewritten to remove
> 167 MB of scanned PDFs and a superseded data dump, taking a clone from
> 126 MiB to 6 MiB. Every commit SHA changed, so an existing clone cannot be
> pulled into — re-clone instead. File contents are unchanged; only the
> removed files and the commit identifiers differ. See `SOURCES.md`.

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
11. **SARTS (Switched Access Remote Test) Technician** - Service testing and validation
12. **Document Preparation Specialist** - Technical documentation

## Project Structure

```
├── src/
│   └── bell_system/                 # The installable Python package
│       ├── __init__.py              # Package exports and version
│       ├── __main__.py              # `python -m bell_system` entry point
│       ├── cli.py                   # Argument parsing and console script
│       ├── settings.py              # User-adjustable simulation settings
│       ├── clock.py                 # Simulated 1983 shift clock
│       ├── console.py               # Terminal output and character set
│       ├── progression.py           # Difficulty, qualification, service index
│       ├── reports.py               # Customer trouble reports and the bureau
│       ├── loop_testing.py          # Loop measurement and test lines
│       ├── npc.py                   # The other craft, and their channels
│       ├── terminal.py              # Dispatch, session and construction
│       ├── constants.py             # Values the terminal and screens share
│       ├── lmos.py                  # Loop Maintenance Operations System
│       ├── special_services.py      # SARTS and special services circuits
│       ├── screens/                 # One module per subsystem's screens
│       ├── simple_terminal.py       # Four-role simplified terminal
│       └── data/                    # Man pages, reference tables, and the
│                                    # packaged geographic dataset
├── tests/                           # pytest suite
├── tools/                           # Build scripts for packaged data
├── docs/                            # Manual, command reference, and guides
├── attached_assets/                 # Searchable text of the cited sources
├── SOURCES.md                       # What every historical claim rests on
├── ROADMAP.md                       # What is planned, and why
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
- **Sources**: `SOURCES.md` - What every historical claim rests on
- **Roadmap**: `ROADMAP.md` - What is planned, and why
- **Historical Assets**: `attached_assets/` - Searchable text of the cited documents

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
