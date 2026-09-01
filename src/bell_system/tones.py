"""
Rendering the signalling to audio.

Every frequency, level and cadence this module needs has been sitting in
data/signaling.py since it was written, described in words and never heard.
A craftsperson identified a call's fate by ear long before any display told
them, and the whole of the Precise Tone Plan exists because a person had to
be able to tell a busy from a reorder down a handset. Reading "480 + 620 Hz,
0.5s on / 0.5s off (60 IPM)" is not that.

This turns those tables into a wave file. Nothing here invents a frequency:
if it is not in data/signaling.py it is not synthesised, and the levels and
cadences are read from the same records the screens print.

HOW A LEVEL BECOMES AN AMPLITUDE

The tables give levels in dBm - power into 600 ohms, which is what a
transmission measuring set reads. A wave file has no impedance and no
absolute level, so the conversion here is a working one: 0 dBm maps to a
comfortable fraction of full scale and everything else sits below it by the
same number of decibels. That keeps the RELATIVE levels honest - a dial
tone really is louder than an idle SF - without pretending a laptop
speaker is terminated in 600 ohms.

That is the only liberty taken and it is taken deliberately, because the
alternative is either clipping or silence.
"""

import math
import struct
import wave
from typing import List, Optional, Sequence, Tuple

from .data.signaling import (
    DTMF_HIGH_GROUP_LEVEL_DBM,
    DTMF_KEYS,
    DTMF_LOW_GROUP_LEVEL_DBM,
    MF_DIGIT_MS,
    MF_INTERDIGIT_MS,
    MF_KP_MS,
    MF_SIGNALS,
    PROGRESS_TONES,
    SF_ADDRESS_LEVEL_DBM,
    SF_FREQUENCY_HZ,
    SF_IDLE_LEVEL_DBM,
)

# Eight thousand samples a second is the network's own rate: a voice channel
# was sampled at 8 kHz for T-carrier, which is why the channel is band
# limited to about 3.4 kHz and why every tone in these tables fits under it.
SAMPLE_RATE = 8000

# Sixteen bit signed, one channel. A telephone circuit is monophonic by
# construction.
SAMPLE_WIDTH = 2
CHANNELS = 1

# What 0 dBm is rendered as, in fractions of full scale.
#
# Chosen so that the loudest thing in the tables exactly fills the scale
# without clipping: the howler is 0 dBm with four components, so a quarter
# each. Everything else then sits below it by exactly the number of
# decibels the table says, which means a busy tone really does render
# eleven dB quieter than dial tone - because it is.
#
# That makes the quiet ones quiet. write(normalise=True) scales a rendering
# up to full scale for listening, which is a change to the file and not to
# the table.
REFERENCE_AMPLITUDE = 0.25

# How long a continuous tone plays when nobody says otherwise.
DEFAULT_SECONDS = 3.0


def amplitude_for(level_dbm: float) -> float:
    """
    Turn a level in dBm into a sample amplitude.

    Relative levels are preserved exactly; the absolute reference is the
    working one described in the module docstring, because a wave file is
    not terminated in 600 ohms.
    """
    return REFERENCE_AMPLITUDE * (10.0 ** (level_dbm / 20.0))


def _samples(frequencies: Sequence[int], seconds: float,
             level_dbm: float) -> List[float]:
    """
    Sum some sine waves for a while.

    Each frequency is generated at the given level and they are added, which
    is what happens on a real pair: two tones on one circuit are one signal
    with two components, not two signals.
    """
    amplitude = amplitude_for(level_dbm)
    count = int(SAMPLE_RATE * seconds)
    out = []
    for index in range(count):
        moment = index / SAMPLE_RATE
        value = sum(math.sin(2.0 * math.pi * hz * moment)
                    for hz in frequencies)
        out.append(amplitude * value)
    return out


def _silence(seconds: float) -> List[float]:
    """Nothing, for a while. Half of every cadence is this."""
    return [0.0] * int(SAMPLE_RATE * seconds)


def _limit(samples: Sequence[float]) -> bytes:
    """
    Pack samples to sixteen bit, clipping rather than wrapping.

    Two tones at the same level sum to twice the amplitude, so a summed
    signal can exceed full scale. Clipping sounds like a loud tone; wrapping
    sounds like a fault in the equipment, and there is enough of that in
    this simulation already.
    """
    packed = bytearray()
    for value in samples:
        clipped = max(-1.0, min(1.0, value))
        packed += struct.pack('<h', int(clipped * 32767))
    return bytes(packed)


def write(path: str, samples: Sequence[float],
          normalise: bool = False) -> str:
    """
    Write samples to a wave file and return the path.

    Args:
        path: Where to write
        samples: What to write
        normalise: Scale up so the loudest point just fills the scale. The
            levels in the tables are relative to each other and honest,
            which makes a busy tone genuinely quiet; this makes it audible
            without changing what the table says.
    """
    if normalise:
        peak = max((abs(value) for value in samples), default=0.0)
        if peak > 0:
            samples = [value / peak * 0.9 for value in samples]
    with wave.open(path, 'wb') as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(_limit(samples))
    return path


# -- what can be rendered ------------------------------------------------


