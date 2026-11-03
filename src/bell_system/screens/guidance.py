"""
What to do next, and how to be shown it.

Playing a fresh shift the way a new player would turned up one finding
that reorganised the whole plan: the game is not hard, it is
undiscoverable. The core loop is four commands and mlt(1) names the fault
and the dispatch outright - it was right sixty times out of sixty when
that was measured. Nothing in the loop requires knowing any telephony.

What the loop does require is knowing that it exists, and nothing said so.
The first screen was forty commands and then a list of sixteen you were
not signed off on, so a new craftsperson's first impression was a list of
things they could not do.

This module is the answer to "what now". One function reads the actual
state of the board and returns the single next thing worth doing, and
three different parts of the terminal ask it: the standing prompt after a
command, the top of help(1), and the wire chief on a first tour.

Asking one place means those three can never disagree, which they would
have within a fortnight if each worked it out for itself.

help(1) lives here for the same reason. It used to open on forty commands
and close on the sixteen you were not signed off on; it now opens on the
one thing worth doing, which is the same sentence the standing prompt
prints, because it is the same function.
"""

from typing import Iterable, List, NamedTuple, Optional, Tuple

from ..console import wrap
from ..data.commendations import (
    COMMENDATIONS, COMMENDATIONS_BY_KEY, MINIMUM_CLOSES)
from ..data.positions import POSITION_COMMANDS
from ..data.hints import EXHAUSTED, HINTS
from ..data.trouble import FAULTS
from ..loop_testing import (
    STAGE_NUMBERS, measure_loop, names_fault, reading_is_clean)
from ..npc import render as render_message
from ..progression import QUALIFICATIONS_BY_KEY, Kpis
from ..reports import hours_minutes
from ..commitment import commitment_label
from ..verbs import measured
from .session import SessionState


class NextAction(NamedTuple):
    """One thing worth doing, and the command that does it."""

    # One line, in the second person, saying what is worth doing.
    reason: str
    # What to type. Empty when there is genuinely nothing pressing.
    command: str
    # Which step of the loop this is, for the first-tour walkthrough.
    step: str


# What asking costs, in minutes of the shift. The same order as reading
# the frame record, because that is what it is: a minute spent finding out
# rather than working.
HINT_MINUTES = 1

# Cells in the board-cleared meter.
METER_WIDTH = 20

# Nothing pressing. Not a failure state: a clear board at the end of a tour
# is the point of the job.
NOTHING = NextAction('', '', 'idle')


