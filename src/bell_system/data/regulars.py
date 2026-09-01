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

Everything below is this simulation's own invention: the names, the
addresses and the histories. No customer record of any real Bell operating
company was consulted and none should be inferred. The street names come
from the same Jersey City pool the rest of the desk draws on.
"""

from typing import Dict, NamedTuple, Sequence, Tuple


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
    ),
}

# How often a new report comes off a line the bureau already knows, rather
# than off a fresh one. A bureau with four chronic lines and a wire centre
# of ten thousand does not see them one time in five, but a player working
# forty reports across a career has to meet them more than once for them to
# be anybody. This is the simulation's own figure and it is set for that.
REGULAR_SHARE = 0.18
