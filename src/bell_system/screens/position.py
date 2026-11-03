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

from ..clock import career_progress
from ..data.positions import desk_only, get as get_position
from ..reports import MAX_PENDING, TroubleReport
from .session import SessionState

# How far the board share can move the two arrival rates. A desk with a low
# board share gets fewer customer reports and proportionally more control
# centre traffic; the total does not change, because a quieter board has to
# mean a busier order wire rather than an emptier tour.
NEUTRAL_SHARE = 0.5

# How many more open reports the last tour of a career carries than the
# first. Measured rather than set by eye: a desk left to fill settles at
# nine on tour one and eleven on tour thirteen, and no position comes near
# the three-to-five backlog a shift opens with. Small on purpose - the last
# attempt at moving this lever overshot and left one desk with a board that
# started full and never took another report for three hundred commands.
#
# What it does not change is throughput. Simulated players close the same
# thirty-two reports a tour at either end, because the board runs saturated
# and arrival falls as depth rises. Depth is pressure, not volume, and that
# is the right thing for it to be.
CAREER_DEPTH = 2

# How long a customer waits, in shift minutes, before ringing the repair
# desk again. A line that is out of service rings sooner than one that is
# only noisy. The simulation's own figures: nothing sourced says how long a
# 1983 customer held on.
PATIENCE = {True: 20, False: 45}

# Most rings a customer makes before they stop ringing and start writing.
MAX_RINGS = 3

# What an advise call costs in shift minutes: the call itself, each ring the
# customer has already made on the report (they are not calm), and the
# extra it takes to tell somebody you have nothing to tell them.
ADVISE_CALL = 3
ADVISE_RING = 2
ADVISE_EMPTY = 3


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
        if self.position.key == 'noc':
            self._count_triage()

    _triage_counted = False

    def _count_triage(self) -> None:
        """
        Open the NOC's windows with the tour, and put them on the index.

        A ticket nobody is on past its window is the NOC's version of a
        report left open past its commitment, and the service index already
        counts those through career.open_overdue. Adding the tickets to
        that count is what makes ignoring the queue cost something without
        anyone looking, and the handoff already prints the result.
        """
        queue: Any = self  # The ticket commands, mixed into the same class.
        queue.triage_book()
        if self._triage_counted:
            return
        self._triage_counted = True
        reports = self.career.open_overdue
        self.career.open_overdue = (
            lambda: reports() + len(queue.triage_overdue()))

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
        #
        # Plus up to two more across a career. Tour one is quiet and tour
        # thirteen is not, and that is the shape of getting good at
        # something rather than a difficulty setting: the difficulty still
        # governs only how forgiving the scoring is.
        deeper = CAREER_DEPTH * career_progress(self.career.shift)
        return round(MAX_PENDING - 3 + 6 * share + deeper)

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

    def position_measure(self) -> List[str]:
        """
        What this desk is judged on, and what it is not.

        The service index is the customer reports component of the network
        switching performance measurement plan. That plan measures a
        switching machine, and eight of these twelve desks are outside its
        scope entirely - a planning engineer has no repair commitments and
        a document preparation specialist has no trunk group.

        Saying so beats forcing a key. What a desk with no component gets
        instead is the tally: not a second score competing with the first,
        just a plain account of what the tour consisted of.
        """
        position = self.position
        if position.nspmp:
            label = position.nspmp.replace('_', ' ')
            return [f"It is the {label} component of the",
                    "performance plan, which is what this desk works."]
        return ["No component of that plan covers this desk. It",
                "measures a switching machine and this is not,",
                "so the index is carried for the record."]


