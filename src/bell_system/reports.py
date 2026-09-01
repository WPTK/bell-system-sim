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
from typing import Dict, List, Optional, Sequence, Tuple

from .cable import CablePlant
from .field import FieldForce
from .weather import Weather
from .data.regulars import REGULAR_SHARE, REGULARS
from .data.trouble import (
    DISPATCH_FORCES,
    FRAME_DEFECT_CODES,
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

# Minutes each action costs. Two clocks run and they are not the same clock.
#
# A report's commitment runs on elapsed time: the customer is out of service
# from the moment they report it until the moment somebody restores it, and
# the hours the repair force spends in a manhole count against that whether
# or not you are doing anything.
#
# Your own working day runs on your time. You are at a test desk. While the
# field force is out on one report you are working the next one, so their
# repair interval is charged to the commitment and not to you.
COST_MLT = 4
COST_CLOSE = 2
# Reading the frame's assignment record. Cheaper than a measurement, which
# is what makes checking the records before testing worth doing.
COST_FRAME_LOOKUP = 2
# Dialling a plant test number. Less than a mechanised test, and it tells
# you less: that trade is the reason to have both.
COST_PLANT_TEST = 2
COST_CALLBACK = 8
# Raising a force and writing the dispatch up.
COST_DISPATCH = 12
# The trip a wrong dispatch wastes, charged to the commitment.
COST_WRONG_DISPATCH = 45
# Working out why the wrong force found nothing, charged to you.
COST_WRONG_DISPATCH_DESK = 8

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
                 clli: str, fault: str = 'NONE',
                 frame_defect: Optional[str] = None,
                 regular: Optional[str] = None):
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
        # Set only on a central office equipment fault: what is actually
        # wrong on the frame, which the cross-connect record shows.
        self.frame_defect = frame_defect
        # Set on the four lines the bureau knows by heart. Keys
        # data.regulars.REGULARS, and is what makes the line card say you
        # have been here before.
        self.regular = regular

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
        # Elapsed time against the commitment, the repair force's hours
        # included.
        self.minutes_spent = 0
        # Your own time at the desk. Never more than the elapsed time.
        self.desk_minutes = 0
        self.tested = False
        self.test_notes: List[str] = []
        self.dispatched_to: Optional[str] = None
        self.field_finding: Optional[str] = None
        # Who went, and how long it took them to get there.
        self.crew: Optional[str] = None
        self.travel_minutes = 0
        # Set when a splicer's trip to another pair in the same binder group
        # repaired this one too. The report still has to be closed out; it
        # just does not need its own dispatch.
        self.sheath_repaired = False
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

    def spend(self, minutes: int, desk: Optional[int] = None) -> None:
        """
        Charge time against the report.

        Args:
            minutes: Elapsed time against the commitment
            desk: Your own time, when it differs from the elapsed time.
                Defaults to the same, which is right for anything you do
                yourself
        """
        self.minutes_spent += minutes
        self.desk_minutes += minutes if desk is None else desk

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
        # The cables this centre serves and the water in them. Wet cable is
        # a sheath fault, not a pair fault, so where a wet pair lands is the
        # plant's decision and not a pair of random numbers.
        self.plant = CablePlant(self.rng)
        self.weather = Weather(self.rng)
        # Who is available to go out, and where they are standing.
        self.force = FieldForce(self.rng)
        # Multipliers on what kind of trouble a report is, set by whichever
        # position sat down. Empty means uniform, which is what every
        # session did before positions differed.
        self.fault_bias: Dict[str, float] = {}
        # How deep a board this desk carries. Set by whichever position sat
        # down: a customer service desk holds more open reports than a
        # planning desk does, and the arrival rate alone cannot express
        # that, because arrival is damped by depth and so self-limiting.
        self.depth_limit = MAX_PENDING
        # The four lines this bureau knows by heart. Built lazily, once
        # each, and then handed back every time one of them reports: the
        # same LineRecord object every time, so the trouble history piles
        # up on one card the way it did.
        self._regulars: Dict[str, LineRecord] = {}

    # -- generation ------------------------------------------------------

    def regular_record(self, key: str, now: datetime) -> LineRecord:
        """
        Return a line record for one of the bureau's regulars.

        The line itself is drawn once and then never moves: the telephone
        number, the cable and pair, the frame appearance. Everything that
        identifies it is fixed, which is what makes it the same line every
        time and what lets the trouble history pile up on one card.

        What comes back is a fresh record carrying those fixed fields, not
        the stored one. The electrical fault lives on the record, so
        handing the same object back would mean this week's trouble
        rewriting last week's report - and the measurement is seeded from
        the fault, so an old report would measure as something it was
        never closed as.
        """
        held = self._regulars.get(key)
        if held is None:
            regular = REGULARS[key]
            wet = any(code == 'WET' for code, _ in regular.faults)
            cable, pair = (self.plant.wet_pair(now) if wet
                           else self.plant.dry_pair())
            held = self._regulars[key] = LineRecord(
                npa=self.npa, nxx=self.nxx,
                line=f"{self.rng.randint(0, 9999):04d}",
                name=regular.name,
                address=regular.address,
                cable=cable, pair=pair,
                class_of_service=regular.class_of_service,
                horizontal=f"{self.rng.randint(1, 24):02d}",
                vertical=f"{self.rng.randint(1, 52):02d}",
                line_equipment=f"{self.rng.randint(0, 3)}-"
                               f"{self.rng.randint(0, 7)}-"
                               f"{self.rng.randint(0, 19):02d}-"
                               f"{self.rng.randint(0, 9):02d}",
                clli=self.clli,
                regular=key,
            )
        return LineRecord(
            npa=held.npa, nxx=held.nxx, line=held.line,
            name=held.name, address=held.address,
            cable=held.cable, pair=held.pair,
            class_of_service=held.class_of_service,
            horizontal=held.horizontal, vertical=held.vertical,
            line_equipment=held.line_equipment,
            clli=held.clli, regular=held.regular,
        )

    def _draw_regular(self, now: datetime) -> Optional[Tuple[str, LineRecord]]:
        """
        Occasionally take the next report off a line the bureau knows.

        Returns the fault and the record together, because a regular's
        trouble is part of who they are: the drop over the bus route opens,
        the sheath on Sussex Street is wet, and the coin station in the
        lobby is nobody's fault at all.
        """
        if self.rng.random() >= REGULAR_SHARE:
            return None
        regular = REGULARS[self.rng.choice(list(REGULARS))]
        codes = [code for code, _ in regular.faults]
        weights = [weight for _, weight in regular.faults]
        fault = self.rng.choices(codes, weights=weights)[0]
        return fault, self.regular_record(regular.key, now)

    def _next_number(self) -> str:
        """Return the next report number in the bureau's series."""
        self._sequence += self.rng.randint(1, 4)
        return f"TR-{self._sequence:05d}"

    def _make_record(self, fault: str, now: datetime) -> LineRecord:
        """
        Build a line record carrying a given electrical condition.

        Cable and pair come from the plant rather than from two random
        numbers: a wet pair lands in a binder group that is already wet, and
        a dry fault deliberately does not, so that several reports off one
        sheath mean what they look like they mean.
        """
        line = f"{self.rng.randint(0, 9999):04d}"
        surname = self.rng.choice(_SURNAMES)
        initial = self.rng.choice(_INITIALS)
        cable, pair = (self.plant.wet_pair(now)
                       if fault == 'WET' else self.plant.dry_pair())
        classes = [code for code, _ in _CLASS_WEIGHTS]
        weights = [weight for _, weight in _CLASS_WEIGHTS]
        class_of_service = self.rng.choices(classes, weights=weights)[0]
        return LineRecord(
            npa=self.npa, nxx=self.nxx, line=line,
            name=f"{surname}, {initial}",
            address=f"{self.rng.randint(2, 1480)} {self.rng.choice(_STREETS)}",
            cable=cable,
            pair=pair,
            class_of_service=class_of_service,
            horizontal=f"{self.rng.randint(1, 24):02d}",
            vertical=f"{self.rng.randint(1, 52):02d}",
            line_equipment=f"{self.rng.randint(0, 3)}-"
                           f"{self.rng.randint(0, 7)}-"
                           f"{self.rng.randint(0, 19):02d}-"
                           f"{self.rng.randint(0, 9):02d}",
            clli=self.clli,
            fault=fault,
            frame_defect=(self.rng.choice(FRAME_DEFECT_CODES)
                          if fault == 'CO_EQUIP' else None),
        )

    def _choose_fault(self) -> str:
        """
        Pick the electrical condition behind a new report.

        The position sitting at the desk biases the draw. It is a bias and
        never a filter: no weight is ever zero, so a switching position
        still gets wet cable now and then and is never handed work whose
        vocabulary it has not been taught. With no position, or a position
        that sets no bias, this is a flat draw exactly as it always was.
        """
        bias = self.fault_bias
        if self.rng.random() < min(0.45, NO_TROUBLE_SHARE * bias.get('NONE', 1.0)):
            return 'NONE'
        if self.rng.random() < min(0.30, 0.07 * bias.get('ROH', 1.0)):
            return 'ROH'
        if not bias:
            return self.rng.choice(REAL_FAULTS)
        weights = [max(0.05, bias.get(fault, 1.0)) for fault in REAL_FAULTS]
        return self.rng.choices(REAL_FAULTS, weights=weights)[0]

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
        drawn = (self._draw_regular(now)
                 if fault is None and record is None else None)
        if drawn is not None:
            condition, line_record = drawn
        else:
            condition = fault or self._choose_fault()
            line_record = record or self._make_record(condition, now)
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
        if condition == 'WET':
            self.plant.attach(line_record.cable, line_record.pair,
                              report.number)
        return report

    def open_shift(self, now: datetime, slack_minutes: int = 0,
                   count: Optional[int] = None) -> List[TroubleReport]:
        """
        Seed the pending list a shift starts with.

        Args:
            now: When the shift begins
            slack_minutes: Extra commitment time the difficulty allows
            count: How many to deal. A first tour is dealt one, so that a
                new craftsperson learns the loop on a board they can see
                the whole of rather than on five reports at once.
        """
        count = self.rng.randint(*OPENING_BACKLOG) if count is None else count
        opened = []
        for index in range(count):
            received = now - timedelta(minutes=self.rng.randint(20, 240))
            report = self.receive(received, slack_minutes)
            # Reports held over have already had time charged against them,
            # by whoever worked the shift before you. It is not your time.
            report.spend(self.rng.randint(0, 30), desk=0)
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

    def dispatch(self, report: TroubleReport, force: str,
                 now: Optional[datetime] = None) -> str:
        """
        Send a repair force and return what the field reports back.

        Dispatching to the wrong place is the expensive mistake it was: the
        trip is charged against the commitment and the trouble is still there.
        """
        fault = FAULTS[report.record.fault]
        wanted = fault.dispatch
        now = now or report.received

        if report.sheath_repaired:
            # A splicer has already been to this binder group on somebody
            # else's report and the pair came back with it. Sending a
            # second crew to a sheath that is dry is the exact waste the
            # cable model exists to teach against, so it does not happen.
            report.dispatched_to = None
            return (f"{report.number} is on a sheath a splicer has already "
                    f"opened. The pair came back with the rest of the "
                    f"group.\nNobody needs to go. Close it out: code 5, "
                    f"found WET.")

        report.dispatched_to = force

        if force.lower() != wanted.lower():
            crew, travel, came_from = self.force.send(
                force, report.number, COST_WRONG_DISPATCH, now)
            report.spend(COST_WRONG_DISPATCH + COST_DISPATCH + travel,
                         desk=COST_DISPATCH + COST_WRONG_DISPATCH_DESK)
            report.status = STATUS_DISPATCHED
            if crew is None:
                return (f"Nobody free on {force.lower()}, which is just as "
                        f"well: the trouble is not theirs.")
            report.crew = crew.name
            report.travel_minutes = travel
            return (f"{crew.name} rolled from {came_from}, {travel} minutes, "
                    f"and found nothing at their end.\n"
                    f"{COST_WRONG_DISPATCH + travel} minutes charged against "
                    f"the commitment, and {crew.name} is now out on nothing.")

        low, high = fault.typical_minutes
        repair = self.rng.randint(low, high)
        crew, travel, came_from = self.force.send(
            force, report.number, repair, now)
        if crew is None:
            # Everybody who answers this category is already out. The job
            # does not vanish; it waits, and the wait is on the commitment.
            waiting = self.force.soonest_free(force, now)
            report.spend(COST_DISPATCH, desk=COST_DISPATCH)
            report.status = STATUS_PENDING
            report.dispatched_to = None
            if waiting is None:  # pragma: no cover - no crew for the category
                return f"Nobody answers {force} from this position."
            back = waiting.back_at().strftime('%H:%M')
            return (f"Nobody free on {force.lower()}. "
                    f"{waiting.crew.name} is on {waiting.report} and is not "
                    f"back before {back}.\n"
                    f"{report.number} stays on the board. Try again when "
                    f"somebody is in.")

        report.crew = crew.name
        report.travel_minutes = travel
        # The repair and the drive are the field force's time, not yours,
        # but both run against the customer's commitment.
        report.spend(repair + travel + COST_DISPATCH, desk=COST_DISPATCH)
        report.status = STATUS_DISPATCHED
        report.field_finding = fault.code
        went = (f"{crew.name} ({crew.title.lower()}) rolled from "
                f"{came_from}, {travel} minutes.")
        if fault.code == 'NONE':
            return (f"{went}\n{crew.name} reports the line tests good at "
                    f"the station. {repair} minutes on the job.")
        if fault.code == 'WET':
            return f"{went}\n" + self._repair_sheath(
                report, crew.name, repair)
        return (f"{went}\n{crew.name} reports {fault.name.lower()} located "
                f"and cleared. {repair} minutes on the job.")

    def _repair_sheath(self, report: 'TroubleReport', force: str,
                       repair: int) -> str:
        """
        A splicer has opened one sheath, which repairs every pair in it.

        This is the whole reason the cable plant is modelled. Water is a
        binder group fault: the splicer finds the opening, dries and
        reseals the section, and every wet pair in that group is fixed by
        the one trip. A craftsperson who reads the board before dispatching
        pays for one trip instead of six, which is the advice the previous
        tour left in their notes.
        """
        record = report.record
        section = self.plant.section_at(record.cable, record.pair)
        if section is None:
            return (f"{force} reports wet cable located and cleared. "
                    f"{repair} minutes charged.")

        cleared = self.plant.repair(section, report.received)
        others = [self.reports[number] for number in cleared
                  if number in self.reports
                  and number != report.number
                  and self.reports[number].status != STATUS_CLOSED]
        for other in others:
            # The sheath is dry. The other pairs in it were repaired by the
            # same trip and cost nothing further; they still have to be
            # closed out, which is the craftsperson's job and not the
            # splicer's.
            other.field_finding = 'WET'
            other.sheath_repaired = True
            if other.status == STATUS_PENDING:
                other.status = STATUS_TESTED

        lines = [f"{force} reports water in cable {section.cable}, binder "
                 f"{section.binder} ({section.colour()}), pairs "
                 f"{section.first_pair}-{section.last_pair}.",
                 f"Sheath opened, dried and resealed. {repair} minutes "
                 f"charged."]
        if others:
            numbers = ', '.join(sorted(other.number for other in others))
            lines.append('')
            lines.append(f"The one trip clears every pair in that group. "
                         f"{len(others)} other report"
                         f"{'' if len(others) == 1 else 's'} on this sheath "
                         f"can be closed without a further dispatch:")
            lines.append(f"  {numbers}")
        return '\n'.join(lines)

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
        """Return whether the pending list is at this desk's working limit."""
        return len(self.pending()) >= self.depth_limit


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
