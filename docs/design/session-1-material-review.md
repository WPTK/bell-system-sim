# Session 1: Material and Design Review

Audit of `WPTK/bell-system-sim` v4.0.0, for the gamification plan.
Scope: the written material, the data files, the design intent. Not run, not linted. Where a claim about
behaviour comes from a docstring and not from play, it says so. S2 owns the playtest.

Page references to *Engineering and Operations in the Bell System*, 2nd ed. (E&O) use the printed page.
PDF page = printed page + 17.

---

## 0. Result

The game has one real strength and one real hole.

**Strength.** The fiction is honest and specific. A UNIX box that is also the repair bureau, a wire chief who
signs your qualifications, twelve position notes that teach real craft in a tired voice, and a failure message
that quotes your own readings back at you. The tone is the product. Nobody else has it.

**Hole.** The loop is four commands and one of them (`mlt`) hands over the answer. In the default mode there is no
decision to make. The story (48 days, the memo, the strike, the marker that is slow on the third trial) sits in
static files and does not move as the tours pass. The calendar counts down but nothing *happens* on it.

Five findings that matter most:

1. **The default mode removes the puzzle.** `mlt` names the fault and the crew. The code's own docstring says it was
   right 60 times out of 60. The first tour teaches "it is not a riddle". The player learns the job before learning
   it is interesting. (P1)
2. **Qualification unlocks screens, not verbs.** The five sign-offs after Loop and Station open 16 commands, most
   of which print status and do not change the board. The reward for progress is more reading. (P1)
3. **The career is 13 identical tours.** Only board depth and weather escalate. The memo, the strike, Thanksgiving,
   Christmas and the last day have no scheduled beats, and the 4-day stride steps over both holidays. (P1)
4. **The best story hooks have no payoff.** Marker 2 and its sequence relay, the RSA's failed `su root` at 03:47,
   Sandoval, the predecessor Alvarez. The divestiture memo promises an audit of closed dispositions; nothing in the
   last tour collects on it. (P1/P2)
5. **The docs describe a different game.** `--tutorial`, `tutorial.py`, a 2.0 manual, seven commands that do not
   exist. The first impression of anyone who reads `docs/` is wrong. (P1, cheap)

---

## 1. System and lore inventory

### 1.1 Mechanics and how each reaches the player

"Reaches" means the surface the player meets it on. "Weight" is my read of how much play it carries today.

