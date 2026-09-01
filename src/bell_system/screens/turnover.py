"""
Handing the board over, and the end of a career.

A tour ends by telling whoever is relieving you what is on the board. That
is handoff(1), and it is a page and a half because a turnover record is a
page and a half. shift(1) is the same information cut down to the four
numbers you want in the middle of one rather than at the end.

Signing off banks the index, moves the calendar on four days and opens a
fresh board with whatever was still pending on it - anything past its
commitment at midnight is still past it in the morning.

Except on the thirteenth tour. A career walks four days at a time from 14
November, so the thirteenth falls on 31 December 1983 and there is no
fourteenth: signing that one off closes the career instead of opening a
board. Nothing mechanical changes about the last day, which is the point
of it, and the board is still on the machine afterwards, because the
machine did not stop on the first of January either.
"""

from typing import List, Optional, Tuple

from .. import save
from ..clock import career_progress, days_to_divestiture
from ..console import wrap
from ..constants import SHIFT_LENGTH_MINUTES
from ..npc import render as render_message
from ..progression import QUALIFICATIONS
from ..weather import Weather
from .session import SessionState

# What the last tour opens on. Nothing mechanical changes - the board is
# the same board and the work is the same work - which is the whole of the
# point. The people in the building know, and that is the only difference,
# and it is enough.
LAST_TOUR_NOTICE = (
    "This is the last working day of the Bell System.",
    "The board is the board. Nothing about the job is different today and",
    "everybody in the building knows it, which is a strange way to spend a",
    "Saturday. Work it the way you have worked the others.",
)


