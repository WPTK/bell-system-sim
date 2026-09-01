"""
The working shift: its clock, its events, and the other craft on the wire.
"""
from ..constants import BELL_SYSTEM_ROLES, SHIFT_LENGTH_MINUTES
import random
from collections import (
    deque,
)
from typing import (
    List,
    Optional,
)
from ..data.shift_events import build as build_shift_events
from ..npc import (
    CRAFT,
    Message,
    render as render_message,
)
from ..progression import (
    QUALIFICATIONS,
)
from ..settings import (
    EPOCH_HOUR,
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
    def generate_shift_events(self) -> None:
        """
        Put the shift's scheduled work, tests and known conditions on the
        board.

        The catalogue is reference data and lives in data/shift_events.py;
        what is here is when to ask for it. Re-run at every shift change,
        which is why it is safe to call again once a position is taken.
        """
        self.shift_events = build_shift_events(
            self.clock.now().hour, self.clock.now().month)
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
        # Find the role name for display
        role_name = "Unknown Role"
        for role_id, (role_key, name) in BELL_SYSTEM_ROLES.items():
            if role_key == self.role:
                role_name = name
                break
        self.emit(f"Role: {role_name}")
        self.emit(f"{'='*60}")

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
                      f"({oldest.record.telephone_number}) in "
                      f"{oldest.age_label()}")
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
        hour = self.clock.now().hour
        if 8 <= hour < 16:
            return "Day Shift (08:00-16:00)"
        elif 16 <= hour < 24:
            return "Evening Shift (16:00-24:00)"
        else:
            return "Night Shift (24:00-08:00)"
    def cmd_handoff(self, args: List[str]) -> str:
        """Bell System shift handoff briefing and turnover record."""
        previous = self.shift_handoff["previous_shift"]
        pending_reports = self.desk.pending()
        overdue_reports = [r for r in pending_reports if r.overdue()]
        untested_reports = [r for r in pending_reports if not r.tested]
        open_now = [t for t in self.active_tickets if t['status'] != 'RESOLVED']
        critical = [t for t in open_now if t['priority'] == 'CRITICAL']
        unacknowledged = [a for a in self.active_alarms if not a['acknowledged']]

        output = f"""Bell System Shift Handoff Record
{self.clock.now().strftime('%B %d, %Y %H:%M EST')}
{'=' * 50}

INCOMING FROM PREVIOUS SHIFT
{'=' * 40}
Operator:                 {previous['operator']}
Shift Ended:              {previous['end_time']}
Summary:                  {previous['summary']}
System Status:            {previous['system_status']}

Key Issues Carried Forward:"""
        for issue in previous['key_issues']:
            output += f"\n  - {issue}"

        output += f"""

Tickets Transferred:      {', '.join(previous['open_tickets'])}

Special Instructions:
  {previous['special_instructions']}

CURRENT SHIFT POSITION
{'=' * 40}
Operator On Duty:         {self.username}
Role:                     {self.role_name or 'Unassigned'}
Shift Number:             {self.career.shift}
Time Worked:              {self.shift_time()} of \
{SHIFT_LENGTH_MINUTES // 60}:00
Commands This Session:    {len(self.command_history)}

Open Trouble Tickets:     {len(open_now)}
  Critical:               {len(critical)}
Unacknowledged Alarms:    {len(unacknowledged)}
Overall Health:           {self.system_health['overall_status']}

REPAIR SERVICE BUREAU
{'=' * 40}
Reports Pending:          {len(pending_reports)}
  Past Commitment:        {len(overdue_reports)}
  Not Yet Measured:       {len(untested_reports)}
Closed This Session:      {len(self.desk.closed())}
Board Moved:              {len(self.desk.closed()) - len(pending_reports):+d} \
reports
Service Index:            {self.career.service_index():.1f} \
({self.career.index_band()})
{self._measure_note()}
Qualifications Held:      {len(self.career.qualifications)} of \
{len(QUALIFICATIONS)}
{self._tour_account()}
"""

        if pending_reports:
            output += ("\nREPORTS CARRIED TO THE NEXT SHIFT\n" + "=" * 40)
            for report in pending_reports[:6]:
                output += (
                    f"\n{report.number}: {report.record.telephone_number}"
                    f"\n  Customer states:    {report.symptom}"
                    f"\n  Commitment:         "
                    f"{report.commitment.strftime('%H:%M %a %b %d')}"
                    f" ({report.age_label()}"
                    f" {'past' if report.overdue() else 'remaining'})"
                    f"\n  Measured:           "
                    f"{'yes' if report.tested else 'NO'}")

        if critical:
            output += "\nCRITICAL TICKETS REQUIRING HANDOFF\n" + "=" * 40
            for ticket in critical:
                output += f"""
{ticket['id']}: {ticket['title']}
  Office:             {self._office_label(ticket['affected_office'])}
  Assigned:           {ticket['assigned_team']}
  Customers Affected: {ticket['customer_impact']:,}"""

        output += f"""

TURNOVER CHECKLIST
{'=' * 40}
  [ ] Review all open trouble tickets with relieving operator
  [ ] Transfer unacknowledged alarms
  [ ] Confirm maintenance windows in progress
  [ ] Record special instructions in the shift log
  [ ] Verify emergency contact roster is current
  [ ] Hand the board over with every commitment stated

Reference: BSP 010-100-000 (Shift Turnover Procedures)

Type 'handoff relieve' to sign off. The service index is banked against
this shift and the next one starts on a fresh board."""

        if args and args[0].lower() in ('relieve', 'signoff', 'end'):
            return self._end_shift()
        return output
    def _end_shift(self) -> str:
        """
        Sign off: bank the index, advance the shift, and start a new board.

        Reports left pending are carried forward, because they were. Anything
        past commitment is still past commitment in the morning.
        """
        banked = self.career.service_index()
        worked = self.shift_time()
        carried = self.desk.pending()
        self.career.end_shift()
        self.current_shift = self.career.shift

        # A new shift starts with its own clock and its own schedule.
        self.shift_minutes = 0
        self._charged_total = sum(report.desk_minutes
                                  for report in self.reports_all())
        self._fired_events = set()
        self.generate_shift_events()

        difficulty = self._difficulty()
        opened = self.desk.open_shift(
            self.clock.now(), difficulty.commitment_slack_minutes)

        lines = [
            f"Relieved. Shift {self.career.shift - 1} closed after "
            f"{worked} worked.",
            '=' * 66,
            f"  Service index banked      {banked:.1f}  "
            f"{self.career.index_band()}",
            f"  Reports closed to date    {self.career.reports_closed}",
            f"  Carried forward           {len(carried)}",
            f"  New on the board          {len(opened)}",
            f"  Shift events              {len(self.shift_events)} scheduled",
            '',
            f"Shift {self.career.shift} begins. "
            f"{len(self.desk.pending())} pending.",
        ]
        if self.career.index_history:
            lines.append('  Index history             '
                         + ', '.join(f"{entry:.1f}"
                                     for entry in
                                     self.career.index_history[-8:]))
        granted = self._grant_qualifications()
        if granted:
            lines.append('')
            lines.extend(granted)
        return '\n'.join(lines)
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
    def _queue_message(self, message, after: int) -> None:
        """Hold a message back so it lands a few commands from now."""
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
        Advance the shift and return whatever the building has to say.

        Called after every command. The shift clock, new work arriving and
        tickets being assigned are simulation state and happen regardless;
        the ambience setting governs only whether anybody tells you about
        them. Interruption rate is the difficulty's: a shift on the forgiving
        setting is quiet, a shift on the other one is not.
        """
        if getattr(self, '_in_pipeline', False):
            # A pipeline's stages are one command; the pipeline charges for
            # itself once it finishes.
            return ''

        quiet = not self.settings.is_on('game.ambience')
        difficulty = self._difficulty()
        pieces = self._advance_shift()
        if not quiet:
            pieces = self._drain_queue() + pieces

        # A first tour is one report and the wire chief. Work still arrives
        # at the bureau; it is held off this board until the first one is
        # closed, which is what the chief says he is doing. Everything the
        # building would otherwise say waits with it - four people talking
        # over a walkthrough is how a new craftsperson stops playing.
        if self.first_tour():
            return '\n'.join(self.at_due() + ([] if quiet else pieces))

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

        # Somebody says something, at the difficulty's rate.
        if random.random() < difficulty.interruption_rate:
            message = self._craft_interruption(difficulty)
            if message is not None:
                pieces.append(render_message(message, self._stamp()))

        if quiet:
            return '\n'.join(fired)
        return '\n'.join(fired + pieces)
    def _craft_interruption(self, difficulty):
        """
        Return whatever one of the other craft would say right now.

        A report past its commitment gets chased first, because that is what
        would actually happen. Otherwise it is advice on the forgiving
        setting and ordinary building noise on either.
        """
        now = self.clock.now()
        pending = self.desk.pending()
        overdue = [report for report in pending if report.overdue()]
        untested = [report for report in pending if not report.tested]
        roll = random.random()

        if overdue and roll < 0.45:
            target = random.choice(overdue)
            return self.switchroom.chase(
                now, target.number, target.record.telephone_number)
        if untested and roll < 0.60 and not difficulty.require_test_before_close:
            return self.switchroom.hint(now)
        if untested and roll < 0.50:
            return self.switchroom.hint(now)
        return self.switchroom.chatter(now, position=self.role)
    def _advance_shift(self) -> List[str]:
        """
        Charge the shift for the work just done and fire anything now due.

        Returns:
            Rendered notices for events that came due, whether or not the
            caller will display them
        """
        charged = sum(report.desk_minutes
                      for report in self.reports_all())
        was = self.shift_minutes
        self.shift_minutes += 1 + max(0, charged - self._charged_total)
        self._charged_total = charged
        return self._weather_events(was) + self._fire_due_events()

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
        if not elapsed:
            return pieces
        spreading = self.desk.plant.spread(elapsed, self.desk.weather.rain)
        for _ in range(spreading):
            if self.desk.full():
                break
            report = self.desk.receive(
                self.clock.now(), self._difficulty().commitment_slack_minutes,
                fault='WET')
            pieces.append(render_message(self.switchroom.assignment(
                self.clock.now(), report.number,
                report.record.telephone_number, report.symptom,
                report.commitment.strftime('%H:%M'),
            ), self._stamp()))
        return pieces
    def shift_time(self) -> str:
        """Return how far into the shift the work has got, as hours:minutes."""
        return f"{self.shift_minutes // 60}:{self.shift_minutes % 60:02d}"
    def _fire_due_events(self) -> List[str]:
        """
        Bring shift events due as the working shift reaches their time.

        Events carry a wall-clock time because that is how a shift schedule
        was written. They are measured here against the work done rather than
        against the real-time clock, which would leave every afternoon event
        unreachable in a session anybody would actually sit through.
        """
        reached = EPOCH_HOUR * 60 + self.shift_minutes
        notices: List[str] = []
        for event in self.shift_events:
            if event['id'] in self._fired_events:
                continue
            try:
                hour, minute = event['time'].split(':')
                due = int(hour) * 60 + int(minute)
            except (ValueError, KeyError):
                continue
            if due > reached:
                continue

            self._fired_events.add(event['id'])
            if event.get('status') == 'PENDING':
                event['status'] = 'ACTIVE'
            notices.append(render_message(self.switchroom.shift_event(
                self.clock.now(), event['id'], event['type'],
                event['title'], event['priority'], event['time'],
            ), self._stamp()))

        if (self.shift_minutes >= SHIFT_LENGTH_MINUTES
                and 'SHIFT-END' not in self._fired_events):
            self._fired_events.add('SHIFT-END')
            notices.append(self._shift_over_notice())
        return notices
    def _shift_over_notice(self) -> str:
        """Return the wire chief telling you your eight hours are up."""
        pending = len(self.desk.pending())
        overdue = sum(1 for report in self.desk.pending() if report.overdue())
        return render_message(Message(
            channel='write', sender='ehalloran', received=self.clock.now(),
            lines=[
                'That is eight hours.',
                f'{pending} still on your board, {overdue} past commitment.',
                "'handoff relieve' when you are ready to sign off.",
            ],
            kind='shift', subject='End of shift', about=None,
        ), self._stamp())
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
                lines.append(f"{person.login:<12} tty{person.tty:<2} "
                             f"{person.name:<16} {person.location}")
            lines.append('-' * 66)
            lines.append("Type 'who' for who is on the system.")
            return '\n'.join(lines)

        login = args[0].lower()
        found = CRAFT.get(login)
        if found is None:
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
                "Keep the order wire clear, we are routining trunks tonight.",
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

    def _measure_note(self) -> str:
        """
        What this desk is judged on, indented under the index.

        The service index scores how you closed reports, not how many, and
        for eight of the twelve positions it does not describe the work at
        all. This says which of those is true here.
        """
        indent = ' ' * 26
        rows = ['Scores how you closed them, not how many.',
                'A tour that closes five perfectly reads',
                'the same as one that closes thirty.']
        rows.extend(self.position_measure())
        return '\n'.join(indent + line for line in rows)

    def _tour_account(self) -> str:
        """
        A plain account of what this tour consisted of.

        Deliberately a tally and not a second score. A number printed
        beside the index would be read as another thing to optimise, and
        most of these are not things to optimise - they are what the desk
        spent the night on.
        """
        tally = self.position_tally()
        if not tally:
            return ''
        rows = ['', f"WHAT THIS DESK DID - {self.position.name}", '=' * 40]
        for label, value in tally:
            rows.append(f"{label + ':':<32}{value}")
        rows.append('')
        rows.append("Not scored. It is what the tour consisted of.")
        return '\n'.join(rows)
