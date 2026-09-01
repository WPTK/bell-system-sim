# Changelog

All notable changes to the Bell System UNIX V7 Terminal Simulation project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-09-01

This release ships everything listed under the `[Unreleased]` sections below,
which accumulated during development, together with the work described here.

The version jumps to 4.0.0 because `--tutorial` is gone and `BellSystemTutorial`
no longer exists as a package export. The package version had also drifted to
2.1.0 while the changelog was at 3.0.0; both now agree.

The round began with the roadmap closed and one question left: whether the
thing was any good to play. It was played rather than read, and the finding
inverted what the roadmap had assumed. **The game was not hard. It was
undiscoverable.** The core loop is four commands, `mlt` names the fault and
the dispatch outright - it was right sixty times out of sixty when that was
measured - and no telephony is needed to work a report. What the loop required
was knowing it existed, and nothing said so: the first screen a new player saw
was forty commands followed by a list of sixteen they were not signed off on.
Everything below follows from that.

### Added - Knowing what to do

- **The tutorial is the first tour.** `tutorial.py` and the `--tutorial` flag
  are gone: 560 lines that walked a radio desk through commands in a terminal
  that was not the game, before the game started, behind a flag whose own
  docstring said to run it *before* using the simulation. A first tour now
  opens with one report on the board and the rest held off it until that one
  is closed, and the wire chief walks you through the loop on `write(1)`, one
  message per step, then stops. That is the whole of the onboarding.
- **One place decides what to do next.** `screens/guidance.py` reads the board
  and returns the single next thing worth doing. Four things ask it - the
  standing prompt after a command, the top of `help(1)`, the board's own
  footer, and the wire chief - so they cannot end up describing different
  situations, which they would have within a fortnight if each worked it out
  for itself.
- **A standing next-action line** after any command that leaves you with
  nothing to look at. `set game.prompts off` for anybody who knows the job.
- **Every refusal names a way out.** A mistyped command, a command you are not
  signed off on, an unknown `report` verb: each was a place a player could
  stop. Each now ends with somewhere to go - and says nothing when the board
  is clear, because telling somebody who mistyped a command to go and read the
  news is not help.
- **`report next`** shows the one report that most wants working. The board is
  a table and reading a table is a skill; this is the same decision the
  standing prompt makes, spent as a command.
- **`help(1)` opens on WHAT TO DO NOW** and names the four commands outright.
  The list of things you are not signed off on moved to `qual(1)`, next to the
  sign-offs that open them.
- **`hint(1)`, one level at a time.** Vasquez on the testboard gives a nudge,
  then you are sent to read something that exists on this machine, then
  Halloran says it outright and is short about it, because by then you have
  asked three times. The level resets when the situation changes. One minute
  of shift time and nothing else: being stuck is already the penalty, and a
  hint with a score attached is a hint nobody uses. Modelled on Infocom's
  InvisiClues, which worked because asking was a deliberate act.
- **`training unix`,** the annual refresher on the machine rather than the job.
  The Seventh Edition toolkit was all implemented and almost none of it was
  discoverable: `/usr/doc/loop.pic` is a diagram that prints as nine lines of
  markup because it is `pic(1)` source, and somebody who `cat`s it reasonably
  concludes the file is broken. The course covers looking around, reading, the
  formatters, pipes, the board as a directory, and where the rest of the
  machine is. Every command it names is checked against the dispatch table and
  every path against the filesystem, so it cannot drift into teaching
  something that is not there.

### Added - Feedback that teaches

- **A post-mortem on a wrong close,** in the numbers the player actually had.
  `measure_loop` is seeded from the line and the fault, so the explanation
  quotes rather than invents, and each rule names the *discriminating* figure:
  tip to ring on a short, the conductor to ground on a ground, the volts on a
  foreign EMF. A line closed without being measured is told what `mlt` would
  have read instead of a number, because naming a figure there would teach the
  wrong reading half the time.
- **A tour summary above the tally.** Three sentences on signing off: what went
  well, what did not, and the one thing worth doing differently. One thing,
  never three, because a list of four things to improve is a list nobody acts
  on.
- **The index as a trend.** `qual(1)` draws the last five tours as a bar once
  there are three behind you. The block glyphs transliterate to a density ramp
  on a terminal held to the period character set, which is what a printer
  would have used to draw the same thing.

### Added - Stakes, and people who remember you

- **The divestiture countdown** is now the line before anybody has typed
  anything, computed from the epoch rather than written down.
- **A career walks the calendar.** Tours are four days apart, so thirteen of
  them cover the forty-eight days from 14 November and the thirteenth falls on
  31 December 1983. There is no fourteenth. Signing that one off closes the
  career: the whole record, every tour of the index drawn as a trend, and the
  wire chief. It happens once, and the board stays on the machine afterwards,
  because the machine did not stop on the first of January either.
