# Playtest report template

For one session at the terminal, whether a person or a scripted run. Paste the
block below into the PR or an issue, fill it in, and route the findings. Nothing here is sent anywhere; the
optional local log is row A20.

Adapted from the playtest-report skill and the CD-PLAYTEST gate in
Donchitos/Claude-Code-Game-Studios (MIT). Changes for this game: deaths
become wrong closes and repeats, time per area becomes minutes per report
and per tour, the quantitative block adds commands discovered against
missed and lore found, and the closing pillar check is written for a
person to run, not an agent.

Companion files: `plan.md` (pillars section 1), `difficulty-curve.md`
(checklist, section 11), `narrative-bible.md` (what the lore should be).

---

```markdown
# Playtest report

## Session
- **Date**:
- **Build**: commit or branch, and the phase it is on (plan section 5)
- **Tester**: name, or "bot skill 0.6 / 0.9"
- **Profile and assists**: fun / craft, and every `set` departure (`set` lists them)
- **Pacing**: 300 baud, or `display.pacing off`
- **Session type**: first time / returning / targeted / scripted wave playtest
- **Position**: sysop or another desk
- **Real time played**:
- **Tours played**: from tour N to tour M (the dates, e.g. 14 Nov to 26 Nov)

## Test focus
What was being tested, in one sentence, and the hypothesis. For the wave
playtest this is "the build at the end of wave N reads as the game in
section 1".

## First five minutes (first sessions only)
- **Understood what the job is?** Yes / No / Partially
- **Understood the commands?** Yes / No / Partially (which not)
- **Mood**: engaged / confused / bored / frustrated / amused
- **Where they first stopped and for how long**:

## Flow
### What worked
-
### Pain points (feel, not defects)
- Issue, severity high / medium / low
### Confusion
- Where, and why (what the screen said against what they expected)
### Moments of delight
-

## Bugs
Anything that plainly breaks goes here, not under pain points.

| # | What | Severity | Reproduce with |
| ---: | --- | --- | --- |

## Numbers
- **Wrong closes and repeats**: count and where. For each, the report number, what they closed it as, the real fault, and whether the debrief made the cause clear to them (yes / no).
- **Minutes per report**: the first, the median, the slowest. Real minutes at the keyboard, and shift minutes (`shift`).
- **Minutes per tour**: real and shift, per tour, and whether the board was cleared, carried or aged out at handoff.
- **Closes per tour, correct and wrong**, and the sign-offs held at each handoff.
- **Index at each handoff** and its band; commendations earned once phase 5 is in.
- **Commands discovered vs missed**: the commands used without prompting; the ones the tester says they did not know existed (`man`, `hint`, `qual`, `finds`, `training unix` and the rest the build has).
- **Lore found**: which files and where from (`ls`, `cat`, `grep`, a message), against the list in the bible. Say how it was found and whether it was understood.
- **Hints used**: how many, at what level, and on which reports.
- **Assists changed during the session**:

## Overall
- **Would play another tour?** Yes / No / Maybe
- **Difficulty**: too easy / right / too hard, for the profile used
- **Pacing**: too slow / good / too fast, tour by tour if it changed
- **Session length**: shorter / right / longer

## Pillar check
Run by whoever ran the session, after the numbers, in this order. Answer in
one line each and quote the moment. A check that cannot be answered from this
session is "not seen", never a pass.

1. **The desk is a system you learn.** Did the tester win anything without knowing why it worked? Did they do something new that they had not done before?
2. **Every report is a person.** Name one person a report made them care about. Did a consequence show in someone's voice, or only as a number?
3. **The Bell System is ending.** Could they say what date it was and what was different about it, without looking? Did any tour feel like filler?
4. **The machine is the story.** What did they find with `ls`, `cat` or `grep`? Did any story arrive that they did not go looking for, and how?
5. **Friction is chosen and period.** Was any friction one they could not turn down? Did anything read as a real fact that is not sourced?
6. **Anti-pillars.** Did a cutscene, an early end, anything that works as phreaking instructions, an invented real person, or a grind or twitch moment appear? Name it.

**Verdict: APPROVE / CONCERNS / REJECT**
- APPROVE: the pillars held and the session had no drift.
- CONCERNS: list each gap between the intended game and the one played, naming the pillar. Mechanics that feel fine alone but undermine another pillar belong here (pillar drift).
- REJECT: the game played is not the game in section 1; stop playtesting and redesign.

## Top three from this session
1.
2.
3.

## Routing
Put every finding in one bucket.

| Bucket | Finding | Goes to |
| --- | --- | --- |
| Design: fun, confusion, a mechanic that breaks a pillar | | an issue labelled `design` and `pillar: ...`; check `plan.md` for the row it changes |
| Balance: numbers that feel wrong | | an issue citing the lever in `difficulty-curve.md`; re-measure with `tools/index_calibration.py` |
| Bug: reproducible defect | | an issue with the reproduce steps |
| Polish: friction, feel, wording | | the P3 checklist in #43 |
```

---

## Notes for whoever runs one

- A scripted run uses bots through the terminal, not a person; its numbers fill the Numbers block, and its pillar check can only answer 1 and 5. Say so in the report.
- One wave playtest at the end of each wave (`plan.md` section 10) is enough. A wrong sign-off count or a hint level is a finding, not a reason to run another.
- Do not paste transcripts of long sessions into the report; link them, and quote only the lines the findings turn on.
