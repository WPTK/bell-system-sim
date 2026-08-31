"""
Trouble reporting: fault types, dispositions and service measurement.

The corrective maintenance sequence the Bell System followed is documented in
Engineering and Operations in the Bell System: detect, notify, verify, locate,
repair, verify. Locating the trouble is described there as the most difficult
and time consuming step, and that is the shape this simulation gives the work.

Two disposition codes are attested and published: code 5 for trouble found and
code 8 for no trouble found, counted separately in the switching performance
measurement plan. They are the success and failure states here.

A caution recorded rather than hidden: the customer-facing report categories a
repair service attendant chose from are NOT verified by any source available
to this project - they most likely live in a Bell System Practice from
division 660, which was not reachable. The FAULTS below are the electrical
conditions the documents do attest; the REPORT_SYMPTOMS are this simulation's
own plain-language wrapping of them, and are marked as such.
"""

from typing import Dict, List, NamedTuple, Tuple


class Fault(NamedTuple):
    """An electrical condition on a subscriber loop or in the office."""

    code: str
    name: str
    where: str
    description: str
    # What mechanised loop testing reports when it measures this condition.
    mlt_signature: str
    # Plausible resistance readings, in ohms, for tip-ring and each to ground.
    tip_ring_ohms: Tuple[int, int]
    to_ground_ohms: Tuple[int, int]
    typical_minutes: Tuple[int, int]
    dispatch: str


# Electrical fault conditions. Every name here appears in the bundled Bell
# documents: open, short, ground, cross, false cross or ground, foreign EMF,
# and the wet cable that causes low insulation resistance.
FAULTS: Dict[str, Fault] = {
    'OPEN': Fault(
        code='OPEN', name='Open', where='LOOP',
        description='One or both conductors discontinuous between the office '
                    'and the station. No loop current can flow.',
        mlt_signature='Infinite resistance tip to ring; no station termination',
        tip_ring_ohms=(3_000_000, 9_999_999),
        to_ground_ohms=(3_000_000, 9_999_999),
        typical_minutes=(90, 320), dispatch='Outside plant',
    ),
    'SHORT': Fault(
        code='SHORT', name='Short', where='LOOP',
        description='Tip and ring in contact. The line appears permanently '
                    'off-hook to the office.',
        mlt_signature='Near zero resistance tip to ring',
        tip_ring_ohms=(0, 90),
        to_ground_ohms=(200_000, 3_000_000),
        typical_minutes=(60, 240), dispatch='Outside plant',
    ),
    'GROUND': Fault(
        code='GROUND', name='Ground', where='LOOP',
        description='One conductor in contact with earth. Causes noise and '
                    'may hold the line off-hook.',
        mlt_signature='Low resistance conductor to ground, tip to ring normal',
        tip_ring_ohms=(150_000, 900_000),
        to_ground_ohms=(0, 4_000),
        typical_minutes=(70, 260), dispatch='Outside plant',
    ),
    'CROSS': Fault(
        code='CROSS', name='Cross', where='LOOP',
        description='Conductors of two different pairs in contact. Each '
                    'subscriber may hear the other.',
        mlt_signature='Foreign potential and abnormal resistance to a second pair',
        tip_ring_ohms=(1_000, 40_000),
        to_ground_ohms=(20_000, 400_000),
        typical_minutes=(110, 400), dispatch='Outside plant',
    ),
    'WET': Fault(
        code='WET', name='Wet cable', where='LOOP',
        description='Water in the cable sheath. Insulation resistance falls '
                    'across many pairs at once and worsens with rain.',
        mlt_signature='Low insulation resistance across several pairs in one cable',
        tip_ring_ohms=(9_000, 90_000),
        to_ground_ohms=(3_000, 60_000),
        typical_minutes=(180, 700), dispatch='Cable repair',
    ),
    'FCG': Fault(
        code='FCG', name='False cross or ground', where='OFFICE',
        description='A test detects a false ground on tip or ring, or a cross '
                    'between the leads, inside the office rather than the loop.',
        mlt_signature='Office test fails; loop measures clean to the frame',
        tip_ring_ohms=(200_000, 2_000_000),
        to_ground_ohms=(100_000, 2_000_000),
        typical_minutes=(30, 130), dispatch='Central office',
    ),
    'FEMF': Fault(
        code='FEMF', name='Foreign EMF', where='LOOP',
        description='Foreign voltage on the pair, commonly from power line '
                    'induction or a crossed power conductor.',
        mlt_signature='DC or AC voltage present with no office battery applied',
        tip_ring_ohms=(80_000, 900_000),
        to_ground_ohms=(40_000, 800_000),
        typical_minutes=(120, 480), dispatch='Outside plant',
    ),
    'ROH': Fault(
        code='ROH', name='Receiver off hook', where='STATION',
        description='The station receiver has been left off hook. The line is '
                    'not faulty; the permanent signal timed out and howler was '
                    'applied.',
        mlt_signature='Station termination present, loop closed, no fault',
        tip_ring_ohms=(180, 900),
        to_ground_ohms=(400_000, 4_000_000),
        typical_minutes=(5, 30), dispatch='None - customer contact',
    ),
    'CO_EQUIP': Fault(
        code='CO_EQUIP', name='Central office equipment', where='OFFICE',
        description='Line equipment, line link appearance or a frame '
                    'cross-connect at fault rather than the loop.',
        mlt_signature='Loop measures clean; fault is toward the switch',
        tip_ring_ohms=(200_000, 3_000_000),
        to_ground_ohms=(200_000, 3_000_000),
        typical_minutes=(25, 120), dispatch='Central office',
    ),
    'NONE': Fault(
        code='NONE', name='No trouble found', where='NONE',
        description='Nothing measures out of limits. The condition may have '
                    'been transient, or it may still be there and hiding.',
        mlt_signature='All measurements within limits',
        tip_ring_ohms=(200_000, 4_000_000),
        to_ground_ohms=(200_000, 4_000_000),
        typical_minutes=(10, 45), dispatch='None',
    ),
}

