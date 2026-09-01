"""
The repair service bureau board and the craft record.
"""

import random
from collections import (
    deque,
)
from typing import (
    Dict,
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
from ..clock import career_progress, days_to_divestiture
from ..console import article as _a, sentence_case as _lower, wrap
from ..lmos import LmosConsole
from ..loop_testing import post_mortem
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

# The board and the craft record rule at 74 columns. The post-mortem is
# prose rather than a table, so it breaks a little short of the rule.
POST_MORTEM_WIDTH = 70

# What a customer says, wrapped. Narrower than the post-mortem because it
# is indented and quoted, which is how a note of a call reads on paper.
CALLBACK_WIDTH = 64

# What a stored home office has to carry to be usable. Anything short of
# this is treated as absent and drawn again, which is what happens to a
# career record written before the office was kept.
HOME_OFFICE_FIELDS = frozenset(
    {'npa', 'nxx', 'city', 'state', 'switch_type', 'clli'})

# What a customer says they hear when a call will not go through, for the
# two conditions where the answer is in the cadence and not in the words.
# Busy is 60 interruptions a minute and reorder is 120; they are the same
# 480 and 620 Hz, so the description says how fast and never says which.
# tone(1) writes both, which is the one question on this board that has to
# be answered by ear.
CADENCE_HEARD: Dict[str, str] = {
    'CO_EQUIP': "I dial and I get the busy signal, but it is going about "
                "twice as fast as a busy usually goes. It does it on every "
                "number I try, including my sister's, and she is not on "
                "the telephone.",
    'NONE': "I get the busy signal. The ordinary one, the slow one. It is "
            "just that I get it rather a lot lately, and I did wonder.",
    # Not a cadence at all, which is the point of having a third: the
    # office took the call and then did nothing with it, so there is
    # nothing to hear. Somebody comparing two tones has to notice that
    # neither of them is what this customer is describing.
    'FCG': "I dial the whole number and then there is nothing. Not a busy, "
           "not a ringing. It goes quiet and it stays quiet until I hang "
           "up.",
}


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

        # The office a career is assigned to, kept on the career record.
        # The switching machine at an office is drawn at random and the
        # COMMON LANGUAGE code is built from it, so without this a
        # craftsperson turned up at a differently named building every
        # session and every line record they had ever seen belonged to
        # somewhere else.
        if self.career.office.keys() >= HOME_OFFICE_FIELDS:
            self.home_office = dict(self.career.office)
        else:
            self.home_office = {
                'npa': npa, 'nxx': nxx, 'city': city,
                'state': STATE_CODES.get(state, state),
                'switch_type': switch_type,
                'clli': (self._office_clli(city, state, switch_type)
                         or 'NWRKNJ02'),
            }
            self.career.office = dict(self.home_office)
            self.career.save()

        npa = self.home_office['npa']
        nxx = self.home_office['nxx']

        self.desk = ReportDesk(npa, nxx, self.home_office['clli'],
                               wet_bias=career_progress(
                                   self.career.shift))
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
        # A first tour opens with one report. The wire chief says he has
        # kept the rest off your board until it is closed, and he has.
        first_tour = (self.career.shift == 1
                      and self.career.reports_closed == 0)
        self.desk.open_shift(self.clock.now(), slack,
                             count=1 if first_tour else None)
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
        return self.dead_end(
            f"{command}: you are not signed off on {qualification.name}.\n\n"
            f"{qualification.description}\n\n"
            f"Correct closures still needed: {remaining}\n"
            f"Type 'qual' for your craft record."
        )
    def _grant_qualifications(self) -> List[str]:
        """
        Award anything newly earned and return the notices.

        The count of what is now held goes with each one, because the man
        signing them notices how many he has signed for you, and so does
        the calendar.
        """
        notices: List[str] = []
        now = self.clock.now()
        for qualification in self.career.grant_available():
            message = self.switchroom.qualification_notice(
                now, qualification.name, qualification.unlocks,
                held=len(self.career.qualifications),
                days_left=days_to_divestiture(now))
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
        if action == 'next':
            return self._show_next_report()
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

        return self.dead_end(
            f"report: unknown option '{args[0]}'\n"
            "Options: board, next, show, dispatch, close, callback, closed, "
            "faults, forces")

    def _show_next_report(self) -> str:
        """
        Show the report that most wants working, and say what it wants.

        The board is a table and reading a table is a skill. This is the
        same decision the standing prompt makes, spent as a command: one
        word, one report, one thing to do with it.
        """
        if not self.desk.pending():
            return self._show_report_board()
        action = self.next_action()
        if not action.command:
            return self._show_report_board()
        report = self.desk.find(action.command.split()[-1])
        if report is None:
            # Nothing on the board wants anything: the prompt is pointing
            # somewhere else, at a sign-off or at the newsreader.
            return f"{action.reason}\n\nType: {action.command}"
        return (f"{self._show_report_detail(report.number)}\n\n"
                f"{action.reason}\n"
                f"Type: {action.command}")
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
        # The board is a table, and reading a table is a skill. Anybody who
        # would rather not is one word away from being told outright. Not on
        # a first tour: the wire chief is already saying this, and two
        # voices saying it is one too many.
        action = self.next_action()
        if (action.command and not self.first_tour()
                and self.settings.is_on('game.prompts')):
            lines.append('')
            lines.append(f"{action.reason} 'report next' shows it.")
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

        finding = self.desk.dispatch(report, canonical, self.clock.now())
        if report.dispatched_to is None:
            # Nobody went: either the force is all out, or the sheath is
            # already repaired. Either way there is no field call coming.
            return finding
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
            self.clock.now(), report.number, called_in, force=canonical,
            crew=report.crew)
        self._queue_message(message, after=random.randint(1, 3))

        sent = (f"{report.number} dispatched to {canonical}.\n"
                f"{finding}\n"
                f"Time charged {report.minutes_spent // 60}:"
                f"{report.minutes_spent % 60:02d} of the commitment "
                f"({report.age_label()} "
                f"{'past' if report.overdue() else 'remaining'}).")
        nudge = self.first_tour_nudge('dispatch')
        return f"{sent}\n\n{nudge}" if nudge else sent
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
            else:
                # Where the trouble was decides how the sentence reads. A
                # central office equipment failure is not something the
                # pair "had", and saying so read like a defect.
                on_the_pair = truth.where == 'LOOP'
                was = (f"There was {_a(truth.name)} on that pair."
                       if on_the_pair
                       else f"The trouble was {_lower(truth.name)}.")
                if disposition == 8:
                    lines.append(was)
                else:
                    named = _a(FAULTS[found].name) if found else 'that'
                    lines.append(f"{was[:-1]}, not {named}.")
            # A score tells you that you guessed wrong. The readings tell
            # you what to read next time, and they are the readings this
            # player actually had in front of them: measure_loop is seeded
            # from the line and the fault, so it quotes rather than invents.
            taught = post_mortem(report.record.telephone_number,
                                 report.record.fault, found, report.tested)
            if taught:
                lines.append('')
                lines.extend(wrap(taught, POST_MORTEM_WIDTH))

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

        parting = self.first_tour_nudge('closed')
        if parting:
            lines.append('')
            lines.append(parting)
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

        # The one question on this board that a screen cannot ask you. On
        # a report about calls not completing the customer describes a
        # rhythm instead of the trouble: busy and reorder are the same 480
        # and 620 Hz and differ only in how fast they are interrupted, so
        # the words cannot separate them and the ear can. It replaces the
        # ordinary answer rather than joining it, because a customer who
        # is telling you about a cadence is not also telling you about
        # last Tuesday.
        heard = CADENCE_HEARD.get(report.record.fault)
        by_ear = heard is not None and 'complete' in report.symptom.lower()
        said = heard if by_ear else detail

        lines = [f"Call back on {report.record.telephone_number} "
                 f"({report.record.name}).", '']
        lines.extend(f"  {line}" for line in
                     wrap(f'"{said}"', CALLBACK_WIDTH))
        if by_ear:
            lines.extend(['', "tone(1) will make both of those if you want "
                              "to hear them side by side."])
        lines.extend(['', f"{COST_CALLBACK} minutes charged. "
                          f"{report.age_label()} "
                          f"{'past' if report.overdue() else 'remaining'}."])
        return '\n'.join(lines)
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
        ]
        # Getting better is the reward, and a column of decimals does not
        # show it. Two shifts is not a trend; from the third the shape is
        # worth drawing.
        trend = self.sparkline(career.index_history)
        if trend:
            span = career.index_history[-5:]
            lines.append(f"  Last five tours     {trend}   "
                         f"{span[0]:.1f} to {span[-1]:.1f}")
        lines.extend([
            '',
            'QUALIFICATIONS',
            '-' * 74,
        ])
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
                short = max(0, needed)
                lines.append(f"      Needs {short} more correct closure"
                             f"{'' if short == 1 else 's'}.")
            lines.append('')

        # What help(1) used to end on. It belongs here, next to the
        # sign-offs that open each one, rather than as the last thing a new
        # craftsperson reads on the first screen they ever see.
        locked = sorted(name for name in self._command_handlers
                        if not career.may_use(name))
        if locked:
            lines.extend(['NOT SIGNED OFF', '-' * 74])
            lines.append(f"  {', '.join(locked)}")
            lines.append('')

        nxt = career.next_qualification()
        if nxt is None:
            lines.append("Fully qualified. Every system on this terminal is "
                         "open to you.")
        else:
            short = career.reports_until_next()
            lines.append(f"Next: {nxt.name} in {short} correct closure"
                         f"{'' if short == 1 else 's'}.")
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
            # Getting better is the reward, and a column of decimals does
            # not show it. Two shifts is not a trend; from the third the
            # shape is worth drawing.
            trend = self.sparkline(career.index_history, span=10)
            if trend:
                lines.append(f"  Trend               {trend}   "
                             f"{min(career.index_history[-10:]):.1f} to "
                             f"{max(career.index_history[-10:]):.1f}")
        lines.extend([
            '',
            "A report closed as no trouble found on a line that really was",
            "faulty counts twice against you: once as a wrong disposition, and",
            "again when the customer calls back.",
        ])
        return '\n'.join(lines)
