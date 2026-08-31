"""
Western Electric switching systems of the Bell System.

The simulation previously chose a switch type and an installation year
independently from overlapping ranges, which routinely produced impossible
machines: a No. 5 Crossbar cut over in 1901, or a 5ESS seventeen years before
the first one entered service. It also placed a No. 3 ESS - the smallest ESS
Western Electric built, for rural community dial offices - in Boston carrying
seven times the traffic the machine could physically handle.

This table records what each machine actually was: when it first carried
traffic, the market it served, and the size class it was engineered for. The
office generator draws from it so that a generated office is always a machine
that could have existed, in a place that would have had one.

Capacities are lines for local (Class 5) switches and trunks for toll
switches, given as the engineered range rather than a single figure.
"""

from typing import Dict, List, NamedTuple, Optional


class SwitchingSystem(NamedTuple):
    """One switching system as Western Electric built and Bell deployed it."""

    name: str
    first_service: int
    technology: str
    market: str
    min_lines: int
    max_lines: int
    is_toll: bool
    notes: str

    def busy_hour_capacity(self) -> int:
        """
        Return an approximate busy-hour call ceiling for the machine.

        Local offices were engineered at roughly one busy-hour call per line;
        toll machines are rated on trunk terminations, which carry far more
        calls each.
        """
        return self.max_lines * (6 if self.is_toll else 1)


# Ordered oldest first. Years are first revenue service in the Bell System.
SWITCHING_SYSTEMS: Dict[str, SwitchingSystem] = {
    'SXS': SwitchingSystem(
        name='Step-by-Step (Strowger)',
        first_service=1919,
        technology='Electromechanical, direct progressive control',
        market='Rural and small urban end offices',
        min_lines=100, max_lines=10000, is_toll=False,
        notes='Direct control: the dial pulses drove the switch train itself. '
              'Still numerous in 1983 and steadily being replaced.',
    ),
    'PANEL': SwitchingSystem(
        name='Panel',
        first_service=1921,
        technology='Electromechanical, common control, motor driven',
        market='Large metropolitan end offices',
        min_lines=5000, max_lines=40000, is_toll=False,
        notes='Confined to the largest cities. Being retired through the '
              'period; the last panel office closed in 1983.',
    ),
    'XB1': SwitchingSystem(
        name='No. 1 Crossbar',
        first_service=1938,
        technology='Electromechanical, common control, crossbar switch',
        market='Metropolitan end offices',
        min_lines=5000, max_lines=35000, is_toll=False,
        notes='First Bell crossbar. Introduced the marker and the '
              'crossbar switch that defined the next three decades.',
    ),
    'XB4': SwitchingSystem(
        name='No. 4 Crossbar',
        first_service=1943,
        technology='Electromechanical, common control, crossbar switch',
        market='Toll switching',
        min_lines=1000, max_lines=12000, is_toll=True,
        notes='The first crossbar toll machine; the 4A that followed added '
              'card-translator routing.',
    ),
    'XB5': SwitchingSystem(
        name='No. 5 Crossbar',
        first_service=1948,
        technology='Electromechanical, common control, crossbar switch',
        market='Suburban and general-purpose end offices',
        min_lines=1000, max_lines=30000, is_toll=False,
        notes='The workhorse local switch of the Bell System. More lines '
              'served on No. 5 Crossbar than on any other single machine.',
    ),
    'XB4A': SwitchingSystem(
        name='No. 4A Crossbar',
        first_service=1953,
        technology='Electromechanical, common control, card translator',
        market='Toll and tandem switching',
        min_lines=2000, max_lines=18000, is_toll=True,
        notes='Card-translator routing made nationwide operator and later '
              'customer direct distance dialing practical.',
    ),
    '1ESS': SwitchingSystem(
        name='No. 1 ESS',
        first_service=1965,
        technology='Stored program control, reed relay network',
        market='Urban and large suburban end offices',
        min_lines=10000, max_lines=65000, is_toll=False,
        notes='First Bell stored-program switch, cut over at Succasunna, '
              'New Jersey in May 1965. Brought custom calling services.',
    ),
    '2ESS': SwitchingSystem(
        name='No. 2 ESS',
        first_service=1970,
        technology='Stored program control, reed relay network',
        market='Suburban end offices',
        min_lines=1000, max_lines=10000, is_toll=False,
        notes='Scaled the 1ESS architecture down for communities too small '
              'to justify a No. 1.',
    ),
    '4ESS': SwitchingSystem(
        name='No. 4 ESS',
        first_service=1976,
        technology='Stored program control, digital time-division network',
        market='Toll and tandem switching',
        min_lines=10000, max_lines=53000, is_toll=True,
        notes='First digital toll switch, cut over in Chicago in January '
              '1976. Rated on trunk terminations, not lines.',
    ),
    '1AESS': SwitchingSystem(
        name='No. 1A ESS',
        first_service=1976,
        technology='Stored program control, 1A processor, reed relay network',
        market='Large urban end offices',
        min_lines=20000, max_lines=128000, is_toll=False,
        notes='The 1A processor roughly quadrupled No. 1 ESS call capacity '
              'and allowed far larger offices.',
    ),
    '3ESS': SwitchingSystem(
        name='No. 3 ESS',
        first_service=1976,
        technology='Stored program control, remreed network',
        market='Rural community dial offices',
        min_lines=500, max_lines=4500, is_toll=False,
        notes='The smallest ESS Western Electric built. Engineered for '
              'rural exchanges; it never served a city.',
    ),
    '2BESS': SwitchingSystem(
        name='No. 2B ESS',
        first_service=1976,
        technology='Stored program control, 3A processor, reed relay network',
        market='Suburban end offices',
        min_lines=1000, max_lines=12000, is_toll=False,
        notes='No. 2 ESS re-engineered around the 3A processor.',
    ),
    '5ESS': SwitchingSystem(
        name='No. 5 ESS',
        first_service=1982,
        technology='Stored program control, digital time-division network',
        market='Local end offices, all sizes',
        min_lines=1000, max_lines=100000, is_toll=False,
        notes='First cut over at Seneca, Illinois in March 1982. Only a '
              'handful were in service before 1984.',
    ),
}

