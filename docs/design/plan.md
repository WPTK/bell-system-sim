# Master plan: gamifying bell-system-sim

Built from the three audits on this branch:

- `session-1-material-review.md` (S1): the written material and design intent.
- `session-2-playtest.md` (S2): the code and a playtest.
- `session-3-research-blueprint.md` (S3): outside research and a blueprint.

Status: **approved by Bill on 2 November 2026, with the recommended option
taken on each of the six decisions in section 8.** So A10 (assignment form)
is deferred and A11 (toll-fraud thread) is built last in phase 8, detection
only. Paths are
under `src/bell_system/` unless they start with `docs/`, `tools/` or
`tests/`.

## 0. What the three agree on

- Fun-mode `mlt` hands over the answer, so there is nothing to decide.
- A sign-off unlocks screens to read, not things to do.
- The 13 tours are the same tour; only board depth and weather change.
- The story is static and the memo's audit never arrives.
- The docs describe a different game.

What to keep as it is: the first tour with one report and Halloran on the
wire, hints that cost no score, the wrong-close debrief that quotes your
own readings, the wet-cable cluster (S2 calls it the best mechanic), the
`moo` payoff, `training unix`, and the 300-baud look (see C28).

## 1. Pillars

Five filters. An idea that fails one is cut. S3 Part 4 is the source;
this is the short form.

1. **The desk is a system you learn.** The rules never change under you.
   The manual is part of the world. You show mastery by doing something
   new, not by repeating something old. *Cut it if* a player can win
   without knowing why it worked.
2. **Every report is a person, and the board remembers.** Customers come
   back with a history. The craft remember how you treated them.
   Consequences are shown in someone's voice, without a lecture. *Cut it
   if* it leaves the person on the line vaguer.
3. **The Bell System is ending, and everyone in the building knows.** The
   13 tours are a countdown with a shape: build, crisis, relief, farewell.
   *Cut it if* it adds nothing to what January means.
4. **The machine is the story.** Lore is found with `ls`, `cat` and
   `grep`, and each sign-off opens the next layer. No cutscenes. *Cut it
   if* a player could not find it that way.
5. **Friction is chosen, and it is period.** Difficulty is a set of
   assists the player controls. The 300 baud and the printed manual stay
   because they are the setting. Nothing historical appears unless it is
   sourced or marked as the simulation's own. *Cut it if* the player
   cannot turn it down, or we cannot say where it came from.

## 2. The rows

One table per kind. IDs are new and stable; the Sources column maps each
row back to the audits (S1 §3, S2 §8, S3 Part 2, with the audit's own
priority in brackets where it differs). **P** is this plan's priority:
P1 shapes the first hours or fixes a visible lie, P2 shapes the middle, P3
is polish. **Pil** is the pillar. **Ph** is the build phase (section 5).
Priority is not order; order is the phase.

### Remove

| ID | Row | Sources | P | Pil | Ph | Files | Acceptance test | Issue |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| **R1** | Fake "customers restored / revenue recovered" text on NOC ticket resolve | S2 §8 P1 Remove; S2 §1.4 | P1 | 5 | 0 | screens/tickets.py | `trouble resolve` prints no customer count or dollar figure, and never says EXCEEDED TARGET when the duration is over target. | in flight |
| **R2** | Stale docs: 2.0 manual, `--tutorial`, seven phantom commands | S1 §3.1 P1; S1 §1.4 | P1 | 5 | 0 | docs/manual.txt, docs/overview.md, docs/faq.md, docs/command_reference.txt | No `--tutorial` and no "Version 2.0" in docs/; a test checks that every command the docs name is in the dispatch table. | in flight |
| **R3** | Fun-mode `mlt` and a correct dispatch name the fault | S1 §3.2 P1 (row 1); S2 §8 P1 (row 4); S3 R1 P1 | P1 | 1 | 2 | screens/testing.py, loop_testing.py, reports.py, data/hints.py, data/man_pages.py | In fun, from a fault type's fifth sighting, `mlt` prints no "System reads this as" or "Dispatch to" line and a correct dispatch message does not contain the fault name (both appear today). | #5 |
| **R4** | Boilerplate base events in `data/shift_events.py` (fixed EV ids, wrong city) | S1 §3.1 P1; S3 R3 P2 | P1 | 3 | 4 | data/shift_events.py, screens/shift.py | No fixed base event ids remain; a test shows tour 1 and tour 7 draw different events and none names a city other than the player's office. | #6 |
| **R5** | Redundant hint channels: ambient `_HINTS` and the default `Next:` suffix | S1 §3.1 P2; S1 §2.4 | P2 | 1 | 6 | npc.py, settings.py | In a scripted 13-tour run, after the first closed report there is no `Next:` line and no ambient MLT-reading message; `game.prompts on` restores the line. | #7 |

### Change

