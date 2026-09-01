"""
The operating companies, and who each of them belongs to in January.

An office in this simulation is somewhere. Until now that meant a city, a
state and a CLLI code, and every office was interchangeable beyond the
label. This is what makes them different from each other: which of the
twenty-one Bell operating companies runs the office, and which of the seven
regional holding companies it passes to on 1 January 1984.

WHY THIS RATHER THAN EQUIPMENT MIX

The roadmap asked for per-operating-company character "drawn from
documented differences in equipment mix and practice". That turned out not
to be gettable: neither the bundled documents nor the sources reachable
from this project establish how one operating company's crossbar-to-ESS mix
differed from another's, and inventing one would have been the exact thing
this project refuses to do.

What IS documented, thoroughly, is the divestiture assignment - and it is
the better answer anyway. The simulated shift is 14 November 1983, and the
one thing everybody in every one of these buildings actually knew about
their own company that autumn was which way it was going in forty-eight
days. That is character, and it is on the record.

WHAT IS VERIFIED HERE

Engineering and Operations in the Bell System (2nd ed., 1984) states that
AT&T "was sole stockholder in twenty-one operating companies and a minority
stockholder in two: the Southern New England Telephone Company and
Cincinnati Bell, Inc.", that "Bell Telephone Company of Nevada is wholly
owned by the Pacific Telephone and Telegraph Company", and that "Four
Chesapeake and Potomac Telephone Companies offer service in Washington,
D.C.; Maryland; Virginia; and West Virginia." Its figure 1-9 gives three
of the seven regional groupings in full - Pacific Telesis, Ameritech and
Bell Atlantic - and names Mountain States Telephone and Telegraph Company
as Mountain Bell.

The remaining four groupings (NYNEX, BellSouth, Southwestern Bell, US West)
are externally sourced from the published divestiture record and marked
`verified=False` below, so that a wrong one can be found.
"""

from typing import Dict, NamedTuple, Optional, Tuple


class Company(NamedTuple):
    """One Bell operating company, and where it goes."""

    key: str
    name: str
    # Two-letter state codes this company served.
    states: Tuple[str, ...]
    # The regional holding company it passes to on 1 January 1984.
    rboc: str
    # True where Engineering and Operations states the assignment directly.
    verified: bool
    # What somebody in one of its buildings would say about it that autumn.
    note: str


# The seven regional holding companies, as the book's figure 1-9 names them.
RBOCS: Dict[str, str] = {
    'AMERITECH': 'American Information Technologies Corporation',
    'BELL ATLANTIC': 'Bell Atlantic Corporation',
    'BELLSOUTH': 'BellSouth Corporation',
    'NYNEX': 'NYNEX Corporation',
    'PACIFIC TELESIS': 'Pacific Telesis Group',
    'SOUTHWESTERN BELL': 'Southwestern Bell Corporation',
    'US WEST': 'U S WEST, Inc.',
}


