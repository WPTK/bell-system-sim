"""
The weather over the wire centre, and what it does to the plant.

One documented fact drives this module: water in a cable sheath drops
insulation resistance across the pairs in a binder group, and rain is what
makes it worse. The fault table has said so since it was written - "worsens
with rain" - and until now there was no rain for it to worsen with.

WHAT IS GROUNDED AND WHAT IS NOT

Grounded: that wet cable is a rain-driven fault, that a pressurised sheath
loses pressure before it takes water, and that November in the mid-Atlantic
is a wet month.

Not grounded, and marked here rather than implied: the actual weather over
northern New Jersey on 14 November 1983. Daily climate records for that date
were not reachable from this project, so the conditions below are the
simulation's own, generated for the shift, and no claim is made that they
are what really happened. A shift is not always wet; whether this one is
gets decided when the shift opens.
"""

import random
from typing import Dict, List, NamedTuple, Optional, Tuple


class Condition(NamedTuple):
    """One weather condition and what it does to the outside plant."""

    key: str
    label: str
    # 0.0 dry, 1.0 the heaviest this models. Multiplies how fast water
    # spreads through a binder group.
    rain: float
    # What a craftsperson standing outside would say about it.
    note: str


# The conditions this simulation models, driest first. Temperatures are not
# attached to a condition because they are a property of the day rather than
# the hour; the shift picks a range when it opens.
CONDITIONS: Dict[str, Condition] = {
    'CLEAR': Condition('CLEAR', 'Clear', 0.0,
                       'Cold and bright. Nothing is getting worse today.'),
    'CLOUDY': Condition('CLOUDY', 'Overcast', 0.0,
                        'Grey and holding. The barometer is going the wrong '
                        'way but nothing is falling yet.'),
    'DRIZZLE': Condition('DRIZZLE', 'Drizzle', 0.35,
                         'Fine rain, the kind that soaks a splicer through '
                         'in an hour and never looks like much.'),
    'RAIN': Condition('RAIN', 'Rain', 0.70,
                      'Steady rain. Anything already wet is getting wetter '
                      'and the manholes are filling.'),
    'HEAVY': Condition('HEAVY', 'Heavy rain', 1.00,
                       'Coming down hard. Water is finding every opening in '
                       'every sheath that has one.'),
}

# Order for a forecast listing and for stepping between neighbours.
SEQUENCE: Tuple[str, ...] = ('CLEAR', 'CLOUDY', 'DRIZZLE', 'RAIN', 'HEAVY')

# How the shift's weather is disposed overall. A regime is picked when the
# shift opens and the hour-to-hour walk is pulled toward it. The weights are
# the simulation's own, set so most tours are dry or grey and a wet tour is
# uncommon enough to be worth remarking on.
REGIMES: Tuple[Tuple[str, int], ...] = (
    ('CLEAR', 30), ('CLOUDY', 34), ('DRIZZLE', 20), ('RAIN', 12), ('HEAVY', 4),
)

# How much each regime's weight is allowed to grow as a career goes on. A
# career walks from mid-November to the last day of December, so a later
# tour being wetter than an early one is the calendar rather than a
# difficulty knob - and the difficulty setting still governs only how
# forgiving the scoring is. CLEAR does not grow at all, so what these do is
# move weight off the dry end without ever making a dry tour impossible.
WET_LEAN: Dict[str, float] = {
    'CLEAR': 0.0, 'CLOUDY': 0.2, 'DRIZZLE': 0.6, 'RAIN': 1.2, 'HEAVY': 1.5,
}

# Minutes of shift time between weather changes. Weather does not turn on a
# minute; an hour is about right and is the interval a craftsperson would
# notice it at.
STEP_MINUTES = 60

# November temperatures in the mid-Atlantic, in degrees Fahrenheit. The
# simulation's own working range, not a record of any particular day.
TEMPERATURE_RANGE = (34, 54)


