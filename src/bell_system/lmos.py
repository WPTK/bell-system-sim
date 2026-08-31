"""
The Loop Maintenance Operations System, and the repair bureau around it.

Telecommunications Transmission Engineering volume 2 describes LMOS as a
component of an Automated Repair Service Bureau: a computer system that
"mechanizes RSB customer line card records by storing them in computer
memory and can produce a variety of management reports". Its listed functions
are customer trouble report processing, control of mechanized testing,
analysis of past trouble reports through the trouble report evaluation and
analysis tool, and the provision of equipment utilization reports. One
installation held up to five million customer line records.

The same passage gives the bureau's three objectives: improve efficiency and
reduce the cost of repair operations, reduce the time required to detect,
locate and repair troubles, and improve the handling of customer contacts by
repair service attendants. It also names the test systems that worked with
it - the line status verifier and automated line verification equipment, both
of limited capability, and mechanised loop testing, which "provides
mechanization of essentially all ARSB test functions".

That is what this module is. It holds no state of its own: the line records
and the trouble reports already live on the report desk, and LMOS is the view
onto them the craft actually sat in front of. TREAT's analyses are computed
from the reports the desk has closed.
"""

from collections import Counter
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .cable import binder_colour, binder_of
from .data.trouble import DISPOSITIONS, FAULTS

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checking
    from .reports import LineRecord, ReportDesk, TroubleReport

# One LMOS installation held up to five million customer line records.
LINE_RECORD_CAPACITY = 5_000_000

# Test systems that worked with an automated repair service bureau, with what
# the document says about each.
TEST_SYSTEMS: Dict[str, Tuple[str, str]] = {
    'LSV': ('Line status verifier', 'Limited capability'),
    'ALV': ('Automated line verification', 'Limited capability'),
    'MLT': ('Mechanised loop testing',
            'Mechanises essentially all bureau test functions'),
}

# The bureau's stated objectives, quoted in substance from the document.
OBJECTIVES: Tuple[str, ...] = (
    'Improve efficiency and reduce the cost of repair operations',
    'Reduce the time required to detect, locate and repair troubles',
    'Improve the handling of customer contacts by repair service attendants',
)

# What the trouble report evaluation and analysis tool reported on.
TREAT_REPORTS: Tuple[str, ...] = (
    'Customer trouble reports',
    'Coin telephone operation',
    'Customer-provided equipment',
    'Special services inventory',
    'Repair force administration',
)


class LineCard:
    """
    One customer line card record as LMOS held it.

    The record is the desk's own :class:`~bell_system.reports.LineRecord`;
    this wraps it with the trouble history LMOS kept alongside it, which is
    what made the system worth having.
    """

    def __init__(self, record: 'LineRecord'):
        self.record = record
        self.history: List['TroubleReport'] = []

    @property
    def report_count(self) -> int:
        """Return how many reports have been taken on this line."""
        return len(self.history)

    @property
    def repeat_count(self) -> int:
        """Return how many of them came back after a close out."""
        return sum(1 for report in self.history if report.repeat_of)

    def is_chronic(self) -> bool:
        """
        Return whether this line has reported often enough to be chronic.

        Three reports on one line is the threshold this simulation uses; no
        source available to it states the Bell System's own.
        """
        return self.report_count >= 3


