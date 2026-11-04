# Getting started

It is Monday 14 November 1983. You work a repair test desk at a Bell System wire centre in Jersey City, logged into a Seventh Edition UNIX machine. Customers are out of service, and the Bell System has forty-eight days left to exist.

A trouble report reaches your board with nothing on it but what the customer said. What is on the pair stays unknown until you measure it. You measure it, send the right crew, and close the report with a published disposition code. The machine around you is a working UNIX system, and the rest of the building talks to you on it.

The game runs in a terminal, needs Python 3.9 or newer and nothing else, and uses no network. The [README](https://github.com/WPTK/bell-system-sim#readme) has the install steps. Everything below assumes it is running. The [command reference](command-reference/index.md) has one page for every command.

## Your first report

Start the game with `bell-system`, type `?` at the `mhuxco login:` prompt to see the twelve positions, then type `1` (or `sysop`). The board prints one pending report and the wire chief writes to your terminal. The chief walks you through the first loop.

The work is four commands:

```
report                          show the board
mlt 1                           measure the line on report 1
report dispatch 1 outside       send a crew
report close 1 5 SHORT          close it as trouble found, fault SHORT
```

A report answers to its number (TR-04471), to the telephone number on it, or to its position on the board. The game saves after every command, so you can quit with `exit` and pick up the tour where you left it.

If you get stuck, three commands help:

- `help` opens on what to do now, worked out from your actual board. `help <command>` gives one line on a single command.
- `hint` asks somebody. Ask again and you get more, up to three levels.
- `report next` shows the one report that most wants working.

`man <command>` prints the manual page for any command. To have the board print its next action along the bottom, run `set game.prompts on`.

## Reading a loop test

`mlt` reports two measurements that are easy to confuse. Insulation resistance is taken with the loop open and the office battery removed. It is high on a healthy pair and low wherever a fault bridges something. Which of tip-ring, tip-ground and ring-ground is low tells you what the fault is. Loop resistance is the resistance of the pair itself with the loop closed, and the 1300-ohm design limit applies to it.

Capacitance is the third reading. Local exchange cable runs 0.083 microfarads to the mile, so the capacitance of an open pair is a distance to the break.

| What you read | What it means |
| --- | --- |
| Infinite tip to ring, no station termination | open |
| Near zero tip to ring | short |
| One conductor low to ground, tip-ring normal | ground |
| Foreign potential with no battery applied | foreign EMF |
| Several pairs low in one cable | wet cable |
| Within limits, loop closed, current flowing | receiver off hook |
| Clean to the frame, customer still cut off | office equipment |

## Closing a report

Codes 5 and 8 are published Bell System dispositions. Code 5 is trouble found, and you name the fault you found and cleared. Code 8 is no trouble found. Closing a faulty line as code 8 closes the report, and the customer may call back. That repeat is what the performance plan counted. The chance is one in four in `fun` and 85 in 100 in `craft`.

The wrong repair force costs forty-five minutes and leaves the trouble where it was. `report forces` lists the forces and `report faults` lists the fault names.

## Difficulty

Two settings change how forgiving the desk is.

`set game.difficulty fun` is the default. Loop testing names the fault for the first two sightings of each kind, a report can be closed without measuring, a wrong call costs little, a missed commitment counts at a quarter, and qualification comes quickly.

`set game.difficulty craft` is called I Hate Myself. Loop testing prints the numbers and nothing else. A report cannot be closed until it has been measured. Wrongly closed lines come back as repeats, and missed commitments count. Qualification is four times slower, and the building interrupts you nearly four times as often.

`set game.ambience off` silences the other craft in either mode.

## Qualification and the service index

You start signed off on Loop and Station, plus whatever your position carries. The game offers the rest as correct closures add up. A command you are not signed off on is refused, except `cosmos jumper`, which only reads a line's frame record. `help` marks those with an asterisk, and `qual` shows how to earn each sign-off.

The ladder is the simulation's own. No source consulted says how many reports earned which sign-off, or that a sign-off locked a command.

The service index follows the weights in the network switching performance measurement plan. Customer reports carry ten of its hundred points, and that is the component you are scored on. `qual index` shows the weights.

Two clocks run. A report's commitment runs on elapsed time, because the customer is out of service whether or not you are working, so the repair force's hours count against it. Your own day runs on your time, because while the field is out on one report you are working the next. Eight hours and relief takes the position: the command in hand finishes, then the tour is handed off as `handoff relieve` would, on the board as it stands. `handoff relieve` signs off the tour, banks the index and starts a new board. Work you did not finish carries forward.

## The other craft

Four channels reach you:

- `write` interrupts you at your terminal, from another terminal on the same machine.
- `mail` reaches you whether you are at the terminal or not.
- `orderwire` is the maintenance circuit between offices, the field and the switching control centre.
- The switching machine's maintenance teletype prints on its own schedule, with no sender.

The people are invented. Their jobs, their places and what they say about the plant come from the period documents listed in [SOURCES.md](https://github.com/WPTK/bell-system-sim/blob/main/SOURCES.md).

## The machine

It is a Seventh Edition UNIX system, so you can move around, read things and join commands with pipes:

```
cd /usr/doc
who | wc -l
ls /usr/bin | grep test
grep WRONG /usr/lmos/closed
```

The board is a directory. `/usr/lmos` holds one file per report, plus `board`, `closed` and `cable`. Your mail is a file under `/usr/spool/mail`, and the practices are under `/usr/bsp`. The filesystem is writable, so `ed`, `cc` and the formatters have somewhere to put things.

## Positions

Twelve positions work the same board and get different work on it, different people talking to them and a different measure of a good tour. Start one directly with `bell-system --role N`.

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

## Settings

Type `set` to see every setting, its value and its options. Settings persist between sessions, and `set reset` restores the defaults.

```
set display.pacing off       print at once instead of at 300 baud
set date.format iso          dates as YYYY-MM-DD
set date.source real         use your own system clock instead of 1983
set display.charset unicode  allow block and box-drawing characters
```

The README lists every setting and every file the game writes to its state directory.

## Where to go next

The [command reference](command-reference/index.md) groups every manual page by who uses it. Use the search box to find a command or a word on a page. Every historical claim in the game rests on a source listed in [SOURCES.md](https://github.com/WPTK/bell-system-sim/blob/main/SOURCES.md), and the simulation's own inventions are marked as such.
