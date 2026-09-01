# Making it fun

A plan for the Bell System simulator, written after playing it rather than
after reading it.

---

## Part 1 — The finding

**The game is not hard. It is undiscoverable.**

That distinction decides everything below, and it is the opposite of what
the roadmap has been assuming.

I played a fresh shift as a new player would. The core loop is four
commands:

```
report                      what is on your board
mlt <n>                     measure the line
report dispatch <n> <force> send somebody
report close <n> 5 <fault>  close it out
```

And `mlt` does not make you work for it. It prints the measurement, then
names the fault, then names where to dispatch:

```
TEST RESULT
  Loop measures clean; fault is toward the switch
  System reads this as: Central office equipment (CO_EQUIP)
  Dispatch to: Central office
```

I checked whether that verdict can lie. Over sixty reports it agreed with
the hidden truth **60 out of 60**. There is no telephony knowledge gate at
all: the machine tells you the answer and you type it back.

The one time I got a report wrong during this exercise, it was because
*I did not read the output before dispatching*. I built this thing and I
still made that mistake — which says the loop is not the problem, and
attention is.

### So what is actually wrong

**The first screen is a wall.** `help` shows about forty commands across
four sections, then a footer listing sixteen commands you are *not* signed
off on. A new player's first impression is a list of things they cannot do.

**Nothing states a goal.** No line anywhere says "close the reports on
your board correctly before the tour ends" — which is the whole game.

**The four-command loop is only visible after you type `report`.** It
prints a perfect one-line summary of itself in its footer. You have to
guess `report` first.

**There is a tutorial and nobody will ever see it.** `src/bell_system/tutorial.py`
is real, works, and sits behind a `--tutorial` flag. Its own docstring says
it is "completely separate from the main simulation" and should be run
"BEFORE using" it. A player who types `bell-system` never learns it exists.

**The stakes are in a file you have to know to open.** The Bell System
dissolves in 48 days. That is the emotional centre of the entire game and
it is one line in the message of the day and a memo at `/usr/doc/divestiture`.

**Nothing tells you how the tour went** except a number that most desks
are honestly not measured by.

---

## Part 2 — Principles

Written down so that the plan below can be checked against them, and so
that a future change can be argued with.

**1. Fun is competence, not ease.** The good feeling here is the one
*Papers, Please* runs on: becoming quick at a job that looked
impenetrable an hour ago. Do not remove difficulty. Remove *confusion*,
which is a different thing and is the thing we have.

**2. Teach through the fiction, never through a tutorial box.** This
project already does this well — the previous holder's notes in each home
directory are the best onboarding in the game and they read as somebody's
leftover paper. Everything below should arrive as a person, a memo, a
teletype or a file.

**3. Accuracy bends for a *reason*, and the bend is recorded.** The
project's discipline is provenance-or-admission, and it stays. What
changes is that "this is the simulation's own, for playability" becomes an
acceptable third answer, said out loud, rather than something to avoid.
There is already precedent: `ed` relents after three question marks and
says so.

**4. One thing at a time.** No screen should introduce more than one new
idea. The current `help` introduces forty.

**5. Never a dead end.** Every refusal names the next action. "You are not
signed off on that" is a dead end; "you are not signed off on that — close
two more reports correctly and Halloran will sign you off" is not.

**6. The player's time is theirs.** Anything that takes a real minute —
baud pacing, a long listing — must be interruptible and must be optional.

---

## Part 3 — The plan

Eight tiers. They are numbered because they are a genuine sequence: each
depends on the ones before it. F1 to F3 are most of the felt improvement.

### F1 — The first ten minutes · **the whole ballgame**

Nothing else on this list matters if a player quits in the first five
minutes, and the first five minutes are currently a wall of commands.

- **Fold the tutorial into the game.** Delete the `--tutorial` flag and
  the standalone script. The first shift of a new career *is* the tutorial,
  and it is a tutorial because the wire chief walks you through one report,
  not because a script says "STEP 1 OF 7".