| ID | Row | Sources | P | Pil | Ph | Files | Acceptance test | Issue |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| **C1** | Age every pending report on shift minutes, not only when worked | S2 §8 P1 (row 1); S2 §1.6 | P1 | 1 | 0 | reports.py, screens/shift.py | Sixteen shift hours of `sleep` on a board of 9 leaves reports past commitment. | in flight |
| **C2** | Field crews return on the shift clock | S2 §8 P1 (row 2); S2 §1.1 | P1 | 1 | 0 | field.py, screens/bureau.py | `shift` after a dispatch shows a return time in shift terms and `sleep` advances it. | in flight |
| **C3** | Zero work is not EXCELLENT; `handoff relieve` needs minimum work | S2 §8 P1 (row 3); S2 §1.8 | P1 | 1 | 0 | progression.py, screens/turnover.py | Thirteen `handoff relieve` with no work does not end EXCELLENT and the first relieve is refused. | in flight |
| **C4** | Split difficulty into named assists; fun counts missed commitments, softer | S3 C5 P1; S2 §8 P1 (row 1, last clause); S2 §4 | P1 | 5 | 1 | settings.py, progression.py | Each assist overrides its profile value, `set` lists departures, and with the commitments assist on, fun counts misses at the reduced weight (test in tests/test_settings.py). | #8 |
| **C5** | One Career schema bump for every new field, and `offer_available` | S3 Part 3 step 1 | P1 | 1 | 1 | progression.py, save.py | An old `career.json` loads; the new fields (`fault_sightings`, `commendations`, `finds`, `groups`, `rapport`, `beats_seen`, `practicals_passed`, `assignment`, `Difficulty.annotation_sightings`) default and round-trip. | #9 |
| **C6** | Save what the player writes (home overlay and `moo.scores`), 64 KB cap | S2 §8 P2; S3 C10 P2; S2 §6 | P2 | 4 | 1 | save.py, filesystem.py | A file written with `echo > ~/note` and the moo scoreboard survive a restart; a write past 64 KB is refused with a message. | #10 |
| **C7** | Make the qualification ladder reachable in 13 tours | S2 §1.7; S2 §8 P2 (competence tracks); S3 Part 1 C2 | P1 | 1 | 1 | progression.py, tools/index_calibration.py | Re-measured after Phase 0: a skill-0.9 craft bot signs off all six by tour 13 and a skill-0.6 bot does not reach Toll (bars are a proposal). | #11 |
| **C8** | Fading reading notes in fun, counted per fault type | S3 C1 P1; S1 §3.2 P1 (row 1) | P1 | 1 | 2 | screens/testing.py, loop_testing.py, data/trouble.py | Fun shows a one-line reading note on sightings 1-2, the crew class only on 3-4, numbers only after; craft shows no note; the count survives a restart. | #12 |
| **C9** | First report teaches: the customer says one thing, the pair another | S1 §2.4 (1); S1 §3.2 P2 (FIRST_TOUR) | P2 | 1 | 2 | reports.py, screens/guidance.py, data/trouble.py | The first report of a new career has symptom text that does not match its fault class, and Halloran has the player `report callback` before `mlt` (test_guidance). | #13 |
| **C10** | Each sign-off after Loop adds a verb that changes the board | S1 §3.2 P1 (row 2); S1 §1.1 | P1 | 1 | 3 | screens/frame.py, screens/remote.py, screens/trunks.py, screens/toll.py, data/man_pages.py | For each of the five sign-offs there is a command that changes `ReportDesk` state, refused before the sign-off and working after it, and listed in `qual`. | #14 |
| **C11** | Qualification practical: `qual take <key>` after the count floor | S3 C3 P1; S3 R4 P2 | P1 | 1 | 3 | screens/practical.py (new), data/practicals.py (new), screens/session.py, screens/bureau.py, terminal.py | Past the floor the sign-off is withheld until `qual take` passes; a failed attempt says what was missed; passes are saved. | #15 |
| **C12** | Point at `cosmos jumper` when the MLT cannot tell CO_EQUIP, FCG, NONE apart | S2 §8 P2; S2 §1.3 | P2 | 1 | 2 | screens/guidance.py, data/hints.py | On an ambiguous craft reading, `report next` and `hint` name the frame lookup once the player holds the frame sign-off. | #16 |
| **C13** | KPIs: MTTR, commitments met %, first-time-right dispatch %, repeat rate, backlog age; per-tour index; PROVISIONAL label under 5 closes; board-cleared meter | S2 §4; S2 §8 P1 (row 6) and P2 (last row); S1 §3.2 P2 (index) | P1 | 1 | 5 | progression.py, reports.py, screens/bureau.py, screens/turnover.py | `qual` shows the five KPIs and a per-tour index; the label reads PROVISIONAL until 5 closes; a scripted career gives the expected KPI values. | #17 |
| **C14** | Commendations beside the index: named, earned, never lost | S3 C2 P1; S3 R2 P1 | P1 | 1 | 5 | progression.py, data/commendations.py (new), screens/guidance.py, screens/bureau.py | Handoff prints commendations earned that tour, `qual` lists all, and a perfect tour earns "first clean tour" once. | #18 |
| **C15** | Tour goals on the briefing, struck at handoff | S3 C6 P1 | P1 | 1 | 4 | screens/shift.py, screens/turnover.py, data/tours.py | The briefing lists 2-3 goals from tours.py; handoff prints each as met or missed; goals never change the index. | #19 |
| **C16** | Regulars get a multi-tour arc with a resolution before 1 January | S3 C4 P1; S1 §3.2 P2; S2 §8 P2 | P1 | 2 | 7 | data/regulars.py, reports.py, screens/bureau.py, screens/records.py | Each of the four regulars has beats on named tours; `custdb` shows the latest note; a table test shows all four end resolved or abandoned by tour 13. | #20 |
| **C17** | Consequences in a person's voice: overdue chase, customer's second call, post-close call | S3 C8 P2; S1 §3.3 P2 (TELSAM); S2 §8 P1 (row 1) | P2 | 2 | 6 | npc.py, data/consequences.py (new) | A repeat shows the customer's second call in 1-2 lines by class of service; an overdue out-of-service report gets an mreyes line; a clean close can draw a call-back. | #21 |
| **C18** | NPC message order: arc beat, then board-driven, then random; tour windows | S1 §3.2 P2 (chatter); S3 R6 P3 | P2 | 2 | 6 | npc.py, data/tours.py | A message tagged for tours 5-8 never appears on tour 2; with a beat due, the beat is picked over the random pool. | #22 |
| **C19** | Netnews advances one item per tour | S2 §8 P2; S2 §6 | P2 | 3 | 4 | screens/games.py, data/tours.py | `readnews` on tour 1 and tour 9 lists different items, and no item is dated after the tour's date. | #23 |
| **C20** | Four desks play differently: one verb and one pressure each (repair, office, NOC, special services) | S1 §3.2 P2 (positions); S2 §8 P2 (positions); S3 R5 P3, A18 P3 | P2 | 1 | 9 | data/positions.py, screens/position.py, special_services.py, screens/tickets.py, screens/remote.py | Each of the four has a command only it can use and a pressure only it feels (NOC: a triage queue on the clock; SARTS: a repair verb for a failing circuit); test_position_differences covers them. | #24 |
| **C21** | Dispatch to a place, not only a force | S3 C9 P2; S1 §4 (3) | P2 | 1 | 8 | reports.py, loop_testing.py, cable.py, data/man_pages.py | `report dispatch N <force> <section>` repairs on the right section and returns the crew's finding on the wrong one; the old form still works in fun. | #25 |
| **C22** | Callbacks with two or three questions, each costing a callback | S3 A13 P2; S2 §1.3 | P2 | 2 | 8 | screens/bureau.py, data/callbacks.py (new) | `report callback N <topic>` answers one question for COST_CALLBACK and the answer narrows the fault set in the test. | #26 |
| **C23** | The ending reads the career (arcs, finds, rapport, commendations, assignment) | S2 §8 P1 (row 5); S3 C11 P2; S1 §2 | P1 | 3 | 10 | screens/turnover.py, npc.py | A table-driven test gives four career shapes four different epilogues. | #27 |
| **C24** | Soften the "qualification governed what you could touch" claim; record the code 5/8 simplification | S1 §4 caveats | P2 | 5 | 1 | README.md, SOURCES.md, progression.py | README states qualification as the simulation's mechanic, and SOURCES.md has a row for the 5/8 simplification. | #28 |
| **C25** | `--simple`: rename it as a Unix sandbox or give it roles | S1 §3.1 P2; S2 §1.5, §8 P3 | P3 | 5 | - | simple_terminal.py, cli.py, README.md | README describes `--simple` as what it is. | #43 |
| **C26** | Backlog past board depth: a "view all" aged list | S2 §7; S2 §8 P3 | P3 | 1 | - | screens/position.py | With 20 pending, `report all` lists every report by age. | #43 |
| **C27** | SHIFT-END becomes a soft stop: relief arrives | S2 §8 P3 | P3 | 1 | - | screens/shift.py | Past the end of the tour a relief NPC takes the board. | #43 |
| **C28** | Time the first tour; if dead time after dispatch is over 60 s, skip pacing for tables on tour 1 | S1 §2.2, §3.2 P1; S3 Part 3 (6) | P3 | 5 | - | terminal.py, settings.py | A timed first tour is on record; the pacing change ships only if it was over 60 s. | #43 |
| **C29** | Four-band results H / O / L / U beside or instead of the index labels | S1 §3.2 P2; S1 §4 (14) | P3 | 5 | - | progression.py | The handoff shows the band; no existing label disappears without a docs update. | #43 |
| **C30** | Re-sign position notes by the right people | S1 §3.1 P3 | P3 | 2 | - | data/homes.py | Each note is signed by someone who would have written it, or the mismatch is stated in the module. | #43 |
| **C31** | Fix the TSPS `status` error | S2 §1.4, §7 | P3 | 5 | - | screens/tsps.py | `tsps status` prints a panel in a fresh career. | #43 |
| **C32** | Priority classes: doctor and hospital lines carry tighter commitments | S3 C12 P3 | P3 | 2 | - | reports.py | A hospital PBX report has a shorter commitment than a home line, labelled as the simulation's own figure. | #43 |
| **C33** | Severity weighting for wrong closes (FEMF closed NTF costs more than cosmetic) | S1 §4 (20) | P3 | 1 | - | progression.py | A wrong close on a FEMF loses more index than a wrong close on an OPEN. | #43 |

