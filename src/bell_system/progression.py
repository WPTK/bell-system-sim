"""
Difficulty, qualification and the service index.

Two ways to work a shift. Fun Simulation is forgiving: it will let you close a
report you never tested, it advances you quickly, and a wrong call costs you
little. Craft is close to the job: you cannot close what you have not
measured, closing a real fault as no trouble found brings the report back on
your own index, commitments you miss are counted, and qualification is slow.

Progression is qualification rather than experience points, because that is
what actually governed what a craftsperson was allowed to touch. You start
qualified on your own wire centre and earn the right to work the switching
control centre, remote offices and the toll network.

Scoring is against the customer reports component of the network switching
performance measurement plan. The plan's ten weights sum to 100 and customer
reports carry ten of them; a craftsperson is scored on that component out of
100, and ``Career.office_contribution`` converts the result back into the
points it was worth to the office. Scoring the player across the whole plan
would mean total failure on the one component they control could still cost
only twenty points, which would tell them nothing.
"""

import json
import os
from typing import Dict, List, NamedTuple, Optional

from .data.trouble import NSPMP_WEIGHTS

CAREER_FILENAME = 'career.json'


class Difficulty(NamedTuple):
    """One way of working the shift."""

    key: str
    name: str
    summary: str
    # Must a loop be measured before its report can be closed?
    require_test_before_close: bool
    # Chance a report closed as no trouble found, on a line that really is
    # faulty, comes back as a repeat report.
    repeat_report_chance: float
    # Reports to close for each step of qualification.
    reports_per_qualification: int
    # How heavily a wrong disposition tells against the service index.
    index_penalty: float
    # Whether missed commitment times are counted against you.
    count_missed_commitments: bool
    # How often the other craft interrupt you, as a share of commands.
    interruption_rate: float
    # Minutes of slack added to every repair commitment.
    commitment_slack_minutes: int


DIFFICULTIES: Dict[str, Difficulty] = {
    'fun': Difficulty(
        key='fun',
        name='Fun Simulation',
        summary='Forgiving. Close reports without testing, advance quickly, '
                'and a wrong call costs little.',
        require_test_before_close=False,
        repeat_report_chance=0.25,
        reports_per_qualification=3,
        # Was 0.4, which turned out to be uninformative rather than
        # forgiving: tools/index_calibration.py plays a few hundred shifts
        # per setting and at 0.4 an ordinary player - one who measures every
        # line and names the fault right about six times in seven - scored
        # EXCELLENT in 89 shifts out of 100. A band nearly everybody is in
        # is not a band. At 0.7 the same player has a median of 94.9 and
        # sits on the SATISFACTORY/EXCELLENT line, a careful player is still
        # EXCELLENT 99 times in 100, and a careless one still never is.
        index_penalty=0.7,
        count_missed_commitments=False,
        interruption_rate=0.06,
        commitment_slack_minutes=90,
    ),
    'craft': Difficulty(
        key='craft',
        name='I Hate Myself',
        summary='Close to the job. Measure before you close, repeat reports '
                'come back on your index, commitments are counted, and '
                'qualification is slow.',
        require_test_before_close=True,
        repeat_report_chance=0.85,
        reports_per_qualification=12,
        index_penalty=1.0,
        count_missed_commitments=True,
        interruption_rate=0.22,
        commitment_slack_minutes=0,
    ),
}

DEFAULT_DIFFICULTY = 'fun'

# How the customer reports score is lost, out of 100. A wrong disposition
# weighs heaviest because it is the one that leaves a customer out of service
# believing somebody has dealt with them. These three are the simulation's
# own apportionment; what is published is the ten points the component is
# worth to the office, which office_contribution reports.
WRONG_DISPOSITION_WEIGHT = 55
REPEAT_REPORT_WEIGHT = 35
MISSED_COMMITMENT_WEIGHT = 20


class Qualification(NamedTuple):
    """One thing a craftsperson is signed off to work."""

    key: str
    name: str
    description: str
    # Reports that must be closed correctly before this is offered.
    requires_reports: int
    # Commands this qualification opens.
    unlocks: tuple


# Qualification follows the work: your own frame first, then the office, then
# the systems that reach beyond it, and toll last.
QUALIFICATIONS: List[Qualification] = [
    Qualification(
        'loop', 'Loop and Station',
        'Subscriber loop testing and station trouble. Where every '
        'craftsperson starts.',
        requires_reports=0,
        unlocks=('report', 'mlt', 'trouble', 'testboard', 'testline'),
    ),
    Qualification(
        'frame', 'Main Distributing Frame',
        'Frame assignment, cross-connects and load balance in your own wire '
        'centre.',
        requires_reports=1,
        unlocks=('cosmos', 'lmos'),
    ),
    Qualification(
        'office', 'Central Office Switching',
        'The switching machine itself: alarms, equipment status and office '
        'diagnostics.',
        requires_reports=2,
        unlocks=('switch', 'alarm', 'crossbar', '3a'),
    ),
    Qualification(
        'scc', 'Switching Control Center',
        'Remote administration of offices from the control centre, and the '
        'teletype traffic they generate.',
        requires_reports=4,
        unlocks=('sarts', 'orderwire'),
    ),
    Qualification(
        'trunk', 'Interoffice Trunks',
        'Trunk testing, supervision and the routing of calls between '
        'offices.',
        requires_reports=6,
        unlocks=('trunk', 'routing', 'dialtone', 'testcall'),
    ),
    Qualification(
        'toll', 'Toll Network',
        'The toll network, its measurement systems and the traffic that '
        'crosses regions.',
        requires_reports=9,
        unlocks=('toll', 'tnds', 'traffic'),
    ),
]