- **The first shift opens with one report and one person.** Halloran
  writes to you on `write(1)`:

  > `Message from ehalloran tty01 [08:02:00 EST]...`
  > `First tour. There is one report on your board and I have kept the`
  > `rest off it until you have closed that one.`
  > `Type 'report'. It tells you what to do next at the bottom.`
  > `EOT`

  That is the entire tutorial. It names the first command and points at
  the affordance that already exists.
- **Halloran follows the loop.** After `report`, a nudge to `mlt`. After
  `mlt`, a nudge to read the TEST RESULT block. After the dispatch, a
  nudge to close. Four messages, then he stops and the board fills.
- **`help` gets a first section: WHAT TO DO NOW.** Three lines, computed
  from actual state — the oldest untested report, the nearest commitment,
  or "your board is clear; `readnews` or `qual`". Everything currently in
  `help` moves below it.
- **`help` stops leading with what you cannot do.** Move the
  not-signed-off list behind `qual`, where it belongs, and make the `*`
  markers a footnote rather than a headline.

*Comparable:* **Papers, Please** opens day one with a single rule — check
the passport is not expired — and adds one rule a day for a fortnight. By
day ten you are doing something that would have been unreadable on day
one, and you never noticed learning it.

*Cost:* small. The messages are four `_POSITION_CHATTER`-shaped entries
and one flag on `Career`. The `help` change is a reordering.

### F2 — Always know what to do next

- **A standing next-action line.** After any command that leaves the
  player with nothing obvious, one line: `Next: TR-02385 is untested and
  due in 1:26. 'mlt 1'.` Suppressible with `set game.prompts off`.
- **Every refusal names the way out.** Audit every "not signed off",
  "unknown option" and "no such" message. Each must end with a command the
  player can actually type.
- **`report` gains a `next` verb.** `report next` picks the report that
  most wants working and shows it. One word instead of reading a table.

*Cost:* small, and it is mostly editing strings that already exist.

### F3 — Hints you ask for, one at a time

The player will get stuck on *what to do*, not on telephony. Give them a
way out that does not spoil anything.

- **`hint`** — with no argument, one nudge about the current situation.
  Ask again, get a bigger one. Three levels: a nudge, a method, the answer.
- **The levels are diegetic.** Level one is Vasquez on `write(1)`. Level
  two is a Bell System Practice reference you can go and read. Level three
  is Halloran telling you outright, and he is slightly short about it.
- **`hint` costs a minute of shift time** and nothing else. No score
  penalty. Being stuck is already the penalty.

*Comparable:* Infocom's **InvisiClues** — hint booklets printed in
invisible ink where you revealed one hint at a time with a marker, so you
got the smallest nudge that unstuck you rather than the answer. The
best-loved hint system ever shipped, and it works because *asking is a
deliberate act*.

*Cost:* moderate. One new module, a hint table keyed by situation, and the
situation detector — which is mostly the same logic F2 needs.

### F4 — Stakes, and people who remember you

The divestiture is the best thing in this game and it is currently a memo.

- **A countdown that means something.** The shift is 14 November 1983 and
  the Bell System ends on 1 January. Put "48 days" where it will be seen —
  the login banner, the handoff record — and let it move if the epoch does.
- **Halloran has an arc.** He signs your qualifications. He should notice
  the third one, and he should say something on the last shift before
  divestiture that he would not say on the first.
- **Recurring customers.** A chronic line is already modelled. Give three
  or four of them names and a history that survives across shifts, so that
  `custdb` on a number you have seen before says *you have been here
  before*.
- **A last shift.** If a career reaches enough tours, the final one is
  31 December 1983. Same board, same work, and everybody in the building
  knows. Nothing mechanical changes. That is the point.

*Comparable:* **Papers, Please** again — the reason its bureaucracy lands
is that the same face comes back on day nine and you remember them.

*Cost:* moderate. The chronic-line machinery exists; the arc is writing.

### F5 — Feedback that teaches

- **A post-mortem instead of a score.** When a report closes wrong, say
  what would have caught it: *"The insulation resistance was 9,000 ohms
  tip to ring. That is wet cable, not a short — a short reads near zero."*
  One sentence, the actual numbers from the actual measurement.
