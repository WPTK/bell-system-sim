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

**It is Monday 14 November 1983. You are at a repair test desk in a Bell
System wire centre in Jersey City, logged into a Seventh Edition UNIX
machine. Customers are out of service. The Bell System has forty-eight days
left to exist.**

On 8 January 1982 AT&T settled the Justice Department's antitrust suit by
agreeing to divest the operating companies. The decree took effect on
1 January 1984, and *Engineering and Operations in the Bell System* records
the consequence plainly: the existence of the Bell System ends with
divestiture. This simulation is set in the run-up. Nothing about the job
changes because of it, which is the point — the reports still arrive, the
commitments still run, and everybody in the building knows.

You work the board. A customer report reaches you with nothing on it but
what the customer said; what is actually on the pair is not known until you
measure it.

```bash
git clone https://github.com/WPTK/bell-system-sim.git
cd bell-system-sim
pip install -e .
bell-system
```

Python 3.9 or newer. No dependencies — standard library only.

---

## Your first ten minutes

There is no tutorial mode and nothing to read first. Log in and the wire
chief puts his head round the door.

The first tour opens with **one report** on the board and the rest held off
it until that one is closed. Halloran walks you through the loop on
`write(1)`, one message per step, and then stops. That is the whole of the
onboarding.

The job is four commands:

```
report                          what is on your board
mlt 1                           measure the line
report dispatch 1 outside       send somebody
report close 1 5 SHORT          close it out
```

`mlt` names the fault and the crew outright on the forgiving difficulty —
you do not need to know any telephony to play. Three things exist for when
you are stuck:

| | |
|---|---|
| `help` | opens on **what to do now**, worked out from your actual board |
| `hint` | asks somebody. Ask again and you get more, three levels deep |
| `report next` | shows the one report that most wants working |

Every refusal names a way out, and the board prints its own next action
along the bottom. If you would rather it did not, `set game.prompts off`.

---

## The work

```
report                       The pending list, nearest commitment first
report show TR-04471         The line record, the symptom, what has been done
report callback TR-04471     Telephone the customer for more than the card holds
mlt TR-04471                 Measure the loop
report dispatch TR-04471 outside plant
report close TR-04471 5 GROUND       Trouble found, and what it was
report close TR-04471 8              No trouble found
```

Codes 5 and 8 are the published Bell System dispositions, counted
separately in the network switching performance measurement plan. Closing a
faulty line as code 8 does not fail loudly. It closes — and then the
customer calls back, and the repeat is on your service index.

**A wrong close tells you what you missed.** Not a score: the actual
numbers from the measurement you took, and what they meant.

> That pair had a wet cable, not a short.
>
> Insulation measured 48,591 ohms tip to ring and 20,241 to ground. Low but
> not zero, and low on every reading at once, is water in the sheath. Short
> reads near zero resistance tip to ring.

Mechanised loop testing gives you insulation resistance on all three
combinations, loop resistance, foreign potential and capacitance. Local
cable runs 0.083 microfarads to the mile, so the capacitance reading on an
open pair is a distance to the break. Transmission goes through the
far-end test line series — 102-type for loss, 100-type for loss and noise,
105-type for the full two-way picture — all at 1004 Hz, because that is the
frequency the loss objectives were stated at.

Water is a **sheath** fault, not a pair fault. A wet binder group takes
more pairs the harder it rains, so several reports off one cable are one
trip, and `cat /usr/lmos/cable` is how you notice before you send four
crews.

### Two difficulties

```
set game.difficulty fun      Fun Simulation
set game.difficulty craft    I Hate Myself
```

**Fun Simulation** is forgiving. Loop testing names the fault it reads, you
may close a report you never measured, a wrong call costs you little,
commitments are not counted against you, and qualification comes quickly.

**I Hate Myself** is close to the job. Loop testing prints the numbers and
nothing else, because reading them is the work. A report cannot be closed
until it has been measured. Wrongly closed lines come back as repeat
reports at a rate you will not enjoy. Missed commitments count.
Qualification is four times slower, and the rest of the building interrupts
you four times as often.

The difficulty governs **how forgiving the scoring is** and nothing else.
How much is happening is a matter of how far into a career you are.

### A career, and its last day

What a craftsperson was allowed to work on was governed by qualification.
You start signed off on Loop and Station plus whatever your position
carries, and earn the rest a correctly closed report at a time:

```
Loop and Station              report, mlt, trouble, testboard, testline
Main Distributing Frame       cosmos, lmos
Central Office Switching      switch, alarm, crossbar, 3a
Switching Control Center      sarts, orderwire, connect
Interoffice Trunks            trunk, routing, dialtone, testcall
Toll Network                  toll, tnds, traffic
```

Halloran signs them, and he notices the third. By the fifth there is not
much left that he can sign.

**A career walks the calendar.** Tours are four days apart, so the
thirteenth falls on 31 December 1983 and there is no fourteenth. The board
gets deeper as you go and the weather gets worse, because it is December.
Signing off that last tour closes the career: the whole record, every tour
of the service index drawn as a trend, and the wire chief. It happens once.

```
shift                        Where you are in the tour
handoff                      The full turnover record
handoff relieve              Sign off. The index banks, the day moves on
qual                         Your craft record and the trend
```

**Your tour survives the window closing.** The board, the weather, the
water in the cable, where every crew is standing and how much of every
commitment has been spent are written down after every command and picked
back up next time you start.

Two clocks run and they are not the same clock. A report's commitment runs
on elapsed time — the customer is out of service whether or not you are
doing anything, so the repair force's hours in a manhole count against it.
Your own working day runs on your time: while the field is out on one
report you are working the next.

---

## The machine

It is a Seventh Edition UNIX system and you are logged into it. Move
around, read things, join commands together.

```
cd /usr/doc         ls -l          nroff why.unix
who | wc -l         ls /usr/bin | grep test
grep WRONG /usr/lmos/closed
```

**Your board is a directory.** `/usr/lmos` holds one file per report with
the whole record on it, plus three that are always there: `board`, `closed`
and `cable`. Your mail is a file under `/usr/spool/mail`. The practices are
under `/usr/bsp`. So there are two ways to work and neither is the proper
one.

New to UNIX? The annual refresher is on the machine and takes ten minutes:

```
training unix
```

It covers the shell, reading a file, joining two commands with a pipe, and
why a document under `/usr/doc` prints as dot commands until you run it
through `nroff(1)`.

The filesystem is writable, so `ed` and `cc` and the formatters have
somewhere to put things:

```
cp /usr/src/cmd/hello.c .    cc hello.c    a.out
ed report                    tbl table | nroff
echo 'note to self' > notes  banner SHIFT 2
```

`ed` is the real one — every line goes to it until you type `q`, and it
answers mistakes with a single question mark. `cc` compiles a C program and
leaves a working `a.out`; it understands `printf` and nothing else, and
says so.

### Things to find

The machine rewards poking at. Some of it is useful, some of it was written
by somebody at Murray Hill on a Friday, and part of the point is that you
cannot always tell which until you have looked.

Without spoiling any of it: there are notes from whoever held your position
last, a nightly netnews feed with people arguing on `net.unix-wizards`, a
scoreboard somebody has been keeping and a grudge attached to it, a file
you cannot read yet and will be able to later, a memo about January, C
source, `fortune`, and a trouble report whose answer is a sound rather than
a number. `/usr/games` exists because it is a long night shift.

```
tone busy                    Write a signalling tone to a file you can listen to
tone reorder                 The same two frequencies, twice as fast
bcd HELLO                    Punch it onto an 026 card
readnews                     The overnight feed
```

You do not need to know anything about telephony to enjoy any of that.

---

## The other craft

You are not alone on the system. The repair service attendant puts reports
on your board and asks what she should tell the customer. The wire chief
reads your index every morning. The cable splicer calls in from a terminal
box and does not have all day. CAROT routines the trunk groups all night
and prints its exceptions to the maintenance teletype whether anybody is
reading or not.

Four lines the bureau knows by heart come back across a career — a sheath
on Sussex Street that has been in water since the spring, a coin station in
a rooming-house lobby, a drop over a bus route — and `custdb` says how long
you have known them and what the last craftsperson wrote on the card.

```
who                          Who is on the system
write gvasquez <message>     Interrupt somebody's terminal, as write(1) did
mail                         What is waiting for you
orderwire                    The maintenance circuit to the control centre
set game.ambience off        Silence, if you want it
```

---

## Accuracy and playability

