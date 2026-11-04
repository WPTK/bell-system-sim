# Difficulty curve: bell-system-sim

> **Status:** Draft, 2 November 2026, against `main` at 054be11 (phase 1 merged).
> **Links to:** `plan.md` (pillars section 1, phases section 5, decisions section 8), `narrative-bible.md`, `playtest-template.md`.
> **Source:** adapted from the difficulty-curve template in Donchitos/Claude-Code-Game-Studios (MIT), cut down to what this game has.

Every number below is read from the code (file named) or from the plan, or is
marked **guess**. A guess is a hypothesis for a scripted run or a playtest to
settle; none is a requirement.

## 1. Philosophy

**Accessible entry, optional depth, with difficulty serving the countdown.**
A new player can finish a career on Fun Simulation without knowing any
telephony; a player who wants the job as it was turns the assists up.
Across the 13 tours the load rises with the calendar (a deeper board, wetter
weather) rather than with a difficulty knob: `position.py` says "that is the
shape of getting good at something rather than a difficulty setting".

What the player is allowed to feel: confusion on tour 1 for no more than the
four steps Halloran walks through; frustration at a wrong close, once per
fault type, because the debrief quotes their own readings; dread at tour 13.
Not allowed: being stuck with no next move (`hint` is free, pillar 5) or
losing the career (anti-pillar 2). The cost of failure is index points, a
repeat call and some shift minutes, never the end of the career.

## 2. Difficulty axes

