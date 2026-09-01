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

from ..data.positions import POSITION_COMMANDS
from ..npc import render as render_message
from ..progression import QUALIFICATIONS_BY_KEY
from .session import SessionState


class NextAction(NamedTuple):
    """One thing worth doing, and the command that does it."""

    # One line, in the second person, saying what is worth doing.
    reason: str
    # What to type. Empty when there is genuinely nothing pressing.
    command: str
    # Which step of the loop this is, for the first-tour walkthrough.
    step: str


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
        pending = self.desk.pending()
        if not pending:
            return self._nothing_pending()

        # The field has been and gone. Closing it costs two minutes and
        # leaving it costs the customer the rest of the day.
        done = [report for report in pending
                if report.field_finding or report.sheath_repaired]
        if done:
            report = done[0]
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
            return NextAction(
                f"{report.number} is past its commitment. It has been "
                f"measured; somebody needs to go.",
                f"report show {report.number}", 'dispatch')

        untested = [report for report in pending if not report.tested]
        if untested:
            report = untested[0]
            return NextAction(
                f"{report.number} has not been measured. "
                f"{report.age_label()} on the commitment.",
                f"mlt {report.number}", 'measure')

        # Everything measured, nothing overdue: send somebody to the one
        # that runs out first.
        report = pending[0]
        if not report.dispatched_to:
            fault = report.record.fault
            force = self._dispatch_for(fault)
            return NextAction(
                f"{report.number} is measured and waiting on a crew. "
                f"{report.age_label()} left.",
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
        from ..data.trouble import FAULTS
        where = FAULTS[fault].dispatch
        return '' if where.startswith('None') else where

    def _nothing_pending(self) -> NextAction:
        """What is worth doing with a clear board."""
        if self.career.shift == 1 and self.career.reports_closed == 0:
            return NextAction(
                "Nothing on the board yet. The bureau will send something.",
                'report', 'wait')
        ready = self._next_qualification()
        if ready is not None:
            return NextAction(
                f"Board clear. You are {ready} from your next sign-off.",
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
                return 'one correct closure'
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
        rows.append("   report close. mlt tells you what the fault is and "
                    "who to send.")
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
        self._tour_nudges.add(step)
        message = self.switchroom.chief_nudge(self.clock.now(),
                                             list(lines))
        return render_message(message, self._stamp())

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
    )

    SHELL_COMMANDS = (
        ('cd', 'Change directory'),
        ('ls', 'List a directory (-l for the long form)'),
        ('cat', 'Read a file'),
        ('grep', 'Search a file for a pattern'),
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
            if needed and not self.career.is_qualified(needed):
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

        lines.extend(['', 'THE MACHINE', '-' * 66])
        lines.extend(self._help_rows(self.SHELL_COMMANDS))
        lines.append("   Commands join with a pipe: who | wc -l")
        lines.append("   Worth reading: /etc/motd, /usr/doc/divestiture,")
        lines.append("                  /usr/users/sysop/notes, /usr/lmos/board")

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
                     if not self.career.may_use(name))
        if locked:
            lines.append(f"* marks a command you are not signed off on "
                         f"({locked} of them). Type 'qual'.")
        return '\n'.join(lines)

    def _help_rows(self,
                   entries: Iterable[Tuple[str, str]]) -> List[str]:
        """Render command rows, marking anything not signed off."""
        rows = []
        for name, summary in entries:
            mark = ' ' if self.career.may_use(name) else '*'
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
        "Measure it before you send anybody. 'mlt 1'.",
    ),
    'measure': (
        'Read the bottom of that. TEST RESULT tells you what the fault is',
        'and which crew it wants. It is not a riddle - it says it outright.',
        'Send whoever it names.',
    ),
    'dispatch': (
        'They will call in when they have been. Then close it out: code 5',
        'if they found trouble, code 8 if there was none, and name the',
        'fault the measurement gave you.',
    ),
    'closed': (
        'That is the job. The rest of the board is coming.',
        'Everything else on this machine is yours to poke at - try',
        "'help', or 'ls /usr/doc'. I am on write if you need me.",
    ),
}