def progress_tone(name: str, seconds: float = DEFAULT_SECONDS) -> List[float]:
    """
    Render one call-progress tone, cadence and all.

    The cadence is the identifying feature. Busy and reorder are the same
    two frequencies and differ only in how fast they are interrupted -
    sixty a minute against a hundred and twenty - which is exactly the
    distinction a craftsperson made by ear and cannot be read off a table.

    Args:
        name: A key of PROGRESS_TONES
        seconds: How long to play for

    Raises:
        KeyError: if no such tone is in the table
    """
    tone = PROGRESS_TONES[name]
    if tone.cadence is None:
        return _samples(tone.frequencies, seconds, tone.level_dbm)

    on, off = tone.cadence
    out: List[float] = []
    while len(out) < SAMPLE_RATE * seconds:
        out.extend(_samples(tone.frequencies, on, tone.level_dbm))
        out.extend(_silence(off))
    return out[:int(SAMPLE_RATE * seconds)]


def mf_digits(digits: str) -> List[float]:
    """
    Render a multifrequency pulse train.

    Two of six frequencies at a time, KP to start and ST to finish, which is
    how an operator's or a switch's address signalling went down an
    interoffice trunk. KP is held longer than a digit because the far end
    needs to recognise the start of a train before it starts counting.

    Args:
        digits: Symbols from MF_SIGNALS - digits, KP, ST

    Raises:
        KeyError: if a symbol is not an MF signal
    """
    out: List[float] = []
    for symbol in _split_symbols(digits):
        signal = MF_SIGNALS[symbol]
        length = (MF_KP_MS if signal.purpose != 'digit' else MF_DIGIT_MS)
        out.extend(_samples((signal.low, signal.high), length / 1000.0,
                            SF_ADDRESS_LEVEL_DBM))
        out.extend(_silence(MF_INTERDIGIT_MS / 1000.0))
    return out


def dtmf(keys: str) -> List[float]:
    """
    Render Touch-Tone.

    One row frequency and one column frequency, and the two groups are sent
    at different levels: the high group louder, because the network's own
    frequency response falls off across the voice band and the far end has
    to hear both.

    Args:
        keys: Characters from DTMF_KEYS

    Raises:
        KeyError: if a character is not on the keypad
    """
    out: List[float] = []
    for key in keys:
        if key in ' -':
            out.extend(_silence(0.06))
            continue
        low_hz, high_hz = DTMF_KEYS[key.upper()]
        # Two groups at two levels, summed as they are on the pair.
        low = _samples((low_hz,), 0.1, DTMF_LOW_GROUP_LEVEL_DBM)
        high = _samples((high_hz,), 0.1, DTMF_HIGH_GROUP_LEVEL_DBM)
        out.extend(a + b for a, b in zip(low, high))
        out.extend(_silence(0.06))
    return out


def sf_supervision(seizure: bool = True,
                   seconds: float = 2.0) -> List[float]:
    """
    Render single-frequency supervision.

    2600 Hz present on an idle trunk and absent when it is seized, which is
    the whole of the signalling and the whole of the vulnerability. This
    renders the idle tone, a seizure, and the tone coming back - which is
    what a trunk sounds like when a call starts and finishes.

    Args:
        seizure: Whether the trunk is seized part way through
        seconds: Total length
    """
    third = seconds / 3.0
    idle = _samples((SF_FREQUENCY_HZ,), third, SF_IDLE_LEVEL_DBM)
    if not seizure:
        return _samples((SF_FREQUENCY_HZ,), seconds, SF_IDLE_LEVEL_DBM)
    return idle + _silence(third) + list(idle)


def _split_symbols(digits: str) -> List[str]:
    """
    Split an MF string into symbols, keeping KP and ST whole.

    A pulse train is written KP-212-ST and the control characters are
    several letters each, so a plain character walk would look for a signal
    called K. The ST primes are longer still - STP, ST2P and ST3P are all
    real signals and all start with ST - so the match has to be greedy or
    ST3P becomes ST followed by nonsense.
    """
    out: List[str] = []
    index = 0
    text = digits.upper().replace('-', '').replace(' ', '')
    # Longest first, so ST3P is not read as ST.
    names = sorted(MF_SIGNALS, key=len, reverse=True)
    while index < len(text):
        for name in names:
            if text.startswith(name, index):
                out.append(name)
                index += len(name)
                break
        else:
            out.append(text[index])
            index += 1
    return out


def render(what: str, argument: Optional[str] = None,
           seconds: float = DEFAULT_SECONDS) -> List[float]:
    """
    Render anything this module knows how to make.

    Args:
        what: A progress tone name, or 'mf', 'dtmf' or 'sf'
        argument: The digits, for mf and dtmf
        seconds: Length, for the continuous kinds

    Raises:
        KeyError: if nothing of that name can be rendered
    """
    lowered = what.lower()
    if lowered in PROGRESS_TONES:
        return progress_tone(lowered, seconds)
    if lowered == 'mf':
        return mf_digits(argument or 'KP212ST')
    if lowered == 'dtmf':
        return dtmf(argument or '5551212')
    if lowered == 'sf':
        return sf_supervision(seconds=seconds)
    raise KeyError(what)


def catalogue() -> List[Tuple[str, str]]:
    """Everything that can be rendered, and what it is."""
    rows = [(name, tone.describe())
            for name, tone in PROGRESS_TONES.items()]
    rows.append(('mf', f"{'/'.join(str(f) for f in (700, 900))} and the rest "
                       f"of six, two at a time"))
    rows.append(('dtmf', 'one row and one column frequency, two levels'))
    rows.append(('sf', f'{SF_FREQUENCY_HZ} Hz present means idle'))
    return rows
