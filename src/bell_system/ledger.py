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

from .data import peers
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


def place_lower(value: Optional[float], cutoffs: Any) -> Optional[int]:
    """How many peers a lower-is-better figure beats. A tie beats nobody."""
    if value is None:
        return None
    return sum(1 for peer in cutoffs if value < peer)


def place_higher(value: Optional[float], cutoffs: Any) -> Optional[int]:
    """How many peers a higher-is-better figure matches or beats."""
    if value is None:
        return None
    return sum(1 for peer in cutoffs if value >= peer)


def _of_ten(beats: int) -> str:
    """'6 of 10', which reads the same for any count."""
    return f"{beats} of {PEER_COUNT}"


def lines(career: Any) -> List[str]:
    """
    The ledger for a spent tour, as printed lines.

    The peers are full tours, so this is asked for at sign-off and not
    part way through one.

    Args:
        career: The career, which holds the tour's counts and difficulty

    Returns:
        Nothing until the peers are generated, or where there are none for
        this difficulty. One line saying so where an assist is in force,
        since the peers were played without any. Otherwise a heading and,
        with too few closes to rest on, a line saying so and placing nothing.
    """
    # Held back until the peers have been played against the balance that
    # ships. A placing against placeholder numbers would be a claim about
    # the office that nothing backs.
    if not peers.GENERATED:
        return []
    table = peers.PEERS.get(career.difficulty.key)
    if not table:
        return []
    if career.assisted:
        return [f"{HEADING} - not placed: assists in force"]
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
        rows.append(f"  Repair time              {hours_minutes(round(kpis.mttr)):>5}"
                    f"   quicker than {_of_ten(beats)}")
    if accuracy is not None:
        beats = place_higher(accuracy, table['accuracy'])
        assert beats is not None
        rows.append(f"  Closes matched the line  {accuracy:>4.0f}%"
                    f"   as often as or more often than {_of_ten(beats)}")
    rows.append("  The peers are the simulation's own. Not scored.")
    return rows
