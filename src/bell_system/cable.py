"""
The outside plant cable, and where the water is.

A trouble report names a cable and a pair. Until now those were two random
numbers, which meant the most characteristic fault in the whole book could
not actually happen: wet cable is documented as dropping insulation
resistance across many pairs at once, and the notes the previous tour left
in /usr/users/sysop warn you about sending six separate crews to one
sheath - but the generator assigned faults one line at a time, so six
reports off one cable never arrived and the advice could not be taken.

This is the structure that makes it possible.

CABLE STRUCTURE

Exchange cable is built in binder groups of twenty-five pairs, each group
wrapped in a coloured binder that follows the same 25-pair colour code as
the pairs inside it: group one is white-blue, group two white-orange, and
so on. Twenty-four groups make six hundred pairs, which is as far as the
scheme goes on its own - violet-slate is never used as a binder - and
larger cables bundle the six-hundred-pair units under a second binder.
That structure is externally sourced and is why water is a binder group
problem rather than a whole-cable problem: it enters at a point in the
sheath and soaks what is next to it.

PRESSURE

Cable was pressurised with dry air to keep water out, at a few pounds,
and monitored: a pressure loss came first and the water came after. That
is why a wet section here has a pressure reading that has already fallen
by the time the first report arrives, and why the pressure contactor
alarm is the thing that could have told you first.
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Pairs to a binder group. The whole of the 25-pair colour code follows from
# this number, and so does the size of a wet section.
PAIRS_PER_BINDER = 25

# Binder groups under one unit binder. The twenty-fifth colour combination,
# violet-slate, is not used as a binder, which is why six hundred pairs is
# where the scheme stops and larger cables use super-units.
BINDERS_PER_UNIT = 24

# The 25-pair colour code. A pair's colours are its tip colour from the first
# sequence and its ring colour from the second; a binder group takes the
# colours of the pair with its own number.
TIP_COLOURS: Tuple[str, ...] = ('White', 'Red', 'Black', 'Yellow', 'Violet')
RING_COLOURS: Tuple[str, ...] = ('Blue', 'Orange', 'Green', 'Brown', 'Slate')

# Working pressure in a pressurised sheath, in pounds per square inch. Dry
# air at a few pounds; the figure is externally sourced and is the level a
# sheath is held at, not a limit.
NOMINAL_PSI = 5.0

# Below this the contactor alarms. The simulation's own working threshold.
ALARM_PSI = 2.5

# How many pairs in a wet binder group eventually report. Water does not take
# the whole group: some pairs are drier than others and some serve customers
# who are out. The range is the simulation's own.
SECTION_REPORTS = (3, 7)

# Chance per shift-minute that an unrepaired wet section takes another pair,
# before weather. The simulation's own, set so a section fills over a tour
# rather than all at once.
SPREAD_PER_MINUTE = 0.010


def binder_colour(binder: int) -> str:
    """
    Return the colour of a binder group, from the 25-pair colour code.

    Group one is white-blue and group twenty-four is violet-brown. Asking
    for the twenty-fifth gets violet-slate, which is a real pair colour and
    is never used as a binder.
    """
    index = (binder - 1) % (len(TIP_COLOURS) * len(RING_COLOURS))
    return (f"{TIP_COLOURS[index // len(RING_COLOURS)]}-"
            f"{RING_COLOURS[index % len(RING_COLOURS)]}")


def binder_of(pair: int) -> int:
    """Return which binder group a pair number falls in."""
    return (pair - 1) // PAIRS_PER_BINDER + 1


class WetSection:
    """
    Water in one binder group of one cable.

    Holds which pairs have reported, how many are going to, and what the
    sheath pressure has fallen to. One splicer trip repairs the section, not
    the pair - which is the whole point of modelling it.
    """

    def __init__(self, cable: int, binder: int, capacity: int,
                 opened: datetime):
        self.cable = cable
        self.binder = binder
        self.capacity = capacity
        self.opened = opened
        self.repaired_at: Optional[datetime] = None
        # Pairs that have reported, and the report on each.
        self.pairs: Dict[int, str] = {}
        self.psi = NOMINAL_PSI

    @property
    def first_pair(self) -> int:
        """The lowest pair number in this binder group."""
        return (self.binder - 1) * PAIRS_PER_BINDER + 1

    @property
    def last_pair(self) -> int:
        """The highest pair number in this binder group."""
        return self.binder * PAIRS_PER_BINDER

    @property
    def repaired(self) -> bool:
        """Whether a splicer has been to it."""
        return self.repaired_at is not None

    @property
    def full(self) -> bool:
        """Whether every pair this section is going to take has reported."""
        return len(self.pairs) >= self.capacity

    def colour(self) -> str:
        """The binder group's colour, for a splicer who has to find it."""
        return binder_colour(self.binder)

    def contains(self, cable: int, pair: int) -> bool:
        """Whether a cable and pair fall in this section."""
        return cable == self.cable and self.first_pair <= pair <= self.last_pair

    def take_pair(self, rng: random.Random) -> Optional[int]:
        """
        Return a pair in this group that has not reported yet, or None.

        Water spreads to what is next to it, so the pair chosen is near the
        ones already wet rather than anywhere in the group.
        """
        free = [pair for pair in range(self.first_pair, self.last_pair + 1)
                if pair not in self.pairs]
        if not free:
            return None
        if not self.pairs:
            return rng.choice(free)
        seed = rng.choice(list(self.pairs))
        free.sort(key=lambda pair: (abs(pair - seed), pair))
        return free[min(rng.randrange(1, 4), len(free)) - 1]

    def reserve(self, pair: int) -> None:
        """
        Take a pair out of the group before the report exists.

        Two calls must not hand out the same pair, so the pair is held the
        moment it is chosen and the report number is attached afterwards.
        """
        self.pairs.setdefault(pair, '')
        # Each pair that goes is another point the air is getting out of.
        self.psi = max(0.0, round(self.psi - 0.55, 2))

    def record(self, pair: int, number: str) -> None:
        """Attach a report number to a pair already reserved in this group."""
        if pair not in self.pairs:
            self.reserve(pair)
        self.pairs[pair] = number

    def alarming(self) -> bool:
        """Whether the pressure contactor on this sheath would be alarming."""
        return self.psi < ALARM_PSI and not self.repaired

    def describe(self) -> str:
        """One line for a listing."""
        state = 'repaired' if self.repaired else f"{self.psi:.1f} psi"
        return (f"cable {self.cable} binder {self.binder} "
                f"({self.colour()}), pairs {self.first_pair}-{self.last_pair}, "
                f"{len(self.pairs)} reported, {state}")


