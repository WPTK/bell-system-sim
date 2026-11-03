"""
Commendations: the credit side of the record, beside the service index.

The index only ever takes marks off. A commendation is a name for something
done well, earned once, printed at the handoff and listed by qual(1), and
never taken back: a later bad tour does not lose one. They reward reading
the line correctly - a close that matched, a crew sent to the right place
first time, a line measured before it was closed - and nothing here is
earned by how much was done, and none for closing fast and guessing: each
one asks for a clean record over at least :data:`MINIMUM_CLOSES` reports, so
a tour of one report proves nothing and a tour of thirty with one wrong
close earns nothing.

The awards and their wording are the simulation's own. A letter of
commendation from a supervisor is period-plausible, but no source consulted
names any award, and none is claimed to have been a Bell System one
(SOURCES.md says so).

The tests are plain functions of :class:`Evidence`, a snapshot of the tour
and the career at the moment they are asked, so the table can be tested
without a terminal and a commendation cannot disagree with the counters
the KPIs are read from.
"""

from typing import Callable, Dict, NamedTuple, Tuple

# The fewest reports a tour, or a run of dispatches, must hold before a clean
# record means anything. Five is the simulation's own number, the same one
# the KPIs use to stop calling themselves PROVISIONAL.
MINIMUM_CLOSES = 5

# A run of correct closes, with no wrong one between, that earns "five
# straight". The simulation's own.
STRAIGHT_RUN = 5


class Evidence(NamedTuple):
    """What a commendation is judged on."""

    # This tour alone.
    closed: int
    wrong: int
    repeats: int
    missed: int
    # Closed having been measured first.
    measured: int
    # First dispatches of a report, and how many named the right force.
    dispatches: int
    dispatches_right: int
    # Customer reports left open past their commitment at the handoff. Only
    # known when the tour is being struck, so zero at any other time.
    late_open: int
    # Correct closes in a row, across tours, ending at the latest close.
    streak: int
    # Other reports one splicer's trip has just repaired. Only known when
    # the dispatch is made.
    cleared_by_one_trip: int


class Commendation(NamedTuple):
    """One thing worth a name."""

    key: str
    name: str
    # When it is asked: 'close', 'dispatch' or 'tour' (the handoff).
    when: str
    description: str
    test: Callable[[Evidence], bool]


def _clean_tour(evidence: Evidence) -> bool:
    return (evidence.closed >= MINIMUM_CLOSES and evidence.wrong == 0
            and evidence.repeats == 0 and evidence.missed == 0
            and evidence.late_open == 0)


def _every_line_measured(evidence: Evidence) -> bool:
    return (evidence.closed >= MINIMUM_CLOSES and evidence.wrong == 0
            and evidence.measured >= evidence.closed)


def _right_first_time(evidence: Evidence) -> bool:
    return (evidence.dispatches >= MINIMUM_CLOSES
            and evidence.dispatches_right == evidence.dispatches)


COMMENDATIONS: Tuple[Commendation, ...] = (
    Commendation(
        'first_clean_tour', 'First clean tour', 'tour',
        f"A tour of {MINIMUM_CLOSES} or more closes in which every one "
        "matched the line, none came back, no commitment was missed and "
        "nothing was handed over past its commitment.",
        _clean_tour),
    Commendation(
        'five_straight', 'Five straight', 'close',
        f"{STRAIGHT_RUN} closes in a row that matched the line, across "
        "tours if it took that long.",
        lambda evidence: evidence.streak >= STRAIGHT_RUN),
    Commendation(
        'right_first_time', 'Right the first time', 'tour',
        f"A tour in which every one of {MINIMUM_CLOSES} or more reports "
        "went to the right repair force on the first dispatch.",
        _right_first_time),
    Commendation(
        'every_line_measured', 'Every line measured', 'tour',
        f"A tour of {MINIMUM_CLOSES} or more closes, each one measured "
        "before it was closed and each one right.",
        _every_line_measured),
    Commendation(
        'one_trip', 'One trip, two lines', 'dispatch',
        "You measured a wet pair and sent the splicer, and the one trip "
        "repaired another report's pair on the same sheath as well.",
        lambda evidence: evidence.cleared_by_one_trip >= 1),
)

COMMENDATIONS_BY_KEY: Dict[str, Commendation] = {
    commendation.key: commendation for commendation in COMMENDATIONS}