### Add

| ID | Row | Sources | P | Pil | Ph | Files | Acceptance test | Issue |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| **A1** | Thirteen tour definitions with dates, themes, kinds and set pieces | S1 §3.3 P1 (calendar); S3 A4 P1, C7 P2; S2 §5 | P1 | 3 | 4 | data/tours.py (new), screens/shift.py, screens/turnover.py, npc.py | tours.py holds 13 entries with unique themes, dates matching `clock` (tour 13 = 31 Dec), and every beat tagged sourced or the simulation's own; `shift` on tour 5 shows tour 5's briefing. | #29 |
| **A2** | The audit: at tour 13, dispositions are audited and open reports pass "with your name on them" | S1 §3.3 P1; S2 §5, §8 P1 (row 5); S3 C11 | P1 | 3 | 4 | screens/turnover.py, npc.py | Tour 13 prints an audit whose counts match `report closed` and the open board; a zero-work career fails it. | #30 |
| **A3** | The Practices binder in `/usr/bsp`: tables the player applies | S3 A1 P1 | P1 | 1 | 2 | data/practices.py (new), filesystem.py, data/hints.py | `ls /usr/bsp` is not empty after tour 1; every sheet carries a header saying its number is the simulation's own; hint level 3 cites a sheet. | #31 |
| **A4** | Finds and fragments: `finds`, and files only `grep` reveals | S3 A2 P1 | P1 | 4 | 7 | filesystem.py, screens/shell.py, screens/finds.py (new), terminal.py | Reading a fragment file records it; `finds` lists titles by number; a fragment appears in `grep` results only once its tour is reached. | #32 |
| **A5** | The predecessor thread, gated by groups; resolve `mreyes-root` at 03:47 | S3 A3 P1; S1 §3.3 P2 (sulog); S2 §8 P2 (sulog, Alvarez) | P1 | 4 | 7 | filesystem.py, data/homes.py, screens/shell.py | Each of the first five sign-offs makes at least one new file readable; the sulog entry is explained by a file readable only after sign-off 4 (test_things_to_find). | #33 |
| **A6** | Rapport with the other craft, and arcs for Sandoval, Alvarez, Reyes | S3 A5 P1 (moved to P2); S1 §3.3 P2 (arcs) | P2 | 2 | 6 | npc.py, screens/shift.py | Rapport is clamped 0-5 with one gain per person per tour; at the threshold one favour fires, once. | #34 |
| **A7** | Root-cause cases across reports and trouble patterning; Marker 2 is the first | S3 A8 P2; S1 §3.3 P2 (Marker 2, patterning); S2 §8 P2 (cascades) | P2 | 4 | 8 | reports.py, cable.py, screens/plant.py, screens/bureau.py, filesystem.py | A planted cause spawns 3-5 member reports, `report show` prints "see also", one action clears them, and Marker 2 fires on tour 9 or 10 in the scripted run. | #35 |
| **A8** | Cascades with a clock; pressure alarms before reports | S2 §8 P2 (cascades); S1 §3.3 P2 (pressure) | P2 | 1 | 8 | cable.py, weather.py, screens/shift.py | An unrepaired wet binder adds a pair per shift hour, faster in rain; a pressure alarm appears before the first report in a seeded run. | #36 |
| **A9** | Transient troubles and retest (no new close code) | S3 A9 P2; S1 §3.3 P2 (hold for retest) | P2 | 1 | 8 | reports.py, loop_testing.py, save.py | A transient report reads faulty on the first `mlt` and clean on one an hour later; closing it 8 after the retest is not a repeat. | #37 |
| **A10** | The assignment form: stay with the operating company or move to AT&T | S3 A7 P2 | P2 | 3 | 10 | screens/turnover.py, progression.py, data/companies.py | Pending decision D5. If built: `assignment` records a choice and the epilogue reflects it. | #38 |
| **A11** | A toll-fraud thread for the Toll sign-off (detection and history only) | S3 A10 P2 | P2 | 4 | 8 | data/fraud.py (new), screens/tnds.py, screens/traffic.py | Pending decision D6. If built: `traffic` shows the anomaly, `mail` reports it, nothing in the text works as instructions. | #39 |
| **A12** | Who is on tonight: NPC shifts, `who`, mail and order wire follow | S3 A12 P2 | P2 | 2 | 6 | npc.py, screens/unix.py | On a night tour `who` omits day-only staff and the order wire only offers people on shift. | #40 |
| **A13** | Legacy: a finished career seeds the next, and `career new` | S3 A11 P2; S3 R7 P3 | P2 | 4 | 11 | progression.py, filesystem.py, screens/turnover.py | A second career finds the first player's notes in the predecessor's home directory. | #41 |
| **A14** | The tour ledger against the office (simulated peers) | S3 A6 P2; S1 §3.3 P3 (league table) | P2 | 1 | 11 | tools/index_calibration.py, data/peers.py (new), screens/turnover.py | Handoff prints MTTR and first-pass accuracy with their place among peers, labelled the simulation's own. | #42 |
| **A15** | The trainee | S3 A14 P3 | P3 | 2 | - | npc.py | After tour 6 a new hire writes and the outcome shows at handoff. | #43 |
| **A16** | More ear cases and cadence siblings (ring-back vs busy, reorder vs all-trunks-busy) | S1 §3.2 P3; S3 A15 P3 | P3 | 1 | - | data/signaling.py, tones.py, data/symptoms | Two new report types whose answer is a sound file. | #43 |
| **A17** | `training mlt` and `training network` | S1 §3.2 P3, §3.3 P3 | P3 | 1 | - | data/primer.py, screens/records.py | `training mlt` runs in the same voice as `training unix`. | #43 |
| **A18** | Clean-work beats from crews | S2 §3, §8 P3 | P3 | 2 | - | field.py, npc.py | A fast correct dispatch draws one line from the crew. | #43 |
| **A19** | Acronym and work-order-code puzzles that use BSP text | S2 §8 P3 | P3 | 1 | - | data/trouble.py, bsp | A crew will not roll without a code that is in a sheet. | #43 |
| **A20** | Local playtest log and summary tool | S3 A16 P3 | P3 | 5 | - | tools/playtest_summary.py (new) | One structured line per tour end; the tool aggregates them; nothing is sent anywhere. | #43 |
| **A21** | Mine the unused `attached_assets/` (BSRS 104.011, SD_26030-01 and others) | S1 §5 | P3 | 5 | - | SOURCES.md, data/ | Marker 2 text is checked against SD_26030-01 before A7 cites it. | #43 |
| **A22** | Moo rivalry: Halloran reacts across tours | S2 §8 P3 | P3 | 2 | - | screens/games.py, npc.py | Beating Halloran changes his next two order-wire lines. | #43 |
| **A23** | One screenshot-worthy period surface per new sign-off (design rule) | S3 A17 P3 | P3 | 5 | - | screens/ | Each new sign-off ships with a named surface in its PR. | #43 |