| Axis | What it is here | Systems | Player control |
| --- | --- | --- | --- |
| **Knowledge** (the main one) | What a reading means, which crew a fault needs, where the practice is written | `data/trouble.py`, `data/hints.py`, `/usr/bsp` (A3), the manual | Yes: `hint`, the annotation fade (`annotation_sightings`: fun 4, craft 0), the binder |
| **Time** | 480 minutes a tour; commitments of 480 (out of service) or 1440 (service affecting); each command and test costs minutes | `constants.py`, `reports.py` `COST_*`, `OUT_OF_SERVICE_COMMITMENT`, `SERVICE_AFFECTING_COMMITMENT` | Yes: `assist.commitment_slack` (fun +90, craft +0), `assist.commitments_count` |
| **Decision** | Which force to dispatch, in what order, when a cluster is one cable | dispatch, `field.py`, wet-cable clustering | Partly: C21 and C22 widen it later; the base is fixed |
| **Resource** | Five crews; one busy while out; a wrong dispatch costs 45 minutes. Outside plant jobs run 30 to 240 minutes (halved in #64: one lineman takes half the faults) | `field.py` `CREWS`, `COST_WRONG_DISPATCH` | No: fixed by the setting |
| **Pressure from others** | Interruptions as a share of commands: fun 0.06, craft 0.22 | `progression.py` `interruption_rate` | Via the profile only; not an assist yet |
| **Execution** | Typing at 300 baud. No timing or aim anywhere | `display.pacing` | Yes: `set display.pacing off` |

There is no execution axis by design (anti-pillar 5). An axis added later
needs a row here first.

## 3. The two profiles side by side

From `progression.DIFFICULTIES`. `assist.*` can override any row on its own.

| Setting | Fun Simulation | Craft ("I Hate Myself") | Assist |
| --- | --- | --- | --- |
| Measure before you close | not required | required | `assist.test_first` |
| Repeat chance on a wrong no-trouble close | 0.25 | 0.85 | `assist.repeat_reports` |
| Correct closes per qualification step | 3 | 12 | `assist.pace` |
| Penalty scale on the index | 0.7 | 1.0 | `assist.scoring` |
| Missed commitment (share of its 20 weight) | 0.25 | 1.0 | `assist.commitments_count` |
| Extra minutes on every commitment | 90 | 0 | `assist.commitment_slack` |
| Interruptions per command | 0.06 | 0.22 | none |
| Does `mlt` name the fault | yes | no | none (R3 and C8 change this in phase 2) |
| Reading-note sightings per fault type | 4 | 0 | `assist.annotate` arrives with C8 |

Index weights (both profiles): wrong disposition 55, repeat 35, missed
commitment 20, report left open past commitment 50. Bands: EXCELLENT from 95,
SATISFACTORY from 88, MARGINAL from 78. All [own].

## 4. The 13-tour axis

Dates and days left from `plan.md` section 6. Board depth is
`round(MAX_PENDING - 3 + 6 * share + CAREER_DEPTH * career_progress)` with
`MAX_PENDING = 9`, `CAREER_DEPTH = 2`, shown for a neutral desk
(`share = 0.5`); a heavier desk sits higher by up to three
(`screens/position.py`, `data/positions.py`). Wet is the chance that the
shift's weather regime is drizzle or worse, from `weather.py` `REGIMES` and
`WET_LEAN` leaned by `career_progress`; the weather then drifts hourly, so
this is the lean, not the day.

| Tour | Date | Days left | Board (neutral desk) | Wet regime | Rain or heavy | Shape (`kind`: theme, from `data/tours.py`) |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | 14 Nov | 48 | 9 (the player is held to 1 report, `FIRST_TOUR`) | 36% | 16% | Build: A new board |
| 2 | 18 Nov | 44 | 9 | 37% | 17% | Build: Records stay |
| 3 | 22 Nov | 40 | 9 | 39% | 18% | Build: Before the holiday |
| 4 | 26 Nov | 36 | 10 | 40% | 19% | Crisis: After the holiday (first tour after Thanksgiving) |
| 5 | 30 Nov | 32 | 10 | 41% | 20% | Build: Deferred work |
| 6 | 4 Dec | 28 | 10 | 43% | 21% | Relief: Weekend coverage |
| 7 | 8 Dec | 24 | 10 | 44% | 22% | Crisis: Pressure watch |
| 8 | 12 Dec | 20 | 10 | 45% | 23% | Build: Inventory for transfer |
| 9 | 16 Dec | 16 | 10 | 46% | 23% | Build: Close honestly |
| 10 | 20 Dec | 12 | 10 | 47% | 24% | Relief: The new owners |
| 11 | 24 Dec | 8 | 11 | 47% | 25% | Crisis: Christmas Eve |
| 12 | 28 Dec | 4 | 11 | 48% | 26% | Relief: The controls come off |
| 13 | 31 Dec | 1 | 11 | 49% | 26% | Farewell: The last day (the audit, A2) |

The board and weather numbers rise by about two reports and ten points of
rain probability across a career. That is gentle on purpose: the load that
makes tour 13 different from tour 1 should come from the calendar's beats
(`tours.py`, A1) and from what the player is by then expected to know, not
from a bigger board. The shape column is each tour's `kind` and `theme` in
`data/tours.py`; Marker 2 (A7, tour 9 or 10 in section 8) is not a tour kind.

### Fun against craft

Sign-offs need cumulative correct closes of `requires_reports * reports_per_qualification`.
`requires_reports` is 1, 2, 4, 6, 12 for Frame, Office, SCC, Trunk, Toll
(`progression.QUALIFICATIONS`).

| Sign-off | Fun | Craft | Earliest tour, 10 a tour | Earliest tour, 5 a tour |
| --- | ---: | ---: | --- | --- |
| Frame | 3 | 12 | fun 1, craft 2 | fun 1, craft 3 |
| Office | 6 | 24 | fun 1, craft 3 | fun 2, craft 5 |
| SCC | 12 | 48 | fun 2, craft 5 | fun 3, craft 10 |
| Trunk | 18 | 72 | fun 2, craft 8 | fun 4, craft 15 (not in 13) |
| Toll | 36 | 144 | fun 4, craft 15 (not in 13) | fun 8, craft 29 (not in 13) |

"10 a tour" is a round pace for reading the table. The calibration bot now
closes about 13 a tour (outside-plant jobs were halved for #64): at 90 in 100
it reaches Toll on craft in 100% of careers, median on tour 11, at 75 in 80%,
at 60 in 20% (`requires_reports` 12; ten let the 60 bot in 75% of the time).
That is a ceiling for a person. "5 a tour" is a **guess** for a careful first-time human; the last
measurement of human pace (2 to 7 closes a tour, S2) was taken before the
clock fix in PR 46 and plan section 4 item 3 says to re-measure. That is C7.

Read it as the plan intends: on Fun the whole ladder is reached by about tour
3 to 6, so the pull on tours 7 to 13 must be the calendar and the people,
not the next sign-off. On Craft the ladder is the spine of the career, and
Toll is for someone working very well (C7: a skill-0.9 craft bot signs off
all six by tour 13, a skill-0.6 bot does not reach Toll).

## 5. What the player knows at each stage

| When | Knows | Does not know yet |
| --- | --- | --- |
| Login | The date and the countdown (the banner), that this is UNIX, that `?` lists positions | What a report is; that `hint` exists |
| First report, minute 0 to 10 | `report`, `mlt`, `report dispatch`, `report close`; Halloran's four messages | Why the fault is what it is; the sign-off ladder |
| End of tour 1 | The loop of the job; the index; that `training unix` exists | What `man` and `/usr/bsp` are for; what a repeat is |
| Tours 2 to 3 | Fault types by name (fun: until sighting 5; craft: from the first); the first sign-off | Reading the `mlt` without a note; clusters |
| Tours 4 to 6 | A cluster is a cable; weather matters; two or three sign-offs and their verbs (phase 3) | Practicals; rapport; the audit |
| Tours 7 to 9 | The binder and the practicals; the regulars by name; finds | Marker 2; what the memo's audit is |
| Tours 10 to 12 | Most commands; the people's arcs | What happens on 31 December |
| Tour 13 | All of it. The audit counts what they did | Nothing the game withholds |

The "when" column assumes a Fun player at 5 to 10 closes a tour; a Craft
player is one to three tours behind on the ladder (section 4) and ahead on
fault names.

## 6. The order mechanics arrive

By phase in `plan.md` section 5. Phases 2, 3 and 4 run in parallel, so their
mechanics land together; what the player sees in order is set by when each is
unlocked, not by merge order.

| Phase | Mechanic | The player meets it | Method | Stakes at introduction |
| ---: | --- | --- | --- | --- |
| 0 | Reports age on shift minutes; crews return on the shift clock; zero work is not EXCELLENT | Tour 1 on, silently | The briefing's countdown and `shift` | Low |
| 1 | Assists, the saved home, a reachable ladder | At first `set`; ladder from tour 1 | `set`, the `qual` command | None |
| 2 | Fun names a fault for its first 2 sightings, the crew class only for the next 2, then numbers; the Practices binder `/usr/bsp` | Tour 2 to 3 (fun); tour 1 (craft, no naming) | A reading note that fades; a hint that cites a sheet | Low: a hint costs nothing |
| 3 | Each sign-off adds a verb that changes the board; `qual take` practical | First sign-off, tour 1 to 3 | Halloran's message; `qual` | Moderate: the practical can be failed and retaken |
| 4 | Thirteen briefings; tour goals; a dated news item per tour; the audit at tour 13 | Tour 2 on; the audit at 13 | The briefing and handoff | Low until tour 13 |
| 5 | KPIs, per-tour index, commendations | End of the first handoff | `qual`, handoff | Low: credit, never penalty |
| 6 | Voices, rapport, a customer's second call, who is on tonight | From tour 3 or 4 | write(1), `who` | Low: one favour per person |
| 7 | Finds, the predecessor files, the regulars' arcs | From the first sign-off on | `ls`, `cat`, `grep`, `finds` | None: optional |
| 8 | Dispatch to a section; callbacks with questions; root-cause cases; cascades; transients | Tour 7 on (guess) | `report dispatch N force section`, `report callback N topic` | Moderate: costs minutes |
| 9 | Four desks that play differently | When the player picks a desk | `shift`, the role picker | Moderate |
| 10 | The ending reads the career | Tour 13 | Handoff | The weight is emotional |
| 11 | A finished career seeds the next | After 13 | `career new` | None |

Rule from the template: never two new mechanics in one encounter. Phase 3's
verb and phase 2's fade both appear in tours 1 to 3; the guard is that the
fade happens in the reading note and the verb happens at a sign-off, and the
two do not share a report. A playtest should confirm that (section 11).

## 7. The first failure, and the first time the player feels competent

**First failure.** In Fun, the first wrong close or wrong dispatch, most
likely on tours 2 to 3 when the fault name first fades (R3, C8 at sighting 5).
A wrong dispatch costs 45 minutes against a 480-minute tour
(`COST_WRONG_DISPATCH`) and a wrong no-trouble close on a faulty line calls
back one time in four (fun) or most of the time (craft). The debrief quotes
the player's own readings (kept from the audits' "keep" list), so the cause is
not ambiguous: it is what they typed and what the pair said. Retry is
immediate; the cost is points and a repeat on the board. In Craft the first
failure can be on the first or second report, from closing before measuring
(refused) or from naming the fault wrong. **Guess:** within the first hour of
real play, tour 1 plus the start of tour 2.

**First competent.** Two beats, both visible to the player.
First: Halloran's first sign-off (Frame: 3 correct closes on Fun, 12 on Craft,
`progression.py`), because the machine says in someone's voice that the player
can do something new. `cosmos jumper`, the read, is open from the start, so
the closes that earn it are not guesses (#64); the sign-off is for `cosmos
fix`. Second: the first report closed correctly after its
reading note has faded, when the crew class was inferred, not read. The first
is the better lever; the second is what makes the first earned. **Guess:**
reached by the end of tour 1 on Fun, by tour 2 or 3 on Craft.

Both depend on the real time one report takes at 300 baud, which has not been
timed (C28 decides whether to skip pacing for tables on tour 1 if dead time
after a dispatch is over 60 seconds).

## 8. Spikes and valleys

| Name | Where | Type | Purpose | Recovery |
| --- | --- | --- | --- | --- |
| The empty board | Tour 1 | Valley | One report, one voice, four messages, a safe place to type wrong things | Is the recovery: the board fills only after the first close |
| The first full board | Tours 2 to 3 | Spike | Opening backlog of 3 to 5 plus arrivals up to the depth of 9; the first time commitments compete | Handoff shows what was carried, never ends the career |
| Thanksgiving | Between 3 and 4 (24 Nov) | Valley (**guess**) | A pause in the calendar and, in tours.py, a quieter briefing | The tour after (26 Nov) is the first with the board at 10 |
| Wet weeks | Tours 5 to 10 | Rising spike | Rain probability rises from 16% to 24%; wet cable is the best mechanic (S2) and clusters | The binder and the `mlt` pattern; Okafor takes the cable |
| Marker 2 | Tour 9 or 10 (A7) | Spike, knowledge type | A run of unrelated reports with no cable in common; the player must read the pattern | Johnson's notes in `marker.notes`, readable well before |
| Christmas Eve | Tour 11 | Valley with a task | Controls go on tonight and must come off (E&O Table 5-1 footnote, plan section 4) | The next tour is the first after Christmas Day |
| The audit | Tour 13 | Spike, emotional | The memo's promise arrives: dispositions are checked, open reports pass "with your name on them" | The epilogue reads the career; the career is never cut short |

## 9. Balancing levers

Player-facing levers are the six assists in `progression.ASSISTS`. The rest
belong to the designer.

| Lever | Choices (fun value first) | Effect | Notes |
| --- | --- | --- | --- |
| `assist.test_first` | on / off | Refuses a close on an unmeasured line | Off on Fun. Turning it off must not skip a practical (C11) |
| `assist.commitments_count` | off 0.0 / soft 0.25 / full 1.0 | Share of the 20-point miss weight; an open report past commitment is lost in full whatever this says | Fun soft, Craft full |
| `assist.repeat_reports` | off 0.0 / soft 0.25 / full 0.85 | Chance a wrong no-trouble close calls back | |
| `assist.commitment_slack` | on 90 / off 0 | Minutes added to every commitment | |
| `assist.pace` | quick 3 / slow 12 | Correct closes per step | Craft slow makes Toll a stretch (section 4) |
| `assist.scoring` | gentle 0.7 / strict 1.0 | Scales every penalty | 0.4 was tried and 89 shifts in 100 were EXCELLENT, which is why 0.7 (see the comment in `progression.py`) |
| `assist.annotate` (C8, not built) | on / off | Keeps reading notes past the fade | Phase 2 |

Designer levers, not player-facing: `MAX_PENDING` 9, `CAREER_DEPTH` 2,
`OPENING_BACKLOG` (3, 5), `NO_TROUBLE_SHARE` 0.18, `REGULAR_SHARE` 0.18, the
weather weights, `LOAD_MINUTES_PER_PENDING` 25, the `COST_*` minutes
(`mlt` 4, close 2, frame lookup 2, plant test 2, callback 8, dispatch 12,
wrong dispatch 45), the interruption rates 0.06 and 0.22 and the sign-off
counts. `tools/index_calibration.py` is how any of them is re-measured.

## 10. What cannot be adjusted

By design, so a lower setting never removes the need to learn:

- The practicals (C11, settled in D3, not yet built) gate every sign-off on both profiles, with `hint` free.
- The plant, its readings and the close codes (pillar 1).
- The date: tour 13 is 31 December and the audit is on it.
- The index weights; only their scale moves.

## 11. Validation checklist

Run a scripted run (bots at skill 0.6 and 0.9 on each profile) for the
numeric items and a human playtest (`playtest-template.md`) for the rest.
Mark an item done only with the run recorded.

### Tour 1 (onboarding)
- [ ] A first-time player reaches the first close without leaving the terminal and without asking anyone.
- [ ] Real minutes to the first close are on record; dead time after dispatch is timed (C28).
- [ ] Nobody reports confusion about what a report is after Halloran's second message.
- [ ] The first wrong close, if it happens, is followed by a player saying what they did wrong.

### Tours 2 to 4 (early)
- [ ] The first sign-off arrives by the end of tour 1 (Fun) or tour 2 to 3 (Craft).
- [ ] No tour introduces a fade and a new verb on the same report.
- [ ] The first full board does not leave a Fun player with more than two reports past commitment at handoff (**guess**, tune).
- [ ] Before the fade, a player can say in their own words how they chose a crew.

### Tours 5 to 9 (mid)
- [ ] A skill-0.6 bot on Craft does not reach Toll; a skill-0.9 bot on Craft signs off all six by tour 13 (C7).
- [ ] A cluster is read as a cable by at least some players without being told.
- [ ] Marker 2, when it fires, is explained by files the player could have read already.
- [ ] No single axis (knowledge, time, resource) is the stated cause of most complaints.

### Tours 10 to 12 (late)
- [ ] The relief tours (6, 10 and 12) are felt as lower pressure by a majority of testers.
- [ ] Every regular has been met at least twice and resolved or abandoned by tour 13 (C16).

### Tour 13 (finale)
- [ ] The audit's counts match `report closed` and the open board (A2).
- [ ] A zero-work career fails the audit and still gets an ending.
- [ ] Testers can say what the ending is about without being prompted.

### Assists and access
- [ ] Each assist, set alone, moves only its own row in `set`.
- [ ] A Fun player with every assist at its easiest still has to pass the practicals.
- [ ] A Craft player who turns on `assist.pace quick` is not told they have failed.
- [ ] `set display.pacing off` changes nothing but speed.

## 12. Open questions

| Question | Where it is tracked |
| --- | --- |
| Real human closes per tour after PR 46 | C7, `tools/index_calibration.py` |
| Real minutes for the first report at 300 baud | C28 |
| Whether Fun's ladder, finished by tour 3 to 6, leaves tours 7 to 13 enough to pull on | Playtest, then A1's set pieces |
| Whether interruption rate should be an assist | New; not planned |
