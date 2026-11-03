"""
The lines you keep coming back to.

Most reports are a name drawn from a hat and a pair drawn from the plant,
and they should be: that is what a day at a repair service bureau was.
But a bureau also had four or five lines everybody knew by heart, and
knowing them was most of what being good at the job looked like from the
outside.

These are those. Each has a reason it keeps reporting, and the reason is
electrical rather than narrative - the cable is genuinely in water, the
drop is genuinely on a pole a bus keeps clipping - so working out what is
wrong is still the same work. What changes is that the second time the
number comes up you have been here before, and the record says so.

Each one also has a year to get through. The card note is where a line
starts and the arc is where it goes: a few beats on named tours, each one
what the bureau would have written on the card by then, and an ending
before the last tour closes. A line is resolved when the plant is changed
so it stops reporting, and abandoned when the customer is gone. Either way
the last card is the last word, and a bureau that has stopped hearing from
a number it knew by heart is told so.

A beat is about the line and the people around it: the job on the order
list, the call that came in, who was written to. It never says what the
next report off the line will turn out to be. That stays in the readings.

Everything below is this simulation's own invention: the names, the
addresses and the histories. No customer record of any real Bell operating
company was consulted and none should be inferred. The street names are
the simulation's own and the card carries no city, so they stand wherever
the office is.
"""

from typing import Dict, NamedTuple, Optional, Sequence, Tuple

RESOLVED = 'resolved'
ABANDONED = 'abandoned'
OPEN = 'open'


class Beat(NamedTuple):
    """One thing that happened to a regular, from a named tour on."""

    tour: int
    # What the card says from this tour. Replaces the one before it.
    note: str
    # What the line is like to work from this tour, where it changed.
    faults: Optional[Sequence[Tuple[str, int]]] = None
    # RESOLVED or ABANDONED on the beat that ends the line's reports.
    ends: str = OPEN


class Regular(NamedTuple):
    """A line the bureau knows by heart."""

    key: str
    name: str
    address: str
    class_of_service: str
    # What is actually wrong with it, and how often. Weighted, because a
    # chronic line is not chronic in one way only: a wet sheath produces a
    # dry fault now and then and the pair is still wet underneath.
    faults: Sequence[Tuple[str, int]]
    # What the last craftsperson wrote on the card. One line, in the voice
    # of somebody who has been out there and is tired of it.
    note: str
    # When this line first came to the bureau's attention.
    since: str
    # What happens to it after the opening note, in tour order. The last
    # beat ends the line.
    arc: Sequence[Beat] = ()


