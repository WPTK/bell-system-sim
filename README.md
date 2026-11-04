# Bell System UNIX V7 Terminal Simulation

A text game set in November 1983. You work a repair test desk at a Bell System wire centre in Jersey City, logged into a simulated Seventh Edition UNIX machine, and take customer trouble reports from measurement to dispatch to close. It runs in your terminal, uses only the Python standard library and one packaged table of North American numbering plan data, and needs no network or API keys.

## Prerequisites

- Python 3.9 or newer.
- git and pip.
- A terminal. Output is plain 7-bit ASCII unless you change it.

The game has no third-party dependencies. Command history needs Python's `readline` module, which stock Windows Python does not have. The game runs without it.

## Quickstart

1. Clone the repository:

   ```bash
   git clone https://github.com/WPTK/bell-system-sim.git
   cd bell-system-sim
   ```

2. Install it:

   ```bash
   python -m pip install .
   ```

3. Start the game:

   ```bash
   bell-system
   ```

You see a login banner and a `mhuxco login:` prompt. Type `?` to list the twelve positions, then type `1` (or `sysop`) and press Enter. The board prints one pending report and the wire chief writes to your terminal. To skip the login, run `bell-system --role 1`. If your shell cannot find `bell-system`, run `python -m bell_system`.

## Configuration

Flags and environment variables:

| Variable / Flag | Default | Description |
| --- | --- | --- |
| `--role N` | login menu | Start as position N (1 to 12) and skip the login. |
| `--simple` | off | Start a plain Unix V7 shell with no board and no positions. |
| `--version` | | Print the version and exit. |
| `BELL_SYSTEM_HOME` | `$XDG_STATE_HOME/bell-system` | Directory for your saves, settings and logs. The game creates it if it is missing. |
| `XDG_STATE_HOME` | `~/.local/state` | Parent of the state directory when `BELL_SYSTEM_HOME` is not set. |

Settings live inside the game. Type `set` for the list, `set <setting>` to read about one, and `set <setting> <value>` to change it. The game saves your changes in `settings.json`. `set reset` restores every default.

| Setting | Default | Description |
| --- | --- | --- |
| `game.difficulty` | `fun` | `fun` lets you close a report you never measured and forgives a wrong call. `craft` ("I Hate Myself") makes you measure first, brings wrongly closed lines back as repeat reports and counts missed commitments. |
| `game.ambience` | `on` | `off` stops the other craft from writing to your terminal. |
| `game.prompts` | `off` | `on` prints the next useful command after a command that leaves you with nothing obvious to do. |
| `assist.*` | `profile` | Eight assists (`assist.test_first`, `assist.commitments_count`, `assist.repeat_reports`, `assist.commitment_slack`, `assist.pace`, `assist.scoring`, `assist.annotate`, `assist.sections`) set one part of the difficulty profile each. `profile` takes the value `game.difficulty` sets. |
| `display.pacing` | `300` | Print speed in baud: `110`, `300`, `1200` or `off`. The game never paces output that goes to a pipe. |
| `display.charset` | `ascii` | `unicode` allows block and box-drawing characters. |
| `display.prompt` | `v7` | `verbose` adds user, host and directory to the shell prompt. |
| `date.source` | `simulated` | `real` shows your own system clock instead of 1983. |
| `date.epoch` | `1983-11-14` | Start date of the shift, as `YYYY-MM-DD`. |
| `date.format` | `v7` | `iso` prints `YYYY-MM-DD`. `us` prints `MM-DD-YYYY`. |
| `date.clock` | `24` | `12` switches to a 12-hour clock. |
| `date.seconds` | `on` | `off` drops seconds from timestamps. |

The game writes these files to the state directory:

| File | Contents |
| --- | --- |
| `career.json` | Difficulty, sign-offs, service index history and your wire centre. |
| `shift.json` | The tour in progress. |
| `home.json` | What you write under `/usr/users` and the moo scoreboard, up to 64 KB. A file that fails to load is renamed `home.json.bad` and never overwritten. |
| `settings.json` | Settings whose value differs from the default. |
| `legacy.json` | What a finished career passes to the next one. |
| `archive/career-N/` | A finished career's files, moved here by `career new`. |
| `tones/` | Audio files written by the `tone` command. |
| `bell_system.log` | Application log, rotated at 10 MB with five backups. |
| `bell_system_history.txt` | Command history. Written only where `readline` is available. |

## Usage and controls

The game saves after every command. The work is four commands:

```
report                          show the board
mlt 1                           measure the line on report 1
report dispatch 1 outside       send a crew
report close 1 5 SHORT          close it as trouble found, fault SHORT
```

| Command | What it does |
| --- | --- |
| `report` | Lists the pending reports, nearest commitment first. |
| `report next` | Shows the one report that most wants working. |
| `report show <n>` | Shows the line record, the symptom and what has been done. |
| `report callback <n>` | Calls the customer for more than the card holds. |
| `mlt <n>` | Measures the loop. |
| `report dispatch <n> <force>` | Sends a crew. `report forces` lists them. |
| `report close <n> 5 <fault>` | Closes a report as trouble found. `report faults` lists the fault names. |
| `report close <n> 8` | Closes a report as no trouble found. A faulty line closed this way comes back as a repeat. |
| `help` | Lists the commands, starting with what to do now. |
| `hint` | Asks somebody. Ask again for more, up to three levels. |
| `man <command>` | Shows the manual page for a command. |
| `qual` | Shows your sign-offs and service index. `qual take <name>` sits the practical for one. |
| `shift` | Shows where you are in the tour. |
| `handoff` | Prints the turnover record. `handoff relieve` signs off the tour. |
| `career new` | Starts a new career once the last tour is signed off. |
| `exit` | Logs out. |

The rest is a Seventh Edition UNIX shell with `ls`, `cd`, `cat`, `grep`, pipes, `ed`, `cc` and `nroff`. Your board is the directory `/usr/lmos`. Press Ctrl-C to stop a listing.

A career is 13 tours that start on 14 November 1983 and end on 31 December 1983. Each position gets different work on the same board. At the login prompt, type `?` to list them:

| # | Login | Position |
| ---: | --- | --- |
| 1 | `sysop` | UNIX Systems Operator |
| 2 | `switch` | Switching Station Technician |
| 3 | `field` | Field Support Liaison |
| 4 | `noc` | National NOC Analyst |
| 5 | `tsps` | Traffic Service Position System Operator |
| 6 | `dba` | Database Administrator |
| 7 | `netplan` | Network Planning Engineer |
| 8 | `custserv` | Customer Service Interface Technician |
| 9 | `radio` | Radio/Microwave Technician |
| 10 | `tnds` | Total Network Data System Analyst |
| 11 | `sarts` | SARTS Technician |
| 12 | `docprep` | Document Preparation Specialist |

## Manual

Type `man <command>` in the game for the manual page of any command, and `help` for the commands your position has. The same pages, with a getting started guide and search, are at <https://wptk.github.io/bell-system-sim/>. Sources for every historical claim are in [SOURCES.md](SOURCES.md).

To build the site locally, install `docs/requirements.txt` into a virtual environment, then run `python tools/build_docs.py` and `mkdocs serve`.

## License

MIT. See [LICENSE](LICENSE).
