"""
Something odd in the toll counts, and a note about it.

A trunk group's counts go wrong in a way congestion does not: attempts far
above the hour's usual and an average hold of a few seconds, nearly all of
it in the small hours, from a handful of originating lines. The counts show
it and a colleague says what it looks like. That is the whole of the
thread. It is detection and history; it names no method, gives no tone,
number or sequence, and tells the player nothing to do, because there is
nothing for a test desk to do about it and a count cannot say why.

The history is sourced. Until 1976 signalling in the Bell System was almost
entirely carried on the channel that carried the voice (E&O, signalling,
printed p. 272), and "reduction of fraud" is one of the eight needs listed
for common-channel signalling (E&O, printed p. 282). Everything else is
the simulation's own and says so: the group, the counts and the case are
invented, and the block that shows them carries a line to that effect.
"""

from typing import Dict, List

from ..seeding import stream

# The tours the counts show it on, and the minutes into the tour at which
# they begin to and the note arrives. Toll is signed off on the eighth tour
# at the soonest, and the thread is there for whoever has it.
FIRST_TOUR = 8
LAST_TOUR = 11
SHOWS_AFTER = 90
MAIL_AFTER = 150

# In the career's ledger once the note has been delivered, so that a
# resumed career is not told twice.
LEDGER = 'fraud:mailed'

GROUP = 'TG 0417'
ROUTE = 'NWRKNJ-ALBYNY'

# What the group does on an ordinary day, for the counts to be set against.
NORMAL_SEIZURES = 312
NORMAL_HOLD = 146

INVENTED = ("The group, the counts and the case are invented for this "
            "simulation.")


def live(tour: int, minutes: int) -> bool:
    """Whether the counts show it at this point of this tour."""
    return FIRST_TOUR <= tour <= LAST_TOUR and minutes >= SHOWS_AFTER


def mail_due(tour: int, minutes: int) -> bool:
    """Whether the note has come by this point of this tour."""
    return FIRST_TOUR <= tour <= LAST_TOUR and minutes >= MAIL_AFTER


def figures(tour: int, seed: str = '') -> Dict[str, int]:
    """
    The counts for a tour, the same however often they are looked at.

    Drawn from a generator of their own and not the desk's, so that looking
    at them changes nothing else. The career's seed is part of it, so that
    two careers see different counts.
    """
    rng = stream(seed, 'fraud', tour)
    return {
        'seizures': rng.randint(1100, 1500),
        'hold': rng.randint(6, 11),
        'lines': rng.randint(3, 5),
        'night': rng.randint(72, 86),
    }


def exception_block(tour: int, seed: str = '') -> List[str]:
    """The holding-time exception as the traffic counts print it."""
    seen = figures(tour, seed)
    return [
        'HOLDING-TIME EXCEPTION',
        '=' * 40,
        f"{GROUP}  {ROUTE}",
        f"Seizures per hour:        {seen['seizures']:,}"
        f"   (usual {NORMAL_SEIZURES})",
        f"Average holding time:     {seen['hold']} sec"
        f"   (usual {NORMAL_HOLD} sec)",
        f"Originating lines:        {seen['lines']} of 4,100 carry the excess",
        f"Midnight to 5 am:         {seen['night']}% of the excess",
        '',
        f"{INVENTED} A count says that it happened and not why.",
    ]


def note(tour: int, seed: str = '') -> List[str]:
    """What the transmission engineer wrote about it."""
    seen = figures(tour, seed)
    return [
        f"Looked at the {GROUP} holding times. It is not congestion.",
        f"Seizures are {seen['seizures'] / NORMAL_SEIZURES:.1f} times the "
        f"hour's usual and the average hold is {seen['hold']} seconds,",
        f"and {seen['night']}% of the excess is between midnight and 5 am, "
        f"from {seen['lines']} lines.",
        "Heavy demand does not look like that.",
        "Signaling on a trunk like this one is still carried on the channel",
        "that carries the voice. Until 1976 that was nearly all of it, and it",
        "is the only reason a customer's line could show in a trunk count",
        "this way. Common-channel signaling is meant to end it, and reduction",
        "of fraud is on the list of what it is for.",
        "The counts have gone to Security. It is theirs now, and it is not a",
        "trouble on any line or trunk that you could clear.",
        f"[{INVENTED}]",
    ]
