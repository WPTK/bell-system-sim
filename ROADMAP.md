# Feature Roadmap

A reevaluation of section 7 of `AUDIT_REPORT.md`, written after sections 1-6
were implemented and merged. The original roadmap was written against a
codebase that did not run. Most of it is now done; some of it was overtaken
by decisions made during the work; and the work itself surfaced problems the
audit could not have seen.

This document is the plan from here.

---

## Part 1 — Where the original roadmap stands

| | Original priority | Status |
|---|---|---|
| P0 | Resurrect what's built | **Done.** Dispatch table, docstring-swallowed imports, aliases, phantom methods, dead code. |
| P1 | Installable and honest | **Done.** src-layout packaging, one launcher, working `--role`, real test suite, restored CI. |
| P2 | Repo hygiene | **Half done.** Node/Replit stack deleted, `.DS_Store` and `logs/` untracked. `attached_assets/` was never moved — see R1. |
| P3 | Period clock and terminal fidelity | **Done differently.** Delivered as *settings* rather than impositions: a 1983 clock, bare Bourne prompt, ASCII-only output, all adjustable. 80-column wrap was deliberately rejected as anti-playability. Baud pacing is the one item not built — see R7. |
| P4 | Close the gameplay loop | **Done, and past the brief.** Diagnose/dispatch/verify, scored handoff, qualification gating, persistence — plus two difficulties, NPCs on four channels, and a working shift clock. |
| P5 | CLLI routing network | **Half done, and half broken.** CLLI coding, the toll routing engine and 80-NPA coverage all shipped. But the coverage only exists when the program is run from the repository root — see R1. Remote-office `connect` and RBOC theming not started — see R6. |
| P6 | Fault model and test equipment | **Done.** Ten fault conditions with real electrical signatures, mechanised loop testing, the far-end test line series, SF supervision. |
| P7 | Stretch | **Not started.** Still stretch — see R8. |

### What was deliberately dropped

* **80-column discipline.** Accuracy that costs playability on a modern
  terminal. The settings screen is the pattern for this class of decision:
  where the two conflict, make it the player's call, default to accurate,
  and mark the departure.
* **"Easter eggs and phreaking lore" as secrets.** 2600 Hz shipped, but as
  craft-side plant: supervision states on the test board, CAROT printing
  exceptions, seizure as a stage of proving a trunk. Documented work, not a
  hunt for hidden content. Test lines belong in the same frame — see R5.

---

## Part 2 — What the audit could not see

Four findings from building the thing. The first is serious.

### The installed product is not the product we tested

`_initialize_nanpa_data` opens `attached_assets/full_dataset_csv.csv` — a
path relative to the current working directory (`terminal.py:2171`). Run from
the repository root it loads 80 numbering plan areas and 3,200 central
offices. Run from anywhere else, which is what `pip install bell-system &&
bell-system` does, `FileNotFoundError` is caught and swallowed into a
six-office fallback.

```
in the repo:   80 NPAs, 3,200 central offices
installed:      6 NPAs,     6 central offices
```

A 533-fold silent degradation. Everything geographic degrades with it: CLLI
assignment, the geographic trouble overview, office selection for the repair
bureau, the ticket system's affected offices. No warning is printed. No test
catches it, because every test runs from the repository root.

This is the single most important item on this roadmap, and it makes the
unfinished half of P2 urgent rather than cosmetic.

### The repository is 126 MiB of pack for 1 MiB of code

`attached_assets/` is 187 MB on disk and in git history: a 46 MB CSV and
about 110 MB of scanned PDFs. Every clone pays it.

The fix is the same as the one above. A distilled dataset — the fields the
simulation actually reads, capped per NPA the way the loader already caps —
measures **489 KB raw, 105 KB gzipped, and covers 279 NPAs**. That is 3.5×
the coverage of today's best case, at a quarter of a percent of the size, in
a file that ships inside the package where the code can always find it.

### `terminal.py` is 11,241 lines

The audit measured it when it was 8,500 and did not raise it, because at the
time the file did not run at all. It runs now, and it has grown. The newer
subsystems — `reports`, `loop_testing`, `npc`, `progression`, `routing` —
were built as separate modules and stayed 400-600 lines each, which is the
proof that the pattern works. The monolith is 57% of the package and holds
81 command handlers.

