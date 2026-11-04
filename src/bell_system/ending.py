"""
The last night, read off the career.

``data/epilogue.py`` holds the words. This gathers what they are chosen
by, from the saved career and the board as it stands at sign-off, and renders
the pieces on the channels the building already has. Reading only: nothing
here changes the career, and a career that is read twice ends the same way.
"""

from datetime import datetime
from typing import Any, Iterable, List, Optional

from . import plantjobs
from .data.companies import NOT_WHOLLY_OWNED, RBOCS, for_state
from .data.epilogue import Ring, Shape, halloran_note, pieces
from .npc import Message, render as render_message
from .reports import STATUS_CLOSED

# The arc beats and favours the ending listens for (npc.py ARC_BEATS and
# FAVOURS). Anything else in the ledger is not the ending's business.
_BEATS = ('alvarez.1', 'alvarez.2', 'reyes.1', 'reyes.2',
          'sandoval.1', 'sandoval.2', 'sandoval.3')
_FAVOUR_PREFIX = 'favour:'
_FAVOURED_PREFIX = 'favoured:'
_SHEATH_FORCE = 'cable repair'


def _ring(desk: Any) -> Optional[Ring]:
    """The report the bureau speaks of: the first one going over open."""
    pending = desk.customers()
    if pending:
        report = pending[0]
        return Ring(report.number, report.record.telephone_number,
                    report.commitment.strftime('%H:%M'), 'open')
    # closed() is newest first, so the last one closed is the first.
    closed = [held for held in desk.closed() if held.closed_at]
    if closed:
        report = closed[0]
        return Ring(report.number, report.record.telephone_number,
                    report.closed_at.strftime('%H:%M'), 'closed')
    return None


def _sheath_open(desk: Any) -> bool:
    """
    Whether the sheath side has work that is not done, as the board stands.

    That is a report the player sent the cable force to and has not closed,
    or a pressure-alarm job the board lists and nobody has cleared. It reads
    the dispatch the player made and the jobs the player can read on the
    board, never the cause of any report (pillar 1), and it reads them as
    they are at the end: a sheath that was spoken of and has been repaired
    is not open.
    """
    return (any(plantjobs.is_open(desk, job) for job in desk.jobs)
            or any((held.dispatched_to or '').lower() == _SHEATH_FORCE
                   for held in desk.customers()))


def _hour_kept(desk: Any, ledger: Iterable[str]) -> bool:
    """
    Whether the hour Reyes got was kept: the report it was given for was
    closed by the commitment as extended. A report that has left the desk,
    or is still open, did not keep it.
    """
    entries = list(ledger)
    if 'favour:mreyes' not in entries:
        return False
    after = entries[entries.index('favour:mreyes') + 1:]
    number = next((entry[len(_FAVOURED_PREFIX):] for entry in after
                   if entry.startswith(_FAVOURED_PREFIX)), '')
    held = desk.reports.get(number)
    return bool(held and held.status == STATUS_CLOSED and held.closed_at
                and held.closed_at <= held.commitment)


def shape_of(career: Any, desk: Any, verdict: str) -> Shape:
    """
    Gather what the ending reads.

    Args:
        career: The career being closed
        desk: The report desk, for the board it hands over
        verdict: The audit's verdict, which is decided before this
    """
    state = str(career.office.get('state', ''))
    company = for_state(state) if state else None
    ledger = career.beats_seen
    return Shape(
        verdict=verdict,
        closed=career.reports_closed,
        sheath_open=_sheath_open(desk),
        hour_kept=_hour_kept(desk, ledger),
        company=company.name if company else '',
        holding=(RBOCS.get(company.rboc, '')
                 if company and company.verified else ''),
        outside=NOT_WHOLLY_OWNED.get(state.upper(), '') if not company else '',
        heard=frozenset(beat for beat in _BEATS if beat in ledger),
        favours=frozenset(entry[len(_FAVOUR_PREFIX):] for entry in ledger
                          if entry.startswith(_FAVOUR_PREFIX)),
        finds=frozenset(career.finds),
        commendations=frozenset(career.commendations),
        ring=_ring(desk),
    )


def epilogue(shape: Shape, now: datetime, stamp: str,
             room: Any = None) -> List[str]:
    """
    Render the pieces of the epilogue, in the order they are said.

    Args:
        shape: What :func:`shape_of` returned
        now: The simulated moment they are said at
        stamp: The timestamp the channels carry
        room: The switchroom, which files each message in the log. A test
            of the words alone leaves it out.
    """
    rendered = []
    for channel, sender, lines in pieces(shape):
        message = Message(channel=channel, sender=sender, received=now,
                          lines=lines, kind='shift', subject='Last tour',
                          about=None)
        if room is not None:
            room.log.append(message)
        rendered.append(render_message(message, stamp))
    return rendered


def chief_note(shape: Shape) -> List[str]:
    """What the wire chief adds to his own last word."""
    return halloran_note(shape)