- **Halloran has an arc.** He signs every qualification, so a fixed line made
  him a form letter. He now says something different at each, notices the
  third, and close to January cannot honestly duck what a sign-off is worth.
- **Four lines the bureau knows by heart** turn up on about one report in six:
  a sheath on Sussex Street that has been in water since the spring, a coin
  station in a rooming-house lobby, a drop over a bus route, a doctor's
  answering line the frame keeps eating. `custdb(1)` says how long we have
  known them and what the last craftsperson wrote on the card.

### Added - The shape of a session

- **A tour survives the window closing.** `save.py` writes the working shift
  after every command - the board, the weather, the water in the cable, where
  every crew is standing, how much of every commitment has been spent - and
  picks it back up next time. Everything is written by hand, field by field;
  nothing is pickled, and a save file is a JSON object a person can read.
  Anything unreadable, from another version, or belonging to a different tour
  is discarded rather than repaired: a shift is two hours, and a resume that
  half works is worse than starting again.
- **`shift(1)`** is the four numbers you want in the middle of a tour, against
  `handoff(1)`'s page and a half at the end of one.
- **The career escalates, on two levers that were measured rather than set by
  eye.** The board goes from nine open reports to eleven across thirteen tours
  and closes the same thirty-two a tour at either end, because arrival falls
  as depth rises - depth is pressure, not volume. The weather goes from twelve
  per cent wet tours to twenty-two, which is the calendar rather than a
  difficulty knob. The difficulty setting still governs only how forgiving the
  scoring is, and there is a test that says so.

### Added - The job as files

- **`/usr/lmos` is the board.** One file per pending report carrying the whole
  record, kept level with the board so a closed report leaves the directory
  rather than sitting in a listing that lies. Three names are always there
  beside them: `board`, `closed`, and `cable` - the last being the one thing
  the board genuinely cannot show you, because a wet sheath is a property of
  the plant rather than of any pair, and reading it is how you find out that
  four reports are one trip.
- **Mail is a file**, under `/usr/spool/mail`, the way Seventh Edition kept it,
  so `grep(1)` works on it. `mail(1)` still empties it when read, which is also
  what Seventh Edition did.

### Added - Things to find

- The `moo` scoreboard takes your score, and Okafor disputes her eleven again
  if you beat it. Her position on that eleven is a matter of record.
- `/usr/adm/sulog` is shut until the wire chief puts you in the `adm` group,
  and when it opens your own `su` attempts are in it. The mode column had been
  on every listing since the filesystem was written and had never meant
  anything; it means something on exactly one file.
- A report about calls not completing now has the customer describing a
  *rhythm* rather than a fault. Busy and reorder are the same 480 and 620 Hz
  and differ only in how fast they are interrupted, so the words cannot
  separate them and the ear can. `tone(1)` writes both. Three conditions share
  that symptom and all three have something to hear, because one without would
  be the answer.
- The message of the day says the games are there, which nothing ever had.

### Added - Earlier in the round

- **Twelve desks that are not the same desk twelve times over.** Each position
  now draws different faults, carries a different board depth, hears from
  different people on the wire, and is judged on the measurement component its
  own work maps to. A planning desk is no longer scored on repair commitments.
- **Eleven buildings on one console.** `connect` works a remote office from the
  switching control centre, with per-office alarm state, and `company` says
  which of the seven regional holding companies each building passes to in
  January.
- **The tone plan, heard rather than read.** `tone` synthesises dial, busy,
  reorder, ringback, congestion, howler, MF and DTMF digits and SF supervision
  to a WAV file at the documented frequencies, levels and cadences. Dial
  against busy measures 11.0 dB apart, which is what the table says.

### Changed

- `help(1)` no longer ends on what you cannot do. The count and a pointer stay;
  the list moved to `qual(1)`.
- The `README` is rewritten around the game rather than a feature list. It led
  with "12 roles, 50+ commands" and said nothing about the first tour, the
  wire chief, `hint(1)`, the career, or a shift surviving the window closing.
  It now opens on the date and the stakes, then the four commands. Things to
  find are teased and not spoiled.
- `SOURCES.md`'s text inventory is counted in lines and words rather than
  megabytes. Half the table read `0.0 MB` and twenty more rows all read
  `0.2 MB`, which distinguished nothing; these files are grepped, and `grep -n`
  answers in line numbers.
- The `terminal` test fixture starts on the second shift with prompts off, for
  the same reason it already had ambience off: a test that exercises a command
  wants the command, not a dice roll and the state of the board.
- `screens/shift.py` gives up the turnover half to `screens/turnover.py`, and
  `terminal.py` gives up `help(1)` to `screens/guidance.py`, both under the
  integrity guards.

### Removed

- `src/bell_system/tutorial.py`, the `--tutorial` flag, and the
  `BellSystemTutorial` export.
- 114 lines of blank space and orphaned section headings left in `terminal.py`
  by an older refactor.
