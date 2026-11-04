# Sources

Every historical value in this simulation is one of three things: verified
against one of the period documents listed below, sourced externally and
marked as such, or explicitly recorded as the simulation's own invention.
This file is the map for the first two.

## The period documents

The code cites a set of period documents. Their searchable text is not part
of this repository; the maintainer keeps it as plain text, so a claim in a
docstring can be checked with `grep` against a copy:

```
grep -n "1300 ohms" Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt
```

### Most cited

| Document | Cited for |
| --- | --- |
| Engineering and Operations in the Bell System, 2nd ed. (1984) | Switching hierarchy and machine capacities, the corrective maintenance sequence, loop design limits (1300 and 1500 ohms with their length bands), coin station line current, the N0/1X area code format, NSPMP measurement weights |
| Telecommunications Transmission Engineering, Vols. 1-3 (1977) | L-carrier spectra, 1004 Hz loss objectives, local cable capacitance at 0.083 uF/mile, balance test lines, SF signalling levels |
| Bell System Technical Journal (1976-1982) | The 100/102/105-type far-end test line series, the remote office test line and 52A responder, CAROT, the processor controlled interrogator, channel maintenance states |

### Full text inventory

Sixty-five files, 968,959 lines and 2,668,827 words of searchable
text, none of them in this repository. Counted in lines and words rather than megabytes because that is
what the number is for: these are grepped, and `grep -n` answers in
line numbers.

