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

What is deliberately *not* saved in the shift file: the filesystem, the
mail, the news spool, and the message log. Those are either rebuilt
identically at construction or they are chatter, and a save file that
carried them would be ten times the size for nothing anybody would notice.

The one part of the filesystem that is kept is what the player wrote, in a
file of its own, ``home.json``. It is not the shift's: the shift file is
thrown away at every handoff, and a note written on tour 2 is still there on
tour 9. It holds only the difference from the shipped tree, under the home
directories and the moo scoreboard, in a file of up to 64 KB. A home that does
not load whole is set aside as ``home.json.bad`` and never written over, and
every file here is written to a scratch name and moved into place, so a crash
mid-write leaves the old file and not a short one.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .cable import WetSection
from .data.practicals import PRACTICALS
from .field import Assignment, CREWS, POOL_CREW
from .filesystem import (
    PLAYER_LIMIT,
    Node,
    is_player_path,
    normalise,
    player_changes,
)
from .jsonfile import read_json, write_text_atomically
from .reports import (
    CONTROLS, STATUS_CLOSED, LineRecord, ReportDesk, TroubleReport,
)

# Bumped whenever the shape below changes in a way that makes an older file
# wrong rather than merely incomplete. An unrecognised version is discarded,
# which costs somebody one tour and never leaves them with a board that is
# half of one shift and half of another.
VERSION = 1

SHIFT_FILENAME = 'shift.json'
HOME_FILENAME = 'home.json'

# Bumped, like VERSION, when an older home file would be wrong rather than
# merely incomplete. An unrecognised version is ignored.
HOME_VERSION = 1

# How a datetime is written. Seconds are enough: the simulation charges in
# minutes and nothing anywhere reads a microsecond.
STAMP = '%Y-%m-%dT%H:%M:%S'


def shift_path(state_directory: str) -> str:
    """Return the saved-shift path inside a state directory."""
    return os.path.join(state_directory, SHIFT_FILENAME)


def home_path(state_directory: str) -> str:
    """Return the saved-files path inside a state directory."""
    return os.path.join(state_directory, HOME_FILENAME)


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
    written['desk_booked'] = report.desk_booked
    written['practical'] = report.practical
    written['sighting'] = report.sighting
    written['frame_looked_up'] = report.frame_looked_up
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
    # Written since reports began ageing on the shift clock. A shift saved
    # before that has been aged by exactly the desk time it charged.
    report.desk_booked = stored.get('desk_booked', report.desk_minutes)
    # Written since practicals; a report from before one is an ordinary one.
    # A name this version has no practical for would be a report that can be
    # neither closed (it is Halloran's) nor handed in (nobody knows it), so
    # it is read as an ordinary report instead.
    practical = stored.get('practical')
    report.practical = (practical if isinstance(practical, str)
                        and practical in PRACTICALS else None)
    # Written since the reading ramp counted sightings of a fault type.
    report.sighting = stored.get('sighting')
    # Written since help learned to send a clean reading to the frame.
    report.frame_looked_up = stored.get('frame_looked_up', False)
    # Nor were overdue reports flagged while they were open. Left alone,
    # the first age() after loading would find every one of them late at
    # once and answer with a burst of misses and escalations for lateness
    # the old shift already had, so those are marked as known.
    if 'desk_booked' not in stored and report.status != STATUS_CLOSED:
        report.missed_commitment = (report.missed_commitment
                                    or report.overdue())
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
        'loaned': desk.force.loaned,
        'out': {key: {'report': job.report, 'travel': job.travel,
                      'work': job.work, 'left': job.left}
                for key, job in desk.force.out.items()},
    }


def _force_in(desk: ReportDesk, stored: Dict[str, Any]) -> None:
    """Read the field force back."""
    crews = {crew.key: crew for crew in (*CREWS, POOL_CREW)}
    loaned = stored.get('loaned')
    desk.force.loaned = loaned if isinstance(loaned, str) else None
    desk.force.at = {key: where for key, where in stored['at'].items()
                     if key in crews}
    if desk.force.loaned:
        desk.force.at.setdefault(POOL_CREW.key, 'FAR')
    out = {}
    for key, job in stored['out'].items():
        left = job['left']
        # A shift saved before the crews ran on the shift clock wrote the
        # time they rolled as a wall-clock stamp. That is not a point on this
        # clock, and the crew is taken to be back; the report they were out
        # on was charged for the trip when they rolled.
        if key not in crews or not isinstance(left, int):
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
            'control': desk.control,
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
            'tour_desk_start': terminal._tour_desk_start,
            'board_reviewed': terminal._board_reviewed,
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
        # Absent from a shift saved before there were controls, and not a
        # control the desk knows is as good as none. Anything that is not a
        # string is not one, and is not allowed to raise below.
        control = board.get('control')
        control = (control if isinstance(control, str)
                   and control in CONTROLS else None)
        _plant_in(desk, stored['plant'])
        _force_in(desk, stored['force'])
    except (KeyError, TypeError, ValueError):
        return False

    desk.reports = held
    desk.order = order
    desk._sequence = board['sequence']
    desk.closed_count = board['closed_count']
    desk.repeat_count = board['repeat_count']
    desk.control = control
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
    # Newer than the first saves. Without them the tour is taken to have
    # been worked, which is the kinder way to be wrong about a resumed shift.
    terminal._tour_desk_start = tour.get('tour_desk_start', 0)
    terminal._board_reviewed = tour.get('board_reviewed', True)
    return True


# -- what the player wrote ------------------------------------------------


