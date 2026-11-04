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
directories and the moo scoreboard, in a file of up to 64 KB, and up to about
17 KB over that in the written-at stamps, which the limit does not count. A
home that does not load whole is set aside as ``home.json.bad`` (then
``.bad.1``, and so on), and every file here is written to a scratch name and moved into place, so a crash
mid-write leaves the old file and not a short one.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .cable import WetSection
from .cases import Case
from .plantjobs import PlantJob, open_missing
from .data.practicals import PRACTICALS
from .data.trouble import FAULTS
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
from .types import TICKET_KEYS

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


# -- the NOC's trouble tickets --------------------------------------------

# Written as text and read back as datetimes; everything else on a ticket is
# plain. A ticket that will not read back is not guessed at.
_TICKET_STAMPS = ('created_time', 'resolution_time')


def _ticket_out(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Write one trouble ticket."""
    written = {key: value for key, value in ticket.items()
               if key not in _TICKET_STAMPS}
    for key in _TICKET_STAMPS:
        if key in ticket:
            written[key] = _stamp(ticket[key])
    return written


def _ticket_in(stored: Any) -> Dict[str, Any]:
    """Read one trouble ticket back, or raise if it will not read."""
    if not isinstance(stored, dict):
        raise TypeError('ticket')
    ticket = dict(stored)
    # Every key a ticket is made with (TICKET_KEYS, read off the type): the
    # displays read them all, and a save missing one loads and then crashes
    # the first screen that does.
    for key in TICKET_KEYS:
        ticket[key]
    for key in _TICKET_STAMPS:
        if key in ticket:
            moment = _moment(ticket[key])
            if moment is None:
                raise ValueError(key)
            ticket[key] = moment
    return ticket


def _pool_in(tour: Dict[str, Any]) -> Optional[Tuple[List[Any], int]]:
    """
    The saved ticket pool and counter, or nothing if there is not a whole
    one: a save from before they were kept, or a damaged one, leaves the
    pool the session was dealt.
    """
    stored = tour.get('tickets')
    counter = tour.get('ticket_counter')
    if (not isinstance(stored, list) or isinstance(counter, bool)
            or not isinstance(counter, int)):
        return None
    try:
        return [_ticket_in(entry) for entry in stored], counter
    except (KeyError, TypeError, ValueError):
        return None


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
    written['first_dispatch_judged'] = report.first_dispatch_judged
    written['clears_after'] = report.clears_after
    written['clears_at'] = report.clears_at
    written['last_read'] = report.last_read
    written['cleared_alone'] = report.cleared_alone
    written['case'] = report.case
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
    # Written since commendations judged the first crew sent. A report from
    # before is taken to have had its first dispatch if it ever had a crew.
    report.first_dispatch_judged = stored.get(
        'first_dispatch_judged', stored.get('dispatched_to') is not None)
    # Written since trouble could go by itself. A report from before is
    # the usual kind, which stays until it is fixed.
    report.clears_after = stored.get('clears_after')
    report.clears_at = stored.get('clears_at')
    last_read = stored.get('last_read')
    report.last_read = (last_read if isinstance(last_read, str)
                        and last_read in FAULTS else None)
    if 'last_read' not in stored and report.tested:
        # Saved before the last reading was kept. It was measured, and the
        # line then was as the record has it: nothing before this save can
        # have cleared a report that did not know it could.
        report.last_read = report.record.fault
    report.cleared_alone = bool(stored.get('cleared_alone', False))
    # Written since one cause could stand behind several reports.
    case = stored.get('case')
    report.case = case if isinstance(case, str) else None
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
        'wet_minutes': section.wet_minutes,
        'credit': section.credit,
        'alarmed': section.alarmed,
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
        # Written since a sheath leaked on the clock. One saved before is
        # taken to have been open as long as it has had pairs to show.
        section.wet_minutes = float(entry.get('wet_minutes', 0.0))
        section.credit = float(entry.get('credit', 0.0))
        section.alarmed = bool(entry.get('alarmed', section.alarming()))
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


# A crew key a saved shift may still carry, and the crew that took its place.
# The central-office crew was Nakamura until the crew list was built from the
# roster (#60), where that work is Johnson's.
RETIRED_CREWS: Dict[str, str] = {'nakamura': 'johnson'}


def _force_in(desk: ReportDesk, stored: Dict[str, Any]) -> None:
    """
    Read the field force back, over the force the desk was dealt.

    The desk starts with every crew the list has, somewhere. What was saved
    moves the crews it knows, under the key they have now; a crew it does not
    know (one the list has since gained) stays where it was dealt, and one the
    list has since lost is dropped.
    """
    crews = {crew.key: crew for crew in (*CREWS, POOL_CREW)}
    loaned = stored.get('loaned')
    desk.force.loaned = loaned if isinstance(loaned, str) else None
    for key, where in stored['at'].items():
        key = RETIRED_CREWS.get(key, key)
        if key in crews:
            desk.force.at[key] = where
    out = {}
    for key, job in stored['out'].items():
        key = RETIRED_CREWS.get(key, key)
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
            'cases': [case.out() for case in desk.cases],
            'jobs': [job.out() for job in desk.jobs],
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
            'triage': terminal.triage_state(),
            'sarts': terminal.special_services.state(
                terminal.career.shift, terminal.shift_minutes),
            'patience': terminal.patience_state(),
            'lamps': terminal.lamp_state(),
            'tickets': [_ticket_out(t) for t in terminal.active_tickets],
            'ticket_counter': terminal.ticket_counter,
        },
    }


def belongs(terminal: Any, stored: Dict[str, Any]) -> bool:
    """Whether a saved shift is this session's: version, tour and wire centre."""
    return (stored.get('version') == VERSION
            and stored.get('shift') == terminal.career.shift
            and stored.get('reports_closed') == terminal.career.reports_closed
            and stored.get('clli') == terminal.desk.clli)


def restore(terminal: Any, stored: Dict[str, Any]) -> bool:
    """
    Put a saved shift back onto a freshly constructed session.

    Returns False and changes nothing if the file does not belong to this
    session (see :func:`belongs`) or does not hold a whole shift. A
    partially applied resume would be worse than no resume at all, so
    everything that can fail is read before anything is assigned.

    Args:
        terminal: The session to restore onto
        stored: What :func:`capture` wrote

    Returns:
        Whether the shift was picked back up
    """
    desk = terminal.desk
    if not belongs(terminal, stored):
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
        sequence = board['sequence']
        closed_count = board['closed_count']
        repeat_count = board['repeat_count']
        regime, key = weather['regime'], weather['key']
        temperature, minutes = weather['temperature'], weather['minutes']
        shift_minutes, charged = tour['shift_minutes'], tour['charged_total']
        fired = set(tour['fired_events'])
        baseline = tuple(tour['baseline'])
        nudges = set(tour['nudges'])
        hint_situation, hint_level = tour['hint_situation'], tour['hint_level']
        assigned = set(tour['assigned_tickets'])
        # Absent from a shift saved before there were controls, and not a
        # control the desk knows is as good as none. Anything that is not a
        # string is not one, and is not allowed to raise below.
        control = board.get('control')
        control = (control if isinstance(control, str)
                   and control in CONTROLS else None)
        # Absent from a shift saved before there were cases: none stood.
        cases = [Case.read(entry) for entry in board.get('cases', [])]
        jobs = [PlantJob.read(entry) for entry in board.get('jobs', [])]
        _plant_in(desk, stored['plant'])
        _force_in(desk, stored['force'])
        pool = _pool_in(tour)
    except (KeyError, TypeError, ValueError):
        return False

    desk.reports = held
    desk.order = order
    desk._sequence = sequence
    desk.closed_count = closed_count
    desk.listed = None
    desk.repeat_count = repeat_count
    desk.control = control
    desk.cases = cases
    desk.jobs = jobs
    open_missing(desk)
    desk._regulars = regulars

    desk.weather.regime = regime
    desk.weather.key = key
    desk.weather.temperature = temperature
    desk.weather._minutes = minutes

    terminal.shift_minutes = shift_minutes
    terminal._charged_total = charged
    terminal._fired_events = fired
    terminal.settle_fired_events()
    terminal._tour_baseline = baseline
    terminal._tour_nudges = nudges
    terminal._hint_situation = hint_situation
    terminal._hint_level = hint_level
    terminal._assigned_tickets = assigned
    # Newer than the first saves. Without them the tour is taken to have
    # been worked, which is the kinder way to be wrong about a resumed shift.
    terminal._tour_desk_start = tour.get('tour_desk_start', 0)
    terminal._board_reviewed = tour.get('board_reviewed', True)
    # The NOC's tickets come back as they were, so their windows go on from
    # where they stood. A save from before they were kept has the pool the
    # session was dealt, and the book copes with that (see restore_triage).
    if pool is not None:
        terminal.active_tickets[:] = pool[0]
        terminal.ticket_counter = pool[1]
    terminal.restore_triage(tour.get('triage'))
    # The repair desk's customers, and what they have been told.
    terminal.restore_patience(tour.get('patience'))
    terminal.restore_lamps(tour.get('lamps'))
    # The special services inventory is dealt again as well, and the desk is
    # not chosen yet when a shift loads. The saved circuits go back, and the
    # outage clock starts from now.
    terminal.special_services.restore(
        tour.get('sarts'), terminal.career.shift, terminal.shift_minutes)
    return True


# -- what the player wrote ------------------------------------------------


def home_record(tree: Dict[str, Node],
                times: bool = True) -> Dict[str, Any]:
    """
    Take the player's files from a filesystem: what differs from the shipped one.

    ``times`` leaves the written-at stamps in or out; the size a home is held
    to is measured without them (see :func:`home_size`).
    """
    changed, removed = player_changes(tree)
    nodes = {}
    for path, node in sorted(changed.items()):
        entry = {'kind': node.kind, 'owner': node.owner,
                 'group': node.group, 'mode': node.mode,
                 'content': node.content if not node.is_dir else None}
        if times:
            entry['mtime'] = _stamp(node.mtime)
        nodes[path] = entry
    return {'version': HOME_VERSION, 'nodes': nodes, 'removed': removed}


def home_text(tree: Dict[str, Node]) -> str:
    """Return what would be written to home.json for this filesystem."""
    return json.dumps(home_record(tree), indent=1, sort_keys=True) + '\n'


def home_size(tree: Dict[str, Node]) -> int:
    """
    Return how big the player's saved files are, as the file they are kept in.

    The limit is on this and nothing narrower - not the text of the files
    alone - because the file is what grows: names, directories and
    permissions all take room in it. Every route that adds to a home (echo,
    mv, cc -o, mkdir) is held to the one measure by asking it. The stamps
    of when a file was written are bookkeeping and are not counted, so a
    home that fitted before it carried them still fits.
    """
    text = json.dumps(home_record(tree, times=False), indent=1,
                      sort_keys=True) + '\n'
    return len(text.encode('utf-8'))


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
    return Node(kind, owner, group, mode, text if kind == 'file' else None,
                _moment(entry.get('mtime')))


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


def aside_name(path: str) -> str:
    """Where a file that would not load goes: ``.bad``, then ``.bad.1``..."""
    name, number = path + '.bad', 0
    while os.path.exists(name):
        number += 1
        name = f'{path}.bad.{number}'
    return name


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
    aside = aside_name(path)
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
    if home_size(terminal.filesystem) > PLAYER_LIMIT:
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


def set_aside(path: str) -> None:
    """Keep a saved shift that would not load, out of the way, as ``.bad``."""
    try:
        os.replace(path, aside_name(path))
    except OSError:
        discard(path)


def discard(path: str) -> None:
    """Throw a saved shift away, at a handoff or when it will not load."""
    try:
        os.remove(path)
    except OSError:
        return