| File | Lines | Words |
| --- | ---: | ---: |
| `00 Frontmatter and Table of Contents_djvu.txt` | 127 | 215 |
| `01 Introduction_djvu.txt` | 64 | 303 |
| `01 UNIX Documentation Road Map_djvu.txt` | 657 | 2,526 |
| `02 Administrative Advice (DEC)_djvu.txt` | 1,065 | 5,425 |
| `02 Editor Tutorial_djvu.txt` | 1,668 | 6,377 |
| `03 Administrative Advice (3B20S)_djvu.txt` | 759 | 4,093 |
| `03 UNIX for Beginners_djvu.txt` | 2,086 | 8,892 |
| `04 Setting Up The UNIX System (DEC)_djvu.txt` | 1,861 | 10,880 |
| `04 UNIX Shell Tutorial_djvu.txt` | 3,006 | 17,959 |
| `05 C Reference Manual_djvu.txt` | 2,517 | 13,620 |
| `05 Setting Up The UNIX System (3B20)_djvu.txt` | 2,254 | 12,219 |
| `06 Auto Call Facility Installation_djvu.txt` | 254 | 1,166 |
| `06 UNIX Programming_djvu.txt` | 1,722 | 9,928 |
| `07 UNIX System Accounting_djvu.txt` | 1,851 | 7,627 |
| `08 File System Checking_djvu.txt` | 1,316 | 7,890 |
| `09 LP Spooling System_djvu.txt` | 947 | 4,872 |
| `10 UNIX System Remote Job Entry_djvu.txt` | 1,738 | 8,261 |
| `11 UNIX System Activity Package_djvu.txt` | 537 | 3,387 |
| `12 Modification Request_djvu.txt` | 27 | 41 |
| `301-925_I1_djvu.txt` | 58,933 | 216,450 |
| `806220_djvu.txt` | 11,241 | 26,569 |
| `BSRS 104.011_djvu.txt` | 15,908 | 24,487 |
| `BSTJ_V56N10_197712_djvu.txt` | 25,898 | 121,712 |
| `BSTJ_V58N05_197905_djvu.txt` | 12,651 | 49,987 |
| `BSTJ_V60N08_198110_djvu.txt` | 20,359 | 100,161 |
| `BSTJ_V61N04_198204_djvu.txt` | 21,077 | 97,998 |
| `Crossbar-Dial-System_Section-III_Part-2-Terminating-Circuits_djvu.txt` | 22,714 | 36,392 |
| `Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt` | 75,884 | 290,608 |
| `Image071317211624_djvu.txt` | 4,578 | 11,373 |
| `Image092317124839_djvu.txt` | 3,707 | 12,349 |
| `Image092317125247_djvu.txt` | 4,551 | 16,747 |
| `SD_26030-01_djvu.txt` | 12,345 | 17,731 |
| `Telecommunications_Transmission_Engineering_Vol_1_Principles_2ed_1977_djvu.txt` | 51,506 | 197,647 |
| `Telecommunications_Transmission_Engineering_Vol_2_Facilities_1ed_1977_djvu.txt` | 59,156 | 237,641 |
| `Telecommunications_Transmission_Engineering_Vol_3_2ed_1977_djvu.txt` | 55,308 | 195,939 |
| `UNIX System User's Manual, System V (Release 1)_djvu.txt` | 58,098 | 221,177 |
| `WE_Fundamentals_of_Telephony_Lesson_1_Mar62_nicer_djvu.txt` | 18,351 | 31,004 |
| `bellsystem_SD-1C900-01_djvu.txt` | 273,678 | 205,429 |
| `bstj50-7-2085_djvu.txt` | 5,485 | 17,841 |
| `bstj57-10-3371_djvu.txt` | 5,851 | 21,336 |
| `bstj57-10-3455_djvu.txt` | 4,850 | 15,161 |
| `bstj57-6-1897_djvu.txt` | 3,136 | 8,314 |
| `bstj57-6-1899_djvu.txt` | 3,319 | 9,626 |
| `bstj57-6-1971_djvu.txt` | 4,290 | 13,045 |
| `bstj57-6-2049_djvu.txt` | 5,153 | 21,163 |
| `bstj57-6-2103_djvu.txt` | 3,756 | 11,543 |
| `bstj57-6-2115_djvu.txt` | 4,259 | 15,326 |
| `bstj57-6-2155_djvu.txt` | 4,314 | 15,274 |
| `bstj57-6-2177_djvu.txt` | 4,518 | 16,496 |
| `bstj57-6-2233_djvu.txt` | 3,817 | 12,983 |
| `bstj58-6-1347_djvu.txt` | 4,180 | 10,424 |
| `bstj59-4-501_djvu.txt` | 5,128 | 17,408 |
| `bstj59-9-1757_djvu.txt` | 3,539 | 11,548 |
| `bstj59-9-1793_djvu.txt` | 4,118 | 14,524 |
| `bstj59-9-1811_djvu.txt` | 3,931 | 13,108 |
| `bstj61-6-981_djvu.txt` | 6,548 | 15,278 |
| `bstj61-7-1589_djvu.txt` | 3,929 | 10,839 |
| `bstj61-9-2459_djvu.txt` | 3,981 | 13,072 |
| `bstj62-10-2911_djvu.txt` | 4,940 | 15,920 |
| `bstj62-3-765_djvu.txt` | 4,174 | 11,094 |
| `bstj62-7-2127_djvu.txt` | 4,792 | 14,807 |
| `bstj62-7-2345_djvu.txt` | 6,327 | 16,103 |
| `cman74_djvu.txt` | 6,299 | 19,296 |
| `cman_djvu.txt` | 5,463 | 19,759 |
| `reader_djvu.txt` | 18,463 | 50,457 |

## Sourced from outside this repository

Some of what the simulation depicts is not in any of the period documents above. Where that
is so, the module says where it came from and what it will not claim. This
is the index of those.

