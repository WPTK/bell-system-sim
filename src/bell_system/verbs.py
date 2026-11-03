"""
What each sign-off lets you do to the board.

A sign-off used to open screens. It opened more reading, and a craftsperson
who held all six had the same board and the same four ways to work it as one
who held none. These are the five verbs that change that, one per sign-off
after Loop and Station. Each does something the dispatch would otherwise do
with a truck, or does something no truck can:

    frame   cosmos fix        a jumper or protector fault, cleared at the frame
    office  switch clear      a false cross or ground, cleared from the switch
    scc     connect pool      a crew from the control centre when yours are out
    trunk   trunk trace       the bad trunk behind a call that will not complete
    toll    toll control      calls held off a congested route, until removed

The first, second and fourth are the three answers to one customer sentence,
"my calls do not complete", which the loop test cannot tell apart: a frame
fault, a false cross or ground in the office, and a trunk that is merely
busy. Each verb finds its own and says nothing useful about the others.

The functions here change the report or the desk and return what they found.
The screens that call them say it in their own voices, and decide who may.
Whether the craftsperson holds the sign-off is not decided here: the command
each hangs from is gated by the sign-off already, which is what refuses it.
"""

from typing import Dict, Optional, Tuple

from .data.trouble import FRAME_DEFECTS, FrameDefect
from .field import POOL_CREW
from .types import TrunkGroup
from .reports import (
    COST_FRAME_FIX,
    COST_FRAME_LOOKUP,
    COST_OFFICE_CLEAR,
    COST_TRUNK_TRACE,
    CONTROLS,
    STATUS_CLOSED,
    STATUS_DISPATCHED,
    ReportDesk,
    TroubleReport,
)


def open_report(desk: ReportDesk,
                token: str) -> Tuple[Optional[TroubleReport], str]:
    """
    Find the report a verb is aimed at.

    Returns:
        The report and an empty string, or None and why not
    """
    report = desk.find(token)
    if report is None:
        return None, f"no report matching '{token}'"
    if report.status == STATUS_CLOSED:
        return None, f"{report.number} is already closed."
    return report, ''


# What mlt writes after the time on a report's notes. The measurement a
# practical certifies is the one note that has it.
MLT_TAG = ' MLT: '


def measured(report: TroubleReport) -> bool:
    """Whether mlt has read this report's loop."""
    return any(MLT_TAG in note for note in report.test_notes)


def already_done(report: TroubleReport, kind: str) -> bool:
    """
    Whether this verb has already been worked on this report.

    ``kind`` is the prefix the verb writes on the report's notes, 'office' or
    'trunk'. A second go would charge the time again, write a second note and,
    for a trace, move another group's quality, so the screens turn it away
    before it costs anything.
    """
    return any(note.startswith(f"{kind}:") for note in report.test_notes)


def _cleared(report: TroubleReport, note: str, minutes: int) -> None:
    """
    Record that the desk cleared this report's fault itself.

    The state a dispatch leaves a report in, without the crew: the finding
    is the fault, so report next calls it ready to close, and the work is
    on the report as a measurement, so a close is not refused as untested.
    """
    report.spend(minutes)
    report.tested = True
    report.test_notes.append(note)
    report.status = STATUS_DISPATCHED
    report.field_finding = report.record.fault


def fix_frame(report: TroubleReport) -> Optional[FrameDefect]:
    """
    Take the frame defect off a line, if it has one.

    cosmos jumper reads the record and costs a look. This is the other half:
    take the jumper down and run it right, or put the protector back. The
    defect is gone from the record afterwards, so a second look says so.
    """
    record = report.record
    defect = FRAME_DEFECTS.get(record.frame_defect or '')
    if defect is None:
        report.spend(COST_FRAME_LOOKUP)
        return None
    _cleared(report, f"frame: {defect.name.lower()}, cleared", COST_FRAME_FIX)
    record.frame_defect = None
    return defect


def clear_office(report: TroubleReport) -> bool:
    """
    Busy out and move a line that has a false cross or ground.

    The trouble is in the line equipment, so the line is moved to a spare
    appearance from the switch and the loop is not touched. A line with
    nothing wrong in the office costs the look.
    """
    if report.record.fault != 'FCG':
        report.spend(COST_FRAME_LOOKUP)
        return False
    _cleared(report,
             f"office: false cross or ground on LEN "
             f"{report.record.line_equipment}, line moved",
             COST_OFFICE_CLEAR)
    return True


def trace_trunk(report: TroubleReport,
                groups: Dict[str, TrunkGroup]) -> Optional[str]:
    """
    Test the trunks a customer's calls take, and certify the bad one.

    A caller whose calls will not complete and whose line measures good
    is, often enough, a caller who has reached a trunk that is not. Only a
    no-trouble report with that complaint has one to find; any other
    report's trunks test clean, and that is the answer.

    Returns:
        The trunk group that was tested and certified, or None
    """
    candidates = [name for name, group in groups.items()
                  if group['status'] == 'ACTIVE']
    traced = (report.record.fault == 'NONE'
              and 'complete' in report.symptom.lower()
              and candidates)
    if not traced:
        report.spend(COST_FRAME_LOOKUP)
        return None
    worst = min(candidates, key=lambda name: groups[name]['quality'])
    groups[worst]['quality'] = min(0.999, groups[worst]['quality'] + 0.004)
    _cleared(report, f"trunk: bad member found in {worst}, certified",
             COST_TRUNK_TRACE)
    return worst


def hold_calls(desk: ReportDesk, name: str) -> Optional[str]:
    """
    Put a network management control on, or take it off.

    Args:
        name: One of CONTROLS, or 'off'

    Returns:
        The control that was on before this, if any
    """
    before = desk.control
    desk.control = name if name in CONTROLS else None
    return before


def control_standing(desk: ReportDesk) -> str:
    """One line saying a control is on, or nothing. A control left on costs."""
    if not desk.control:
        return ''
    return (f"Toll control on: {desk.control}. It stays until "
            f"'toll control off'.")


def borrow_crew(desk: ReportDesk, force: str) -> bool:
    """Ask the control centre for its pool crew, for one category."""
    return desk.force.borrow(force)


# The pool crew's name, for the screens that mention it.
POOL_NAME = POOL_CREW.name