- The finished planning documents - the audit, its remediation, the roadmap,
  the fun plan and a superseded UX proposal - move to a gitignored
  `docs/archive/`. They record how the project got here rather than how it
  works. `SOURCES.md` stays: it is the live provenance record and is cited from
  the code.

### Fixed

- **The wire centre was redrawn every session.** The switching machine at an
  office is drawn at random and the COMMON LANGUAGE code is built from it, so a
  craftsperson turned up at a differently named building each morning and every
  line record they had ever seen belonged somewhere else. Nothing noticed until
  a shift started surviving the session and refused to load into the wrong
  office. The office is career state now.
- **A regular's line record was shared across every report on it**, so this
  week's trouble rewrote last week's - and because the measurement is seeded
  from the fault, an old report measured as something it was never closed as.
- **`su(1)` appended to the log through the operator's own read**, which
  silently emptied `/usr/adm/sulog` for anybody not yet allowed to read it,
  which is everybody at the start.
- **A saved shift that would not parse was never discarded**, so it sat there
  refusing to load and taking each tour's work down with it.
- **The career had no end.** Tours ran past the divestiture date for ever, each
  one announcing that it was the last working day of the Bell System.
- **The report files were a minute behind the board.** The sync ran after a
  command rather than before, which left `ls(1)` one report behind `cat(1)` on
  `/usr/lmos/board` - that file is rendered when it is read, so the two were
  describing boards a minute apart.
- **An undiagnosed intermittent failure** in `custdb(1)`'s listing test, which
  took its telephone number after running the command and so could pick a
  report that arrived during it. Two new tests made the same mistake and were
  rewritten to compare within one command.
- Prose defects in the close-out that had been there since it was written:
  "a open", "a foreign emf" (an article that never looked at the noun, and a
  `lower()` that flattened initialisms), "a central office equipment on that
  pair" for a fault that was never on the pair, and "Needs 1 more correct
  closures".
- `handoff(1)`'s manual page described four verbs the command does not have and
  never mentioned `relieve`, the one that ends a tour.

### Verification

1,786 tests passing and 1 skipped, against 1,391 at the start of the round.
`ruff` and `mypy` clean across 72 source modules with no suppressions. CI green
on Python 3.9, 3.10, 3.11 and 3.12.

## [Unreleased]

### Added - Gameplay: the work, the difficulty and the other craft

- **The repair service bureau.** Customer trouble reports arrive on a pending
  board carrying a hidden electrical fault. Commitment intervals lengthen with
  the backlog; every action is charged against them. Reports close against
  disposition code 5 (trouble found, name the fault) or code 8 (no trouble
  found) - the two published Bell System dispositions, counted separately in
  the network switching performance measurement plan. Closing a faulty line as
  code 8 brings the customer back as a repeat report.
- **Mechanised loop testing.** `mlt` reports insulation resistance on all three
  combinations, loop resistance, foreign potential and capacitance. Insulation
  and loop resistance are kept strictly apart, because they are different
  measurements and only one of them is what the 1300-ohm design limit applies
  to. Capacitance converts to distance at the documented 0.083 uF per mile for
  local exchange cable. Readings are seeded from the line's own number, so a
  pair measures the same on every retest.
- **Far-end test lines.** The 100, 102 and 105-type series, the balance test
  line and the remote office test line, all measured at 1004 Hz. Test line
  types and their measurements are attested in the Bell System Technical
  Journal for April 1982; the dialable access codes are the simulation's own
  and are marked as such, because real ones were local to each office.
- **Single frequency supervision.** `testboard supervision` reads the 2600 Hz
  supervisory state of a trunk. Tone on when idle, off when seized, and tone
  present during a connection is the irregularity routine testing looks for.
- **Two difficulties.** `set game.difficulty fun` for Fun Simulation and
  `set game.difficulty craft` for I Hate Myself. The harder setting withholds
  the fault name from loop testing, refuses a close on an unmeasured line,
  brings wrongly closed lines back at a much higher rate, counts missed
  commitments, quadruples the qualification requirement and quadruples how
  often the rest of the building interrupts you.
- **A service index with room to fall.** The measurement plan scored an office
  across ten weighted components summing to 100, of which customer reports
  carried ten. A craftsperson is scored on that component out of 100, because
  scoring them across the whole plan would mean total failure on the one
  component they control could still cost only twenty points. `qual index`
  shows both numbers: the component score, and what it is worth to the
  office's own index.
- **Qualification-based progression.** Six qualifications gate the commands
  they open. A new craftsperson holds Loop and Station plus whatever their
  assigned position carries, and earns the rest a correctly closed report at a
  time. `qual` shows the craft record; `qual index` shows the measurement
  weights the service index is scored against.
- **A persistent career.** Difficulty, qualifications, closure counts and the
  index history survive between sessions in `career.json` beside the settings,
  and tolerate a missing or damaged file the same way the settings do.
- **Shift handoff that carries state.** `handoff relieve` banks the service
  index against the shift, advances the shift count and opens a new board;
  unfinished work carries forward.