| Mechanic | Where | Reaches the player through | Weight |
| --- | --- | --- | --- |
| Trouble report with hidden fault | `reports.py`, `data/trouble.py` | `report`, `report show`, `report callback` | **Core.** 10 faults, 3 frame defects, customer wording is the sim's own (`REPORT_SYMPTOMS`) |
| Commitment clock | `reports.py`, `clock.py` | Board sort order, "past commitment", `Next:` line | **Core.** Elapsed time, separate from your working day. Good idea, easy to miss |
| MLT | `loop_testing.py`, `screens/testing.py` | `mlt N` | **Core.** Real physics (0.083 uF/mile, 1300 ohm limit). Fun mode appends a TEST RESULT that names the answer |
| Dispatch and field force | `field.py`, `screens/dispatch.py` | `report dispatch N force`, `report forces`, order wire calls | **Core.** Five named crews, wrong force costs 45 min. Best "other people" system in the game |
| Disposition 5 / 8, repeat reports | `reports.py`, `progression.py` | `report close N 5 FAULT` / `8`, callbacks, `report closed` | **Core.** The wrong-close debrief is the best feedback in the game |
| Service index | `progression.py` | Board footer, `qual`, `qual index`, handoff | Core. A rate, not a volume; the docstring admits five perfect closes score 100 |
| Wet cable as sheath fault | `cable.py`, `/usr/lmos/cable` | Several reports off one cable; `cat /usr/lmos/cable`; Okafor on the order wire | **Best cross-report puzzle.** The only one |
| Weather and rain | `weather.py`, `npc.weather` | Rjohnson on write(1); more wet reports | Good, tied to a real cause |
| Regulars | `data/regulars.py` | 18% of new reports; `custdb` history | 4 lines. Good notes, no arc |
| LMOS / TREAT views, frame and COSMOS | `lmos.py`, `screens/frame.py` | `lmos`, `cosmos` (Main Distributing Frame sign-off) | A read-only view of what the desk already holds, plus frame defects for CO_EQUIP. First sign-off with real content |
| Qualification (6 levels) | `progression.py` | `qual`, Halloran's sign-off message, "not signed off" refusals | Core gate. See §3 |
| Difficulty (fun / craft) | `progression.py` | `set game.difficulty` | Two knobs only: scoring forgiveness and interruption rate |
| Career calendar | `clock.py`, `screens/turnover.py` | `shift`, `handoff`, `handoff relieve`, "N days to divestiture" | 13 tours, 4 days apart, last pulled onto 31 Dec |
| Last tour | `screens/turnover.py`, `npc.last_word` | Career close, index trend, Halloran's goodbye | Lands well, but there is no audit and no consequence |
| 12 positions | `data/positions.py`, `data/homes.py` | Login menu, `help` section, home dir notes, voices | A mix on the same board. See §1.3 |
| Switching / ESS / crossbar / 3A | `screens/plant.py`, `switching.py`, `data/switching.py` | `switch`, `alarm`, `crossbar`, `3a`, `5ess` | Mostly status screens (hypothesis from docstrings; S2 to confirm) |
| Trunks, routing, test calls | `routing.py`, `screens/trunks.py` | `trunk`, `routing`, `testcall`, `testboard supervision` | Real stages (seize, wink, KP/ST, route advance). Rich but off the main loop |
| Test lines (100/102/105, ROTL, balance) | `loop_testing.py`, `data/testlines.py` | `testline` | Rich, off the loop |
| CAROT | `npc.py` teletype, `screens/trunks.py` | Teletype interruptions | Atmosphere only; exceptions require no decision |
| SARTS / special services | `special_services.py`, `screens/remote.py` | `sarts`, `connect` | Best note in the game (`sarts` circuits.notes); mechanics thin |
| SCC and remote offices | `screens/remote.py`, `npc.office_assignment` | `connect CLLI`, Petrak on the order wire | The one qualification that adds a verb |
| Tickets and shift events | `screens/tickets.py`, `ticket_generation.py`, `data/shift_events.py` | `events`, `ticket`, order wire | A second work queue. Generic. See §3 |
| NPC channels (write, mail, order wire, TTY) | `npc.py` | Interruptions at 6% of commands (fun) or 22% (craft) | Period-correct, well voiced, small pool |
| Hints | `data/hints.py`, `screens/guidance.py`, `npc._HINTS` | `hint`, `help`, `report next`, `Next:` line, first-tour nudges | **Seven overlapping channels** for a four-command loop |
| UNIX toolkit | `screens/shell.py`, `unix.py`, `filters.py`, `editor.py`, `docprep.py` | Any shell command; `training unix` | Remarkably complete (ed, cc, nroff, tbl, pic). A game inside the game |
| Games and toys | `screens/games.py` | `moo`, `bcd`, `ppt`, `fortune`, `tone` | Moo has a payoff (Okafor); the rest are texture |
| Geography, CLLI, NANPA, companies | `data/clli.py`, `geography.py`, `companies.py` | Office assignment, `clli`, `company` | Deep, accurate, mostly invisible |
| Persistence | `save.py`, `progression.py` | Tour survives the window | Good. Quiet retention hook |

Counts: 159 registered commands and 159 man pages. About 61 ambient NPC messages across the whole career
(13 shared, 4 per position × 12, 7 untested-report hints). 8 shift-event slots drawn from about 12 candidates.

### 1.2 Lore inventory (what the player can find, and what it pays off)

