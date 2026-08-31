"""
Customer trouble reports and the repair service bureau loop.

Engineering and Operations in the Bell System gives the corrective maintenance
sequence as detect, notify, verify, locate, repair, verify, and says plainly
that locating the trouble is the most difficult and time consuming step. That
is the shape of the work here. A report arrives with nothing but the
customer's words; the electrical truth is hidden until measured; and the two
published disposition codes decide whether the report is closed honestly or
merely closed.

The loop a player works:

    report                  the pending list, oldest commitment first
    report show N           the line record and what the customer said
    mlt N                   measure the loop
    report dispatch N FORCE send a repair force to the right place
    report close N 5 FAULT  trouble found, and what it was
    report close N 8        no trouble found

Getting the disposition wrong does not fail loudly. It closes, and then some
of those reports come back as repeats - which is exactly what the measurement
plan was counting when it scored codes 5 and 8 separately.

Not verified, and marked here rather than hidden: the commitment intervals,
the per-action time costs and the load factor are the simulation's own. The
Bell System's actual repair commitment policy varied by company and by year,
and no bundled source states it. What is taken from the documents is the
maintenance sequence, the disposition codes and the electrical vocabulary.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

from .data.trouble import (
    DISPATCH_FORCES,
    DISPOSITIONS,
    FAULTS,
    REAL_FAULTS,
    REPORT_SYMPTOMS,
)

# Commitment intervals, in minutes of the working day. Out of service means
# the customer cannot originate or receive; anything else is service
# affecting and gets the longer interval.
OUT_OF_SERVICE_COMMITMENT = 480
SERVICE_AFFECTING_COMMITMENT = 1440

# Faults that leave the station unable to originate or receive at all.
OUT_OF_SERVICE_FAULTS = frozenset({'OPEN', 'SHORT', 'CO_EQUIP', 'FCG'})

# Minutes each action costs against a report's commitment.
COST_MLT = 4
COST_CLOSE = 2
COST_WRONG_DISPATCH = 45
COST_CALLBACK = 8

# A backlog slows every commitment: each report already pending adds this
# many minutes to a new one.
LOAD_MINUTES_PER_PENDING = 25

# Share of reports on which nothing is actually wrong with the line.
NO_TROUBLE_SHARE = 0.18

# Reports open at the start of a shift, and the most that may be open at once.
OPENING_BACKLOG = (3, 5)
MAX_PENDING = 9

STATUS_PENDING = 'PEND'
STATUS_TESTED = 'TESTED'
STATUS_DISPATCHED = 'DISP'
STATUS_CLOSED = 'CLOSED'

# Plausible surnames for line records. Ordinary period American surnames,
# nothing more; no real subscriber is depicted.
_SURNAMES: Sequence[str] = (
    'Abbott', 'Barnhart', 'Calloway', 'DeSantis', 'Ellsworth', 'Fairbanks',
    'Gallagher', 'Hargrove', 'Ivers', 'Jankowski', 'Kowalczyk', 'Lindgren',
    'Marchetti', 'Novotny', 'Okafor', 'Pettibone', 'Quintero', 'Rasmussen',
    'Stankiewicz', 'Thibodeaux', 'Ulrich', 'Vandermeer', 'Whitcomb',
    'Yarborough', 'Zabriskie',
)

_INITIALS: Sequence[str] = tuple('ABCDEFGHJKLMNPRSTW')

_STREETS: Sequence[str] = (
    'Maple St', 'Third Ave', 'Ridgeway Dr', 'Franklin Rd', 'Orchard Ln',
    'Elm St', 'Wilson Ave', 'Cedar Ct', 'Bergen Pl', 'Summit Ave',
    'Grand St', 'Church Rd', 'Lakeview Ter', 'Hillside Ave',
)

# Class of service codes. Widely used Bell System line classes; the codes
# themselves are conventional rather than quoted from a bundled document.
CLASSES_OF_SERVICE: Dict[str, str] = {
    '1FR': 'One party flat rate residence',
    '1MR': 'One party message rate residence',
    '1FB': 'One party flat rate business',
    'PBX': 'PBX station line',
    'COIN': 'Coin station',
    'PVT': 'Private line, no dial tone',
}

# How often each class turns up. Residence dominated the loop plant.
_CLASS_WEIGHTS = (('1FR', 46), ('1MR', 18), ('1FB', 22), ('PBX', 8),
                  ('COIN', 4), ('PVT', 2))


class LineRecord:
    """
    One subscriber line as the loop assignment record carries it.

    ``fault`` is the electrical truth and is never shown to the player
    directly. It is what a measurement is taken against.
    """

    def __init__(self, npa: str, nxx: str, line: str, name: str, address: str,
                 cable: int, pair: int, class_of_service: str,
                 horizontal: str, vertical: str, line_equipment: str,
                 clli: str, fault: str = 'NONE'):
        self.npa = npa
        self.nxx = nxx
        self.line = line
        self.name = name
        self.address = address
        self.cable = cable
        self.pair = pair
        self.class_of_service = class_of_service
        self.horizontal = horizontal
        self.vertical = vertical
        self.line_equipment = line_equipment
        self.clli = clli
        self.fault = fault

    @property
    def telephone_number(self) -> str:
        """Return the number in the form a repair attendant would read it."""
        return f"{self.npa}-{self.nxx}-{self.line}"

    @property
    def local_number(self) -> str:
        """Return the seven digit number within the numbering plan area."""
        return f"{self.nxx}-{self.line}"

    def cable_pair(self) -> str:
        """Return the cable and pair as the assignment record writes it."""
        return f"{self.cable:04d}/{self.pair:04d}"


class TroubleReport:
    """A customer trouble report from receipt through to close out."""

    def __init__(self, number: str, record: LineRecord, symptom: str,
                 received: datetime, commitment: datetime,
                 repeat_of: Optional[str] = None):
        self.number = number
        self.record = record
        self.symptom = symptom
        self.received = received
        self.commitment = commitment
        self.repeat_of = repeat_of
        self.status = STATUS_PENDING
        self.minutes_spent = 0
        self.tested = False
        self.test_notes: List[str] = []
        self.dispatched_to: Optional[str] = None
        self.field_finding: Optional[str] = None
        self.disposition: Optional[int] = None
        self.found: Optional[str] = None
        self.closed_at: Optional[datetime] = None
        self.correct: Optional[bool] = None
        self.missed_commitment = False

    # -- derived ---------------------------------------------------------

    @property
    def out_of_service(self) -> bool:
        """Return whether the station cannot originate or receive."""
        return self.record.fault in OUT_OF_SERVICE_FAULTS

    def elapsed(self) -> timedelta:
        """Return the working time charged against this report."""
        return timedelta(minutes=self.minutes_spent)

    def due_in(self) -> timedelta:
        """Return the working time remaining before the commitment."""
        allowed = self.commitment - self.received
        return allowed - self.elapsed()

    def overdue(self) -> bool:
        """Return whether the commitment has been passed."""
        return self.due_in() < timedelta(0)

    def spend(self, minutes: int) -> None:
        """Charge working time against the report."""
        self.minutes_spent += minutes

    def age_label(self) -> str:
        """Return the time remaining, or how far past commitment it is."""
        remaining = self.due_in()
        overdue = remaining < timedelta(0)
        total = int(abs(remaining).total_seconds() // 60)
        stamp = f"{total // 60}:{total % 60:02d}"
        return f"-{stamp}" if overdue else stamp


class ReportDesk:
    """
    The bureau's pending list, and the rules for working it.

    The desk owns report generation, the commitment clock and close out. It
    knows nothing about the terminal: it returns state, and the terminal
    renders it.
    """

    def __init__(self, npa: str, nxx: str, clli: str,
                 rng: Optional[random.Random] = None):
        self.npa = npa
        self.nxx = nxx
        self.clli = clli
        self.rng = rng or random.Random()
        self.reports: Dict[str, TroubleReport] = {}
        self.order: List[str] = []
        self._sequence = self.rng.randint(1200, 8600)
        self.closed_count = 0
        self.repeat_count = 0

    # -- generation ------------------------------------------------------

    def _next_number(self) -> str:
        """Return the next report number in the bureau's series."""
        self._sequence += self.rng.randint(1, 4)
        return f"TR-{self._sequence:05d}"

    def _make_record(self, fault: str) -> LineRecord:
        """Build a line record carrying a given electrical condition."""
        line = f"{self.rng.randint(0, 9999):04d}"
        surname = self.rng.choice(_SURNAMES)
        initial = self.rng.choice(_INITIALS)
        classes = [code for code, _ in _CLASS_WEIGHTS]
        weights = [weight for _, weight in _CLASS_WEIGHTS]
        class_of_service = self.rng.choices(classes, weights=weights)[0]
        return LineRecord(
            npa=self.npa, nxx=self.nxx, line=line,
            name=f"{surname}, {initial}",
            address=f"{self.rng.randint(2, 1480)} {self.rng.choice(_STREETS)}",
            cable=self.rng.randint(1, 88),
            pair=self.rng.randint(1, 900),
            class_of_service=class_of_service,
            horizontal=f"{self.rng.randint(1, 24):02d}",
            vertical=f"{self.rng.randint(1, 52):02d}",
            line_equipment=f"{self.rng.randint(0, 3)}-"
                           f"{self.rng.randint(0, 7)}-"
                           f"{self.rng.randint(0, 19):02d}-"
                           f"{self.rng.randint(0, 9):02d}",
            clli=self.clli,
            fault=fault,
        )

    def _choose_fault(self) -> str:
        """Pick the electrical condition behind a new report."""
        if self.rng.random() < NO_TROUBLE_SHARE:
            return 'NONE'
        if self.rng.random() < 0.07:
            return 'ROH'
        return self.rng.choice(REAL_FAULTS)

    def _commitment(self, fault: str, received: datetime,
                    slack_minutes: int) -> datetime:
        """
        Return the repair commitment for a new report.

        Out of service gets the shorter interval. Everything already pending
        pushes the interval out, because the force is finite.
        """
        base = (OUT_OF_SERVICE_COMMITMENT if fault in OUT_OF_SERVICE_FAULTS
                else SERVICE_AFFECTING_COMMITMENT)
        load = len(self.pending()) * LOAD_MINUTES_PER_PENDING
        return received + timedelta(minutes=base + load + slack_minutes)

    def receive(self, now: datetime, slack_minutes: int = 0,
                fault: Optional[str] = None,
                record: Optional[LineRecord] = None,
                repeat_of: Optional[str] = None) -> TroubleReport:
        """
        Take a new report onto the pending list.

        Args:
            now: Time the report was received
            slack_minutes: Extra commitment time the difficulty allows
            fault: Force a particular electrical condition
            record: Reuse an existing line record, as a repeat does
            repeat_of: The report number this one came back from

        Returns:
            The report that was created
        """
        condition = fault or self._choose_fault()
        line_record = record or self._make_record(condition)
        line_record.fault = condition
        symptom = self.rng.choice(REPORT_SYMPTOMS.get(condition, ('Trouble',)))
        report = TroubleReport(
            number=self._next_number(),
            record=line_record,
            symptom=symptom,
            received=now,
            commitment=self._commitment(condition, now, slack_minutes),
            repeat_of=repeat_of,
        )
        self.reports[report.number] = report
        self.order.append(report.number)
        return report

    def open_shift(self, now: datetime, slack_minutes: int = 0) -> List[TroubleReport]:
        """Seed the pending list a shift starts with."""
        count = self.rng.randint(*OPENING_BACKLOG)
        opened = []
        for index in range(count):
            received = now - timedelta(minutes=self.rng.randint(20, 240))
            report = self.receive(received, slack_minutes)
            # Reports held over have already had time charged against them.
            report.spend(self.rng.randint(0, 30))
            opened.append(report)
            del index
        return opened

    # -- access ----------------------------------------------------------

    def pending(self) -> List[TroubleReport]:
        """Return open reports, nearest commitment first."""
        open_reports = [
            self.reports[number] for number in self.order
            if self.reports[number].status != STATUS_CLOSED
        ]
        return sorted(open_reports, key=lambda report: report.due_in())

    def closed(self) -> List[TroubleReport]:
        """Return closed reports, most recently closed first."""
        done = [
            self.reports[number] for number in self.order
            if self.reports[number].status == STATUS_CLOSED
        ]
        return sorted(done, key=lambda report: report.closed_at or datetime.min,
                      reverse=True)

    def find(self, token: str) -> Optional[TroubleReport]:
        """
        Look up a report by number, by telephone number, or by position.

        A craftsperson at the desk refers to a report every one of these ways,
        so all three resolve.
        """
        token = token.strip().upper()
        if token in self.reports:
            return self.reports[token]
        if not token.startswith('TR-') and f"TR-{token}" in self.reports:
            return self.reports[f"TR-{token}"]

        digits = ''.join(character for character in token if character.isdigit())
        if len(digits) in (7, 10):
            for report in self.pending():
                record = report.record
                if digits.endswith(record.nxx + record.line):
                    return report

        if token.isdigit():
            position = int(token)
            pending = self.pending()
            if 1 <= position <= len(pending):
                return pending[position - 1]
        return None

    # -- working ---------------------------------------------------------

    def record_test(self, report: TroubleReport, note: str,
                    minutes: int = COST_MLT) -> None:
        """Note a measurement against a report and charge the time."""
        report.tested = True
        report.test_notes.append(note)
        if report.status == STATUS_PENDING:
            report.status = STATUS_TESTED
        report.spend(minutes)

    def dispatch(self, report: TroubleReport, force: str) -> str:
        """
        Send a repair force and return what the field reports back.

        Dispatching to the wrong place is the expensive mistake it was: the
        trip is charged against the commitment and the trouble is still there.
        """
        fault = FAULTS[report.record.fault]
        wanted = fault.dispatch
        report.dispatched_to = force

        if force.lower() != wanted.lower():
            report.spend(COST_WRONG_DISPATCH)
            report.status = STATUS_DISPATCHED
            return (f"{force} reports nothing found at their end. "
                    f"{COST_WRONG_DISPATCH} minutes charged against the "
                    f"commitment.")

        low, high = fault.typical_minutes
        repair = self.rng.randint(low, high)
        report.spend(repair)
        report.status = STATUS_DISPATCHED
        report.field_finding = fault.code
        if fault.code == 'NONE':
            return (f"{force} reports the line tests good at the station. "
                    f"{repair} minutes charged.")
        return (f"{force} reports {fault.name.lower()} located and cleared. "
                f"{repair} minutes charged.")

    def close(self, report: TroubleReport, disposition: int,
              found: Optional[str], now: datetime,
              count_commitments: bool) -> bool:
        """
        Close a report and judge the disposition against the truth.

        Returns:
            Whether the report was closed correctly
        """
        report.spend(COST_CLOSE)
        report.status = STATUS_CLOSED
        report.disposition = disposition
        report.found = found
        report.closed_at = now
        report.missed_commitment = count_commitments and report.overdue()

        truth = report.record.fault
        if disposition == 8:
            correct = truth == 'NONE'
        else:
            correct = truth != 'NONE' and found == truth

        report.correct = correct
        self.closed_count += 1
        return correct

    def should_repeat(self, report: TroubleReport, chance: float) -> bool:
        """
        Return whether a wrongly closed report comes back.

        A report closed as no trouble found on a line that really is faulty is
        the classic repeat. So is a report closed against the wrong fault: the
        real one was never touched.
        """
        if report.correct:
            return False
        if report.record.fault == 'NONE':
            # Nothing was wrong; a wrong disposition here costs the index but
            # does not bring the customer back.
            return False
        return self.rng.random() < chance

    def repeat(self, report: TroubleReport, now: datetime,
               slack_minutes: int = 0) -> TroubleReport:
        """Bring a wrongly closed report back on the same line."""
        self.repeat_count += 1
        return self.receive(
            now, slack_minutes,
            fault=report.record.fault,
            record=report.record,
            repeat_of=report.number,
        )

    def full(self) -> bool:
        """Return whether the pending list is at its working limit."""
        return len(self.pending()) >= MAX_PENDING


def disposition_name(code: int) -> str:
    """Return the published name of a disposition code."""
    disposition = DISPOSITIONS.get(code)
    return disposition.name if disposition else 'Unknown'


def valid_force(force: str) -> Optional[str]:
    """Return the canonical dispatch force name matching a player's word."""
    lowered = force.strip().lower()
    for candidate in DISPATCH_FORCES:
        if candidate.lower() == lowered or candidate.lower().startswith(lowered):
            return candidate
    aliases = {
        'co': 'Central office', 'office': 'Central office',
        'osp': 'Outside plant', 'plant': 'Outside plant',
        'cable': 'Cable repair', 'installer': 'Station',
    }
    return aliases.get(lowered)