- **A tour summary that reads as prose.** The handoff already carries a
  tally. Add three sentences above it: what went well, what did not, and
  the one thing to do differently. Written from the tally, not scored.
- **Show the trend.** After the third shift, `qual` shows the last five
  index figures as a sparkline. Getting better is the reward.

*Comparable:* **Return of the Obra Dinn** confirms deductions three at a
time — enough feedback to keep going, not so much that you brute-force it.

*Cost:* moderate. The post-mortem needs a rule per fault, which is a
dozen sentences and is the highest-value writing on this list.

### F6 — The shape of a session

- **Save and resume mid-shift.** Currently a shift is one process. It
  should survive being closed. This is the single most likely cause of a
  player never coming back.
- **`shift` shows where you are in the tour** — how long is left, what is
  due, what is carried.
- **Escalation across a career.** Tour one is quiet. By tour five the
  board is deeper, the weather is worse, and the SCC is handing out
  offices. The difficulty setting stays what it is: how forgiving the
  scoring is, not how much is happening.

*Cost:* the save/resume is the largest single item on this document.
Everything else here is small.

### F7 — Things to find

The game already rewards curiosity well — the netnews spool, the moo
scoreboard, `bcd`, the fortunes. More of the same, and one new kind.

- **`moo` already has a scoreboard with a grudge on it.** Let the player
  actually get onto it, and let Okafor comment if they beat her eleven.
- **A locked thing.** One file on the machine that cannot be read on the
  first tour and can on a later one. `/usr/adm/sulog` is already the shape
  of this: a record of people trying things they should not.
- **Let `tone` be a puzzle.** A trouble report where the customer
  describes a sound. `tone busy` and `tone reorder` are the same two
  frequencies at different rates; hearing the difference is the answer.
  This is the one place the simulation can ask something a screen cannot.
- **A break.** `moo`, `arithmetic` and `fortune` are here. Say so
  somewhere — Zachtronics ships a solitaire game inside SHENZHEN I/O for
  exactly this reason and puts it on the box.

### F8 — What not to do

Written down because each of these is tempting and each would make it
worse.

- **Do not add a score that competes with the service index.** R5a
  already resisted this once. A second number is read as a second thing to
  optimise.
- **Do not gate content behind telephony knowledge.** Nothing should
  require knowing what a false cross or ground *is*. `mlt` names it; that
  is the design and it is correct.
- **Do not make the machine friendlier than a machine.** `ed` answering
  `?` is one of the best jokes in the game. The fix for confusion is
  *elsewhere* — a person, a memo, a hint you asked for — not a chattier
  shell.
- **Do not add a progress bar, an XP number, or an achievement popup.**
  The qualifications are the progression and they are diegetic. Keep it.
- **Do not build multi-user.** Already declined in the roadmap and it is
  still the right call.
- **Do not remove the pacing.** It is off by default in a pipe, it is
  interruptible, and at 300 baud it is one of the most evocative things
  here. Make it discoverable, not absent.

---

## Part 4 — Order of work

| | Tier | Effort | Why here | |
|---|---|---|---|---|
| 1 | F1 first ten minutes | small | Nothing else matters if they quit | **done** |
| 2 | F2 next action | small | Mostly editing strings that exist | **done** |
| 3 | F5 post-mortem | moderate | Turns every mistake into a lesson | **done** |
| 4 | F3 hints | moderate | Needs F2's situation detector | |
| 5 | F4 stakes | moderate | Writing, and the best writing available | |
| 6 | F7 things to find | small | Cheap, and it is the flavour | |
| 7 | F6 save/resume | large | The biggest single build here | |

The first three are built. `screens/guidance.py` holds the one function
that decides what to do next, and F3's hint levels want the same
function, so the ordering held: F3 is now a matter of writing three
levels of nudge around a situation detector that already exists.

F1 and F2 together are perhaps two days and they are most of the felt
difference between "this is impenetrable" and "oh, I see".

---

## The one-sentence version

The game already tells you the answer; it just never tells you where to
stand.