| Lore | Where | Reaches the player | Payoff |
| --- | --- | --- | --- |
| Wire-chief walkthrough | `screens/guidance.py` `FIRST_TOUR` | 5 write(1) messages on the first tour | Complete, then silent |
| MOTD | `filesystem.py` | Login | Sets divestiture, names `hint`, `training`, games |
| `/usr/doc/divestiture` memo | `filesystem.py:140` | `cat`; sysop notes say "read it first" | **Unpaid.** Says open reports pass "with your name on them" and dispositions "are audited after transfer". Nothing audits |
| `/usr/doc/bulletin` (83-114) | `filesystem.py:187` | `cat` | A five-line tutorial in costume; good. Static |
| 12 position notes | `data/homes.py` | `ls` in your home | **Best writing in the repo.** Teaching, not decorating (wet cable, "records are not the plant", "nobody owns the circuit") |
| `rjohnson/marker.notes` + 4 other mentions of Marker 2 | `filesystem.py:1493`, `npc.py`, `homes.py` | Notes, chatter, aisle notes | **Unpaid.** "If it ever fails outright the trouble is in the sequence relay." It never fails |
| `/usr/adm/sulog` (locked) | `filesystem.py:261` | Refused read; Halloran opens it with the 3rd sign-off; your own `su` attempts appear | Half-paid. Contains `mreyes-root` failing at 03:47 and a BADSU at 07:52 on the day. Nobody explains it |
| Netnews (14 articles, 8 groups) | `filesystem.py:1118-1400` | `readnews` | Strong: the August strike, the 1956/1982 decrees, uucp, RFC 850. Static, same on tour 13 as tour 1 |
| `moo`, `moo.scores`, Okafor's grudge | `games.py`, `npc.moo_beaten` | Games, news, scoreboard | **Paid.** The model for every other thread |
| Cadence puzzle (busy vs reorder) | `data/signaling.py`, `tone` | A report whose answer is a sound | Paid, and unique |
| Regulars' cards | `data/regulars.py` | `custdb` | Notes are good. Faults repeat; the story does not advance |
| UUCP log, messages, passwd, group | `filesystem.py` | `cat` | Texture; a few clues (pwba, ihnp4) |
| C sources, makefile, papers, fortunes | `filesystem.py` | `cat`, `cc`, `make` | Teaching, texture |
| `training unix` (BSP 000-100-000) | `data/primer.py` | `training unix` | Excellent voice. UNIX only |

### 1.3 The twelve positions

From `data/positions.py`. Every desk works the same board, the same ten faults and the same two close codes.
What differs is the mix, the people who talk to you, and a note.

| # | Desk | Board share | Fault bias | Voices | Note by |
| ---: | --- | ---: | --- | --- | --- |
| 1 | sysop | 0.42 | none | adm, Nakamura | R. Alvarez (a real predecessor) |
| 2 | switch | 0.50 | FCG ×3, CO_EQUIP ×2.5 | Johnson, Halloran | Nakamura |
| 3 | field | 0.72 | WET ×2.5, OPEN, GROUND | Okafor, Finch, Reyes | Reyes |
| 4 | noc | 0.28 | none | Petrak, CAROT | Halloran |
| 5 | tsps | 0.62 | ROH ×3, NONE, SHORT | Haverty, Reyes | Petrak |
| 6 | dba | 0.42 | CO_EQUIP ×3, FCG | Okafor, Halloran | Okafor |
| 7 | netplan | 0.25 | none | Halloran, Nakamura | Halloran |
| 8 | custserv | 0.78 | NONE, ROH | Reyes, Haverty | Reyes |
| 9 | radio | 0.30 | none | Nakamura, Vasquez | Vasquez |
| 10 | tnds | 0.30 | none | CAROT, Petrak | Nakamura |
| 11 | sarts | 0.40 | FEMF, CROSS | Vasquez, Nakamura | Johnson |
| 12 | docprep | 0.35 | none | Petrak, adm | (formatting note) |

Read: five desks have no fault bias and board share under 0.4. Their texture is chatter and a note, and 8 of 12
have no performance-plan component (`nspmp=None`), so the service index means little to them. Three or four
fantasies are real (repair desk, office/switching, special services, NOC). The rest are skins.

### 1.4 The three things you flagged

| Claim | Verdict | Evidence |
| --- | --- | --- |
| `docs/overview.md` describes `tutorial.py` and `--tutorial` | **Confirmed absent.** Neither exists. `cli.py` has `--role`, `--simple`, `--version` only. `guidance.py` says outright there is no tutorial mode | `overview.md:14,18,36,86,150`; `faq.md:28`; `manual.txt:7-8`; `build_parser()` |
| `docs/manual.txt` is still 2.0 with the old catalogue | **Confirmed**, and worse: `command_reference.txt` is headed "Version 2.0 - November 2024". The old bracket-style catalogue lists **seven commands that do not exist**: `analysis`, `circuits`, `forecast`, `netdata`, `pwb`, `rje`, `testing`. The newer repair-bureau sections (lines ~340-540) are accurate and good | `manual.txt:655`; dispatch table check |
| `shift_events.py` is invented boilerplate | **Confirmed, and its own docstring says so.** Fixed IDs (EV-8001...), identical base events every tour, the Pentagon line, "TH-3 path NYC-WAS", a 5ESS cutover, a NYC maintenance window, for a desk in Jersey City. Ice-storm event repeats on every December tour. Nothing in it connects to the board, the memo or the calendar | `data/shift_events.py` |

