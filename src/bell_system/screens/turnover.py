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

from typing import Dict, List, NamedTuple, Optional, Tuple

from .. import save
from ..clock import career_progress, days_to_divestiture
from ..console import wrap
from ..constants import SHIFT_LENGTH_MINUTES
from ..npc import (
    AUDIT_EXCEPTIONS,
    AUDIT_FAILED,
    AUDIT_PASSED,
    render as render_message,
)
from ..progression import QUALIFICATIONS
from ..reports import hours_minutes
from ..verbs import control_standing
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


# The memo of 1 November says only that disposition codes "are audited after
# transfer" and that open reports go over "with your name on them". How an
# audit would weigh a record is not in any document consulted, so the
# thresholds below are the simulation's own. Ten per cent of dispositions
# not matching the line is a finding; a quarter is a failure.
AUDIT_FINDING_RATE = 0.10
AUDIT_FAILURE_RATE = 0.25


class Audit(NamedTuple):
    """What the audit at the end of the last tour found."""

    closed: int
    correct: int
    wrong: int
    repeats: int
    open_numbers: List[str]
    late: int
    verdict: str
    reasons: List[str]


def audit(closed: int, wrong: int, repeats: int,
          open_numbers: List[str], late: int) -> Audit:
    """
    Judge a career's dispositions and the board it hands over.

    Reads counts only, the same ones ``report closed`` ends on and the board
    as it stands, so the audit cannot disagree with either. It gives a
    verdict and the words that go with it. It never ends the career: the
    thirteenth tour closes it on 31 December whatever this says.

    Args:
        closed: Reports closed over the career
        wrong: How many did not match what was on the line. Read from the
            career's own count and held between none and all of them, so a
            damaged record cannot make the audit's figures negative
        repeats: Reports that came back after a wrong close. Shown, not
            weighed: the verdict reads dispositions and the board
        open_numbers: Reports on the board at transfer, which go over with
            the craftsperson's name on them
        late: How many of those are past their commitment
    """
    wrong = max(0, min(wrong, closed))
    rate = wrong / closed if closed else 0.0
    failed: List[str] = []
    findings: List[str] = []
    if not closed:
        failed.append("Nothing was closed, so there is no disposition to "
                      "stand behind and the board goes over as you left it.")
    if closed and rate > AUDIT_FAILURE_RATE:
        failed.append(f"{wrong} of {closed} dispositions did not match "
                      f"the line.")
    if closed and late > closed:
        failed.append(f"More went over past commitment ({late}) than you "
                      f"closed ({closed}).")
    if AUDIT_FINDING_RATE < rate <= AUDIT_FAILURE_RATE:
        findings.append(f"{wrong} of {closed} dispositions did not match "
                        f"the line.")
    if late and not failed:
        findings.append(f"{late} went over past commitment.")
    if failed:
        verdict, reasons = AUDIT_FAILED, failed
    elif findings:
        verdict, reasons = AUDIT_EXCEPTIONS, findings
    elif wrong:
        verdict, reasons = AUDIT_PASSED, [
            f"{wrong} of {closed} did not match the line, inside what the "
            f"audit lets stand."]
    else:
        verdict, reasons = AUDIT_PASSED, [
            "Every disposition on record matched the line."]
    return Audit(closed, closed - wrong, wrong, repeats, open_numbers, late,
                 verdict, reasons)