class Weather:
    """
    The weather over this wire centre for the length of one shift.

    Advanced by the shift clock in whole hours. Holds the current condition,
    the regime the shift is pulled toward, and the temperature.
    """

    def __init__(self, rng: Optional[random.Random] = None,
                 wet_bias: float = 0.0):
        """
        Args:
            rng: The generator to draw from
            wet_bias: 0.0 for mid-November, 1.0 for the end of December.
                Leans the regime draw toward the wet end without ever
                closing off a dry tour.
        """
        self.rng = rng or random.Random()
        lean = max(0.0, min(1.0, wet_bias))
        keys = [key for key, _ in REGIMES]
        weights = [weight * (1.0 + lean * WET_LEAN[key])
                   for key, weight in REGIMES]
        self.regime = self.rng.choices(keys, weights=weights)[0]
        # A shift starts somewhere near its regime rather than at it.
        start = SEQUENCE.index(self.regime)
        drift = self.rng.choice((-1, 0, 0, 1))
        self.key = SEQUENCE[max(0, min(len(SEQUENCE) - 1, start + drift))]
        low, high = TEMPERATURE_RANGE
        self.temperature = self.rng.randint(low, high)
        self._minutes = 0
        self.history: List[Tuple[int, str]] = [(0, self.key)]

    # -- what it is ------------------------------------------------------

    @property
    def condition(self) -> Condition:
        """The condition right now."""
        return CONDITIONS[self.key]

    @property
    def rain(self) -> float:
        """How hard it is raining, 0.0 to 1.0, for the plant to answer to."""
        return self.condition.rain

    @property
    def wet(self) -> bool:
        """Whether anything is falling."""
        return self.rain > 0.0

    def label(self) -> str:
        """The condition and the temperature, as a craftsperson would say it."""
        return f"{self.condition.label}, {self.temperature}F"

    # -- what it does ----------------------------------------------------

    def advance(self, shift_minutes: int) -> Optional[str]:
        """
        Move the weather on to a given point in the shift.

        Returns a line worth saying out loud if the weather changed, and
        None if it did not. Weather changes at most one step at a time,
        pulled toward the shift's regime: it does not go from clear to
        heavy rain inside an hour.

        Args:
            shift_minutes: Minutes into the shift

        Returns:
            What changed, or None
        """
        if shift_minutes < self._minutes + STEP_MINUTES:
            return None
        self._minutes = shift_minutes - (shift_minutes % STEP_MINUTES)

        here = SEQUENCE.index(self.key)
        target = SEQUENCE.index(self.regime)
        if here < target:
            step = self.rng.choices((1, 0, -1), weights=(55, 35, 10))[0]
        elif here > target:
            step = self.rng.choices((-1, 0, 1), weights=(55, 35, 10))[0]
        else:
            step = self.rng.choices((0, 1, -1), weights=(60, 20, 20))[0]

        moved = max(0, min(len(SEQUENCE) - 1, here + step))
        if moved == here:
            return None
        was = self.condition.label
        self.key = SEQUENCE[moved]
        self.temperature += self.rng.choice((-2, -1, 0, 0, 1))
        self.history.append((self._minutes, self.key))
        return self._change_line(was)

    def _change_line(self, was: str) -> str:
        """What somebody in the building would say about the change."""
        now = self.condition.label
        if self.rain and not CONDITIONS[self.history[-2][1]].rain:
            return f"It has started raining. {was} to {now.lower()}."
        if not self.rain and CONDITIONS[self.history[-2][1]].rain:
            return f"The rain has stopped. {was} to {now.lower()}."
        if SEQUENCE.index(self.key) > SEQUENCE.index(self.history[-2][1]):
            return f"Weather worsening: {was.lower()} to {now.lower()}."
        return f"Weather easing: {was.lower()} to {now.lower()}."

    def outlook(self) -> str:
        """What the rest of the tour looks like, in one line."""
        here = SEQUENCE.index(self.key)
        there = SEQUENCE.index(self.regime)
        if here < there:
            return "Getting worse before it gets better."
        if here > there:
            return "Should ease off as the tour goes on."
        return "Settled, as far as anybody can tell."
