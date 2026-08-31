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
