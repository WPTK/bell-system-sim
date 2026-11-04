"""
Causes that stand behind several reports at once.

A report is a symptom. Engineering and Operations says the measurement
plan counts "a quantification of symptoms rather than causes" (p. 679 [696]),
and says the attendant's screen shows "information on cable and other
equipment failures that are affecting the particular customer's circuit"
(p. 581 [598]). A case is the cause: one thing wrong in the plant or the
office, and three to five reports that are all it looks like from the
customer's end.

WHAT IS GROUNDED AND WHAT IS NOT

Grounded: that one failure can show up as many customers' troubles, that an
attendant is shown what other failures bear on a circuit, and that a
crossbar marker that cannot finish times out and leaves lines that cannot
complete calls (XB-III; E&O p. 802 [819]).

The simulation's own: that there are two kinds of case here, which of two or
three conditions each one turns out to be, how many reports each throws,
when in a tour they arrive, and all of the story around Marker 2. The sequence relay, the number 2, the "third trial" and
the eleven seconds are the story's and not the sources': SD_26030-01 has
none of them (the source-mining notes, section 1), and nothing here
claims it does.
"""

from typing import Dict, NamedTuple, Tuple


class CaseKind(NamedTuple):
    """One sort of shared cause, and everything particular to it."""

    key: str
    # The conditions a case of this kind may turn out to be, each with what
    # the crew that clears it says it found. Every member of one case has the
    # one condition, drawn when the case is planned. The force that clears
    # the case is the force that clears it (data.trouble.FAULTS), and a
    # field finding is the one place a case may say what was wrong.
    faults: Dict[str, str]
    # What the members have in common: 'frame', the line link frame their
    # line equipment is on, or 'cable'.
    shared: str
    # How a "see also" line says what they share. Never a fault, a force
    # or a close code.
    place: str
    # How many reports it throws, and when in the tour (shift minutes) they
    # arrive between.
    members: Tuple[int, int]
    window: Tuple[int, int]
    # Who says what when the third report comes in, and when the cause is
    # cleared. The sender is a key of npc.CRAFT; nothing here tells the
    # player what to do about it.
    sender: str
    opened: Tuple[str, ...]
    closed: Tuple[str, ...]


CASE_KINDS: Dict[str, CaseKind] = {
    'marker': CaseKind(
        key='marker', shared='frame',
        faults={
            'FCG': 'Marker 2 in aisle 4 has failed outright and was timing '
                   'out on every call it took. It is busied out and the '
                   'other marker has the frame.',
            'CO_EQUIP': 'Marker 2 in aisle 4 has failed outright and was '
                        'timing out on every call it took, and the line '
                        'link appearances it was holding are fouled. It is '
                        'busied out and the other marker has the frame.',
        },
        place='line link frame {where}',
        members=(3, 5), window=(25, 170),
        sender='rjohnson',
        opened=("That frame is in my aisle. Marker 2 took eleven seconds on",
                "a third trial earlier, and I have three off the one",
                "frame. I am only telling you where it is."),
        closed=("Marker 2 is out and the other one has the frame.",
                "Two years I have been saying it."),
    ),
    'dig': CaseKind(
        key='dig', shared='cable',
        # All three are loop trouble from a cable hit on the route, and the
        # force that clears each is Outside plant, not the sheath splicers:
        # a cable that is cut or crushed is not a wet one.
        faults={
            'OPEN': 'A trench crew has cut the cable and the pairs were '
                    'hanging in the ditch. Joined up and closed.',
            'SHORT': 'A trench crew has crushed the cable under a bucket '
                     'and the pairs were touching. Cut out, joined up and '
                     'closed.',
            'GROUND': 'A trench crew has torn the sheath off the cable and '
                      'bare pairs were lying in the wet ditch. Joined up '
                      'and closed.',
        },
        place='cable {where}',
        members=(3, 4), window=(30, 150),
        sender='lokafor',
        opened=("Somebody is digging on the route. I can hear the machine",
                "from here."),
        closed=("Joined up and closed. They did not call it in.",
                "They never do."),
    ),
}
