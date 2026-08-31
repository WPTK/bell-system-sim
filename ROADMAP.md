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

### R5 — Deepen the loop with what the new model makes possible · weeks

The report engine, the fault vocabulary and the frame state can now support
work the old codebase could not have:

- [ ] **Cable-level faults.** `WET` is documented as affecting many pairs in
      one sheath and the fault data says so, but the generator still assigns
      faults one line at a time. Wet cable should arrive as six reports off
      one cable, rewarding the craftsperson who notices before dispatching
      six trips.
- [ ] **COSMOS work orders that matter.** Frame assignment already exists;
      wire it to the reports so a `CO_EQUIP` fault can be a bad
      cross-connect you find on the frame.
- [ ] **Named field forces.** Dispatch goes to a person with a location and
      a travel time rather than to a category.
- [ ] **Test lines as craft tools.** ANAC, loop-arounds and milliwatt
      supplies, documented in the manual pages like everything else, usable
      to verify a line before you close it.
- [ ] **Weather on the shift clock.** Rain is the documented cause of wet
      cable getting worse. The clock exists; the fault exists; connect them.
- [ ] **Revisit the index penalties** once real play data exists. The current
      apportionment (55/35/20) is the simulation's own and untested against
      how the loop actually plays over many shifts.

### R5a — What is different about each position · **started**

The answer used to be: the help text, one qualification, and a home
directory that did not exist for eleven of the twelve.

- [x] Twelve homes, each with a `.profile` that opens the desk on its own
      work and a file left by whoever sat there last. That file is where a
      good deal of what you need to know about the job actually lives
- [x] The role logins are in `/etc/passwd`
- [ ] **Different work, not just a different opening.** The board is the
      same twelve ways. A radio position should be handed radio troubles, a
      special services position should be handed circuits. The report
      generator already knows about fault categories; the positions do not
      read them
- [ ] **Different people talking to you.** The order wire and the NPC
      chatter are the same regardless of desk. A TSPS operator should hear
      from operators
- [ ] **Different measure of a good tour.** The repair index is a repair
      measure. A planning desk is not judged on commitments met

### R6 — More than one office · weeks

The unfinished half of the original P5:

- [ ] `connect <clli>` to work a remote office from the switching control
      centre, which is what the SCC qualification is supposed to mean
- [ ] Per-operating-company character — Pacific Bell, Illinois Bell,
      Southern Bell — drawn from documented differences in equipment mix and
      practice, not invented flavour
- [ ] The SCC assigning you an office for the shift

### R7 — Fidelity settings still on the table · days

- [ ] `display.pacing` — optional baud-rate output pacing (110 for a Model
      33, 300 for a Model 43, off). The last unbuilt P3 item, and it belongs
      as a setting rather than a default
- [ ] A login sequence in front of the role picker — the `login:` and
      `Password:` prompts and the connect banner, honouring the same
      setting pattern. Distinct from the `.profile` below, which is what
      the shell does *after* you are in
- [x] Real filesystem exploration: `cat`, `cd`, `grep`, `more`, `head`, `wc`
      and the rest. The tree is now 114 nodes, writable, with a dictionary,
      a bibliography, a netnews spool and twelve home directories
- [x] A login sequence of the right kind: selecting a position runs the
      `.profile` in its home, the way `login(1)` did, so each desk opens on
      its own work

### R8 — Stretch

- [ ] Tone synthesis: MF, DTMF and SF rendered as audio through the standard
      library's `wave`, or a browser front end with Web Audio
- [ ] Multi-user: a shared board over sockets, order wire between real people
- [ ] A second era: the same engine at 1955 or 1995 is a different network,
      and the switching data already carries service dates

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
