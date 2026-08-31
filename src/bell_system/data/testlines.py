"""
Test lines, responders and the transmission measurements they return.

Every test line type named here is attested in the bundled documents. The
Bell System Technical Journal for April 1982 describes single-channel
transmission testing "using the RT miniresponder as a 102-type Far-End Test
Line (FETL) for a 1-way (RSS to ESS) loss measurement, a 100-type FETL for a
1-way (RSS to ESS) loss and noise measurement, or a 105-type FETL for 2-way
loss, noise, noise with tone, and gainslope measurements". The same paper
describes the Remote Office Test Line and the 52A responder it contains, the
Centralized Automatic Reporting On Trunks system that drives them with
multifrequency signalling, and the Processor Controlled Interrogator that
works the same equipment from the local office or a switching control centre
without CAROT. Balance test lines in toll offices are described in
Telecommunications Transmission Engineering volume 3, which also gives 1004 Hz
as the frequency the loss objectives are stated at.

What is NOT claimed: the dialable access codes for these test lines varied by
office and were carried in office records rather than a national list, so the
codes below are the simulation's own and are marked as such. The measurement
limits are the simulation's own working values too, chosen to sit either side
of the published 1004 Hz objectives rather than to reproduce any one office's
test record.
"""

from typing import Dict, NamedTuple, Tuple

# The frequency the Bell System stated its loss objectives at, and therefore
# the frequency every loss measurement here is made at.
TEST_TONE_HZ = 1004

# Transmitted level of the test tone at the sending end.
TEST_TONE_DBM = 0.0


class TestLine(NamedTuple):
    """One test line or responder a craftsperson can reach."""

    code: str
    name: str
    measures: Tuple[str, ...]
    direction: str
    description: str
    # Access code within the office. Simulation's own: real codes were local.
    access: str
    attested: bool


TEST_LINES: Dict[str, TestLine] = {
    '100': TestLine(
        code='100', name='100-type far-end test line',
        measures=('loss', 'noise'),
        direction='one way',
        description='Terminates the far end and returns a one-way loss and '
                    'noise measurement toward the testing office.',
        access='0100', attested=True,
    ),
    '102': TestLine(
        code='102', name='102-type far-end test line',
        measures=('loss',),
        direction='one way',
        description='Milliwatt supply at the far end for a one-way loss '
                    'measurement. The simplest of the series.',
        access='0102', attested=True,
    ),
    '105': TestLine(
        code='105', name='105-type far-end test line',
        measures=('loss', 'noise', 'noise with tone', 'gain slope'),
        direction='two way',
        description='Responder giving two-way loss, noise, noise with tone '
                    'and gain slope. The full transmission picture.',
        access='0105', attested=True,
    ),
    'BAL': TestLine(
        code='BAL', name='Balance test line',
        measures=('return loss',),
        direction='toward the switch',
        description='Connects the balance termination to the trunk so the '
                    'office balance network can be measured.',
        access='0104', attested=True,
    ),
    'ROTL': TestLine(
        code='ROTL', name='Remote office test line',
        measures=('loss', 'noise', 'supervision'),
        direction='two way',
        description='Seizes a trunk from the far office under command and '
                    'connects it to a 52A responder. Driven by CAROT, or by '
                    'the processor controlled interrogator from an SCC.',
        access='0103', attested=True,
    ),
}

# Ordering for display: the numbered series first, then the two by name.
TEST_LINE_ORDER: Tuple[str, ...] = ('102', '100', '105', 'BAL', 'ROTL')


class TransmissionLimits(NamedTuple):
    """Working limits a measurement is judged against."""

    loss_low_db: float
    loss_high_db: float
    noise_high_dbrnc: float
    slope_high_db: float


# The simulation's own working limits. Loss is judged either side of the via
# net loss range a short intertoll trunk would carry; noise and slope are set
# where a craftsperson would start looking rather than where a circuit fails
# outright.
LIMITS = TransmissionLimits(
    loss_low_db=0.0,
    loss_high_db=4.0,
    noise_high_dbrnc=31.0,
    slope_high_db=1.5,
)


class Responder(NamedTuple):
    """Far-end equipment that answers an automatic test."""

    code: str
    name: str
    description: str


RESPONDERS: Dict[str, Responder] = {
    '52A': Responder(
        '52A', '52A responder',
        'The responder inside a remote office test line. CAROT sends it '
        'multifrequency signals; it configures itself for the test, sends or '
        'receives tones, and reports back.'),
    'MINI': Responder(
        'MINI', 'Miniresponder',
        'A single-board version of the 52A carried in a remote switching '
        'terminal, functionally the same as a 56A remote office test line.'),
}

# Channel maintenance states used by remote switching, quoted from the same
# paper. "High and wet" means the host side is off-hook outside a connection,
# most often because carrier has failed.
CHANNEL_STATES: Dict[str, str] = {
    'ACTIVE': 'Available for use by both call processing and maintenance.',
    'HIGH AND WET': 'Host side off-hook and not in a connection. Unavailable '
                    'to call processing; usually a carrier failure.',
    'CML': 'Queued for a deferred channel diagnostic. Temporarily '
           'unavailable to call processing.',
    'LOCKED OUT': 'Out of service and permanently unavailable to call '
                  'processing without manual intervention.',
}


class PlantTest(NamedTuple):
    """A test number a craftsperson dials from a station to check a line."""

    key: str
    name: str
    # What you do with it, in one line.
    purpose: str
    # What happens when the line is good.
    good: str
    attested: bool


