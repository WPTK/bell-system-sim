"""
Taking a position, and what changes when you do.

The machine deals the whole shift before it knows who sat down. Every
generator - the report desk, the ticket system, the alarms, the shift
events - runs inside BellSystemTerminal.__init__, and self.role is still
None there: it is not set until run() calls select_role(). That ordering is
why the twelve positions were identical, and this module is the one moment
where it stops being true.

take_position() is called from _apply_role, immediately after the sign-off.
It is the first point at which the machine knows which desk it is. It does
NOT re-deal the board: the opening backlog was dealt before you arrived,
which is correct in fiction - you inherit the last tour's board, and what
arrives on yours is yours.

Everything here degrades to the neutral position, which is exactly what the
simulation did before the table existed. A session with no role selected
behaves as it always has.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..data.positions import get as get_position
from ..reports import MAX_PENDING
from .session import SessionState

# How far the board share can move the two arrival rates. A desk with a low
# board share gets fewer customer reports and proportionally more control
# centre traffic; the total does not change, because a quieter board has to
# mean a busier order wire rather than an emptier tour.
NEUTRAL_SHARE = 0.5


class PositionCommands(SessionState):
    """
    What a position changes about the shift.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- taking it -------------------------------------------------------

    def take_position(self, role_key: Optional[str]) -> None:
        """
        Sit down at a desk, and let the shift know which one.

        Pushes the position's fault bias and board depth onto the report
        desk. Everything else is read on demand through the accessors
        below, so that state already dealt is left alone.
        """
        self.position = get_position(role_key)
        self.desk.fault_bias = dict(self.position.fault_bias)
        self.desk.depth_limit = self.board_depth()

    def board_depth(self) -> int:
        """
        How many open reports this desk carries.

        Arrival rate alone cannot express this. The rate falls as the board
        fills, so a board-heavy desk given a faster arrival simply reaches
        the same ceiling sooner and ends up with the same board and fewer
        tickets - which is a desk with less work, not a different one. The
        depth is the lever that actually moves.
        """
        share = self.position.board_share
        # A gentle range around today's nine. It must never fall near the
        # three-to-five report backlog a shift opens with, or the desk
        # starts full and refuses work for the whole tour - which is how
        # the first attempt at this gave a planning desk a dead board.
        return round(MAX_PENDING - 3 + 6 * share)

    # -- what it changes -------------------------------------------------

    def ticket_rate(self, base: float) -> float:
        """
        Scale the rate the control centre hands this desk something.

        This is the lever that actually moves, and the only one. Report
        arrival is not scaled at all: measuring it showed the board runs
        saturated - arrival falls as depth rises, so reports come in
        exactly as fast as you close them and the rate makes no difference
        to how many you see. Scaling it only ever removed tickets, which
        is a desk with less work rather than a different one.
        """
        return base * ((1.0 - self.position.board_share) / NEUTRAL_SHARE)

    def prefer_tickets(self, tickets: List[Any]) -> List[Any]:
        """
        Narrow a pool of unassigned tickets to this desk's own kind.

        A preference and not a filter: a desk with nothing of its own
        waiting takes what there is, because somebody has to.
        """
        wanted = self.position.ticket_categories
        if not wanted or not tickets:
            return tickets
        mine = [ticket for ticket in tickets
                if ticket.get('category') in wanted]
        return mine or tickets

    def position_voices(self) -> Tuple[str, ...]:
        """Who talks to this desk on top of the whole building."""
        return self.position.voices

    # -- what it did tonight ---------------------------------------------

    def position_tally(self) -> List[Tuple[str, str]]:
        """
        What this desk did this tour, as label and value.

        Deliberately a tally and not a score. The service index is the only
        thing scored, and this prints beside it to say what the tour
        actually consisted of - which for most of these desks is not
        repair commitments at all.
        """
        rows: List[Tuple[str, str]] = []
        for key in self.position.tally:
            counter = _COUNTERS.get(key)
            if counter is None:  # pragma: no cover - guarded by a test
                continue
            label, value = counter(self)
            rows.append((label, value))
        return rows


# -- the counters --------------------------------------------------------
#
# Each reads state the simulation already keeps. Nothing here adds a
# persisted number, and nothing here is scored.


def _closed(terminal: Any) -> List[Any]:
    """Reports closed this tour."""
    return terminal.desk.closed()


def _at_jobs(terminal: Any) -> Tuple[str, str]:
    """Work queued to run later in the shift."""
    queued = len(terminal._at_jobs)
    return 'at(1) jobs still queued', str(queued)


def _uucp_queue(terminal: Any) -> Tuple[str, str]:
    """What is waiting to go out over uucp."""
    log = terminal._read('/usr/adm/uucplog') or ''
    failed = sum(1 for line in log.split('\n') if 'FAILED' in line)
    return 'uucp calls that failed', str(failed)


def _commands_run(terminal: Any) -> Tuple[str, str]:
    """How much was typed."""
    return 'commands typed', str(sum(terminal.command_counts.values()))


def _office_faults(terminal: Any) -> Tuple[str, str]:
    """Closed reports whose trouble was on the office side of the frame."""
    count = sum(1 for report in _closed(terminal)
                if report.record.fault in ('FCG', 'CO_EQUIP'))
    return 'office troubles closed', str(count)


