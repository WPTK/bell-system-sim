# Session 2: code analysis and live playtest

Gamification audit of `bell-system-sim` v4.0.0. Scope: how the game plays, what it measures, what story it tells, and what to change. Not a bug hunt.

Method: read the code by search and line range; drove the real game through `BellSystemTerminal.execute_command` and through the CLI (fresh `BELL_SYSTEM_HOME` each run, so no real save was touched); wrote scripted "bot" players at skill 0.6, 0.9 and 1.0, on both difficulties, with machine-paced and human-paced clocks; and played the cold start by hand. Paths below are relative to `src/bell_system/`.

## 0. The short version

1. **The loop is a lookup, not a diagnosis.** In `fun`, the MLT prints "Dispatch to: Outside plant" and a correct dispatch prints the fault name back. The tutorial says so: "It is not a riddle - it says it outright." Craft mode is where deduction lives, and it only half works (CO_EQUIP, FCG and NONE look alike on an MLT).
2. **Time has no teeth.** Commitments age only when *you* spend minutes on that report (`reports.py: TroubleReport.spend`). An untouched board did not age over 16 hours of shift time. Missed commitments were 0 in every bot career. A career that does nothing at all (13 x `handoff relieve`) ends at **100.0 EXCELLENT** with 47 reports on the board.
3. **Two clocks fight.** Field crews return on wall-clock time (`field.py: Assignment.back_at` against `clock.now()`), while the board ages on shift minutes. At human pace only 2-7 reports close per tour and "Nobody free on outside plant" is the dominant message.
4. **The twelve positions are one game with different paint.** Fault bias, ticket mix, voice and a tally line differ. NOC, SCC, TSPS and ticket screens are dashboards with a one-command "win".
5. **The story is rich and static, and the ending ignores it.** Memo, bulletin, netnews, sulog, moo rivalry, the Alvarez notes: all good, none advance with the calendar, none pay off. Tour 13 ends on a stats block and Halloran's line about "the seven", which contradicts the twelve positions.

What is already good and worth protecting: the first tour's one-report tutorial; the sheath-cluster moment (one splicer dispatch clears four pairs); the callback / repeat-report sting in craft; the regulars' CHRONIC flag in `custdb`; the voices (Halloran, mreyes, rjohnson); the whole `/usr` filesystem as a place to snoop.

---

## 1. Playtest log

### 1.1 Cold new player, first five minutes (fun, position 1)

The login screen sells it well: "48 days to divestiture. This machine is being inventoried." Then a notice, a board with exactly **one** report, and Halloran on the order wire: "I have kept the rest off it until that one is closed."

```
$ mlt TR-01367
...
TEST RESULT
  Infinite resistance tip to ring; no station termination
  System reads this as: Open (OPEN)
  Dispatch to: Outside plant

Message from ehalloran: Read the bottom of that. TEST RESULT tells you what the fault is
and which crew it wants. It is not a riddle - it says it outright.
```

Three commands to a correct close (`mlt`, `report dispatch`, `report close 5 OPEN`). A correct dispatch:

```
Bright, A. (lineman) rolled from the garage, 5 minutes. ... reports open located and cleared.
163 minutes on the job.
```

Annotation: this is the best five minutes in the game. It teaches the verbs, uses a person's name, and gives a wait. It also teaches that the machine tells you the answer, which the next 12 tours never un-teach in `fun`.

Cold-player misplay (I closed blind as a SHORT instead of reading the MLT):

```
There was an open on that pair, not a short ...
Closed 1, correct 0. Service index 37.0 (UNSATISFACTORY).
```

Then a repeat report "R" for the same line appeared on the board (TR-01368, 201-200-9600). One wrong first close drops the index from 100 to 37 in `fun` and to 10 in `craft`, because the index is a cumulative rate over a tiny n. It reads as a verdict on the player, not as a lesson. The recovery path ("a repeat is a second chance to fix it") is good and under-explained.

State transition seen: `shift` right after dispatch showed `Bright, A. ... back about 10:48:00`. That is the wall-clock return time, not a shift-minute one.

### 1.2 Full tour, `fun`

Bot at skill 0.9, machine-paced: tour 1 closes everything it is given. The loop collapses to `mlt N; report dispatch N <force>; report close N 5 <fault>`. The final index is 94 at skill 0.9 and 85 at skill 0.6. The only visible difference between a careful and a careless player is a few points on a status line.

Wrong dispatch force (edge test):

```
... found nothing at their end.
```