One more drift: `SOURCES.md` calls `attached_assets/` plain text. Several files are archive.org HTML pages with
about 2,950 lines of page chrome before the text. Greppable, but not what it says.

---

## 2. Cognitive load and onboarding

### 2.1 The first five minutes, as written

1. `bell-system`: a login with a 12-way choice of job (`?` lists them). **The first decision is the least
   informed one.** The README's headline says "you are at a repair test desk". The menu says Document Preparation
   Specialist is an option. Same board either way.
2. MOTD: 20 lines. Divestiture notice, then `hint`, `training`, games, a scoreboard reference. Good voice, but six
   pointers before the first report.
3. One report, rest of the board held back. `report` makes Halloran write: "Type 'report'. It tells you what to do
   next along the bottom."
4. `mlt 1`: "Read the bottom of that. TEST RESULT tells you what the fault is... It is not a riddle."
5. Dispatch. Then **wait** for the crew to call in.
6. `report close 1 5 FAULT`. Halloran: "That is the job. The rest of the board is coming."

### 2.2 Judgment

**What works.**
- One function (`next_action`) feeds the standing prompt, the top of `help`, `hint` and `report next`. They cannot
  disagree. Good engineering for onboarding.
- Halloran is the right voice. He does not say "STEP 1 OF 7". Five messages, then he leaves. That is the
  "colleague, not tutorial" the code comment promises.
- Every refusal names a way out (`dead_end`). Players do not stall on "command not found".
- `hint` is three people at three depths (Vasquez nudges, Halloran points at a file, Halloran says it). It costs
  one shift minute, no score. Right call. The `EXHAUSTED` line is honest.
- `training unix` is the single best piece of diegetic teaching: a mandatory annual refresher, "slightly weary
  about itself". Keep that voice everywhere.
- The wrong-close debrief quotes the player's own numbers. This teaches telephony better than any manual.

**What does not.**
- **No puzzle in the first five minutes.** The chief tells you the answer is printed at the bottom. The report
  has no customer, no story, and no gap between what the customer said and what is on the pair. That gap is the
  premise of the game ("nothing on it but what the customer said") and the first report skips it.
- **Dead time after dispatch.** The first tour holds the board at one report. After dispatch the `wait` hint is
  "Wait. Work something else... or go and get a coffee." There is nothing else on the board. How long this lasts in
  real seconds is for S2 to time. If it is more than about 60 seconds it is the worst moment in the game.
- **300 baud by default.** `display.pacing` defaults to `300`: character by character, one extra delay per
  newline (`terminal.py:1245-1258`). A full MLT block runs well over 30 seconds at 30 cps (my arithmetic, not
  timed). Ctrl-C cuts it. It is correct and charming, and it means the player waits on their very first reading.
  Accuracy is the right default for a veteran and the wrong one for minute three.
- **Seven help channels.** First-tour nudges, `Next:` after commands, `Meanwhile:` on refusals, `help`'s WHAT TO
  DO NOW block, `hint` (3 levels), `report next`, and ambient `_HINTS` from NPCs. For a four-command loop.
  `Next: ... 'mlt 1'` is the game talking out of costume, in a UNIX V7 shell. It is switchable
  (`game.prompts off`) but on by default.
- **`mlt` removes the reason to learn.** In fun mode the numbers never matter. In craft mode they are the whole
  game. There is nothing in between, and no path from one to the other except flipping a setting.
- **The documents contradict it.** A new player who reads `docs/manual.txt` meets 2.0, 50+ commands in
  bracket-menu style, and a `--tutorial` flag.

### 2.3 Load, counted

- First five minutes need: 4 commands, 3 ideas (board and commitment, measure before trusting the customer, two
  close codes). Low.