### A quarter of the command surface is honest stubs, and three of them are progression rewards

25 of 81 commands answer with "subsystem not available in this release." That
honesty was the right call during the audit. It is now the largest gap
between what the product advertises and what it does.

Two specifics make it worse than a flat 31%:

* **Document Preparation Specialist is 7 of 7 stubbed.** Select role 12 and
  every command it lists is a placeholder.
* **Three qualifications pay out in stubs.** `frame` unlocks `lmos`, `scc`
  unlocks `sarts`, `toll` unlocks `toll`. On the hard difficulty the toll
  sign-off costs 108 correct closures and one of its three rewards is a
  "not available" screen.

---

## Part 3 — The roadmap

Ordered by what is most broken for a real user, not by what is most
interesting to build.

### R1 — Make the installed product the product · **done**

- [x] Distil `full_dataset_csv.csv` to the fields the simulation reads and
      ship it inside `bell_system/data/` (489 KB, 279 NPAs)
- [x] Load it with `importlib.resources`, not a relative path
- [x] Fail loudly, not silently: if the data is missing, say so
- [x] Add a test that constructs a terminal from a temporary working
      directory and asserts full coverage — the guard that was missing
- [x] Removed from the working tree **and from history** — a clone went
      from 126.33 MiB to 6.21 MiB; publish it
      as a release asset or a documented separate download
- [x] Keep a short `SOURCES.md` mapping every historical claim to its
      document, so the provenance survives the files leaving the repo

Fixes a silent 533× degradation, *raises* coverage from 80 NPAs to 279, and
takes the clone from 126 MiB to roughly 1 MiB. One change, three wins.

### R2 — Nothing gates progression behind a stub · **done**

- [x] Build `lmos`, `sarts` and `toll`, or move them out of the
      qualification unlock lists — all three built
- [x] Add a test asserting that no `QUALIFICATIONS` entry unlocks a command
      in `UNIMPLEMENTED_COMMANDS`

`lmos` is the natural one to build first: the Loop Maintenance Operations
System was the real front end for exactly the trouble reports the simulation
now models, so it is a view onto state that already exists rather than new
state.

### R3 — Break up `terminal.py` · **done**

- [x] Extract by subsystem into modules of the shape `reports.py` already
      has: state and rules in the module, rendering in the terminal
- [x] Target: no module over 1,000 lines; `terminal.py` becomes dispatch,
      session and rendering
- [x] Cuts made, roughly by size: TNDS, TSPS, traffic, trunks and
      switching, carrier, tickets, directory and operator

Do this before R4, not after. Adding twenty subsystems to an 11,000-line file
is how it got to 11,000 lines.

### R4 — Finish or retire the stubs · **done**

`UNIMPLEMENTED_COMMANDS` started at eighteen names and is now empty. Every
command on the machine does something.

- [x] Role 12 built rather than dropped: `nroff`, `troff`, `tbl` and `eqn`,
      then `pic` and `refer` as well. `refer` fills citations from a
      bibliography of real papers whose page ranges were checked
- [x] Fourteen implemented, four removed. `pwb` and `rje` were removed
      because there was nothing behind the name — PWB was a system, not a
      program, and its remote job entry was `send(1)` and `rjestat(1)`,
      which the machine now has. `analysis` and `netdata` were command names
      with no referent that duplicated `tnds` subcommands
- [x] Four of the fourteen turned out to have real data already in the
      simulation behind them: `trace` is the routing engine printed one leg
      at a time, `capacity` reads the trunk groups, `coer` reads the offices
      and the board, `custdb` prints the card LMOS already holds. Tests
      check the join, not just the output
- [x] `_subsystem_unavailable()` removed with its last caller. The empty
      set stays, because it is where the next honest stub goes

### R4a — The Seventh Edition toolkit · **done**

Twenty-six commands added on the UNIX side, because the fun of this is
using UNIX at work in 1983 and the toolkit was half there.

- [x] Filters: `pr`, `comm`, `join`, `look`, `split`, `sum`, `dd`, `expr`,
      `basename`, `true`, `false`
- [x] Deferred work: `at` against the shift clock with jobs spooled under
      `/usr/spool/at`, `make` against a real makefile, `nohup`, `nice`,
      `time`, `kill`
- [x] The network: `uuname`, `uulog`, `uux`, and `su` writing to the
      `/usr/adm/sulog` that was already on the machine
