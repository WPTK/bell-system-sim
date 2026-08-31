"""
The repair service bureau board and the craft record.
"""

import random
from collections import (
    deque,
)
from typing import (
    List,
    Optional,
)
from ..data.clli import (
    STATE_CODES,
)
from ..data.trouble import (
    DISPATCH_FORCES,
    DISPOSITIONS,
    FAULTS,
    NSPMP_CATEGORIES,
    NSPMP_WEIGHTS,
)
from ..lmos import LmosConsole
from ..npc import (
    Switchroom,
    render as render_message,
)
from ..progression import (
    MISSED_COMMITMENT_WEIGHT,
    QUALIFICATIONS,
    QUALIFICATIONS_BY_KEY,
    REPEAT_REPORT_WEIGHT,
    WRONG_DISPOSITION_WEIGHT,
)
from ..reports import (
    CLASSES_OF_SERVICE,
    COST_CALLBACK,
    ReportDesk,
    disposition_name,
    valid_force,
)
from ..special_services import (
    SartsConsole,
    SartsInventory,
)


from .session import SessionState


class BureauCommands(SessionState):
    """
    The repair service bureau board and the craft record.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`,
    which owns the session state these read.
    """

    def _initialize_repair_bureau(self) -> None:
        """
        Stand up the report board, the other craft, and the home wire centre.

        The wire centre is chosen from the geographic data already loaded so
        the reports the desk generates carry a numbering plan area and a
        COMMON LANGUAGE code that belong together.
        """
        home = None
        for office in self.central_offices.values():
            if office['npa'] in ('201', '212', '203'):
                home = office
                break
        if home is None and self.central_offices:
            home = next(iter(self.central_offices.values()))

        if home is None:
            npa, nxx, city, state, switch_type = '201', '555', 'Newark', 'NJ', '1ESS'
        else:
            npa = home['npa']
            nxx = home['nxx']
            city = home['city']
            state = home['state']
            switch_type = home['switch_type']

        self.home_office = {
            'npa': npa, 'nxx': nxx, 'city': city,
            'state': STATE_CODES.get(state, state),
            'switch_type': switch_type,
            'clli': self._office_clli(city, state, switch_type) or 'NWRKNJ02',
        }

        self.desk = ReportDesk(npa, nxx, self.home_office['clli'])
        self.switchroom = Switchroom()
        self.special_services = SartsInventory(self.home_office['clli'])
        self.lmos_console = LmosConsole(self)
        self.sarts_console = SartsConsole(self)
        self._queued_messages: deque = deque()
        self._assigned_tickets: set = set()

        # Minutes of the working shift consumed. The simulated clock runs in
        # real time, so a shift's events would never come due inside a
        # session if they waited on it. They come due on the work instead:
        # every command costs a minute at the terminal, and everything
        # charged against a report is charged against the shift too.
        self.shift_minutes = 0
        self._charged_total = 0
        self._fired_events: set = set()

        slack = self.career.difficulty.commitment_slack_minutes
        self.desk.open_shift(self.clock.now(), slack)
    def _difficulty(self):
        """Return the active difficulty profile."""
        return self.career.difficulty
    def reports_all(self):
        """Return every report the desk has seen this session."""
        return list(self.desk.reports.values())
    def _qualification_block(self, command: str) -> Optional[str]:
        """
        Return the wire chief's refusal when a command is not signed off.

        Qualification governed what a craftsperson was allowed to work on, so
        an unqualified command is refused by a person rather than reported as
        a missing binary.
        """
        needed = self.career.qualification_for_command(command)
        if needed is None or self.career.is_qualified(needed):
            return None
        qualification = QUALIFICATIONS_BY_KEY[needed]
        remaining = max(
            0,
            qualification.requires_reports
            * self._difficulty().reports_per_qualification
            - self.career.reports_correct,
        )
        return (
            f"{command}: you are not signed off on {qualification.name}.\n\n"
            f"{qualification.description}\n\n"
            f"Correct closures still needed: {remaining}\n"
            f"Type 'qual' for your craft record."
        )
    def _grant_qualifications(self) -> List[str]:
        """Award anything newly earned and return the notices."""
        notices: List[str] = []
        for qualification in self.career.grant_available():
            message = self.switchroom.qualification_notice(
                self.clock.now(), qualification.name, qualification.unlocks)
            notices.append(render_message(message, self._stamp()))
        return notices
    def cmd_report(self, args: Optional[List[str]] = None) -> str:
        """Work the repair service bureau's board of customer trouble reports."""
        args = args or []
        if not args:
            return self._show_report_board()

        action = args[0].lower()
        rest = args[1:]

        if action in ('board', 'list'):
            return self._show_report_board()
        if action == 'closed':
            return self._show_closed_reports()
        if action == 'faults':
            return self._show_fault_reference()
        if action == 'forces':
            return ('Repair forces a report may be dispatched to:\n  '
                    + '\n  '.join(DISPATCH_FORCES))
        if action in ('show', 'detail'):
            if not rest:
                return "report: usage: report show <number>"
            return self._show_report_detail(rest[0])
        if action == 'dispatch':
            if len(rest) < 2:
                return ("report: usage: report dispatch <number> <force>\n"
                        "Forces: " + ', '.join(DISPATCH_FORCES))
            return self._dispatch_report(rest[0], ' '.join(rest[1:]))
        if action == 'close':
            if not rest:
                return ("report: usage: report close <number> <5|8> [fault]\n"
                        "  5  trouble found - name the fault\n"
                        "  8  no trouble found")
            return self._close_report(rest[0], rest[1:])
        if action == 'callback':
            if not rest:
                return "report: usage: report callback <number>"
            return self._report_callback(rest[0])

        return (f"report: unknown option '{args[0]}'\n"
                "Options: board, show, dispatch, close, callback, closed, "
                "faults, forces")
    def _show_report_board(self) -> str:
        """Render the pending list, nearest commitment first."""
        pending = self.desk.pending()
        office = self.home_office
        header = (
            f"Repair Service Bureau - Pending Trouble Reports\n"
            f"{office['city']}, {office['state']}  {office['clli']}"
            f"{' ' * 6}{self.clock.timestamp()}\n"
            + '=' * 74
        )
        if not pending:
            return (header + "\n\nBoard is clear. Nothing pending.\n\n"
                    "New reports arrive during the shift. Type 'qual' for "
                    "your craft record.")

        lines = [
            header,
            f"{'#':>2}  {'REPORT':<10} {'TELEPHONE':<14} {'CLS':<5} "
            f"{'CUSTOMER STATES':<26} {'DUE':>6}  ST",
            '-' * 74,
        ]
        for position, report in enumerate(pending, 1):
            marker = '!' if report.overdue() else ' '
            repeat = 'R' if report.repeat_of else ' '
            lines.append(
                f"{position:>2}{marker} {report.number:<10} "
                f"{report.record.telephone_number:<14} "
                f"{report.record.class_of_service:<5} "
                f"{report.symptom[:26]:<26} "
                f"{report.age_label():>6}  {report.status}{repeat}"
            )
        lines.append('-' * 74)

        overdue = sum(1 for report in pending if report.overdue())
        repeats = sum(1 for report in pending if report.repeat_of)
        lines.append(
            f"{len(pending)} pending, {overdue} past commitment, "
            f"{repeats} repeat. Service index {self.career.service_index():.1f} "
            f"({self.career.index_band()})."
        )
        lines.append('')
        lines.append("report show <n> | mlt <n> | report dispatch <n> <force> "
                     "| report close <n> <5|8> [fault]")
        return '\n'.join(lines)
    def _show_report_detail(self, token: str) -> str:
        """Render one report in full: the line record and everything done to it."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"

        record = report.record
        class_name = CLASSES_OF_SERVICE.get(record.class_of_service, 'Unknown')
        lines = [
            f"{report.number}"
            f"{' ' * max(1, 40 - len(report.number))}"
            f"Received {report.received.strftime('%H:%M %a %b %d')}",
            '=' * 74,
            'LINE RECORD',
            f"  Telephone number    {record.telephone_number}",
            f"  Name                {record.name}",
            f"  Address             {record.address}",
            f"  Class of service    {record.class_of_service}  ({class_name})",
            f"  Cable and pair      {record.cable_pair()}",
            f"  Frame appearance    H {record.horizontal} / V {record.vertical}",
            f"  Line equipment      {record.line_equipment}",
            f"  Office              {record.clli}",
            '',
            'REPORT',
            f"  Customer states     {report.symptom}",
            f"  Commitment          "
            f"{report.commitment.strftime('%H:%M %a %b %d')}"
            f"   ({report.age_label()} "
            f"{'past' if report.overdue() else 'remaining'})",
            f"  Status              {report.status}",
            f"  Time charged        {report.minutes_spent // 60}:"
            f"{report.minutes_spent % 60:02d}",
        ]
        if report.repeat_of:
            lines.append(f"  Repeat of           {report.repeat_of}")
        if report.dispatched_to:
            lines.append(f"  Dispatched to       {report.dispatched_to}")

        lines.extend(['', 'MEASUREMENTS'])
        if report.test_notes:
            for note in report.test_notes:
                lines.append(f"  {note}")
        else:
            lines.append("  None. The line has not been tested.")
            lines.append(f"  Measure it:  mlt {report.number}")

        lines.extend([
            '',
            'CLOSE OUT',
            f"  report close {report.number} 5 <fault>   trouble found",
            f"  report close {report.number} 8           no trouble found",
        ])
        if self._difficulty().require_test_before_close:
            lines.append("  This shift will not accept a close on a line that "
                         "has not been measured.")
        return '\n'.join(lines)
    def _show_closed_reports(self) -> str:
        """Render what has been closed this session and how it was judged."""
        closed = self.desk.closed()
        if not closed:
            return "No reports closed this session."
        lines = [
            "Reports closed this session",
            '=' * 74,
            f"{'REPORT':<10} {'TELEPHONE':<14} {'DISP':<5} {'FOUND':<10} "
            f"{'TRUTH':<10} RESULT",
            '-' * 74,
        ]
        for report in closed:
            verdict = 'correct' if report.correct else 'WRONG'
            if report.missed_commitment:
                verdict += ', missed commitment'
            lines.append(
                f"{report.number:<10} {report.record.telephone_number:<14} "
                f"{'code ' + str(report.disposition):<5} "
                f"{(report.found or '-'):<10} "
                f"{report.record.fault:<10} {verdict}"
            )
        lines.append('-' * 74)
        lines.append(
            f"Closed {self.career.reports_closed}, correct "
            f"{self.career.reports_correct}, repeats {self.career.repeat_reports}. "
            f"Service index {self.career.service_index():.1f} "
            f"({self.career.index_band()})."
        )
        return '\n'.join(lines)
    def _show_fault_reference(self) -> str:
        """Render the fault vocabulary a close out is written against."""
        lines = [
            "Trouble conditions and where they live",
            '=' * 74,
            f"{'CODE':<10} {'NAME':<26} {'WHERE':<9} DISPATCH",
            '-' * 74,
        ]
        for fault in FAULTS.values():
            lines.append(
                f"{fault.code:<10} {fault.name:<26} {fault.where:<9} "
                f"{fault.dispatch}"
            )
        lines.extend([
            '-' * 74,
            '',
            'What each one measures like:',
            '',
        ])
        for fault in FAULTS.values():
            lines.append(f"  {fault.code:<10} {fault.mlt_signature}")
        lines.extend([
            '',
            "Close a report with 'report close <n> 5 <code>' when you have "
            "found and",
            "cleared one of these, or with code 8 when nothing was there.",
        ])
        return '\n'.join(lines)
    def _dispatch_report(self, token: str, force: str) -> str:
        """Send a repair force out and report what they found."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."

        canonical = valid_force(force)
        if canonical is None:
            return (f"report: '{force}' is not a repair force.\n"
                    f"Forces: {', '.join(DISPATCH_FORCES)}")

        finding = self.desk.dispatch(report, canonical)
        if report.field_finding:
            fault = FAULTS[report.field_finding]
            called_in = (
                'nothing wrong at the station, line tests good'
                if fault.code == 'NONE'
                else f'{fault.name.lower()} cleared, back in service')
        else:
            called_in = (f'nothing at our end. Somebody else has this one, '
                         f'not {canonical.lower()}')
        message = self.switchroom.field_call(
            self.clock.now(), report.number, called_in, force=canonical)
        self._queue_message(message, after=random.randint(1, 3))

        return (f"{report.number} dispatched to {canonical}.\n"
                f"{finding}\n"
                f"Time charged {report.minutes_spent // 60}:"
                f"{report.minutes_spent % 60:02d} of the commitment "
                f"({report.age_label()} "
                f"{'past' if report.overdue() else 'remaining'}).")
    def _close_report(self, token: str, rest: List[str]) -> str:
        """Close a report against a disposition code and judge the call."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."
        if not rest:
            return ("report: name a disposition code.\n"
                    "  5  trouble found - name the fault\n"
                    "  8  no trouble found")

        try:
            disposition = int(rest[0])
        except ValueError:
            return f"report: '{rest[0]}' is not a disposition code. Use 5 or 8."
        if disposition not in DISPOSITIONS:
            return (f"report: code {disposition} is not a disposition this "
                    f"bureau uses. Use 5 or 8.")

        difficulty = self._difficulty()
        if difficulty.require_test_before_close and not report.tested:
            return (f"{report.number} has not been measured.\n\n"
                    "Verify, locate, repair, verify. This shift will not "
                    "accept a close on a line\n"
                    f"nobody tested. Run 'mlt {report.number}' first.")

        found = None
        if disposition == 5:
            if not rest[1:]:
                return ("report: code 5 is trouble found. Name what you "
                        "found.\n"
                        f"  report close {report.number} 5 <code>\n"
                        f"Codes: {', '.join(FAULTS)}")
            found = rest[1].upper()
            if found not in FAULTS:
                return (f"report: '{found}' is not a trouble condition.\n"
                        f"Codes: {', '.join(FAULTS)}\n"
                        "Type 'report faults' for what each one means.")

        correct = self.desk.close(
            report, disposition, found, self.clock.now(),
            difficulty.count_missed_commitments)
        self.career.record_closure(correct, report.missed_commitment)

        lines = [
            f"{report.number} closed, code {disposition} - "
            f"{disposition_name(disposition)}.",
        ]
        if correct:
            lines.append("The close out matches what was on the line.")
        else:
            truth = FAULTS[report.record.fault]
            if report.record.fault == 'NONE':
                lines.append("Nothing was actually wrong with that line.")
            elif disposition == 8:
                lines.append(f"There was a {truth.name.lower()} on that pair.")
            else:
                lines.append(f"That pair had a {truth.name.lower()}, not "
                             f"{FAULTS[found].name.lower() if found else 'that'}.")

        if report.missed_commitment:
            lines.append("Commitment was missed. It counts.")

        if self.desk.should_repeat(report, difficulty.repeat_report_chance):
            repeat = self.desk.repeat(
                report, self.clock.now(), difficulty.commitment_slack_minutes)
            self.career.record_repeat()
            notice = self.switchroom.repeat_notice(
                self.clock.now(), repeat.number,
                f"code {disposition}", report.record.telephone_number)
            self._queue_message(notice, after=random.randint(2, 5))

        lines.append('')
        lines.append(
            f"Closed {self.career.reports_closed}, correct "
            f"{self.career.reports_correct}. Service index "
            f"{self.career.service_index():.1f} ({self.career.index_band()})."
        )

        granted = self._grant_qualifications()
        if granted:
            lines.append('')
            lines.extend(granted)
        return '\n'.join(lines)
    def _report_callback(self, token: str) -> str:
        """Call the customer back and get more out of them than the card has."""
        report = self.desk.find(token)
        if report is None:
            return f"report: no report matching '{token}'"
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."

        report.spend(COST_CALLBACK)
        fault = FAULTS[report.record.fault]
        detail = {
            'OPEN': "It went dead all at once. There was work in the street "
                    "last week.",
            'SHORT': "Nothing at all when I pick it up, and my daughter says "
                     "she gets a busy signal every time.",
            'GROUND': "There is a hum, worse when it rains, and sometimes it "
                      "rings once by itself.",
            'CROSS': "I can hear two other people talking. They can hear me "
                     "as well.",
            'WET': "It has been getting worse all week, since the storm. The "
                   "neighbours have it too.",
            'FCG': "I get nothing when I dial. The dial tone is there and "
                   "then it just sits.",
            'FEMF': "There is a loud buzz, and I felt something off the set "
                    "once. The power line runs right past.",
            'ROH': "No, I have not had any trouble calling out. People say "
                   "they cannot reach me.",
            'CO_EQUIP': "It never rings. I have tried a different telephone "
                        "and it does the same thing.",
            'NONE': "It happened twice on Tuesday and it has been fine since. "
                    "Perhaps it fixed itself.",
        }.get(report.record.fault, fault.description)

        return (f"Call back on {report.record.telephone_number} "
                f"({report.record.name}).\n\n"
                f"  \"{detail}\"\n\n"
                f"{COST_CALLBACK} minutes charged. "
                f"{report.age_label()} "
                f"{'past' if report.overdue() else 'remaining'}.")
    def cmd_qual(self, args: Optional[List[str]] = None) -> str:
        """Show the craft record: difficulty, qualifications and service index."""
        args = args or []
        if args and args[0].lower() == 'index':
            return self._show_service_index()

        career = self.career
        difficulty = career.difficulty
        lines = [
            f"Craft Record - {self.username}",
            '=' * 74,
            f"  Difficulty          {difficulty.name}",
            f"  {' ' * 18}  {difficulty.summary}",
            f"  Shift               {career.shift}",
            f"  Reports closed      {career.reports_closed} "
            f"({career.reports_correct} correct, {career.reports_wrong} wrong)",
            f"  Repeat reports      {career.repeat_reports}",
            f"  Missed commitments  {career.missed_commitments}"
            + ('' if difficulty.count_missed_commitments else '  (not counted)'),
            f"  Customer reports    {career.service_index():.1f} of 100  "
            f"{career.index_band()}",
            f"  Worth to the office {career.office_contribution():.1f} of "
            f"{NSPMP_WEIGHTS['customer_reports']} index points",
            '',
            'QUALIFICATIONS',
            '-' * 74,
        ]
        for qualification in QUALIFICATIONS:
            held = career.is_qualified(qualification.key)
            mark = 'x' if held else ' '
            lines.append(f"  [{mark}] {qualification.name}")
            lines.append(f"      {qualification.description}")
            lines.append(f"      Opens: {', '.join(qualification.unlocks)}")
            if not held:
                needed = (qualification.requires_reports
                          * difficulty.reports_per_qualification
                          - career.reports_correct)
                lines.append(f"      Needs {max(0, needed)} more correct "
                             f"closures.")
            lines.append('')

        nxt = career.next_qualification()
        if nxt is None:
            lines.append("Fully qualified. Every system on this terminal is "
                         "open to you.")
        else:
            lines.append(f"Next: {nxt.name} in "
                         f"{career.reports_until_next()} correct closures.")
        lines.extend([
            '',
            "Change difficulty with 'set game.difficulty fun' or "
            "'set game.difficulty craft'.",
            "'qual index' explains how the index is scored.",
        ])
        return '\n'.join(lines)
    def _show_service_index(self) -> str:
        """Explain the index against the published measurement weights."""
        career = self.career
        difficulty = career.difficulty
        lines = [
            "Service index",
            '=' * 74,
            "The network switching performance measurement plan scored an",
            "office across ten weighted components summing to 100. Customer",
            "reports carried ten of them.",
            '',
            f"{'COMPONENT':<28} {'CATEGORY':<20} WEIGHT",
            '-' * 74,
        ]
        for key, weight in NSPMP_WEIGHTS.items():
            label = key.replace('_', ' ').title()
            marker = ' <' if key == 'customer_reports' else ''
            lines.append(
                f"{label:<28} {NSPMP_CATEGORIES[key]:<20} {weight:>3}{marker}")
        lines.extend([
            '-' * 74,
            f"{'Total':<49} {sum(NSPMP_WEIGHTS.values()):>3}",
            '',
            "You are scored on the marked component, out of 100, because that",
            "is the one you work. Total failure on it would cost the office",
            "only ten of its hundred points, which would tell you nothing.",
            '',
            'HOW THE HUNDRED IS LOST',
            '-' * 74,
            f"  Wrong disposition   {WRONG_DISPOSITION_WEIGHT:>3}",
            f"  Repeat report       {REPEAT_REPORT_WEIGHT:>3}",
            f"  Missed commitment   {MISSED_COMMITMENT_WEIGHT:>3}"
            + ('' if difficulty.count_missed_commitments
               else '  (not counted on this setting)'),
            f"  Difficulty factor   {difficulty.index_penalty:>3.1f} "
            f"({difficulty.name})",
            '',
            "  Each is lost in proportion to the share of your closed reports",
            "  it applies to, then scaled by the difficulty factor. Close every",
            "  report wrongly and the whole 55 goes.",
            '',
            "  A wrong close weighs heaviest because it is the one that leaves",
            "  a customer out of service believing somebody has dealt with",
            "  them. The apportionment is the simulation's own; the ten points",
            "  the component is worth to the office are the published figure.",
            '',
            'YOUR STANDING',
            '-' * 74,
            f"  Reports closed      {career.reports_closed}",
            f"  Closed correctly    {career.reports_correct}",
            f"  Closed wrongly      {career.reports_wrong}",
            f"  Came back as repeat {career.repeat_reports}",
            f"  Missed commitments  {career.missed_commitments}",
            f"  Customer reports    {career.service_index():.1f} of 100  "
            f"({career.index_band()})",
            f"  Worth to the office {career.office_contribution():.1f} of "
            f"{NSPMP_WEIGHTS['customer_reports']} points",
        ])
        if career.index_history:
            lines.append('')
            lines.append('  Previous shifts     '
                         + ', '.join(f"{entry:.1f}"
                                     for entry in career.index_history[-10:]))
        lines.extend([
            '',
            "A report closed as no trouble found on a line that really was",
            "faulty counts twice against you: once as a wrong disposition, and",
            "again when the customer calls back.",
        ])
        return '\n'.join(lines)