REGULARS: Dict[str, Regular] = {
    'kowalczyk': Regular(
        key='kowalczyk',
        name='Kowalczyk, S',
        address='214 Sussex St',
        class_of_service='1FB',
        faults=(('WET', 6), ('GROUND', 2), ('NONE', 1)),
        note='Sheath is in water from the corner to the manhole and has '
             'been since the spring. Pumped twice. Splicing has the '
             'estimate.',
        since='March 1983',
        arc=(
            Beat(4, 'Splicing has the estimate approved. A work order is on '
                    'the board for the Sussex St cable and it has no date.'),
            Beat(7, 'S. Kowalczyk has rung the bureau twice to ask when. The '
                    'answer on the card is "before the holidays".',
                 faults=(('WET', 7), ('GROUND', 2), ('NONE', 1))),
            Beat(11, 'New cable in from the corner to the manhole and the '
                     'old run dead-ended. Nothing left to chase. This '
                     'line is closed out of the chronic file.',
                 ends=RESOLVED),
        ),
    ),
    'ferrante': Regular(
        key='ferrante',
        name='Ferrante, D',
        address='1109 Ocean Ave',
        class_of_service='COIN',
        faults=(('ROH', 6), ('SHORT', 2), ('NONE', 2)),
        note='Coin station in the lobby of a rooming house. Handset ends '
             'up off the hook most weekends. Line is fine. It is the '
             'building.',
        since='January 1983',
        arc=(
            Beat(3, 'Building changed managers. The collector has asked '
                    'the new one who to leave the key with, and has not '
                    'been told.'),
            Beat(5, 'Landlord has been written to about the lobby. No '
                    'answer. Nobody on the card can say who owns the '
                    'coin telephone now.'),
            Beat(7, 'Rooming house closed by the city. Coin telephone pulled '
                    'from the lobby on a disconnect order. Nobody left to '
                    'report it.',
                 ends=ABANDONED),
        ),
    ),
    'whitcomb': Regular(
        key='whitcomb',
        name='Whitcomb, A',
        address='87 Bergen Ave',
        class_of_service='1FR',
        faults=(('OPEN', 5), ('CROSS', 2), ('FEMF', 2)),
        note='Aerial drop crosses the bus route. Third open on this pair '
             'this year and every one of them within a week of weather. '
             'Wants a new drop, not another splice.',
        since='February 1983',
        arc=(
            Beat(3, 'Somebody has asked the bus company for a clearance on '
                    'the route. Nothing back yet.'),
            Beat(6, 'New drop is on the order list for the pole across the '
                    'lot.'),
            Beat(9, 'New drop placed on the far pole, well clear of the '
                    'bus route. A. Whitcomb called to say thank you, which '
                    'nobody on the card remembers happening before.',
                 ends=RESOLVED),
        ),
    ),
    'duchesne': Regular(
        key='duchesne',
        name='Duchesne, M',
        address='466 Central Ave',
        class_of_service='1MR',
        faults=(('CO_EQUIP', 5), ('FCG', 3), ('NONE', 1)),
        note="Answering line for a doctor's exchange. Frame appearance has "
             'been taken for a spare twice. Tag it and leave it tagged.',
        since='August 1983',
        arc=(
            Beat(4, "The tag has held since it went on. The doctor's exchange "
                    'rang the bureau to say so, and to say it was the '
                    'first time anyone had rung them back.'),
            Beat(8, "Doctor's exchange has asked for a second line on the "
                    'same number, rotary. Service order written. The first pair '
                    'stays tagged until it is in.',
                 faults=(('CO_EQUIP', 4), ('FCG', 3), ('NONE', 2))),
            Beat(12, 'Rotary in: two lines on the one number, tagged and on '
                     'different blocks. The exchange no longer depends on '
                     'one pair. Closed out of the chronic file.',
                 ends=RESOLVED),
        ),
    ),
}

# How often a new report comes off a line the bureau already knows, rather
# than off a fresh one. A bureau with four chronic lines and a wire centre
# of ten thousand does not see them one time in five, but a player working
# forty reports across a career has to meet them more than once for them to
# be anybody. This is the simulation's own figure and it is set for that.
REGULAR_SHARE = 0.18


def beat_at(regular: Regular, tour: int) -> Optional[Beat]:
    """Return the latest beat on or before a tour, or None before the first."""
    held = None
    for beat in regular.arc:
        if beat.tour <= tour:
            held = beat
    return held


def note_at(regular: Regular, tour: int) -> str:
    """Return what the card says on a tour: the latest beat's note."""
    beat = beat_at(regular, tour)
    return beat.note if beat else regular.note


def faults_at(regular: Regular, tour: int) -> Sequence[Tuple[str, int]]:
    """Return the weights the line's trouble is drawn from on a tour."""
    held = regular.faults
    for beat in regular.arc:
        if beat.tour <= tour and beat.faults is not None:
            held = beat.faults
    return held


def status_at(regular: Regular, tour: int) -> str:
    """Return OPEN, RESOLVED or ABANDONED for a line on a tour."""
    beat = beat_at(regular, tour)
    return beat.ends if beat else OPEN


def reporting_at(tour: int) -> Tuple[Regular, ...]:
    """Return the regulars still reporting on a tour."""
    return tuple(regular for regular in REGULARS.values()
                 if status_at(regular, tour) == OPEN)
