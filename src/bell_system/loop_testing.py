"""
Loop measurement, test lines and the readings a craftsperson interprets.

Mechanised loop testing is listed in Engineering and Operations in the Bell
System's abbreviation table as MLT. The source conflict over what the letters
stand for is recorded in the manual page rather than papered over: that table
expands MLT as "mechanical loop testing", while the system was more widely
called Mechanized Loop Testing.

The physical constants used to turn a fault into a set of readings are taken
from the bundled documents:

  * Local exchange cable capacitance is 0.083 microfarads per mile
    (Telecommunications Transmission Engineering volume 2), which is what
    makes a capacitance measurement into a distance to an open.
  * Loops of 18 kilofeet or less were designed to 1300 ohms maximum and
    nonloaded; 18 to 24 kilofeet to 1500 ohms with H88 loading; anything
    longer went on digital loop carrier (Engineering and Operations).
  * A coin telephone needs 23 milliamperes of line current, which is what
    puts its range limit at the same 1300 ohms, about three miles. That
    sentence is also where the loop resistance per mile used below comes
    from: 1300 ohms over about three miles is roughly 430 ohms to the mile,
    and it is derived from the document rather than quoted from it.

Two different measurements are reported and must not be confused. Insulation
resistance is measured with the loop open and the office battery removed; it
is high on a healthy pair and low where a fault is bridging something. Loop
resistance is the resistance of the pair itself with the loop closed, and it
is the number the 1300-ohm design limit applies to. Reporting one as the
other is the mistake this module exists to avoid.

The readings themselves are derived from the resistance ranges declared for
each fault in :mod:`bell_system.data.trouble`. They are seeded from the line's
own number, so a line measures the same way every time it is tested - as a
real pair would, and so that re-testing is not a way to re-roll the answer.
"""

import random
from typing import Dict, List, NamedTuple, Optional, Tuple

from .data.testlines import LIMITS, TEST_LINES, TEST_TONE_DBM, TEST_TONE_HZ
from .data.trouble import FAULTS

# Local exchange cable mutual capacitance, microfarads per mile.
CABLE_UF_PER_MILE = 0.083

# Loop resistance per mile of cable, derived from the statement that 1300
# ohms is typically about three miles. Real figures vary with conductor
# gauge; this is one working number, not a gauge table.
LOOP_OHMS_PER_MILE = 433

# Loop design limits.
RESISTANCE_DESIGN_LIMIT_OHMS = 1300
LOADED_DESIGN_LIMIT_OHMS = 1500
NONLOADED_MAX_KFT = 18
LOADED_MAX_KFT = 24

# Line current a coin station needs to work, in milliamperes.
COIN_STATION_CURRENT_MA = 23

# Central office battery.
OFFICE_BATTERY_VOLTS = -48.0

# A station on hook looks like this to a test: the ringer across the pair.
RINGER_IMPEDANCE_OHMS = 8_000


class LoopMeasurement(NamedTuple):
    """
    One mechanised measurement of a subscriber loop.

    The three resistance readings are insulation resistance, taken with the
    loop open. ``loop_resistance_ohms`` is the resistance of the pair with the
    loop closed, and is None where the pair is open and there is nothing to
    measure.
    """

    tip_ring_ohms: int
    tip_ground_ohms: int
    ring_ground_ohms: int
    loop_resistance_ohms: Optional[int]
    capacitance_uf: float
    dc_volts: float
    ac_volts: float
    loop_current_ma: float
    station_termination: bool
    distance_miles: float
    verdict: str
    # The fault MLT is prepared to name. Withheld on the harder difficulty,
    # where reading the numbers is the job.
    suspected: Optional[str]


def _line_seed(number: str, fault: str) -> random.Random:
    """Return a generator seeded so one line always measures the same."""
    return random.Random(f"{number}:{fault}")


