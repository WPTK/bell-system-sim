"""
Bell System call-progress tones and interoffice signaling.

A simulation built around crossbar, ESS, TSPS and toll operations contained no
signaling vocabulary at all: no multifrequency pulsing, no single-frequency
supervision, and none of the call-progress tones a craftsperson listened for
on a test set all day. This module supplies that vocabulary as data.

Frequencies and cadences follow the Precise Tone Plan, which specified exact
frequencies and amplitudes for call-progress tones. Telecommunications
Transmission Engineering (1977) confirms the plan and its scope but gives no
adoption date, and no other source consulted supplies one, so none is claimed
here. Through this period precise tones were the electronic-switching
standard while step-by-step and older crossbar offices still produced
non-precise tones from ringing-generator harmonics - a simulation may
legitimately show both.

Tone frequencies, cadences and levels below are the widely reproduced
standard values; they are NOT stated in the transmission volumes bundled with
this repository. The primary Bell source for them is Notes on the Network
(1980), which was not available. Treat them as well-attested but
secondary.

Cadence is expressed as (on, off) seconds. Interruption rates are given in
interruptions per minute, the unit Bell System practices used.
"""

from typing import Dict, List, NamedTuple, Optional, Tuple


class ProgressTone(NamedTuple):
    """A call-progress tone as heard by a subscriber or a test set."""

    name: str
    frequencies: Tuple[int, ...]
    cadence: Optional[Tuple[float, float]]
    interruptions_per_minute: Optional[int]
    level_dbm: float
    meaning: str

    def describe(self) -> str:
        """Return a one-line engineering description of the tone."""
        pair = ' + '.join(f'{hz} Hz' for hz in self.frequencies)
        if self.cadence is None:
            timing = 'continuous'
        else:
            on, off = self.cadence
            timing = f'{on:g}s on / {off:g}s off'
            if self.interruptions_per_minute:
                timing += f' ({self.interruptions_per_minute} IPM)'
        return f'{pair}, {timing}, {self.level_dbm:g} dBm'


# The Precise Tone Plan tones. A craftsperson identified a call's fate by ear
# from these long before any display told them.
PROGRESS_TONES: Dict[str, ProgressTone] = {
    'dial': ProgressTone(
        name='Dial tone',
        frequencies=(350, 440),
        cadence=None,
        interruptions_per_minute=None,
        level_dbm=-13.0,
        meaning='Office ready to receive digits. Objective: returned within '
                '3 seconds on 98 percent of attempts.',
    ),
    'busy': ProgressTone(
        name='Line busy',
        frequencies=(480, 620),
        cadence=(0.5, 0.5),
        interruptions_per_minute=60,
        level_dbm=-24.0,
        meaning='Called line is off-hook. Sixty interruptions per minute.',
    ),
    'reorder': ProgressTone(
        name='Reorder (all trunks busy)',
        frequencies=(480, 620),
        cadence=(0.25, 0.25),
        interruptions_per_minute=120,
        level_dbm=-24.0,
        meaning='No path available through the network, or a dialing '
                'irregularity. Twice the busy rate; known as fast busy.',
    ),
    'ringback': ProgressTone(
        name='Audible ringing',
        frequencies=(440, 480),
        cadence=(2.0, 4.0),
        interruptions_per_minute=None,
        level_dbm=-19.0,
        meaning='Ringing current is being applied to the called line. Not '
                'synchronised with the actual ringing.',
    ),
    'congestion': ProgressTone(
        name='Congestion (equipment irregularity)',
        frequencies=(480, 620),
        cadence=(0.2, 0.3),
        interruptions_per_minute=120,
        level_dbm=-24.0,
        meaning='Network management control in effect, or trunk group '
                'blocked beyond reorder threshold.',
    ),
    'howler': ProgressTone(
        name='Receiver off-hook (howler)',
        frequencies=(1400, 2060, 2450, 2600),
        cadence=(0.1, 0.1),
        interruptions_per_minute=None,
        level_dbm=0.0,
        meaning='Permanent signal: receiver left off-hook. Applied at high '
                'level after a timeout to alert the subscriber.',
    ),
    'highandwet': ProgressTone(
        name='Vacant code / intercept',
        frequencies=(200, 400),
        cadence=(0.25, 0.25),
        interruptions_per_minute=120,
        level_dbm=-24.0,
        meaning='Unassigned code. Normally routed to an intercept operator '
                'or announcement rather than tone.',
    ),
}


class MFDigit(NamedTuple):
    """One multifrequency signal: a digit or a control character."""

    symbol: str
    low: int
    high: int
    purpose: str


# Multifrequency interoffice pulsing. Six frequencies, two sounded at a time,
# used between offices to pass called-number digits - quite distinct from the
# Touch-Tone frequencies a subscriber's set produced.
MF_FREQUENCIES: Tuple[int, ...] = (700, 900, 1100, 1300, 1500, 1700)

