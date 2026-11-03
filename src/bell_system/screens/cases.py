"""
Where on the plant a crew is told to go, and the cases a board can hold.

A dispatch used to name a force and nothing else, and a splicer sent to
Cable repair opened the right sheath because the desk knew which one it was.
A person at the position would have said where. These are the parts of that
which are the player's to say: which cable and which binder group, in the
words the assignment record uses for them.
"""

import random
import re
from typing import List, Optional, Tuple

from ..cable import (
    BINDERS_PER_UNIT, PAIRS_PER_BINDER, binder_colour, binder_of,
)
from ..cases import MARKER_LEDGER, arrivals, case_of, plan
from ..npc import Message
from ..reports import TroubleReport
from .session import SessionState

# From this tour on a tour may open with a sheath already leaking, and the
# share of tours that do. The simulation's own: it is the water the board's
# own draws would otherwise start from nothing.
FIRST_LEAK_TOUR = 2
LEAK_SHARE = 0.5

# A section as the player writes it: the cable, a slash and the binder
# group, as in 81/8. Not the cable and pair the report carries, which is
# 0081/0181 and would be the answer to be copied.
_SECTION = re.compile(r'^(\d{1,4})/(\d{1,2})$')


class CaseCommands(SessionState):
    """Naming a section for a crew, and the shared causes behind reports."""

    def _named_section(self, words: str
                       ) -> Tuple[str, Optional[Tuple[int, int]], str]:
        """
        Split a cable and binder group off the end of a dispatch.

        Args:
            words: What followed the report number: a force, and perhaps a
                section after it

        Returns:
            The force's words, the section if one was named, and a refusal
            if what looked like a section is not one
        """
        parts: List[str] = words.split()
        if not parts or '/' not in parts[-1]:
            return words, None, ''
        token = parts.pop()
        found = _SECTION.match(token)
        if found is None:
            return ' '.join(parts), None, (
                f"report: '{token}' is not a cable and binder group.\n"
                f"Write it cable/binder, as in 81/8.")
        cable, binder = int(found.group(1)), int(found.group(2))
        if not 1 <= cable <= self.desk.plant.cable_count:
            return ' '.join(parts), None, (
                f"report: this wire centre has cables 1 to "
                f"{self.desk.plant.cable_count}. There is no cable {cable}.")
        if not 1 <= binder <= BINDERS_PER_UNIT:
            return ' '.join(parts), None, (
                f"report: binder groups run 1 to {BINDERS_PER_UNIT}, in "
                f"twenty-fives of pairs. There is no group {binder}.")
        return ' '.join(parts), (cable, binder), ''

    def _section_asked(self, force: str,
                       section: Optional[Tuple[int, int]]) -> str:
        """
        Refuse a splicer's dispatch that does not say where to go.

        Asked of every Cable repair dispatch, whatever the report is, so the
        question carries no information about it. Nothing is charged.
        """
        if force != 'Cable repair' and section is not None:
            # Said of any force and any report alike, so that it does not
            # tell whether the force was the right one.
            return ("report: only Cable repair takes a cable and binder "
                    "group.\n"
                    "  report dispatch <number> <force>")
        if (force != 'Cable repair' or section is not None
                or not self._difficulty().section_required):
            return ''
        return ("The splicers will not open a sheath on a guess. Which one?\n"
                "  report dispatch <number> cable <cable>/<binder>\n"
                f"A binder group is {PAIRS_PER_BINDER} pairs, counted from "
                "1. 'man cable' has the colour code.")

    def cmd_cable(self, args: Optional[List[str]] = None) -> str:
        """
        The binder groups of a 600-pair cable, or the one a pair is in.

        Read-only. The colour code is what a splicer is told to find, and
        working out which group a pair is in is the part that is yours.
        """
        args = args or []
        if args:
            if not args[0].isdigit() or not (
                    1 <= int(args[0]) <= BINDERS_PER_UNIT * PAIRS_PER_BINDER):
                return (f"cable: '{args[0]}' is not a pair. Pairs run 1 to "
                        f"{BINDERS_PER_UNIT * PAIRS_PER_BINDER}.")
            binder = binder_of(int(args[0]))
            return (f"Pair {args[0]} is in binder group {binder} "
                    f"({binder_colour(binder)}).")
        rows = ["BINDER GROUPS", '=' * 46,
                f"{'GROUP':<7}{'PAIRS':<12}COLOUR"]
        for binder in range(1, BINDERS_PER_UNIT + 1):
            rows.append(f"{binder:<7}"
                        f"{(binder - 1) * PAIRS_PER_BINDER + 1}-"
                        f"{binder * PAIRS_PER_BINDER}".ljust(19)
                        + binder_colour(binder))
        rows.extend(['', "cable <pair> says which group a pair is in. "
                         "report dispatch <number> cable <cable>/<group>."])
        return '\n'.join(rows)

    def _plant_case(self) -> None:
        """
        Decide whether this tour's trouble has a cause standing behind it.

        Asked when a tour opens, after the board is dealt. The plan is the
        tour's alone, so the board is dealt the same whether there is one
        or not; only what arrives later is the case's.
        """
        self._plant_leak()
        case = plan(self.career.shift, self.career.beats_seen)
        # A cause a tour left behind is still a cause while any report of
        # it is open: one right trip clears the run on the next tour as it
        # did on the one it began. It throws no more reports of its own,
        # because the minutes it was due at were that tour's.
        carried = []
        for old in self.desk.cases:
            if any(self.desk.reports[number].status != 'CLOSED'
                   for number in old.members if number in self.desk.reports):
                old.due = []
                carried.append(old)
        self.desk.cases = carried + ([case] if case else [])

    def _plant_leak(self) -> None:
        """
        Start the tour's leak, if it has one: water in a sheath nobody has
        reported, which the contactor will alarm on before a customer does.
        """
        tour = self.career.shift
        if tour < FIRST_LEAK_TOUR or random.Random(
                f"leak:{tour}").random() >= LEAK_SHARE:
            return
        self.desk.plant.begin_leak(
            self.clock.now(), random.Random(f"leak-site:{tour}"))

    def _case_events(self) -> List[Message]:
        """
        Let whatever reports a cause has thrown by now come onto the board.

        Each comes in as any assignment does, for the caller to show or
        hold. When the third has come in,
        whoever is nearest the cause says what they can see, once.
        """
        pieces: List[Message] = self._fraud_events()
        if not self.desk.cases or self.first_tour():
            return pieces
        now = self.clock.now()
        slack = self._difficulty().commitment_slack_minutes
        for report in arrivals(self.desk, self.shift_minutes, now, slack):
            pieces.append(self.switchroom.assignment(
                now, report.number, report.record.telephone_number,
                report.symptom, report.commitment.strftime('%H:%M')))
            case = case_of(self.desk, report)
            # Kept once the first of it has come, and not when it was
            # planned: a shift resumed from a save that has no cases would
            # otherwise have used up the one it never saw.
            if (case and case.kind == 'marker'
                    and MARKER_LEDGER not in self.career.beats_seen):
                self.career.beats_seen.append(MARKER_LEDGER)
                self.career.save()
            if case and not case.opened and len(case.members) >= 3:
                case.opened = True
                note = self.switchroom.case_note(now, case.spec, report.number)
                if note:
                    pieces.append(note)
        return pieces

    def _case_cleared(self, report: TroubleReport) -> None:
        """Say once that the cause behind a report has been cleared."""
        case = case_of(self.desk, report)
        key = f'cleared:{case.ident}' if case else ''
        if not case or not case.cleared or key in self.career.beats_seen:
            return
        self.career.beats_seen.append(key)
        note = self.switchroom.case_note(
            self.clock.now(), case.spec, report.number, closing=True)
        if note:
            self._queue_message(note, after=2)

    def _is_own_section(self, report: TroubleReport,
                        section: Optional[Tuple[int, int]]) -> bool:
        """Whether a dispatch's section is the one the report's pair is in."""
        return (section is None
                or section == (report.record.cable,
                               binder_of(report.record.pair)))
