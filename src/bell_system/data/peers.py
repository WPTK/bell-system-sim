"""
The simulated peers the tour ledger places a tour against.

No source consulted publishes a distribution of repair times or of
dispositions that matched the line for craftspeople, so none is claimed.
These are the simulation's own: careers played by the bot in
``tools/index_calibration.py`` at several skills and paces, one value per
decile. The ledger says so wherever it prints them.

Written by ``python3 tools/index_calibration.py peers``, not by hand, and
run again whenever the balance changes: a peer who is quicker than a player
on the old board says nothing about the new one.

Each tuple is ten values in ascending order, the middle of each tenth of
the tours played. ``mttr`` is minutes, received to close, averaged over the
tour's repairs; ``accuracy`` is the percent of the tour's closes that
matched the line. The ledger counts how many of the ten the player beats.
Only aggregates are kept: nothing here is about any report, and the tuples
carry no way back to a board.
"""

from typing import Dict, Tuple

# False while the numbers are placeholders, and the ledger prints nothing
# then. The run that writes real numbers sets it True.
GENERATED = True

# How they were played, so that this file can be written again from nothing.
# ``python3 tools/index_calibration.py peers 4`` plays these careers
# and writes the same numbers. A career is ``play_career(skill, difficulty,
# seed, dawdle=dawdle)``, seeds counting up from 1 on each difficulty across
# the skills, then the dawdles, then the careers.
CAREERS_PER_CELL = 4
SEEDS = (1, 48)
SKILLS = (0.55, 0.7, 0.85, 0.95)
# Minutes the peer sits on the clock after every close.
DAWDLES = (0, 20, 45)
# Times the peer asks again, a minute apart, for a crew that is out, before
# closing the report anyway.
CREW_WAITS = 6
TOURS = 13
# A tour counts toward the deciles only with this many closes.
MINIMUM_CLOSES = 5

PEERS: Dict[str, Dict[str, Tuple[float, ...]]] = {
    'fun': {
        'mttr': (224.9, 323.7, 366.2, 399.1, 426.6, 456.7, 500.9, 539.3, 585.7, 681.9),
        'accuracy': (46.2, 57.1, 66.7, 72.7, 77.8, 83.3, 88.9, 92.3, 100.0, 100.0),
    },
    'craft': {
        'mttr': (176.4, 235.8, 279.2, 314.2, 335.4, 364.4, 389.0, 425.2, 474.9, 571.4),
        'accuracy': (43.0, 56.2, 64.3, 71.4, 76.6, 81.0, 87.5, 91.7, 94.9, 100.0),
    },
}
