"""
The last night, read off the career.

``data/epilogue.py`` holds the words. This gathers what they are chosen
by, from the saved career and the board as it stands at sign-off, and renders
the pieces on the channels the building already has. Reading only: nothing
here changes the career, and a career that is read twice ends the same way.
"""

from datetime import datetime
from typing import Any, List, Optional

from .data.companies import NOT_WHOLLY_OWNED, RBOCS, for_state
from .data.epilogue import Ring, Shape, halloran_note, pieces
from .npc import Message, render as render_message

# The arc beats and favours the ending listens for (npc.py ARC_BEATS and
# FAVOURS). Anything else in the ledger is not the ending's business.
_BEATS = ('alvarez.1', 'alvarez.2', 'reyes.1', 'reyes.2',
          'sandoval.1', 'sandoval.2', 'sandoval.3')
_FAVOUR_PREFIX = 'favour:'


def _ring(desk: Any) -> Optional[Ring]:
    """The report the bureau speaks of: the first one going over open."""
    pending = desk.customers()
    if pending:
        report = pending[0]
        return Ring(report.number, report.record.telephone_number,
                    report.commitment.strftime('%H:%M'), 'open')
    closed = [held for held in desk.closed() if held.closed_at]
    if closed:
        report = closed[-1]
        return Ring(report.number, report.record.telephone_number,
                    report.closed_at.strftime('%H:%M'), 'closed')
    return None


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
        open_count=len(desk.customers()),
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
