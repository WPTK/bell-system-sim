# Session 3 research blueprint: gamifying bell-system-sim

Audit of `WPTK/bell-system-sim` v4.0.0, outside research and synthesis.
Not a bug hunt. Sessions S1 (material review) and S2 (code and playtest)
run in parallel; where this document depends on something they may find
different, it says "confirm with S1/S2".

How this was made: the seven required readings, one `researcher` agent for
the wider areas, and a text search of Bill's copy of *Engineering and
Operations in the Bell System*, 2nd ed. 1984 ("E&O" below, extracted with
`pdftotext -layout`; cited by section number). I read the repo lightly:
README, `docs/overview.md`, `SOURCES.md`, and the parts of
`progression.py`, `reports.py`, `npc.py`, `save.py`, `filesystem.py`,
`clock.py`, `screens/shift.py`, `screens/turnover.py`, `screens/guidance.py`
and `data/` needed to say where a change goes.

## Part 0. What the game already does well (keep it)

These are things the research says to protect, and the blueprint assumes
they stay:

- **Onboarding by doing.** One report on the first board, Halloran walking
  the loop on `write(1)`, no tutorial mode. This matches Zarf's "emulate the
  situation, do not be told it" (A3).
- **Every refusal names a way out; hints cost no score** (`cmd_hint`
  docstring). Right call; see Zarf on failure messages (A3) and Pope on not
  stacking new rules (B1).
- **A wrong close explains itself with the player's own readings.** This is
  the best single piece of feedback in the game. It is the "immediate
  feedback" that flow depends on (B3).
- **The world is a filesystem** (`/usr/lmos`, `/usr/bsp`, mail as a file).
  That is a database you can `grep`, which is exactly the Her Story
  mechanic (B2) with no new UI.
- **Period honesty rules** (`SOURCES.md`). They are a feature, not a limit,
  and every Add row below follows them.

## Part 1. Research notes by area

Each note: the principle in my words, the source, and how it bites here.
Status tags: **read** = I or the researcher read the page; **snippet** =
seen only in a search result or abstract; **unverified** = believed, not
sourced. Anything tagged snippet or unverified is not leaned on as the sole
support for a P1 row.

### A. The seven required readings

All seven were read. Two needed extra effort: the Pomona page is rejected by
the web fetcher on certificate grounds, and was read by downloading the HTML
directly; the Liverpool PDF was downloaded and converted to text.

**A1. Game Design Skills, "Text-Based Games"** (read).
https://gamedesignskills.com/game-design/text-based/
- Signpost what the player can do and forgive loose input. Here: the shell
  already suggests near-misses; keep every new command discoverable from
  `help` and the standing prompt.
- Persistent state and NPC memory make a text world feel inhabited. Here:
  NPCs and customers should remember the tour before (rows A5, C5).
- Failures should be informative and flavourful. Here: each failed command
  is a place to plant a line of lore.
- Save the biggest rewards for key story moments. Here: gate big reveals to
  specific tours (A4).