# -- the counters --------------------------------------------------------
#
# Each reads state the simulation already keeps. Nothing here adds a
# persisted number, and nothing here is scored.

    # -- the repair desk's customers ------------------------------------

    _patience_book: Optional[Dict[str, Any]] = None

    def patience_book(self) -> Dict[str, Any]:
        """
        What the repair desk has told its customers, and who has rung.

        ``told`` is the report's elapsed time when the customer was last
        advised; ``rung`` the most rings the sweep has seen on a report,
        so that closing it does not take the count away. Tied to the board
        it describes: a new board is a new book.
        """
        book = self._patience_book
        if book is None or book['desk'] != id(self.desk):
            book = {'desk': id(self.desk), 'told': {}, 'rung': {}}
            self._patience_book = book
        return book

    def patience(self, report: TroubleReport) -> Tuple[int, int]:
        """
        Return the rings a customer has made on a report and the minutes
        until the next.

        Their wait is the report's own elapsed time, which is the shift
        clock: it moves with what is typed and run, and the board ages while
        it does. The first tour is a grace, because the wire chief is still
        talking.
        """
        window = PATIENCE[report.out_of_service]
        if self.first_tour():
            return 0, window
        wait = report.minutes_spent - self.patience_book()['told'].get(
            report.number, 0)
        return min(MAX_RINGS, wait // window), window - wait % window

    def patience_queue(self) -> List[Tuple[TroubleReport, int, int]]:
        """
        The customers holding, most rings first, then soonest to ring.

        Looking is when a ring is noticed, and what it noticed is kept.
        """
        rung = self.patience_book()['rung']
        queue = []
        for report in self.desk.customers():
            rings, left = self.patience(report)
            rung[report.number] = max(rung.get(report.number, 0), rings)
            queue.append((report, rings, left))
        return sorted(queue, key=lambda row: (-row[1], row[2]))

    def advise(self, args: List[str]) -> str:
        """
        trouble advise [REPORT]: the repair desk's call back to a customer.

        With no argument, the customers holding. With a report, ring that
        customer and tell them where it stands. The call costs shift
        minutes, more for each time they have already rung, and more again
        when there is nothing yet to tell them - so the report is worth
        testing before the customer is, and a customer on the third ring is
        worth reaching before one on the first.
        """
        refusal = desk_only(self.position, 'custserv', 'trouble advise')
        if refusal:
            return refusal
        if args:
            return self._advise_call(args[0])
        queue = self.patience_queue()
        lines = [f"CUSTOMERS HOLDING   {self.position.name}",
                 f"Shift time {self.shift_time()}", '=' * 66,
                 f"{'REPORT':<10}{'LINE':<14}{'RINGS':<7}{'NEXT RING':<11}"
                 f"{'CALL':<6}TOLD", '-' * 66]
        for report, rings, left in queue:
            known = bool(report.tested or report.dispatched_to)
            lines.append(
                f"{report.number:<10}{report.record.telephone_number:<14}"
                f"{rings:<7}{str(left) + 'm':<11}"
                f"{self._advise_cost(rings, known):>2}m   "
                f"{'status' if known else 'nothing yet'}")
        if not queue:
            lines.append("Nobody is holding.")
        lines += [
            '-' * 66,
            f"{len(queue)} customer(s) with a report open.",
            "",
            "  trouble advise <REPORT>   Ring them back and say where it",
            "                            stands (CALL minutes)",
            "  report test <REPORT>      Find something to tell them first",
            "",
            "A customer rings again after 20 shift minutes out of service,",
            "45 otherwise, counted from the last call. These figures are",
            "the simulation's own.",
        ]
        return '\n'.join(lines)

    @staticmethod
    def _advise_cost(rings: int, known: bool) -> int:
        """Shift minutes an advise call costs."""
        return (ADVISE_CALL + ADVISE_RING * rings
                + (0 if known else ADVISE_EMPTY))

    def _advise_call(self, token: str) -> str:
        """Ring one customer back, and say what there is to say."""
        wanted = token.upper()
        report = next((r for r in self.desk.customers()
                       if r.number == wanted
                       or r.number.split('-')[-1].lstrip('0') == wanted
                       .lstrip('0')), None)
        if report is None:
            return (f"trouble advise: no customer holding on '{token}'.\n"
                    f"'trouble advise' lists them.")
        rings, _ = self.patience(report)
        book = self.patience_book()
        book['rung'][report.number] = max(
            book['rung'].get(report.number, 0), rings)
        known = bool(report.tested or report.dispatched_to)
        cost = self._advise_cost(rings, known)
        self._pass_time(cost)
        if known:
            book['told'][report.number] = report.minutes_spent
            if report.dispatched_to:
                said = (f"{report.crew or report.dispatched_to} is on it"
                        f" ({report.dispatched_to}).")
            else:
                said = (report.test_notes[-1] if report.test_notes
                        else "it has been tested.")
            tone = (f"They had rung {rings} time(s) already." if rings
                    else "They had not rung yet.")
            return '\n'.join([
                f"{report.number}: rang {report.record.telephone_number}. "
                f"{tone}",
                f"Told them: {said}",
                f"That was {cost} minutes of the shift; they will not ring "
                f"for {PATIENCE[report.out_of_service]} more.",
            ])
        # Nothing to tell: half the wait is forgiven, no more.
        wait = report.minutes_spent - book['told'].get(report.number, 0)
        book['told'][report.number] = report.minutes_spent - wait // 2
        return '\n'.join([
            f"{report.number}: rang {report.record.telephone_number} with "
            f"nothing to tell them.",
            f"That was {cost} minutes of the shift, and half of what they "
            f"had waited",
            f"is still owed. Test the line first: report test "
            f"{report.number}",
        ])


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


def _tickets_past_window(terminal: Any) -> Tuple[str, str]:
    """Tickets whose triage window closed with nobody on them."""
    return ('tickets past their response window',
            str(terminal.triage_lapsed()))


def _customers_rang_back(terminal: Any) -> Tuple[str, str]:
    """Rings customers made while their report was open."""
    terminal.patience_queue()  # Looking is when a ring is noticed.
    return ('customer ringbacks',
            str(sum(terminal.patience_book()['rung'].values())))


def _alarms_cleared(terminal: Any) -> Tuple[str, str]:
    """Alarms cleared at the cause, not only acknowledged."""
    return ('alarms cleared at the cause',
            str(len(terminal.lamp_book()['cleared'])))


def _alarms_lit(terminal: Any) -> Tuple[str, str]:
    """Alarms whose lamp rose above their class while nobody worked them."""
    terminal.lamp_panel()  # Looking is when a lamp that rose is noticed.
    return ('alarm lamps that rose',
            str(len(terminal.lamp_book()['lit'])))


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
            str(len(terminal.special_services.in_trouble())))


def _circuit_minutes_out(terminal: Any) -> Tuple[str, str]:
    """Shift minutes special services circuits spent held in trouble."""
    inventory = terminal.special_services
    inventory.accrue(terminal.career.shift, terminal.shift_minutes)
    return 'circuit-minutes out of service', str(inventory.minutes_out())


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
    'tickets_past_window': _tickets_past_window,
    'customers_rang_back': _customers_rang_back,
    'alarms_cleared': _alarms_cleared,
    'alarms_lit': _alarms_lit,
    'no_trouble_found': _no_trouble_found,
    'off_hook_caught': _off_hook_caught,
    'commitments_met': _commitments_met,
    'repeats': _repeats,
    'found_in_records': _found_in_records,
    'orders_raised': _orders_raised,
    'circuits_in_trouble': _circuits_in_trouble,
    'circuit_minutes_out': _circuit_minutes_out,
    'tests_run': _tests_run,
    'documents_set': _documents_set,
    'files_written': _files_written,
    'weather_now': _weather_now,
}