def measure_loop(telephone_number: str, fault_code: str,
                 name_fault: bool = True) -> LoopMeasurement:
    """
    Measure a loop and return what mechanised loop testing reports.

    Args:
        telephone_number: The line under test, used to seed the readings
        fault_code: The electrical condition actually present
        name_fault: Whether the system may name the fault it suspects

    Returns:
        The readings, and a verdict line in the system's own voice
    """
    fault = FAULTS.get(fault_code, FAULTS['NONE'])
    rng = _line_seed(telephone_number, fault_code)

    tip_ring = rng.randint(*fault.tip_ring_ohms)
    to_ground_low, to_ground_high = fault.to_ground_ohms
    tip_ground = rng.randint(to_ground_low, to_ground_high)
    # A ground is on one conductor. The other stays clean.
    if fault_code == 'GROUND':
        ring_ground = rng.randint(200_000, 3_000_000)
        if rng.random() < 0.5:
            tip_ground, ring_ground = ring_ground, tip_ground
    else:
        ring_ground = rng.randint(to_ground_low, to_ground_high)

    # Loop length, and therefore capacitance. An open reads short because the
    # measurement stops at the break.
    length_miles = round(rng.uniform(0.4, 3.4), 2)
    if fault_code == 'OPEN':
        distance = round(length_miles * rng.uniform(0.15, 0.85), 2)
    else:
        distance = length_miles
    capacitance = round(distance * CABLE_UF_PER_MILE, 3)

    dc_volts = 0.0
    ac_volts = 0.0
    if fault_code == 'FEMF':
        if rng.random() < 0.6:
            ac_volts = round(rng.uniform(28.0, 118.0), 1)
        else:
            dc_volts = round(rng.uniform(6.0, 52.0), 1)
    elif fault_code == 'CROSS':
        dc_volts = round(rng.uniform(1.5, 9.0), 1)

    station_termination = fault_code not in ('OPEN',)
    if fault_code == 'ROH':
        loop_current = round(rng.uniform(24.0, 46.0), 1)
    elif fault_code == 'SHORT':
        loop_current = round(rng.uniform(60.0, 120.0), 1)
    elif fault_code == 'OPEN':
        loop_current = 0.0
    else:
        loop_current = round(rng.uniform(0.0, 0.4), 1)

    # Loop resistance is only meaningful on a loop that closes. An open pair
    # has none to measure, and a short reads the resistance of the fault
    # rather than the resistance of the pair.
    if fault_code == 'OPEN':
        loop_resistance: Optional[int] = None
    elif fault_code == 'SHORT':
        loop_resistance = tip_ring
    else:
        loop_resistance = int(round(length_miles * LOOP_OHMS_PER_MILE))

    return LoopMeasurement(
        tip_ring_ohms=tip_ring,
        tip_ground_ohms=tip_ground,
        ring_ground_ohms=ring_ground,
        loop_resistance_ohms=loop_resistance,
        capacitance_uf=capacitance,
        dc_volts=dc_volts,
        ac_volts=ac_volts,
        loop_current_ma=loop_current,
        station_termination=station_termination,
        distance_miles=distance,
        verdict=fault.mlt_signature,
        suspected=fault.code if name_fault else None,
    )