P3 rows have no phase and no issue of their own. They live as a checklist
in #43.

## 3. Where the audits disagree

| Topic | What each said | Pick | Why |
| --- | --- | --- | --- |
| How fun stops naming the fault | S1: fade by sign-off. S2: stop echoing the fault on dispatch. S3: fade by sightings of each fault. | S3's per-fault count, S1's middle step (crew class only), S2's no-echo on dispatch (R3, C8). | A count teaches every fault twice however fast sign-offs come. |
| What a sign-off gives | S1: a verb. S2: more tracks (speed, streak). S3: a practical. | Verb as the reward, practical as the gate, close count stays as the floor, no new tracks (C10, C11, C7). | The practical tests the verb; a track is a second counter to keep honest. |
| Tour dates | S1: snap the stride to the holidays. S3: keep it, script each tour. | Keep the four-day stride (A1). | `clock.py` documents it as the simulation's own, and both holidays fall between two tours anyway (section 6). |
| Hold for retest | S1: a third close code. S3: a transient flag and no new code. | S3 (A9). | Two close codes are what the README teaches and what E&O counts (S1 §4, row 18). |
| What to save | S2: scoreboard, `ed` files, news position, mail. S3: a 64 KB home overlay. | S3's overlay plus `moo.scores` (C6). News position follows the tour (C19). | Anything that is a function of the tour needs no saving. |
| Status-only plant screens | S1: remove or hide about 5,400 lines. S2: four dashboards with one-command wins, no deletion. | Keep them. Give them a use through C10 and C20. | S1's count was a hypothesis; the screens are the setting. |
| The 300-baud default | S1: faster on tour 1. S3: leave alone. | Leave it, and time the first tour (C28, P3). | Nobody has timed it, and the Model 43 rate is sourced in `SOURCES.md`. |
| The twelve desks | S1: four real lenses, rest become transfers. S2: each gets one verb. S3: one verb each, P3. | Four lenses first, the rest untouched, no relabel (C20, D4). | S1 and S2 agree on four; relabelling changes what the README promises. |
| Ending | S1: the audit. S2: a tour-13 incident, audit and epilogue. S3: the ending reads flags. | Audit early (A2, phase 4). Epilogue late (C23, phase 10). | The audit needs only existing dispositions. The epilogue needs rapport, finds and arcs first. |
| Scoring | S1: H/O/L/U bands. S2: per-tour index, PROVISIONAL label. S3: commendations. | S2 and S3 (C13, C14). Bands go to P3 (C29). | Bands rename labels that tests and docs already use. |
| Events | S1: a dated script replaces `shift_events`. S3: generate them from board state. | `data/tours.py` for the set pieces; generated filler between (R4, A1). | One dated beat per tour, the rest from the board. |
| Marker 2 | S1: a scripted payoff. S3: a general root-cause case. | One framework; Marker 2 is its first case (A7). | One mechanism to test. |