| Claim | Where it is used | What it rests on |
| --- | --- | --- |
| Exchange cable is built in binder groups of 25 pairs, each binder taking the colours of the pair with its own number; 24 groups make 600 pairs and violet-slate is never used as a binder | `src/bell_system/cable.py` | The 25-pair colour code, published widely and consistently across telephony references |
| Cable is pressurised with dry air to keep water out, and pressure falls before water enters | `src/bell_system/cable.py` | Outside plant air pressure practice |
| Trouble can clear before anyone finds it, so a retest an hour on can read clean on a line that read faulty | `src/bell_system/reports.py` `transient_after` | Engineering and Operations in the Bell System, 2nd ed. 1984, p. 579 [596]: "many trouble indications are transient", and verification is "determining if a reported trouble condition still exists". **The simulation's own:** that it is ground, cross and foreign voltage that behave so, that a quarter of those reports do, and that they clear 20 to 50 elapsed minutes after the first test. The book attests the phenomenon and no rate |
| A dispatch names the place the trouble is, and a crew sent to the wrong place finds nothing and costs the trip | `src/bell_system/reports.py` `send_crew`, `_named_job`; `src/bell_system/screens/cases.py` | Engineering and Operations in the Bell System, 2nd ed. 1984, p. 581 [598] (locating trouble as "determining whether the trouble is in central office, loop, or premises equipment") and p. 582 [599] (remote testing "eliminating false dispatches"). **The simulation's own:** the cable and binder group as the unit of a splicer's dispatch, the `cable/binder` form, and the minutes a wrong trip costs. A pressure alarm opens a plant job of its own (`PJ-001`, no customer) that a splicer can be sent to by `report dispatch PJ-001 cable <c>/<b>`; the trip is charged to the job and to no report, and so is a dispatch typed after some other report that names the group a job is open on (`screens/bureau.py` `_dispatch_report`, `plantjobs.py`). A wet report's own group is that report's trouble and is charged to it. A report on the job's sheath is not cleared with it and is dispatched, and judged, on its own |
| A group of toll trunks shows seizures far above the hour's usual with a hold of a few seconds, a stated share of the excess between midnight and 5 am, and a transmission engineer writes that it is not congestion and has gone to Security | `src/bell_system/data/fraud.py` `exception_block`, `note` | Two sourced facts, both Engineering and Operations in the Bell System, 2nd ed.: until 1976 signaling was almost entirely carried on the channel that carried the voice (the signaling section, printed p. 272; the note says only that most of a trunk's signaling is still carried so, which the same section supports), and "reduction of fraud" is item (8) in the list of needs for common-channel signaling (printed p. 282). **The simulation's own and marked invented on the screen:** the group, its route, every count, the hour of the excess, the number of lines, and the whole case. No period document gives a history of toll fraud, a detection method or what a bureau did about a case, and nothing from the period documents' signalling engineering is used here: no tone, frequency or procedure |
| A callback can ask one question (when it began, whether it is the same on other telephones, what is heard on picking up) and the answer narrows what the trouble can be without naming it | `src/bell_system/data/callbacks.py` `TOPICS`, `narrowed` | The simulation's own, as `REPORT_SYMPTOMS` is. The conditions are the documented ones (`data/trouble.py`); what a customer says of each is invented, and no source gives a script for a bureau's call to a customer. Which conditions share an answer is the design: the true condition is always among those an answer fits, no answer fits every condition, and for every pair of questions there is a condition whose two answers fit conditions that different forces clear (a cross and a wet sheath both creep up and are both shared with a neighbour) |
| Water in a sheath goes on spreading until somebody opens it, faster in rain, and the pressure alarm comes before the customers do | `src/bell_system/cable.py` `leak`, `begin_leak`, `LEAK_PSI_PER_HOUR`, `FIRST_PAIR_AFTER` | Cable pressurisation practice (the row above: pressure falls before water enters) and the same Engineering and Operations passages for wet cable worsening with rain. **The simulation's own:** a pair an hour, a pair every fifteen minutes in the heaviest rain, 1.5 psi an hour, the alarm at 2.5 psi (a hundred minutes in), the first customer a hundred and fifty minutes in, one tour in two from the second carrying such a leak, and the `PRESSURE ALARM` line on the maintenance teletype. No source consulted gives a rate or a threshold |
| One failure can be many customers' troubles, and the attendant's screen shows the failures bearing on a circuit; a crossbar marker that cannot finish a call times out | `src/bell_system/cases.py`, `src/bell_system/data/cases.py` | Engineering and Operations in the Bell System, 2nd ed. 1984, p. 679 [696] (the measurement plan counts "a quantification of symptoms rather than causes"), p. 581 [598] (the screen "information on cable and other equipment failures that are affecting the particular customer's circuit") and p. 802 [819] (marker time-out). **The simulation's own:** that there are two sorts of case here, a failed marker and a cut cable; three to five reports and three or four; which of two or three conditions each is (a marker: a false cross or ground, or faulty line equipment; a dig: an open, a short or a ground, all Outside plant work); the minutes they arrive in; one tour in three carrying one from the fourth, drawn from the career's seed and the tour so that two careers are not dealt the same; Marker 2 on tour 9 or 10; the sequence relay, the number 2, the third trial and the eleven seconds, none of which is in `SD_26030-01` |
| RFC 850 (June 1983) header set, order, `.UUCP` site suffix, full day name in `Date`, and reply-format `Path` lines required until 1 January 1984 | `src/bell_system/filesystem.py` netnews spool | RFC 850 itself, including its worked example, from which the relay sites cbosgd, mhuxj, mhuxt and eagle are taken |
| The August 1983 AT&T strike: 7-28 August, and a settlement of 5.5 per cent in the first year and 1.5 in each of the next two | `net.misc/88` in the netnews spool | Published accounts of the strike |
| The 1956 consent decree kept AT&T out of the computer business; the 1982 decree let it in, which is why System V arrived commercially | `net.unix-wizards/121`, `/usr/doc/why.unix` | Published antitrust history, consistent with Engineering and Operations on divestiture |
| Ritchie and Thompson, CACM 17(7), July 1974, 365-375; Thompson and Bourne in BSTJ 57(6) part 2, July-August 1978, at 1931-1946 and 1971-1990; Feldman on make in SP&E 9(4), April 1979, 255-265; Kernighan on pic in SP&E 12(1), January 1982, 1-21 | `/usr/dict/papers`, read by `refer(1)` | Each citation checked against the publication record |
| Teletype Model 33 at 110 baud, ten characters a second; Model 43 (1977) switchable to 110 or 300, ten or thirty | `display.pacing` in `src/bell_system/settings.py` and `terminal.py` | Teletype Corporation specifications. The eleven-bit frame at 110 and ten above it is what makes those published character rates come out right |
| ANAC reads back the calling number; a 102-type line is a milliwatt supply at 1004 Hz and 0 dBm; a 100-type line is a quiet termination; a loop around is a pair of numbers, one toned and one silent | `src/bell_system/data/testlines.py` | Plant test number practice. The dialable codes are **not** claimed: they were local to each office, and the module says so |
| Western Electric equipment in-service years (302, 500, 1500, 2500, 1A2, No. 1 and No. 5 crossbar, 1ESS, 1AESS, 4ESS, 5ESS, T1, D4, L4, TD-2, TH-3) | `src/bell_system/screens/plant.py` | Published Bell System equipment history. Anything the sources consulted did not settle is absent from the table rather than guessed at |
| Long-haul calling jams the intertoll trunks on Mother's Day and on Christmas Day | `src/bell_system/data/homes.py` `noc` notes | Engineering and Operations in the Bell System, 2nd ed. 1984, section 5.6 (`grep -n "Mother's Day"`): Christmas Day and Mother's Day "produce intertoll trunk congestion"; local and intrastate toll traffic is light and long-haul traffic is heavy, and the book says the total message volume on those days is "well below that of the average business day". So the note says the trunks jam and does not call either day one of the heaviest of the year. **The book says nothing of how long this has been so**, and the note no longer does |
| A geosynchronous satellite adds about 250 milliseconds one way, so a question and its answer wait about half a second | `src/bell_system/npc.py` transmission chatter, `src/bell_system/screens/plant.py` `satellite` | Engineering and Operations in the Bell System, 2nd ed. 1984: delay "on the order of 250 milliseconds one way" and "the 250-millisecond, 1-way transmission delay from one earth station up to the satellite and down to another" (`grep -n "250 milliseconds"`). The half second is that figure doubled for a round trip, which is arithmetic. The altitude in `satellite` is the usual figure for a geostationary orbit and is not in the period documents |
| At divestiture the operating companies keep exchange service within a LATA, the interexchange facilities are transferred to AT&T, and service between LATAs is offered by AT&T and other interexchange carriers | `src/bell_system/filesystem.py` `DIVESTITURE_MEMO` and the net.general post `/usr/spool/news/net.general/203` | Engineering and Operations in the Bell System, 2nd ed. 1984, section 1.3: "Facilities, personnel, and accounts used to provide interexchange services ... must be transferred from the BOCs to AT&T", and the BOCs "offer regulated telecommunications services within LATAs, while AT&T and other interexchange carriers (ICs) offer services between LATAs" (`grep -n "interexchange"`). The memo's wording is the simulation's own. An earlier draft said the toll network "above class 4" stays with AT&T; the book divides the work by LATA and not by class of office, so that claim is gone |
| The machine in the game is UNIX Version 7, released in 1979 | `src/bell_system/filesystem.py` `MOTD`, the shell and its manual pages | The release and its year are sourced: `reader_djvu.txt` places the Seventh Edition in 1979, and `03 UNIX for Beginners_djvu.txt` says "this paper describes Version 7 UNIX". **That a repair bureau's machine still ran Version 7 in November 1983 is the simulation's own choice.** No source consulted says which release an operating company ran there, and nothing here claims it did |
| The calendar of the thirteen tours: 14 November 1983 (Monday) to 31 December 1983 (Saturday), four days apart, the last pulled back onto 31 December | `src/bell_system/clock.py`, `src/bell_system/data/tours.py` | The epoch and the forty-eight days are from Engineering and Operations as `clock.py` quotes it; the four-day stride is the simulation's own. The weekdays are derived by calendar arithmetic. A test checks `tours.py` against the clock |
| Thanksgiving was Thursday 24 November 1983, and Christmas Day was Sunday 25 December 1983 | `data/tours.py` (tours 3, 4, 11 and 12) | Derived. Thanksgiving is the fourth Thursday of November, a rule outside the period documents; the Thursdays that month are 3, 10, 17 and 24. Christmas Day is a fixed date and its weekday is arithmetic |
| On Christmas Day local and intrastate calling is light and long-haul interstate traffic far exceeds engineered capacity; network management answers with controls such as cancelling alternate routing and rerouting across time zones | `data/tours.py` tour 11 | Engineering and Operations in the Bell System, 2nd ed. 1984, section 5.6 and Table 5-1. Nothing is claimed about 24 December itself: the beat is preparation, and what the office is asked to do is the simulation's own |
| Tour briefings, goals, set pieces and the nightly article | `data/tours.py` | The simulation's own, except where a beat is marked `SOURCED`, which names the document: the memo and bulletin in `/usr/doc`, E&O above, or RFC 850. Every beat carries one of the two tags, `events detail` shows it, and no real person is quoted: every poster in the news is made up. A player who moves the epoch gets the routine and no set pieces |
| The divestiture assignment: twenty-one wholly owned operating companies, two AT&T held a minority of (SNET, Cincinnati Bell), Nevada Bell wholly owned by Pacific Telephone, four Chesapeake and Potomac companies, and the Pacific Telesis / Ameritech / Bell Atlantic groupings in full | `src/bell_system/data/companies.py`, `company(1)` | Engineering and Operations in the Bell System, 2nd ed. 1984, figure 1-9 and the surrounding text — quoted in the module |
| The NYNEX, BellSouth, Southwestern Bell and US West groupings | the same table | Externally sourced; the book's OCR of figure 1-9 gives only three groupings in full. Each is marked `verified=False` and prints a `?` in `company all` |
| Close codes: Engineering and Operations counts customer-reported troubles in the switching performance plan as "trouble found" (code 5) or "no trouble found" (code 8), separately. The simulation offers only those two on every report, and scores a wrong one | `src/bell_system/data/trouble.py` `DISPOSITIONS`, `src/bell_system/progression.py` | Engineering and Operations in the Bell System, 2nd ed. 1984, section 16.4. **A simplification:** the plan counts the two codes for reports attributable to switching equipment, and the book names no other codes. That a craftsperson's close was judged right or wrong against the line's real fault, and the weights that follow from it (55, 35, 20, 50), are the simulation's own |
| The audit at the end of the last tour: dispositions audited, open reports handed over with the craftsperson's name on them, and a verdict of passed, passed with exceptions or failed | `src/bell_system/screens/turnover.py`, `src/bell_system/npc.py` | The memo of 1 November says dispositions "are audited after transfer" and that open reports go over "with your name on them", and that is all it says. The thresholds (a tenth of dispositions not matching the line is a finding, a quarter a failure) and the wire chief's words are the simulation's own |
| The qualification ladder (Loop and Station to Toll), the number of correct closes for each sign-off, and the commands each opens | `src/bell_system/progression.py` | The simulation's own. No source consulted gives sign-off counts, or says a sign-off gated a command. The counts are tuned by `tools/index_calibration.py ladder` so the ladder can be climbed in thirteen tours |
| The five KPIs (mean time to repair, commitments met, right-first-time dispatch, repeat rate, backlog age), the per-tour index, the board-cleared meter and the commendations | `src/bell_system/progression.py` `compute_kpis`, `src/bell_system/data/commendations.py` | The simulation's own. Engineering and Operations in the Bell System counts customer-reported troubles under the switching performance plan (close codes 5 and 8, see above), and no source consulted defines these five measures for a craftsperson, so none is presented as a Bell System figure. The definitions, the five-close threshold below which they read PROVISIONAL, and every commendation's name and test are the simulation's own. No source for awards or commendations was consulted, and none is claimed to have existed |
| The tour ledger (mean time to repair and share of closes that matched the line, each placed among ten simulated peers) | `src/bell_system/ledger.py`, `src/bell_system/data/peers.py`, `tools/index_calibration.py` `peers` | The simulation's own. No source consulted publishes a distribution of repair times or of dispositions for craftspeople, so the peers are not historical and no office is claimed to have been ranked this way. They are careers the calibration bot played at several skills and paces, regenerated whenever the balance changes, and the ledger labels them as the simulation's own. Aggregates only; nothing in it is about a report |
| The finds and the thread of the last holder of the sysop position: sixteen numbered files (`finds`), the unsent letter, the record journal, the chief's list, the scratch notes, and the groups (`craft`, `uucp`, `adm`, `sys`, `mgmt`) that one sign-off each opens | `src/bell_system/data/finds.py`, `src/bell_system/data/homes.py`, `src/bell_system/screens/shell.py` | The simulation's own. The people are the invented roster and R. Alvarez, who has no login. The su log's record format follows the Seventh Edition's; the record journal's format and every date and count in these files are invented, and no source consulted says a sign-off gated a file. Which group a sign-off gives is invented too |
| The Practices binder in `/usr/bsp`: six sheets in divisions 620 and 660, built from `FAULTS`, `REPORT_SYMPTOMS` and the `loop_testing` constants | `src/bell_system/data/practices.py` | The simulation's own. Divisions 620 and 660 are real Bell System divisions (`BSP_CATEGORIES`), but no Practice from either was reachable, so the section and sheet numbers are not Bell System numbers, and each sheet says so in its header. Each sheet also lists which of its figures come from a period document (the 1300 and 1500 ohm limits, coin station current, cable capacitance per mile, close codes 5 and 8) and which are the simulation's own (the resistance ranges, repair minutes, complaint wording, and what separates a clean reading) |
| A special services trouble can be at the office, the loop or the premises, or on an interoffice facility; `sarts repair` sends a force to one of three places | `src/bell_system/special_services.py` `PLACES`, `sarts(1)` | Engineering and Operations in the Bell System, 2nd ed. 1984, p. 581 [598]: trouble location is "determining whether the trouble is in central office, loop, or premises equipment", and note 4: "In the case of special services, troubles may be traced to interoffice facilities." **That is all the book says.** The three places this desk uses (this office, the interoffice facility, the customer's end), the odds of each (3, 4 and 3 in ten), the minutes a force takes (10, 20, 15), the loop-back costs (3 by relay, 15 by a visit to the jack), the 12 minutes a wrong force costs to send again, and the 60-minute window past which a circuit held in trouble is a missed commitment are the simulation's own. Its outage figures are simulated shift minutes, not any real office's |
| The office desk's alarm panel: alarms standing at a lamp that is minor, major or critical; `connect work` clears one at its cause | `src/bell_system/screens/remote.py`, `connect(1)` | The three lamp classes are conventional alarm practice, and the alarm types are the five the office was already dealt from. **The 40-minute rise, the point in it each alarm ripens at, the 3, 5 and 8 minutes of work (2 more for another building), the rule that an alarm held a whole span at the top lamp is a missed commitment, the deal of two or more alarms a tour (30 in 100 each) and which alarm is a symptom of which (trunk degraded of carrier loss, carrier loss of radio fade, memory parity of power supply) are the simulation's own.** No source consulted gives any of them. Its figures are simulated shift minutes, not any real office's |

### What was looked for and not found

Recorded so that nobody repeats the search, and so that nothing was
invented to fill the gap:

- **The daily weather over northern New Jersey on 14 November 1983.** Every
  archive reachable from here was blocked. `src/bell_system/weather.py`
  therefore generates the shift's conditions and states plainly that no
  claim is made about what really happened that day.
- **The customer-facing report categories a repair service attendant chose
  from.** Most likely a division 660 practice, not reachable. The electrical
  faults are documented; `REPORT_SYMPTOMS` is the simulation's own
  plain-language wrapping and is marked as such.
- **COSMOS transaction syntax.** Not reproduced from any source; the
  `cosmos` subcommands are the simulation's own and the screen says so.
- **A wire centre's actual field force size.** No source consulted fixes a
  number, so `src/bell_system/field.py` uses five as a working figure and
  says why.
- **Documented differences in equipment mix between operating companies.**
  The roadmap asked for per-company character drawn from these. Neither the
  period documents nor anything else reachable establishes how one
  operating company's crossbar-to-ESS mix differed from another's.
  `data/companies.py` says so, and uses the divestiture assignment instead
  — which is documented, and is what people in those buildings actually
  knew about their own company in November 1983.

## What does not ship

Three categories are not in the repository. All are recoverable; none is needed
to run or test the simulation.

### The period document text

The sixty-five `*_djvu.txt` files in the inventory above were tracked until
release 5.0.0 and were then removed from the repository. They were never used
at runtime and no test reads them. They were reference reading for the
historical accuracy work.

### The NANPA geographic dump

`full_dataset_csv.csv` was a 46 MB modern extract of North American numbering
plan data. The simulation now ships a distilled 42 KB dataset built from it,
at `src/bell_system/data/nanpa.csv.gz`, carrying only the six columns the
code reads and only area codes that could have existed in the period.

To rebuild it you need the dump. Any current NANPA-derived extract with the
columns `npa, nxx, city, state, country, latitude, longitude` will do; pass
its path on the command line:

```
python tools/build_nanpa.py --source /path/to/full_dataset_csv.csv
```

The build script documents the period filter and the eighteen area codes
excluded by name for postdating the simulation.

### Scanned PDFs

| Document | Size |
| --- | ---: |
| `325-048_i9_Nov82_SSM_Station_Service_Manual_vI_tci_ocr_r.pdf` | 25.2 MB |
| `42397-5ess.pdf` | 0.3 MB |
| `Bell-System-Technical-Journal-1976-3.pdf` | 1.9 MB |
| `BellLabs_v7vol2a.pdf` | 1.3 MB |
| `Documents_for_the_PWB_UNIX_Time-Sharing_System_Edition_1.0_197710.pdf` | 46.3 MB |
| `PWB_UNIX_Edition_1_Section_1_May77.pdf` | 11.5 MB |
| `UNIX_ProgrammersManual_Nov71.pdf` | 6.8 MB |
| `UNIX_Programmers_Manual_Seventh_Edition_January_1979_Volume_1_SRI_Reprint_June_1980.pdf` | 30.0 MB |
| `bell_system_80_series.pdf` | 2.4 MB |

9 files, 126 MB total.

These are page scans. No line of code cites any of them, because they are
images rather than searchable text - every verifiable claim in this project
rests on the text of the period documents listed above.

They were removed from the git history as well as the working tree, which
took a clone from 126.33 MiB to 6.21 MiB. Every commit is otherwise
unchanged: the rewrite was verified file by file, and all 119 files present
at the previous `main` and all 149 at the branch tip are byte-identical
before and after. They were reference reading during the
historical accuracy work and are not needed to build or run anything.

Scans of this material are held by the Internet Archive and by bitsavers,
which is where copies of these particular files came from. Exact per-file
provenance was not recorded when they were first added to the repository, so
the titles above are the reliable identifier rather than any URL this file
could offer.

## The discipline

Four rules held through the audit and the work that followed:

1. **Provenance or admission.** A value is verified against a period
   document, externally sourced, or explicitly marked as the simulation's
   own. Where a source could not be reached, the gap is recorded in the
   source code rather than filled with plausible invention.
2. **Conflicts are recorded, not resolved silently.** Where two sources
   disagree - CLLI code length, what MLT stands for - both readings and the
   choice are written down.
3. **Derived is not quoted.** Figures computed from a document say so. The
   loop resistance per mile is derived from "1300 ohms, typically about three
   miles"; it is not a figure any document states.
4. **Externally sourced is labelled.** The eighteen post-period area codes in
   `tools/build_nanpa.py` come from the published history of the numbering
   plan, not from the period documents, and each carries its year and parent
   code so a wrong one can be found.
