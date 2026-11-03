"""
The practical a sign-off waits on.

Past the count of correct closures Halloran offers a sign-off and holds it. 'qual
take <key>' stages one report on the live board that needs what the sign-off is
for, 'qual submit' hands it in, and he signs or says what was missed. The
count is the same in fun and in craft: what the difficulty changes is how much
the board forgives, not whether you can do the job.

The scenarios are in data/practicals.py. This is the driver.
"""

from datetime import timedelta
from typing import List, Optional, Tuple

from ..clock import days_to_divestiture
from ..console import wrap
from ..data.practicals import PRACTICALS, Practical, Scene
from ..npc import render as render_message
from ..progression import QUALIFICATIONS_BY_KEY
from ..reports import TroubleReport
from .session import SessionState

# A staged report is never late. Nothing about it is the customer's.
NEVER_DUE = timedelta(days=30)

# Halloran speaks to the width of the craft record.
BRIEF_WIDTH = 64


class PracticalCommands(SessionState):
    """
    Practicals for the sign-offs after Loop.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _practical_open(self) -> Optional[Tuple[Practical, TroubleReport]]:
        """The practical on the board, and the report it staged."""
        for report in self.desk.pending():
            if report.practical in PRACTICALS:
                return PRACTICALS[report.practical or ''], report
        return None

    def _practical_key(self) -> Optional[str]:
        """The sign-off whose practical is on the board, if one is."""
        staged = self._practical_open()
        return staged[0].key if staged else None

    def _may_use(self, command: str) -> bool:
        """
        Whether a command is open to the operator right now.

        Signed off, or the tool of a sign-off whose practical is on the
        board: Halloran lends it for as long as the report is there.
        """
        if self.career.may_use(command):
            return True
        needed = self.career.qualification_for_command(command)
        return needed is not None and needed == self._practical_key()

    def _scene(self, report: TroubleReport) -> Scene:
        """What a practical looks at and moves."""
        return Scene(self.desk, report, self.trunk_groups,
                     self.shift_minutes, self._practical_memory)

    def _fill(self, lines: Tuple[str, ...], report: TroubleReport,
              extra: str = '') -> List[str]:
        """Put the report's own numbers into what he says."""
        return [line.format(number=report.number,
                            tn=report.record.telephone_number, extra=extra)
                for line in lines]

    def _practical_hints(self) -> List[Tuple[str, List[str]]]:
        """The nudges for the practical on the board, smallest first."""
        staged = self._practical_open()
        if staged is None:
            return []
        practical, report = staged
        return [('ehalloran', self._fill(level, report))
                for level in practical.hints]

    def _qual_practical(self, args: List[str]) -> str:
        """Take a practical, or hand one in."""
        if args[0].lower() == 'submit':
            return self._practical_submit()
        return self._practical_take(args[1:])

    def _practical_take(self, args: List[str]) -> str:
        """Stage the practical for a sign-off whose count has been met."""
        offered = {q.key: q for q in self.career.offer_available()}
        staged = self._practical_open()
        if not args:
            ready = ', '.join(offered) or 'none yet'
            return (f"qual: usage: qual take <sign-off>\n"
                    f"Ready for a practical: {ready}.")
        key = args[0].lower()
        if key not in PRACTICALS:
            return (f"qual: no practical for '{args[0]}'.\n"
                    f"Sign-offs with one: {', '.join(PRACTICALS)}.")
        qualification = QUALIFICATIONS_BY_KEY[key]
        if self.career.is_qualified(key):
            return f"qual: you are already signed off on {qualification.name}."
        if key not in offered:
            short = (qualification.requires_reports
                     * self._difficulty().reports_per_qualification
                     - self.career.reports_correct)
            return (f"qual: not yet. {qualification.name} is offered at "
                    f"{short} more correct closure"
                    f"{'' if short == 1 else 's'}.")
        if staged is not None and staged[0].key == key:
            said = self._practical_memory.get(self._said(staged[1]), '')
            return self._brief(*staged, extra=said, again=True)
        if staged is not None:
            return (f"qual: you have {staged[0].title} on the board "
                    f"({staged[1].number}). Hand it in with 'qual submit' "
                    f"first.")
        practical = PRACTICALS[key]
        refusal = practical.blocked(self.trunk_groups)
        if refusal:
            return f"Practical: {practical.title}\n\n{refusal}"
        report = self.desk.receive(self.clock.now(), fault=practical.fault)
        report.practical = key
        report.commitment = report.received + NEVER_DUE
        if practical.symptom:
            report.symptom = practical.symptom
        extra = practical.stage(self._scene(report))
        self._practical_memory[self._said(report)] = extra
        # The hints are about this report now, from the top.
        self._hint_situation = ''
        self._hint_level = 0
        self._sync_report_files()
        return self._brief(practical, report, extra=extra)

    @staticmethod
    def _said(report: TroubleReport) -> str:
        """Where the sentence the stage added to the brief is kept."""
        return f"said {report.number}"

    def _brief(self, practical: Practical, report: TroubleReport,
               extra: str = '', again: bool = False) -> str:
        """What Halloran says when he sets one up."""
        lines = [f"Practical: {practical.title}", '=' * 50]
        for line in self._fill(practical.brief, report, extra):
            lines.append(line)
        lines.extend([
            '',
            f"{report.number} is on your board. You have the tools of the "
            f"sign-off for as long as it is there.",
            "'hint' is free while it is. 'qual submit' when you are done.",
        ])
        if again:
            lines.insert(0, "Still on your board:")
        return '\n'.join(lines)

    def _practical_submit(self) -> str:
        """Hand the practical in. He looks, and signs or says what was missed."""
        staged = self._practical_open()
        if staged is None:
            return ("qual: no practical on your board. "
                    "'qual take <sign-off>' sets one up.")
        practical, report = staged
        scene = self._scene(report)
        missed = practical.check(scene)
        self._end_practical(practical, report)
        if missed:
            lines = [f"Practical: {practical.title} - not signed.", '']
            for sentence in missed:
                lines.extend(wrap(sentence, BRIEF_WIDTH))
            lines.extend(['', f"'qual take {practical.key}' sets it up "
                              f"again. 'hint' is free."])
            return '\n'.join(lines)
        qualification = self.career.pass_practical(practical.key)
        if qualification is None:
            # Worked, and already signed (a role the game was started with
            # carries sign-offs). Nothing to grant, so nothing to announce.
            return (f"Practical: {practical.title}\n\n"
                    f"Worked, but you are already signed off on it.")
        message = self.switchroom.qualification_notice(
            self.clock.now(), qualification.name, qualification.unlocks,
            held=len(self.career.qualifications),
            days_left=days_to_divestiture(self.clock.now()))
        return '\n'.join([f"Practical: {practical.title} - passed.", '',
                          render_message(message, self._stamp())])

    def _end_practical(self, practical: Practical,
                       report: TroubleReport) -> None:
        """Take the staged report off the board and put the board back."""
        practical.strike(self._scene(report))
        self._practical_memory.pop(self._said(report), None)
        self.desk.discard(report)
        self._hint_situation = ''
        self._hint_level = 0
        self._sync_report_files()

    def _abandon_practical(self) -> None:
        """A handoff ends a practical that was never handed in."""
        staged = self._practical_open()
        if staged is not None:
            self._end_practical(*staged)

    def _offer_qualifications(self) -> List[str]:
        """
        Say once that a sign-off is there to be taken.

        The count is the floor and not the sign-off. The notice goes out when
        the count is first met, from the man who signs, and says what the
        next step is. Once is once for the career: the record carries it, so
        a new session does not send it again.
        """
        notices: List[str] = []
        for qualification in self.career.offer_available():
            if qualification.key in self.career.offered:
                continue
            self.career.offered.append(qualification.key)
            self.career.save()
            message = self.switchroom.practical_offer(
                self.clock.now(), qualification.name, qualification.key)
            notices.append(render_message(message, self._stamp()))
        return notices