# The machines a metropolitan wire center could plausibly carry. A rural
# community dial office switch in a big city is the error this prevents.
METROPOLITAN_SWITCHES: List[str] = [
    'PANEL', 'XB1', 'XB5', '1ESS', '1AESS', '5ESS',
]

# What a small town or rural exchange would actually have had.
RURAL_SWITCHES: List[str] = [
    'SXS', 'XB5', '2ESS', '2BESS', '3ESS',
]

# Toll and tandem machines, which serve trunks rather than subscriber lines.
TOLL_SWITCHES: List[str] = ['XB4', 'XB4A', '4ESS']


def available_in(year: int, candidates: Optional[List[str]] = None) -> List[str]:
    """
    Return the switch codes that had entered service by a given year.

    Args:
        year: The year an office is being placed in service
        candidates: Restrict to these codes; defaults to every system

    Returns:
        Codes whose first service year is at or before the given year
    """
    pool = candidates if candidates is not None else list(SWITCHING_SYSTEMS)
    return [
        code for code in pool
        if code in SWITCHING_SYSTEMS and SWITCHING_SYSTEMS[code].first_service <= year
    ]


def describe(code: str) -> str:
    """Return a one-line description of a switching system."""
    system = SWITCHING_SYSTEMS.get(code)
    if system is None:
        return f'{code}: unknown switching system'
    return (f'{system.name} ({system.first_service}), {system.technology}; '
            f'{system.min_lines:,}-{system.max_lines:,} '
            f'{"trunks" if system.is_toll else "lines"}')