# What each condition shows in the readings, written as the sentence a wire
# chief would say over your shoulder. The number in each is pulled from the
# measurement the player actually took, because "you should have measured
# more carefully" teaches nothing and "tip to ring measured 39 ohms" teaches
# the reading.
def _reading_tell(fault_code: str, measured: LoopMeasurement) -> str:
    """Return the sentence naming what the readings said."""
    tip_ring = f"{measured.tip_ring_ohms:,}"
    to_ground = min(measured.tip_ground_ohms, measured.ring_ground_ohms)
    if fault_code == 'OPEN':
        return (f"Tip to ring measured {tip_ring} ohms with no station "
                f"termination, and the capacitance put the end of the pair "
                f"at {measured.distance_miles:.2f} miles. The pair stops "
                f"there.")
    if fault_code == 'SHORT':
        return (f"Tip to ring measured {tip_ring} ohms. Near zero across the "
                f"pair is tip and ring in contact.")
    if fault_code == 'GROUND':
        return (f"One conductor measured {to_ground:,} ohms to ground with "
                f"tip to ring at {tip_ring}. One leg down and the other "
                f"clean is a conductor on earth.")
    if fault_code == 'CROSS':
        return (f"Tip to ring measured {tip_ring} ohms with "
                f"{measured.dc_volts:.1f} volts DC on the pair and no office "
                f"battery applied. That is another pair's battery.")
    if fault_code == 'WET':
        return (f"Insulation measured {tip_ring} ohms tip to ring and "
                f"{to_ground:,} to ground. Low but not zero, and low on "
                f"every reading at once, is water in the sheath.")
    if fault_code == 'FEMF':
        present = (f"{measured.ac_volts:.1f} volts AC" if measured.ac_volts
                   else f"{measured.dc_volts:.1f} volts DC")
        return (f"There was {present} on that pair with no office battery "
                f"applied. Voltage arriving from somewhere else is foreign "
                f"potential.")
    if fault_code == 'ROH':
        return (f"The station was terminated and drawing "
                f"{measured.loop_current_ma:.1f} mA with the loop closed. "
                f"That is a receiver off the hook, not a fault on the pair.")
    if fault_code == 'FCG':
        return ("The loop measured clean to the frame and the office test "
                "was the one that failed. That puts it inside the office.")
    if fault_code == 'CO_EQUIP':
        return (f"Every loop reading was within limits - {tip_ring} ohms tip "
                f"to ring - and the customer was still out of service. A "
                f"clean loop points at the switch.")
    return (f"Every reading was within limits, {tip_ring} ohms tip to ring "
            f"and nothing on the pair that should not be there.")


def post_mortem(telephone_number: str, actual: str,
                claimed: Optional[str], tested: bool) -> str:
    """
    Say what the measurement would have caught, using its own numbers.

    A wrong close out was scored and then forgotten, which taught the
    player that they had guessed wrong without ever teaching them what to
    read. The readings are seeded from the line and the fault, so this can
    quote back the exact figures the player had in front of them.

    Args:
        telephone_number: The line, which seeds its readings
        actual: The condition that was really on the pair
        claimed: What the report was closed as, or None for code 8
        tested: Whether the line was ever measured

    Returns:
        Two sentences at most, or an empty string when there is nothing
        useful to say
    """
    if actual == claimed:
        return ''
    measured = measure_loop(telephone_number, actual, name_fault=False)

    if not tested:
        # Nothing to quote back, because they never looked. Naming a figure
        # here would teach the wrong reading half the time - tip to ring is
        # normal on a ground - so name what the test would have said.
        signature = FAULTS[actual].mlt_signature
        return (f"That line was never measured. mlt would have read: "
                f"{signature[0].lower()}{signature[1:]}.")

    lines = [_reading_tell(actual, measured)]
    if claimed is not None and claimed in FAULTS and claimed != actual:
        signature = FAULTS[claimed].mlt_signature
        lines.append(f"{FAULTS[claimed].name} reads "
                     f"{signature[0].lower()}{signature[1:]}.")
    return ' '.join(lines)


def distance_to_open(capacitance_uf: float) -> float:
    """
    Return the distance a capacitance measurement implies, in miles.

    Local exchange cable runs 0.083 microfarads per mile, so a capacitance
    reading on an open pair is a distance to the break.
    """
    if CABLE_UF_PER_MILE <= 0:
        return 0.0
    return round(capacitance_uf / CABLE_UF_PER_MILE, 2)


def design_note(loop_ohms: Optional[int], length_kft: float) -> str:
    """Return how a loop of this length and resistance should have been built."""
    if loop_ohms is None:
        return (f"{length_kft:.1f} kft measured to the fault. Loop resistance "
                f"cannot be read on an open pair.")
    if length_kft <= NONLOADED_MAX_KFT:
        limit = RESISTANCE_DESIGN_LIMIT_OHMS
        rule = f"nonloaded, {limit} ohms maximum"
    elif length_kft <= LOADED_MAX_KFT:
        limit = LOADED_DESIGN_LIMIT_OHMS
        rule = f"H88 loading, {limit} ohms maximum"
    else:
        return "Beyond 24 kft: digital loop carrier territory."
    state = 'within' if loop_ohms <= limit else 'OVER'
    return f"{length_kft:.1f} kft: {rule}. Measured loop {state} design limit."