class GuidanceCommands(SessionState):
    """
    Working out what to do next, and saying so.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- the one place that decides ---------------------------------------

    def next_action(self) -> NextAction:
        """
        Return the single next thing worth doing on this board.

        Ordered by what would actually cost you: a report the field has
        already cleared and nobody has closed out, then anything past its
        commitment, then anything untested, then the nearest commitment.
        A report is never suggested twice in a row for the same reason,
        because the point is to move the board rather than to nag.
        """
        # A practical's report is Halloran's, not a customer's: nothing
        # about it is worth closing, dispatching or measuring for its own
        # sake, and 'report close' on it is refused.
        staged = self._practical_open()
        pending = [report for report in self.desk.pending()
                   if not report.practical]
        if staged is not None:
            if not measured(staged[1]):
                return NextAction(
                    f"{staged[1].number} is {staged[0].title}, the "
                    f"practical. He signs the reading as well as the fix: "
                    f"measure it first.",
                    f"mlt {staged[1].number}", 'measure')
            return NextAction(
                f"{staged[1].number} is {staged[0].title}, the practical. "
                f"Work it, then hand it in.",
                'qual submit', 'practical')
        if not pending:
            return self._nothing_pending()

        # The field has been and gone. Closing it costs two minutes and
        # leaving it costs the customer the rest of the day.
        done = [report for report in pending
                if report.field_finding or report.sheath_repaired]
        if done:
            report = done[0]
            if report.field_finding == 'NONE':
                # Nothing was there. Closing it as trouble found is scored
                # wrong, and the right close names no condition.
                return NextAction(
                    f"{report.number} was looked at in the field and "
                    f"nothing was wrong. It is waiting to be closed out.",
                    f"report close {report.number} 8", 'close')
            # The code is the answer, so it is only typed for the player
            # while the fault is still being named to them.
            if not names_fault(self._reading_stage(report, count=False)):
                found = '<fault>'
            else:
                found = report.field_finding or 'WET'
            return NextAction(
                f"{report.number} has been cleared in the field and is "
                f"waiting to be closed out.",
                f"report close {report.number} 5 {found}",
                'close')

        overdue = [report for report in pending if report.overdue()]
        if overdue:
            report = overdue[0]
            if not report.tested:
                return NextAction(
                    f"{report.number} is past its commitment and has not "
                    f"been measured.",
                    f"mlt {report.number}", 'measure')
            if self._reads_clean(report):
                return self._clean_reading(report)
            return NextAction(
                f"{report.number} is past its commitment. It has been "
                f"measured; somebody needs to go.",
                f"report show {report.number}", 'dispatch')

        untested = [report for report in pending if not report.tested]
        if untested:
            report = untested[0]
            if self.first_tour() and 'callback' not in self._tour_nudges:
                return NextAction(
                    f"{report.number} says one thing on the card and the "
                    f"customer will say another.",
                    f"report callback {report.number}", 'callback')
            return NextAction(
                f"{report.number} has not been measured. "
                f"{commitment_label(report)}.",
                f"mlt {report.number}", 'measure')

        # Everything measured, nothing overdue: send somebody to the one
        # that runs out first.
        report = pending[0]
        if not report.dispatched_to and self._reads_clean(report):
            return self._clean_reading(report)
        if not report.dispatched_to:
            fault = report.record.fault
            force = ('' if self._reading_stage(report, count=False)
                     == STAGE_NUMBERS else self._dispatch_for(fault))
            return NextAction(
                f"{report.number} is measured and waiting on a crew. "
                f"{commitment_label(report)}.",
                f"report dispatch {report.number} {force.lower()}"
                if force else f"report show {report.number}",
                'dispatch')
        return NextAction(
            f"{report.number} is with the field. Nothing on the board "
            f"needs you this minute.",
            'report', 'wait')

    def _dispatch_for(self, fault: str) -> str:
        """
        Where a fault wants somebody, when the player has already measured.

        Only offered once the report has been tested: suggesting the right
        force before the measurement would hand over the answer, and the
        measurement is the part worth doing.
        """
        where = FAULTS[fault].dispatch
        return '' if where.startswith('None') else where

    def _reads_clean(self, report) -> bool:
        """
        Whether a measured report's readings cannot tell the office from
        nothing, so that a dispatch would be a guess.

        Only at the numbers stage: before that mlt has named a crew class
        for the report, and the prompt must not contradict it.
        """
        if not report.tested or report.dispatched_to:
            return False
        if self._reading_stage(report, count=False) != STAGE_NUMBERS:
            return False
        record = report.record
        return reading_is_clean(measure_loop(
            record.telephone_number, record.fault, name_fault=False))

    def _clean_reading(self, report) -> NextAction:
        """
        What to do with a report whose loop reads clean everywhere.

        Office equipment, a false cross or ground and no trouble all look
        the same to mlt, and the one cheap thing that separates them is the
        frame record. Once it has been looked up, or where the player is not
        signed off to look, the answer is no longer a lookup, and nothing
        here says which of the three it is.
        """
        number = report.number
        if not self.career.may_use('cosmos'):
            return NextAction(
                f"{number} reads clean on every measurement; sheet 660-003.",
                f"report show {number}", 'dispatch')
        if report.frame_looked_up:
            return NextAction(
                f"{number} reads clean and its frame record has been read. "
                f"What is left is your call; sheet 660-003.",
                f"report show {number}", 'dispatch')
        return NextAction(
            f"{number} reads clean on every measurement; sheet 660-003. "
            f"The frame record has more.",
            f"cosmos jumper {report.record.telephone_number}", 'frame')

    def _nothing_pending(self) -> NextAction:
        """What is worth doing with a clear board."""
        if self.career.shift == 1 and self.career.reports_closed == 0:
            return NextAction(
                "Nothing on the board yet. The bureau will send something.",
                'report', 'wait')
        offered = self.career.offer_available()
        if offered:
            return NextAction(
                f"Board clear. {offered[0].name} is ready for its "
                f"practical.",
                f"qual take {offered[0].key}", 'idle')
        ready = self._next_qualification()
        if ready is not None:
            return NextAction(
                f"Board clear. You are {ready} from being offered your "
                f"next sign-off.",
                'qual', 'idle')
        return NextAction(
            "Board clear. Worth reading something while it lasts.",
            'readnews', 'idle')

    def _next_qualification(self) -> Optional[str]:
        """How far off the next sign-off is, in plain words."""
        from ..progression import QUALIFICATIONS
        held = set(self.career.qualifications)
        difficulty = self._difficulty()
        for qualification in QUALIFICATIONS:
            if qualification.key in held:
                continue
            needed = (qualification.requires_reports
                      * difficulty.reports_per_qualification)
            short = needed - self.career.reports_correct
            if short <= 0:
                continue
            return (f"{short} correct closure"
                    f"{'' if short == 1 else 's'}")
        return None

    # -- what to do next --------------------------------------------------

    # Which step of the first-tour walkthrough a command completes. The
    # wire chief speaks after these and nothing else.
    LOOP_STEPS = {'report': 'board', 'mlt': 'measure'}

    # Commands that leave the operator looking at something. A standing
    # prompt after these would be noise; a prompt after `pwd` is the point.
    SELF_EXPLANATORY = frozenset({
        'help', 'man', 'qual', 'report', 'handoff', 'set', 'clear',
        'history', 'more', 'cat', 'ls', 'readnews', 'moo', 'fortune',
        'arithmetic', 'ed', 'training', 'hint',
    })

    def _add_guidance(self, result: str, command: str) -> str:
        """
        Put the wire chief, or the standing prompt, on the end of a result.

        Two different things and only ever one of them. On a first tour the
        chief is walking you through one report and the prompt would be
        talking over him; after that he is gone and the prompt is what is
        left.
        """
        nudge = self.first_tour_nudge(self.LOOP_STEPS.get(command, ''))
        if nudge is not None:
            return f"{result}\n{nudge}" if result else nudge

        if command in self.SELF_EXPLANATORY or self.first_tour():
            return result
        line = self.next_line()
        if not line:
            return result
        return f"{result}\n\n{line}" if result else line

    # -- saying it --------------------------------------------------------

    def next_line(self) -> str:
        """
        The standing prompt, or nothing.

        Printed after a command that leaves the operator with nothing
        obvious in front of them. Off with 'set game.prompts off', because
        somebody who knows the job does not need telling.
        """
        if not self.settings.is_on('game.prompts'):
            return ''
        action = self.next_action()
        if not action.command:
            return ''
        return f"Next: {action.reason} '{action.command}'"

    def guidance_rows(self) -> List[str]:
        """The WHAT TO DO NOW block at the top of help(1)."""
        action = self.next_action()
        rows = ['WHAT TO DO NOW', '-' * 66]
        if action.command:
            rows.append(f"   {action.reason}")
            rows.append(f"   Type: {action.command}")
        else:
            rows.append("   Nothing is waiting on you.")
        rows.append('')
        rows.append("   The whole job is four commands: report, mlt, "
                    "report dispatch,")
        rows.append("   report close. mlt gives you the readings; "
                    "'report faults' says")
        rows.append("   what they add up to.")
        rows.append("   Stuck on something? 'hint' asks somebody. Ask "
                    "again for more.")
        return rows

    def dead_end(self, message: str) -> str:
        """
        Put a way out on the end of a refusal.

        A refusal that names nothing is where a player stops. Every one of
        them can afford a second line, and this is that line. Off with the
        standing prompt, because it is the same prompt.
        """
        if not self.settings.is_on('game.prompts'):
            return message
        action = self.next_action()
        # Nothing is waiting, so there is no way out to name. Telling
        # somebody who mistyped a command to go and read the news is not
        # help, it is the terminal having the last word.
        if not action.command or action.step == 'idle':
            return message
        return f"{message}\n\nMeanwhile: {action.reason} '{action.command}'"

    def first_tour(self, after_close: bool = False) -> bool:
        """
        Whether this is somebody's first ten minutes on the job.

        True from the moment a first shift opens until the first report is
        closed out. The board is held at one report for the whole of it and
        the building keeps quiet, because the wire chief is talking and one
        thing at a time is the point.

        `after_close` extends it by exactly one closure, for the one line
        the chief says on the way out.
        """
        if self.career.shift != 1:
            return False
        closed = self.career.reports_closed
        return closed == 0 or (after_close and closed == 1)

    def first_tour_nudge(self, step: str) -> Optional[str]:
        """
        The wire chief walking a new craftsperson through one report.

        This is the entire tutorial. It is not a tutorial box and it does
        not say STEP 1 OF 7: it is Halloran on write(1), because that is
        who would do it and because the game already has that channel.

        Fires once per step of the loop, only on a first tour, and stops
        of its own accord once the first report is closed.
        """
        if not self.first_tour(after_close=step == 'closed'):
            return None
        if step in self._tour_nudges:
            return None
        lines = FIRST_TOUR.get(step)
        if lines is None:
            return None
        if step == 'measure' and not self._difficulty().annotation_sightings:
            lines = FIRST_TOUR_MEASURE_UNNAMED
        self._tour_nudges.add(step)
        message = self.switchroom.chief_nudge(self.clock.now(),
                                             list(lines))
        return render_message(message, self._stamp())

    # -- asking for help ---------------------------------------------------

    def cmd_hint(self, args: Optional[List[str]] = None) -> str:
        """
        Ask somebody. Ask again and you get more.

        Three levels to a situation and they are revealed one at a time,
        so what you get is the smallest nudge that unsticks you rather
        than the answer. The level resets whenever the situation changes,
        because a player who has just moved on to a different problem is
        at the beginning of that one.

        A minute of shift time and nothing else, and not even that while a
        practical is on the board. There is no score
        penalty for asking: being stuck is already the penalty, and a hint
        system with a cost attached is a hint system nobody uses.
        """
        del args
        situation = self._situation()
        if situation != self._hint_situation:
            self._hint_situation = situation
            self._hint_level = 0
        self._hint_level += 1
        # A practical is not the shift, and the minute is for the shift.
        if situation != 'practical':
            self._pass_time(HINT_MINUTES)

        levels = (self._practical_hints() if situation == 'practical'
                  else HINTS[situation])
        if self._hint_level > len(levels):
            return render_message(self.switchroom.advice(
                self.clock.now(), 'ehalloran', list(EXHAUSTED),
                len(levels)), self._stamp())
        sender, lines = levels[self._hint_level - 1]
        asked = render_message(self.switchroom.advice(
            self.clock.now(), sender, list(lines), self._hint_level),
            self._stamp())
        if self._hint_level < len(levels):
            asked = f"{asked.rstrip()}\n\nStill stuck? Type 'hint' again."
        return asked

    def _situation(self) -> str:
        """
        Name what the operator is in the middle of.

        The same step the standing prompt works from, so the hint and the
        prompt can never end up describing different situations.

        The one exception is somebody who has not yet looked at the board.
        The answer there is not "measure that report", it is "there is a
        loop and here it is" - but only until they have typed report(1)
        once. After that a first tour is stuck on the same things anybody
        else is stuck on, and gets the same three levels about them.
        """
        if self._practical_open() is not None:
            return 'practical'
        # 'board' is marked the first time report(1) runs, so this is
        # exactly "has not looked at the board yet".
        if self.first_tour() and 'board' not in self._tour_nudges:
            return 'first'
        step = self.next_action().step
        return step if step in HINTS else 'idle'

    # -- looking back ------------------------------------------------------

    def tour_summary(self, closed: int, correct: int, missed: int,
                     repeats: int, unmeasured: int = 0) -> List[str]:
        """
        Three sentences on a tour, written from its tally.

        The handoff already carried the numbers. Numbers are a score, and a
        score tells somebody how they did without telling them anything
        about the work. These say what went well, what did not, and the one
        thing worth doing differently - and only ever one, because a list of
        four things to improve is a list nobody acts on.

        Args:
            closed: Reports closed out this tour
            correct: How many of those matched what was on the line
            missed: Commitments passed
            repeats: Reports that came back after being closed
            unmeasured: Closes this tour that no mlt came before

        Returns:
            The sentences, or an empty list for a tour with no work in it
        """
        if not closed:
            return ["Nothing was closed out this tour. The board is the "
                    "job: 'report next' picks the one that wants working."]

        wrong = closed - correct
        lines = []

        if correct == closed:
            lines.append(f"Every one of the {closed} you closed matched what "
                         f"was on the line.")
        elif correct:
            lines.append(f"{correct} of {closed} matched what was on the "
                         f"line.")
        else:
            lines.append(f"You cleared {closed} off the board, which is the "
                         f"half of the job that is not in doubt.")

        # The largest single failure is the one worth naming. Naming three
        # is how a tour summary becomes something a player skips.
        worst = max((wrong, 'wrong'), (missed, 'missed'), (repeats, 'repeat'),
                    key=lambda pair: pair[0])
        if not worst[0]:
            lines.append("Nothing came back, nothing ran past commitment.")
            lines.append("There is not much to do differently. Carry on.")
            return lines

        count, kind = worst
        lines.append(FAILURES[kind][0].format(count=count,
                                              s='' if count == 1 else 's'))
        lines.append(FAILURES[kind][1]
                     + (UNMEASURED_ADVICE if kind == 'wrong' and unmeasured
                        else ''))
        return lines

    def sparkline(self, values: List[float], span: int = 5) -> str:
        """
        Draw the last few figures as a bar, so a trend reads at a glance.

        A column of decimals is a table and nobody reads a table for a
        trend. Eight levels, because that is what the block characters give
        and the console transliterates them for a terminal that cannot
        print them.
        """
        recent = values[-span:]
        if len(recent) < 2:
            return ''
        low, high = min(recent), max(recent)
        if high - low < 0.05:
            # A flat run would otherwise draw as noise around a rounding
            # error. Flat is the honest picture.
            return SPARK_LEVELS[len(SPARK_LEVELS) // 2] * len(recent)
        step = (high - low) / (len(SPARK_LEVELS) - 1)
        return ''.join(SPARK_LEVELS[int(round((value - low) / step))]
                       for value in recent)

    # -- the credit side ---------------------------------------------------

    def kpi_rows(self, kpis: Kpis, heading: str) -> List[str]:
        """
        The five KPIs under a heading, with the label that says how far to
        trust them.

        None of the five is a Bell System figure: they are the simulation's
        own measures, and they are measures, not part of the score. The
        service index stays the only thing that takes marks off.
        """
        def percent(value: Optional[float]) -> str:
            return 'none yet' if value is None else f"{value:.1f}%"

        mttr = ('none yet' if kpis.mttr is None
                else f"{hours_minutes(int(round(kpis.mttr)))}  "
                     f"({kpis.mttr:.0f} min)")
        age = ('none yet' if kpis.backlog_age is None
               else f"{hours_minutes(int(round(kpis.backlog_age)))} on the "
                    f"{len(self.desk.customers())} open")
        repeats = ('none yet' if kpis.repeat_rate is None
                   else f"{kpis.repeat_rate:.1f} per 100 closed")
        return [
            f"{heading}  {self.provisional_label(kpis.closed)}",
            '-' * 74,
            f"  Mean time to repair   {mttr}",
            f"  Commitments met       {percent(kpis.commitments_met)}",
            f"  Right first dispatch  {percent(kpis.first_time_right)}",
            f"  Repeat rate           {repeats}",
            f"  Backlog age           {age}",
        ]

    def provisional_label(self, closes: int) -> str:
        """PROVISIONAL, and how far off, until there are enough closes."""
        if closes >= MINIMUM_CLOSES:
            return f"({closes} closed)"
        return f"PROVISIONAL ({closes} of {MINIMUM_CLOSES} closes)"

    def tour_index_row(self) -> str:
        """This tour's own index, which the cumulative one cannot show."""
        career = self.career
        if not career.tour_scored():
            return "  Tour index            none yet: nothing closed"
        return (f"  Tour index            {career.tour_index():.1f} of 100  "
                f"{self.provisional_label(career.tour_counts()['closed'])}")

    def board_meter(self) -> str:
        """
        How much of this tour's board has been cleared.

        Not a score. The index is a rate, so a perfect five-report tour and
        a perfect thirty-two read the same on it; this is the one place the
        difference shows.
        """
        closed = self.career.tour_counts()['closed']
        total = closed + len(self.desk.customers())
        if not total:
            return "  Board cleared         nothing on the board"
        filled = int(round(METER_WIDTH * closed / total))
        return (f"  Board cleared         [{'#' * filled}"
                f"{'.' * (METER_WIDTH - filled)}] {closed} of {total}")

    def credit_rows(self) -> List[str]:
        """The tour's index, its meter and its KPIs: what a handoff shows."""
        kpis = self.kpi_rows(self.career.tour_kpis(), 'KPIs THIS TOUR')
        # The heading carries the PROVISIONAL label, so it stays; the rule
        # under it is for the qual screen.
        return [self.tour_index_row(), self.board_meter(), '',
                kpis[0], *kpis[2:]]

    def commendation_lines(self, earned: List[str]) -> List[str]:
        """The commendations earned this tour, named, or nothing."""
        known = [COMMENDATIONS_BY_KEY[key] for key in earned
                 if key in COMMENDATIONS_BY_KEY]
        if not known:
            return []
        rows = ['COMMENDATIONS EARNED THIS TOUR', '-' * 66]
        for commendation in known:
            rows.append(f"  {commendation.name}")
            rows.extend(f"    {line}" for line in
                        wrap(commendation.description, 60))
        return rows

    def commendation_roll(self) -> List[str]:
        """Every commendation there is, marked where it is held."""
        held = self.career.commendations
        rows = [f"COMMENDATIONS  {sum(c.key in held for c in COMMENDATIONS)}"
                f" of {len(COMMENDATIONS)}", '-' * 74]
        for commendation in COMMENDATIONS:
            mark = 'x' if commendation.key in held else ' '
            rows.append(f"  [{mark}] {commendation.name}")
            rows.extend(f"      {line}" for line in
                        wrap(commendation.description, 62))
        rows.append("  Earned once and kept. The names and what earns them "
                    "are the simulation's own.")
        return rows

    # -- help(1) ----------------------------------------------------------

    # Commands each position works day to day. Every name here is checked
    # against the dispatch table by the test suite: this list once carried
    # two commands that had never existed.
    # What each desk reaches for, printed as its section of help(1).
    # The table lives in data/positions.py, where the rest of what is
    # different about a position lives with it.
    ROLE_COMMANDS = POSITION_COMMANDS

    # The work itself, which every position has a board of.
    BUREAU_COMMANDS = (
        ('report', 'The pending trouble reports on your board'),
        ('mlt', 'Measure a subscriber loop'),
        ('testboard', 'The test board: loops, test lines, supervision'),
        ('testline', 'Far-end test lines and responders'),
        ('testcall', 'Place a test call through the network'),
        ('qual', 'Your craft record and service index'),
        ('hint', 'Ask somebody what to do. Ask again for more'),
    )

    SHELL_COMMANDS = (
        ('cd', 'Change directory'),
        ('ls', 'List a directory (-l for the long form)'),
        ('cat', 'Read a file'),
        ('grep', 'Search a file for a pattern'),
        ('finds', 'What you have turned up'),
        ('wc', 'Count lines, words and characters'),
        ('man', 'The manual page for any command'),
    )

    PEOPLE_COMMANDS = (
        ('who', 'Who is on the system'),
        ('write', 'Write to another terminal'),
        ('mail', 'Read your mail'),
        ('orderwire', 'The maintenance order wire'),
        ('handoff', 'Shift turnover; handoff relieve to sign off'),
    )

    def cmd_help(self, args: Optional[List[str]] = None) -> str:
        """
        Show available commands, marking what this craftsperson may work.

        Qualification governs what may be used, so the listing says so rather
        than offering a command that will be refused.

        Args:
            args: Optional command name for specific help

        Returns:
            Help information formatted for terminal display
        """
        if args and args[0]:
            command = args[0].lower()
            command = self.COMMAND_ALIASES.get(command, command)
            if command not in self.man_pages:
                return (f"No help available for '{args[0]}'. "
                        f"Use 'help' to see available commands.")
            needed = self.career.qualification_for_command(command)
            note = ''
            if needed and not self._may_use(command):
                note = (f"\n\nYou are not signed off on "
                        f"{QUALIFICATIONS_BY_KEY[needed].name}. "
                        f"Type 'qual'.")
            first = self.man_pages[command].strip().splitlines()
            summary = first[1].strip() if len(first) > 1 else command
            return (f"{summary}\n\n"
                    f"Use 'man {command}' for complete documentation.{note}")

        pending = len(self.desk.pending())
        lines = [
            f"Bell System UNIX V7 Commands - Role: "
            f"{self.role_name or 'unassigned'}",
            '=' * 66,
            '',
        ]
        # What to do comes before what exists. A new craftsperson opening
        # help(1) on a board with work on it wants one instruction, not a
        # catalogue, and the catalogue is still directly underneath.
        lines.extend(self.guidance_rows())
        lines.extend([
            '',
            f"THE WORK   {pending} trouble report(s) on your board, "
            f"{self.shift_time()} into the shift",
            '-' * 66,
        ])
        lines.extend(self._help_rows(self.BUREAU_COMMANDS))

        role_commands = self.ROLE_COMMANDS.get(self.role or '')
        if role_commands:
            lines.extend(['', f"THIS POSITION   {self.role_name}", '-' * 66])
            lines.extend(self._help_rows(
                (name, self._help_summary(name))
                for name in sorted(role_commands)
            ))
            if self.position.verb:
                lines.append(f"   Only this desk: {self.position.verb}")
                lines.append(f"   {self.position.pressure}")

        lines.extend(['', 'THE MACHINE', '-' * 66])
        lines.extend(self._help_rows(self.SHELL_COMMANDS))
        lines.append("   Commands join with a pipe: who | wc -l")
        lines.append("   Worth reading: /etc/motd, /usr/doc/divestiture,")
        lines.append("                  /usr/users/sysop/notes")
        # The job is reachable as files, which is the whole argument for
        # putting it on a UNIX machine rather than behind twelve screens.
        lines.append("   The board is files: /usr/lmos holds one per report, "
                     "plus board,")
        lines.append("                       closed and cable. Your mail is "
                     "/usr/spool/mail.")
        # Zachtronics ships a solitaire game inside SHENZHEN I/O and puts
        # it on the box, for the reason that a job with no break in it is
        # a job. These have been in /usr/games since the filesystem was
        # written and nothing has ever said so.
        lines.append("   There is a break: moo, fortune, arithmetic. "
                     "/usr/games has them.")

        lines.extend(['', 'THE OTHER CRAFT', '-' * 66])
        lines.extend(self._help_rows(self.PEOPLE_COMMANDS))

        lines.extend([
            '',
            'THE SYSTEM',
            '-' * 66,
            "  set               Settings, including difficulty and ambience",
            "  bsp search <topic>  Bell System Practices",
            "  help <command>    One line on a single command",
            "  ps, df, date, pwd, more, head, tail, sort, echo, file, cal",
            "  exit              Log out",
            '',
        ])

        # The list itself lives in qual(1), where the sign-offs that open
        # each one are. Ending help(1) on sixteen things you may not do was
        # the last thing a new craftsperson read, and it read as a wall.
        locked = sum(1 for name in self._command_handlers
                     if not self._may_use(name))
        if locked:
            lines.append(f"* marks a command you are not signed off on "
                         f"({locked} of them). Type 'qual'.")
        return '\n'.join(lines)

    def _help_rows(self,
                   entries: Iterable[Tuple[str, str]]) -> List[str]:
        """Render command rows, marking anything not signed off."""
        rows = []
        for name, summary in entries:
            mark = ' ' if self._may_use(name) else '*'
            rows.append(f" {mark}{name:<12} {summary}")
        return rows

    def _help_summary(self, command: str) -> str:
        """Return the one-line description from a command's manual page."""
        page = self.man_pages.get(command)
        if not page:
            return command
        parts = page.strip().splitlines()
        if len(parts) < 2:
            return command
        line = parts[1].strip()
        return line.split(' - ', 1)[1] if ' - ' in line else line