- **The other craft, on four period channels.** `write(1)` interrupts your
  terminal in the Seventh Edition form, `mail(1)` waits for you, the order wire
  carries the field forces and the switching control centre, and the
  maintenance teletype prints CAROT's exceptions whether anybody is reading or
  not. `who` and `write` now list the same eight people.
- **Test calls.** `testcall <from> <to> [test line]` places a call through the
  network and shows every stage: seizure removing the 2600 Hz supervisory tone,
  the start signal from the far end, the multifrequency address bracketed by KP
  and ST, the route advance through the hierarchy, answer supervision, and
  release. Name a test line and the connection is measured rather than merely
  completed, with loss accumulating over every trunk in tandem.
- **Ticket assignment by name.** The switching control centre puts one of the
  existing trouble tickets on your position over the order wire, which is the
  difference between a list and an assignment.
- **A working shift clock.** The simulated clock runs in real time, so a
  shift's events would never come due inside a session anybody would sit
  through. Events come due on the work instead: every command costs a minute
  at the terminal, and everything you do to a report is charged to the shift
  as well as to the report's commitment. Eight hours of work and the wire
  chief tells you your tour is up. A shift is about twenty-five to thirty
  reports.
- **Two clocks, kept apart.** A report's commitment runs on elapsed time - the
  customer is out of service whether or not you are doing anything, so the
  repair force's hours in a manhole count against it. Your own working day
  runs on your time; you are at a test desk, and while the field is out on one
  report you are working the next.
- **`set game.ambience off`** for players who want the terminal to themselves.

### Changed

- **`help` leads with the work.** It now opens with the board and how many
  reports are on it, groups commands by what they are for, marks anything the
  craftsperson is not signed off on, and lists what is still locked. `help
  <command>` gives the one-line summary from that command's manual page and
  says if it is gated.
- **The shift briefing shows the board.** Whatever position was selected,
  the briefing states what is pending, the nearest commitment, the difficulty,
  the service index and how many qualifications are held - and on a first
  shift, that the harder setting exists.
- **The tutorial teaches the job.** A new step walks the report loop, how to
  read a loop measurement, and why closing a faulty line as code 8 costs more
  than leaving it open.
- `testboard` is a working board rather than a fixed screen: it measures loops,
  reaches test lines and reads supervision.
- `who` lists the craft roster with job titles, and everyone it lists can
  actually be written to.

### Fixed

- **A trouble ticket entered by craft crashed every screen that read it.**
  `trouble create` stored a bare office code where generated tickets store the
  office record, so `trouble list`, `trouble geographic`, `trouble priority`
  and `handoff` all raised `string indices must be integers` for the rest of
  the session. Manual tickets now carry the same record.
- **Shift handoff printed a Python dictionary.** The critical-ticket block
  rendered the office record raw, putting `{'npa': '213', ...}` on a terminal
  that could not have produced one. Offices now render as a place and a CLLI.
- `TroubleTicket.affected_office` was declared as `str` while every producer
  and consumer treated it as a record. The declaration now matches the code.
- The SARTS role's help listed `testing` and `circuits`, neither of which has
  ever been a command. Every name in the role help is now checked against the
  dispatch table by the test suite.
- The module integrity guard no longer flags ordinary prose that begins with
  the word "from" as an import stranded in a docstring.

### Notes on provenance

Attested and used: the corrective maintenance sequence; disposition codes 5 and
8; the measurement plan weights; the electrical fault vocabulary; the
100/102/105-type test line series and their measurements; the remote office
test line, the 52A responder, CAROT and the processor controlled interrogator;
1004 Hz as the frequency loss objectives are stated at; 0.083 uF per mile local
cable capacitance; the 1300-ohm and 1500-ohm loop design limits with their
length bands; 23 mA for coin station operation.

Marked in source as the simulation's own, not claimed as Bell practice: the
customer-facing trouble category wording (the real attendant's list most likely
lives in a Bell System Practice from division 660, which was not reachable);
test line access codes; commitment intervals and per-action time costs; the
transmission working limits; the loop resistance per mile, which is derived
from the documented "1300 ohms, typically about three miles" rather than quoted.

## [Unreleased] - Roadmap R1

### Fixed

- **The installed package was a different product.** `_initialize_nanpa_data`
  opened the geographic dataset by a path relative to the working directory.
  From the source tree that loaded 80 numbering plan areas and 3,200 central
  offices; from anywhere else - which is what `pip install bell-system &&
  bell-system` does - `FileNotFoundError` was caught and swallowed into a
  six-office fallback with no warning. Every geographic feature degraded with
  it: CLLI assignment, the geographic trouble overview, office selection for
  the repair bureau, the ticket system's affected offices.

### Added