## 4. Corrections to the audits

1. **S2's "the seven" finding is dropped** (S2 §0 item 5, §1.8, and the
   gap-map row). Halloran's "Whichever of the seven you end up at" (`npc.py`
   `last_word`) means the seven regional holding companies, listed in
   `RBOCS` in `data/companies.py`. It does not contradict the twelve
   positions. The rest of S2's ending finding stands (C23).
2. **S1's "Christmas-eve overload" has no source.** S1's own §4 row 11
   says E&O names *Christmas Day*. Tour 11 is 24 December. The beat is
   the preparation: controls go on tonight and must be taken off
   (E&O Table 5-1 footnote, as S1 quotes it), not an overload on the eve.
3. **S2's close counts and "Toll never reached" were measured before the
   clock fix.** C7 re-measures after phase 0.
4. **S1's "about 5,400 lines" of status screens is S1's hypothesis.** S2
   confirmed four dashboards, not the lot.
5. **Dates are pinned in section 6.** Several in the audits were arithmetic
   or unsourced.

## 5. Phases

Order is forced by shared files, not by value. These are the files that
collide most; each lists the phases that change it.

| File | Phases that change it, in order |
| --- | --- |
| `progression.py` | 0, 1, 5, 10, 11 |
| `reports.py` | 0, 2, 5, 7, 8 |
| `screens/turnover.py` | 0, 4, 5, 10, 11 |
| `screens/shift.py` | 0, 4, 6, 8 |
| `npc.py` | 4, 6, 10 |
| `screens/bureau.py` | 0, 3, 5, 7, 8 |
| `filesystem.py` | 1, 2, 7, 8, 11 |
| `screens/guidance.py` | 2, 5 |
| `screens/records.py` | 7 |
| `screens/shell.py` | 7 |
| `data/man_pages.py` | 2, 3, 8 |
| `terminal.py` | 3, 7 |
| `SOURCES.md` | 1 |