class CablePlant:
    """
    The cables this wire centre serves, and the water in them.

    Holds no line records and no reports: it knows only which binder groups
    are wet, and the report desk asks it where to put the next wet pair.
    """

    def __init__(self, rng: random.Random, cable_count: int = 88):
        self.rng = rng
        self.cable_count = cable_count
        self.sections: List[WetSection] = []

    # -- where water is --------------------------------------------------

    def open_sections(self) -> List[WetSection]:
        """Wet sections a splicer has not been to yet."""
        return [section for section in self.sections if not section.repaired]

    def section_at(self, cable: int, pair: int) -> Optional[WetSection]:
        """Return the open wet section covering a cable and pair, if any."""
        for section in self.open_sections():
            if section.contains(cable, pair):
                return section
        return None

    def wet_pair(self, now: datetime) -> Tuple[int, int]:
        """
        Return the cable and pair the next wet report should land on.

        An open section that has not taken all its pairs takes this one:
        that is what makes six reports arrive off one sheath. Only when
        every open section is full does water start somewhere new.
        """
        candidates = [section for section in self.open_sections()
                      if not section.full]
        section = (self.rng.choice(candidates) if candidates
                   else self._new_section(now))
        pair = section.take_pair(self.rng)
        if pair is None:
            section = self._new_section(now)
            pair = section.take_pair(self.rng) or section.first_pair
        section.reserve(pair)
        return section.cable, pair

    def attach(self, cable: int, pair: int, number: str) -> None:
        """Note which report a wet pair produced, once it has a number."""
        section = self.section_at(cable, pair)
        if section is not None:
            section.record(pair, number)

    def _new_section(self, now: datetime) -> WetSection:
        """Start water in a binder group nothing is already wet in."""
        for _ in range(40):
            cable = self.rng.randint(1, self.cable_count)
            binder = self.rng.randint(1, BINDERS_PER_UNIT)
            if not any(existing.cable == cable and existing.binder == binder
                       for existing in self.open_sections()):
                break
        else:  # pragma: no cover - only when every group is already wet
            cable = self.rng.randint(1, self.cable_count)
            binder = self.rng.randint(1, BINDERS_PER_UNIT)
        section = WetSection(cable, binder,
                             self.rng.randint(*SECTION_REPORTS), now)
        self.sections.append(section)
        return section

    def dry_pair(self) -> Tuple[int, int]:
        """
        Return a cable and pair for a fault that is not water.

        Deliberately not inside an open wet section: a dry fault on a wet
        pair would make the pattern unreadable, and the pattern is the
        thing this whole module exists to make readable.
        """
        for _ in range(40):
            cable = self.rng.randint(1, self.cable_count)
            pair = self.rng.randint(1, BINDERS_PER_UNIT * PAIRS_PER_BINDER)
            if self.section_at(cable, pair) is None:
                return cable, pair
        return cable, pair

    # -- working it ------------------------------------------------------

    def repair(self, section: WetSection, now: datetime) -> List[str]:
        """
        A splicer has been to the section. Return the reports it clears.

        One trip repairs the sheath, which repairs every pair in it. That is
        the reward for noticing before dispatching six times, and it is what
        actually happened: the splicer opens the sheath once.
        """
        section.repaired_at = now
        section.psi = NOMINAL_PSI
        return [number for number in section.pairs.values() if number]

    def spread(self, minutes: int, rain: float) -> int:
        """
        Let unrepaired water take more of its binder group.

        Rain is the documented reason wet cable gets worse, so the rate is
        multiplied by how hard it is raining. Returns how many pairs went,
        which the desk turns into reports.

        Args:
            minutes: Shift minutes elapsed since the last call
            rain: 0.0 for dry, 1.0 for the heaviest the weather models
        """
        gone = 0
        for section in self.open_sections():
            if section.full:
                continue
            chance = SPREAD_PER_MINUTE * minutes * (1.0 + 3.0 * rain)
            if self.rng.random() < chance:
                gone += 1
        return gone