# What went wrong, and the one thing to do about it. One entry per way a
# tour can go badly; the summary names whichever happened most.
FAILURES = {
    'wrong': (
        "{count} close out{s} named a condition the line did not have.",
        "The readings say what is on the pair, and 'report faults' says "
        "what each one adds up to.",
    ),
    'missed': (
        "{count} commitment{s} went past.",
        "Work the nearest commitment first. 'report next' picks it, and a "
        "trip by the wrong force costs three quarters of an hour.",
    ),
    'repeat': (
        "{count} report{s} came back after being closed.",
        "A faulty line closed as no trouble found does not fail loudly. It "
        "closes, and then the customer telephones again.",
    ),
}

# Added to the wrong-close advice only for a tour with a close nobody
# measured first. Said to somebody who measured every line, it is a lecture.
UNMEASURED_ADVICE = " Four minutes of mlt is worth it before every close."

# Eight levels for the index trend. console.render() turns these into ASCII
# on a terminal held to the period character set, which is most of them.
SPARK_LEVELS = '\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588'


# The measure step where mlt never names a crew (Craft), so he does not say
# that it does. Same step, same place in the loop.
FIRST_TOUR_MEASURE_UNNAMED = (
    'Read the bottom of that, and read it against what the customer',
    "told you. 'report faults' says what each reading adds up to.",
)