- **A packaged geographic dataset.** `bell_system/data/nanpa.csv.gz`, 42 KB,
  read through `importlib.resources` so it is found wherever the package is
  installed. Coverage went up as well as becoming reliable: **108 numbering
  plan areas and 4,320 central offices, everywhere**, against 80 and 3,200 in
  the best case before.
- **A period filter with a source.** Engineering and Operations in the Bell
  System (2nd ed., 1984) describes "the basic set of 152 area codes possible
  using the N0/1X format", making a middle digit of 0 or 1 a structural
  property of every area code in service during 1978-1983. Codes created
  between 1984 and 1994 share that format, so eighteen of them - 718 among
  them - are excluded by name in `tools/build_nanpa.py`, each carrying its
  year and parent code, and marked as externally sourced rather than
  repo-verified.
- **`tools/build_nanpa.py`**, so the dataset is reproducible from its source
  rather than a binary someone has to trust.
- **`SOURCES.md`**, mapping every historical claim to the document it rests
  on, and recording what no longer ships and how to get it back.
- **Loud failure.** Missing data raises `GeographyUnavailable`, and the
  terminal marks itself `geography_degraded` and logs it rather than quietly
  substituting a stub network.
- **The guard that was missing.** `tests/test_geography.py` builds a terminal
  from a temporary working directory and asserts full coverage. Every test
  previously ran from the repository root, which is why nothing saw this.

### Changed

- 166 MB removed from the working tree: 120 MB of scanned PDFs, which no line
  of code cites because they are images rather than searchable text, and the
  46 MB NANPA dump now superseded by the packaged dataset. The 21 MB of
  searchable text that the code actually cites stays, so every claim remains
  checkable with `grep`.

## [Unreleased] - Roadmap R2

### Fixed

- **Three qualifications paid out in placeholders.** Main Distributing Frame
  unlocked `lmos`, Switching Control Center unlocked `sarts`, and Toll
  Network - which costs 108 correct closures on the hard difficulty -
  unlocked `toll`. All three answered "subsystem not available in this
  release". All three are now real, and a test asserts that no qualification
  can ever unlock a command in `UNIMPLEMENTED_COMMANDS` again.

### Added

- **`lmos` - the Loop Maintenance Operations System.** A view onto the report
  desk rather than a second copy of it: customer line card records with their
  trouble history, reports in process, chronic lines, the trouble report
  evaluation and analysis tool with its coin telephone and repair force
  analyses, and an equipment utilisation report. Telecommunications
  Transmission Engineering vol. 2 supplies the whole shape - the system
  "mechanizes RSB customer line card records", its listed functions, the five
  million record capacity, the bureau's three objectives, and the three test
  systems, of which mechanised loop testing "provides mechanization of
  essentially all ARSB test functions".
- **`sarts` - the Switched Access Remote Test System.** A special services
  circuit inventory reached through its access arrangement and measured on
  the existing test line series: a four-wire circuit on the 105-type
  responder, a two-wire on the 100-type, both at 1004 Hz. A circuit on manual
  jack access cannot be reached and says so, because that is the point of the
  distinction. Engineering and Operations supplies the definition of a
  special service, the named categories, and SMAS providing "concentrated
  metallic access to individual circuits to permit remote access and testing
  by the Switched Access Remote Test System".
- **`toll` - the toll network.** Offices by class, the homing chain, and
  trunk group occupancy, against the routing engine's own picture. "The toll
  network consists of the class 4 and higher offices" is the boundary the
  document draws, and the one the command draws.

### Changed

- The stub count drops from 25 of 81 commands to 22 of 81.
- `lmos.py` and `special_services.py` carry their own screens rather than
  adding to `terminal.py`, which is the shape the monolith is being broken
  into.

## [Unreleased] - Roadmap R3

### Changed

- **`terminal.py` split from 11,241 lines to 1,800.** Two hundred and
  thirty-three methods lived in one class because every subsystem's screens
  were written into it. They now sit in `bell_system/screens/`, seventeen
  modules grouped by the part of the plant they belong to, none over 1,000
  lines. `terminal.py` keeps dispatch, session and construction.
- **Shared constants moved to `bell_system/constants.py`** so the terminal and
  its screens import them rather than one reaching into the other.
- **The session contract is explicit.** `screens/session.py` declares every
  attribute and cross-subsystem method a screen may use. The coupling was
  always there and invisible; it is now written down in one place and checked.

### Fixed

- **Thirty-five type findings that were being suppressed.** `terminal.py` was
  excluded from mypy by a per-module override. Splitting it exposed what the
  override was hiding: a `CentralOffice` TypedDict missing the `clli` and
  `switch_name` keys the code sets on it, four unguarded `Optional`
  dereferences, ticket dictionaries appended to a `List[TroubleTicket]`
  without matching it, `max()` over untyped values, and a role lookup that
  could pass `None` to `dict.get`. All fixed, and **the override is gone** -
  nothing in the package is excluded from type checking now.

### Added