**A2. Pomona CS181G, "Text-Based Game Design"** (read via direct download).
https://cs.pomona.edu/classes/cs181g/notes/text-based.html
- Text games run on **operational logics**: *linking* (rooms joined, things
  inside things), *resource*, and *game-state* logics; persistence ("once
  solved, stays solved") is a logic in its own right.
- Separate **durable definitions** (rooms, doors, messages) from **transient
  player state**, and load the first from data files. Here this is already
  the shape: `data/*.py` definitions, `save.py` state. New content goes in
  `data/`, new state goes in `Career` or `save.capture`, never mixed.
- The interesting design question is what the world graph is. For this game
  the graph is ticket to line to cable to office to person; the blueprint
  adds cross-links (root causes, arcs, finds), not more rooms.

**A3. Zarf, "IF for Writers"** (read). https://www.eblong.com/zarf/essays/if-for-writers.html
- Let the player emulate the situation; do not narrate it at them.
- Build **complicity**: even a forced step should feel chosen. Closing a
  report "no trouble found" under a clock should feel like the player's
  call, which it does (code 8 with the callback risk).
- Control is layered (input, actions, puzzles, goals, arc). Decide which are
  free and which fixed. Here: free tool order, fixed 13-tour arc.
- Failure text can carry setting and character; teach core verbs early and
  keep them consistent.

**A4. Liverpool COMP222, lecture 1** (read; low yield).
https://cgi.csc.liv.ac.uk/~xiaowei/game_materials/lecture1.pdf
It is a course introduction and a history of games, not a design lecture.
Three small things apply: *Spacewar* ended up shipped as a diagnostic
program on PDP-1s (a work tool that became play, which is this game's own
shape); the **1983 video game crash** is on its own timeline (a period
joke or a netnews thread); and the module treats game AI as finite-state
agents plus content generation, which is the level of NPC machinery this
game needs and no more. Nothing here supports a row on its own.

**A5. Jerry Green, "Simulation principles"** (read). https://jerrygreen.github.io/en/simulation-principles
- The world runs without the player; NPCs choose among their most urgent
  needs, sometimes randomly among the top few.
- **Causality**: nothing spawns from nowhere; tickets and items have
  lifecycles. Reports should come from weather, cable age and storms (the
  game already ties weather to wet sheath).
- Rare, varied events; narrative urgency matched to gameplay urgency; if the
  player ignores something, consequences show.
- Environmental storytelling: stale files and old mail tell a story with no
  cutscene.

**A6. ch0m5, "Game Design Pillars"** (read). https://ch0m5.github.io/Game-Design-Pillars/
- Pillars are specific filters ("have fun" is not one). Set them early, have
  one decider, and cut ideas that fail them. Part 4 below does this.
- Make the core loop satisfying before adding lore; guide with feedback and
  short-term goals; keep rules coherent so players can form strategies.

**A7. The Design Lab, "Simulation Ruleset"** (read). https://thedesignlab.blog/2025/05/12/designing-immersive-games-using-the-simulation-ruleset/
- A rule is something the world **always** does. Four kinds: physical,
  systemic, UX (state shown to the player), accessibility (more than one way
  past a blocked task).
- Consistency builds immersion; mark exceptions. Overlapping systems make
  emergence. Believability beats realism.

### B. Wider research

**B1. Zachtronics, Papers Please, Hypnospace, Uplink: manual-driven simulation**
- *A dense in-fiction manual replaces the tutorial*, and Barth said he
  could not subtract the hard part and keep the game. He kept real
  structure but invented the rules to avoid real electronics' unpredictability.
  Inverse interview (read): https://inverse.com/article/23382-shenzhen-io-zachtronics-zach-barth-interview
- Puzzles state **criteria, not answers**, so solutions range from elegant to
  kludgy; players are compared on measured scores; the team watches player
  data to find difficulty spikes; texture is deliberately "nubbly". The Amp
  Hour #332 transcript (read, first 100K chars): https://theamphour.com/332-an-interview-with-zach-barth-of-zachtronics
- Zachtronics ships puzzles it has not fully solved (Game Developer page on
  the 2019 GDC talk, read): https://gamedeveloper.com/design/video-zachtronics-approach-to-open-ended-puzzle-design
  The SpaceChem GDC 2013 postmortem exists (abstract only, snippet):
  https://gdcvault.com/play/1017983/Ahead-of-the-Curve-The
  The worldwide score histogram per criterion is **unverified** (one
  Wikipedia snippet on *Infinifactory*).
- *Papers, Please* (Pope): never add a new rule on a day with other new
  things; moral outcomes kept vague and non-judgemental; a handful of
  scripted encounters per day with the rest generated from the day's rules;
  the hard problem was 30 days with no dry spells; pressure is applied
  selectively with relief. Read: https://www.gamedeveloper.com/design/designing-the-bleak-genius-of-i-papers-please-i-
- *Hypnospace Outlaw* (Tholen devlog, read): a fake period OS carried the
  whole game once it was the thing players responded to; characters are
  revealed in layers through profiles; some secrets are left unexplained.
  https://jay-tholen.itch.io/hypnospace-outlaw/devlog/3891/devlog-1-an-adventure-game-a-journey-through-hypnospace-outlaws-prototypes
- *Uplink*: **no design claim could be sourced.** Do not cite it.

**B2. Epistolary and computer-based story**
- *Her Story* (Barlow): a structural hook first; the database shows only the
  first five clips per search word, so revelations come from combining
  words; he hand-tuned over- and under-used clips from usage data; no hints
  on what to search; the fake-computer feel comes from degraded media and
  real keyboard noise. Read: https://www.pocketgamer.biz/making-of-her-story/
- *Telling Lies*: the player sees one side of each exchange and infers the
  other; the "ah ha" is the player's own connection. GDC 2019 coverage
  (read): https://gameinformer.com/gdc-2019/2019/03/27/her-story-creator-finally-details-what-to-expect-from-telling-lies
- *Orwell*: information is ambivalent, the player decides what to pass on,
  documents sit in layers (public, private, never meant to be seen).
  Read: https://www.gamedeveloper.com/design/road-to-the-igf-osmotic-studios-i-orwell-i-
- Infocom: *Deadline* moved interviews and reports into a physical dossier
  the disk could not be solved without, and the box cost $10 more (Maher,
  read): https://www.filfre.net/?p=618. Feelies doubled as copy protection
  and sometimes as puzzle material: https://www.ifwiki.org/Copy_protection

**B3. Academic frameworks**
- **Self-Determination Theory** in games: autonomy, competence,
  relatedness. Ryan, Rigby and Przybylski (2006), *Motivation and Emotion*
  30(4), "The Motivational Pull of Video Games". DOI resolves
  (https://doi.org/10.1007/s11031-006-9051-8); I did not read the paper
  text, only the University of Rochester release
  (https://www.rochester.edu/news/printable.php?id=2719) and the PENS
  summary (https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/,
  read by the researcher; the page returns 403 to a plain request). PENS
  adds easy-to-master controls, clear consistent feedback, and choice of
  goals and strategy.
- **Flow**: Csikszentmihalyi's challenge-skill balance, as applied to games
  by Chen, "Flow in Games (and Everything Else)", CACM 50(4), April 2007,
  31-34, DOI 10.1145/1232743.1232769 (snippet and a summary blog,
  https://wordpress.cs.vt.edu/csblog/2007/06/01/in-the-flow/ read).
  Too hard gives anxiety, too easy gives boredom. A Game Developer piece
  argues balance alone is not enough: clear goals, immediate feedback and a
  sense of growth are also needed
  (https://www.gamedeveloper.com/design/gamification-dynamics-flow-and-art,
  author not identified). The 1990 book itself was not read.
- **Octalysis** (Yu-kai Chou): eight core drives: Epic Meaning and Calling;
  Development and Accomplishment; Empowerment of Creativity and Feedback;
  Ownership and Possession; Social Influence and Relatedness; Scarcity and
  Impatience; Unpredictability and Curiosity; Loss and Avoidance.
  https://yukaichou.com/octalysisbook (read). The white-hat/black-hat split
  is from Chou's Medium essay (403, snippet) and a Yale summary
  (https://som.yale.edu/blog/the-motivating-power-of-games). Sources
  disagree on drives 4 and 5. My working reading, **not sourced**: 1-3
  white hat, 6-8 black hat. Used here only as a lens, never as a quota.

**B4. Telecom authenticity**
- **Repair loop, from E&O 13.2.3 (in Bill's PDF, read).** Corrective
  maintenance is six functions: trouble *detection*, *notification*,
  *verification*, *location*, *repair*, *service verification*, and E&O
  calls location "often the most difficult and time-consuming step". The
  repair service attendant works from an operations system that returns, in
  real time, name and address, service status, the date of the last trouble
  and the number of previous reports, an appointment time that accounts for
  both the backlog awaiting dispatch **and the size of the craft work
  force**, results of any automatic tests, and known cable or equipment
  failures affecting that circuit. After repair, the craftsperson verifies
  clearance and the customer is notified and satisfied. E&O notes that many
  trouble indications are transient, so verified troubles get first
  priority, and that remote testing helps "eliminating false dispatches".
- **Measurement, E&O 16.4.2.** A trouble report is created, tracked, and its
  disposition recorded; these give "micro measurements" of customer actions
  and of the maintenance effort. Customer attitudes are measured too
  (16.4, "customer satisfaction", cited to McDade 1979).
- **SCC, E&O 14.x.** About fifteen offices to a control centre, thirty or
  more possible, sited so the goal is within a half-hour dispatch time from
  any office it serves.
- **MLT/LMOS in the BSTJ**: the July-August 1982 issue (Vol. 61 no. 6 part 2)
  carries "Mechanized Loop Testing Strategies and Techniques" (p. 1209),
  "Mechanized Loop Testing Design" (p. 1235) and "Second-Generation MLT"
  (p. 1257). Scan at bitsavers (too large to fetch; contents from the
  listing): https://bitsavers.mirrorservice.org/magazines/Bell_System_Technical_Journal/BSTJ_V61N06_198207_Part_2.pdf
  Check whether `attached_assets/` already holds this issue before citing.
- **A working description of the LMOS flow** (amateur, 1986 but detailed):
  Phrack 9, "Loop Maintenance Operations System",
  https://phrack.org/issues/9/loop-maintenance-operations-system (read).
  The attendant enters line and symptoms; LMOS returns a basic output report
  with line history and test values; the report is screened to a dispatcher
  or tester; LMOS keeps a trouble history of the last 40 days; MLT runs
  AC/DC, soak, balance and dial-tone tests and retests after repair before
  the customer is told. It never mentions a "test desk"; the term appears in
  a Bell patent (US4645874, snippet).
- **Signalling and fraud.** E&O: until 1976 signalling was almost entirely
  per-line or per-trunk, in the voice channel; common-channel interoffice
  signalling (CCIS) is growing, and "reduction of fraud" is listed among the
  needs it answers (E&O ch. 5 and the signalling chapter, which the repo's
  copy of the book also carries). This is the sourced hook for any blue-box
  story: the same in-band design that made toll fraud possible was being
  replaced.
- **Phreaking.** Lapsley, *Exploding the Phone* (Grove, 2013), not read;
  TAP ran from the early 1970s to 1983 per Cheshire Catalyst's HOPE 1994
  talk (snippet, https://infocondb.org/con/hope/hackers-on-planet-earth/the-history-of-tap-magazine);
  2600 began in 1984 (snippet). **Not found:** a Computer History Museum oral
  history, historyofphonephreaking.org, Telephone World, Bell Labs Record.
  Treat anything beyond "it existed and these dates" as needing a source.
- **Divestiture and morale.** The MFJ was a consent decree entered 24 August
  1982 by Judge Greene, ending the 1956 Final Judgment
  (https://en.wikipedia.org/wiki/Modification_of_Final_Judgment). UPI, 19
  December 1983, "Jan. 1, 1984: AT&T D-Day" (read by the researcher; 403 to a
  plain request): employees described grief, Chairman Brown said "Mother
  doesn't live here anymore", an executive called the "culture shock"
  "difficult to exaggerate", and promotion-from-within gave way to
  risk-taking. https://www.upi.com/amp/Archives/1983/12/19/Jan-1-1984-ATT-D-Day/6083440658000/
  The E&O preface gives the restructuring as about 1 million employees and
  about $160 billion in assets (the table of contents places the MFJ at
  17.4.4); its chapter 1 says AT&T Communications drew its first employees
  from the BOCs, the AT&T General Departments and Long Lines.

### C. Gaps found in this game, from the research

Five observations. Each is checked against the code I read; S2 should
confirm in play.

1. **The index only subtracts.** `Career.service_index` starts at 100 and
   loses points for wrong dispositions, repeats and (on craft) missed
   commitments. A player who plays flawlessly sees nothing happen. SDT
   competence and Chen's growth requirement both want evidence of mastery,
   and Octalysis would call this loss-and-avoidance with nothing on the
   other side.
2. **The ladder is a counter.** `QUALIFICATIONS[].requires_reports` is a
   count of correct closes (27 correct on Fun, 108 on craft, for the last
   rung). Counting rewards repetition. The research says reward a new
   *capability being shown*.
3. **The filesystem is not saved.** `save.py` says so by design. The game
   invites `ed` and `echo > notes`, but notes die with the session, so the
   best diegetic journal there is cannot be used as one.
4. **Lore is planted, not structured.** Finds are real (sulog, memo, news)
   but nothing counts them, orders them or pays them off. Her Story works
   because the database is searchable *and* the plot is tuned to what
   searching turns up.
5. **Mastery has no yardstick except the player's own index.** The
   calibration tool (`tools/index_calibration.py`) already plays hundreds of
   simulated shifts. That is a population the player could be measured
   against, as Zachtronics measures players against each other.

## Part 2. Blueprint

Legend. **P1** = do first, biggest effect per line of code. **P2** = second
wave. **P3** = nice to have. "Where" names the module, "State" names what
is saved, "Command" names anything the player types.

Conventions for every row: standard library only; new definitions go in
`data/` (durable), new state goes in `Career` (`career.json`) or
`save.capture` (`shift.json`) as the existing code does; no screens module
over 1,000 lines and `terminal.py` under 2,000 (`tests/test_integrity.py`);
every new historical claim goes through `SOURCES.md` as verified, sourced
or **the simulation's own**. A row that adds an invented number says so in
its Build cell.

### 2.1 Remove

| # | Pri | Principle and source | What goes | Build note |
|---|---|---|---|---|
| R1 | P1 | Emulate, do not narrate (Zarf A3); keep the real friction, soften it with scaffolding (Barth B1); competence needs something to do (SDT B3) | Fun mode's `mlt` **naming the fault outright every time**. `loop_testing.measure_loop(name_fault=True)` and the "It names the fault and the crew" text in `data/hints.py` | Replaced by the fading annotation in C1. Delete the unconditional `name_fault` default on the Fun profile; keep the parameter. `data/man_pages.py` line 1857 and the `first` hint level 2 need rewording. |
| R2 | P1 | Octalysis: loss-and-avoidance with no counterweight (B3); flow needs visible growth (Chen B3) | The index as the **only** scoreboard | Not deleted, demoted: C2 puts a credit side beside it. |
| R3 | P2 | Her Story / Green: consequences should be causal, not scheduled (A5, B2) | Fixed-id base events in `data/shift_events.py` ("EV-8001 trunk group monitoring TG-023... TG-045 at 73%") that print the same invented figures every tour | Replace with lines generated from the day's `ReportDesk`, weather and cable state in `shift_events.build`. Confirm with S1 whether these figures are labelled invention. |
| R4 | P2 | Reward a capability shown, not a count (SDT, Chen B3) | Qualification as **count only** | Count stays as an eligibility floor; the practical in C3 is the gate. |
| R5 | P3 | Coherent rules and meaningful choices (Pillars A6, Octalysis empowerment B3) | Positions that differ by **presentation only** (`docs/overview.md`: "the command set is presentational - execution is not gated") | Give each of the 12 positions one verb only it uses and one report type only it sees (A18 below). Confirm with S1/S2 how far `test_position_differences.py` already goes. |
| R6 | P3 | Green: a world that runs without you has state-driven voices (A5); Barlow tuned his, he did not leave them random (B2) | Ambient chatter drawn **at random** as the main texture (`npc._CHATTER`, `Switchroom._pick`) | Keep as filler. Selection order becomes: arc beat, then board-driven message (A5/A6 below), then random pool. `_pick` gains a priority list. |
| R7 | P3 | Replay (Octalysis ownership, B3) | `Career.finished` as a terminal state ("nobody to relieve you twice") | Not removed from the story, but the dead end is replaced by A12 (legacy and new hire). |

### 2.2 Change

| # | Pri | Principle and source | Mechanic | How to build it |
|---|---|---|---|---|
| C1 | P1 | Scaffolding that fades keeps the player in the flow channel (Chen B3); competence (SDT) | **Annotated readings that fade.** The first N sightings of each fault type on Fun show a one-line reading note ("low on every reading at once is water in the sheath"); after N, numbers only. Craft shows none | Where: `screens/testing.py` (the `mlt` renderer) and `loop_testing.py`. State: `Career.fault_sightings: Dict[str,int]` in `career.json` (load/save in `progression.py`, tolerant of absence as the other fields are). Data: annotation text per fault in `data/trouble.py` `FAULTS` (a `reading_note` field). Difficulty gains `annotation_sightings: int` (Fun 2, craft 0). Test in `tests/test_progression.py`. |
| C2 | P1 | Competence needs evidence of growth (SDT, Chen B3); Development and Accomplishment (Octalysis); Zachtronics scores per criterion (B1) | **Commendations beside the index.** Named, earned, never lost: *first clean tour*, *five consecutive correct closes*, *found the shared sheath*, *closed an out-of-service within commitment during a storm*, *measured every line on a tour*, and so on. Printed at handoff. The index keeps its penalty maths | Where: `Career.record_closure` (`progression.py`) already sees every close; add `Career.commendations: List[str]` and a small table `data/commendations.py` of (key, name, test callable name, description). `tour_summary` in `screens/guidance.py` prints new ones. `qual` lists them. State: `career.json`. The wording is the simulation's own; label it so (a "performance letter" is period-plausible but the specific awards are not claimed). |
| C3 | P1 | A rung should test a capability (SDT competence; Zachtronics criteria-not-answers B1; Zarf layered control A3) | **Qualification practical.** After the count floor, `qual take <key>` stages a short scenario on the live board that uses the new commands: e.g. for *Interoffice Trunks* a trunk group with a stuck member to find and busy out; for *Toll* a congestion pattern in `traffic`. Pass and Halloran signs; fail and he says what you missed | Where: new `data/practicals.py` (scenario id, setup lines, check callable, debrief text), driver in a new mixin `screens/practical.py` (declare shared attrs in `screens/session.py`). Reuses `ReportDesk` plant and `special_services`. `Career.grant_available` becomes `offer_available`; granting moves to the practical. State: `Career.practicals_passed`. Command: `qual take <key>`. Keep the existing sign-off remarks in `npc._SIGN_OFF_REMARKS`. |
| C4 | P1 | Regulars are the best narrative device the game has; Papers Please repeats people until they matter (B1); NPC and customer memory (A1) | **Four regulars get a multi-tour arc.** Kowalczyk's sheath gets a splice crew date and then a failure; Ferrante's rooming house changes hands; Whitcomb's drop is finally replaced just before the last tour; Duchesne's doctor changes exchanges at divestiture. Callbacks (`report callback`) carry the beat; `custdb` shows it on the card | Where: `data/regulars.py` gains `arc: Tuple[Beat,...]` where `Beat(tour, note, callback_lines, fault_bias)`; `ReportDesk.regular_record` (`reports.py`) picks the beat for `career.shift`; `screens/bureau.py::_report_callback` prints the lines; `screens/records.py::cmd_custdb` shows the card with the latest note. State: `career.json` `beats_seen`. The `note` and `since` fields are already in the voice the arc needs. Mark arc events as invented in the module docstring, as `regulars.py` already does. |
| C5 | P1 | Autonomy: more than one way past the same wall (SDT, Design Lab accessibility rule A7); Zachtronics difficulty is chosen (B1) | **Split difficulty into assists.** The two profiles stay as presets, but each rule becomes a named setting: `assist.annotate`, `assist.close_untested`, `assist.hint_pointers`, `assist.commitments_count`, `assist.interruptions` | Where: `progression.Difficulty` fields already hold the rules (`require_test_before_close`, `count_missed_commitments`, `interruption_rate`...); add overrides in `settings.py` that, when set, win over the profile. `set` already lists and marks departures from period behaviour, so the display work is done. State: `settings.json`. README line on "how forgiving, nothing else" stays true. |
| C6 | P1 | Short-term goals and clear feedback (Pillars A6; Chen B3; Octalysis accomplishment) | **Tour goals on the briefing.** Two or three visible goals per tour, drawn from the tour's theme and the board ("clear both out-of-service reports before 11:00", "find what the Sussex St reports share", "pass the Office practical"). Struck through at handoff | Where: `screens/shift.py::show_shift_briefing` and `_emit_board_briefing`; progress read by `guidance.next_action`; `tour_summary` prints met/missed. Definitions in `data/tours.py` (see A4). State: `shift.json` `tour.goals`. No score effect: goals only feed commendations (C2), so they cannot be failed in a way that bites. |
| C7 | P2 | Papers Please: relief days and selective pressure (B1); Chen: avoid constant overload (B3) | **Tour shape is a sawtooth, not a ramp.** Today the board deepens and the weather worsens monotonically with `career_progress`. Add scripted quiet and crisis tours | Where: `data/tours.py` supplies per-tour `kind` (`routine`, `storm`, `holiday`, `audit`, `quiet`) and a depth modifier; `turnover._end_shift` applies it where it sets `desk.depth_limit = self.board_depth()`; `Weather(...wet_bias=...)` already takes a bias. Calibrate with `tools/index_calibration.py`. |
| C8 | P2 | Pope: moral outcomes vague, never a lecture (B1); consequences shown (A5) | **Consequence in a person's voice.** A wrong close that comes back as a repeat shows the customer's second call, one or two lines, no moral. A missed out-of-service commitment gets a line from the attendant who took the call | Where: `npc.Switchroom.repeat_notice` and `chase` (`npc.py`) already exist; extend with `data/consequences.py` keyed by class of service (`1FB` home, `COIN`, `PBX`, `1MR`). `tests/test_stakes.py` suggests some stakes text exists; confirm with S1 and extend rather than duplicate. |
| C9 | P2 | Trouble location is the hardest step (E&O 13.2.3 B4); layered control (Zarf A3) | **Dispatch to a place, not just a force.** `report dispatch 1 outside plant` becomes `... outside plant <section>` where capacitance/distance readings let the player name a cable section or terminal. Right place: the repair happens. Wrong place: the trip is spent and the report comes back with the crew's finding | Where: `ReportDesk.dispatch` (`reports.py`; `COST_WRONG_DISPATCH` already prices a wrong force); sections come from `cable.py` binder-group and `WetSection` model; `loop_testing` already turns capacitance into distance (0.083 uF/mile, sourced). Fun mode accepts the old form. State: report field `dispatch_where` in `save._REPORT_FIELDS`. Update `data/man_pages.py` for `report`. |
| C10 | P2 | Persistent state makes a text world live (A1); notes you wrote are yours (Octalysis ownership B3) | **Save the player's home directory.** What you write with `ed` and `echo` under `/usr/users/<you>` survives sessions | Where: `save.py` (docstring currently says the filesystem is deliberately not saved). Write only the player-created overlay, not the static tree: add `home.json` beside `shift.json` and a `capture_home`/`restore_home` pair; the terminal's working filesystem is the `FILESYSTEM` dict of `Node`s in `filesystem.py`. Limits: 64 KB total, text only. Enables A2 and A12. |
| C11 | P2 | Relatedness and ownership at the end (SDT B3; Octalysis epic meaning) | **The ending reads the career.** `npc.last_word` and `_end_career` currently take tours, closed and index. Feed them the arc flags, rapport (A5), commendations (C2), finds (A2) and assignment (A8) | Where: `npc.Switchroom.last_word`, `screens/turnover._end_career`. Keep the quiet tone the README promises. Test the combinatorics with a table-driven test in `tests/test_progression.py`. |
| C12 | P3 | Special service and priority lines (E&O 13.2.3 footnote 4 on special services, B4) | **Priority classes**: a doctor's answering line and a hospital PBX carry tighter commitments and named consequences | Where: `reports.CLASSES_OF_SERVICE`, `_commitment`. The 480/1440-minute commitments are the simulation's own (`reports.py` constants); label any new figure the same way. |

### 2.3 Add

| # | Pri | Principle and source | Mechanic | How to build it |
|---|---|---|---|---|
| A1 | P1 | Diegetic manual as puzzle material (Barth B1; Infocom dossier, Maher B2; Zarf A3) | **The Practices binder.** `/usr/bsp` is an empty directory in the static tree. Fill it with short practice sheets that give *tables you apply*: reading bands to fault, remedy by force, commitment rules. MLT output cites the sheet ("see section 234-320"). Fun mode links to the sheet; craft makes you open it | Where: new `data/practices.py` (sheet id, title, body in nroff-friendly text so `nroff` works as the README promises, and the tables as plain text); populated into `/usr/bsp` by the filesystem builder in `filesystem.py` at qualification time (the static `FILESYSTEM` dict takes a callable overlay). `data/hints.py` level 3 points at a sheet instead of giving the answer. **Authenticity:** the real BSP numbering scheme and text are not in the repo's sources unless S1 finds them in `BSRS 104.011` or `301-925_I1`; until then every sheet number is **the simulation's own** and says so in a header line, and each table's values trace to `loop_testing`/`data/trouble.py`, which already carry their sources. |
| A2 | P1 | Searchable database as narrative (Her Story, Telling Lies B2); Hypnospace layers (B1); Orwell layers (B2) | **Finds and fragments.** Mark 20-30 existing and new files as fragments of one story. Reading one (`cat`, `grep` hit, `more`) records it. `finds` prints a numbered list by title only. A third of the fragments are only visible by `grep` across files, not by browsing | Where: `Node` in `filesystem.py` gains an optional `fragment: str` id; the read path in `screens/shell.py` (it already enforces permission denied at line ~105) calls `self.career.note_find(id)`. State: `Career.finds: List[str]` in `career.json`. Command: `finds` (new `cmd_finds` in `screens/records.py`, which also holds `custdb` and `training`). Payoff text in A3. Her Story shows five results per search; do the same: `grep` over the spool stays as is, but a fragment-bearing file appears in the first five matches only when its tour has been reached. |
| A3 | P1 | Layered privacy as progression (Orwell B2); environmental storytelling (A5); sourcing: this uses structures the game already has | **The predecessor's story, gated by permissions.** "Notes from whoever held your position last" are in the README. Make it a thread: `.sh_history`, a half-written mail draft, a `sulog` entry, a note taped to a terminal. Files are mode 600 or group `adm`/`craft`. Halloran's third sign-off already adds you to `adm` (`npc._SIGN_OFF_REMARKS[3]`); make each sign-off open the next layer, so promotion literally gives you the next chapter | Where: `filesystem.py` adds `/usr/users/<predecessor>/` files; `Career.groups: List[str]` replaces the single hard-coded `adm` grant; the group list feeds the permission check in `screens/shell.py`. State: `career.json`. Command: none (it is `ls -l` and `cat`). The thread ends in one decision in the last tour (what you do with what you know). Everything about the predecessor is the simulation's own invention; `SOURCES.md` gets one line saying so. |
| A4 | P1 | Papers Please: a few scripted beats per day, the rest systemic (B1); save the big reveals for key moments (A1) | **Thirteen tour definitions.** One row per tour: theme, kind (C7), goals (C6), one scripted set-piece event, which arc beats fire (C4), which mail and orderwire traffic is guaranteed. The date comes from `clock` (tours are four days apart from 14 November, the last pulled to 31 December) | Where: new `data/tours.py` (`TOUR[1..13]`); `shift.generate_shift_events` and `_fire_due_events` read it; `npc` gets one `tour_traffic(tour)`. Real calendar hooks must be sourced or labelled: Thanksgiving 24 November 1983 is a fact; anything about local weather is not (the repo already refuses to claim it, `SOURCES.md`). The August 1983 strike is already sourced there and can echo in mail. |
| A5 | P1 | Relatedness (SDT, PENS B3); needs-driven NPCs (A5) | **Rapport with the other craft.** Every NPC keeps a small integer for you. Helping Reyes with a customer, answering the splicer quickly, replying on `write` all raise it. At thresholds they do something for you: the splicer comes sooner, Halloran signs a rung one report early, Johnson tells you what he wrote on the marker | Where: `npc.Craft` gets `rapport_hooks`; `Career.rapport: Dict[str,int]`; reply logic in `screens/shift.py::_craft_reply` and `cmd_write`; favours as `Switchroom.favour(login)`. State: `career.json`. Decay and caps so it cannot be farmed (clamp 0-5, one gain per tour per person). Command: none; it is inferred from `write`/`mail`. |
| A6 | P2 | Zachtronics ranks players against a population (B1; histogram claim is unverified, so lean on the scores, not the histogram) | **The tour ledger against the office.** Handoff prints your mean time-to-clear, first-pass accuracy and board carried, each with where it sits among simulated peers ("better than most of the office on accuracy; slower than most on time") | Where: `tools/index_calibration.py` already plays hundreds of shifts; have it emit a small distribution file `data/peers.py` (deciles per metric per difficulty). `screens/turnover.tour_summary` reads it. Label as the simulation's own population, not historical. No network, no leaderboard. |
| A7 | P2 | Epic meaning and autonomy at a fork (Octalysis, SDT B3); divestiture reality (UPI B4; E&O ch. 1) | **The assignment.** From mid-career a form arrives: stay with the operating company or move to AT&T Communications or Long Lines. The choice colours the last three tours' mail and the epilogue and changes which NPCs are friendly | Where: `data/companies.py` already carries the 21-company table and the seven holding groupings with verified/unverified flags; `Career.assignment`; command `assignment` in `screens/turnover.py`. E&O chapter 1 is the source for "AT&T Communications drew staff from BOCs, General Departments and Long Lines". **How individual craft were actually told is not sourced here**; mark the form and the process as the simulation's own. |
| A8 | P2 | Causality and overlapping systems (A5, A7) | **Root-cause cases across reports.** A bad carrier channel bank, a miscrossed frame pair, or a failing trunk causes three to five reports across a tour. Finding the shared cause clears them with one action | Where: extend the sheath pattern already in `plant.py`/`cable.py`: add `RootCause` objects to `ReportDesk` that spawn member reports; `report show` prints "see also"; `lmos` command lists the cluster once the `frame` qualification is held. State: `save._plant_out` extended. Commendation: C2. |
| A9 | P2 | Trouble verification and transient troubles (E&O 13.2.3 B4); false dispatches (E&O) | **Retest before you close and the "cleared itself" outcome.** A share of reports test clean (already ~18% `NO_TROUBLE_SHARE`); add transients where the second MLT an hour later shows the fault is gone, to teach the difference between code 8 and a cleared transient | Where: `reports.TroubleReport` field `transient: bool`; `ReportDesk.record_test` returns a clean reading on retest; `loop_testing` seed is per line, so retests currently repeat exactly. A transient needs a time-based variation: seed by line plus tour-minute bucket. Document in `loop_testing` docstring, which says readings are deliberately stable. |
| A10 | P2 | Epistolary threads; fraud and CCIS (E&O B4); phreaking history (Lapsley, TAP; B4) | **A toll-fraud thread for the Toll qualification.** `tnds`/`traffic` show an anomaly (short-holding-time seizures on one trunk group) that turns out to be someone using in-band signalling. The finding goes to security by `mail`. Optional lore: a TAP issue in a tester's drawer (TAP ran to 1983, so it is period-correct) | Where: `data/shift_events.py` event type; `screens/tnds.py` and `screens/traffic.py` produce the anomaly row; `data/fraud.py` text. Keep it to detection and history; no tone tables or procedures. Cite E&O (in-band signalling until 1976, CCIS and "reduction of fraud" as a stated need) and label the plot as invented. Do **not** add anything that would work as instructions. |
| A11 | P2 | Replay and the player's mark on the world (Octalysis ownership B3; Her Story's layering B2) | **Legacy.** Finishing a career writes `legacy.json`; a new career begins with the previous player's notes in the predecessor's directory, and a new hire arrives to train | Where: `progression.py` (`Career.finished` handling, new `begin_new_career`), `screens/turnover.py::_end_career`, `filesystem.py` builds `/usr/users/<previous>` from the legacy; depends on C10 for notes. Command: `career new` in `screens/turnover.py`. This is the cheapest source of replay value in the plan. |
| A12 | P2 | Needs-driven NPCs; the world runs without you (A5) | **Who is on tonight.** Tours alternate day, evening and night; NPCs have shifts; `who`, mail and orderwire reflect it; some people only exist on nights | Where: `npc.Craft` gains `shifts: Tuple[str,...]`; `Switchroom` filters by `clock.now().hour`; `who` command filters. The `show_shift_briefing` already knows the hour (`_get_shift_hours`). |
| A13 | P2 | Layered control: free input, fixed arc (Zarf A3) | **Callbacks with two or three questions.** `report callback` becomes a short exchange (symptom detail, history, who is home) instead of one block. Each answer narrows the fault space | Where: `screens/bureau.py::_report_callback`; `data/callbacks.py` keyed by fault code and class of service; the `report` command's argument parser accepts `callback <n> <topic>`. Cost stays `COST_CALLBACK` (8 minutes) per question so asking is a choice. |
| A14 | P3 | Relatedness (SDT B3); competence by teaching | **The trainee.** After the middle of the career a new hire writes to you with questions; your answers (and how you handle their first reports) raise their outcome and your rapport | Where: new `Craft` entry; `shift._craft_reply`; outcome reported at handoff. Builds on A5 and A11. |
| A15 | P3 | Sound as diagnosis (the game already has `tone` and a report whose answer is a sound; B4 on in-band tones) | **More ear cases.** Reports described as hum, clicking, cross-talk, a "party line" voice | Where: `tones.py` already writes tone files; add `data/symptoms` entries and `report callback` lines; the answer is in the sound file the player opens. |
| A16 | P3 | Usage data finds difficulty spikes (Barth, Amp Hour B1) | **Local playtest log.** An opt-in log of per-tour numbers (time to first close, errors by fault type) that `tools/` can aggregate | Where: `bell_system.log` already rotates; add one structured line per tour end; `tools/playtest_summary.py` reads it. Never sent anywhere. |
| A17 | P3 | Hypnospace: a period OS is the product (B1) | **One more period surface per qualification.** Each new qualification adds one artefact that feels like the thing (a teletype tape, a COSMOS screen, a trunk status board) with its own tone, not just commands | Where: `screens/` mixins already do this; the rule is a design rule: do not ship a qualification without one surface a player would screenshot. |
| A18 | P3 | Meaningful choices per role (Pillars A6; R5) | **One verb per position.** For each of the 12 positions, one command or report type that only it has | Where: `data/positions.py` and `ROLE_QUALIFICATIONS` in `progression.py`; confirm with S1/S2 which positions are already distinct. |

## Part 3. Order of work, and what to leave alone

1. **Foundation (small, unlocks the rest):** C5 assists, C10 home save,
   C1 fading annotation, and the `Career` fields for `finds`, `groups`,
   `rapport`, `commendations`, `beats_seen`, `fault_sightings` in one
   `progression.py` change. That is one schema bump, tested once.
2. **The loop feels better:** C2 commendations, C6 tour goals, C3
   practicals.
3. **The story gets a spine:** A4 tours, A2/A3 finds and the predecessor,
   C4 regular arcs, A5 rapport. These share one data authoring effort; do
   them as a set so the arc can be read end to end.
4. **Depth:** C9 dispatch to a place, A8 root causes, A9 transients, A1
   practices, A6 ledger, A10 fraud thread, C11 ending.
5. **Replay:** A11 legacy, A14 trainee.
6. Leave alone: the onboarding, the 300 baud pacing, the write-the-wrong-
   close feedback, the no-score hints.

Rows that need a decision from Bill before work: A7 (how much of the
assignment story to invent), A10 (how close to phreaking to go), and R3/R5
(which depend on what S1 and S2 found in the events and positions).

## Part 4. Pillars

Five, each one a filter ("does this idea serve it, or can it be cut").

1. **The desk is a system you learn, not a menu you work through.** Rules
   are always the same (Design Lab), the manual is part of the world
   (Barth), and mastery is shown by doing something new, not by repeating
   something old (SDT, Chen). Test: could a player explain *why* it worked?
2. **Every report is a person, and the board remembers.** Customers come
   back with a history, the craft remember how you treated them, and
   consequences are shown quietly (Pope, Zarf, Green). Test: does this
   make the person on the other end of the line more specific?
3. **The Bell System is ending, and everyone in the building knows.** The
   13 tours are a countdown with a shape: build, crisis, relief, farewell.
   The sourced sadness of the period (UPI, E&O) is the engine of meaning
   (Octalysis epic meaning). Test: does it add to what January means?
4. **The machine is the story.** Lore is discovered by reading, searching
   and getting permissions, never by cutscene; the layers follow your
   promotions (Her Story, Orwell, Hypnospace). Test: could a player find
   it with `ls`, `cat` or `grep`?
5. **Friction is chosen, and it is always period.** Difficulty is a set of
   assists the player controls (SDT autonomy); the 300-baud, 7-bit,
   printed-manual texture stays because it is the setting (Zachtronics
   "nubbly"); and nothing historical is shown unless it is sourced or
   labelled as the simulation's own (`SOURCES.md`). Test: can the player
   turn it down, and can we say where it came from?

## Part 5. Authenticity guardrails for everything above

- New claim, new line in `SOURCES.md`: *verified in bundled document*,
  *externally sourced* (give the source and say what was not found) or
  *the simulation's own*. This document's sourced items are the E&O sections
  cited above and the external URLs in Part 1; its own inventions are every
  practice-sheet number (A1), the predecessor and all NPC arcs (A3, C4), the
  assignment process (A7), commendations (C2), the tour themes (A4), and any
  commitment figure that is not already in `reports.py`.
- Things the research could not source: Uplink design claims; the worldwide
  histogram in Zachtronics games; a CHM oral history; the real BSP numbering;
  how individual craft were assigned to companies; local weather. They stay
  out, or in as labelled invention.
- Unread, and so not leaned on: Lapsley's book, Csikszentmihalyi's 1990
  book, the Ryan et al. paper text, the BSTJ 61/6 articles themselves. If
  any of these becomes the basis of a row, read it first.
