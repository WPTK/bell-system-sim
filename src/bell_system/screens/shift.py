"""
The working shift: its clock, its events, and the other craft on the wire.
"""
from ..constants import BELL_SYSTEM_ROLES, SHIFT_LENGTH_MINUTES
import random
from datetime import timedelta
from collections import (
    deque,
)
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
)
from ..field import CREWS
from ..data import tours
from ..data.consequences import Late
from ..data.tours import Tour, watch_of
from ..commitment import commitment_label
from ..plantjobs import open_job
from ..npc import (
    CRAFT,
    FAVOUR_MINUTES,
    WATCH_LABELS,
    Message,
    CRAFT_BY_NAME,
    adjust_rapport,
    chatter_key,
    favour_due,
    forget_rested,
    is_away,
    on_shift,
    rapport_with,
    render as render_message,
    watch_at,
)
from ..progression import (
    QUALIFICATIONS,
)
from .session import SessionState


class ShiftCommands(SessionState):
    """
    The working shift: its clock, its events, and the other craft on the wire.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _initialize_shift_handoff(self) -> None:
        """Initialize authentic Bell System shift handoff data."""
        self.shift_handoff = {
            "previous_shift": {
                "operator": "Johnson, R.",
                "end_time": "07:59",
                "summary": "Routine night operations - 3 tickets transferred",
                "key_issues": [
                    "RIDGE-X1 intermittent alarms - monitoring",
                    "UUCP queue backup - resolved 06:30",
                    "Crossbar maintenance scheduled 09:15"
                ],
                "open_tickets": ["SW-2847", "MX-2156", "FD-1293"],
                "system_status": "All systems operational",
                "special_instructions": "Monitor trunk TG-047 for blocking threshold"
            }
        }
    def tour_script(self) -> Optional[Tour]:
        """
        Return this tour's entry in data/tours.py, if it applies.

        It does not on a calendar other than the one it was written for: a
        player who moved the epoch gets the routine and no set pieces.
        """
        return tours.script(self.career.shift, self.clock.tour_day())

    def tour_brief(self, counts: Optional[Mapping[str, int]] = None
                   ) -> List[str]:
        """
        The tour's theme, its briefing and its goals, as printed lines.

        Shared by the briefing a shift opens with and by shift(1), so the
        two cannot disagree about what today is for. Given the tour's
        counts, each goal says how far along it is.
        """
        entry = self.tour_script()
        if entry is None:
            return []
        lines = [f"Tour {entry.number} of {len(tours.TOURS)}: "
                 f"{entry.theme} ({entry.kind})"]
        lines.extend(f"  {line}" for line in entry.briefing)
        lines.append("  Goals, struck at handoff and never scored:")
        for goal in entry.goals:
            progress = f"  (so far {counts[goal.metric]})" if counts else ''
            lines.append(f"    - {goal.text}{progress}")
        if counts:
            lines.append("  Unworked time will still age the board at "
                         "handoff.")
        return lines

    def generate_shift_events(self) -> None:
        """
        Put the tour's scheduled work, tests and known conditions on the
        board, and the news the feed has brought in.

        The catalogue is reference data and lives in data/tours.py; what is
        here is when to ask for it. Re-run at every shift change, which is
        why it is safe to call again once a position is taken. The board is
        the same for the same tour at the same office, because a saved shift
        rebuilds it and the events that have fired are remembered by number.
        """
        self.shift_events = tours.build(
            self.career.shift, self.home_office, self.clock.tour_day())
        self.deliver_news()
    def show_shift_briefing(self) -> None:
        """
        Display role-specific shift briefing.

        Provides authentic Bell System shift briefing information
        tailored to the selected operational role.
        """
        current_time = self.clock.now().strftime("%H:%M")
        current_date = self.clock.now().strftime("%B %d, %Y")

        self.emit(f"\n{'='*60}")
        self.emit(f"BELL SYSTEM SHIFT BRIEFING - {current_date}")
        self.emit(f"Shift Start Time: {current_time}")
        self.emit(f"Watch: {self._get_shift_hours()}")
        # Find the role name for display
        role_name = "Unknown Role"
        for role_id, (role_key, name) in BELL_SYSTEM_ROLES.items():
            if role_key == self.role:
                role_name = name
                break
        self.emit(f"Role: {role_name}")
        if self.resumed:
            # Not a new tour: the one somebody put down. Worth saying,
            # because the board is not the board a shift usually opens on
            # and the difference matters if part of it is already overdue.
            self.emit(f"Resumed: {self.shift_time()} already worked, "
                      f"{len(self.desk.pending())} on the board")
        self.emit(f"{'='*60}")
        brief = self.tour_brief()
        if brief:
            self.emit()
            for line in brief:
                self.emit(line)
            self.emit()

        # Role-specific briefings
        role_briefings = {
            "sysop": self._get_sysop_briefing(),
            "switch": self._get_switch_briefing(),
            "field": self._get_field_briefing(),
            "noc": self._get_noc_briefing(),
            "tsps": self._get_tsps_briefing(),
            "dba": self._get_dba_briefing(),
            "netplan": self._get_netplan_briefing(),
            "custserv": self._get_custserv_briefing(),
            "radio": self._get_radio_briefing(),
            "tnds": self._get_tnds_briefing(),
            "sarts": self._get_sarts_briefing(),
            "docprep": self._get_docprep_briefing()
        }

        briefing = role_briefings.get(self.role or '',
                                      "Generic Bell System briefing")
        self.emit(briefing)

        self.emit("\nShift Events:")
        for i, event in enumerate(self.shift_events[:5], 1):
            priority_marker = "*** " if event["priority"] == "CRITICAL" else "** " if event["priority"] == "HIGH" else "* " if event["priority"] == "MEDIUM" else ""
            self.emit(f"  {i}. {event['time']} [{event['type']}] {priority_marker}{event['status']}")
            self.emit(f"     {event['title']}")
            self.emit(f"     ID: {event['id']}")
            self.emit()

        self.emit("\nCurrent System Status:")
        self.emit("  Network Operations: NORMAL")
        self.emit("  Switch Centers: 47/48 operational")
        self.emit("  TNDS Collection: ACTIVE")
        self.emit("  Emergency Services: OPERATIONAL")

        self._emit_board_briefing()

        self.emit("\nType 'help' for available commands or 'man <command>' for detailed help.")
        self.emit(f"{'='*60}")
    def _emit_board_briefing(self) -> None:
        """
        Show the board the shift starts with, and what to do about it.

        Whatever position a craftsperson holds, there is a board of customer
        trouble waiting. Saying so at the start of the shift is the
        difference between a terminal with commands and a terminal with a
        job.
        """
        pending = self.desk.pending()
        difficulty = self._difficulty()

        self.emit("\nRepair Service Bureau:")
        self.emit(f"  Reports on your board: {len(pending)}")
        if pending:
            oldest = pending[0]
            self.emit(f"  Nearest commitment:    {oldest.number} "
                      f"({oldest.record.telephone_number}) "
                      f"{commitment_label(oldest)}")
        self.emit(f"  Difficulty:            {difficulty.name}")
        self.emit(f"  Service index:         "
                  f"{self.career.service_index():.1f} of 100 "
                  f"({self.career.index_band()})")
        self.emit(f"  Shift:                 {self.career.shift}")

        held = len(self.career.qualifications)
        self.emit(f"  Qualifications:        {held} of "
                  f"{len(QUALIFICATIONS)} held")

        self.emit("\n  'report' for the board, 'mlt <report>' to measure a "
                  "loop,")
        self.emit("  'qual' for your craft record.")
        self.emit("\n  This is a UNIX machine. Look around: 'cd /usr/doc', "
                  "'ls', 'cat divestiture'.")
        self.emit("  Commands join with a pipe: 'who | wc -l'.")
        if self.career.shift == 1 and not self.career.reports_closed:
            self.emit("  'set game.difficulty craft' if you want the shift "
                      "worked the hard way.")
    def _get_shift_hours(self) -> str:
        """Get current shift description."""
        return WATCH_LABELS[self.current_watch()]

    def current_watch(self) -> str:
        """
        Which watch of the day this tour is worked on.

        The tour says (``tours.watch_of``), and the clock opens the tour on
        that watch's hour. With ``date.source`` set to ``real`` the clock is
        the host's and its hour decides, since that is the one place the
        hour on the clock is the hour.
        """
        if self.settings.get('date.source') == 'real':
            return watch_at(self.clock.now())
        return watch_of(self.career.shift)

    def is_in(self, login: str) -> bool:
        """Whether this person is in the building on this watch and tour."""
        return on_shift(login, self.current_watch(), self.career.shift)

    def absent_crews(self) -> Set[str]:
        """Keys of the field crews who are away for the whole of this tour."""
        return {crew.key for crew in CREWS
                if is_away(CRAFT_BY_NAME.get(crew.name, ''), self.career.shift)}
    def cmd_events(self, args: List[str]) -> str:
        """Bell System operational events and shift activity"""
        if not args:
            output = [f"Bell System Operational Events - Shift {self.current_shift}"]
            output.append("=" * 55)
            output.append("")

            for i, event in enumerate(self.shift_events, 1):
                priority_marker = "*** " if event["priority"] == "CRITICAL" else "** " if event["priority"] == "HIGH" else "* " if event["priority"] == "MEDIUM" else ""
                output.append(f"{i:2d}. {event['time']} [{event['type']}] {priority_marker}{event['status']}")
                output.append(f"    {event['title']}")
                output.append(f"    Event ID: {event['id']}")
                output.append("")

            output.append("Commands:")
            output.append("  events detail <event_id>     - View detailed event information")
            output.append("  events work <event_id>       - Work on specific event")
            output.append("  events priority <level>      - Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)")
            output.append("  events status <status>       - Filter by status")
            output.append("")
            return "\n".join(output)

        elif args[0] == "detail" and len(args) > 1:
            event_id = args[1].upper()
            found_event = next(
                (e for e in self.shift_events if e["id"] == event_id), None)

            if not found_event:
                return f"Event {event_id} not found. Use 'events' to see available events."

            output = [f"BELL SYSTEM EVENT DETAILS: {found_event['id']}"]
            output.append("=" * 50)
            output.append("")
            output.append(f"Time:        {found_event['time']}")
            output.append(f"Type:        {found_event['type']}")
            output.append(f"Priority:    {found_event['priority']}")
            output.append(f"Status:      {found_event['status']}")
            output.append(f"Title:       {found_event['title']}")
            origin = found_event['origin']
            output.append("Origin:      " + (
                found_event['source'] if origin == tours.OWN
                else f"{origin.title()} - {found_event['source']}"))
            output.append("")
            output.append("Description:")
            output.append(f"  {found_event['description']}")
            output.append("")
            output.append("Details:")
            output.append(f"  {found_event['details']}")
            output.append("")
            output.append("Recommended Actions:")
            for i, action in enumerate(found_event['actions'], 1):
                output.append(f"  {i}. {action}")
            output.append("")
            output.append(f"Use 'events work {event_id}' to begin working this event")
            output.append("")
            return "\n".join(output)

        elif args[0] == "work" and len(args) > 1:
            event_id = args[1].upper()
            found_event = next(
                (e for e in self.shift_events if e["id"] == event_id), None)

            if not found_event:
                return f"Event {event_id} not found. Use 'events' to see available events."

            # Update event status to indicate work started
            found_event["status"] = "IN_PROGRESS"

            output = [f"WORKING EVENT: {found_event['id']} - {found_event['title']}"]
            output.append("=" * 60)
            output.append("")
            output.append(f"Event Type: {found_event['type']}")
            output.append(f"Priority: {found_event['priority']}")
            output.append("")
            output.append("WORK LOG INITIATED:")
            output.append(f"  {self.clock.now().strftime('%H:%M')} - Work started by {self.username}")
            output.append(f"  {self.clock.now().strftime('%H:%M')} - Reviewing event details and recommended actions")
            output.append("")
            output.append("NEXT STEPS:")
            for i, action in enumerate(found_event['actions'], 1):
                output.append(f"  {i}. {action}")
            output.append("")

            # Role-specific guidance
            role_guidance = {
                "radio": "Use 'radio' commands to investigate microwave path issues",
                "switch": "Use 'switch' and '3a' commands for switching system problems",
                "noc": "Coordinate with other teams and monitor network impact",
                "field": "Dispatch field technicians and coordinate on-site activities",
                "sysop": "Check system logs and coordinate with development teams"
            }

            if self.role in role_guidance:
                output.append("Role-Specific Guidance:")
                output.append(f"  {role_guidance[self.role]}")
                output.append("")

            output.append("Use relevant Bell System commands to investigate and resolve this event.")
            output.append("Document progress with 'ticket create' if escalation needed.")
            output.append("")
            return "\n".join(output)

        elif args[0] == "priority" and len(args) > 1:
            priority = args[1].upper()
            filtered_events = [e for e in self.shift_events if e["priority"] == priority]

            if not filtered_events:
                return f"No events found with priority '{priority}'"

            output = [f"Events with Priority: {priority}"]
            output.append("=" * 40)
            output.append("")
            for event in filtered_events:
                output.append(f"{event['time']} [{event['type']}] {event['status']}")
                output.append(f"  {event['title']}")
                output.append(f"  Event ID: {event['id']}")
                output.append("")

            return "\n".join(output)

        elif args[0] == "status" and len(args) > 1:
            status = args[1].upper()
            filtered_events = [e for e in self.shift_events if e["status"] == status]

            if not filtered_events:
                return f"No events found with status '{status}'"

            output = [f"Events with Status: {status}"]
            output.append("=" * 40)
            output.append("")
            for event in filtered_events:
                output.append(f"{event['time']} [{event['type']}] {event['priority']}")
                output.append(f"  {event['title']}")
                output.append(f"  Event ID: {event['id']}")
                output.append("")

            return "\n".join(output)

        else:
            return f"events: unknown option '{args[0]}'\nUse 'events' for available commands"
    def _stamp(self) -> str:
        """Return a timestamp in the form the messaging channels carried."""
        return self.clock.log_stamp()

    def start_tour_clock(self) -> None:
        """Put the clock on this tour's day and the hour of its watch."""
        self.clock.set_tour(self.career.shift,
                            tours.start_hour(self.career.shift))
        # The office panel's book is settled by the sign-offs held as the tour
        # opens, so it is opened here and not at the first look at the panel:
        # a sign-off passed in the middle of the tour cannot change it.
        office: Any = self  # The office commands, mixed into the same class.
        office.lamp_book()

    def _queue_message(self, message, after: int) -> None:
        """
        Hold a message back so it lands a few commands from now.

        A repeat is filed by the bureau (``bureau.py``, ``_close_report``) with
        the code it was closed under and nothing of the customer; the class of
        service and the new commitment are on the report, and the customer's
        second call is made from them here. This is a workaround for not
        editing that call site, which is outside this phase's files.
        """
        if message.kind == 'repeat' and message.about:
            report = self.desk.find(message.about)
            original = self.desk.find(report.repeat_of or '') if report else None
            if report and original:
                message = self.switchroom.with_class(
                    message, f'code {original.disposition}',
                    report.record.telephone_number,
                    report.record.class_of_service,
                    report.commitment.strftime('%H:%M'))
        self._queued_messages.append([after, message])

    def _drain_queue(self) -> List[str]:
        """Return any held messages that are now due."""
        due: List[str] = []
        remaining: deque = deque()
        while self._queued_messages:
            countdown, message = self._queued_messages.popleft()
            countdown -= 1
            if countdown <= 0:
                due.append(render_message(message, self._stamp()))
            else:
                remaining.append([countdown, message])
        self._queued_messages = remaining
        return due

    def _interrupt(self) -> str:
        """
        Advance the shift and return what the building has to say.

        Eight hours is the tour, and ``_relief_due`` ends it, after the line
        the player typed and outside its output.
        """
        if getattr(self, '_in_pipeline', False):
            return ''  # a pipeline charges for itself once it finishes
        return self._building_says()

    def _relief_due(self) -> str:
        """
        The handoff, once the line that crossed eight hours has finished.

        The same sign-off as ``handoff relieve``, whatever the ambience. It
        starts the next tour on a clock at zero, so it cannot fire twice,
        and a career that is finished has no tour to end.
        """
        if self.shift_minutes < SHIFT_LENGTH_MINUTES or self.career.finished:
            return ''
        return self._time_is_up()

    def _building_says(self) -> str:
        """
        Advance the shift and return whatever the building has to say.

        Called after every command. The shift clock, new work arriving and
        tickets being assigned are simulation state and happen regardless;
        the ambience setting governs only whether anybody tells you about
        them. Interruption rate is the difficulty's: a shift on the forgiving
        setting is quiet, a shift on the other one is not.
        """
        quiet = not self.settings.is_on('game.ambience')
        difficulty = self._difficulty()
        pieces = self._advance_shift()
        if not quiet:
            pieces = self._drain_queue() + pieces

        # A first tour is one report and the wire chief. Work still
        # arrives at the bureau; it is held off this board until the first
        # one is closed, which is what the chief says he is doing, and the
        # people who would hand you more work hold off with it. The
        # building itself carries on - the weather turns, the shift events
        # come due - because a first tour that is silent is not a shift,
        # it is a tutorial with the lights off.
        if self.first_tour():
            return '\n'.join(self.at_due() + ([] if quiet else pieces))

        pieces.extend(self._settle_people(quiet))

        # The switching control centre puts a ticket on you now and then.
        # These are the tickets the trouble system already carries; being
        # handed one by name is the difference between a list and an
        # assignment.
        if random.random() < self.ticket_rate(difficulty.interruption_rate * 0.3):
            unassigned = [
                ticket for ticket in self.active_tickets
                if ticket['status'] != 'RESOLVED'
                and ticket['id'] not in self._assigned_tickets
            ]
            # This desk's own kind first. A preference and not a filter:
            # with nothing of its own waiting it takes what there is,
            # because somebody has to.
            unassigned = self.prefer_tickets(unassigned)
            if unassigned:
                ticket = random.choice(unassigned)
                self._assigned_tickets.add(ticket['id'])
                ticket['assigned_team'] = f"{self.username} (this position)"
                pieces.append(render_message(self.switchroom.ticket_assignment(
                    self.clock.now(), ticket['id'], ticket['title'],
                    ticket['priority'],
                    self._office_label(ticket['affected_office']),
                ), self._stamp()))

        # New work arrives. The rate falls off as the board fills, which is
        # what a finite repair force actually produces: a board that hovers
        # around a working depth rather than emptying or running away.
        depth = len(self.desk.pending())
        arrival = max(0.0, 0.45 - 0.045 * depth)
        if not self.desk.full() and random.random() < arrival:
            report = self.desk.receive(
                self.clock.now(), difficulty.commitment_slack_minutes)
            same_day = report.commitment.date() == report.received.date()
            committed = report.commitment.strftime(
                '%H:%M' if same_day else '%H:%M %a')
            pieces.append(render_message(self.switchroom.assignment(
                self.clock.now(), report.number,
                report.record.telephone_number, report.symptom, committed,
            ), self._stamp()))

        # The control centre hands out an office, once, to somebody signed
        # off to work one. This is the switching control centre
        # qualification actually paying out in work rather than in screens.
        if (self.career.may_use('connect')
                and random.random() < difficulty.interruption_rate * 0.4):
            assigned = self.scc_assignment()
            if assigned:
                pieces.append(assigned)

        # Anything at(1) queued for this minute runs now. A job the operator
        # asked for is not ambience and is not suppressed by turning ambience
        # off: they asked for it, so they get it.
        fired = self.at_due()

        # Somebody says something, at the difficulty's rate. With ambience
        # off nobody does: a message built and not shown is still filed in
        # the mailbox, which would put craft traffic into mail(1) on a
        # terminal that was told to leave you alone.
        if quiet:
            return '\n'.join(fired)
        if random.random() < difficulty.interruption_rate:
            message = self._craft_interruption(difficulty)
            if message is not None:
                pieces.append(render_message(message, self._stamp()))

        return '\n'.join(fired + pieces)

    def _craft_interruption(self, difficulty):
        """
        Return whatever one of the other craft would say right now.

        In order: a story beat that is due, then somebody asking after a
        report past its commitment, then the building. Nobody offers
        advice unasked; that is hint(1).
        """
        overdue = [
            Late(report.number, report.record.telephone_number,
                 report.record.class_of_service, report.out_of_service,
                 report.commitment.strftime('%H:%M'))
            for report in self.desk.pending() if report.overdue()]
        message = self.switchroom.next_message(
            self.clock.now(), self.career.shift, position=self.role,
            overdue=overdue, seen=self.career.beats_seen,
            recall=self._last_closed())
        if message is not None:
            ledger = self.career.beats_seen
            if message.beat:
                ledger.append(message.beat)
                if message.about:
                    ledger.append(f'about:{message.about}')
            elif message.kind == 'chase' and message.about:
                ledger.append(f'chased:{message.about}')
            elif message.kind == 'chatter':
                forget_rested(ledger, self.career.shift)
                key = chatter_key(self.career.shift, message.lines)
                if key not in ledger:
                    ledger.append(key)
            if message.beat or message.kind in ('chase', 'chatter'):
                self.career.save()
        return message

    def _last_closed(self):
        """
        The report most recently closed, for a person who speaks of it.

        One that an earlier beat already spoke of is not offered again, so
        two beats never tell the same story twice.
        """
        spoken = self.career.beats_seen
        done = [r for r in self.desk.closed()
                if not r.practical and r.closed_at
                and f'about:{r.number}' not in spoken]
        if not done:
            return None
        report = done[0]
        return Late(report.number, report.record.telephone_number,
                    report.record.class_of_service, False,
                    report.closed_at.strftime('%H:%M'))

    def _settle_people(self, quiet: bool) -> List[str]:
        """
        What the day's closed work does to how the crews feel about you.

        Each report closed this tour moves its crew's rapport one step, up
        when the code was right and down when it was not, once per person per
        tour. A correct one may bring a call back to the board later. At the
        threshold one person does a favour, once.

        The ledger (``settled:``, ``rang:``, ``favour:`` in the career's
        ``beats_seen``) is what makes each of those once across a save and a
        resume; the room keeps nothing of its own. A report closed on an
        earlier tour was settled on that tour or not at all, so it is only
        marked here, never counted: the first tour has no people, and the
        reports it closed must not move anyone in the second.
        """
        room = self.switchroom
        ledger = self.career.beats_seen
        tour = self.career.shift
        today = self.clock.tour_day()
        spoken: List[str] = []
        changed = False
        for report in self.desk.closed():
            key = f'settled:{report.number}'
            if key in ledger or report.practical:
                continue
            ledger.append(key)
            changed = True
            if report.closed_at is None or report.closed_at.date() < today:
                continue
            changed |= adjust_rapport(
                self.career.rapport, ledger,
                rapport_with(report.crew), tour, 1 if report.correct else -1)
            if (report.correct and not quiet
                    and room.rings_back(report.number, ledger)):
                closed = (report.closed_at.strftime('%H:%M')
                          if report.closed_at else '')
                self._queue_message(room.call_back(
                    self.clock.now(), report.number,
                    report.record.telephone_number,
                    report.record.class_of_service, closed),
                    after=room.rng.randint(2, 5))
        if not quiet:
            # The favour is asked at the door, so it waits until the nearest
            # report is close enough to its commitment for an hour to matter.
            login = favour_due(self.career.rapport, ledger, self.is_in)
            # A report is helped once: a second favour on it would stack an
            # hour on an hour, so one that already has its hour is passed
            # over for the next.
            waiting = sorted((r for r in self.desk.customers()
                              if not r.overdue()
                              and f'favoured:{r.number}' not in ledger),
                             key=lambda r: r.commitment)
            window = timedelta(minutes=FAVOUR_MINUTES)
            if login and waiting and waiting[0].due_in() <= window:
                target = waiting[0]
                target.commitment += timedelta(minutes=FAVOUR_MINUTES)
                self.career.beats_seen.append(f'favour:{login}')
                self.career.beats_seen.append(f'favoured:{target.number}')
                changed = True
                spoken.append(render_message(room.favour(
                    self.clock.now(), login, target.number,
                    target.commitment.strftime('%H:%M')), self._stamp()))
        if changed:
            self.career.save()
        return spoken

    def _advance_shift(self) -> List[str]:
        """
        Charge the shift for the work just done and fire anything now due.

        Returns:
            Rendered notices for events that came due, whether or not the
            caller will display them
        """
        charged = self._charged_minutes()
        was = self.shift_minutes
        self.shift_minutes += 1 + max(0, charged - self._charged_total)
        self._charged_total = charged
        late = self.desk.age(self.shift_minutes - was, was)
        late_notices = [render_message(message, self._stamp())
                        for message in self._report_late(late)]
        return (late_notices + self._weather_events(was)
                + [render_message(message, self._stamp())
                   for message in self._case_events()]
                + self._fire_due_events())

    def _pass_time(self, minutes: int) -> None:
        """
        Let shift minutes go by that nobody spent on a report.

        Waiting and asking for a hint both move the clock, and a board does
        not stop ageing because the craftsperson did. Whatever the attendant
        has to say about a commitment that passed is held for the next
        prompt, like any other message that arrives while you are busy.
        """
        was = self.shift_minutes
        self.shift_minutes += minutes
        late = self.desk.age(minutes, was)
        for message in self._report_late(late):
            self._queue_message(message, after=1)
        for notice in self._case_events():
            self._queue_message(notice, after=1)

    def _report_late(self, late) -> List[Message]:
        """
        Count reports that have just passed their commitment and say so.

        Counted here, when the commitment passes, rather than when the
        report is closed: it is missed whether or not anybody ever gets
        round to closing it. The attendant says so once per report.
        """
        if not late:
            return []
        self.career.record_missed(len(late))
        notices = []
        for report in late:
            # Missed is counted either way; said is once. A shift file that
            # was dealt again must not make her say it a second time.
            if f'chased:{report.number}' in self.career.beats_seen:
                continue
            self.career.beats_seen.append(f'chased:{report.number}')
            notices.append(self.switchroom.overdue_notice(
                self.clock.now(), report.number,
                Late(report.number, report.record.telephone_number,
                     report.record.class_of_service, report.out_of_service,
                     report.commitment.strftime('%H:%M'))))
        # The ledger is the only thing that remembers, across a quit, that
        # she has said it: written now, not at the next beat, or a resume
        # lets the board-driven chase ask the same again.
        self.career.save()
        return notices

    def _weather_events(self, was: int) -> List[str]:
        """
        Move the weather on, and let the rain get into the cable.

        Wet cable is documented as worsening with rain, and this is where
        the two are actually connected: water in an unrepaired binder group
        takes another pair, faster the harder it is raining, and that pair
        becomes a report. A sheath somebody has been to does not spread,
        which is the reward for going.
        """
        pieces: List[str] = []
        changed = self.desk.weather.advance(self.shift_minutes)
        if changed:
            pieces.append(render_message(
                self.switchroom.weather(self.clock.now(), changed),
                self._stamp()))

        elapsed = max(0, self.shift_minutes - was)
        # A first tour is one report and the wire chief. The weather still
        # turns, but the water is not allowed to take another pair and put
        # a second report on a board that is meant to hold one.
        if not elapsed or self.first_tour():
            return pieces
        plant = self.desk.plant
        spreading = plant.leak(elapsed, self.desk.weather.rain)
        for section in plant.open_sections():
            if section.alarming() and not section.alarmed:
                section.alarmed = True
                job = open_job(self.desk, section.cable, section.binder,
                               self.clock.now())
                pieces.append(render_message(self.switchroom.pressure_alarm(
                    self.clock.now(), section.cable, section.psi,
                    job.number), self._stamp()))
        for section in spreading:
            if self.desk.full():
                break
            report = self.desk.receive(
                self.clock.now(), self._difficulty().commitment_slack_minutes,
                fault='WET', section=section)
            pieces.append(render_message(self.switchroom.assignment(
                self.clock.now(), report.number,
                report.record.telephone_number, report.symptom,
                report.commitment.strftime('%H:%M'),
            ), self._stamp()))
        return pieces
    def shift_time(self) -> str:
        """Return how far into the shift the work has got, as hours:minutes."""
        return f"{self.shift_minutes // 60}:{self.shift_minutes % 60:02d}"
    def _due_events(self) -> List[Dict[str, Any]]:
        """Return the events whose time the working shift has reached."""
        reached = (tours.start_hour(self.career.shift) * 60
                   + self.shift_minutes)
        due_now = []
        for event in self.shift_events:
            if event['id'] in self._fired_events:
                continue
            try:
                hour, minute = event['time'].split(':')
                due = int(hour) * 60 + int(minute)
            except (ValueError, KeyError):
                continue
            if due <= reached:
                due_now.append(event)
        return due_now

    def settle_fired_events(self) -> None:
        """
        Make a resumed shift's fired events agree with the board it rebuilt.

        A save written before the tour script kept the old event numbers.
        Left alone, every event already due on the new board would fire at
        once as a burst, and the old numbers would sit in the set for
        nothing. Numbers that are not on the board are dropped, and what is
        already due is taken to have fired: the player has been through it.
        """
        on_board = {event['id'] for event in self.shift_events}
        self._fired_events = {fired for fired in self._fired_events
                              if fired in on_board}
        for event in self._due_events():
            self._fired_events.add(event['id'])
            if event.get('status') == 'PENDING':
                event['status'] = 'ACTIVE'

    def _fire_due_events(self) -> List[str]:
        """
        Bring shift events due as the working shift reaches their time.

        Events carry a wall-clock time because that is how a shift schedule
        was written. They are measured here against the work done rather than
        against the real-time clock, which would leave every afternoon event
        unreachable in a session anybody would actually sit through.
        """
        notices: List[str] = []
        for event in self._due_events():
            self._fired_events.add(event['id'])
            if event.get('status') == 'PENDING':
                event['status'] = 'ACTIVE'
            notices.append(render_message(self.switchroom.shift_event(
                self.clock.now(), event['id'], event['type'],
                event['title'], event['priority'], event['time'],
            ), self._stamp()))

        return notices

    def cmd_write(self, args: Optional[List[str]] = None) -> str:
        """Send a line to another craftsperson's terminal, as write(1) did."""
        args = args or []
        if not args:
            lines = [
                "write: usage: write <user> [message]",
                '',
                f"{'LOGIN':<12} {'TTY':<5} {'NAME':<16} WHERE",
                '-' * 66,
            ]
            for person in CRAFT.values():
                if not self.is_in(person.login):
                    continue
                lines.append(f"{person.login:<12} tty{person.tty:<2} "
                             f"{person.name:<16} {person.location}")
            lines.append('-' * 66)
            lines.append("Type 'who' for who is on the system.")
            return '\n'.join(lines)

        login = args[0].lower()
        found = CRAFT.get(login)
        if found is None or not self.is_in(login):
            return f"write: {args[0]} is not logged on."
        if login == 'carot':
            return ("write: CAROT is a test system, not a terminal. It prints "
                    "to you; you\ndo not write back to it.")

        if len(args) == 1:
            return (f"write: say something.\n"
                    f"Usage: write {login} <message>\n\n"
                    f"{found.name}, {found.title}, {found.location}.\n"
                    f"{found.manner}")

        reply = self._craft_reply(login)
        return (f"Message sent to {login} tty{found.tty}.\n"
                f"EOT\n\n"
                f"Message from {login} tty{found.tty} [{self._stamp()}]...\n"
                f"{reply}\nEOT")
    def _craft_reply(self, login: str) -> str:
        """Return what a craftsperson says back when written to."""
        pending = self.desk.pending()
        oldest = pending[0] if pending else None
        replies = {
            'rjohnson': [
                "Busy on the frame. If it is a pair, take it to the board.",
                "I have seen that one. Measure it before you believe it.",
            ],
            'mreyes': [
                f"You have {len(pending)} on your board. I have more coming.",
                "Tell me something I can put on the card and I will call them.",
            ],
            'dpetrak': [
                "SCC has you. Nothing outstanding from here.",
                "Keep the order wire clear, we are routining trunks this shift.",
            ],
            'lokafor': [
                "I am up a pole. Make it quick.",
                "Give me a cable and pair and I will go look at it.",
            ],
            'gvasquez': [
                "Board is yours. Send me a number and I will read it out.",
                "Capacitance is the distance. That is the whole trick.",
            ],
            'ehalloran': [
                f"Your index is {self.career.service_index():.1f}. "
                f"{self.career.index_band()}.",
                "Work what you are signed off on and nothing else.",
            ],
            'tnakamura': [
                "Everything is stated at 1004 Hz. Read it there.",
                "If a trunk is long on loss, do not put it back in service.",
            ],
        }
        pool = replies.get(login, ["Go ahead."])
        if oldest is not None and login == 'mreyes':
            pool.append(f"{oldest.number} is the one I would do first.")
        return random.choice(pool)
    def cmd_mail(self, args: Optional[List[str]] = None) -> str:
        """Read the mail the other craft have left, as mail(1) did."""
        args = args or []
        if args and args[0].lower() in ('-s', 'send'):
            return ("mail: this terminal takes mail; it does not originate "
                    "it.\nUse 'write <user>' to reach somebody now.")

        waiting = self.switchroom.take_mail()
        if not waiting:
            return "No mail."
        rendered = [f"Mail for {self.username}: {len(waiting)} message(s)", '']
        for message in waiting:
            rendered.append(render_message(
                message, message.received.strftime('%a %b %d %H:%M:%S %Y')))
            rendered.append('-' * 66)
        return '\n'.join(rendered)
    def cmd_orderwire(self, args: Optional[List[str]] = None) -> str:
        """Listen on, or speak into, the maintenance order wire."""
        args = args or []
        if not args:
            traffic = [
                message for message in self.switchroom.log
                if message.channel == 'orderwire'
            ][-6:]
            lines = [
                "Order wire - maintenance circuit",
                f"{self.home_office['clli']} to SCC_BEDMINSTER   "
                f"{self.clock.timestamp()}",
                '=' * 66,
            ]
            if not traffic:
                lines.append("Circuit quiet. Nothing on the wire.")
            else:
                for message in traffic:
                    lines.append(render_message(
                        message, message.received.strftime('%H:%M')))
            lines.extend([
                '',
                "Usage: orderwire report <what you are calling in>",
                "       orderwire scc            raise the control centre",
            ])
            return '\n'.join(lines)

        action = args[0].lower()
        if action == 'scc':
            pending = len(self.desk.pending())
            return (f"[ORDER WIRE SCC_BEDMINSTER {self._stamp()}]\n"
                    f"Petrak, SCC. Go ahead.\n\n"
                    f"You report {pending} pending and a service index of "
                    f"{self.career.service_index():.1f}.\n"
                    f"SCC acknowledges. Nothing outstanding from this end.")
        if action == 'report':
            if len(args) < 2:
                return "orderwire: say what you are reporting."
            said = ' '.join(args[1:])
            return (f"[ORDER WIRE {self.home_office['clli']} {self._stamp()}]\n"
                    f"{self.username}: {said}\n\n"
                    f"[ORDER WIRE SCC_BEDMINSTER {self._stamp()}]\n"
                    f"SCC copies. Logged against this office.")
        return ("orderwire: unknown option. Use 'orderwire', "
                "'orderwire scc' or\n'orderwire report <text>'.")