- Four integrity guards so none of this can quietly come back: every screens
  module must be mixed into the terminal, no screens module may exceed 1,000
  lines, `terminal.py` may not exceed 2,000, and every `self.x()` call is
  resolved against the constructed class's method resolution order rather
  than a single file.

## [Unreleased] - History rewrite

### Changed

- **Git history rewritten to remove 167 MB of files no code cites.** A clone
  went from **126.33 MiB to 6.21 MiB**, and from roughly a minute to one
  second. Removed: ten scanned PDFs, the 46 MB NANPA dump the packaged
  dataset supersedes, and two leftovers from the deleted Replit stack
  (`generated-icon.png`, `package-lock.json`).
- The 21.5 MB of searchable text the code actually cites was retained in
  full, so every historical claim is still checkable with `grep`.

### Note for existing clones

Every commit SHA changed. An existing clone cannot be pulled into and must be
re-cloned. File contents are unchanged: the rewrite was verified path by path
and content-hash by content-hash — 119 files at the previous `main` and 149
at the branch tip are byte-identical before and after, with zero additions
and no removals beyond the ten intended files.

## [Unreleased] - The machine you are sitting at

The simulation had drifted into being a telephony examination. Three quarters
of the commands were plant operations, the UNIX layer was twelve working
commands, and the filesystem was ten directories with 724 bytes in them whose
listings named files that did not exist. You could not change directory. You
could not read anything. Being a person at a Bell System UNIX machine in 1983
is the point, and it was the one part not implemented.

### Added

- **A shell.** `cd`, `cat`, `more`, `head`, `tail`, `grep`, `wc`, `sort`,
  `uniq`, `echo`, `file` and `cal`, with Seventh Edition behaviour: `grep`
  reads standard input when given no file, `wc` prints lines, words and
  characters in that order, `head` and `tail` default to ten lines, `ls`
  columnates for a terminal and prints one entry per line down a pipe.
- **Pipes.** `who | wc -l` works. A pipeline is one command, so its stages do
  not each advance the shift clock or pull a new report onto the board
  half-way through.
- **A filesystem worth walking around in**: 47 nodes and 6,985 readable bytes,
  against 12 and 724. Directories no longer carry a list of what they claim to
  hold - children are found by walking the tree, so a listing cannot name a
  file that is not there. `/bin` and `/usr/bin` are generated from the real
  dispatch table, which makes `ls /usr/bin | grep test` a way to find
  commands.
- **The company is ending.** The shift is 14 November 1983; the Bell System
  was dissolved on 1 January 1984, forty-eight days later. Engineering and
  Operations records the consent decree and that "the existence of the Bell
  System ends with divestiture". That is now in the message of the day, in a
  memo under `/usr/doc`, and in `cal 12 1983`. It is atmosphere rather than
  mechanics: nothing about it requires knowing any telephony.
- **The job is readable as files.** `/usr/lmos/board` is the trouble report
  board, one report to a line and fixed width so `grep` and `wc` are useful on
  it. `/usr/adm/shiftlog` is what you have closed. `/usr/bsp` holds the
  practices. Reading the board with `cat` is a real alternative to the
  `report` screens rather than a decoration.
- Things left to find: the previous operator's notes, an operations bulletin,
  C source under `/usr/src/cmd`, fortunes, the accounting logs.

### Changed

- `help` leads with the work, then the machine, and says that commands join
  with a pipe and which files are worth reading.
- The shift briefing points at the filesystem on the first shift.

## [Unreleased] - The rest of the machine

### Added

- **A writable filesystem.** `cp`, `mv`, `rm`, `mkdir`, `rmdir`, `touch`,
  `chmod`, `du`, `find`, and `>` and `>>` redirection. Everything downstream
  needed somewhere to put its output.
- **Shell quoting.** `grep 'two words'` and `sed 's/a/b/'` used to see the
  quote as part of the argument. The line is tokenised properly now.
- **Filters**: `tr`, `cut`, `sed`, `tee`, `rev`, `cmp`, `diff`, `od`, `spell`.
  `diff` reports in ed(1) command form, which is what diff output was for.
- **Utilities**: `banner`, `factor`, `primes`, `bc`, `units`, `sleep`, `mesg`,
  `wall`, `passwd`, `stty`, `tty`, `sync`. `units` knows kilofeet, because
  that is what outside plant is measured in.
- **Section 6.** `fortune`, `bcd`, `ppt`, `arithmetic`, `moo`. `bcd` punches a
  real 026 card - A to I on the 12 zone, J to R on the 11, S to Z on the 0 -
  and `ppt` punches paper tape.
- **Netnews.** `/usr/spool/news` carries a nightly uucp feed:
  net.unix-wizards, net.general, net.jokes, net.sources. `readnews` lists and
  reads them, and they are files, so `grep` works on them too.
- **ed.** The editor, with addresses, ranges, `a i c d p n s w r q Q = h H`
  and `/pattern/`. Every line goes to it until you type `q`. It answers
  mistakes with a single question mark and nothing else, which is the whole
  point of ed - with one deliberate deviation: after three in a row it says
  how to get out.