COMPANIES: Dict[str, Company] = {
    'njb': Company(
        'njb', 'New Jersey Bell', ('NJ',), 'BELL ATLANTIC', True,
        'Bell Atlantic in January, and the long lines through here go to '
        'AT&T. Half the people in this building will be working for one of '
        'them and half for the other, and the wall runs through the frame.'),
    'nyt': Company(
        'nyt', 'New York Telephone', ('NY',), 'NYNEX', False,
        'NYNEX, which nobody can pronounce yet. Manhattan alone is more '
        'switching than most of the country.'),
    'net': Company(
        'net', 'New England Telephone', ('MA', 'ME', 'NH', 'RI', 'VT'),
        'NYNEX', False,
        'NYNEX with New York, which is a long way from Vermont in every '
        'sense a plant man would mean it.'),
    'bpa': Company(
        'bpa', 'Bell of Pennsylvania', ('PA',), 'BELL ATLANTIC', True,
        'Bell Atlantic. Philadelphia and Pittsburgh have never agreed '
        'about anything and now they are in the same company again.'),
    'dst': Company(
        'dst', 'Diamond State Telephone', ('DE',), 'BELL ATLANTIC', True,
        'Bell Atlantic. The smallest of the twenty-one and it knows it.'),
    'cp': Company(
        'cp', 'Chesapeake and Potomac Telephone', ('DC', 'MD', 'VA', 'WV'),
        'BELL ATLANTIC', True,
        'Four separate C&P companies, one for the District and one each for '
        'Maryland, Virginia and West Virginia, and all four go to Bell '
        'Atlantic together.'),
    'sb': Company(
        'sb', 'Southern Bell', ('FL', 'GA', 'NC', 'SC'), 'BELLSOUTH', False,
        'BellSouth. Growing faster than anywhere else in the system and '
        'the plant records have never quite caught up with it.'),
    'ssb': Company(
        'ssb', 'South Central Bell', ('AL', 'KY', 'LA', 'MS', 'TN'),
        'BELLSOUTH', False,
        'BellSouth with Southern Bell, back together after eight years '
        'apart, which somebody in Atlanta finds funny.'),
    'ib': Company(
        'ib', 'Illinois Bell', ('IL',), 'AMERITECH', True,
        'Ameritech. Chicago has the first 5ESS in the country an hour down '
        'the road at Seneca and everybody here has been to look at it.'),
    'inb': Company(
        'inb', 'Indiana Bell', ('IN',), 'AMERITECH', True,
        'Ameritech. Indianapolis runs a tighter plant record than anybody '
        'gives it credit for.'),
    'mib': Company(
        'mib', 'Michigan Bell', ('MI',), 'AMERITECH', True,
        'Ameritech. The route between Flint and Kalamazoo is in the '
        'transmission textbook, which people here mention.'),
    'ob': Company(
        'ob', 'Ohio Bell', ('OH',), 'AMERITECH', True,
        'Ameritech. Cleveland and Columbus and Cincinnati, except '
        'Cincinnati, which was never really ours.'),
    'wt': Company(
        'wt', 'Wisconsin Telephone', ('WI',), 'AMERITECH', True,
        'Ameritech, and the only one of the five whose name does not have '
        'Bell in it, which somebody is going to fix.'),
    'swb': Company(
        'swb', 'Southwestern Bell', ('AR', 'KS', 'MO', 'OK', 'TX'),
        'SOUTHWESTERN BELL', False,
        'Southwestern Bell Corporation, which is the only region keeping '
        'the name it had. Five states and most of them a long drive.'),
    'mb': Company(
        'mb', 'Mountain States Telephone and Telegraph',
        ('AZ', 'CO', 'ID', 'MT', 'NM', 'UT', 'WY'), 'US WEST', False,
        'US West. Mountain Bell covers seven states and about a tenth of '
        'the country by area, most of which has nobody in it.'),
    'nwb': Company(
        'nwb', 'Northwestern Bell', ('IA', 'MN', 'NE', 'ND', 'SD'),
        'US WEST', False,
        'US West. Everything between Minneapolis and the Rockies, and in '
        'February a fault is where the road ends.'),
    'pnb': Company(
        'pnb', 'Pacific Northwest Bell', ('OR', 'WA'), 'US WEST', False,
        'US West, which puts Seattle and Denver in one company. Rain does '
        'to cable here what nowhere else in the system sees.'),
    'pt': Company(
        'pt', 'Pacific Telephone and Telegraph', ('CA',),
        'PACIFIC TELESIS', True,
        'Pacific Telesis. The biggest operating company in the system and '
        'it will be the whole of its own region.'),
    'nb': Company(
        'nb', 'Bell Telephone Company of Nevada', ('NV',),
        'PACIFIC TELESIS', True,
        'Pacific Telesis. Wholly owned by Pacific Telephone already, so '
        'January changes the letterhead and not much else.'),
}

# The two AT&T was only a minority stockholder in, which is why an office in
# Connecticut or Cincinnati is not in the table above and does not divest.
NOT_WHOLLY_OWNED: Dict[str, str] = {
    'CT': 'Southern New England Telephone Company',
    'OH-CIN': 'Cincinnati Bell, Inc.',
}


def _by_state() -> Dict[str, Company]:
    """Index the companies by the states they serve."""
    index: Dict[str, Company] = {}
    for company in COMPANIES.values():
        for state in company.states:
            index.setdefault(state, company)
    return index


COMPANIES_BY_STATE: Dict[str, Company] = _by_state()


def for_state(state: str) -> Optional[Company]:
    """
    Return the operating company serving a state, or None.

    None is a real answer for Connecticut, where Southern New England
    Telephone was only minority-held and is not part of the divestiture.
    """
    return COMPANIES_BY_STATE.get(state.upper())