class Lmos:
    """
    The bureau's view onto its line records and its trouble reports.

    Reads the report desk rather than duplicating it, so nothing here can
    drift out of step with the board a craftsperson is actually working.
    """

    def __init__(self, desk: 'ReportDesk'):
        self.desk = desk

    # -- line records ----------------------------------------------------

    def line_cards(self) -> Dict[str, LineCard]:
        """Build the line card index from every report the desk has seen."""
        cards: Dict[str, LineCard] = {}
        for report in self.desk.reports.values():
            number = report.record.telephone_number
            card = cards.get(number)
            if card is None:
                card = cards[number] = LineCard(report.record)
            card.history.append(report)
        for card in cards.values():
            card.history.sort(key=lambda report: report.received)
        return cards

    def find_card(self, token: str) -> Optional[LineCard]:
        """Look a line card up by telephone number, or by report number."""
        cards = self.line_cards()
        digits = ''.join(c for c in token if c.isdigit())
        for number, card in cards.items():
            if digits and ''.join(c for c in number if c.isdigit()).endswith(digits):
                return card
        report = self.desk.find(token)
        if report is not None:
            return cards.get(report.record.telephone_number)
        return None

    def chronic_lines(self) -> List[LineCard]:
        """Return lines that have reported often enough to want attention."""
        chronic = [card for card in self.line_cards().values() if card.is_chronic()]
        return sorted(chronic, key=lambda card: card.report_count, reverse=True)

    # -- report processing ----------------------------------------------

    def in_process(self) -> List['TroubleReport']:
        """Return the reports the bureau is currently working."""
        return self.desk.pending()

    def status_counts(self) -> Counter:
        """Return how many pending reports sit at each status."""
        return Counter(report.status for report in self.desk.pending())

    def utilisation(self) -> Dict[str, int]:
        """
        Return the equipment utilisation figures the system reported.

        Counts of what the bureau's testing actually did this session, which
        is what an equipment utilisation report was for.
        """
        pending = self.desk.pending()
        closed = self.desk.closed()
        every = pending + closed
        return {
            'line_records': len(self.line_cards()),
            'reports_in_process': len(pending),
            'reports_closed': len(closed),
            'tested': sum(1 for report in every if report.tested),
            'untested': sum(1 for report in every if not report.tested),
            'measurements': sum(len(report.test_notes) for report in every),
            'dispatched': sum(1 for report in every if report.dispatched_to),
        }

    # -- TREAT -----------------------------------------------------------

    def trouble_analysis(self) -> Dict[str, Counter]:
        """
        Analyse closed reports the way the analysis tool did.

        Returns:
            Counters over dispositions, the conditions actually found, and
            the repair forces the work went to
        """
        closed = self.desk.closed()
        return {
            'dispositions': Counter(
                f"Code {report.disposition} - "
                f"{DISPOSITIONS[report.disposition].name}"
                for report in closed if report.disposition in DISPOSITIONS
            ),
            'conditions': Counter(
                FAULTS[report.record.fault].name for report in closed
            ),
            'forces': Counter(
                report.dispatched_to for report in closed
                if report.dispatched_to
            ),
        }

    def coin_analysis(self) -> Dict[str, int]:
        """Return the coin telephone operation figures the tool reported."""
        cards = self.line_cards()
        coin = [card for card in cards.values()
                if card.record.class_of_service == 'COIN']
        return {
            'coin_lines': len(coin),
            'reports': sum(card.report_count for card in coin),
            'repeats': sum(card.repeat_count for card in coin),
        }

    def force_administration(self) -> Dict[str, Counter]:
        """Return how the repair forces were used, by dispatch and outcome."""
        every = self.desk.pending() + self.desk.closed()
        wasted: Counter = Counter()
        for report in every:
            if report.dispatched_to and report.field_finding is None:
                wasted[report.dispatched_to] += 1
        return {
            'dispatches': Counter(report.dispatched_to for report in every
                                  if report.dispatched_to),
            'wasted_trips': wasted,
        }