`SOURCES.md` and `data/man_pages.py` take small appends from nearly every
phase. Those are the only collisions allowed between parallel phases, and
they merge cleanly if each PR rebases on main before it lands.

### Order at a glance

| Wave | Phases | Note |
| ---: | --- | --- |
| 1 | 0 | In flight. |
| 2 | 1 | Alone. |
| 3 | 2, 3, 4 | Parallel. Disjoint except the `data/man_pages.py` append. |
| 4 | 5, 6 | Parallel. 6 can start when 4 has merged. 9 may start any time after 3. |
| 5 | 7 | After 5. 7a and 7b run in parallel. |
| 6 | 8 | After 6 and 7 (both change `screens/shift.py` or `reports.py`). PRs in order. |
| 7 | 10 | After 6, 7 and 8. |
| 8 | 11 | After 10. |

Phase 9 runs beside waves 4 to 7 if nobody else touches
`screens/position.py`, `special_services.py` or `screens/tickets.py`.
The long path is 0, 1, 4, 5, 7, 8, 10, 11. Everything else fits beside it.

### Gamify phase 0: Clocks, scoring and docs

In progress in two fix sessions. Nothing here is filed as an issue.

- **Rows:** R1, R2, C1, C2, C3
- **Starts after:** -
- **Can run alongside:** -
- **PRs:** Two PRs already open or in flight.

### Gamify phase 1: Foundation

One schema bump so the rest of the plan can add fields without touching `progression.py` again. Assists, saved player files, a ladder that can be climbed.

- **Rows:** C4, C5, C6, C7, C24
- **Starts after:** Phase 0 merged
- **Can run alongside:** Nothing. Everything else waits for it.
- **PRs:** One PR: C4, C5, C6, C7, C24.

### Gamify phase 2: The reading ramp

Fun mode stops handing over the answer. The Practices binder gives the player something to look up instead.

- **Rows:** R3, C8, C9, C12, A3
- **Starts after:** Phase 1
- **Can run alongside:** Phases 3 and 4. The one shared file is `data/man_pages.py` (see below).
- **PRs:** Two PRs, in order. 2a: R3, C8, C9 (testing, loop_testing, trouble, reports). 2b: A3, C12 (practices, filesystem, guidance, hints).

### Gamify phase 3: Qualification verbs and practicals

A sign-off adds a verb that changes the board, and a practical proves you can use it.