QUALIFICATIONS_BY_KEY: Dict[str, Qualification] = {
    qualification.key: qualification for qualification in QUALIFICATIONS
}


class Career:
    """
    What a craftsperson carries from one shift to the next.

    Persisted as JSON beside the settings, and tolerant of a missing or
    damaged file for the same reason: a career record must never stop the
    simulation starting.
    """

    def __init__(self, path: Optional[str] = None,
                 difficulty: str = DEFAULT_DIFFICULTY):
        self.path = path
        self.difficulty_key = difficulty
        self.shift: int = 1
        self.reports_closed: int = 0
        self.reports_correct: int = 0
        self.reports_wrong: int = 0
        self.repeat_reports: int = 0
        self.missed_commitments: int = 0
        self.qualifications: List[str] = ['loop']
        self.index_history: List[float] = []
        if path:
            self.load()

    # -- difficulty ------------------------------------------------------

    @property
    def difficulty(self) -> Difficulty:
        """Return the active difficulty profile."""
        return DIFFICULTIES.get(self.difficulty_key, DIFFICULTIES[DEFAULT_DIFFICULTY])

    def set_difficulty(self, key: str) -> None:
        """Change difficulty and persist it."""
        if key in DIFFICULTIES:
            self.difficulty_key = key
            self.save()

    # -- qualification ---------------------------------------------------

    def is_qualified(self, key: str) -> bool:
        """Return whether the craftsperson holds a qualification."""
        return key in self.qualifications

    def qualification_for_command(self, command: str) -> Optional[str]:
        """Return the qualification a command needs, if any."""
        for qualification in QUALIFICATIONS:
            if command in qualification.unlocks:
                return qualification.key
        return None

    def may_use(self, command: str) -> bool:
        """Return whether the craftsperson may use a command."""
        needed = self.qualification_for_command(command)
        return needed is None or needed in self.qualifications

    def available_qualifications(self) -> List[Qualification]:
        """Return qualifications earned but not yet taken up."""
        threshold = self.difficulty.reports_per_qualification
        return [
            qualification for qualification in QUALIFICATIONS
            if qualification.key not in self.qualifications
            and self.reports_correct >= qualification.requires_reports * threshold
        ]

    def grant_available(self) -> List[Qualification]:
        """Award every qualification whose requirement is met."""
        granted = self.available_qualifications()
        for qualification in granted:
            self.qualifications.append(qualification.key)
        if granted:
            self.save()
        return granted

    def next_qualification(self) -> Optional[Qualification]:
        """Return the next qualification to work toward."""
        held = set(self.qualifications)
        for qualification in QUALIFICATIONS:
            if qualification.key not in held:
                return qualification
        return None

    def reports_until_next(self) -> int:
        """Return how many more correct closures the next qualification needs."""
        nxt = self.next_qualification()
        if nxt is None:
            return 0
        needed = nxt.requires_reports * self.difficulty.reports_per_qualification
        return max(0, needed - self.reports_correct)

    # -- service index ---------------------------------------------------

    def service_index(self) -> float:
        """
        Return this craftsperson's customer report performance, out of 100.

        A word about what this number is and is not. The network switching
        performance measurement plan scored an *office*, across ten weighted
        components summing to 100, of which customer reports carried ten.
        Scoring a player on that whole scale would mean total failure on the
        one component they control could still only cost twenty points, which
        tells them nothing.

        So this is the customer reports component itself, scored out of 100.
        ``office_contribution`` converts it back into the points it would
        have been worth in the plan, which is where the published weight
        belongs.

        The three ways to lose it are the three ways the work goes wrong: a
        wrong disposition, a report that came back, and a commitment missed.
        A wrong close weighs heaviest because it is the one that leaves a
        customer out of service believing they have been dealt with.

        The 55/35/20 apportionment was the simulation's own and, for a long
        time, untested. It has now been played: tools/index_calibration.py
        works a few hundred shifts per setting with players who fail in one
        way each, and the ordering holds. A player who measures every line
        and then names the wrong fault scores worse than one who is merely
        ordinary, and one who never measures at all scores worse again.

        The same exercise found what this number does NOT measure, which is
        worth saying here rather than leaving to be discovered. It is a
        rate, not a volume. A tour that closes five reports perfectly scores
        100, better than a tour that closes thirty-two with two mistakes.
        That is correct for what it is - the performance plan scored offices
        on rates, and a repair index has never been a productivity measure -
        but it means the index alone does not tell you whether the board
        moved. The handoff record prints closed and carried beside it for
        exactly that reason.
        """
        if not self.reports_closed:
            return 100.0

        closed = self.reports_closed
        wrong_rate = self.reports_wrong / closed
        repeat_rate = min(1.0, self.repeat_reports / closed)
        missed_rate = (min(1.0, self.missed_commitments / closed)
                       if self.difficulty.count_missed_commitments else 0.0)

        penalty = (
            wrong_rate * WRONG_DISPOSITION_WEIGHT
            + repeat_rate * REPEAT_REPORT_WEIGHT
            + missed_rate * MISSED_COMMITMENT_WEIGHT
        ) * self.difficulty.index_penalty

        return max(0.0, round(100.0 - penalty, 1))

    def office_contribution(self, component: str = 'customer_reports') -> float:
        """
        Return what this performance is worth to the office's own index.

        Customer reports carry ten of the plan's hundred points. This is that
        share, earned in proportion to the score above.

        Args:
            component: Which of the plan's ten components to weigh this
                against. Only a desk the plan actually covers passes
                anything but the default; most of the twelve positions are
                outside its scope and say so rather than borrowing a key.
        """
        weight = NSPMP_WEIGHTS.get(component, NSPMP_WEIGHTS['customer_reports'])
        return round(weight * self.service_index() / 100.0, 1)

    def index_band(self) -> str:
        """Return the service band the current index falls in."""
        index = self.service_index()
        if index >= 95:
            return 'EXCELLENT'
        if index >= 88:
            return 'SATISFACTORY'
        if index >= 78:
            return 'MARGINAL'
        return 'UNSATISFACTORY'

    # -- recording -------------------------------------------------------

    def record_closure(self, correct: bool, missed_commitment: bool = False) -> None:
        """Record a closed trouble report."""
        self.reports_closed += 1
        if correct:
            self.reports_correct += 1
        else:
            self.reports_wrong += 1
        if missed_commitment:
            self.missed_commitments += 1
        self.save()

    def record_repeat(self) -> None:
        """Record a report that came back after being closed."""
        self.repeat_reports += 1
        self.save()

    def end_shift(self) -> None:
        """Close the shift, banking the index and advancing the count."""
        self.index_history.append(round(self.service_index(), 1))
        self.shift += 1
        self.save()

    # -- persistence -----------------------------------------------------

    def load(self) -> None:
        """Read the career record, ignoring anything unreadable."""
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r') as handle:
                stored = json.load(handle)
        except (OSError, ValueError):
            return
        if not isinstance(stored, dict):
            return

        self.shift = max(1, int(stored.get('shift', 1)))
        self.reports_closed = max(0, int(stored.get('reports_closed', 0)))
        self.reports_correct = max(0, int(stored.get('reports_correct', 0)))
        self.reports_wrong = max(0, int(stored.get('reports_wrong', 0)))
        self.repeat_reports = max(0, int(stored.get('repeat_reports', 0)))
        self.missed_commitments = max(0, int(stored.get('missed_commitments', 0)))

        held = stored.get('qualifications')
        if isinstance(held, list):
            self.qualifications = [
                key for key in held if key in QUALIFICATIONS_BY_KEY
            ] or ['loop']

        history = stored.get('index_history')
        if isinstance(history, list):
            self.index_history = [
                float(entry) for entry in history
                if isinstance(entry, (int, float))
            ][-40:]

        difficulty = stored.get('difficulty')
        if difficulty in DIFFICULTIES:
            self.difficulty_key = difficulty

    def save(self) -> None:
        """Write the career record, ignoring a read-only filesystem."""
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as handle:
                json.dump({
                    'difficulty': self.difficulty_key,
                    'shift': self.shift,
                    'reports_closed': self.reports_closed,
                    'reports_correct': self.reports_correct,
                    'reports_wrong': self.reports_wrong,
                    'repeat_reports': self.repeat_reports,
                    'missed_commitments': self.missed_commitments,
                    'qualifications': self.qualifications,
                    'index_history': self.index_history[-40:],
                }, handle, indent=2, sort_keys=True)
                handle.write('\n')
        except OSError:
            return


def career_path(state_directory: str) -> str:
    """Return the career file path inside a state directory."""
    return os.path.join(state_directory, CAREER_FILENAME)


# The position a craftsperson is assigned to carries its own sign-off: you
# were put at that desk, so you are qualified for it. Everything beyond the
# desk is earned. Roles whose work needs no qualification are absent.
ROLE_QUALIFICATIONS: Dict[str, str] = {
    'switch': 'office',
    'field': 'loop',
    'noc': 'trunk',
    'dba': 'frame',
    'netplan': 'trunk',
    'custserv': 'loop',
    'tnds': 'toll',
    'sarts': 'scc',
}
