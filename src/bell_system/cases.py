"""
Causes behind several reports: planning them, dealing their reports out
over a tour, and clearing them with one trip.

The desk holds the cases and owns the rules; it knows nothing of the
terminal. The terminal asks for a plan when a tour opens, and asks once the
shift clock has moved for whatever reports have come due.

A plan is made from the tour number alone, with a generator of its own, so
it takes nothing from the one the board is dealt from: which kind, how many
reports, and at which minute of the tour each one comes in.
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .cable import BINDERS_PER_UNIT, PAIRS_PER_BINDER
from .data.cases import CASE_KINDS, CaseKind

if TYPE_CHECKING:  # pragma: no cover - avoids an import cycle at runtime
    from .reports import ReportDesk, TroubleReport

# The tours the scripted case lands on. It is Marker 2 (docs/design/
# narrative-bible.md, T1): it fires on the first of these the career
# reaches, and on the second only if the first never had it.
MARKER_TOURS = (9, 10)

# From this tour on a tour may carry an ordinary case, and the share of
# tours that do. The simulation's own.
FIRST_CASE_TOUR = 4
CASE_SHARE = 0.35

# The career's ledger entry that says Marker 2 has been planted.
MARKER_LEDGER = 'case:marker2'


class Case:
    """One shared cause, and the reports it has thrown so far."""

    def __init__(self, ident: str, kind: str, where: str, due: List[int]):
        self.ident = ident
        self.kind = kind
        # What the members share, in the words of a "see also" line: the
        # line link frame such as 2-5, or a cable number.
        self.where = where
        # Shift minutes at which reports still to come arrive, soonest first.
        self.due = sorted(due)
        self.members: List[str] = []
        self.cleared = False
        # Whether the third report has been said out loud.
        self.opened = False

    @property
    def spec(self) -> CaseKind:
        """The kind this is."""
        return CASE_KINDS[self.kind]

    def place(self) -> str:
        """What its members share, as a see-also line says it."""
        return self.spec.place.format(where=self.where)

    def out(self) -> Dict[str, Any]:
        """Write the case for the save."""
        return {'ident': self.ident, 'kind': self.kind, 'where': self.where,
                'due': list(self.due), 'members': list(self.members),
                'cleared': self.cleared, 'opened': self.opened}

    @classmethod
    def read(cls, stored: Dict[str, Any]) -> 'Case':
        """Read a case back, or raise if it will not read."""
        if stored['kind'] not in CASE_KINDS:
            raise ValueError(f"no such case kind {stored['kind']!r}")
        case = cls(str(stored['ident']), stored['kind'],
                   str(stored['where']), [int(m) for m in stored['due']])
        case.members = [str(number) for number in stored['members']]
        case.cleared = bool(stored['cleared'])
        case.opened = bool(stored['opened'])
        return case


def plan(tour: int, seen: List[str]) -> Optional[Case]:
    """
    Decide what, if anything, this tour's trouble is standing behind.

    Args:
        tour: Which tour of the career is opening
        seen: The career's ledger of things said once

    Returns:
        A case with its reports still to come, or None
    """
    if tour in MARKER_TOURS and MARKER_LEDGER not in seen:
        kind = 'marker'
    elif (tour >= FIRST_CASE_TOUR
          and random.Random(f"case:{tour}").random() < CASE_SHARE):
        kind = 'dig'
    else:
        return None
    chance = random.Random(f"{kind}:{tour}")
    spec = CASE_KINDS[kind]
    count = chance.randint(*spec.members)
    due = [chance.randint(*spec.window) for _ in range(count)]
    if spec.shared == 'frame':
        where = f"{chance.randint(0, 3)}-{chance.randint(0, 7)}"
    else:
        where = f"{chance.randint(1, 88):04d}"
    return Case(f"CASE-{tour}-{kind}", kind, where, due)


def arrivals(desk: 'ReportDesk', shift_minutes: int, now: datetime,
             slack_minutes: int) -> List['TroubleReport']:
    """
    Deal whichever case reports the shift clock has reached.

    A board that is full holds them back and they come when there is room,
    so a case never pushes the board past the depth the desk carries.
    """
    dealt: List['TroubleReport'] = []
    for case in desk.cases:
        while case.due and case.due[0] <= shift_minutes and not desk.full():
            case.due.pop(0)
            dealt.append(_deal(desk, case, now, slack_minutes))
    return dealt


def _deal(desk: 'ReportDesk', case: Case, now: datetime,
          slack_minutes: int) -> 'TroubleReport':
    """
    Put the next of a case's reports on the board.

    The report is dealt as any other is and then made one of the case: its
    line is moved onto what the others share, so that the sharing is in the
    line records and not only in a list somebody keeps.
    """
    spec = case.spec
    report = desk.receive(now, slack_minutes, fault=spec.fault)
    record = report.record
    if spec.shared == 'frame':
        # The line link frame is the first two places of the equipment
        # number. Cable and pair stay as drawn, which is why the lines have
        # no cable in common (narrative-bible.md, T1).
        tail = record.line_equipment.split('-', 2)[2]
        record.line_equipment = f"{case.where}-{tail}"
    else:
        record.cable = int(case.where)
        chance = random.Random(f"{case.ident}:{len(case.members)}")
        taken = {desk.reports[number].record.pair for number in case.members
                 if number in desk.reports}
        record.pair = chance.randint(1, BINDERS_PER_UNIT * PAIRS_PER_BINDER)
        while (record.pair in taken
               or desk.plant.section_at(record.cable, record.pair)):
            record.pair = chance.randint(
                1, BINDERS_PER_UNIT * PAIRS_PER_BINDER)
    report.case = case.ident
    case.members.append(report.number)
    return report


def case_of(desk: 'ReportDesk', report: 'TroubleReport') -> Optional[Case]:
    """The case a report belongs to, if it belongs to one."""
    if report.case is None:
        return None
    for case in desk.cases:
        if case.ident == report.case:
            return case
    return None


def see_also(desk: 'ReportDesk', report: 'TroubleReport') -> List[str]:
    """
    What the attendant's screen shows about the rest of the run.

    Names the other open reports and what they share. Never what is wrong
    with any of them, whose crew would clear it or how to close it: that is
    for the measurement and the field to say.
    """
    case = case_of(desk, report)
    if case is None:
        return []
    others = [number for number in case.members
              if number != report.number and number in desk.reports
              and desk.reports[number].status != 'CLOSED']
    if not others:
        return []
    return [f"  See also            {', '.join(others)}",
            f"                      all on {case.place()}"]


def clear(desk: 'ReportDesk', report: 'TroubleReport', name_fault: bool
          ) -> List[str]:
    """
    A crew has cleared the cause behind a report. Clear the rest of the run.

    The other open reports are left as an earlier splice leaves a wet sheath's
    other pairs: repaired, needing only a close. Reports that had not yet
    arrived do not, because the cause is gone.

    Args:
        desk: The desk the report is on
        report: The report the right crew was sent on
        name_fault: Whether the crew says what it found

    Returns:
        What to add to the field's answer, or nothing if the report is not
        part of a case that was still standing
    """
    case = case_of(desk, report)
    if case is None or case.cleared:
        return []
    case.cleared = True
    case.due = []
    others = []
    for number in case.members:
        other = desk.reports.get(number)
        if other is None or other is report or other.status == 'CLOSED':
            continue
        other.field_finding = other.record.fault
        other.sheath_repaired = True
        other.clears_at = other.clears_after = None
        if other.status == 'PEND':
            other.status = 'TESTED'
        others.append(other.number)
    lines = []
    if name_fault:
        lines.append(case.spec.found)
    if others:
        lines.append(
            f"That was the cause of {len(others) + 1} reports. "
            f"{len(others)} other{'' if len(others) == 1 else 's'} on "
            f"{case.place()} can be closed without a further dispatch:")
        lines.append(f"  {', '.join(sorted(others))}")
    return lines