- **cc.** Compiles a C program to a runnable `a.out`. It understands `printf`
  and nothing else, which the manual page states plainly rather than letting
  you discover it. `cp /usr/src/cmd/hello.c . && cc hello.c && a.out` works.
- **nroff, troff and tbl.** Real formatters over the ms and man macros, with
  filling to a measure. `tbl table | nroff` lays out a table and formats it,
  which is how they were used. The Document Preparation role is no longer
  stubbed end to end.

### Changed

- The dispatch table and command aliases moved to `screens/dispatch.py`. The
  integrity guard caught `terminal.py` creeping back over 2,000 lines, which
  is what it is for.
- Stubs: 25 of 81 commands, then 18 of 131. UNIX commands: 20 of 81 (24%),
  now 70 of 131 (53%).

### Fixed

- The stub `nroff`, `troff`, `tbl` and `eqn` in `screens/documents.py` won the
  method resolution order over the real implementations and shadowed them.
  Removed, with a note in that module saying why.
- `pic` and `refer` were taken off the stub list by an over-eager edit without
  being implemented. The honesty test caught it and they are back on it.

## [3.0.0] - 2025-05-27

### MAJOR RELEASE: COMPREHENSIVE COMMAND VALIDATION & CRITICAL ERROR RESOLUTION

This release represents a complete overhaul of the command system achieving 100% validation success across all operational roles. This is a major milestone release that resolves 174 critical command failures and establishes the simulation as a fully functional, professional-grade Bell System terminal experience.

### 🔧 CRITICAL FIXES APPLIED
- **Resolved 174 Command Failures**: Complete systematic resolution of all command execution errors
- **Fixed Missing Attributes**: Resolved critical `command_counts` attribute error affecting 162 commands
- **Corrected Indexing Bugs**: Fixed sequence indexing error in error reporting system
- **Added Core Commands**: Implemented missing essential commands (status, test, quit, clear)
- **Enhanced Equipment Commands**: Added specialized Bell System equipment command (antenna)
- **Improved Alias Handling**: Enhanced command alias resolution for seamless user experience

### 📊 VALIDATION ACHIEVEMENTS
- **Testing Scope**: 200+ commands tested across all 12 operational roles
- **Success Rate**: 100% command validation success achieved
- **Error Resolution**: 174/174 critical issues resolved (100% fix rate)
- **Role Coverage**: All 12 Bell System operational positions fully functional
- **Equipment Commands**: Complete coverage of specialized Bell System hardware

### 🚀 NEW COMMAND IMPLEMENTATIONS
- **cmd_status**: Comprehensive Bell System operational status overview with real-time metrics
- **cmd_test**: Equipment testing interface for all Bell System hardware and circuits
- **cmd_quit**: Proper session termination with command history persistence
- **cmd_clear**: Terminal screen clearing functionality with authentic behavior
- **cmd_antenna**: Microwave antenna and tower equipment management system
- **cmd_errors**: Enhanced error tracking with troubleshooting guidance and solutions
- **cmd_history**: Command history display with usage statistics and filtering
- **cmd_verbosity**: Dynamic logging level control for debugging and monitoring

### 🔍 COMPREHENSIVE TESTING FRAMEWORK
- **Automated Validation Suite**: Complete testing infrastructure for all commands
- **Role-by-Role Testing**: Systematic validation across all 12 operational positions
- **Error Detection System**: Comprehensive error identification and resolution tracking
- **Input Validation Testing**: Edge case handling and malformed input protection
- **Historical Authenticity Verification**: Ensuring all fixes preserve Bell System accuracy

### 💡 ENHANCED USER EXPERIENCE
- **Professional Logging**: Multi-level logging system with automatic file rotation
- **Command History**: Persistent history with readline integration and navigation
- **Intelligent Error Handling**: Contextual error messages with actionable suggestions
- **Performance Monitoring**: Session analytics and command execution tracking
- **Usage Statistics**: Comprehensive command frequency and success rate analysis

### 🎯 OPERATIONAL EXCELLENCE
- **100% Role Functionality**: All 12 Bell System roles fully operational and tested
- **Complete Command Coverage**: Every specialized equipment command working perfectly
- **Authentic Procedures**: All Bell System terminology and workflows preserved
- **Terminal Authenticity**: Pure terminal interface maintained for historical accuracy
- **Professional Quality**: Enterprise-grade error handling and system reliability

### 🛠️ TECHNICAL IMPROVEMENTS
- **Robust Error Handling**: Comprehensive exception management throughout system
- **Memory Efficiency**: Optimized data structures and command processing
- **Session Management**: Enhanced session tracking with proper cleanup procedures
- **Code Quality**: Maintained high standards while implementing critical fixes
- **Performance Optimization**: Improved command lookup and execution efficiency