Cost: `COST_WRONG_DISPATCH = 45` minutes charged to that report. In `fun` nothing else happens. There is no embarrassment, no phone call from a foreman, no customer calling back angrier.

### 1.3 Full tour, `craft`

Craft requires `mlt` before close ("Verify, locate, repair, verify. This shift will not accept a close on a line nobody tested."). That is a good rule: it gives the MLT a reason to exist.

Code 8 on a faulty line (GROUND), then ticket spawn:

```
Service index 10.0
mreyes: You closed it as code 8. It is TR-02212 now, and it counts as a repeat.
```

This is the strongest consequence in the game: mreyes names the new report number and tells you it is yours. Keep this and widen it.

Craft MLT cannot separate CO_EQUIP, FCG and NONE. To tell them apart a player has to `cosmos jumper` (a 2-minute frame lookup that prints "RECORD DOES NOT AGREE WITH THE PLANT"), place a callback (`COST_CALLBACK = 8`), or dispatch by elimination. That is the right design instinct, since it makes the frame a second instrument, but nothing signposts it, and a correct dispatch still prints the fault name for free, which lets a lucky guess erase the deduction.

### 1.4 Other positions (switch, noc, tsps, sarts, docprep)

All five load into the same repair-desk core. Differences I could measure:

- **switch**: fault bias toward CO_EQUIP; qualification route office. Same board, same verbs.
- **noc**: the `trouble` tickets are a dashboard. `trouble resolve TK-4516` resolves instantly and prints invented numbers:

```
Total Duration:       241 minutes
Target Time:          15 minutes
Performance:          EXCEEDED TARGET
Customer Impact:      28,943 customers restored
Revenue Recovered:    $257,288
```

  Duration 241 against a target of 15 and still "EXCEEDED TARGET". `screens/tickets.py: _resolve_trouble_ticket` ignores the work and the clock.
- **tsps**: `tsps` prints a good static panel (49 of 52 positions, Erlang C, speed of answer 2.6 s, objective 2 to 6). Nothing to decide. In my run `tsps status` raised an error.
- **sarts**: has a real test loop (`sarts list|trouble|test|circuit|categories`, deterministic). But `sarts test 1/2/3` all returned "on manual jack access ... needs somebody at the office", and a failing circuit is "held in trouble" with no repair verb. A dead end.
- **docprep**: reads as documentation and lore work on the same shared board; no distinct loop.

Verdict: the 12 positions do **not** really differ in what the player does minute to minute.

### 1.5 `--simple`

`python -m bell_system --simple` starts `simple_terminal.py` (598 lines): a bare V7 shell with `ls cat cd ps who grep wc ed df du find man`. `report`, `mlt` and `1` all answer "command not found". The README describes it as "a simplified four-role interface"; there are no roles in it. It is a sandbox for learning Unix, not a simpler game. Either rename it or make it the tutorial it looks like.

### 1.6 Edge cases

| Case | What happened | Fun? |
|---|---|---|
| Wrong close (`5 SHORT` on an OPEN) | Told the truth; index fell to 37 (fun) / 10 (craft); a repeat report appeared | Sharp, but the index swing at n=1 is cruel |
| Code 8 on a GROUND line | New TR number, counts as repeat, mreyes says so | Best consequence in the game |
| Wrong dispatch force | 45 min charged; "found nothing at their end" | Cheap; no story |
| Ignoring commitments | Board of 9 untouched for 16:31 of shift time: ages unchanged, `Past commitment 0`, `Missed commitments 0` | Broken: no pressure |
| Repeat report | Appears on board; `should_repeat()` / `repeat()` in `reports.py` | Good seed, rare |
| Wet-cable cluster | 4 pairs in cable 47 binder 4 reported together; one `Cable repair` dispatch ("330 minutes charged") cleared the lot | **The single best mechanic.** Wants more teeth |
| Close after sheath repair, craft | "has not been measured ... Run 'mlt' first" | Correct but fussy: the repair already proved the fault |
| Regulars | Show up with notes in `custdb` and a CHRONIC flag; never resolve or escalate | Strong seed, no payoff |

Wet cluster excerpt (`cat /usr/lmos/cable` showed `47  4  4  open  2.8  TR-02434 TR-02437 TR-02440 TR-02444`):

```
Sandoval, J. reports water in cable 47, binder 4 (White-Brown), pairs 76-100.
Sheath opened, dried and resealed. 330 minutes charged.
The one trip clears every pair in that group. 3 other reports on this sheath can be closed ...
Time charged 5:56 of the commitment (18:29 remaining).
```