- Surface area visible from the shell: 159 commands, 159 man pages, 12 positions, 6 sign-offs, 13 named people,
  about 14 netnews posts, 12 home dirs. High, but opt-in. This is fine. The shell is a playground, and the README
  says so.
- Concepts that arrive by the end of tour 3 with no teaching: sheath faults and cable files, past-commitment vs
  oldest, force selection (4 forces, 5 named crews), what a sign-off unlocks, two clocks. These are introduced by
  NPCs, which is the right mechanism. They are not introduced on a schedule, so some players will never see them.

### 2.4 Onboarding fixes, in order of value

1. First report should be a *teaching* report. Customer says one thing, the pair says another. Halloran asks you to
   `report callback` before measuring so you meet the customer. Cheap: one scripted draw.
2. Skip the pacing delay for tables and readings on tour 1. Keep it for narrative lines. Or ship the first tour at
   `display.pacing off` and announce the switch to 300 baud on tour 2 as a story beat ("they've moved you to the
   Model 43").
3. Put a second thing on the board during the wait (the chief held it back for sound reasons, but a held-back
   second report that arrives *because* the crew is out is a better rhythm than silence).
4. Make the login menu a choice about the *story* only after tour 1. Day one: you are the test desk.
5. Fold the seven hint channels into three: the chief (first tour), `hint` (on demand), the prompt (opt-in).

---

## 3. Remove / Change / Add

P1 = do before anything else; changes the first hour or fixes a visible lie. P2 = shapes the middle of the
game. P3 = polish.

### 3.1 Remove

| P | File / module | Mechanic | Reason |
| --- | --- | --- | --- |
| P1 | `docs/manual.txt` (old catalogue, lines ~40-340, synopsis, version line), `docs/command_reference.txt` (version line, old sections), `docs/faq.md:28`, `docs/overview.md` (tutorial, `--tutorial`) | Stale documentation | Describes a game that does not exist: a tutorial flag and module, seven phantom commands, "Version 2.0 - November 2024" in a game set in 1983 |
| P1 | `data/shift_events.py` | Boilerplate briefing events | Fixed IDs, same three base events every tour, wrong city, no link to the board or the calendar. Replace with a dated script (see Add) |
| P2 | `npc._HINTS` (ambient "how to read an MLT" messages) | Redundant hint channel | `mlt` already names the answer and `hint` explains it. It is the hint system talking a fourth way |
| P2 | `Next:` suffix on every command after tour 1 | Non-diegetic prompt | Default on, breaks the V7 shell illusion the README sells. Keep for tour 1 and for `help`; make off the default after the first closed report |
| P2 | Status-only plant screens: `plant.py`, `radio.py`, `carrier.py`, `tsps.py`, `tnds.py`, `traffic.py`, `toll.py` (about 5,400 lines, hypothesis) | Menu-style commands (`5ess`, `satellite`, `western`, `tariff`, `microwave`...) | They print plausible tables and change nothing. Either wire each into the board (a fault source, a decision) or hide it from `help` and keep it as `man`-only reference. S2 to confirm which have consequences |
| P2 | `simple_terminal.py`, `--simple` | Second front door | "Four-role simplified interface" bypasses the repair loop that README calls the job. Not read; S2 to check whether it earns its place |
| P3 | `data/homes.py` authorship | Notes by the wrong people | Only the sysop note is by a real predecessor. A splicer writing the DBA's note and a transmission engineer writing the switching note dilutes "whoever held your position last". Re-sign them or accept it |

### 3.2 Change

| P | File / module | Mechanic | Reason |
| --- | --- | --- | --- |
| P1 | `progression.py` (`DIFFICULTIES['fun']`), `screens/testing.py` | MLT in fun mode names the fault | Make the assist *fade* with sign-offs: tour 1 names the fault, then names the class (loop / office / station) only, then names nothing unless asked (`mlt -h`). Gives fun mode a ramp to craft mode |
| P1 | `progression.py` (`QUALIFICATIONS.unlocks`), `screens/remote.py`, `screens/frame.py` | Qualification unlocks | Each sign-off should add a **verb that changes the board**, not a screen. Frame: `cosmos jumper` already finds a CO_EQUIP defect; let it fix one too. Office: clear FCG from the switch side. SCC: take another office's tickets with `connect`. Trunk: act on CAROT exceptions. Toll: apply network management controls. Today only `connect` does this |
| P1 | `clock.py`, `screens/turnover.py` | 13 identical tours | Give each tour a date, a reason and a beat. Snap the stride to the holidays: Thanksgiving is 24 Nov (tours land on 22 and 26), Christmas Day falls between 24 and 28 Dec. Last tour stays 31 Dec |
| P1 | `terminal.py` (`_pace_rate`), `settings.py` (`display.pacing`) | 300 baud default | See §2.4. Pace the story, not the table |
| P2 | `data/regulars.py` | Four chronic lines | Give each an arc across the 13 tours with a resolution before 1 Jan (Kowalczyk's sheath is finally spliced or finally abandoned; Whitcomb gets her drop). At 18% share, each regular should be someone the player *worries* about |
| P2 | `progression.py` (`service_index`) | Index is a rate | Add the E&O four-band scheme (H / O / L / U, E&O p. 679) and a separate *board cleared* meter, so a perfect five-report tour stops looking identical to a perfect thirty-two |
| P2 | `data/positions.py` | 12 same-board desks | Make four of them real lenses with a different win condition (repair, office, NOC, special services) and relabel the rest as "transfers" you can take after tour 3. Same code, different promise |
| P2 | `npc.py` (`_CHATTER`, `_POSITION_CHATTER`) | 61 static messages | Same lines on tour 1 and tour 13, none tied to date or board state except weather. Tag each with a tour window and a trigger so Okafor's manhole gets wetter each rainy tour |
| P2 | `screens/guidance.py` (`FIRST_TOUR`) | Walkthrough says what, not why | Add one line of *why* on the measure step: "the customer told us noise; the pair will tell you what." Keeps the voice |
| P3 | `data/signaling.py`, `tone` | The cadence puzzle | It is the best "answer is a sound" moment and appears once. Give it two siblings (ring-back vs busy; reorder vs all-trunks-busy) |
| P3 | `data/primer.py` | UNIX-only refresher | Add a second course, `training mlt`, in the same weary voice (BSP 000-200-000), so the telephony has a diegetic home too |

### 3.3 Add

| P | Where | Mechanic | Reason |
| --- | --- | --- | --- |
| P1 | New `data/calendar.py` (dated beats), read by `clock.py` and `screens/shift.py` | Dated beats per tour | One real or sourced beat per tour, replacing `shift_events`: 14 Nov start, the strike aftermath (already in netnews), Thanksgiving, a Christmas-eve overload (see §4, E&O p. 180), the last day. Facts need sourcing; keep SOURCES discipline |
| P1 | `screens/turnover.py`, `npc.last_word` | **The audit.** At tour 13, dispositions are audited and open reports pass "with your name on them" | The memo promises it (`/usr/doc/divestiture`, rules 1 and 2). It converts a ceremonial ending into a verdict, and gives the "wrong close" mechanic a long fuse. This is the best single addition |
| P2 | `filesystem.py`, `data/trouble.py` | **Pay off Marker 2.** Around tour 9-10, a CO_EQUIP / FCG cluster whose cause is the sequence relay | Five files already set it up. Johnson says "I have been saying this for two years". The player either listened or did not |
| P2 | `filesystem.py` (`SULOG`), `npc.py` | **Resolve `mreyes-root`.** Two candidate stories: (a) the RSA tried to reach a line record the system had locked; (b) someone used her terminal. Pick one, seed one clue elsewhere | A mystery already in the data with no end |
| P2 | `reports.py`, `screens/bureau.py` | **Trouble patterning**, from E&O p. 597-598 | Several reports whose only common factor is a dialled destination point at a network fault, found by pattern across reports, not MLT on one pair. The second puzzle the game lacks |
| P2 | `cable.py`, `reports.py` | **Pressure alarms before reports** (E&O p. 598) | Cable.py already models pressure falling first. Let the player act on the alarm and win by foresight, before the reports arrive |
| P2 | `reports.py` | **Hold for retest** as a third close (E&O p. 580: many troubles are transient) | Fixes the `NONE` fault's ambiguity ("transient or hiding"). Gives code 8 a cost that is not binary |
| P2 | `reports.py`, `screens/bureau.py` | Post-close customer call (TELSAM-style, E&O p. 680) | A second axis: technically right but late, or right and kind. The RSA's note about believing the customer becomes a mechanic |
| P2 | `npc.py` | Arcs for Sandoval, Alvarez, Reyes | Sandoval "newer, says less... the wire chief has noticed and has not decided about" is a plot with no ending. Alvarez signs one note and vanishes |
| P3 | `screens/turnover.py` | Wire-centre league table | E&O p. 679: results were compared across BOCs and published. A fake peer table that Halloran reads |
| P3 | `data/primer.py` | `training mlt`, `training network` | See §3.2 |
| P3 | `attached_assets/` | Use the unmined sources | See §5 |

---

## 4. Passages in E&O that could seed mechanics

Printed page / PDF page. Quotations are short; paraphrase otherwise.

| # | Passage | Pages | Seed |
| ---: | --- | --- | --- |
| 1 | **The attendant's screen.** The RSA is supported by a system showing name and address, service status, date of last trouble and count of previous reports, an appointment time that accounts for backlog and force size, results of automatic tests, and cable or equipment failures already affecting the circuit | 581 / 598 | Rebuild `report show` as this screen. Repeat count and known-cable-failure line become clues. Appointment time becomes a negotiation with the customer |
| 2 | **Verification.** "Many trouble indications are transient." Verified troubles get first priority | 580 / 597 | Third close: hold for retest. Transient reports that clear on their own |
| 3 | **Location is the hardest step**, and where the fault sits decides who goes (office, loop, premises). Footnote: for specials it may be interoffice facilities | 581 / 598 | Already used. Extend "who goes" to four places for special services |
| 4 | **False dispatches** and the **Defective Equipment Replacement Program**: customers bring phones to a service centre, 51% of 11 million troubled home phones in a year, 90% would do it again | 582 / 599 | `wasted_trips` as a first-class stat; a "swap the set" close for station faults |
| 5 | **Loop maintenance surveillance.** Automatic line insulation testing and cable pressure monitoring find incipient trouble before the customer feels it. A repair person with a test set still has to go to the frame or the cable route | 598-599 / 615-616 | Preventive layer: sweep results arrive before reports. Reward foresight |
| 6 | **Switching maintenance.** Electronic offices fail rarely, harder to diagnose, and a failure can hit many customers. Craft gets little practice, so maintenance is centralised. Small offices run unattended and alarms go to a central place | 599 / 616 | A rare, high-stakes office incident you cannot solve alone: you need Petrak. Pays off Marker 2 |
| 7 | **Trunk maintenance.** After the call ends nobody can say which trunk was bad, so trunk trouble is found by routine testing (footnote: CAROT) | 600 / 617 | CAROT exceptions as the *only* complaint a trunk can make. Pull the circuit or leave it in service: a decision with a cost |
| 8 | **Network Service Centers.** Reports are analysed for patterns, "such as a large number of reports resulting from attempts to reach a certain location"; support systems named in a footnote (NOTIS, NSCS, ATRS) | 597-598 / 614-615 | Trouble patterning (see §3.3) |
| 9 | **Congestion feeds itself.** Reorder causes reattempts which cause more load. A receiver timeout after 20-30 seconds wastes the work already done. Overload past about 150% of engineered load makes carried load fall | 177-178 / 194-195 | A NOC-desk loop with a real feedback curve. Fig. 5-12 is a ready-made timeline |
| 10 | **Network management controls**, Table 5-1: directionalization, cancel-to / cancel-from, rerouting, code blocking at 50/75/100%, Dynamic Overload Control, SDOC. Footnote: manual controls "may be applied too slowly and are often left in effect too long" | 180-181 / 197-198 | Toll sign-off verb. Apply a control, and it *stays on* until you remove it. Forgetting costs |
| 11 | **Focused and general overloads.** Mount Saint Helens (May 1980): calls to the Pacific Northwest three to five times Mother's Day. Mother's Day and **Christmas Day** reroute across time zones | 179-180 / 196-197 | Christmas-eve tour as a set piece. The NOC desk's note ("Mother's Day... do not raise anything") already tells the player the rule |
| 12 | **Switching Control Centers.** Unattended offices; maintenance data to a remote teletype; a shared minicomputer serving two SCCs and many offices; on-site work dispatched from a central pool | 632-634 / 649-651 | Constrain `connect`: one console, many offices, a limited dispatch pool. Petrak's eleven buildings become eleven tickets |
| 13 | **Special services.** One-person testing is the goal; SARTS; DACS for remote digital access | 601 / 618 | Support for the `sarts` note: "nobody owns it". Tests that need a partner you do not have |
| 14 | **Four-band results**: H (so high it may not be cost-effective), O (objective), L (low), U (unsatisfactory). Results collected monthly, compared across BOCs, published widely | 679 / 696 | Replace EXCELLENT/SATISFACTORY. An **H** band is a gift: a perfect 100 can read as over-serving |
| 15 | **Two tiers of measurement.** Ten components on top, eighteen supporting performance indicators beneath, for diagnosis | 681 / 698 | The index as two layers: headline, and indicators that tell you *why* |
| 16 | **TELSAM.** Short telephone interviews with customers about repair service, selected from a sample | 680-681 / 697-698 | A post-close customer call. Satisfaction as a second score |
| 17 | **Control = diagnose symptom to cause.** "Most measurements are observed effects... a quantification of symptoms rather than causes" | 679 / 696 | A design sentence for the hint system and the debrief: say what the reading *meant* |
| 18 | **Customer reports component.** Code 5 and code 8 counted separately, "attributable to the switching equipment" | 682-683 / 699-700 | Caution, not a seed: the game applies 5/8 to every loop report. Defensible as a simplification; say so in `SOURCES.md` |
| 19 | **After divestiture** "no one company will be responsible for complete end-to-end telephone service"; each company picks its own measurements | 683 / 700 | The January theme as a mechanic: circuits with one end in each company; who owns the repair |
| 20 | **Defect seriousness classes**, A/B/C/D at 100/50/10/1 demerits (a manufacturing scheme) | 748 / 765 | A severity weighting for wrong closes: a FEMF closed as NTF is a 100, a cosmetic miss is a 1 |

Two caveats worth recording:

- E&O does not support "qualification governed what a craftsperson could touch" as a stated fact. The only
  hits for *qualif* are unrelated. The mechanic is sound design and a plausible reading of craft practice, but
  README and `progression.py` present it as history. Soften the claim or find a source.
- E&O names **LMOS** once outside the glossary (printed p. 653 / PDF 670, in a list of operations-system
  inputs) and **MLT** only in the abbreviation table (p. 826 / PDF 843; the text layer interleaves columns there,
  so the expansion cannot be read cleanly from it). The repair-bureau detail the code cites comes from
  *Telecommunications Transmission Engineering* vol. 2, not from this book. The book supports the corrective
  maintenance sequence, the RSA's screen and the performance plans; it does not describe a test desk.

---

## 5. Unmined material already in `attached_assets/`

Not read beyond title and headings.

| File | What it is | Use |
| --- | --- | --- |
| `BSRS 104.011` | Western Electric Distribution and Repair Services, issue 45, 1 July 1983: an index of tools and test sets | Flavour for a craft toolkit and for storeroom-style items |
| `SD_26030-01` | No. 5 crossbar: line, line link, marker connector control circuit | Ground the Marker 2 / sequence-relay payoff (to check that the circuit names it) |
| `bellsystem_SD-1C900-01` | 3A central control circuit description | Support for the `3a` screens |
| `806220` | 1A2 key telephone systems: service | Station-side faults for the installer |
| `WE_Fundamentals_of_Telephony_Lesson_1_Mar62` | A training lesson | A style model for `training mlt` |

---

## 6. Limits of this review

- I did not run the game. Claims about timing, pacing feel, mid-career pacing and what the plant screens do
  come from docstrings and code structure. S2 should time the first tour, the dispatch wait, and tour-to-tour
  board depth.
- I read `man_pages.py` by grep only (159 pages exist), and did not read `simple_terminal.py`, `tickets.py`,
  or the plant, radio, carrier, TSPS, TNDS, traffic or toll screens beyond their docstrings and sizes.
- The 61-message and 12-event counts were taken from the data tables directly.
- Historical dates added by me (Thanksgiving 24 Nov 1983, 14 Nov 1983 a Monday) are calendar arithmetic. Any
  further real events for the dated script need sourcing under the `SOURCES.md` rules.