class TurnoverCommands(SessionState):
    """
    The turnover record, the shift summary and the end of a career.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

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
{days_to_divestiture(self.clock.now())} days to divestiture
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

        Except on the last tour, when there is no morning to carry them to.
        """
        banked = self.career.service_index()
        worked = self.shift_time()
        carried = self.desk.pending()
        summary = self.tour_summary(*self._tour_worked())
        if self.clock.last_tour(self.career.shift):
            if self.career.finished:
                return (
                    "You have been relieved. There is nobody to relieve "
                    "you twice on the last\nday of the Bell System, and "
                    "there is no shift after this one to open.\n\n"
                    "The board is still there if you want it. "
                    "'qual' has the career record.")
            return self._end_career(banked, worked, summary)
        self.career.end_shift()
        self.current_shift = self.career.shift
        # The tour that was saved is over. The next command writes the new
        # one; until then there is nothing on disk worth picking up.
        self.resumed = False
        save.discard(self.shift_file)
        # A new tour is a new day four days on, so it gets that day's
        # weather and that point of the career's board. The cable plant is
        # not redrawn: water in a sheath nobody has been to is still there
        # in the morning, which is the whole reason a sheath is worth a
        # trip.
        progress = career_progress(self.career.shift)
        self.desk.weather = Weather(self.desk.rng, wet_bias=progress)
        self.desk.depth_limit = self.board_depth()
        self._tour_baseline = self._career_counters()
        # A new tour is a new day. Four days on, until the last one.
        self.clock.set_tour(self.career.shift)

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
        ]
        # What the tour was like, before what it scored. The tally is a
        # score and a score says how you did without saying anything about
        # the work.
        if summary:
            for sentence in summary:
                lines.extend(f"  {line}" for line in wrap(sentence, 64))
            lines.append('')
        lines.extend([
            f"  Service index banked      {banked:.1f}  "
            f"{self.career.index_band()}",
            f"  Reports closed to date    {self.career.reports_closed}",
            f"  Carried forward           {len(carried)}",
            f"  New on the board          {len(opened)}",
            f"  Shift events              {len(self.shift_events)} scheduled",
            '',
            f"Shift {self.career.shift} begins. "
            f"{len(self.desk.pending())} pending. "
            f"{self.clock.date()}.",
        ])
        if self.career.index_history:
            trend = self.sparkline(self.career.index_history, span=8)
            recent = ', '.join(f"{entry:.1f}"
                               for entry in self.career.index_history[-8:])
            lines.append(f"  Index history             {recent}"
                         + (f"  {trend}" if trend else ''))
        granted = self._grant_qualifications()
        if granted:
            lines.append('')
            lines.extend(granted)
        if self.clock.last_tour(self.career.shift):
            lines.append('')
            lines.extend(LAST_TOUR_NOTICE)
        return '\n'.join(lines)

    def _end_career(self, banked: float, worked: str,
                    summary: List[str]) -> str:
        """
        The end of the last tour, which is the end of the Bell System.

        Nothing new opens. There is no fourteenth tour to carry a board
        into and the index is not banked against a shift that will never
        be worked, so this is an account of the career rather than a
        turnover record - and then the terminal is still there, because
        the machine did not stop on the first of January either.
        """
        career = self.career
        career.index_history.append(round(banked, 1))
        career.finished = True
        career.save()
        self.resumed = False
        save.discard(self.shift_file)

        lines = [
            f"Relieved. Tour {career.shift} closed after {worked} worked.",
            '=' * 66,
        ]
        for sentence in summary:
            lines.extend(f"  {line}" for line in wrap(sentence, 64))
        lines.extend([
            '',
            'THE CAREER',
            '-' * 66,
            f"  Tours worked        {career.shift}",
            f"  Reports closed      {career.reports_closed} "
            f"({career.reports_correct} correct, "
            f"{career.reports_wrong} wrong)",
            f"  Came back           {career.repeat_reports}",
            f"  Missed commitments  {career.missed_commitments}",
            f"  Service index       {banked:.1f}  {career.index_band()}",
            f"  Signed off on       {len(career.qualifications)} of "
            f"{len(QUALIFICATIONS)}",
        ])
        trend = self.sparkline(career.index_history, span=13)
        if trend:
            lines.append(f"  Every tour of it    {trend}")
        lines.extend(['', render_message(self.switchroom.last_word(
            self.clock.now(), career.shift, career.reports_closed,
            len(career.qualifications)), self._stamp())])
        lines.append("The board is still on the machine. Nobody is coming "
                     "to take it off you tonight.")
        return '\n'.join(lines)

    def _career_counters(self) -> Tuple[int, int, int, int]:
        """Snapshot the four counters a tour is judged on."""
        career = self.career
        return (career.reports_closed, career.reports_correct,
                career.missed_commitments, career.repeat_reports)

    def _tour_worked(self) -> Tuple[int, int, int, int]:
        """Return closed, correct, missed and repeats for this tour alone."""
        now = self._career_counters()
        closed, correct, missed, repeats = (
            current - was for current, was in zip(now, self._tour_baseline))
        return closed, correct, missed, repeats

    def cmd_shift(self, args: Optional[List[str]] = None) -> str:
        """
        Where you are in the tour.

        The handoff record is a page and a half and it is for handing the
        board over. This is the four numbers you want in the middle of a
        tour: how far in you are, what is due, what has not been touched,
        and who is out. It fits on a screen.
        """
        del args
        pending = self.desk.pending()
        overdue = [report for report in pending if report.overdue()]
        untested = [report for report in pending if not report.tested]
        with_field = [report for report in pending if report.dispatched_to]
        now = self.clock.now()
        left = max(0, SHIFT_LENGTH_MINUTES - self.shift_minutes)
        closed, correct, missed, repeats = self._tour_worked()

        rows = [
            f"Tour {self.career.shift}   {self.clock.date(now)}   "
            f"{days_to_divestiture(now)} days to divestiture",
            '=' * 62,
            f"  Worked              {self.shift_time()} of "
            f"{SHIFT_LENGTH_MINUTES // 60}:00",
            f"  Left                {left // 60}:{left % 60:02d}",
            '',
            f"  On the board        {len(pending)}",
            f"  Past commitment     {len(overdue)}",
            f"  Not yet measured    {len(untested)}",
            f"  Out with the field  {len(with_field)}",
            '',
            f"  Closed this tour    {closed} "
            f"({correct} correct, {closed - correct} wrong)",
            f"  Missed commitments  {missed}",
            f"  Came back           {repeats}",
        ]
        soonest = pending[0] if pending else None
        if soonest is not None:
            rows.extend([
                '',
                f"  Nearest commitment  {soonest.number}  "
                f"{soonest.age_label()} "
                f"{'past' if soonest.overdue() else 'remaining'}",
            ])
        busy = self.desk.force.busy(now)
        if busy:
            rows.extend(['', 'OUT NOW', '-' * 62])
            for job in busy:
                rows.append(f"  {job.crew.name:<16}{job.report:<11}"
                            f"back about "
                            f"{self.clock.time(job.back_at())}")
        rows.extend(['', "'handoff' is the full turnover record. "
                         "'handoff relieve' signs off."])
        return '\n'.join(rows)

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