Ignoring commitments (sixteen shift hours of `sleep 7200` on a board of 9):

```
before [('TR-02431', '9:08'), ('TR-02451', '10:55'), ('TR-02434', '18:29')]
after  [('TR-02431', '9:08'), ('TR-02451', '10:55'), ('TR-02434', '18:29')]   shift_minutes 991
  Worked              16:31 of 8:00
  Past commitment     0
  Missed commitments  0
```

### 1.7 Pushing through the 13 tours

Bot careers, fun and craft, machine-paced and human-paced:

- Human-paced clock: only **2-7 closes per tour** fit; "Nobody free on outside plant" fired **27-44 times per tour**. Pending at tour opens in one craft run: 1, 13, 14, and so on; by tour 13 the backlog compounds to **15-33 pending** (the board's depth limit is 9-11, so the rest sits unseen).
- The index is cumulative: it swings at low n, then goes flat. By mid-career a bad tour moves it a fraction of a point.
- Qualifications gate on correct closes only. In craft, SCC, Trunk and Toll still needed 13, 37 and 73 more closes after the first three. **Toll (108 correct closes in total) is never reached.**
- Late game: the board never changes character. Tour 13 is the same board as tour 3 with more rows on it.

### 1.8 The 31 December ending (verified by running it)

Thirteen `handoff relieve` commands with **zero work** (each "closed after 0:01 worked"):

```
Shift 13 begins. 47 pending. December 31, 1983.
This is the last working day of the Bell System.
The board is the board. Nothing about the job is different today ...

THE CAREER
  Tours worked        13
  Reports closed      0 (0 correct, 0 wrong)
  Missed commitments  0
  Service index       100.0  EXCELLENT
  Signed off on       1 of 6
  Every tour of it    ▅▅▅▅▅▅▅▅▅▅▅▅▅

ehalloran: That is the tour, and that is the company.
13 tours and 0 reports off the board. I signed 1 of your qualifications ...
They go with you. Whichever of the seven you end up at in the morning ...
Go home.

The board is still on the machine. Nobody is coming to take it off you tonight.
```

Findings:

- You can finish the whole game in about a second.
- A player who did nothing is rated EXCELLENT.
- Halloran notices "0 reports"; the game does not.
- "The seven" contradicts twelve positions.
- 47 open reports are simply left. That is the one thing the January memo says must not happen (it points at records-retention instructions in `/usr/doc/divestiture`).
- `SHIFT-END` is only a notice: nothing forces a handoff, and nothing is lost by working past the end of the tour ("Worked 16:31 of 8:00").

### 1.9 Filesystem lore

Walked `/usr/users`, `readnews`, the moo scoreboard, the locked file, the January memo and `/usr/games`. Detail in section 6.

---

## 2. Core loop and pacing

**Loop:** report (board) -> measure (`mlt`, 4 min) -> dispatch (12 min, or 45 if wrong) -> close (`5 <fault>` or `8`). Costs live in `reports.py`: `COST_MLT 4`, `COST_CLOSE 2`, `COST_FRAME_LOOKUP 2`, `COST_PLANT_TEST 2`, `COST_CALLBACK 8`, `COST_DISPATCH 12`, `COST_WRONG_DISPATCH 45`.

| Stage | Fun | Craft |
|---|---|---|
| Tour 1 | One report, scripted. Perfect. | Same, then the first wrong close costs 90 index points |
| Tours 2-4 | Too easy: the MLT result *is* the dispatch. Opaque only in "why is nobody free" | Good: MLT interpretation, `mlt` required, repeats bite |
| Tours 5-9 | Repetitive: the same row 5-40 times | Repetitive; frame and callback instruments barely used |
| Tours 10-13 | Backlog (15-33) but no stakes; index flat | Same. Backlog is the only pressure and it is invisible past depth 9-11 |

Why it feels repetitive:

- One verb sequence, with no variation in order of operations except craft's `mlt` gate.
- Faults are drawn from a weighted table (`data/trouble.py: FAULTS`, `NSPMP_WEIGHTS`); only OPEN, SHORT, GROUND, CROSS and WET are easy to tell apart, and nothing ties a fault type to a story beat.
- Crew return is wall-clock; a human reading the screen sees "back about 10:48" and either `sleep`s (`tools.py: cmd_sleep` only advances `shift_minutes`) or retypes.

Why it feels opaque:

- The two clocks (displayed time against shift minutes).
- "Nobody free" is shown without offering the next-best action.
- The index is a cumulative rate with no per-tour read.

**Do the 12 positions differ?** Not in decisions. `screens/position.py` (`board_depth`, `ticket_rate`, `prefer_tickets`, `position_tally`) and `data/positions.py` change what shows up and who talks. They do not change what you *do*.

---

## 3. Metrics for Fun

Intrinsic satisfactions present now, and how well they land:

| Satisfaction | Now | Evidence |
|---|---|---|
| Command mastery | Medium. `qual` gates commands by closes; man pages and `help` are rich | 16 gated commands at tour 1, marked `*` |
| Decoding acronyms | Latent. BSP and `man` hold it; no mechanic *uses* it | `bsp search <topic>`; no puzzle depends on it |
| Cascading failures under time pressure | Weak. Wet clusters exist; time does not pressure them | Section 1.6 |
| Voyeuristic discovery | Strong, but static | `/usr/users`, readnews, sulog, notes |
| Social and rival | Present: moo rivalry with Halloran | `screens/games.py`, `npc.py: moo_beaten` |
| Competence feedback | Weak: text only, no "that was clean" beat | |
| Surprise | Low | Faults draw from a flat table |

Possible, cheap to add (ties to section 8):

- A **clean-work beat**: right dispatch in under N minutes gives one line of acknowledgement from the crew.
- **Acronym puzzles**: a crew will not roll without the right work-order code; the code is in a BSP.
- **Cascades with a clock**: an unrepaired wet binder grows (`cable.py`) one pair per hour of shift time, and weather (`weather.py`) raises the rate.
- **Whodunit lore**: let `sulog` and the mreyes 03:47 failed root attempt be something the player can investigate with `grep` and resolve.

## 4. Metrics for Achievement

| KPI | Tracked? | Where | Note |
|---|---|---|---|
| Reports closed / correct / wrong | Yes | `progression.py: Career` | Wrong weighted 55 |
| Repeat reports (came back) | Yes | `record_repeat` | Weighted 35; only fed by `_close_report` |
| Missed commitments | Yes, but always 0 in practice; "(not counted)" in fun | `MISSED_COMMITMENT_WEIGHT = 20` | Aging problem, see 1.6 |
| Service index | Yes | `service_index()`; `index_history[-40:]` | Cumulative; 100 with no data |
| Qualification tiers | Yes (6) | `QUALIFICATIONS` | Correct closes only; Toll unreachable |
| Promotions / position | No | | The 12 positions are never earned |
| Clearance | Partly | `shell.py: _may_read`, `ADM_GROUP_QUALIFICATIONS = 3` | Gates files, not story |
| MTTR (mean time to repair) | **No** | | Natural: first MLT to close, per report |
| Commitments met % | **No** | | Needs the aging fix first |
| Repeat rate per 100 closes | **No** (count only) | | |
| First-time-right dispatch % | **No** | | Cheap: wrong dispatch is already counted |
| Cleared-without-field % | **No** | | e.g. code 8 correctly closed |
| Backlog age / carried per tour | Partly (`Carried forward`) | `turnover.py` | No age distribution |
| Regular-customer satisfaction | No | `data/regulars.py` | |

Should track: MTTR, commitments met %, first-time-right dispatch %, repeat rate, backlog age, and a **per-tour** index next to the cumulative one. The `qual` screen already has the right layout ("Worth to the office 10.0 of 10 index points", a sparkline); it needs better inputs.

Index behaviour I measured: at skill 0.9 against 0.6 the final index separates weakly (fun 94 vs 85; craft 92 vs 77). A player who does no work scores 100.

---

## 5. Narrative arc

**Now.** Beginning: strong. 48 days, a notice, a single report, a mentor, the previous occupant's notes. Middle: reports and ambient mail, with no change in stakes between tour 3 and tour 11. End: a stats block and one speech.

**Should be.** Three acts over 13 tours (the game already stamps each tour with "N days to divestiture"):

- **Act I, tours 1-4, "learn the board".** Keep as is. Add the first regular (the CHRONIC line) on tour 2.
- **Act II, tours 5-9, "the machine is leaving".** A weather event, a cascade (wet binder or the ice storm in EV-8050), a rival NPC, the sulog thread comes alive. Records start to be requested for the divestiture inventory.
- **Act III, tours 10-13, "audit and handoff".** The January memo's audit arrives. Every open report must be dispositioned or formally carried. Regulars resolve one way or the other. Qualifications decide the position you land in on 2 January.
- **Tour 13 climax.** Last day: a real incident, not an ordinary board; Halloran on the order wire; the final board graded against the memo.
- **Epilogue.** A 2 January message from the new operating company that reflects what you did: your qualifications, your unclosed reports, which regulars you kept, who beat whom at moo. Today's `_end_career` ignores all of this.

---

## 6. Story discovery: what exists

Inventory from walking the filesystem (`filesystem.py`; full text in the shared notes transcript `lore.txt`):

- **Divestiture memo, `/usr/doc/divestiture`**: promises an audit and an open-report handoff. Neither appears in play.
- **`/etc/motd`**: the login notice, pointing at `/usr/games`, `net.games` and `moo.scores`.
- **`/etc/passwd`, `/usr/users/*`**: named staff (ehalloran, mreyes, rjohnson, tnakamura, dpetrak, "R. Alvarez") with notes. rjohnson leaves marker notes; the Alvarez notes read as an unresolved thread.
- **`sulog`** (`jobs.py: cmd_su` writes it) and the **mreyes 03:47 failed root attempt**: the strongest hook in the game; no payoff.
- **`readnews`** (`games.py: _news_articles`): good period netnews that **does not advance with the calendar**.
- **moo scoreboard**: a rivalry with Halloran; **the scoreboard and `ed` files reset on restart** (`save.py` saves shift, force, plant and weather, not the filesystem, mail or news).
- **`/usr/bsp`**: practices; useful for acronyms; not used by any mechanic.
- **Locked file and permissions** (`shell.py: _may_read`, `_groups`): a nice idea; unlocking is by qualification count only.
- **`/usr/games`**: moo, fortune, arithmetic.
- **Regulars** (`data/regulars.py`, 4 of them, `REGULAR_SHARE 0.18`): `custdb` shows notes and CHRONIC; nothing happens to them.
- **Voices**: `npc.py: CRAFT`, Halloran's `last_word`, mreyes' repeat notice, rjohnson's event pings.

What is missing is any *state* that links these. The world is read-only. The player cannot change, act on, or be changed by a single piece of lore.

---

## 7. Gap map

| Gap | Type | Detail |
|---|---|---|
| Commitments inert | Mechanical | Only `spend()` ages a report |
| Two clocks | Mechanical | `field.py` wall-clock vs `shift_minutes` |
| Fault name free on correct dispatch | Mechanical | `ReportDesk.dispatch` |
| Wrong dispatch costs only minutes | Mechanical | `COST_WRONG_DISPATCH 45` |
| CO_EQUIP / FCG / NONE indistinguishable on craft MLT | Mechanical | Needs signposting of `cosmos jumper` |
| Zero-work run scores 100 EXCELLENT | Mechanical | `service_index()` with n=0 |
| `handoff relieve` from minute 0 | Mechanical | `turnover.py: cmd_handoff` |
| `SHIFT-END` is a notice only | Mechanical | `shift.py: _shift_over_notice` |
| Backlog invisible past depth 9-11 | Mechanical | `board_depth()`; 15-33 pending by tour 13 |
| Dashboards with one-command wins | Mechanical | `tickets.py`, NOC, SCC, TSPS |
| SARTS dead end for failing circuits | Mechanical | `special_services.py` |
| TSPS `status` error | Blocker (brief) | |
| `--simple` is not a game | Mechanical | `simple_terminal.py` vs README |
| Progression only by correct closes | Progression | `QUALIFICATIONS`; Toll unreachable |
| No promotions, no earned position | Progression | `data/positions.py` |
| Index volatile then flat | Progression | Cumulative, in `progression.py` |
| Missed commitments not counted in fun | Progression | |
| Ending ignores play | Narrative | `turnover.py: _end_career`, "the seven" |
| Memo's audit absent | Narrative | |
| Regulars never resolve | Narrative | `data/regulars.py` |
| News static | Narrative | `games.py` |
| Scoreboard and `ed` reset on restart | Narrative | `save.py` |
| sulog / 03:47 and Alvarez threads | Narrative | `filesystem.py` |
| No tour-level arc between 2 and 12 | Narrative | |

---

## 8. Remove / Change / Add matrix

### P1

| | Action | Files / mechanic |
|---|---|---|
| **Change** | Age every pending report on shift minutes, not only on `spend()`. Overdue leads to an mreyes escalation and is counted. Count misses in fun (softer) and craft (full) | `reports.py: TroubleReport.spend/due_in/overdue`, `screens/shift.py: _advance_shift`, `MISSED_COMMITMENT_WEIGHT` |
| **Change** | One clock. Crews return on `shift_minutes`; "Nobody free" gives the earliest return in shift terms and proposes the next action | `field.py: Assignment.back_at`, `clock.py`, `screens/bureau.py: _dispatch_report` |
| **Change** | Zero work must not be EXCELLENT. Index uses unworked backlog age; `handoff relieve` needs a minimum of minutes worked, or a board review | `progression.py: service_index`, `turnover.py: cmd_handoff` |
| **Change** | A correct dispatch confirms the force but does not print the fault; craft reveals at close. Fun keeps a reveal ladder (hint, MLT line, reveal) | `reports.py: ReportDesk.dispatch`, `data/trouble.py` |
| **Change** | Rebuild the ending: tour 13 incident, audit against the memo, epilogue from the new company that reads play state; fix "the seven" | `screens/turnover.py: _end_career, LAST_TOUR_NOTICE`, `npc.py: last_word` |
| **Add** | KPIs: MTTR, commitments met %, first-time-right dispatch %, repeat rate, per-tour index beside the cumulative one | `progression.py`, `screens/bureau.py: cmd_qual`, the `shift` screen |
| **Remove** | Fake "28,943 customers / $257,288 recovered / EXCEEDED TARGET" | `screens/tickets.py: _resolve_trouble_ticket` |

### P2

| | Action | Files / mechanic |
|---|---|---|
| **Add** | Cascades with a clock: an unrepaired wet binder grows by pairs; weather raises the rate; `cat /usr/lmos/cable` psi falls | `cable.py`, `weather.py`, `screens/shift.py: _weather_events` |
| **Add** | Regulars with arcs: they escalate if ignored and resolve if fixed; show up in the ending | `data/regulars.py`, `screens/records.py: cmd_custdb`, `reports.py: _draw_regular` |
| **Change** | Give each position one distinct verb and one distinct pressure (switch: alarm incidents; noc: triage queue on the real clock; tsps: staffing decision; sarts: a repair verb for failing circuits; docprep: retention inventory for the memo) | `data/positions.py`, `screens/position.py`, `special_services.py`, `screens/tickets.py` |
| **Add** | Competence tracks besides close counts (speed, repeat-free streak) so Toll is reachable and promotion is real | `progression.py: QUALIFICATIONS`, `ROLE_QUALIFICATIONS` |
| **Change** | Persist the world: scoreboard, `ed` files, news position, mail | `save.py` |
| **Change** | News advances with the calendar (one item per tour) | `screens/games.py: _news_articles`, `clock.py` |
| **Add** | Payoff for the sulog 03:47 thread and the Alvarez notes: an investigable chain via `grep` and `cat` that ends in a decision | `filesystem.py`, `screens/jobs.py` |
| **Change** | Signpost the frame as an instrument (`cosmos jumper`) when an MLT is ambiguous | `screens/guidance.py: next_action`, `screens/frame.py: _cross_connect` |
| **Change** | Show a provisional index label until 5 closes, so n=1 is not a verdict | `progression.py` |

### P3

| | Action | Files / mechanic |
|---|---|---|
| **Change** | `--simple`: rename it (a Unix training sandbox), or give it four real roles | `simple_terminal.py`, `cli.py`, README |
| **Add** | Clean-work beats from crews; acknowledgement for a fast correct dispatch | `field.py`, `npc.py` |
| **Add** | Acronym and work-order-code puzzles that use BSP text | `bsp`, `data/trouble.py` |
| **Change** | `SHIFT-END` becomes a soft stop: a relief NPC arrives and takes the board | `screens/shift.py: _shift_over_notice` |
| **Change** | Show backlog beyond depth 9-11 as an aged list or a "view all" | `screens/position.py: board_depth` |
| **Change** | Fix the TSPS `status` error | TSPS screen |
| **Add** | Rival tension: moo scoreboard persists and Halloran reacts across tours | `screens/games.py`, `npc.py` |

### Suggested build order

1. Fix time (aging and one clock). Everything else rides on it.
2. Make zero work visible (index, relieve).
3. Ending and the tour 13 incident.
4. KPIs.
5. Position differentiation, one position at a time (NOC first: it already has the cleanest dashboard to turn into a queue).

### Not covered in this pass

A real person playing over several hours (I used human-paced and machine-paced bots); ambience and sound settings; performance; the content of the `training unix` module beyond its first screen; the docprep and switch positions beyond a first tour.