- [x] `paste`, `dirname` and `nl` deliberately absent: PWB and System III,
      after the period
- [x] Two shell bugs found on the way: `|` and `>` were searched for in the
      raw line, so `grep '|'` started a pipeline and `expr 5 '>' 3` wrote a
      file. A shell decides punctuation before anything else
- [x] `;` as a command separator

### R5 — Deepen the loop with what the new model makes possible · **done**

- [x] **Cable-level faults.** Exchange cable is built in binder groups of
      twenty-five pairs, each in a coloured binder following the same
      25-pair colour code as the pairs inside it, twenty-four groups to six
      hundred pairs. Water is a binder group fault, so a wet pair now lands
      in a group that is already wet and a dry fault deliberately does not.
      One splicer trip repairs the sheath and every pair in it, and names
      the binder and its colour so the splicer could find it. A second trip
      to a sheath already opened is refused. `lmos cable` groups the board
      by binder group; the same information has always been in
      `/usr/lmos/board`, where `sort` and `uniq` find it too.
- [x] **COSMOS work orders that matter.** `cosmos jumper` invented a
      vertical, a horizontal and a jumper length on every call, so two
      looks at one line disagreed. It reads the assignment record now, and
      a central office fault has a real defect on the frame — a jumper on
      the wrong horizontal, a protector left operated, a leg off the
      terminal — visible in the record for two desk minutes against four
      for a measurement and an hour for a trip. Service orders raised by
      `provision` appear on the frame's list.
- [x] **Named field forces.** Five people with real Bell craft titles, each
      standing somewhere. The nearest free one goes, the drive is charged
      against the commitment, and when they are all out the report waits.
      `force` shows who is where. The wrong-dispatch penalty names the
      person who drove out to the wrong place.
- [x] **Test lines as craft tools.** ANAC, the 102-type milliwatt supply,
      the 100-type quiet termination, loop around and ringback, reachable
      through `testline` against a line rather than a trunk. Aural rather
      than electrical, so they hear things a loss measurement passes — and
      none of them finds everything, which a good answer says out loud.
- [x] **Weather on the shift clock.** A shift gets a regime and walks the
      conditions an hour at a time toward it; an unrepaired binder group
      takes another pair faster the harder it is raining. What is not
      claimed, and the module says so: the actual weather over northern New
      Jersey on 14 November 1983, whose daily climate records were not
      reachable from here.
- [x] **Revisit the index penalties.** `tools/index_calibration.py` plays a
      few hundred shifts per setting with five players who fail in one way
      each. The 55/35/20 apportionment holds and stays. Two findings acted
      on: the forgiving setting was uninformative rather than forgiving (an
      ordinary player scored EXCELLENT in 89 shifts out of 100 at a 0.4
      multiplier, now 0.7), and the index is a rate rather than a volume —
      a tour that closes five reports perfectly outscores one that closes
      thirty-two with two mistakes. That is correct for a repair index and
      is now said out loud, with closed and carried printed beside it.

### R5a — What is different about each position · **done**

The answer used to be: the help text, one qualification, and a home
directory that did not exist for eleven of the twelve.

- [x] Twelve homes, each with a `.profile` that opens the desk on its own
      work and a file left by whoever sat there last
- [x] The role logins are in `/etc/passwd`
- [x] **Different work.** One table, `data/positions.py`, read at seams that
      already existed. `fault_bias` is a multiplier and never a filter — a
      switching desk sees false cross and ground go from 9.7 to 19.9 per
      cent over six thousand draws, and every fault stays reachable at
      every desk. Board depth is the only lever on volume: measuring showed
      the board runs saturated, so the arrival rate does nothing and
      scaling it only removed tickets. Ticket categories are a preference,
      not a filter.
- [x] **Different people.** Forty-eight lines, four per desk, added to the
      shared pool rather than replacing it — a docprep desk still hears
      CAROT at three in the morning, it just also hears Petrak on the
      difference between an addendum and a revision. Four craft added,
      three of whom already existed elsewhere in the tree with no voice.
- [x] **Different measure.** NSPMP measures a switching machine and eight
      of these desks are not one, so the table names a component where one
      fits and says plainly that none covers the rest. A tour account in
      the handoff, read from counters that already existed — a tally and
      not a second score, and it says so.

