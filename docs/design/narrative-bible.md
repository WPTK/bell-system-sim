# Narrative bible

What is true in the world of the game, who speaks and how, and what the
answers are to the questions the machine asks and never answers. Written
2 November 2026 against `main` at 054be11. Companion to `plan.md`, whose
pillar 4 says the machine is the story.

Adapted from the narrative rules of Donchitos/Claude-Code-Game-Studios (MIT):
canon levels, voice profiles, written world rules and true answers for every
mystery. Its rule on localisation is not adopted: the English here is
period English and is the product.

This file records. It fixes nothing. Every contradiction found while writing
it is listed in section 8, and no code or text was changed.

## 1. How to use it

**Canon levels.** Every item in sections 3 to 7 carries one.

| Level | Meaning | Who may change it |
| --- | --- | --- |
| **Established** | Already shipped on `main`. A player can read it today. The source file is cited. | Only a PR that edits the shipped text and this entry together, with the reason. |
| **Provisional** | Designed here or in `plan.md`; not shipped. It is the intended truth. | Any PR in the named phase, which edits this entry in the same PR. |
| **Under Review** | A conflict, a gap or a claim with no source. Nothing builds on it until it is settled. | Bill, or the review that finds it. |

**Period facts.** Each is marked **[sourced]** with where it rests (a
`SOURCES.md` row or a cited document) or **[own]** for the simulation's own
invention, which is the `SOURCES.md` rule. A fact that is neither is
**Under Review** until it has a row.

**Line limit.** From the narrative rules: no line of dialogue past 120
characters. The shipped text is hand-wrapped near 72, so a message is a
list of short lines; keep to that.

**Check before you write.** A PR that adds or changes narrative text checks
it against sections 4 (voices), 3 (world rules) and 5 (truths), and adds
any new person or fact here (`plan.md` section 10).

## 2. The setting in four sentences

**Established.** It is Monday 14 November 1983, 48 days before the Bell
System ends on 1 January 1984 (`clock.py`, E&O). The player is a new
craftsperson at a wire centre on a Seventh Edition UNIX machine called
`mhuxco`, working a repair test desk across 13 tours four days apart, the last
on 31 December. Nobody in the building thinks the network will stop; they
think the company will, and each of them has a different private answer to
what that means. The player has no name: the text says "you", and the login is
the position.

## 3. World rules

What can and cannot happen at the desk. A new feature that breaks one of
these changes this table first.

| # | Rule | Canon | Where it lives |
| ---: | --- | --- | --- |
| W1 | The plant tells the truth. A reading means the same thing every time it is taken; people and records can be wrong, measurements cannot. | Established | `reports.py`, `data/trouble.py`; `dba` notes: "The records are not the plant." |
| W2 | Every trouble has a cause in the plant, drawn from a fixed set of fault types. There is no fault without a physical reason. | Established | `data/trouble.py`; `data/regulars.py` ("the reason is electrical rather than narrative") |
| W3 | A report closes with code 5 (trouble found) or 8 (no trouble found), and is judged against the line's real fault. | Established | `data/trouble.py` `DISPOSITIONS`; [own], with the E&O 16.4 simplification recorded in `SOURCES.md` |
| W4 | A tour is 480 minutes. Time passes on what the player does, not on the wall clock: commands, tests, dispatches and callbacks each cost shift minutes. | Established | `constants.py` `SHIFT_LENGTH_MINUTES`; `reports.py` `COST_*` |
| W5 | Four channels reach the player and nothing else does: write(1), mail(1), the order wire, the maintenance teletype. Nobody speaks aloud and nobody arrives at the desk. | Established | `npc.py` `CHANNEL_*` |
| W6 | Qualification, not rank, decides what the player may touch. A command outside the held sign-offs is refused. The ladder is [own]. | Established | `progression.py` `QUALIFICATIONS`; `SOURCES.md` |
| W7 | The building is closed. There is no outside network except uucp and the netnews spool, dated no later than the tour. | Established as to uucp; the dating is Provisional (C19) | `filesystem.py`, `plan.md` C19 |
| W8 | No one dies and no one is hurt on screen. Harm is a line out of service, a missed commitment, a person who rang twice. The worst case is a doctor's answering line (`duchesne`). | Provisional | pillar 2; `data/regulars.py` |
| W9 | The date never moves past 31 December 1983. There is no tour 14 and no "after". Everything about 1 January is told as a forecast by someone in the room. | Established | `clock.py` `set_tour` |
| W10 | The audit is held at tour 13 and reads the dispositions on record; a failed audit changes the words, not the length of the career. | Provisional (A2, C23; D2) | `plan.md` section 8 |
| W11 | Nothing on the machine works as instructions against a real network: no tones, no dialable codes, no procedure that would do anything outside the simulation. | Provisional (A11, D6); the shipped test lines already disclaim dialable codes | `data/testlines.py`; `SOURCES.md` |
| W12 | Weather in the game is the simulation's own and claims nothing about 14 November 1983. | Established | `weather.py`; `SOURCES.md` "looked for and not found" |
| W13 | The people, customers, addresses and operating-company lines are invented and say so. Real organisations appear only as the E&O names them. | Established | `data/regulars.py` docstring; `npc.py` docstring |
| W14 | A player may read anything their qualifications and group allow, and the machine never hides lore behind a puzzle that needs outside knowledge. | Provisional (pillar 4 test) | `plan.md` section 1 |
| W15 | The groups are a ladder, one rung to a sign-off: `craft`, `uucp`, `adm`, `sys`, `mgmt`. A file shut to the player is shut by its mode and group bits, as on a real machine, and opens when the group is given. The ladder is [own]; `mgmt` is a group the player is put in and not a rank: it opens Halloran's file and no command. A new shut file goes on the ladder in `data/finds.py`, and a sign-off that opens nothing is a defect. | Established | `data/finds.py` `GROUP_FOR_SIGN_OFF`; `screens/shell.py` `_may_read` |
| W16 | A regular's card says what has happened to the line and the people on it, never what the next report off it will be. Fault, force and close code stay in `mlt` and the field finding. | Established (C16) | `data/regulars.py` arcs; `tests/test_regulars_arc.py` |