# What Halloran says, one message per step of the loop. Four messages and
# then he leaves you alone, which is the difference between a colleague and
# a tutorial.
FIRST_TOUR = {
    'open': (
        'First tour. There is one report on your board and I have kept the',
        'rest off it until that one is closed.',
        "Type 'report'. It tells you what to do next along the bottom.",
    ),
    'board': (
        'That is the board. One line to a report: who is out, what they',
        'say is wrong, and when we promised them.',
        'What they say is what they noticed, and it is not always what is',
        "on the pair. Ring them back first: 'report callback 1'.",
    ),
    'callback': (
        'Hear the difference? The card said one thing and the customer',
        'said another. The pair has the last word, so put a meter on it.',
        "'mlt 1', and read the numbers against both.",
    ),
    'measure': (
        'Read the bottom of that, and read it against what the customer',
        "told you. Where it names a crew, send them; 'report faults' says",
        'what each reading adds up to when it does not.',
    ),
    'dispatch': (
        'They will call in when they have been. Then close it out: code 5',
        'if they found trouble, code 8 if there was none, and name the',
        'fault the readings showed.',
    ),
    'closed': (
        'That is the job. The rest of the board is coming.',
        'Everything else on this machine is yours to poke at. Your annual',
        "refresher is due and you may as well sit it now: 'training unix'.",
        'I am on write if you need me.',
    ),
}