def home_record(tree: Dict[str, Node]) -> Dict[str, Any]:
    """Take the player's files from a filesystem: what differs from the shipped one."""
    changed, removed = player_changes(tree)
    return {
        'version': HOME_VERSION,
        'nodes': {path: {'kind': node.kind, 'owner': node.owner,
                         'group': node.group, 'mode': node.mode,
                         'content': node.content if not node.is_dir else None}
                  for path, node in sorted(changed.items())},
        'removed': removed,
    }


def home_text(tree: Dict[str, Node]) -> str:
    """Return what would be written to home.json for this filesystem."""
    return json.dumps(home_record(tree), indent=1, sort_keys=True) + '\n'


def home_size(tree: Dict[str, Node]) -> int:
    """
    Return how big the player's saved files are, as the file they are kept in.

    The limit is on this and nothing narrower - not the text of the files
    alone - because the file is what grows: names, directories and
    permissions all take room in it. Every route that adds to a home (echo,
    mv, cc -o, mkdir) is held to the one measure by asking it.
    """
    return len(home_text(tree).encode('utf-8'))


def _home_node(path: Any, entry: Any) -> Optional[Node]:
    """Read one saved node, or nothing if it is not one this version keeps."""
    if (not isinstance(path, str) or not is_player_path(path)
            or normalise(path, '/') != path or not isinstance(entry, dict)):
        return None
    kind = entry.get('kind')
    text = entry.get('content')
    if kind not in ('dir', 'file') or (kind == 'file' and
                                       not isinstance(text, str)):
        return None
    owner, group, mode = (entry.get(name) for name in ('owner', 'group', 'mode'))
    if not (isinstance(owner, str) and isinstance(group, str)
            and isinstance(mode, str)):
        return None
    return Node(kind, owner, group, mode, text if kind == 'file' else None)


def restore_home(terminal: Any, stored: Any) -> Optional[int]:
    """
    Put the player's files back onto a freshly built filesystem.

    Entry by entry: a node that is damaged, outside the saved paths, not
    spelled the way the shell spells it, or whose directory is not there is
    left out, and the rest are kept. Anything outside the saved paths is
    refused however it got into the file, so that a hand-edited home.json
    is not a way to rewrite /bin.

    Returns:
        How many entries were left out, or None if the record as a whole
        is not one to apply (not this version's, not shaped like a record,
        or larger than a home may be)
    """
    if (not isinstance(stored, dict) or stored.get('version') != HOME_VERSION
            or not isinstance(stored.get('nodes'), dict)
            or not isinstance(stored.get('removed'), list)):
        return None
    left_out = 0
    nodes = {}
    for path, entry in stored['nodes'].items():
        node = _home_node(path, entry)
        if node is None:
            left_out += 1
        else:
            nodes[path] = node
    removed = []
    for path in stored['removed']:
        if (isinstance(path, str) and is_player_path(path)
                and normalise(path, '/') == path):
            removed.append(path)
        else:
            left_out += 1

    tree = dict(terminal.filesystem)
    for path in removed:
        tree.pop(path, None)
    # Shallowest first, so a directory is there before what is in it.
    for path in sorted(nodes, key=lambda held: held.count('/')):
        parent = tree.get(path.rsplit('/', 1)[0] or '/')
        if parent is None or not parent.is_dir:
            left_out += 1
            continue
        tree[path] = nodes[path]
    if home_size(tree) > PLAYER_LIMIT:
        return None
    terminal.filesystem.clear()
    terminal.filesystem.update(tree)
    return left_out


def load_home(path: str, terminal: Any) -> Optional[str]:
    """
    Read the player's files from disk and put them back.

    A file that does not load whole is never written over: it is set aside
    as home.json.bad, so that what could be saved of it is kept and what
    could not is still there to read, and the player is told once.

    Returns:
        What to tell the player, or None if all was well
    """
    if not path or not os.path.exists(path):
        return None
    left_out = restore_home(terminal, read_json(path))
    if left_out == 0:
        terminal._home_text = home_text(terminal.filesystem)
        return None
    aside = path + '.bad'
    try:
        os.replace(path, aside)
    except OSError:
        # Cannot move it, so cannot be sure of leaving it be: write nothing.
        terminal._home_locked = True
        return ("Your saved files could not be read all of the way, and the "
                "file could not be set aside, so none will be saved this "
                "session.")
    if left_out is None:
        return (f"Your saved files could not be read. The file is kept as "
                f"{aside}.")
    return (f"{left_out} of your saved files could not be read and were "
            f"left out. The original is kept as {aside}.")


def write_home(path: str, terminal: Any) -> None:
    """
    Write the player's files if they have changed since they were last written.

    Nothing is written for a player who has written nothing, and nothing is
    written twice: this runs after every command. A home that is over the
    limit is not written at all, so the file on disk stays the last one that
    fitted; the commands that add files refuse before that happens.
    """
    if not path or getattr(terminal, '_home_locked', False):
        return
    record = home_record(terminal.filesystem)
    text = json.dumps(record, indent=1, sort_keys=True) + '\n'
    if text == getattr(terminal, '_home_text', None):
        return
    if not (record['nodes'] or record['removed']) and not os.path.exists(path):
        return
    if len(text.encode('utf-8')) > PLAYER_LIMIT:
        return
    try:
        write_text_atomically(path, text)
    except OSError:
        return
    terminal._home_text = text


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
        write_text_atomically(
            path, json.dumps(capture(terminal), indent=1, sort_keys=True)
            + '\n')
    except OSError:
        return


def read(path: str) -> Optional[Dict[str, Any]]:
    """Read a saved shift, or nothing at all if it will not read."""
    stored = read_json(path)
    return stored if isinstance(stored, dict) else None


def discard(path: str) -> None:
    """Throw a saved shift away, at a handoff or when it will not load."""
    try:
        os.remove(path)
    except OSError:
        return