class FrameDefect(NamedTuple):
    """Something wrong on the main distributing frame rather than the loop."""

    code: str
    name: str
    # What the cross-connect record shows when this is the trouble.
    record_note: str
    # What the frame technician does about it.
    remedy: str


# Central office equipment trouble, as it appears on the frame.
#
# The main distributing frame is the field of terminations where outside
# plant cable meets office equipment: verticals carry the cable side through
# a protector, horizontals carry the equipment side, and a jumper of two
# wires runs between them. Everything that can be wrong with that
# arrangement is here, and all three are ordinary frame troubles rather than
# anything exotic.
#
# Which one a line has is the simulation's own; that these are the three
# things that go wrong on a frame is what the frame is.
FRAME_DEFECTS: Dict[str, FrameDefect] = {
    'WRONG_HORIZONTAL': FrameDefect(
        'WRONG_HORIZONTAL', 'Jumper run to the wrong horizontal',
        'the jumper terminates on a horizontal that is not this line\'s '
        'office equipment',
        'Take the jumper down and run it to the assigned horizontal.'),
    'OPERATED_PROTECTOR': FrameDefect(
        'OPERATED_PROTECTOR', 'Protector unit left operated',
        'the protector unit is in its inactive position, which disconnects '
        'the customer without disturbing the cross-connect',
        'Restore the protector unit. Somebody left it out and forgot.'),
    'OFF_THE_BLOCK': FrameDefect(
        'OFF_THE_BLOCK', 'Jumper off the terminal',
        'one leg of the jumper is not making at the vertical',
        'Re-terminate the jumper. Usually the tip.'),
}

FRAME_DEFECT_CODES: Tuple[str, ...] = tuple(FRAME_DEFECTS)


# Faults a craftsperson would find on a report that turns out to be real.
REAL_FAULTS: List[str] = [
    'OPEN', 'SHORT', 'GROUND', 'CROSS', 'WET', 'FCG', 'FEMF', 'CO_EQUIP',
]

# How a customer describes the trouble. These are the simulation's own
# plain-language wrapping: the electrical conditions above are documented, but
# the category list an attendant selected from is not, so nothing here is
# claimed to be a Bell-published taxonomy.
REPORT_SYMPTOMS: Dict[str, Tuple[str, ...]] = {
    'OPEN': ('No dial tone', 'Cannot call out', 'Line appears dead'),
    'SHORT': ('No dial tone', 'Line always busy to callers'),
    'GROUND': ('Noise on the line', 'Hum on the line', 'Cannot be called'),
    'CROSS': ('Hearing another conversation', 'Noise on the line'),
    'WET': ('Noise on the line', 'Cuts off during calls', 'Weak transmission'),
    'FCG': ('Cannot call out', 'Calls do not complete'),
    'FEMF': ('Loud hum on the line', 'Shock reported at the set'),
    'ROH': ('Cannot be called', 'Callers get busy'),
    'CO_EQUIP': ('Cannot be called', 'Calls do not complete', 'No ring'),
    'NONE': ('Noise on the line', 'Cuts off during calls', 'Cannot call out'),
}


class Disposition(NamedTuple):
    """How a trouble report was closed out."""

    code: int
    name: str
    description: str


# Codes 5 and 8 are published Bell System dispositions, counted separately in
# the network switching performance measurement plan.
DISPOSITIONS: Dict[int, Disposition] = {
    5: Disposition(5, 'Trouble found', 'A fault was located and corrected.'),
    8: Disposition(8, 'No trouble found',
                   'No fault could be located. The report is closed out '
                   'without a repair.'),
}

# Weights from the network switching performance measurement plan for 1 and
# 1A ESS offices. The service index is scored against these.
NSPMP_WEIGHTS: Dict[str, int] = {
    'dial_tone_speed': 15,
    'receiver_overflow': 5,
    'restore_verify_failure': 5,
    'transmitter_timeouts': 10,
    'office_overflow': 15,
    'fcg_supervisory': 15,
    'receiver_timeouts': 10,
    'equipment_irregularities': 5,
    'lost_billing': 10,
    'customer_reports': 10,
}

NSPMP_CATEGORIES: Dict[str, str] = {
    'dial_tone_speed': 'Machine Access',
    'receiver_overflow': 'Machine Access',
    'restore_verify_failure': 'Machine Access',
    'transmitter_timeouts': 'Machine Switching',
    'office_overflow': 'Machine Switching',
    'fcg_supervisory': 'Machine Switching',
    'receiver_timeouts': 'Machine Switching',
    'equipment_irregularities': 'Machine Switching',
    'lost_billing': 'Billing',
    'customer_reports': 'Customer Reports',
}

# Repair forces a report can be dispatched to.
DISPATCH_FORCES: Tuple[str, ...] = (
    'Central office', 'Outside plant', 'Cable repair', 'Station',
)
