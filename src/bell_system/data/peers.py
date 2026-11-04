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

PEERS: Dict[str, Dict[str, Tuple[float, ...]]] = {
    'fun': {
        'mttr': (234.6, 321.1, 365.6, 387.6, 412.0, 440.4, 473.9, 507.3, 552.8, 640.1),
        'accuracy': (45.5, 55.6, 64.3, 71.4, 77.2, 81.8, 87.5, 92.3, 100.0, 100.0),
    },
    'craft': {
        'mttr': (179.2, 230.1, 261.5, 295.2, 329.1, 359.6, 387.0, 421.9, 467.3, 544.5),
        'accuracy': (45.5, 55.6, 64.3, 70.8, 76.9, 81.8, 86.7, 91.8, 95.7, 100.0),
    },
}
