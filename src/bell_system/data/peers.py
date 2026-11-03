"""
The simulated peers the tour ledger places a tour against.

No source consulted publishes a distribution of repair times or of
dispositions that matched the line for craftspeople, so none is claimed.
These are the simulation's own: ten careers per difficulty, played by the
bot in ``tools/index_calibration.py``, one value per decile. The ledger says
so wherever it prints them.

``python3 tools/index_calibration.py peers`` regenerates this file. It is
run again whenever the balance changes, because a peer who is quicker than
a player on the old board says nothing about the new one.

Each tuple is ten values in ascending order, the middle of each tenth of
the tours the bot played. The ledger counts how many of the ten the player
beats. Only aggregates are kept: nothing here is about any report, and the
tuples carry no way back to a board.
"""

from typing import Dict, Tuple

# False while these are placeholders, and the ledger prints nothing then: the
# run that writes real numbers sets it True. It is made against the final
# balance.
GENERATED = False

PEERS: Dict[str, Dict[str, Tuple[float, ...]]] = {
    # mttr: minutes, received to close, averaged over the tour's repairs.
    # accuracy: percent of the tour's closes that matched the line.
    'fun': {
        'mttr': (60.0, 75.0, 90.0, 105.0, 120.0, 135.0, 150.0, 170.0,
                 195.0, 230.0),
        'accuracy': (50.0, 58.0, 65.0, 72.0, 78.0, 83.0, 88.0, 92.0,
                     96.0, 100.0),
    },
    'craft': {
        'mttr': (60.0, 75.0, 90.0, 105.0, 120.0, 135.0, 150.0, 170.0,
                 195.0, 230.0),
        'accuracy': (50.0, 58.0, 65.0, 72.0, 78.0, 83.0, 88.0, 92.0,
                     96.0, 100.0),
    },
}
