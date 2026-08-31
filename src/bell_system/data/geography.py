"""
The geographic data the simulation places its network on.

Central office codes, the places they serve and their coordinates, packaged
with the code rather than read from the working directory. The distinction
matters more than it sounds: this data used to be loaded by a path relative
to wherever the program happened to be started from, so an installed copy run
from a home directory silently fell back to six offices instead of several
thousand, and every geographic feature quietly degraded with it.

Coverage is limited to numbering plan areas that could have existed in the
period depicted. Engineering and Operations in the Bell System (2nd edition,
1984) describes "the basic set of 152 area codes possible using the N0/1X
format", so a middle digit of 0 or 1 is a structural property of every area
code in service during 1978-1983. The filter is applied when the dataset is
built; ``tools/build_nanpa.py`` documents it and the residual it cannot
remove.
"""

import csv
import gzip
import io
from typing import Dict, List, Optional

try:  # pragma: no cover - importlib.resources.files is 3.9+
    from importlib.resources import files as _resource_files
except ImportError:  # pragma: no cover
    _resource_files = None  # type: ignore[assignment]

DATASET = 'nanpa.csv.gz'

# Places for the simulation to fall back on if the packaged dataset cannot be
# read at all. Deliberately tiny and deliberately announced: this is the
# degraded mode, and callers are told when they are in it.
FALLBACK: Dict[str, Dict[str, List[dict]]] = {
    '212': {'555': [{'city': 'New York', 'state': 'New York',
                     'latitude': '40.7128', 'longitude': '-74.0060'}]},
    '312': {'555': [{'city': 'Chicago', 'state': 'Illinois',
                     'latitude': '41.8781', 'longitude': '-87.6298'}]},
    '415': {'555': [{'city': 'San Francisco', 'state': 'California',
                     'latitude': '37.7749', 'longitude': '-122.4194'}]},
}


class GeographyUnavailable(RuntimeError):
    """Raised when the packaged dataset is missing or unreadable."""


def _open_dataset() -> io.TextIOWrapper:
    """
    Return the packaged dataset as a text stream.

    Raises:
        GeographyUnavailable: if the data does not ship with this install
    """
    if _resource_files is None:  # pragma: no cover - very old Python
        raise GeographyUnavailable(
            'importlib.resources.files is unavailable on this Python.')
    try:
        resource = _resource_files(__package__).joinpath(DATASET)
        return io.TextIOWrapper(gzip.open(resource.open('rb')), encoding='utf-8')
    except (FileNotFoundError, OSError, ModuleNotFoundError) as exc:
        raise GeographyUnavailable(
            f'{DATASET} does not ship with this installation. Rebuild it with '
            f'tools/build_nanpa.py, or reinstall the package.') from exc


def load(limit_npas: Optional[int] = None) -> Dict[str, Dict[str, List[dict]]]:
    """
    Read the packaged dataset into the shape the simulation uses.

    Args:
        limit_npas: Keep only this many numbering plan areas. For tests that
            want a small network quickly; None loads everything.

    Returns:
        Numbering plan area to central office code to a list of places

    Raises:
        GeographyUnavailable: if the packaged data cannot be read
    """
    data: Dict[str, Dict[str, List[dict]]] = {}
    with _open_dataset() as handle:
        for row in csv.DictReader(handle):
            npa = row['npa']
            if npa not in data:
                if limit_npas is not None and len(data) >= limit_npas:
                    continue
                data[npa] = {}
            data[npa].setdefault(row['nxx'], []).append({
                'city': row['city'],
                'state': row['state'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
            })
    if not data:
        raise GeographyUnavailable(f'{DATASET} is present but empty.')
    return data


def office_count(data: Dict[str, Dict[str, List[dict]]]) -> int:
    """Return how many central office codes a loaded dataset carries."""
    return sum(len(exchanges) for exchanges in data.values())