The simulation runs period-accurate by default: a 1983 clock, the bare
Bourne shell prompt, output restricted to the printable 7-bit ASCII a
Teletype Model 43 or DATASPEED 40 could render, and printing paced at
**300 baud** — ten bits to the character, thirty characters a second, which
is what a Model 43 actually did.

Where accuracy costs playability on a modern terminal, the choice is yours
rather than ours. Type `set` (or `settings`) for the screen, which lists
every setting, its current value, its options, and marks any that depart
from 1978–1983 behaviour.

```
set                          Every setting and where it stands
set display.pacing off       Print at once instead of at 300 baud
set display.pacing 110       A Model 33 instead: eleven bits, ten a second
set date.format iso          Dates as YYYY-MM-DD instead of UNIX date(1) order
set date.source real         Use your own system clock instead of 1983
set date.epoch 1978-06-01    Run the shift on a different date
set display.charset unicode  Allow block and box-drawing glyphs
set game.difficulty craft    Work the shift the hard way
set game.prompts off         Stop the terminal telling you what to do next
set game.ambience off        Stop the other craft interrupting you
set reset                    Restore period-accurate defaults
```

Settings persist between sessions. Pacing switches itself off when output
is not going to a terminal, because a pipe has nobody watching it.

Every historical value in the simulation is either verified against a
bundled document, externally sourced and labelled, or explicitly marked as
the simulation's own invention. Where a source could not be reached, the
gap is recorded in the code rather than filled with something plausible.
`SOURCES.md` is the record.

---

## Running it

```bash
bell-system                    Start the simulation
bell-system --role 3           Start at position 3, skipping the login
bell-system --simple           A simplified four-role interface
python -m bell_system          Equivalent to bell-system
bell-system --version
```

At the login prompt, `?` lists the twelve positions. Each works the same
board but gets different work on it, different people talking to it, and a
different measure of a good tour:

| | | | |
|---|---|---|---|
| 1 `sysop` | UNIX Systems Operator | 7 `netplan` | Network Planning Engineer |
| 2 `switch` | Switching Station Technician | 8 `custserv` | Customer Service Interface |
| 3 `field` | Field Support Liaison | 9 `radio` | Radio/Microwave Technician |
| 4 `noc` | National NOC Analyst | 10 `tnds` | TNDS Analyst |
| 5 `tsps` | Traffic Service Position Operator | 11 `sarts` | SARTS Technician |
| 6 `dba` | Database Administrator | 12 `docprep` | Document Preparation |

### Where your files go

State is written to a per-user directory, not the one you ran from:
`$BELL_SYSTEM_HOME` if set, otherwise `$XDG_STATE_HOME/bell-system`,
otherwise `~/.local/state/bell-system`.

| | |
|---|---|
| `career.json` | Difficulty, sign-offs, index history, your wire centre |
| `settings.json` | Everything `set` changes |
| `shift.json` | The tour you are in the middle of |
| `bell_system.log` | Rotating application log |
| `bell_system_history.txt` | Command history |

> **If you cloned before 31 August 2026:** the history was rewritten to
> remove 167 MB of scanned PDFs and a superseded data dump, taking a clone
> from 126 MiB to 6 MiB. Every commit SHA changed, so an existing clone
> cannot be pulled into — re-clone instead. File contents are unchanged.

---

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests        # 1800-odd tests
ruff check src tests
mypy src/bell_system          # clean, with no suppressions
```

The package is `src/bell_system/`. `terminal.py` is dispatch and session
only; every screen lives in `screens/`, one module per subsystem, mixed
into the terminal. `screens/session.py` declares every attribute and
cross-mixin method they share, which is what keeps that arrangement
honest. Reference tables and manual pages live in `data/`.

Three guards in `tests/test_integrity.py` hold the shape: no screens module
over 1,000 lines, `terminal.py` under 2,000, and every `self.x()` call
resolving against the constructed class.

| | |
|---|---|
| `docs/overview.md` | How the package fits together |
| `docs/api.md` | Programmatic use of the simulation classes |
| `docs/manual.txt` | Operational guide |
| `docs/command_reference.txt` | Quick reference |
| `docs/faq.md` | Common questions |
| `docs/contributing.md` | Layout and conventions |
| `SOURCES.md` | What every historical claim rests on |
| `attached_assets/` | Searchable text of the cited documents |