## 4. Voices

One profile per recurring person. **Pronouns** are given only where the
shipped text uses them; otherwise use the name. **Rule:** a line of dialogue
for that person must pass the Never column.

Sample lines are quoted from the code and are the standard. Wrapping is
normalised to one line.

**Who is on (Provisional, phase 6c, A12).** The building is staffed round the clock, with three day jobs and an evening man, the simulation's own: Nakamura and Bright on the day watch (08:00-16:00), Haverty and Finch on day and evening. Everyone else, and both machines, are on all three. Reyes (03:47) and Halloran (06:15) must stay on nights for T2. Off watch a person is absent from `who`, `write` and the mail and order-wire traffic; `man write` says so. Which watch a tour is worked on is the tour's own (`data/tours.py` `Tour.watch`, the simulation's own: day on tours 1, 2, 5, 8, 10 and 13, evening on 3, 7, 9 and 11, night on 4, 6 and 12), because an eight-hour tour on the clock's own hour would never leave the day. The clock therefore opens each tour on its watch's hour (day 08:00, evening 16:00, night 00:00; `SimClock.set_tour`, `tours.start_hour`), the shift briefing names the watch and starts at that hour, message stamps and the board's event times follow it, and a line of chatter either depends on the watch or names no time of day (no "afternoon batch", no "this morning", no clock time that a night tour has not reached); only with `date.source` set to `real` does the host's hour decide. A crew the bureau dispatches is called out, not asked in: dispatch ignores the watch, and a crew sent in the evening still calls in. The one absence that does change dispatch is **Okafor on tours 12 and 13** (T3): she is not in `who`, `write` is refused, no message is in her voice, and the crew pool cannot send her, so Sandoval takes the sheath, as `sandoval.3` says. Hints are asked for, so they can come from anyone, on or off watch. `npc.py` `Craft.watches`, `AWAY`.

**Rapport and the favour (Provisional, phase 6b, A6; the simulation's own invention).** Each report closed in a tour moves the crew that worked it, or the bureau, one step: up for a right code, down for a wrong one, at most once each way per person per tour. At step 3 that person does one favour, once: they ring the customer and the report with the nearest commitment gets an hour more, said in their own voice (`npc.py` `FAVOURS`). It is held until that report is within the hour of its commitment, since that is when an hour matters. Only people who work the board have one: Reyes, Okafor, Sandoval, Finch, Bright, Nakamura. Nobody offers one unasked before then and nobody is ever told their rapport. It is kept in the career file (`rapport`, and the `rapport+:`, `settled:`, `rang:`, `chased:`, `about:`, `favour:`, `favoured:` and `said:` entries of `beats_seen`) so that a resume says nothing twice. The `chased:` entry is written when the notice is said, not at the next beat, so a quit straight after does not lose it. A line of ambient chatter is not offered again within three tours of being said (`npc.py` `CHATTER_REST_TOURS`), and the lines said are kept in the same ledger.

**Ambient chatter over a career (Provisional, #93).** A line is not offered again within `CHATTER_REST_TOURS` (3) tours of being said, so a voice that speaks once a tour for the thirteen of them needs four lines it can say on every tour it is heard. Every voice on every desk has that (`tests/test_chatter_career.py`). When a busy desk says its pool dry the building is quiet until a line has rested; a line is never said early to fill the silence. New lines keep to the speaker's profile below, name no fault, force or close code (only `mlt` and a field finding do), and say no time of day.

### Halloran, E.: wire chief  (`ehalloran`, CENTRAL_OFF, tty01)

**Canon:** Established (`npc.py` `CRAFT`, `_SIGN_OFF_REMARKS`, `last_word`; `data/hints.py`). He/him in the code.

- **Does:** signs every qualification and says one thing about each. Reads the service index every morning and does not praise it. Plain declaratives, short sentences, instructions before reasons. Deflects feeling into the job.
- **Never:** effusive or funny on purpose. Never explains the lore; he points at where the practice is.
- **Sample:** "Reminder to all craft: a report closed as no trouble found is still a report. The index does not care how quickly the board cleared." (`npc.py` `_CHATTER`)
- **Arc:** says less as the end nears, then one thing more at the last tour (`last_word`: "Go home."). Said less, in the ambient traffic, means a chance of 15 per cent a tour from tour 9, up to 70 per cent, that his chatter is held back on that call (`npc.py` `halloran_quiet`).

### Reyes, M.: repair service attendant  (`mreyes`, RSB_NEWARK, tty07)

**Canon:** Established. She/her.

- **Does:** speaks for the customer. Every message has a report number, a number to ring and a time. Asks the question she has to answer, never gives an order.
- **Never:** blames a person; guesses a cause out loud (`custserv` notes: "The one thing you are not allowed to do is guess out loud.").
- **Sample:** "TR-05518 on 201-200-4380 was due 20:25 and has gone. What do I tell them?" (`npc.py` `overdue_notice`; one form, two lines: the report, then the customer's words by class if the line is out, "The line is working. They would like a time." if not)
- **Open:** the 03:47 su (section 5, T2).
- **Consequences (Provisional, phase 6b, C17):** the customer's words come through her, one line by class of service, in three places: a report past its commitment with the line out of service, the second call on a repeat, and (a quarter of clean closes) a call to say it held. `data/consequences.py`. Each message keeps to her profile: report, number, time, a question. The notice when a commitment passes is said once and the board does not ask the same again; the second call and the call-back each end on her question.
- **Arc (Provisional, phase 6b, A6):** `reyes.1` (tours 5-8) and `reyes.2` (tours 9-11) are about a closed report: she cannot reopen it and asks if there is another way; a customer asks who will have the line's trouble card in February. The two never speak of the same report. They wait for a report to speak of. Neither explains T2.

### Johnson, R.: switching equipment technician  (`rjohnson`, CENTRAL_OFF, tty02)

**Canon:** Established. Twenty-two years on step and crossbar.

- **Does:** tells you what he did, not what the manual says. Understates. Dry about machines that nearly work.
- **Never:** quotes a practice number; raises a ticket on Marker 2.
- **Sample:** "Marker 2 took eleven seconds on a third trial earlier. Peg count is up and nothing is out of limits, which is the whole problem with a marker." (`npc.py`)

### Okafor, L.: cable splicer  (`lokafor`, FIELD_SUP, tty04)

**Canon:** Established. She/her. "The splicer" in this bible's shorthand.

- **Does:** reports from inside the plant: manholes, water, time. Short, wet and impatient, calling in on a butt-in set. Sets a boundary in one line ("it is mine"). Insists on her moo score.
- **Never:** speaks in dB or percentages; lingers on the phone.
- **Sample:** "It is wet in here. Whatever you have out of that cable, it is mine." (`npc.py` `_CHATTER`)

### Sandoval, J.: cable splicer  (`jsandoval`, FIELD_SUP, tty11)

**Canon:** Established as a name, a role and one netnews post; the voice is Provisional beyond that.

- **Does:** says little, and says it plainly. When Sandoval writes, it is about the job, not the plant: what the company has learned it can do without.
- **Never:** complains about the weather or a crew; jokes.
- **Sample:** "It is because there is less and less of this job that needs a person standing in front of it, and the company now knows that, and so do we." (`filesystem.py` NEWS_MISC_88)
- **Open:** section 5, T3.
- **Arc (Provisional, phase 6b, A6):** three orderwire notes to the test desk, never more than three lines. `sandoval.1` (tours 4-7): small-count aerial spliced and tested, send more of that size. `sandoval.2` (tours 8-10): the memo says his employment continues; he looked for which company it means. `sandoval.3` (tours 12-13): Okafor is not on this shift, he has the Franklin sheath, will be slow, will do it. No beat names the strike or the move from `mhuxt`.

### Alvarez, R.: the predecessor, sysop position, evening tour  (no login, no tty)

**Canon:** Established as two files (`data/homes.py` sysop `notes`; `filesystem.py` `TESTLOG_C`), signed "evening tour" since phase 7b (I10). Phase 7b adds, all the simulation's own and all Provisional: the position's test log `/usr/adm/testlog` (what `testlog.c` writes: a line a day of reports closed, how many no trouble found, and the board left); a Franklin Street scratch file `/tmp/.f`, which arrives on tour 2 and says only what the crews found; and the thread of the handover (`data/finds.py`, `data/homes.py` `dead.letter`): a sent handover, a cut-off unsent letter to Halloran, one layer to a sign-off (W16). Nothing else about Alvarez is shipped, and nothing about Alvarez names a pronoun; use the name or they.

- **Does:** hands down practical advice in the first person, confesses a mistake to be useful, and signs off without a flourish. Slightly tired. Writes for whoever "has this position next".
- **Never:** addresses the player by name or by sign-off; is angry at anyone.
- **Sample:** "I sent four separate crews to Franklin Street last month. Do not be me." (`data/homes.py`)
- **Arc (Provisional, phase 6b, A6):** has no voice of their own; Halloran speaks of them. `alvarez.1` (tours 2-4, mail): the position had somebody before you, `testlog.c` is theirs. `alvarez.2` (tours 10-12, write): Alvarez rang to ask how the position was going; Halloran said it was being worked. No pronouns in either.

### Petrak, D.: SCC maintenance administrator  (`dpetrak`, SCC_BEDMINSTER, tty03)

**Canon:** Established.

- **Does:** speaks in the order-wire form: "SCC to office." then one item. Polite, never asks twice, watches eleven offices from one console. Puts the cost in the first clause.
- **Never:** raises the voice; asks for a favour.
- **Sample:** "SCC to office. Routine. No action, just logging that we have you on the wire." (`npc.py`)

### Nakamura, T.: transmission engineer  (`tnakamura`, TRANS_CTR, tty05)

**Canon:** Established.

- **Does:** states the unit and the frequency, and corrects you if you did not. Treats a number as a claim.
- **Never:** says "about". Never reassures.
- **Sample:** "Loss objectives are stated at 1004 Hz. If you are reading at any other frequency you are not measuring what the objective is written against." (`npc.py`)

### Vasquez, G.: testboard technician  (`gvasquez`, TEST_CENTER, tty09)

**Canon:** Established.

- **Does:** lives on the board; gives the reading before you ask. Offers to run it, never to explain it.
- **Never:** tells you what to do with the reading.
- **Sample:** "Board is quiet. If you want a pair measured before you commit to it, send it over and I will run it." (`npc.py`)

### Finch, W.: station installer  (`wfinch`, FIELD_SUP, tty06)

**Canon:** Established.

- **Does:** speaks for the customer's side of the protector; knows how long they waited before they rang.
- **Never:** blames the customer.
- **Sample:** "Three weeks and one report. They always wait." (`npc.py` `_POSITION_CHATTER`)

### Bright, A.: lineman  (`abright`, FIELD_SUP, tty12)

**Canon:** Established.

- **Does:** reports from a ladder or a pole; looks ahead to who will own the problem in January.
- **Never:** sounds hurried.
- **Sample:** "That pole at Grand has been leaning since the storm and it is going to be somebody's problem in January." (`npc.py`)

### Haverty, J.: chief operator  (`jhaverty`, TSPS_NEWARK, tty10)

**Canon:** Established. She/her.

- **Does:** brings you a call somebody is still holding; counts in people, not in calls.
- **Never:** uses a technical word the caller could not repeat.
- **Sample:** "Six is not six people being wrong." (`npc.py`)

### ADM and CAROT: the machine's own voices  (`adm`, `carot`)

**Canon:** Established. Not people.

- **Does:** ADM writes in log-file register; CAROT prints in capitals, with no verbs of feeling.
- **Never:** speaks to the player or uses "you". Every line must be one that a teletype would print.
- **Samples:** "/usr/spool is at 84 percent. uucp has 47 files queued for pwba and pwba has not answered since 06:44." (ADM); "CAROT ROUTINE TEST COMPLETE" (CAROT)

### VP-OPS: the memo's author

**Canon:** Established (`DIVESTITURE_MEMO`).

- **Does:** official register, numbered duties, then one paragraph in a human voice.
- **Never:** appears anywhere but in that memo.
- **Sample:** "Work the board. That is the job on 31 December and it is the job on 2 January."
- **Open:** who wrote the last paragraph; section 5, T4.

### The regulars: the customers  (`data/regulars.py`)

**Canon:** Established as cards, with an arc each (phase 7a, C16): Kowalczyk (214 Sussex St, 1FB, wet sheath), Ferrante (1109 Ocean Ave, coin, off-hook), Whitcomb (87 Bergen Ave, 1FR, aerial drop), Duchesne (466 Central Ave, 1MR, a doctor's answering line). They have no lines of speech yet; the card note is the voice, and from tour 3 it changes on named tours.

| Line | Beats (tour) | Ends |
| --- | --- | --- |
| Kowalczyk | 4 estimate approved, no date; 7 two calls asking when, "before the holidays"; 11 new cable in, old sheath dead-ended | Resolved, tour 11 |
| Ferrante | 3 collector finds the box emptied, new manager; 5 landlord written to, no answer; 7 rooming house closed by the city, coin telephone pulled | Abandoned, tour 7 |
| Whitcomb | 3 clearance asked of the bus company; 6 new drop on the order list; 9 new drop on the far pole, a thank-you call | Resolved, tour 9 |
| Duchesne | 4 the tag has held, the exchange rings to say so; 8 second line asked for, rotary; 12 rotary in, two lines, different blocks | Resolved, tour 12 |

- **Does:** exists in the note of the last craftsperson who went out: tired, specific, a verb in the past tense. A beat is about the line and the people around it: the job on the order list, the call that came in, who was written to. Once a line is resolved or abandoned it stops reporting, and its last card stays readable in `custdb` for a craftsperson who has closed a report on it. Beyond the card they will speak through Reyes and the customer's second call (C17).
- **Never:** speaks in the abstract; names the system that will fix it ("they very much do not want to hear the word 'facility'", `custserv` notes); says what the next report off the line will be (W16).
- **Fixed:** each line's number, cable and pair, frame appearance and line equipment are fixed by the office and the line's name, so they are the same on every tour. Addresses carry no city (I12).
- **Sample:** "Aerial drop crosses the bus route. Third open on this pair this year and every one of them within a week of weather." (Whitcomb's card, until tour 3)

### Others without a voice yet

Customers on ordinary reports are drawn from a name pool and have no voice. The authors of the netnews spool (Kellner, Marchetti, Corrigan, Teixeira, Weatherly, Strand, Gillam, Okonkwo, Greenhalgh) are background; they speak only in their posts. A new recurring person needs an entry here before they appear.

## 5. The truths

For each open mystery: what the game shows now, then the true answer. A
truth is **Provisional** until its phase merges and this entry is edited to
say Established. The player may never learn all of it. The test for any new
text is that it contradicts none of these.

### T1. Marker 2

**Shown now (Established):** a slow third trial on the number 5 crossbar's marker 2 in aisle 4, "since 81"; Johnson says do not raise a ticket because it will be closed no trouble found; two homes name the cause differently (section 8, I4). `filesystem.py` `marker.notes`, `data/homes.py` (sysop, switch), `npc.py`.

**True answer (Provisional):** the sequence relay in marker 2 is wearing out. It lengthens the third trial slightly each month, which is why the timing chain is "within limits" and the peg count is up. Johnson is right and has been right for two years. The relay fails outright on tour 9 or tour 10, takes the marker out, and produces a run of reports on lines with no cable in common. A player who has read `marker.notes` and the peg count sees it coming; one who has not sees three or four unrelated troubles and learns the pattern from Johnson.
**Pays off:** phase 8, row A7 (8b). **Check first:** A21. The sequence relay detail is [own] until `SD_26030-01` is read against it.
**Period facts:** a number 5 crossbar has markers and registers [sourced, E&O and `SD_26030-01`]; dial tone speed and peg count as the measures are [sourced, E&O]. The relay failure is [own].

### T2. The RSA's failed su at 03:47

**Shown now (Established):** `SU 11/14 03:47 - tty07 mreyes-root` in `/usr/adm/sulog`, readable only from the third sign-off. Halloran's `su` at 06:15 succeeds. The teletype line now agrees with the log: 03:47, tty07 (I1, resolved in 7b). `/usr/adm/lmoslog`, shut until the fourth sign-off, shows four refused attempts from 03:41 to 03:52 and Halloran's success at 06:15, and `~ehalloran/reopened`, shut until the fifth, is his own list.

**True answer (Provisional):** Reyes was not breaking in. Alvarez closed a run of reports no trouble found in the last week of that desk to clear the board (a trend in `testlog`: no trouble found climbing while the board falls, never a count), and the customers rang back after Alvarez left; on the night bureau Reyes found she could not reopen a closed report. At 03:47 Reyes tried the only way she knew, and the machine refused her. Halloran su'd at 06:15, reopened the reports under his own name, and those are the opening reports (`reports.py` `OPENING_BACKLOG`, three to five). He did it because the memo says open reports pass to the operating company "with your name on them", and he would rather it was his. He did not tell her.
**Pays off:** phase 7, row A5 (7b, shipped): `/usr/adm/lmoslog`, readable after the fourth sign-off, explains it, and `~ehalloran/reopened`, after the fifth, says only that he reopened the reports that rang back, and the reader works out why; phase 10 (C23) lets Reyes say so.
**Period facts:** su logs in `/usr/adm/sulog` [sourced, the Seventh Edition manual, scanned, not in the repo text; needs a `SOURCES.md` row]. Everything else is [own].

### T3. Sandoval

**Shown now (Established):** the second splicer, newer than Okafor, slower on a big sheath, who "says less" and whom the wire chief "has noticed and has not decided about" (`npc.py`, `field.py`); the author of a netnews post on the August strike from `mhuxt`; Okafor tells the player to "give it to Sandoval".

**True answer (Provisional):** Sandoval came over from the neighbouring wire centre (`mhuxt`) in the autumn when its splicing force was cut. Sandoval was out in the August strike and thinks the memo's "your employment continues" is a promise from a company that will not exist. Halloran has not decided about Sandoval because Halloran does not know either. Sandoval is good on small-count aerial and drop work and slow on a big sheath because that is what he came from; on tour 12 or 13, when Okafor is out, Sandoval takes the sheath job nobody else will, and the player can learn why by ending up in the same room.
**Pays off:** phase 6b, row A6 (rapport, `sandoval.1` to `.3` in `npc.py` `ARC_BEATS`; the Franklin sheath beat is `sandoval.3`); the last line in phase 10 (C23).
**Period facts:** the 1983 strike and its terms [sourced, `SOURCES.md` `net.misc/88`]; Sandoval's history is [own].

### T4. The January memo

**Shown now (Established):** `/usr/doc/divestiture`, dated 1 November 1983: duties numbered 1 to 4, then "A NOTE" in a different register. Also the MOTD and the login banner.

**True answer (Provisional):** every number in it is true. Employment does continue and qualifications do transfer. The audit is real: the operating company's auditors check dispositions against what a test would have read, which is why the game's wrong-close debrief quotes the player's own readings. Halloran wrote "A NOTE" himself and sent it up to the vice president, who signed it. That is why it sounds like a person and why Halloran never refers to it.
**Pays off:** phase 4, row A2 (the audit); phase 10, C23 (the epilogue may say who wrote it).
**Period facts:** the date of divestiture and the quoted E&O sentence [sourced, `clock.py`, E&O]; "toll network above class 4 remains with AT&T" [own wording of the divestiture split, no row yet: Under Review]; the 1 November date, the memo and the VP [own].

### T5. The locked file

**Shown now (Established):** `/usr/adm/sulog`, mode `-rw-r-----`, owner `adm`, group `adm`. Halloran puts the player in the `adm` group at the third sign-off and tells them it "has your name in it" (`screens/shell.py` `sync_groups`; `npc.py`). The log now does: one `SU mm/dd HH:MM + tty01 ehalloran-<login>` line, stamped at the sign-off (I2, I3 resolved in 7b).

**True answer (Provisional):** Halloran locked nothing on purpose. The mode is the machine's default for an accounting file. What he does on purpose is the group: adding someone to `adm` is his way of saying he has decided they are staying. The file holds Reyes's failed attempt, his own successful one, and one line for the player, written at the moment of the third sign-off, which is the only way his sentence is literally true.
**Pays off:** phase 7, row A5 (7b).

### T6. The moo rivalry

**Shown now (Established):** `moo.scores`: Vasquez 4, Johnson 5, Reyes 7, Okafor 11 "(says the terminal was slow)"; `sysop -`. Beating 11 draws a message from Okafor on write(1) (`screens/games.py`, `npc.py`); a netnews post from her claims witnesses.

**True answer (Provisional):** the terminal was not dropping characters; it was an eleven. She says otherwise because everyone else's number is a joke and hers is the one she cared about. The "witnesses" were Sandoval and Bright, who were in the room and have never mentioned it. Halloran is not on the board because he plays at six in the morning on the console and has a better score than anyone, which he keeps in a file in his home directory.
**Pays off:** unscheduled, row A22 (P3): beating Halloran changes his next two order-wire lines. If A22 ships the file is a find (A4).

## 6. Periods and calendar

Dates stand as in `plan.md` section 6; this file adds nothing to them. A
tour's text must not state a date that file marks external without its
`SOURCES.md` row.

## 7. Canon catalogue

Everything shipped that is a fact about the world, one line each, so a new
PR can see what it must not contradict. All **Established**.

| Item | Where | Period fact |
| --- | --- | --- |
| 14 Nov 1983 is the start; 31 Dec is the last tour | `clock.py` | [sourced] E&O; stride [own] |
| The host is `mhuxco`; the office city and CLLI come from loaded data | `terminal.py`, `screens/bureau.py` | [own] |
| MOTD, "UNIX Version 7", copyright 1979 | `filesystem.py` | [own wording]; Version 7 as the machine: no `SOURCES.md` row (Under Review) |
| Operations Bulletin 83-114, 14 Nov 1983 | `filesystem.py` | [own] |
| Divestiture memo, 1 Nov 1983, VP-OPS | `filesystem.py` | [own]; see T4 |
| Group `craft` (rjohnson, lokafor, gvasquez, mreyes, wfinch, jsandoval, abright), group `mgmt` (ehalloran, dpetrak, tnakamura, jhaverty) | `filesystem.py` | [own] |
| The 13-person roster in section 4 | `npc.py` | [own]; "titles are real; the people are not" (`field.py`) |
| The four regulars and their histories (March, January, February, August 1983), and their arcs to tours 7, 9, 11 and 12 | `data/regulars.py` | [own] |
| uucp traffic: `pwba` not answering since 06:44; `bsp.660` requested from `pwba` | `filesystem.py` `UUCPLOG` | [own]; the practice number is a reference to the Practices binder (A3) |
| The August 1983 strike, 7 to 28 August, 5.5 and 1.5 per cent | `net.misc/88` | [sourced] `SOURCES.md` |
| 1956 and 1982 decrees, why System V arrived | `net.unix-wizards/121`, `why.unix` | [sourced] `SOURCES.md` |
| RFC 850 netnews headers | `filesystem.py` | [sourced] `SOURCES.md` |
| Local cable 0.083 microfarad a mile; 1004 Hz objectives; CAROT, ROTL, PCI | `npc.py`, `data/testlines.py` | [sourced] `SOURCES.md` (Transmission Engineering, BSTJ) |
| Mother's Day the busiest calling day, "for forty years" | `data/homes.py` noc notes | No `SOURCES.md` row: Under Review |
| "Half a second" by satellite | `npc.py` radio chatter | Physics, not a dated fact; the figure is a round trip. Under Review for the wording |
| Average TSPS call "under thirty seconds", "several hundred" a tour | `data/homes.py` tsps notes | [own]; no row: Under Review |
| Fade margin, diversity switch, the Chester hop, TH-3 | `npc.py`, `data/homes.py` | Equipment years [sourced] `SOURCES.md` (TH-3); the hop is [own] |
| The finds: the numbered files in `data/finds.py` `FRAGMENTS` that `finds` lists once read. New in A4, all the simulation's own and Provisional: `/usr/adm/testlog` (Alvarez), `/tmp/.f` (tour 2), `/usr/users/rjohnson/.trial` (tour 5, Johnson's third-trial times, which rise by a second or so a season), `/usr/adm/.retain` (tour 8, the chief's retention list), `/usr/lib/.xfer` (tour 10, accounts for transfer) | `data/finds.py` | [own]; log formats follow the Seventh Edition where it had them. None says what is true about T1 or T2 |
| The thread of the last holder, one file to a sign-off: `~sysop/dead.letter`, the sent handover (`/usr/spool/mail/ehalloran`), `/usr/adm/sulog`, `/usr/adm/lmoslog`, `~ehalloran/reopened` | `data/finds.py`, `data/homes.py` | [own]; the su log format follows the Seventh Edition. Shut by group, W15 |
| The Okafor eleven | `screens/games.py`, `npc.py`, `filesystem.py` | [own] |

## 8. Inconsistencies found

Listed and not fixed. **A** needs a decision about the truth; **B** is a
mismatch of fact with an obvious reading; **C** is a gap or an unsourced
claim. Where the plan already tracks it, the row is named.

| # | Sev | What | Where | Note |
| ---: | :-: | --- | --- | --- |
| I1 | A | The su log shows a failed `mreyes-root` at 03:47 on tty07; the teletype line showed it at 07:52 on tty03, which is Petrak's tty | `filesystem.py` `SULOG`; `npc.py` sysop chatter | **Resolved in 7b:** the teletype line is now 03:47, tty07. One event. (One-line change in `npc.py`.) |
| I2 | A | Halloran says the sulog "has your name in it" at the third sign-off; no line in it carries the player's login | `npc.py` `_SIGN_OFF_REMARKS`; `filesystem.py` `SULOG` | **Resolved in 7b** by `sync_groups`: one line for the player at the sign-off. |
| I3 | B | The sulog's mode `-rw-------` does not show the group read that the `adm` group is given | `screens/shell.py` `_may_read`; `filesystem.py` | **Resolved in 7b:** the mode is `-rw-r-----` and `_may_read` reads the group bit. |
| I4 | A | The cause of Marker 2 is "the sequence relay" in Johnson's notes and "the timing chain" in the switch notes | `filesystem.py` `marker.notes`; `data/homes.py` switch | **Resolved in 7b:** the switch notes now say the trouble is in the sequence relay and the timing chain it feeds is within limits. T1 stands. |
| I5 | B | Position notes are signed by people who would not have written them: the records desk by Okafor, special services by Johnson, radio by Vasquez, switching by Nakamura | `data/homes.py` | Already tracked as plan row C30. |
| I6 | B | The field notes speak of "Vasquez's crew"; there is no such crew, and Vasquez is a testboard technician | `data/homes.py` field notes; `field.py` `CREWS` | |
| I7 | B | Nakamura is a transmission engineer in the roster and a switching equipment technician in the crew list; Johnson holds that title in the roster. The central-office field call is mapped to Johnson but matches Nakamura by name | `npc.py` `CRAFT`, `FORCE_SENDERS`; `field.py` | |
| I8 | B | Two roster entries share tty 11 (CAROT and Sandoval); `/etc/ttys` lists four terminals and the roster has twelve | `npc.py`; `filesystem.py` | |
| I9 | C | Sandoval's post comes from `mhuxt`, a different machine, but Sandoval is in this office's craft group | `filesystem.py` NEWS_MISC_88, `GROUP` | T3 explains it as an account not yet moved. |
| I10 | C | "Tour 2" in Alvarez's notes reads as the game's tour 2; in the fiction it is the second shift of a day | `data/homes.py`; `filesystem.py` `TESTLOG_C` | **Resolved in 7b:** signed "evening tour". |
| I11 | C | Message ids run <44>, <45> for 14 Nov and <46> for 9 Nov, so the spool is not in order of id | `filesystem.py` | |
| I12 | C | The regulars' addresses are Jersey City street names; the office city is the first of the loaded NANPA offices in 201, 212 or 203 and can be another | `data/regulars.py`; `screens/bureau.py` | Plan R4 handles the same problem in shift events. Decided in 7a: the card carries no city, so the street names stand wherever the office is. |
| I13 | C | Four period claims have no `SOURCES.md` row: Mother's Day "forty years"; the satellite "half a second"; the TSPS average call; and the toll-network-above-class-4 line in the memo | section 7 | Needs a row or an [own] marker. |
| I14 | C | `SOURCES.md` has no row for "UNIX Version 7" as the 1983 machine | `filesystem.py` MOTD | |