Found on the way: `Switchroom` was silently discarding 40 per cent of every
ambient message it generated, and 99.7 per cent of the older hands' advice,
because the dedup window was larger than the advice pool. Fixed separately.

### R6 — More than one office · **done**

- [x] `connect <clli>` reaches another building from the console — by code,
      by place, or by its number in the listing. Each office has its own
      alarms and its own health, generated from its CLLI so two looks
      agree, with identifiers of its own so acknowledging one building's
      alarm does not touch another's. The trouble board deliberately does
      not travel: a loop lands on one frame, which is why a control centre
      could watch eleven offices and a repair bureau could not.
- [x] Per-operating-company character — **not** equipment mix, which
      turned out not to be gettable from any source reachable here.
      `company(1)` gives the twenty-one operating companies and the seven
      regional holding companies they pass to on 1 January 1984, which is
      documented, is the better answer, and is the one thing everybody in
      those buildings actually knew about their own company that autumn.
      Three of the seven groupings are quoted from Engineering and
      Operations; the other four are marked `?` as externally sourced.
- [x] The SCC assigns you an office for the tour, picking the worst
      building on the console that is not the one you are sitting in.
      `connect` is now what the SCC sign-off unlocks — it previously paid
      out in two commands that both stayed in your own building.

### R7 — Fidelity settings still on the table · **done**

- [x] `display.pacing` — output paced at a terminal speed: 110 for a Model
      33, 300 for the Model 43 this position is strapped for, 1200 for a
      later CRT, or off. The frame is eleven bits at 110 (two stop bits,
      because a mechanical printer needed them) and ten above it, which is
      why 110 gives ten characters a second and 300 gives thirty. Default
      is 300, because accuracy is the default; a pipe is never paced and
      Ctrl-C stops a listing.
- [x] A login sequence: getty banner, `login:`, a password only when
      `/etc/passwd` carries one, `/etc/motd`, then the shell reads
      `.profile`. root has a password and is refused; the twelve craft
      positions do not, because the machine is in a locked building.
- [x] Real filesystem exploration: `cat`, `cd`, `grep`, `more`, `head`, `wc`
      and the rest. The tree is 114 nodes, writable, with a dictionary, a
      bibliography, a netnews spool and twelve home directories.

### R8 — Stretch

- [x] **Tone synthesis.** `tone(1)` renders the Precise Tone Plan, MF
      address pulsing, Touch-Tone and 2600 Hz supervision to wave files
      through the standard library. Nothing invents a frequency: every
      value comes from `data/signaling.py`, and the relative levels are
      exact — busy really does render eleven dB below dial tone, because
      it is. `-n` normalises for listening, which changes the file and not
      the table. Busy and reorder are the same two frequencies at
      different rates, which is the distinction a craftsperson made by ear
      and cannot be read off a page.
- [x] **A second era**, for the network. Already substantially built: the
      office generator reads each system's first-service year, so 1955
      gives step-by-step and crossbar with no ESS anywhere, and 1971 gives
      the first two. `era(1)` reports what the date produces and, when the
      epoch is moved, says plainly that the writing did not move with it.
- [ ] **A second era, for the fiction.** The plant follows the date; the
      message of the day, the divestiture memo and the netnews spool do
      not. That is a content job rather than an engine one, and it is
      substantial: the divestiture framing is the emotional centre of the
      game, so a second era needs its own centre rather than a date swap.
- [ ] **Multi-user: not built, deliberately.** A shared board over sockets
      is a large build — concurrency, a protocol, persistence, session
      recovery — and the payoff for a single-player period simulator is
      unclear. The order wire between real people is the appealing half;
      the shared board is the expensive half and the one that would make
      every existing test conditional on a network. Recorded here as
      considered and declined rather than left looking unfinished.

---

## Working rules carried forward

The four that held through sections 1-6 and should hold here:

1. **Provenance or admission.** Every historical value is repo-verified,
   externally sourced, or explicitly marked as the simulation's own. Gaps get
   recorded in the source, not filled with plausible invention.
2. **Accuracy by default, playability by setting.** Where the two conflict,
   make it the player's call and mark the departure.
3. **Say what is not built.** A stub that admits it beats a placeholder that
   reads like real output.
4. **A test for every bug found.** Especially the silent ones — R1 exists
   because there was no test that ran from another directory.