# Plant test numbers: what a craftsperson dials to check a subscriber line
# rather than a trunk. Every one of these is attested.
#
# The automatic number announcement circuit reads back the number of the
# line you are calling from, which is what an installer uses to find out
# which pair they are on. A 102-type line is a milliwatt supply and returns
# 1004 Hz at 0 dBm; a 100-type line is a quiet termination and returns
# silence, which is what you measure noise against. A loop around is a pair
# of numbers: one end returns the milliwatt tone and the other is silent,
# and calling both connects them, which is how one person tested a circuit
# end to end on their own. Ringback rings the line you are calling from
# after you hang up.
#
# What is NOT claimed: the dialable codes. Those were carried in each
# office's records rather than in a national list, and the access strings
# below are the simulation's own, as the trunk test lines above already say.
PLANT_TESTS: Dict[str, PlantTest] = {
    'ANAC': PlantTest(
        'ANAC', 'Automatic number announcement',
        'Reads back the number of the line you are calling from.',
        'A recorded voice gives the ten digits, twice.',
        attested=True),
    'MW': PlantTest(
        'MW', 'Milliwatt supply (102 type)',
        'Returns 1004 Hz at 0 dBm so a loss measurement has something to '
        'measure.',
        'A steady tone at reference level.',
        attested=True),
    'QUIET': PlantTest(
        'QUIET', 'Quiet termination (100 type)',
        'Terminates the line in its characteristic impedance and sends '
        'nothing, so noise can be measured against silence.',
        'Silence, and a noise reading well under the objective.',
        attested=True),
    'LOOP': PlantTest(
        'LOOP', 'Loop around',
        'Two numbers: one returns the tone, the other is silent, and '
        'calling both connects them end to end.',
        'Tone on the first, and it drops when the second is answered.',
        attested=True),
    'RING': PlantTest(
        'RING', 'Ringback',
        'Rings the line you are calling from after you hang up, so ringing '
        'and the ringer can be checked from the station.',
        'The line rings back within a few seconds.',
        attested=True),
}

PLANT_TEST_ORDER: Tuple[str, ...] = ('ANAC', 'MW', 'QUIET', 'LOOP', 'RING')

# What each plant test does on a line with a given fault. The mapping is the
# simulation's own reasoning from the electrical condition: an open pair
# cannot carry a call at all, a ground puts noise on everything, and a
# receiver off hook means the line is busy to the test as well.
#
# A value of None means the test tells you nothing useful on that fault,
# which is itself worth knowing: no single test finds everything.
PLANT_TEST_RESULTS: Dict[str, Dict[str, str]] = {
    'OPEN': {
        'ANAC': 'No answer. The call does not complete: nothing on the pair.',
        'MW': 'No answer. Nothing is getting through.',
        'QUIET': 'No answer.',
        'LOOP': 'No answer at either end.',
        'RING': 'No ringback. The pair will not carry the current.',
    },
    'SHORT': {
        'ANAC': 'Busy. The office sees this line permanently off hook.',
        'MW': 'Busy.',
        'QUIET': 'Busy.',
        'LOOP': 'Busy.',
        'RING': 'No ringback: the line never goes on hook to be rung.',
    },
    'GROUND': {
        'ANAC': 'Reads back, under a hum you can hear over the announcement.',
        'MW': 'Tone present, and a hum with it.',
        'QUIET': 'Not quiet. Noise well over the objective on a line that '
                 'should be silent.',
        'LOOP': 'Tone present, noisy both ways.',
        'RING': 'Rings back, and the ringer sounds tinny.',
    },
    'CROSS': {
        'ANAC': 'Reads back, and somebody else is audible on the pair.',
        'MW': 'Tone present with a second conversation under it.',
        'QUIET': 'Not quiet. Speech audible on a line terminated in silence.',
        'LOOP': 'Tone present, and a third party on the circuit.',
        'RING': 'Rings back, and so does something else.',
    },
    'WET': {
        'ANAC': 'Reads back, weak and cutting.',
        'MW': 'Tone present but down on level, and it wanders.',
        'QUIET': 'Noise over the objective, rising and falling.',
        'LOOP': 'Tone down at both ends.',
        'RING': 'Rings back weakly.',
    },
    'FEMF': {
        'ANAC': 'Reads back under a loud hum at power frequency.',
        'MW': 'Tone present, buried in hum.',
        'QUIET': 'Loud hum on a line that should be silent. Foreign voltage.',
        'LOOP': 'Hum at both ends.',
        'RING': 'Rings back. The hum is there through the ring.',
    },
    'ROH': {
        'ANAC': 'Busy.',
        'MW': 'Busy.',
        'QUIET': 'Busy.',
        'LOOP': 'Busy.',
        'RING': 'No ringback: the receiver is off the hook.',
    },
    'FCG': {
        'ANAC': 'No answer, and the loop measures clean to the frame.',
        'MW': 'No answer.',
        'QUIET': 'No answer.',
        'LOOP': 'No answer.',
        'RING': 'No ringback.',
    },
    'CO_EQUIP': {
        'ANAC': 'No answer. Whatever is wrong is on the office side.',
        'MW': 'No answer.',
        'QUIET': 'No answer.',
        'LOOP': 'No answer.',
        'RING': 'No ringback.',
    },
    'NONE': {
        'ANAC': 'Reads the number back cleanly, twice.',
        'MW': 'Steady tone at reference level.',
        'QUIET': 'Silence. Noise well under the objective.',
        'LOOP': 'Tone on the first, dropping when the second answers.',
        'RING': 'Rings back within a few seconds.',
    },
}