- **Rows:** C10, C11
- **Starts after:** Phase 1
- **Can run alongside:** Phases 2 and 4. Shared with phase 2: `data/man_pages.py`, append-only here.
- **PRs:** Two PRs, in order. 3a: C10 (frame, remote, trunks, toll). 3b: C11 (practical, bureau, terminal).

### Gamify phase 4: Tours, calendar and the audit

Thirteen different tours on a real calendar, and the audit that the divestiture memo promises.

- **Rows:** R4, C15, C19, A1, A2
- **Starts after:** Phase 1
- **Can run alongside:** Phases 2 and 3 (no shared files).
- **PRs:** Two PRs, in order. 4a: R4, A1, C15, C19. 4b: A2. Both touch `turnover.py` and `npc.py`.

### Gamify phase 5: The credit side

Credit as well as penalty. KPIs and commendations.

- **Rows:** C13, C14
- **Starts after:** Phases 2, 3 and 4
- **Can run alongside:** Phase 6, and phase 9 once phase 3 has merged.
- **PRs:** One PR: C13, C14 (both change `progression.py`).

### Gamify phase 6: People

Voices, rapport, consequence, who is on tonight. One owner for `npc.py`.

- **Rows:** R5, C17, C18, A6, A12
- **Starts after:** Phase 4
- **Can run alongside:** Phases 5, 7 and 9 (no shared files).
- **PRs:** One PR: R5, C17, C18, A6, A12. Split in order if it runs large.

### Gamify phase 7: The machine as story

Finds, the predecessor, and the regulars. Two disjoint PRs.

- **Rows:** C16, A4, A5
- **Starts after:** Phase 5 (for `reports.py` and `bureau.py`); phase 2 (for `filesystem.py`)
- **Can run alongside:** Phases 6 and 9.
- **PRs:** Two PRs, parallel. 7a: C16 (regulars, reports, bureau, records). 7b: A4, A5 (filesystem, shell, finds, homes).

### Gamify phase 8: Board cases

Cases that cross reports: root causes, cascades, transients, dispatch to a place.

- **Rows:** C21, C22, A7, A8, A9, A11
- **Starts after:** Phases 6 and 7
- **Can run alongside:** Phase 9 only.
- **PRs:** Three PRs, in order, all in `reports.py`. 8a: A9, C21. 8b: A7, A8. 8c: C22, and A11 if D6 says build.

### Gamify phase 9: Positions

Four desks that play differently. NOC first.

- **Rows:** C20
- **Starts after:** Phase 3 (for `screens/remote.py`)
- **Can run alongside:** Phases 5, 6, 7 and 8, if none of them touch `screens/position.py`, `special_services.py` or `screens/tickets.py`.
- **PRs:** One PR per desk, in order, NOC first: C20.

### Gamify phase 10: The ending

The epilogue reads what you did.

- **Rows:** C23, A10
- **Starts after:** Phases 6, 7 and 8
- **Can run alongside:** Phase 9 may still be running.
- **PRs:** One PR: C23. A10 only if D5 says build.

### Gamify phase 11: Replay and ledger

A finished career seeds the next, and the ledger against the office.

- **Rows:** A13, A14
- **Starts after:** Phase 10
- **Can run alongside:** Nothing.
- **PRs:** Two PRs, in order. 11a: A13. 11b: A14. Both touch `turnover.py`.


## 6. Dates

