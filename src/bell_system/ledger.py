"""
The tour ledger: this tour's figures placed against simulated peers.

Two of the five measures are placed, the two a repair bureau is judged on at
the end of a tour: how long a repair took, and how often the close matched
the line. Each is set beside ten peers the simulation played itself
(``data/peers.py``) and nothing more is said: the peers are not a real
office, the figures are not Bell System figures, and nothing is scored.

Aggregates only (pillar 1). The ledger takes the tour's counts and no
report, so nothing it prints can say what was wrong with any line.
"""

from typing import Any, List, NamedTuple, Optional

from .data.peers import PEERS
from .reports import hours_minutes

HEADING = 'TOUR LEDGER'
PEER_COUNT = 10


class Placing(NamedTuple):
    """One figure and where it stands among the peers."""

    value: Optional[float]
    beats: Optional[int]


def accuracy_of(counts: Any) -> Optional[float]:
    """Percent of a tour's closes that matched the line, or None if none."""
    closed = counts['closed']
    return round(100.0 * (closed - counts['wrong']) / closed, 1) if closed \
        else None


def place_lower(value: Optional[float], peers: Any) -> Optional[int]:
    """How many peers a lower-is-better figure beats."""
    if value is None:
        return None
    return sum(1 for peer in peers if value < peer)


def place_higher(value: Optional[float], peers: Any) -> Optional[int]:
    """How many peers a higher-is-better figure beats."""
    if value is None:
        return None
    return sum(1 for peer in peers if value > peer)


def _of_ten(beats: int) -> str:
    """'6 of 10', which reads the same for any count."""
    return f"{beats} of {PEER_COUNT}"


def lines(career: Any) -> List[str]:
    """
    The ledger for the tour as it stands, as printed lines.

    Args:
        career: The career, which holds the tour's counts and difficulty

    Returns:
        Nothing where there are no peers for this difficulty. Otherwise a
        heading and, with too few closes to rest on, a line saying so and
        placing nothing.
    """
    table = PEERS.get(career.difficulty.key)
    if not table:
        return []
    head = [f"{HEADING} - against {PEER_COUNT} simulated peers on "
            f"{career.difficulty.name}"]
    if career.tour_provisional():
        return head + [
            "  Too few closes this tour to place it against them."]
    kpis = career.tour_kpis()
    accuracy = accuracy_of(career.tour_counts())
    rows = list(head)
    if kpis.mttr is not None:
        beats = place_lower(kpis.mttr, table['mttr'])
        assert beats is not None
        rows.append(f"  Repair time    {hours_minutes(round(kpis.mttr)):>6}"
                    f" average   quicker than {_of_ten(beats)}")
    if accuracy is not None:
        beats = place_higher(accuracy, table['accuracy'])
        assert beats is not None
        rows.append(f"  First pass     {accuracy:>5.0f}% matched   "
                    f"right more often than {_of_ten(beats)}")
    rows.append("  The peers are the simulation's own. Not scored.")
    return rows