class TransmissionResult(NamedTuple):
    """What a test line returned."""

    test_line: str
    loss_db: Optional[float]
    noise_dbrnc: Optional[float]
    noise_with_tone_dbrnc: Optional[float]
    slope_db: Optional[float]
    passed: bool
    notes: List[str]


def access_test_line(code: str, circuit: str,
                     rng: Optional[random.Random] = None,
                     degraded: bool = False) -> Optional[TransmissionResult]:
    """
    Reach a test line on a circuit and return the measurement.

    Args:
        code: Test line code, one of the keys of ``TEST_LINES``
        circuit: The trunk or channel identifier being tested
        rng: Generator, for reproducible tests
        degraded: Whether the circuit under test is known to be impaired

    Returns:
        The measurement, or None if no such test line exists
    """
    test_line = TEST_LINES.get(code.upper())
    if test_line is None:
        return None
    generator = rng or random.Random(f"{code}:{circuit}")

    loss = noise = noise_tone = slope = None
    notes: List[str] = []

    if 'loss' in test_line.measures:
        loss = round(
            generator.uniform(4.2, 7.8) if degraded
            else generator.uniform(0.2, 3.6), 1)
    if 'noise' in test_line.measures:
        noise = round(
            generator.uniform(31.0, 44.0) if degraded
            else generator.uniform(14.0, 29.0), 1)
    if 'noise with tone' in test_line.measures:
        base = noise if noise is not None else 20.0
        noise_tone = round(base + generator.uniform(0.5, 4.0), 1)
    if 'gain slope' in test_line.measures:
        slope = round(
            generator.uniform(1.6, 3.4) if degraded
            else generator.uniform(0.0, 1.2), 1)
    if 'return loss' in test_line.measures:
        loss = round(
            generator.uniform(6.0, 10.0) if degraded
            else generator.uniform(15.0, 27.0), 1)
        notes.append('Balance termination applied; reading is return loss.')

    passed = True
    if code.upper() == 'BAL':
        if loss is not None and loss < 11.0:
            passed = False
            notes.append('Return loss below objective. Check office balance '
                         'network.')
    else:
        if loss is not None and not (LIMITS.loss_low_db <= loss <= LIMITS.loss_high_db):
            passed = False
            notes.append(f'Loss outside {LIMITS.loss_low_db} to '
                         f'{LIMITS.loss_high_db} dB working limits.')
        if noise is not None and noise > LIMITS.noise_high_dbrnc:
            passed = False
            notes.append(f'Noise above {LIMITS.noise_high_dbrnc} dBrnC.')
        if slope is not None and slope > LIMITS.slope_high_db:
            passed = False
            notes.append(f'Gain slope above {LIMITS.slope_high_db} dB.')

    if passed:
        notes.append('Circuit within working limits.')

    return TransmissionResult(
        test_line=test_line.name,
        loss_db=loss,
        noise_dbrnc=noise,
        noise_with_tone_dbrnc=noise_tone,
        slope_db=slope,
        passed=passed,
        notes=notes,
    )


def tone_header() -> str:
    """Return the line describing the test tone every loss reading uses."""
    return f"Test tone {TEST_TONE_HZ} Hz at {TEST_TONE_DBM:+.1f} dBm"


# Supervision states a single frequency signalling unit can show. The 2600 Hz
# tone is on the trunk when it is idle and removed when it is seized, so a
# trunk showing tone while a connection is up, or no tone while idle, is the
# anomaly a routine test is looking for.
SUPERVISION_STATES: Dict[str, Tuple[str, str]] = {
    'IDLE': ('Tone on', 'Trunk idle, SF tone present in both directions.'),
    'SEIZED': ('Tone off', 'Trunk seized, tone removed toward the far end.'),
    'CONNECTED': ('Tone off', 'Talking state, no tone in either direction.'),
    'HELD': ('Tone on far end only', 'Far end has released; near end has not.'),
    'ANOMALOUS': ('Tone on during connection',
                  'Tone present while the trunk is in use. Report to CAROT '
                  'and hold the circuit out of service.'),
}