Every date, with where it stands under the `SOURCES.md` rules: *repo*
(stated in the code or a bundled document), *derived* (calendar
arithmetic), *external* (needs a `SOURCES.md` row before text relies on
it), or *own* (the simulation's choice).

| Date | What | Status |
| --- | --- | --- |
| 14 Nov 1983 (Mon) | Career epoch, 48 days before divestiture | Repo: `clock.py`. Weekday derived. |
| 1 Jan 1984 | Divestiture takes effect | Repo: E&O, as `clock.py` quotes it. |
| Tour dates below | 14 Nov plus 4 days per tour; tour 13 pulled back to 31 Dec | Own: `clock.py` calls the stride the simulation's own. |
| 24 Nov 1983 (Thu) | Thanksgiving | Derived: the Thursdays that month are 3, 10, 17 and 24, and the rule is the fourth. The rule is outside the bundled documents, so it needs a `SOURCES.md` row (external) before any text says it. |
| 25 Dec 1983 (Sun) | Christmas Day | Fixed date; weekday derived. |
| 7-28 Aug 1983 | The AT&T strike | Already in `SOURCES.md` (`net.misc/88`). |
| 24 Aug 1982 | MFJ entered by Judge Greene | External (S3 cites a reference page). `SOURCES.md` has only "the 1982 decree". Add a row before use. |
| 19 Dec 1983 | UPI, "Jan. 1, 1984: AT&T D-Day" | External (S3 via a researcher; the page returned 403 to a plain request). Not in `SOURCES.md`. Paraphrase only. Cannot appear before tour 10 (20 Dec). |
| May 1980 | Mount St. Helens call surge; Mother's Day and Christmas Day reroutes | Repo: E&O printed pp. 179-180, as S1 reads it. Not re-read for this plan. |
| 14 Nov 1983 weather | Any claim about the real weather | Not used. `SOURCES.md` records that it was looked for and not found. |
| TAP to 1983; 2600 from 1984 | Phreaking history | Snippet only (S3). 2600 starts after the game's last day. Nothing dated is used in A11 until sourced. |

| Tour | Date | Day | Days left | Note |
| ---: | --- | --- | ---: | --- |
| 1 | 14 Nov 1983 | Mon | 48 |  |
| 2 | 18 Nov 1983 | Fri | 44 |  |
| 3 | 22 Nov 1983 | Tue | 40 | Thanksgiving (Thu 24 Nov) falls after this tour |
| 4 | 26 Nov 1983 | Sat | 36 | First tour after Thanksgiving |
| 5 | 30 Nov 1983 | Wed | 32 |  |
| 6 | 4 Dec 1983 | Sun | 28 |  |
| 7 | 8 Dec 1983 | Thu | 24 |  |
| 8 | 12 Dec 1983 | Mon | 20 |  |
| 9 | 16 Dec 1983 | Fri | 16 |  |
| 10 | 20 Dec 1983 | Tue | 12 | First tour on which a 19 Dec 1983 article can be mentioned |
| 11 | 24 Dec 1983 | Sat | 8 | Christmas Eve |
| 12 | 28 Dec 1983 | Wed | 4 | First tour after Christmas Day (Sun 25 Dec) |
| 13 | 31 Dec 1983 | Sat | 1 | Last day; pulled back from 2 Jan by `clock.py` |

Tours 4, 6, 11 and 13 fall on a weekend. `clock.py` already notes that a
craftsperson worked every day, so this is not a defect; A1 should not
write "Monday" copy for them.

## 7. Phase 0: in flight

Not filed as issues. Two fix sessions are doing these. R1, R2 and C1 to C3
stay in the table above so nothing is counted twice.

- Reports age on shift minutes, not only when worked (C1).
- Field crews return on the shift clock (C2).
- A career with zero work is no longer EXCELLENT, and `handoff relieve`
  requires minimum work (C3).
- The fake "28,943 customers / $257,288" text in `screens/tickets.py` is
  removed (R1).
- Stale docs fixed: `docs/manual.txt`, `docs/overview.md` (tutorial),
  `docs/faq.md`, `docs/command_reference.txt` (R2; issue #3, PR #4).

Two things to check when these land. C4 assumes missed commitments may not
yet count in fun; if phase 0 already does that, C4 shrinks. C17 assumes the
overdue chase from mreyes is not in phase 0.

## 8. Decisions for Bill

Six, each blocks the rows named. A recommendation is first.

1. **How far does fun mode fade?** (blocks R3, C8)
   - Recommended: to numbers only after a fault's fourth sighting, with an
     assist (`assist.annotate`) that keeps the notes for anyone who wants them.
   - Or stop at the crew class, so fun never fully removes a hint.
2. **Can the audit hurt?** (blocks A2, C23)
   - Recommended: it gives a verdict and shapes the epilogue. Nothing is
     lost and the career still ends on 31 December. This keeps the README's quiet tone.
   - Or a failed audit ends the career early.
3. **Do practicals gate sign-offs in fun mode too?** (blocks C11)
   - Recommended: yes, with `hint` free. The verbs in C10 mean nothing if the
     sign-off can be had by counting.
   - Or craft only, and fun keeps the count.
4. **Four real desks, or relabel the other eight?** (blocks C20)
   - Recommended: build four (repair, office, NOC, special services) and leave
     the other eight alone for now.
   - Or relabel the eight as transfers you may take after tour 3, as S1
     proposed. That changes what the README promises.
5. **The assignment form** (blocks A10)
   - Recommended: not now. The epilogue can use the company of the player's
     own office, which `data/companies.py` already sources.
   - Or invent a form offering the operating company or AT&T, marked as the
     simulation's own. How craft were actually told is unsourced.
6. **The toll-fraud thread** (blocks A11)
   - Recommended: build it last in phase 8, detection and history only, no
     tones and nothing that works as instructions, plot marked invented.
   - Or skip it and leave Toll with its verb and practical alone.

## 9. Tracking

- Milestones: "Gamify phase N: name", N = 0 to 11, one per phase above.
  Milestone 0 has no issues by design.
- Labels: `design`, `gamification`, `P1`, `P2`, `P3`, and one per pillar
  (`pillar: system`, `pillar: people`, `pillar: ending`, `pillar: machine`,
  `pillar: period`).
- One issue per P1 and P2 row outside phase 0 (38 issues). Each carries the ID,
  files, acceptance test and the phase it starts after.
- P3 rows: checklist in #43.
- A10 and A11 have issues but are blocked on D5 and D6.
