"""
Putting a shift down and picking it back up.

A tour is a couple of hours of work. It used to be one process: closing
the window threw away the board, the weather, where every crew was
standing and how much of every commitment had been spent, and the next
session started from nothing with only the career record carried over.
That is the single most likely reason somebody plays once.

This writes the working shift beside the career record and reads it back.
The rules it follows are the ones any save file wants and most do not get:

  * Everything is written by hand, field by field, in the same style as
    :meth:`bell_system.progression.Career.save`. Nothing is pickled. A
    save file is a JSON object a person can read, and a person can tell
    from reading it what state their shift was in.
  * Anything unreadable, anything from a different version, and anything
    belonging to a different tour of the career is discarded rather than
    repaired. A shift is two hours; a corrupted resume that half works is
    worse than starting the tour again.
  * Loading never raises. The worst outcome is a fresh board.

What is deliberately *not* saved: the filesystem, the mail, the news
spool, and the message log. Those are either rebuilt identically at
construction or they are chatter, and a save file that carried them would
be ten times the size for nothing anybody would notice.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .cable import WetSection
from .field import Assignment, CREWS
from .reports import LineRecord, ReportDesk, TroubleReport

# Bumped whenever the shape below changes in a way that makes an older file
# wrong rather than merely incomplete. An unrecognised version is discarded,
# which costs somebody one tour and never leaves them with a board that is
# half of one shift and half of another.
VERSION = 1

SHIFT_FILENAME = 'shift.json'

# How a datetime is written. Seconds are enough: the simulation charges in
# minutes and nothing anywhere reads a microsecond.
STAMP = '%Y-%m-%dT%H:%M:%S'


def shift_path(state_directory: str) -> str:
    """Return the saved-shift path inside a state directory."""
    return os.path.join(state_directory, SHIFT_FILENAME)


def _stamp(moment: Optional[datetime]) -> Optional[str]:
    """Write a datetime, or nothing if there was not one."""
    return None if moment is None else moment.strftime(STAMP)


def _moment(text: Any) -> Optional[datetime]:
    """Read a datetime back, or nothing if it will not read."""
    if not isinstance(text, str):
        return None
    try:
        return datetime.strptime(text, STAMP)
    except ValueError:
        return None


# -- the line record ------------------------------------------------------

_RECORD_FIELDS = (
    'npa', 'nxx', 'line', 'name', 'address', 'cable', 'pair',
    'class_of_service', 'horizontal', 'vertical', 'line_equipment', 'clli',
    'fault', 'frame_defect', 'regular',
)


def _record_out(record: LineRecord) -> Dict[str, Any]:
    """Write a line record."""
    return {field: getattr(record, field) for field in _RECORD_FIELDS}


def _record_in(stored: Dict[str, Any]) -> LineRecord:
    """Read a line record back."""
    return LineRecord(**{field: stored[field] for field in _RECORD_FIELDS})


# -- the trouble report ---------------------------------------------------

# Everything on a report that is a plain value. The datetimes and the line
# record are handled either side of this.
_REPORT_FIELDS = (
    'number', 'symptom', 'repeat_of', 'status', 'minutes_spent',
    'desk_minutes', 'tested', 'test_notes', 'dispatched_to', 'field_finding',
    'crew', 'travel_minutes', 'sheath_repaired', 'disposition', 'found',
    'correct', 'missed_commitment',
)


def _report_out(report: TroubleReport) -> Dict[str, Any]:
    """Write one trouble report, everything on it included."""
    written = {field: getattr(report, field) for field in _REPORT_FIELDS}
    written['record'] = _record_out(report.record)
    written['received'] = _stamp(report.received)
    written['commitment'] = _stamp(report.commitment)
    written['closed_at'] = _stamp(report.closed_at)
    return written


def _report_in(stored: Dict[str, Any]) -> TroubleReport:
    """Read one trouble report back, or raise if it will not read."""
    received = _moment(stored['received'])
    commitment = _moment(stored['commitment'])
    if received is None or commitment is None:
        raise ValueError('report has no received or commitment time')
    report = TroubleReport(
        number=stored['number'],
        record=_record_in(stored['record']),
        symptom=stored['symptom'],
        received=received,
        commitment=commitment,
        repeat_of=stored['repeat_of'],
    )
    for field in _REPORT_FIELDS:
        if field not in ('number', 'symptom', 'repeat_of'):
            setattr(report, field, stored[field])
    report.test_notes = list(stored['test_notes'])
    report.closed_at = _moment(stored['closed_at'])
    return report


# -- the cable plant, the weather and the field force ---------------------


def _plant_out(desk: ReportDesk) -> List[Dict[str, Any]]:
    """Write where the water is, and which pairs it has taken."""
    return [{
        'cable': section.cable,
        'binder': section.binder,
        'capacity': section.capacity,
        'opened': _stamp(section.opened),
        'repaired_at': _stamp(section.repaired_at),
        'pairs': {str(pair): number
                  for pair, number in section.pairs.items()},
        'psi': section.psi,
    } for section in desk.plant.sections]


def _plant_in(desk: ReportDesk, stored: List[Dict[str, Any]]) -> None:
    """Read the wet sections back onto a fresh plant."""
    sections = []
    for entry in stored:
        opened = _moment(entry['opened'])
        if opened is None:
            raise ValueError('wet section has no opening time')
        section = WetSection(entry['cable'], entry['binder'],
                             entry['capacity'], opened)
        section.repaired_at = _moment(entry['repaired_at'])
        section.pairs = {int(pair): number
                         for pair, number in entry['pairs'].items()}
        section.psi = entry['psi']
        sections.append(section)
    desk.plant.sections = sections


def _force_out(desk: ReportDesk) -> Dict[str, Any]:
    """Write where every crew is standing and who is out on what."""
    return {
        'at': dict(desk.force.at),
        'out': {key: {'report': job.report, 'travel': job.travel,
                      'work': job.work, 'left': _stamp(job.left)}
                for key, job in desk.force.out.items()},
    }


def _force_in(desk: ReportDesk, stored: Dict[str, Any]) -> None:
    """Read the field force back."""
    crews = {crew.key: crew for crew in CREWS}
    desk.force.at = {key: where for key, where in stored['at'].items()
                     if key in crews}
    out = {}
    for key, job in stored['out'].items():
        left = _moment(job['left'])
        if key not in crews or left is None:
            continue
        out[key] = Assignment(crew=crews[key], report=job['report'],
                              travel=job['travel'], work=job['work'],
                              left=left)
    desk.force.out = out


# -- the whole shift ------------------------------------------------------


def capture(terminal: Any) -> Dict[str, Any]:
    """
    Take everything about a working shift that has to survive being closed.

    Args:
        terminal: The session to read

    Returns:
        A plain dictionary of primitives, ready for json.dump
    """
    desk = terminal.desk
    return {
        'version': VERSION,
        # The career this belongs to. A save from a different tour, or from
        # before a handoff, is not this shift and is thrown away.
        'shift': terminal.career.shift,
        'reports_closed': terminal.career.reports_closed,
        'role': terminal.role,
        'role_name': terminal.role_name,
        'clli': desk.clli,
        'board': {
            'reports': [_report_out(report)
                        for report in desk.reports.values()],
            'order': list(desk.order),
            'sequence': desk._sequence,
            'closed_count': desk.closed_count,
            'repeat_count': desk.repeat_count,
            'regulars': {key: _record_out(record)
                         for key, record in desk._regulars.items()},
        },
        'plant': _plant_out(desk),
        'weather': {
            'regime': desk.weather.regime,
            'key': desk.weather.key,
            'temperature': desk.weather.temperature,
            'minutes': desk.weather._minutes,
        },
        'force': _force_out(desk),
        'tour': {
            'shift_minutes': terminal.shift_minutes,
            'charged_total': terminal._charged_total,
            'fired_events': sorted(terminal._fired_events),
            'baseline': list(terminal._tour_baseline),
            'nudges': sorted(terminal._tour_nudges),
            'hint_situation': terminal._hint_situation,
            'hint_level': terminal._hint_level,
            'assigned_tickets': sorted(terminal._assigned_tickets),
        },
    }


def restore(terminal: Any, stored: Dict[str, Any]) -> bool:
    """
    Put a saved shift back onto a freshly constructed session.

    Returns False and changes nothing if the file does not belong to this
    session: a different version, a different tour of the career, or a
    different wire centre. A partially applied resume would be worse than
    no resume at all, so everything that can fail is read before anything
    is assigned.

    Args:
        terminal: The session to restore onto
        stored: What :func:`capture` wrote

    Returns:
        Whether the shift was picked back up
    """
    desk = terminal.desk
    if (stored.get('version') != VERSION
            or stored.get('shift') != terminal.career.shift
            or stored.get('reports_closed') != terminal.career.reports_closed
            or stored.get('clli') != desk.clli):
        return False

    try:
        board = stored['board']
        reports = [_report_in(entry) for entry in board['reports']]
        held = {report.number: report for report in reports}
        order = [number for number in board['order'] if number in held]
        regulars = {key: _record_in(entry)
                    for key, entry in board['regulars'].items()}
        tour = stored['tour']
        weather = stored['weather']
        _plant_in(desk, stored['plant'])
        _force_in(desk, stored['force'])
    except (KeyError, TypeError, ValueError):
        return False

    desk.reports = held
    desk.order = order
    desk._sequence = board['sequence']
    desk.closed_count = board['closed_count']
    desk.repeat_count = board['repeat_count']
    desk._regulars = regulars

    desk.weather.regime = weather['regime']
    desk.weather.key = weather['key']
    desk.weather.temperature = weather['temperature']
    desk.weather._minutes = weather['minutes']

    terminal.shift_minutes = tour['shift_minutes']
    terminal._charged_total = tour['charged_total']
    terminal._fired_events = set(tour['fired_events'])
    terminal._tour_baseline = tuple(tour['baseline'])
    terminal._tour_nudges = set(tour['nudges'])
    terminal._hint_situation = tour['hint_situation']
    terminal._hint_level = tour['hint_level']
    terminal._assigned_tickets = set(tour['assigned_tickets'])
    return True


def write(path: str, terminal: Any) -> None:
    """
    Write the shift, ignoring a filesystem that will not take it.

    Follows Career.save in swallowing OSError: somebody running this off a
    read-only mount should still get to play, and losing a resume is not
    worth an exception in the middle of a tour.
    """
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as handle:
            json.dump(capture(terminal), handle, indent=1, sort_keys=True)
            handle.write('\n')
    except OSError:
        return


def read(path: str) -> Optional[Dict[str, Any]]:
    """Read a saved shift, or nothing at all if it will not read."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as handle:
            stored = json.load(handle)
    except (OSError, ValueError):
        return None
    return stored if isinstance(stored, dict) else None


def discard(path: str) -> None:
    """Throw a saved shift away, at a handoff or when it will not load."""
    try:
        os.remove(path)
    except OSError:
        return