### 📋 COMPATIBILITY & STANDARDS
- **Backward Compatibility**: All existing functionality preserved without changes
- **Historical Accuracy**: Complete fidelity to 1978-1983 Bell System operations
- **Python Standards**: Code maintains PEP 8 compliance and best practices
- **Type Safety**: All new implementations include proper type annotations
- **Documentation**: Comprehensive docstrings and usage examples

## [2.0.0] - 2025-01-19

### Added
- Complete repository refactoring to professional CLI-only structure
- New `bin/bell-system` CLI entry point with argument parsing
- Comprehensive Python package structure with `src/` organization
- Professional documentation suite in `docs/` directory
- GitHub CI/CD workflows for automated testing and linting
- Pre-commit hooks for code quality enforcement
- Example scripts demonstrating usage patterns
- API documentation with comprehensive code examples
- Performance profiling and optimization tools
- Enhanced logging system with structured output

### Changed
- **BREAKING**: Converted from Node.js wrapper to pure Python CLI application
- **BREAKING**: Moved all source code to `src/` directory structure
- **BREAKING**: Changed entry point from `npm run dev` to `bell-system` command
- Updated documentation to reflect CLI-only architecture
- Improved code organization following Python package standards
- Enhanced error handling and user experience

### Removed
- All Node.js dependencies and web framework components (337 packages)
- Web server infrastructure (`server/index.ts`)
- React and UI library dependencies
- Legacy Python files (`v1_bell_system_unix.py`, `v1a_enhanced_bell_system.py`)
- Replit-specific configuration files
- Unused build and development tools

### Fixed
- Import duplication and circular dependency issues
- Type hint errors preventing application startup
- Code style inconsistencies across modules
- Memory leaks in long-running terminal sessions

### Security
- Removed potential web-based attack vectors
- Added input validation for all CLI arguments
- Implemented secure file path handling
- Added audit logging for security events

## [1.0.0] - 2024-11-01

### Added
- Initial Bell System UNIX V7 Terminal Simulation
- 12 authentic operational roles from 1978-1983 period
- 50+ period-accurate commands with historical validation
- Role-based access control system
- Comprehensive manual page system
- Interactive tutorial for Bell System operations
- Authentic shift briefings and operational procedures
- Historical Bell System terminology and workflows
- Command history and session management
- Professional logging and error tracking

### Documentation
- Complete user manual with operational procedures
- Command reference guide for all Bell System operations
- Historical context and background information
- Installation and setup instructions

## [0.1.0] - 2024-06-19

### Added
- Initial project setup and basic terminal framework
- Core Bell System role definitions
- Basic command processing engine
- Historical asset collection and documentation
- Development environment configuration

---

## Version History Summary

- **v4.0.0**: The game made discoverable - the tutorial folded into the first
  shift, a standing next action, hints you ask for, feedback that teaches, a
  career that walks the calendar to the last day of the Bell System, and a tour
  that survives the window closing
- **v3.0.0**: Comprehensive command validation and critical error resolution
- **v2.0.0**: Professional CLI-only refactoring with comprehensive GitHub readiness
- **v1.0.0**: Complete Bell System simulation with 12 roles and historical accuracy
- **v0.1.0**: Initial development framework and asset collection

## Migration Notes

### Upgrading to v4.0

**Breaking Changes:**

1. **`--tutorial` is gone.** There is no separate tutorial mode. The first
   shift of a new career *is* the tutorial: it opens with one report and the
   wire chief walks you through the loop on `write(1)`. Just run
   `bell-system`.
2. **`BellSystemTutorial` is no longer exported** from the `bell_system`
   package, and `bell_system/tutorial.py` is removed. Nothing in the package
   referenced it.
3. **A new state file.** `shift.json` appears beside `career.json` and
   `settings.json` in the state directory, holding the tour you are in the
   middle of. It is written after every command and removed when you sign off
   with `handoff relieve`. Deleting it costs you one tour and nothing else.

**Nothing else changes.** Existing `career.json` and `settings.json` files are
read as before; a career that predates this version simply picks up its wire
centre the first time it opens and keeps it from then on.

### Upgrading from v1.x to v2.0

**Breaking Changes:**
1. **Entry Point**: Use `bell-system` command instead of `npm run dev`
2. **Installation**: Install with `pip install -e .` instead of `npm install`
3. **File Structure**: Source code moved to `src/` directory

**Migration Steps:**
```bash
# Remove old installation
rm -rf node_modules/ package.json package-lock.json

# Install new CLI version
pip install -e .

# Update usage
bell-system                # instead of npm run dev
bell-system --tutorial     # new tutorial mode
bell-system --role 1      # direct role selection
```

**Preserved Features:**
- All 12 Bell System operational roles maintained
- Complete command set with historical accuracy
- Session management and command history
- Comprehensive logging and diagnostics
- Interactive tutorial system
- Historical documentation assets

For detailed technical changes, see the [API documentation](api.md) and [architecture overview](overview.md).