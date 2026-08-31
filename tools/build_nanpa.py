#!/usr/bin/env python3
"""
Distil the NANPA geographic dump into the dataset the package ships.

The source file is a 46 MB modern NANPA extract covering North America. The
simulation needs six of its fourteen columns, only United States rows, and
only numbering plan areas that could have existed in the period depicted.

The period filter is not a guess. Engineering and Operations in the Bell
System (2nd edition, 1984) describes "the basic set of 152 area codes
possible using the N0/1X format", and notes that careful code management had
postponed their exhaustion "to about the turn of the century". A middle digit
of 0 or 1 is therefore a hard structural property of every area code in
service during 1978-1983, and any code with a middle digit of 2 through 9 was
created in 1995 or later.

The format rule alone is not enough. Codes created between 1984 and 1994
shared the N0/1X format, so eighteen of them survive it - 718, which split
from 212 in September 1984, among them. Those are excluded by name in
POST_PERIOD_NPAS below.

Provenance, stated plainly: the format rule is repo-verified from Engineering
and Operations. The split dates in POST_PERIOD_NPAS are not in any document
available to this project; they come from the published history of the
numbering plan and are marked here as externally sourced. Each entry carries
its year and its parent code so a wrong one can be found and corrected rather
than merely suspected.

Run from the repository root, with attached_assets present:

    python tools/build_nanpa.py
"""

import argparse
import csv
import gzip
import os
import re
import sys

# Area code format in service through the period: N, then 0 or 1, then any
# digit. Attested in Engineering and Operations, 2nd edition, page 118.
PERIOD_NPA = re.compile(r'^[2-9][01][0-9]$')

# Numbering plan areas created after the simulated period but sharing the
# N0/1X format, so the structural filter cannot catch them. Externally
# sourced, not repo-verified: value is the year and the code it split from.
POST_PERIOD_NPAS = {
    '210': '1992, from 512 (San Antonio)',
    '310': '1991, from 213 (west Los Angeles)',
    '407': '1988, from 305 (Orlando)',
    '410': '1991, from 301 (Baltimore)',
    '508': '1988, from 617 (Massachusetts)',
    '510': '1991, from 415 (Oakland)',
    '610': '1994, from 215 (Pennsylvania)',
    '706': '1992, from 404 (Georgia)',
    '708': '1989, from 312 (Chicago suburbs)',
    '718': '1984, from 212 (Brooklyn, Queens, Staten Island)',
    '719': '1988, from 303 (southern Colorado)',
    '810': '1993, from 313 (Michigan)',
    '818': '1984, from 213 (San Fernando Valley)',
    '903': '1990, from 214 (north east Texas)',
    '908': '1991, from 201 (New Jersey)',
    '909': '1992, from 714 (San Bernardino)',
    '910': '1993, from 919 (North Carolina)',
    '917': '1992, New York City overlay',
}

# Central office codes to keep per numbering plan area. The simulation wants
# breadth of geography rather than depth in any one area.
NXX_PER_NPA = 40

SOURCE = os.path.join('attached_assets', 'full_dataset_csv.csv')
TARGET = os.path.join('src', 'bell_system', 'data', 'nanpa.csv.gz')

FIELDS = ('npa', 'nxx', 'city', 'state', 'latitude', 'longitude')


def distil(source: str, target: str) -> dict:
    """
    Read the NANPA dump and write the packaged dataset.

    Returns:
        Counts describing what was kept, for the caller to report
    """
    kept: dict = {}
    read = 0

    with open(source, newline='') as handle:
        for row in csv.DictReader(handle):
            read += 1
            if row['country'] != 'United States':
                continue
            npa = row['npa']
            if not PERIOD_NPA.match(npa) or npa in POST_PERIOD_NPAS:
                continue
            area = kept.setdefault(npa, {})
            if len(area) >= NXX_PER_NPA or row['nxx'] in area:
                continue
            area[row['nxx']] = (
                row['city'], row['state'],
                row.get('latitude', '0'), row.get('longitude', '0'),
            )

    os.makedirs(os.path.dirname(target), exist_ok=True)
    # mtime=0 so rebuilding identical data produces an identical file.
    with gzip.GzipFile(target, 'wb', mtime=0) as raw:
        writer = csv.writer(_TextWrapper(raw))
        writer.writerow(FIELDS)
        for npa in sorted(kept):
            for nxx in sorted(kept[npa]):
                city, state, lat, lon = kept[npa][nxx]
                writer.writerow([npa, nxx, city, state, lat, lon])

    return {
        'rows_read': read,
        'npas': len(kept),
        'offices': sum(len(area) for area in kept.values()),
        'bytes': os.path.getsize(target),
    }


class _TextWrapper:
    """Adapt a binary file object for csv.writer, which wants text."""

    def __init__(self, binary):
        self.binary = binary

    def write(self, text: str) -> int:
        """Encode and forward a chunk of CSV text."""
        return self.binary.write(text.encode('utf-8'))


def main() -> int:
    """Build the dataset and report what it contains."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=SOURCE)
    parser.add_argument('--target', default=TARGET)
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"{args.source} not found. This script needs the NANPA dump "
              f"from attached_assets; see SOURCES.md.", file=sys.stderr)
        return 1

    counts = distil(args.source, args.target)
    print(f"read     {counts['rows_read']:>9,} rows")
    print(f"kept     {counts['npas']:>9,} numbering plan areas")
    print(f"         {counts['offices']:>9,} central office codes")
    print(f"wrote    {counts['bytes']:>9,} bytes to {args.target}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