# The six frequencies and the existence of KP and ST are verified in
# Engineering and Operations in the Bell System; the individual pair
# assignments below are the standard MF-R1 table but are not stated in any
# document bundled here. Note that 1300+1700 is ST2P domestically, while
# CCITT No. 5 calls the same pair KP2 on international trunks.
MF_SIGNALS: Dict[str, MFDigit] = {
    '1': MFDigit('1', 700, 900, 'digit'),
    '2': MFDigit('2', 700, 1100, 'digit'),
    '3': MFDigit('3', 900, 1100, 'digit'),
    '4': MFDigit('4', 700, 1300, 'digit'),
    '5': MFDigit('5', 900, 1300, 'digit'),
    '6': MFDigit('6', 1100, 1300, 'digit'),
    '7': MFDigit('7', 700, 1500, 'digit'),
    '8': MFDigit('8', 900, 1500, 'digit'),
    '9': MFDigit('9', 1100, 1500, 'digit'),
    '0': MFDigit('0', 1300, 1500, 'digit'),
    'KP': MFDigit('KP', 1100, 1700, 'control: key pulse, begins the digit train'),
    'ST': MFDigit('ST', 1500, 1700, 'control: start, ends the digit train'),
    'STP': MFDigit('STP', 900, 1700, 'control: start prime, operator number identification'),
    'ST2P': MFDigit('ST2P', 1300, 1700, 'control: start double prime'),
    'ST3P': MFDigit('ST3P', 700, 1700, 'control: start triple prime'),
}

# Nominal MF timing: each digit is sounded for about 60 ms with a 60 ms
# interdigit interval; KP is held longer so the receiver can lock to it.
MF_DIGIT_MS = 60
MF_INTERDIGIT_MS = 60
MF_KP_MS = 100

# Single-frequency supervision on analogue toll trunks. 2600 Hz present means
# the trunk is idle; its removal marks seizure, and its return marks release.
SF_FREQUENCY_HZ = 2600
# Verified in Telecommunications Transmission Engineering Vol 1: the idle
# supervisory tone sits at -20 dBm0, and is raised 12 dB to -8 dBm0 when the
# same 2600 Hz is used to pulse address information, which is permissible
# because those pulses are short.
SF_IDLE_LEVEL_DBM = -20.0
SF_ADDRESS_LEVEL_DBM = -8.0

# Touch-Tone, the subscriber-facing signaling. Two tones, one from each group,
# chosen so that the human voice is unlikely to simulate a valid pair - a
# protection MF deliberately does not have, since the talking path is muted
# while an office outpulses. Levels are repo-verified: the low group is
# transmitted at nominally -6 dBm and the high group at -4 dBm, the 2 dB
# difference being the customary "twist".
DTMF_ROW_HZ: Tuple[int, ...] = (697, 770, 852, 941)
# The fourth column (1633 Hz, keys A-D) was not part of the twelve-button set
# a subscriber had; sixteen-button sets were supplied for government private
# line service. A civilian simulation of this period should default to twelve.
DTMF_COLUMN_HZ: Tuple[int, ...] = (1209, 1336, 1477, 1633)
DTMF_LOW_GROUP_LEVEL_DBM = -6.0
DTMF_HIGH_GROUP_LEVEL_DBM = -4.0

DTMF_KEYS: Dict[str, Tuple[int, int]] = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633),
}

# Trunk supervision arrangements a craftsperson would select on a test set.
SUPERVISION_TYPES: Dict[str, str] = {
    'LOOP': 'Loop start. Seizure by closing the loop; used on subscriber '
            'lines and small PBX trunks.',
    'GROUND': 'Ground start. Tip grounded to seize; avoids the glare that '
              'loop start suffers on two-way PBX trunks.',
    'EM1': 'E&M Type I. Single-ended E lead to ground, M lead to battery. '
           'The common arrangement on interoffice trunks.',
    'EM2': 'E&M Type II. Four-wire signaling leads with SB and SG; fully '
           'isolated between the two offices.',
    'IMMEDIATE': 'Immediate start. The originating office pulses as soon as '
                 'it seizes, after a fixed guard interval.',
    'WINK': 'Wink start. The terminating office returns a brief off-hook '
            'wink to say its register is attached and ready.',
    'DELAY': 'Delay dial. The terminating office holds off-hook until ready, '
             'then goes on-hook to invite pulsing.',
}


def mf_sequence(digits: str, prefix_kp: bool = True,
                suffix_st: bool = True) -> List[MFDigit]:
    """
    Build the multifrequency signal train an office would outpulse.

    A real MF train is bracketed: KP to open the register, the digits, then
    ST to release it.

    Args:
        digits: The digits to outpulse
        prefix_kp: Whether to lead with KP, as an office always would
        suffix_st: Whether to close with ST

    Returns:
        The signals in the order they are sounded

    Raises:
        ValueError: if a character is not an MF digit
    """
    train: List[MFDigit] = []
    if prefix_kp:
        train.append(MF_SIGNALS['KP'])
    for character in digits:
        if character not in MF_SIGNALS or MF_SIGNALS[character].purpose != 'digit':
            raise ValueError(f'{character!r} is not an MF digit')
        train.append(MF_SIGNALS[character])
    if suffix_st:
        train.append(MF_SIGNALS['ST'])
    return train


def mf_train_duration_ms(train: List[MFDigit]) -> int:
    """Return roughly how long a signal train takes to outpulse."""
    total = 0
    for signal in train:
        total += MF_KP_MS if signal.symbol == 'KP' else MF_DIGIT_MS
        total += MF_INTERDIGIT_MS
    return total
