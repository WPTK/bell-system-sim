# Source mining: what the corpus can ground for phases 7, 8 and 9

Row A21 of issue #43. Later phases cite this file instead of re-reading the
corpus. It writes no code and edits no `SOURCES.md` row; each phase adds its
own `SOURCES.md` rows from what is here.

## 0. How to read this file

**Where things are.** All paths are in `attached_assets/` unless marked E&O.

- **E&O** is `Engineering_and_Operations_in_the_Bell_System_2ed_1984.pdf`
  (Bill's copy, not in the repo). I cite the **printed page**, with the PDF page
  in brackets; PDF page = printed page + 17. The repo's
  `Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt` holds the
  same text, so every E&O quote below can be found with `grep -n`; the line
  numbers there differ from the PDF's, so I don't give them.
- **Other files** are cited by line number in the `_djvu.txt` file. Short
  names: **SD** = `SD_26030-01`; **XB-III** =
  `Crossbar-Dial-System_Section-III_Part-2-Terminating-Circuits`; **TTE-2**,
  **TTE-3** = `Telecommunications_Transmission_Engineering_Vol_2/3`; **SARTS** =
  `bstj59-4-501` (Giguere, April 1980); **TNDS** = `bstj62-7-2127` (September
  1983); **WE-62** = `WE_Fundamentals_of_Telephony_Lesson_1_Mar62`.

**Quotes** are 15 words or fewer, copied exactly. Where a word was hyphenated
across a line break in the source I have joined it. The SD is OCR of schematic
drawings and prints in capitals; I keep its OCR errors and mark them
`[sic]`.

**Verdicts** in the marker table are MATCHES, CONTRADICTS, or NOT COVERED.
NOT COVERED means the text I could search does not say it; for the SD that is
weaker than it sounds (see 1.3).

**Method.** `pdftotext -layout` on the E&O PDF, then `grep` with page
numbers. `grep` on the repo's text files for the rest. Nothing was read whole.

## 1. Marker 2 and the sequence relay (A7 / A21)

### 1.1 What the game says

| # | Claim | Where in `src/bell_system/` |
| --- | --- | --- |
| M1 | The office is a No. 5 crossbar with markers; markers sit in "aisle 4", aisles 1-2 are line link frames, 3 originating registers, 5-6 trunk link frames and outgoing senders | `data/homes.py:76-92`, `filesystem.py:1497` |
| M2 | A marker sets up a path and lets go, so one marker serves many calls; a marginal marker makes thousands of calls slightly worse | `screens/plant.py:67-68`, `data/homes.py:94-98` |
| M3 | Markers are numbered; "Marker 2" is slow | `filesystem.py:1497`, `npc.py:217`, `data/homes.py:86` |
| M4 | The slowness is on the "third trial" | `filesystem.py:1498`, `npc.py:151,217`, `data/homes.py:64,86` |
| M5 | Marker 2 took eleven seconds, "nothing out of limits", peg count up | `npc.py:217-219` |
| M6 | Dial tone speed is on the wrong side of the objective but nothing is alarming | `npc.py:220-223` |
| M7 | Two people looked and both wrote NTF (no trouble found) | `data/homes.py:88` |
| M8 | The trouble is "in the timing chain", which is within limits | `data/homes.py:89-90` |
| M9 | "If it ever fails outright the trouble is in the sequence relay, not the marker" | `filesystem.py:1501-1502` |
| M10 | Slow "since 81", "two years", measured "11/2" | `filesystem.py:1498-1499`, `data/homes.py:64-65,87` |

### 1.2 Claim by claim against SD_26030-01 and the rest of the corpus

| # | Verdict | Evidence |
| --- | --- | --- |
| M1 | **MATCHES** for "No. 5 crossbar has markers and line link frames" | SD title (line 7): "Crossbar Systems - No. 5 - Line, Line Link and Marker Connector Control Circuit". SD 6763-6764: "TWO MARKERS SHOULD BE CHOSEN TO BE PREFERRED ON ALTERNATE CALLS" in each line link frame. E&O p. 802 [819] glossary: markers "determine terminal locations of calling LINES" in "a No. 5 Crossbar SWITCHING SYSTEM". The aisle layout itself is the simulation's own. |
| M2 | **MATCHES**, for crossbar markers generally; the SD does not say it | E&O p. 403 [420]: "markers could set connections for a call in less than 1 second" and "then move on to the next call". E&O p. 260 [277] sets out the common-control principle. |
| M3 | **NOT COVERED** | The SD has a marker *group* and no individual marker numbers in the OCR. It does say markers are preferred in pairs per frame and the preference is "PERIODICALLY SHIFTED TO DISTRIBUTE WEAR" (SD 6769-6770, `HAY` [sic] for MAY). So one marker carrying a disproportionate share is plausible; the number "2" is the simulation's own. |
| M4 | **NOT COVERED**, and the source describes fewer trials | SD 7384-7385 has only "SECOND TRIAL" and "IF FIRST TRIAL", labels on a function diagram. XB-III 5573-5574: on a trouble release "on second trial the sender will seize another marker". XB-III 14738-14739: "the marker will time out and a second trial will be made". `grep -i "third trial"` over all of `attached_assets/` finds nothing. XB-III 5631-5632 registers second trial on three relays, TR1 to TR3 (OCR `TRl`), which is three relays and not a third trial. XB-III describes a terminating circuit and does not say which crossbar system; do not cite it for the No. 5 specifically. |
| M5 | **NOT COVERED**, and in tension | The sources give no marker time-out figure, and E&O p. 403 puts a normal marker operation under one second (for No. 1 crossbar). In XB-III a marker that cannot finish "will time out", gets a second trial on another marker, and leaves a trouble-indicator record (14521-14527: "prevent a large number of trouble indicator records"). A marker that routinely takes eleven seconds and leaves no record is the simulation's own. Label it. |
| M6 | **MATCHES** the measure | E&O p. 682 [699] Table 16-1 lists "Dial-Tone Speed" under Machine Access. E&O p. 153 [170]: digit receivers are engineered so "the probability of dial-tone delay exceeding 3 seconds is less than a" specified value. "Peg count" in E&O p. 182 [199] means attempts offered to a *trunk group*, not marker operations; the game's use of it for a marker is a loose borrowing. |
| M7 | **MATCHES** the code | E&O p. 683 [700]: "no trouble found" (code 8), counted apart from code 5, "trouble found". Two NTFs on one marker is the simulation's own. |
| M8 | **NOT COVERED**, partly plausible | SD has timing sheets: line 7299 "ALL TIMING" with "FOR OVER ALL TIMING SEE SC-4" and a "TRANSFER START LEAD TIMER" block (7307-7308). No limits are legible in the OCR. "Timing chain" is not a term in the SD. |
| M9 | **NOT COVERED** | See 1.3. No "sequence relay" anywhere in the SD, XB-III, E&O or the Transmission Engineering volumes. |
| M10 | **NOT COVERED**, and fine | All dates are the simulation's own. Slow-since-1981 sits inside the game's 1983 year. |

### 1.3 The sequence relay

**Verdict: the source does not support it.** `grep -i "sequence"` over
`SD_26030-01_djvu.txt` returns zero lines; so do `SEQ` and `SQ` as a relay
designator. The name is not in XB-III, in E&O (checked on the PDF text, whole
book), or in either Transmission Engineering volume on the circuit.

Where "sequence" does appear in the corpus, it is another part:

- WE-62 5396-5397 and 5416-5419: "Sequence Switch (Power-Driven Relay)", and
  "it always opens and closes the circuits wired to its contacts in the same
  order". A 1962 training lesson on dial switching, not a crossbar marker part.
- `BSRS 104.011` 11027: `Sequence Type, "A" Cam Roller & Spring Assembly`, listed
  under SWITCHES, and 11903: `Sequence Selector 28 Type 456.134`. These are
  repair-spec index entries for other equipment, with no description.

**Caveat on the SD.** The file is OCR of schematic drawings. The word `relay`
appears 18 times in 12,345 lines, so most relay designators and symbols did not
survive. "Not in the OCR" is not proof that no relay of that function is on the
drawings. If the claim matters, check the sheets themselves at
https://archive.org/details/bellsystem_SD_26030-01 .

**What the SD does offer for a marker payoff** (all would need the same
labelling care):

- "MARKER CONN PREF CONT CKT", the marker connector preference control circuit
  (index at 3139, sheets at 4444, 4468, 4476). This is the circuit that decides
  which marker a line link frame prefers, and it is the closest named analogue
  to a "cause that is not the marker".
- "DIAL TONE LOCKOUT CKT" (4486) and the make-busy circuits (3127, 3131).
- The XB-III chain: a false ground puts a check relay out of step so "the
  marker will time out" (14626-14627), and if the foreign-cross-or-ground
  relay operates "The marker will block in this condition and time out"
  (11949-11950). E&O p. 802 [819] adds that markers "call in a trouble
  recorder when necessary".
- E&O p. 682 [699] Table 16-1 lists, under Machine Switching, "Transmitter
  Timeouts", "Office Overflow", "FCG* & Supervisory Failures", "Receiver
  Timeouts" and "Equipment Irregularities", with the footnote "False cross or
  ground". These are real office-performance counts a marker problem would
  move.

**Recommendation for A7** (the decision is the phase's):

1. Keep Marker 2 as story. Label the "sequence relay", the number "2", the
   "third trial" and the eleven seconds as the simulation's own in the PR and
   in `SOURCES.md`.
2. If a sourced cause is wanted, point the payoff at the preference control
   circuit, or at the false-ground time-out chain, not at the sequence relay.
3. If it stays "third trial", the nearest sourced fact is "second trial on
   another marker"; the simulation's third is an extension.

## 2. Phase 7: the machine as story (C16, A4, A5)

### 2.1 C16: regulars, reports, bureau, records

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 581 [598] | The attendant's system shows "the date of the last trouble and the number of previous trouble reports" | `custdb` history line for a regular |
| E&O p. 581 [598] | Same list: "information on cable and other equipment failures that are affecting the particular customer's circuit" | A regular's report linked to a plant cause (feeds A7) |
| E&O p. 678 [695] | Repair efforts "initiated and tracked, and the final disposition recorded" | Closing and recording a regular's report |
| TTE-3 45951-45983 (heading "Trouble Reports and Requests for Credit") | The trouble ticket carries "service quality indicators such as a missed appointment or a subsequent report" and space for "the final resolution" of the problem | What a record holds; "subsequent report" is the period word for a repeat |
| TTE-2 52552-52553 | The repair service bureau is where "records of station locations, cable assignments, and customer services are maintained" | `custdb` contents |
| TTE-2 52576-52580 | LMOS stores "customer line card records" and supports "analysis of past trouble reports" (the TREAT program) | Looking up a regular's past reports |
| E&O p. 683 [700] | Code 5 "trouble found" versus code 8 "no trouble found" | A regular who keeps calling and whose line tests clean |

**Retention: no source.** Nothing in the corpus says how long a trouble ticket
or line record is kept. `grep` for retention, purge, history file and similar
finds nothing in E&O, TTE or BSTJ. The nearest are "final disposition recorded"
(above) and SARTS 4418-4421, a tester's log of "last 21 lines of commands"
(a console history, not a record rule). Any retention figure the game states is
the simulation's own.

**Regular arcs and resolutions before 1 January:** no source; all four are the
simulation's own.

### 2.2 A4 and A5: finds, fragments, the predecessor

| Source | Passage | Serves |
| --- | --- | --- |
| `02 Administrative Advice (DEC)` 433-439 | A short list of logs under `/usr/adm`: `errfile` (hardware errors), `ctlog`, and `sulog`, "a log of those who execute the superuser command" | A5: `sulog` is a real, documented log; A4: the shape of admin files worth `grep`ping |
| `03 Administrative Advice (3B20S)` 369 | Same line for the 3B20S | Same; the 3B20S is closer to a 1983 telephone-company machine |
| `UNIX System User's Manual, System V (Release 1)` 31992-31999 | `su(1)`: "Su allows one to become another user without logging off" | A5: what `su root` is |
| `07 UNIX System Accounting` 23 | "The login and init programs record connect sessions by writing records into" `/etc/wtmp` (OCR reads `/ete/wtmp`) | A5: who was logged in at 03:47 |
| `01 UNIX Documentation Road Map` 393 | `grep(1)`: "search a file for a pattern" | A4: the game's own `grep` verb |

**Gaps.**

- Not in the corpus: the *format* of an `sulog` line. The game's
  `BADSU 11/14 07:52 - tty03 mreyes-root` (`npc.py`, teletype channel) is the
  simulation's own unless sourced from outside.
- The `mreyes-root` story, the contents of every fragment, and the
  predecessor thread are the simulation's own; no document describes a craft
  person leaving a machine in this state.
- A plausible reason a predecessor is gone: E&O p. 599 [616] says on-site
  work "can be performed on a dispatch basis from a central pool". That is
  real context for a transfer to a centralised group, not for anything the
  predecessor did.

## 3. Phase 8: board cases (C21, C22, A7, A8, A9, A11)

### 3.1 Crossbar marker faults (A7)

See section 1 for Marker 2. For marker faults in general:

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 802 [819] | Markers "recognize line busy, trouble, intercept, and vacant-line conditions" and "call in a trouble recorder" | What a marker does when it finds trouble |
| XB-III 5572-5574 | Trouble release: "on second trial the sender will seize another marker" | A retry, with a different marker, as the visible symptom |
| XB-III 11949-11950, 14626-14627 | A foreign ground "will block" the marker, which will "time out" | A fault whose symptom is a time-out, not an alarm |
| XB-III 14521-14527 | A jack on the trouble indicator frame exists to "prevent a large number of trouble indicator records" from a cut cable | Trouble indicator records are the craft's evidence |
| E&O p. 599 [616] | "electromechanical switching systems require more extensive periodic maintenance" | Why a crossbar office has regular minor faults |
| E&O p. 682 [699] | NSPMP machine-switching components (see 1.3) | The counts a marker fault would move |

### 3.2 Root cause across reports (A7)

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 679 [696] | "They are a quantification of symptoms rather than causes" | The thesis of A7: reports are symptoms |
| E&O p. 581 [598] | The attendant sees "information on cable and other equipment failures that are affecting the particular customer's circuit" | `report show` "see also" |
| E&O p. 581 [598] | Trouble location "is often the most difficult and time-consuming step in the maintenance process" | Why the cause is found by the player, not given |
| E&O p. 599 [616] | "some failures can affect a large number of customers" (electronic offices) | A rare office incident with many members |
| TTE-3 45982-45983 | The ticket has space "to indicate the cause of the complaint" | Recording the cause when it is found |

How many reports a planted cause spawns (3-5), tour 9 or 10 timing: no
source; the simulation's own.

### 3.3 Dispatch to a place (C21) and callbacks (C22)

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 581 [598] | Trouble location is "determining whether the trouble is in central office, loop, or premises equipment" | The three places a dispatch can be wrong about |
| E&O p. 581 [598] n. 4 | "In the case of special services, troubles may be traced to interoffice facilities." | A fourth place, for special services |
| E&O p. 582 [599] | Remote testing helps "eliminating false dispatches" | The cost of a wrong place |
| E&O p. 582 [599] | "Premises repair generally requires dispatching a craftsperson." | Which dispatches are unavoidable |
| SARTS 3034-3035 | "Craftspeople were therefore dispatched with greater accuracy" once faults could be isolated | Accuracy as the measure of a good dispatch |
| E&O p. 581 [598] | The attendant "talks with the customer in an attempt to identify the cause" | C22: callback topics |
| E&O p. 582 [599] | The repair is done when "the customer has been notified and is satisfied" | When a callback is owed |

**Gaps:** "section" as a unit of dispatch (the game's `cable.py` sections),
the cost of a callback in `COST_CALLBACK`, and which questions narrow which
fault sets are the simulation's own.

### 3.4 Cascades and pressure alarms (A8)

| Source | Passage | Serves |
| --- | --- | --- |
| TTE-2 52457-52463 | Cables "are maintained under gas pressure to impede the entrance of water", giving "indications of such breaks by changes in gas pressure" | Pressure alarm before the first report. `SOURCES.md` currently lists cable pressurisation as outside practice; this passage is a corpus source for it |
| TTE-2 6746-6747 | Underground cable sheaths "ultimately admit moisture and the affected lengths of cable must be replaced" | The wet binder |
| TTE-2 52459-52460 | Transmission "deteriorates significantly when moisture enters transmission cables" | Why a wet binder worsens |
| E&O p. 177 [194] | "Switching overloads can spread throughout the network if appropriate countermeasures are not taken." | The general shape of a cascade |
| E&O p. 177 [194] | "such congestion tends to sustain itself" | A cascade that does not stop alone |
| E&O p. 179 [196] | In the simulated overload, switching timeouts "increase rapidly after 40 minutes" | A cascade with a clock, with the real timescale |
| TTE-3 18987-18988 | This "snowballing" effect accounts for the congestion when calls rise above forecast | Same, in the period vocabulary |
| `BSTJ_V60N08_198110` 8630 | "This situation has a cascading effect" | The only literal "cascade"; it is about trunk use, not faults |

**Gap:** a pair added per shift hour, faster in rain, is the simulation's own
rate. No source gives a rate of moisture spread.

### 3.5 Transients and retest (A9)

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 579 [596] | "many trouble indications are transient, correcting verified troubles receives first priority" | The grounding for A9, in the Bell System's own words |
| E&O p. 579 [596] | Trouble verification is "determining if a reported trouble condition still exists" | The retest is a real step |
| E&O p. 579 [596] | "An interval may occur between trouble notification and the start of the trouble-location function" | A delay before the retest is plausible |
| E&O p. 683 [700] | Code 8 "no trouble found" | "No new close code": a transient clears to the existing NTF code |
| TTE-3 45980-45981 | The ticket records "a subsequent report" | The definition of a repeat |

**Gap:** the retest one hour later is the simulation's own figure; the source
gives no interval.

### 3.6 Network cases and congestion on the board

Not a phase 8 row, but a phase 8 board case may want it. See section 4.1.

### 3.7 Toll fraud (A11): detection and history only

**Almost nothing in the corpus. Treat the row as the simulation's own.**
The word "fraud" occurs in E&O three times in passing and nowhere else in
`attached_assets/`. Verified by `grep -i fraud` over all 65 text files and over
the E&O PDF text.

| Source | Passage | Use |
| --- | --- | --- |
| E&O p. 282 [299] | In a list of needs that in-band signalling cannot meet: "(8) reduction of fraud" | The only sentence that names fraud as a network problem. One line of history |
| E&O p. 475-476 [492-493] | Coin phones must "withstand abuse by customers, fraud attempts, vandalism" | Fraud as a station-side concern |
| E&O p. 52 [69] | "Control of outgoing call possibilities from selected lines may also be important to avoid abuses." | A real control, in customer switching |
| E&O p. 678 [695] | Billing integrity is a measured service quality; AMA errors are its example | The measurement side: billing records |
| E&O p. 682 [699] | NSPMP Billing component, "Lost Billing" | What a billing count looks like |
| E&O p. 179 [196] | A higher-than-normal ACH with a normal CCH means "demand is heavy"; a high CCH means short holding times | The only pattern-reading method in the corpus, and it is about congestion. An A11 `traffic` anomaly can borrow the *form*, not claim it as fraud detection |

**Constraint for the phase.** The corpus has 2600 Hz only as signalling
engineering: `BSTJ_V61N04_198204` 8934-8937 (a pack's tone generator) and
`BSRS 104.011` 4764 ("FYA 2600 HZ Tone Supply & Transfer Type"). Do not set
either beside the fraud thread. The brief for A11 is detection and history,
with no tones and nothing that works; these passages would invite the join.

**Not in the corpus:** any history of toll fraud (dates, cases, the Bell System
response), detection methods, security staff, or how a fraud case is
investigated. History in A11 needs an outside source marked as such, or the
plot is marked invented, as the row's acceptance test already says.

## 4. Phase 9: positions (C20)

### 4.1 NOC (network management)

The best-covered topic. E&O section 5.6 ("Network Management", printed
pp. 176-181 [193-198]) is a sequence of ready-made desk material.

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 177 [194] | "It is the responsibility of network management to prevent such deterioration of service" | The NOC's job |
| E&O p. 177 [194] | After 20 to 30 seconds "the transmitter will time out and route the call to a reorder tone" | A mechanism the NOC pressure can show |
| E&O p. 177 [194] | "since high blocking generates more reattempts per call" | Reattempts feed the load |
| E&O p. 179 [196] | "Signals indicating all-busy status for trunk groups are provided in Network Management Centers." | What the NOC board shows |
| E&O p. 179 [196] | ACH and CCH for trunk groups "as frequently as every 5 minutes" | A real sampling interval for `traffic` |
| E&O p. 180 [197] | "The most effective indicators of switching congestion are dial-tone delay" and incoming digit-receiver delay | Which two numbers a NOC reads |
| E&O p. 180 [197] | "Restrictive controls eliminate or reduce routing alternatives" ; expansive controls permit "additional nonstandard routing" | The verb: restrict or expand |
| E&O p. 181 [198] Table 5-1 | Controls: directionalization, cancellation of alternate routing, rerouting, code blocking, DOC, SDOC, each with a type and function; code blocking at "50 percent, 75 percent, or 100 percent" | The control menu, complete |
| E&O p. 181 [198] Table 5-1 note | Manual controls "may be applied too slowly and are often left in effect too long" | The NOC's pressure: lifting a control in time |
| E&O p. 181 [198] | DOC controls last "only about 10 seconds"; "preferred over manual controls" | Automatic versus manual |
| E&O p. 179 [196] | Christmas Day, Mother's Day and other holidays "produce intertoll trunk congestion"; Mount Saint Helens (May 1980) is the example of a focused overload | Dated, sourced tour-13 and event material |
| E&O p. 180 [197] | Eastern traffic can be routed "via Central, Mountain, or even Pacific" on Christmas morning | A real expansive control, with a reason |
| TNDS 4088-4097 | "The Network Management Center (NMC) keeps the network operating efficiently when unusual traffic" | The NMC's own description, 1983 |
| TNDS 3226-3228 | Status measurement "indicates the presence or absence of a condition", usually a lamp | A NOC board lamp |

**Gaps:** the one verb and one pressure per desk are design (row text); which
controls the simulation offers, and how the game scores a lifted control, are
its own. No source gives a control's effect size beyond "about 40 percent" for
DOC (Table 5-1).

### 4.2 Office (switching) desk

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 599 [616] | "system alarms indicating trouble conditions or failures are transmitted to a centralized location" for unstaffed offices | The alarm-driven desk |
| E&O p. 599 [616] | "do not afford the craft force much practice" on hard electronic troubles; "centralized maintenance and self-diagnostics a necessity" | Why an office desk needs a specialist |
| E&O p. 633 [650] | An electronic office "can operate unattended, either entirely or for substantial parts of each day" | Unattended offices, remote maintenance teletype |
| E&O p. 632-633 [649-650] (14.3.2) | The Switching Control Center System; master control center lamps and keys; maintenance teletype | `SCC to office` and the teletype channel |
| E&O p. 567 [584] (12.5.3) | "Telephone buildings use a variety of alarm systems to indicate equipment" | The alarm panel |
| E&O p. 682 [699] | NSPMP machine switching components (1.3) | Office performance counts as the scoreboard |
| Section 3.1 | Marker and time-out material | Office-desk faults |

### 4.3 Special services desk

| Source | Passage | Serves |
| --- | --- | --- |
| E&O p. 40 [57] | "All other services are considered special services (often called specials)." | Definition |
| E&O p. 86 [103] | Circuits "dedicated to a specific customer to provide special services are called special-services circuits" | Definition, with interoffice circuits included |
| E&O p. 581 [598] n. 4 | Special-services troubles "may be traced to interoffice facilities" | A different place to look than a loop |
| SARTS 2975-2978 | "The total Special Service Center (SSC) concept provides testing support" ; the aim is "one person with control and testing of a large variety of circuits" | The SSC desk's whole premise |
| SARTS 2988-2989 | "Many special-service circuits bypass conventional switching systems" | Why access is hard: the desk's pressure |
| SARTS 3940-3951 | "The problem of testing special-service circuits is one of obtaining access" at the correct point; access points sit on the Circuit Layout Record card | The verb: get access, read the CLR |
| SARTS 3101-3106 | An earlier "centralized repair service center" used "No. 14 local test desks" with dedicated test trunks | Period context for the older desk |
| SARTS 4418-4421 | The test position keeps "the tester's last 21 lines of commands" | A supervisor's history log |
| `bstj62-10-2911` (title line 2953) | "A Model for Special-Service Circuit Activity", December 1983 | Counts and holding times of special circuits; read before using any number from it |
| `806220` (1A2 key telephone service) | One hit on special services; otherwise station-side | Optional: installer-side faults |

**Gap:** what a special-services *ticket* looks like. SARTS gives access
points and the CLR but no ticket format. `screens/tickets.py` and
`special_services.py` formats are the simulation's own.

### 4.4 Repair desk

Covered by 2.1 and 3.2 to 3.3 plus E&O pp. 579-582 [596-599]: the six
functions of corrective maintenance (detection, notification, verification,
location, repair, service verification) are already in `SOURCES.md`.

## 5. Gaps: rows whose content is the simulation's own

For each row, what has no source in `attached_assets/` or the E&O PDF.

| Row | Has a source for | Must be labelled the simulation's own |
| --- | --- | --- |
| C16 regulars | What the attendant sees; code 5 and 8; "subsequent report" | The four arcs and their endings; any retention period |
| A4 finds | Real admin logs and `grep` | Every fragment's text and the tour gating |
| A5 predecessor | `sulog` exists and what it logs; `su(1)`; `wtmp` | The `sulog` line format (unless sourced elsewhere); the `mreyes-root` story |
| C21 dispatch | Three places (office, loop, premises); false dispatches | "Sections" and what the wrong-section crew finds |
| C22 callbacks | The attendant questions the customer | Topics, cost, and the fault sets a topic narrows |
| A7 Marker 2 | Markers, retries, time-outs, trouble recorder, NTF, dial tone speed | "Sequence relay", "third trial", "Marker 2", eleven seconds, "since 81", "timing chain" as a failure site |
| A7 root causes | Symptoms versus causes; "see also" concept | Member counts (3-5), tour 9-10 timing |
| A8 cascades | Gas pressure and moisture; congestion spreading; 40-minute timeout rise | Rates (a pair per hour, rain factor) |
| A9 transients | "many trouble indications are transient"; verification; code 8 | The one-hour retest |
| A11 toll fraud | Only "(8) reduction of fraud" and billing-integrity measures | Everything else: the anomaly, the mail, the plot; history needs an outside source or an "invented" mark |
| C20 NOC | Controls, indicators, holidays, the NMC | Which controls are offered and how they score |
| C20 office | Alarms, SCC, NSPMP counts | Alarm and teletype formats |
| C20 special services | SSC, CLR, access, test position | Ticket format, the specific circuits |

## 6. Files checked and found of little use here

- `BSRS 104.011`: an alphabetical *index* of repair-specification sections by
  equipment type (issue date 1 July 1983 per the previous review). Entries
  have a number and a title, no content. Useful only for naming a real Bell
  System Practice number, never for a claim about what a procedure says. It
  has no crossbar, test desk or special-services entries.
- `bellsystem_SD-1C900-01` (3A central control): no marker or trouble-desk
  content; supports the `3a` screens only.
- The UNIX volumes beyond the five passages in 2.2: no use for these phases.
- Not surveyed beyond keyword hits: `BSTJ_V56N10_197712`, `BSTJ_V58N05_197905`,
  `BSTJ_V60N08_198110`, `BSTJ_V61N04_198204`, and the TSPS and Transaction
  Network papers. A phase that needs more should grep, not read.
- The `Image*` files are UNIX documentation catalogues.

## 7. Verification

Quotes were checked against the E&O PDF text and the repo files with `grep` and
by line range. Before a phase cites a line, run `grep -n` for the quoted words
in the named file; the line numbers are for the committed text and will drift
if the files are ever re-extracted.