class LmosConsole:
    """
    The screens a repair service bureau position showed.

    Holds the rendering for the ``lmos`` command so it lives beside the state
    it displays rather than in the terminal. The terminal supplies session
    context - the clock, the difficulty, the board - and dispatches here.
    """

    def __init__(self, terminal):
        self.terminal = terminal

    @property
    def lmos(self) -> Lmos:
        """Return a view onto the terminal's current report desk."""
        return Lmos(self.terminal.desk)

    def command(self, args: Optional[List[str]] = None) -> str:
        """Dispatch an ``lmos`` subcommand."""
        args = args or []
        if not args:
            return self.status()

        action = args[0].lower()
        rest = args[1:]
        if action in ('status', 'arsb'):
            return self.status()
        if action in ('line', 'card', 'record'):
            if not rest:
                return "lmos: usage: lmos line <telephone number>"
            return self.line_card(rest[0])
        if action in ('reports', 'process'):
            return self.report_processing()
        if action == 'chronic':
            return self.chronic()
        if action == 'treat':
            return self.treat(rest[0] if rest else None)
        if action in ('utilisation', 'utilization', 'equipment'):
            return self.utilisation()
        if action in ('cable', 'sheath', 'plant'):
            return self.cable_analysis()
        return (f"lmos: unknown option '{args[0]}'\n"
                "Options: status, line, reports, chronic, treat, "
                "utilisation, cable")


    def cable_analysis(self) -> str:
        """
        Group the pending reports by cable and binder group.

        Water in a sheath is not a pair fault. It drops insulation
        resistance across the pairs in one twenty-five-pair binder group at
        once, so several reports off one group is what water looks like from
        a repair position - and one splicer trip repairs all of them.

        This is the view that makes that visible without reading the whole
        board. The same information is in /usr/lmos/board, where sort(1)
        and uniq(1) will find it too.
        """
        pending = self.terminal.desk.pending()
        if not pending:
            return "lmos: nothing pending"

        groups: Dict[Tuple[int, int], List['TroubleReport']] = {}
        for report in pending:
            record = report.record
            key = (record.cable, binder_of(record.pair))
            groups.setdefault(key, []).append(report)

        rows = ["Loop Maintenance Operations System - cable analysis",
                f"{self.terminal.clock.timestamp()}",
                '=' * 74, '',
                f"{'CABLE':<8}{'BINDER':<8}{'COLOUR':<16}{'PAIRS':<12}"
                f"{'RPTS':<6}REPORTS",
                '-' * 74]
        suspect = []
        for (cable, binder), reports in sorted(groups.items()):
            pairs = sorted(report.record.pair for report in reports)
            span = (f"{pairs[0]}" if len(pairs) == 1
                    else f"{pairs[0]}-{pairs[-1]}")
            numbers = ' '.join(report.number for report in reports)
            rows.append(f"{cable:<8}{binder:<8}{binder_colour(binder):<16}"
                        f"{span:<12}{len(reports):<6}{numbers[:28]}")
            if len(reports) > 1:
                suspect.append((cable, binder, len(reports)))

        rows.append('-' * 74)
        rows.append('')
        if suspect:
            rows.append("MORE THAN ONE REPORT IN A BINDER GROUP")
            for cable, binder, count in suspect:
                rows.append(f"  cable {cable} binder {binder} "
                            f"({binder_colour(binder)}): {count} reports")
            rows.append('')
            rows.append("That is what water looks like. Test one of them "
                        "before you dispatch:")
            rows.append("a single trip to the sheath repairs every pair in "
                        "the group, and")
            rows.append("six trips to six pairs repairs the same thing six "
                        "times over.")
        else:
            rows.append("No binder group has more than one report on it. "
                        "Nothing here looks")
            rows.append("like water.")
        return '\n'.join(rows)

    # -- screens ---------------------------------------------------------

    def status(self) -> str:
        """Render the bureau's overall position."""
        lmos = self.lmos
        counts = lmos.utilisation()
        statuses = lmos.status_counts()
        office = self.terminal.home_office

        lines = [
            "Loop Maintenance Operations System",
            f"Automated Repair Service Bureau - {office['city']}, "
            f"{office['state']}  {office['clli']}",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            '',
            'LINE RECORDS',
            f"  Held on this system     {counts['line_records']:>9,}",
            f"  System capacity         {LINE_RECORD_CAPACITY:>9,}",
            '',
            'TROUBLE REPORT PROCESSING',
            f"  In process              {counts['reports_in_process']:>9,}",
            f"  Closed this session     {counts['reports_closed']:>9,}",
        ]
        for status, count in sorted(statuses.items()):
            lines.append(f"    {status:<20}  {count:>9,}")

        lines.extend([
            '',
            'MECHANIZED TESTING',
        ])
        for code, (name, note) in TEST_SYSTEMS.items():
            mark = '>' if code == 'MLT' else ' '
            lines.append(f"  {mark} {code:<5} {name:<32} {note}")

        lines.extend([
            '',
            'BUREAU OBJECTIVES',
        ])
        for objective in OBJECTIVES:
            lines.append(f"  - {objective}")

        lines.extend([
            '',
            "  lmos line <number>   The customer line card record",
            "  lmos reports         Trouble reports in process",
            "  lmos chronic         Lines reporting repeatedly",
            "  lmos treat           Trouble report evaluation and analysis",
            "  lmos utilisation     Equipment utilisation report",
        ])
        return '\n'.join(lines)

    def line_card(self, token: str) -> str:
        """Render one customer line card record and its trouble history."""
        card = self.lmos.find_card(token)
        if card is None:
            return (f"lmos: no line card record for '{token}'.\n"
                    "This system holds records for lines that have reported "
                    "trouble.")

        record = card.record
        lines = [
            f"Line Card Record - {record.telephone_number}",
            '=' * 74,
            f"  Name                 {record.name}",
            f"  Address              {record.address}",
            f"  Class of service     {record.class_of_service}",
            f"  Cable and pair       {record.cable_pair()}",
            f"  Frame appearance     H {record.horizontal} / V {record.vertical}",
            f"  Line equipment       {record.line_equipment}",
            f"  Office               {record.clli}",
            '',
            'TROUBLE HISTORY',
            '-' * 74,
            f"  Reports on this line {card.report_count}",
            f"  Repeats              {card.repeat_count}",
        ]
        if card.is_chronic():
            lines.append("  CHRONIC - three or more reports on this line")
        lines.append('')

        for report in card.history:
            closed = ('open' if report.disposition is None
                      else f"code {report.disposition}")
            lines.append(
                f"  {report.number}  {report.received.strftime('%b %d %H:%M')}  "
                f"{report.symptom[:28]:<28} {closed}")
        return '\n'.join(lines)

    def report_processing(self) -> str:
        """Render the reports the bureau currently has in process."""
        pending = self.lmos.in_process()
        if not pending:
            return "No trouble reports in process."

        lines = [
            "Trouble Report Processing",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            f"{'REPORT':<11}{'TELEPHONE':<15}{'STATUS':<8}{'TESTED':<8}"
            f"{'DISPATCHED':<18}DUE",
            '-' * 74,
        ]
        for report in pending:
            lines.append(
                f"{report.number:<11}{report.record.telephone_number:<15}"
                f"{report.status:<8}{'yes' if report.tested else 'no':<8}"
                f"{(report.dispatched_to or '-')[:17]:<18}"
                f"{report.age_label()}"
            )
        lines.append('-' * 74)
        lines.append("Mechanized testing is controlled from this system: "
                     "'mlt <report>'.")
        return '\n'.join(lines)

    def chronic(self) -> str:
        """Render lines that keep reporting."""
        chronic = self.lmos.chronic_lines()
        lines = [
            "Chronic Lines",
            '=' * 74,
            "Lines carrying three or more trouble reports. The threshold is "
            "this",
            "simulation's own; no source available to it states the Bell "
            "System's.",
            '',
        ]
        if not chronic:
            lines.append("No line has reported three times yet.")
            return '\n'.join(lines)

        lines.extend([
            f"{'TELEPHONE':<15}{'CABLE/PAIR':<13}{'CLS':<6}{'REPORTS':>8}"
            f"{'REPEATS':>9}",
            '-' * 74,
        ])
        for card in chronic:
            lines.append(
                f"{card.record.telephone_number:<15}"
                f"{card.record.cable_pair():<13}"
                f"{card.record.class_of_service:<6}"
                f"{card.report_count:>8}{card.repeat_count:>9}"
            )
        return '\n'.join(lines)

    def treat(self, which: Optional[str] = None) -> str:
        """Render the trouble report evaluation and analysis tool."""
        lmos = self.lmos
        if which and which.lower().startswith('coin'):
            coin = lmos.coin_analysis()
            return '\n'.join([
                "TREAT - Coin Telephone Operation",
                '=' * 74,
                f"  Coin lines on record   {coin['coin_lines']}",
                f"  Reports taken          {coin['reports']}",
                f"  Repeats                {coin['repeats']}",
                '',
                "  A coin station needs 23 mA to operate, which puts its "
                "range limit",
                "  at 1300 ohms, about three miles.",
            ])

        if which and which.lower().startswith('force'):
            force = lmos.force_administration()
            lines = [
                "TREAT - Repair Force Administration",
                '=' * 74,
                f"{'FORCE':<22}{'DISPATCHES':>12}{'WASTED TRIPS':>15}",
                '-' * 74,
            ]
            forces = set(force['dispatches']) | set(force['wasted_trips'])
            if not forces:
                lines.append("  Nothing dispatched yet.")
            for name in sorted(forces):
                lines.append(
                    f"{name:<22}{force['dispatches'][name]:>12}"
                    f"{force['wasted_trips'][name]:>15}")
            return '\n'.join(lines)

        analysis = lmos.trouble_analysis()
        lines = [
            "Trouble Report Evaluation and Analysis Tool",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            '',
            'AVAILABLE ANALYSES',
        ]
        for report in TREAT_REPORTS:
            lines.append(f"  - {report}")

        lines.extend(['', 'CLOSE OUT DISPOSITIONS', '-' * 74])
        if not analysis['dispositions']:
            lines.append("  Nothing closed yet.")
        for name, count in analysis['dispositions'].most_common():
            lines.append(f"  {name:<44}{count:>6}")

        lines.extend(['', 'CONDITIONS FOUND', '-' * 74])
        if not analysis['conditions']:
            lines.append("  Nothing closed yet.")
        for name, count in analysis['conditions'].most_common():
            lines.append(f"  {name:<44}{count:>6}")

        lines.extend([
            '',
            "  treat coin    Coin telephone operation",
            "  treat force   Repair force administration",
        ])
        return '\n'.join(lines)

    def utilisation(self) -> str:
        """Render the equipment utilisation report."""
        counts = self.lmos.utilisation()
        return '\n'.join([
            "Equipment Utilisation Report",
            f"{self.terminal.clock.timestamp()}",
            '=' * 74,
            f"  Line records held        {counts['line_records']:>8,}",
            f"  Reports in process       {counts['reports_in_process']:>8,}",
            f"  Reports closed           {counts['reports_closed']:>8,}",
            f"  Reports measured         {counts['tested']:>8,}",
            f"  Reports not measured     {counts['untested']:>8,}",
            f"  Measurements taken       {counts['measurements']:>8,}",
            f"  Dispatches made          {counts['dispatched']:>8,}",
            '',
            "  Mechanised loop testing mechanises essentially all bureau test",
            "  functions; the line status verifier and automated line",
            "  verification equipment have limited capability beside it.",
        ])