def _alarms_open(terminal: Any) -> Tuple[str, str]:
    """Alarms nobody has acknowledged."""
    open_now = [alarm for alarm in terminal.active_alarms
                if not alarm.get('acknowledged')]
    return 'alarms unacknowledged', str(len(open_now))


def _wasted_trips(terminal: Any) -> Tuple[str, str]:
    """Crews sent somewhere the trouble was not."""
    count = sum(1 for report in terminal.reports_all()
                if report.dispatched_to and not report.field_finding)
    return 'crews sent to the wrong place', str(count)


def _dispatches(terminal: Any) -> Tuple[str, str]:
    """Times somebody was put in a truck."""
    count = sum(1 for report in terminal.reports_all()
                if report.dispatched_to)
    return 'crews dispatched', str(count)


def _sheaths_cleared(terminal: Any) -> Tuple[str, str]:
    """Wet binder groups a splicer has opened."""
    repaired = [section for section in terminal.desk.plant.sections
                if section.repaired]
    pairs = sum(len(section.pairs) for section in repaired)
    return ('sheaths opened',
            f"{len(repaired)} ({pairs} pairs cleared)")


def _groups_over(terminal: Any) -> Tuple[str, str]:
    """Trunk groups carrying more than their objective."""
    over = [name for name, group in terminal.trunk_groups.items()
            if group['utilization'] > 85]
    return 'trunk groups over objective', str(len(over))


def _tickets_worked(terminal: Any) -> Tuple[str, str]:
    """Trouble tickets this position was handed."""
    return 'tickets assigned to you', str(len(terminal._assigned_tickets))


def _no_trouble_found(terminal: Any) -> Tuple[str, str]:
    """Reports closed code 8."""
    count = sum(1 for report in _closed(terminal) if report.disposition == 8)
    return 'closed as no trouble found', str(count)


def _off_hook_caught(terminal: Any) -> Tuple[str, str]:
    """
    Receivers off the hook, closed without putting anybody in a truck.

    This desk's whole skill: a short and a receiver off hook look the same
    from a position, and knowing the difference saves a trip.
    """
    caught = sum(1 for report in _closed(terminal)
                 if report.record.fault == 'ROH' and not report.dispatched_to)
    return 'off-hook receivers, no trip sent', str(caught)


def _commitments_met(terminal: Any) -> Tuple[str, str]:
    """Promises to customers kept against promises made."""
    closed = _closed(terminal)
    missed = sum(1 for report in closed if report.missed_commitment)
    return 'commitments met', f"{len(closed) - missed} of {len(closed)}"


def _repeats(terminal: Any) -> Tuple[str, str]:
    """Customers who had to call again."""
    return 'reports that came back', str(terminal.desk.repeat_count)


def _found_in_records(terminal: Any) -> Tuple[str, str]:
    """Troubles found by reading the frame rather than measuring the loop."""
    count = sum(1 for report in terminal.reports_all()
                if any('frame record' in note for note in report.test_notes))
    return 'found in the records', str(count)


def _orders_raised(terminal: Any) -> Tuple[str, str]:
    """Service orders put on the frame's list."""
    return 'service orders raised', str(len(terminal._service_orders))


def _circuits_in_trouble(terminal: Any) -> Tuple[str, str]:
    """Special service circuits not in service."""
    return ('special circuits in trouble',
            str(len(terminal.sarts.in_trouble())))


def _tests_run(terminal: Any) -> Tuple[str, str]:
    """Measurements and plant tests taken."""
    counts = terminal.command_counts
    run = (counts.get('mlt', 0) + counts.get('testline', 0)
           + counts.get('testcall', 0) + counts.get('testboard', 0))
    return 'tests run', str(run)


def _documents_set(terminal: Any) -> Tuple[str, str]:
    """Passes through the document tools."""
    counts = terminal.command_counts
    run = sum(counts.get(name, 0) for name in
              ('nroff', 'troff', 'tbl', 'eqn', 'pic', 'refer', 'spell'))
    return 'documents formatted', str(run)


def _files_written(terminal: Any) -> Tuple[str, str]:
    """Files this position created or changed."""
    counts = terminal.command_counts
    written = sum(counts.get(name, 0) for name in
                  ('ed', 'cp', 'mv', 'touch', 'mkdir', 'cc', 'tee'))
    return 'files written', str(written)


def _weather_now(terminal: Any) -> Tuple[str, str]:
    """What it is doing outside, which is a radio desk's whole afternoon."""
    return 'weather', terminal.desk.weather.label()


_COUNTERS: Dict[str, Any] = {
    'at_jobs': _at_jobs,
    'uucp_queue': _uucp_queue,
    'commands_run': _commands_run,
    'office_faults': _office_faults,
    'alarms_open': _alarms_open,
    'wasted_trips': _wasted_trips,
    'dispatches': _dispatches,
    'sheaths_cleared': _sheaths_cleared,
    'groups_over': _groups_over,
    'tickets_worked': _tickets_worked,
    'no_trouble_found': _no_trouble_found,
    'off_hook_caught': _off_hook_caught,
    'commitments_met': _commitments_met,
    'repeats': _repeats,
    'found_in_records': _found_in_records,
    'orders_raised': _orders_raised,
    'circuits_in_trouble': _circuits_in_trouble,
    'tests_run': _tests_run,
    'documents_set': _documents_set,
    'files_written': _files_written,
    'weather_now': _weather_now,
}