class TurnoverCommands(SessionState):
    """
    The turnover record, the shift summary and the end of a career.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    def cmd_handoff(self, args: List[str]) -> str:
        """Bell System shift handoff briefing and turnover record."""
        previous = self.shift_handoff["previous_shift"]
        pending_reports = self.desk.customers()
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
{self._goal_section(final=False)}"""

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
            if not self._tour_has_work():
                return self._nothing_to_hand_over()
            return self._end_shift()
        if self.clock.last_tour(self.career.shift):
            found = self.stored_audit()
            if found is not None:
                lines = self.audit_lines(found, final=True)
            elif not self.career.finished:
                lines = self.audit_lines(self.career_audit(), final=False)
            else:
                lines = []
            if lines:
                output += '\n\n' + '\n'.join(lines)
        return output

    def stored_audit(self) -> Optional[Audit]:
        """
        The audit the career was signed off with, or None before that.

        Read from what ``_end_career`` kept, so the last day can be read
        again once it is over. The verdict is the stored one; the figures
        beside it are the career's own, which no longer move.
        """
        career = self.career
        if not career.finished or not career.audit_verdict:
            return None
        found = audit(career.reports_closed, career.reports_wrong,
                      career.repeat_reports, list(career.audit_open),
                      career.audit_late)
        return found._replace(verdict=career.audit_verdict)

    def career_audit(self) -> Audit:
        """
        The audit of the career as it stands.

        The figures are the ones ``report closed`` ends on, and the open
        board is the one ``report`` shows, so the three agree.
        """
        pending = self.desk.customers()
        career = self.career
        return audit(career.reports_closed, career.reports_wrong,
                     career.repeat_reports,
                     [report.number for report in pending],
                     sum(1 for report in pending if report.overdue()))

    def audit_lines(self, found: Audit, final: bool) -> List[str]:
        """
        The audit as printed.

        Args:
            found: What :meth:`career_audit` returned
            final: False for the look ahead the handoff gives on the last
                day, which can still be changed by working the board
        """
        heading = 'THE AUDIT' if final else 'THE AUDIT, AS THINGS STAND'
        rows = [
            heading,
            '-' * 66,
            f"  Dispositions on record   {found.closed}",
            f"    matched the line       {found.correct}",
            f"    did not match          {found.wrong}",
            f"  Came back as repeats     {found.repeats}",
            f"  Handed over open         {len(found.open_numbers)}"
            + (f", {found.late} past commitment" if found.late else ''),
        ]
        if found.open_numbers:
            shown = ', '.join(found.open_numbers[:6])
            more = len(found.open_numbers) - 6
            rows.append(f"    your name is on them   {shown}"
                        + (f" and {more} more" if more > 0 else ''))
        if final:
            rows.append(f"  Verdict                  {found.verdict}")
            for reason in found.reasons:
                rows.extend(f"    {line}" for line in wrap(reason, 60))
        else:
            # The board is aged by the hours nobody worked before the audit
            # reads it, so a verdict given now could be taken back. The
            # counts are shown and the verdict waits for sign-off.
            rows.append("  Verdict                  struck at sign-off")
            rows.append("    Unworked time will still age the board first.")
        rows.append("  The memo says dispositions are audited and open "
                    "reports go over with")
        rows.append("  your name on them. How the audit weighs them is the "
                    "simulation's own.")
        if not final:
            rows.append("  Working the board changes these. Nothing here "
                        "ends the career early.")
        return rows

    def _audit_again(self) -> str:
        """The stored audit as text to append, or nothing before sign-off."""
        found = self.stored_audit()
        if found is None:
            return ''
        return '\n\n' + '\n'.join(self.audit_lines(found, final=True))

    def goal_counts(self) -> Dict[str, int]:
        """
        Read off the figures a tour's goals ask about.

        The tour's own tally, and the board as it stands. Reading only: a
        goal is never a reason for anything to change, and never moves the
        index.
        """
        closed, correct, missed, repeats = self._tour_worked()
        pending = self.desk.customers()
        return {
            'closed': closed, 'correct': correct, 'wrong': closed - correct,
            'missed': missed, 'repeats': repeats, 'carried': len(pending),
            'late': sum(1 for report in pending if report.overdue()),
            'unmeasured': sum(1 for report in pending if not report.tested),
        }

    def goal_lines(self, final: bool) -> List[str]:
        """
        The tour's goals, each marked met or missed.

        Args:
            final: Whether the tour is being handed over. Until it is, a
                goal is shown as it stands and may still go either way.
        """
        entry = self.tour_script()
        if entry is None:
            return []
        counts = self.goal_counts()
        rows = []
        for goal in entry.goals:
            if final:
                met = goal.met(counts)
                verdict = 'met' if met else 'missed'
            else:
                # Unworked time ages the board before the tour is struck, so
                # nothing is ticked until it is. A blank box would read as
                # missed, so the preview marks every goal as undecided.
                met = False
                verdict = f"so far {counts[goal.metric]}"
            box = 'x' if met else ('?' if not final else ' ')
            rows.append(f"  [{box}] {goal.text:<46}{verdict}")
        if not final:
            rows.append("  [?] judged at sign-off. Unworked time will still "
                        "age the board at handoff.")
        return rows

    def _goal_section(self, final: bool) -> str:
        """The goals under their heading, or nothing on a tour with none."""
        rows = self.goal_lines(final)
        if not rows:
            return ''
        return '\n'.join(['TOUR GOALS', '=' * 40, *rows,
                          'Not scored. The service index is the only score.',
                          ''])

    def _tour_has_work(self) -> bool:
        """
        Whether there is anything to hand over a record of.

        A tour has something to show for it once a report has been worked
        (a measurement, a dispatch, a call, a close: anything that charged
        the desk) or once the board has been read. Thirteen sign-offs typed
        one after another ended a career in a second with a perfect record
        and forty-seven reports nobody had looked at, and the handoff is
        exactly the place that cannot be taken without having looked.
        """
        return (self._board_reviewed
                or self._charged_total > self._tour_desk_start
                or self._tour_worked()[0] > 0)

    def _nothing_to_hand_over(self) -> str:
        """Refuse a sign-off on a tour nobody has done anything in."""
        pending = len(self.desk.customers())
        if pending:
            on_it = ('there is 1 report' if pending == 1
                     else f"there are {pending} reports")
            return (
                "Nothing to hand over: you have not looked at the board "
                f"or worked anything this tour, and {on_it} on it.\n\n"
                "Read it with 'report' (or 'report next' for the one to do "
                "first), work what you can, then 'handoff relieve' again.")
        return ("Nothing to hand over: the board is clear and you have not "
                "looked at it this tour.\n\n"
                "Read it with 'report', then 'handoff relieve' again.")

    def _end_shift(self) -> str:
        """
        Sign off: bank the index, advance the shift, and start a new board.

        Reports left pending are carried forward, because they were. Anything
        past commitment is still past commitment in the morning.

        Except on the last tour, when there is no morning to carry them to.
        """
        # The rest of the tour goes by with the board as you leave it. Reports
        # nobody worked pass their commitments in the hours left, and the
        # index you bank is the one for the board you are handing over.
        left = max(0, SHIFT_LENGTH_MINUTES - self.shift_minutes)
        # A practical is this tour's. It does not go on the board of the next.
        self._abandon_practical()
        late = self.desk.new_tour(left, self.shift_minutes)
        if late:
            self.career.record_missed(len(late))
        banked = self.career.service_index() if self.career.scored() else None
        worked = self.shift_time()
        carried = self.desk.pending()
        summary = self.tour_summary(*self._tour_worked())
        goals = self._goal_section(final=True)
        if self.clock.last_tour(self.career.shift):
            if self.career.finished:
                return (
                    "You have been relieved. There is nobody to relieve "
                    "you twice on the last\nday of the Bell System, and "
                    "there is no shift after this one to open.\n\n"
                    "The board is still there if you want it. "
                    "'qual' has the career record."
                    + self._audit_again())
            return self._end_career(banked, worked, summary, goals)
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
        self._tour_desk_start = self._charged_total
        self._board_reviewed = False
        self._fired_events = set()
        self.generate_shift_events()

        difficulty = self._difficulty()
        opened = self.desk.open_shift(
            self.clock.now(), difficulty.commitment_slack_minutes)

        past = sum(1 for report in carried if report.overdue())
        carried_late = f", {past} past commitment" if past else ''
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
        if goals:
            lines.extend([goals, ''])
        lines.extend([
            f"  Service index banked      {self._banked_line(banked)}",
            f"  Reports closed to date    {self.career.reports_closed}",
            f"  Carried forward           {len(carried)}{carried_late}",
            f"  New on the board          {len(opened)}",
            f"  Shift events              {len(self.shift_events)} scheduled",
            '',
            f"Shift {self.career.shift} begins. "
            f"{len(self.desk.customers())} pending. "
            f"{self.clock.date()}.",
        ])
        if self.career.index_history:
            trend = self.sparkline(self.career.index_history, span=8)
            recent = ', '.join(f"{entry:.1f}"
                               for entry in self.career.index_history[-8:])
            lines.append(f"  Index history             {recent}"
                         + (f"  {trend}" if trend else ''))
        offered = self._offer_qualifications()
        if offered:
            lines.append('')
            lines.extend(offered)
        if self.clock.last_tour(self.career.shift):
            lines.append('')
            lines.extend(LAST_TOUR_NOTICE)
        return '\n'.join(lines)

    def _banked_line(self, banked: Optional[float]) -> str:
        """The index as banked, or why there is not one."""
        if banked is None:
            return "none yet: nothing closed, nothing past commitment"
        return f"{banked:.1f}  {self.career.index_band()}"

    def _end_career(self, banked: Optional[float], worked: str,
                    summary: List[str], goals: str = '') -> str:
        """
        The end of the last tour, which is the end of the Bell System.

        Nothing new opens. There is no fourteenth tour to carry a board
        into and the index is not banked against a shift that will never
        be worked, so this is an account of the career rather than a
        turnover record - and then the terminal is still there, because
        the machine did not stop on the first of January either.
        """
        career = self.career
        if banked is not None:
            career.index_history.append(round(banked, 1))
        found = self.career_audit()
        career.audit_verdict = found.verdict
        career.audit_open = list(found.open_numbers)
        career.audit_late = found.late
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
        if goals:
            lines.extend(['', goals])
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
            f"  Service index       {self._banked_line(banked)}",
            f"  Signed off on       {len(career.qualifications)} of "
            f"{len(QUALIFICATIONS)}",
        ])
        trend = self.sparkline(career.index_history, span=13)
        if trend:
            lines.append(f"  Every tour of it    {trend}")
        lines.extend(['', *self.audit_lines(found, final=True)])
        lines.extend(['', render_message(self.switchroom.last_word(
            self.clock.now(), career.shift, career.reports_closed,
            len(career.qualifications), found.verdict), self._stamp())])
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
        pending = self.desk.customers()
        overdue = [report for report in pending if report.overdue()]
        untested = [report for report in pending if not report.tested]
        with_field = [report for report in pending if report.dispatched_to]
        now = self.clock.now()
        left = max(0, SHIFT_LENGTH_MINUTES - self.shift_minutes)
        closed, correct, missed, repeats = self._tour_worked()
        brief = self.tour_brief(self.goal_counts())

        rows = [
            f"Tour {self.career.shift}   {self.clock.date(now)}   "
            f"{days_to_divestiture(now)} days to divestiture",
            '=' * 62,
            *brief,
            *([''] if brief else []),
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
        busy = self.desk.force.busy(self.shift_minutes)
        if busy:
            rows.extend(['', 'OUT NOW', '-' * 62])
            for job in busy:
                rows.append(f"  {job.crew.name:<16}{job.report:<11}"
                            f"back in "
                            f"{hours_minutes(job.back_at() - self.shift_minutes)}")
        standing = control_standing(self.desk)
        if standing:
            rows.extend(['', standing])
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
