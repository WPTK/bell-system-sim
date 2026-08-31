"""
L-carrier coaxial transmission systems.

The simulation's frequency-allocation table gave each L-system the wrong
spectrum and the wrong multiplex-level name, contradicting the very documents
bundled with this repository. The figures here are taken from
Telecommunications Transmission Engineering (1977) and Engineering and
Operations in the Bell System (1984), both in attached_assets, and the two
sources agree with each other on every value.

The distinction the old table lost is between the frequency-division
multiplex hierarchy - the bands in which channels are assembled - and the
line band actually transmitted down the coaxial tube. 564-3084 kHz, for
instance, is the basic mastergroup, not the L4 line spectrum.
"""

from typing import Dict, NamedTuple, Tuple


class MultiplexLevel(NamedTuple):
    """One level of the frequency-division multiplex hierarchy."""

    name: str
    channels: int
    low_khz: float
    high_khz: float

    def band(self) -> str:
        """Return the band as engineering text."""
        return f'{self.low_khz:,.0f} - {self.high_khz:,.0f} kHz'


# The assembly hierarchy. Channels are combined upward through these bands
# before being placed on a line.
MULTIPLEX_HIERARCHY: Tuple[MultiplexLevel, ...] = (
    MultiplexLevel('Basic group', 12, 60, 108),
    MultiplexLevel('Basic supergroup', 60, 312, 552),
    MultiplexLevel('Basic mastergroup (U600)', 600, 564, 3084),
    MultiplexLevel('Basic jumbogroup', 3600, 564, 17548),
)

# Pilot frequencies used for regulation and alarm at each level, in kHz.
MULTIPLEX_PILOTS_KHZ: Dict[str, float] = {
    'Basic group': 104.08,
    'Basic supergroup': 315.92,
    'Basic mastergroup (U600)': 2840.0,
    'Basic jumbogroup': 5888.0,
    'Multimastergroup': 13920.0,
}


class CarrierSystem(NamedTuple):
    """An L-carrier system as engineered and deployed."""

    name: str
    service_year: int
    channels: int
    line_low_khz: float
    line_high_khz: float
    repeater_spacing_miles: float
    tubes_per_cable: int
    working_channels_per_cable: int
    noise_objective_dbrnc0: int
    technology: str

    def line_band(self) -> str:
        """Return the transmitted line band as engineering text."""
        if self.line_high_khz >= 1000:
            return f'{self.line_low_khz:,.0f} kHz - {self.line_high_khz / 1000:,.3f} MHz'
        return f'{self.line_low_khz:,.0f} - {self.line_high_khz:,.0f} kHz'

    def bandwidth_mhz(self) -> float:
        """Return the occupied bandwidth in megahertz."""
        return (self.line_high_khz - self.line_low_khz) / 1000


# Repeater spacing halves with each generation: the wider the band, the closer
# the repeaters must be to hold a comparable signal-to-noise ratio, and halving
# lets an older route's repeater points be reused on conversion.
L_CARRIER_SYSTEMS: Dict[str, CarrierSystem] = {
    'L1': CarrierSystem(
        name='L1 coaxial carrier',
        service_year=1946, channels=600,
        line_low_khz=60, line_high_khz=2788,
        repeater_spacing_miles=8, tubes_per_cable=8,
        working_channels_per_cable=1800, noise_objective_dbrnc0=44,
        technology='Vacuum tube',
    ),
    'L3': CarrierSystem(
        name='L3 coaxial carrier',
        service_year=1953, channels=1860,
        line_low_khz=312, line_high_khz=8284,
        repeater_spacing_miles=4, tubes_per_cable=12,
        working_channels_per_cable=9300, noise_objective_dbrnc0=44,
        technology='Vacuum tube',
    ),
    'L4': CarrierSystem(
        name='L4 coaxial carrier',
        service_year=1967, channels=3600,
        line_low_khz=564, line_high_khz=17548,
        repeater_spacing_miles=2, tubes_per_cable=20,
        working_channels_per_cable=32400, noise_objective_dbrnc0=40,
        technology='Solid state',
    ),
    'L5': CarrierSystem(
        name='L5 coaxial carrier',
        service_year=1974, channels=10800,
        line_low_khz=3124, line_high_khz=60556,
        repeater_spacing_miles=1, tubes_per_cable=22,
        working_channels_per_cable=108000, noise_objective_dbrnc0=40,
        technology='Solid state',
    ),
    'L5E': CarrierSystem(
        name='L5E coaxial carrier',
        service_year=1978, channels=13200,
        line_low_khz=3252, line_high_khz=64844,
        repeater_spacing_miles=1, tubes_per_cable=22,
        working_channels_per_cable=132000, noise_objective_dbrnc0=40,
        technology='Solid state',
    ),
}

# The L3 line signal is assembled from three mastergroups plus one supergroup:
# 3 x 600 + 60 = 1860 channels.
L3_LINE_ASSEMBLY: Tuple[Tuple[str, float, float], ...] = (
    ('Basic supergroup', 312, 552),
    ('Mastergroup 1', 564, 3084),
    ('Mastergroup 2', 3164, 5684),
    ('Mastergroup 3', 5764, 8284),
)

# L5 repeater types. "One mile" is the basic repeater spacing; regulating and
# equalizing repeaters and power feed points sit at wider intervals.
L5_REPEATER_PLAN: Dict[str, str] = {
    'Basic': 'Every 1 mile nominal; restores line loss',
    'Regulating': 'At most every 7 miles; corrects temperature-driven loss',
    'Equalizing': 'Midpoint of a power feed span, at most every 37.5 miles',
    'Power feed': 'At most every 75 miles; power fed over the centre conductors',
}


def describe_system(code: str) -> str:
    """Return a one-line description of an L-carrier system."""
    system = L_CARRIER_SYSTEMS.get(code)
    if system is None:
        return f'{code}: unknown carrier system'
    return (f'{system.name} ({system.service_year}): {system.channels:,} channels, '
            f'{system.line_band()}, repeaters every '
            f'{system.repeater_spacing_miles:g} mi')
