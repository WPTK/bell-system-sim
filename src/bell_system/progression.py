"""
Difficulty, qualification and the service index.

Two ways to work a shift. Fun Simulation is forgiving: it will let you close a
report you never tested, it advances you quickly, and a wrong call costs you
little. Craft is close to the job: you cannot close what you have not
measured, closing a real fault as no trouble found brings the report back on
your own index, commitments you miss are counted, and qualification is slow.

Progression is qualification rather than experience points, because a
craft job was one of being trusted with more of the plant. The sign-off
ladder below is the simulation's own mechanic: no source consulted sets how
many reports earned a Bell System craftsperson which sign-off, or whether a
sign-off gated a command at all, and SOURCES.md says so. You start qualified
on your own wire centre and earn the right to work the switching control
centre, remote offices and the toll network.

Scoring is against the customer reports component of the network switching
performance measurement plan. The plan's ten weights sum to 100 and customer
reports carry ten of them; a craftsperson is scored on that component out of
100, and ``Career.office_contribution`` converts the result back into the
points it was worth to the office. Scoring the player across the whole plan
would mean total failure on the one component they control could still cost
only twenty points, which would tell them nothing.
"""

import json
import math
import os
from typing import Any, Callable, Dict, List, NamedTuple, Optional

from .data.trouble import NSPMP_WEIGHTS
from .jsonfile import read_json, write_text_atomically

CAREER_FILENAME = 'career.json'

# The shape of career.json. 1 is every file written before this field
# existed. A file is read whatever its number says, because every field
# below defaults when it is missing: the number records which fields the
# writer knew about, so that a later change can tell an old file from a new
# one without guessing from what is absent. Fields that later work wants
# to keep across tours are all here already, so adding the next one is a
# line in _LIST_FIELDS or _COUNT_FIELDS and not a change to load or save.
SCHEMA = 2

# Career attributes that are a list of names, in the order they happened.
_LIST_FIELDS = ('commendations', 'finds', 'groups', 'beats_seen',
                'practicals_passed', 'offered', 'audit_open')
# Career attributes that are a count for each of a set of names.
_COUNT_FIELDS = ('fault_sightings', 'rapport')
# Every key save() writes. Anything else in the file is a later version's.
_KNOWN_KEYS = frozenset((
    'schema', 'difficulty', 'shift', 'reports_closed', 'reports_correct',
    'reports_wrong', 'repeat_reports', 'missed_commitments', 'qualifications',
    'index_history', 'office', 'finished', 'assignment', 'audit_verdict',
    'audit_late',
)) | frozenset(_LIST_FIELDS) | frozenset(_COUNT_FIELDS)


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
    # How much of MISSED_COMMITMENT_WEIGHT a missed commitment costs: all of
    # it where the job counts them, a share of it where it is forgiving.
    missed_commitment_scale: float
    # How often the other craft interrupt you, as a share of commands.
    interruption_rate: float
    # Minutes of slack added to every repair commitment.
    commitment_slack_minutes: int
    # How many sightings of one fault type still get a reading note from
    # the mechanised test and a naming from the field. Counted per fault
    # type in Career.fault_sightings, 0 for none at all. A profile's way of
    # coaching, kept apart from require_test_before_close so that asking
    # for the one does not change the other.
    annotation_sightings: int


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
        # is not a band. At 0.7 the same player has a median of 95.0 and
        # sits on the SATISFACTORY/EXCELLENT line, a careful player is still
        # EXCELLENT in all 200 shifts played, and a careless one never is
        # (re-measured with commitments and the unworked board counted).
        index_penalty=0.7,
        missed_commitment_scale=0.25,
        interruption_rate=0.06,
        commitment_slack_minutes=90,
        annotation_sightings=4,
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
        missed_commitment_scale=1.0,
        interruption_rate=0.22,
        commitment_slack_minutes=0,
        annotation_sightings=0,
    ),
}

DEFAULT_DIFFICULTY = 'fun'


class Assist(NamedTuple):
    """
    One thing a player can turn up or down without changing profile.

    A difficulty profile is a bundle, and a player who wants the craft
    scoring with the fun pace has no way to say so. An assist names one
    field of the profile, and what it may be set to in place of the
    profile's own value. The setting ``key`` is the authority; the profile
    is what applies while it reads ``profile``.
    """

    key: str
    # The Difficulty field this overrides.
    field: str
    # What each choice sets the field to.
    choices: Dict[str, Any]
    summary: str
    detail: str


PROFILE = 'profile'

# annotation_sightings for a player who wants the notes to stay.
ANNOTATE_ALWAYS = 1_000_000

ASSISTS: List[Assist] = [
    Assist(
        'assist.test_first', 'require_test_before_close',
        {'on': True, 'off': False},
        'Must a loop be measured before its report is closed',
        'on refuses a close on a line nobody has measured; off allows it.',
    ),
    Assist(
        'assist.commitments_count', 'missed_commitment_scale',
        {'off': 0.0, 'soft': 0.25, 'full': 1.0},
        'How much a missed commitment costs the index',
        'full counts every miss at its whole weight, as the job does; soft '
        'at a quarter of it; off not at all. A report still open past its '
        'commitment is lost in full whatever this says.',
    ),
    Assist(
        'assist.repeat_reports', 'repeat_report_chance',
        {'off': 0.0, 'soft': 0.25, 'full': 0.85},
        'How often a wrongly closed line calls back',
        'The chance that a report closed no trouble found on a line that '
        'was faulty comes back as a repeat: never, one time in four, or '
        'most of the time.',
    ),
    Assist(
        'assist.commitment_slack', 'commitment_slack_minutes',
        {'on': 90, 'off': 0},
        'Extra time on every repair commitment',
        'on adds ninety minutes to each commitment; off holds them to the '
        'interval the plan sets.',
    ),
    Assist(
        'assist.pace', 'reports_per_qualification',
        {'quick': 3, 'slow': 12},
        'Correct closures for each step of qualification',
        'quick offers a sign-off at every 3 correct closures a step, slow '
        'at every 12. The practical is what signs it.',
    ),
    Assist(
        'assist.scoring', 'index_penalty',
        {'gentle': 0.7, 'strict': 1.0},
        'How heavily a mistake tells against the index',
        'gentle scales every penalty by 0.7, strict by 1.0.',
    ),
    Assist(
        'assist.annotate', 'annotation_sightings',
        {'off': 0, 'fade': 4, 'on': ANNOTATE_ALWAYS},
        'Whether the test and the crews keep naming the fault',
        'off prints the numbers and nothing else from the first sighting; '
        'fade names a fault type for its first two sightings, the crew class '
        'for the next two, and then leaves the reading to you; on never '
        'stops.',
    ),
]

ASSISTS_BY_KEY: Dict[str, Assist] = {assist.key: assist for assist in ASSISTS}

# How the customer reports score is lost, out of 100. A wrong disposition
# weighs heaviest because it is the one that leaves a customer out of service
# believing somebody has dealt with them. These three are the simulation's
# own apportionment; what is published is the ten points the component is
# worth to the office, which office_contribution reports.
WRONG_DISPOSITION_WEIGHT = 55
REPEAT_REPORT_WEIGHT = 35
MISSED_COMMITMENT_WEIGHT = 20
# A report still open and past its commitment is a customer who has been told
# somebody would come and nobody has. It is lost in full on either setting,
# which is what keeps a board nobody works from scoring as a perfect one.
UNWORKED_BACKLOG_WEIGHT = 50


def score_index(closed: int, wrong: int, repeats: int, missed: int,
                backlog: int, difficulty: 'Difficulty') -> float:
    """
    Score a record out of 100. Career.service_index is this with the
    career's own counts; tools/index_calibration.py calls it with a played
    shift's, so the two cannot drift apart.

    Every report whose fate is decided is either closed or still open past
    its commitment. A career that has closed nothing but is sitting on an
    overdue board has a score, and it is not 100.
    """
    decided = closed + backlog
    if not decided:
        return 100.0

    wrong_rate = wrong / closed if closed else 0.0
    repeat_rate = min(1.0, repeats / closed) if closed else 0.0
    missed_rate = min(1.0, missed / decided)
    backlog_rate = backlog / decided

    penalty = (
        wrong_rate * WRONG_DISPOSITION_WEIGHT
        + repeat_rate * REPEAT_REPORT_WEIGHT
        + missed_rate * MISSED_COMMITMENT_WEIGHT
        * difficulty.missed_commitment_scale
        + backlog_rate * UNWORKED_BACKLOG_WEIGHT
    ) * difficulty.index_penalty

    return max(0.0, round(100.0 - penalty, 1))


class Qualification(NamedTuple):
    """One thing a craftsperson is signed off to work."""

    key: str
    name: str
    description: str
    # Reports that must be closed correctly before this is offered.
    requires_reports: int
    # Commands this qualification opens.
    unlocks: tuple
    # The one thing it lets you do to the board, as typed, and what it does.
    # The rest of unlocks is screens to read; this is the reward for the
    # sign-off. Nothing here is gated separately: the command it hangs from
    # is in unlocks, so the wire chief refuses it until the sign-off is held.
    verb: str = ''
    verb_effect: str = ''


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
        verb='cosmos fix <report>',
        verb_effect='Clear a jumper or protector fault at the frame, no '
                    'truck.',
    ),
    Qualification(
        'office', 'Central Office Switching',
        'The switching machine itself: alarms, equipment status and office '
        'diagnostics.',
        requires_reports=2,
        unlocks=('switch', 'alarm', 'crossbar', '3a'),
        verb='switch clear <report>',
        verb_effect='Busy out and move a line off bad line equipment: a '
                    'false cross or ground, cleared from the switch.',
    ),
    Qualification(
        'scc', 'Switching Control Center',
        'Remote administration of offices from the control centre, and the '
        'teletype traffic they generate.',
        requires_reports=4,
        # connect(1) is what this sign-off is actually for. It said
        # "remote administration of offices from the control centre" and
        # paid out in two commands that stay in your own building.
        unlocks=('sarts', 'orderwire', 'connect'),
        verb='connect pool <force>',
        verb_effect='Draw a crew from the control centre pool when '
                    'yours are out. One a tour, and it starts far away.',
    ),
    Qualification(
        'trunk', 'Interoffice Trunks',
        'Trunk testing, supervision and the routing of calls between '
        'offices.',
        requires_reports=6,
        unlocks=('trunk', 'routing', 'dialtone', 'testcall'),
        verb='trunk trace <report>',
        verb_effect='Test the trunks the customer calls take and find '
                    'the bad one, which is what a no-trouble report on '
                    'calls not completing usually is.',
    ),
    Qualification(
        'toll', 'Toll Network',
        'The toll network, its measurement systems and the traffic that '
        'crosses regions.',
        # Nine, then ten. tools/index_calibration.py plays whole careers
        # through the terminal now that the clocks agree. At nine (108
        # correct closes on I Hate Myself) a bot that names the fault 60
        # times in 100 reached Toll on the last tour in 2 careers of 12. At
        # ten (120), in 40 careers each, it never does, and a bot at 90 in
        # 100 signs off on all six in 97% of them, the median on tour 12.
        # That bot is a ceiling and a person is slower, so on I Hate Myself
        # Toll is for someone working very well. assist.pace is the way to
        # ask for the quicker ladder without changing the scoring.
        requires_reports=10,
        unlocks=('toll', 'tnds', 'traffic'),
        verb='toll control <block|reroute|off>',
        verb_effect='Hold calls off a congested route to thin the board. '
                    'It stays on, and what it costs you stays with it, '
                    'until you take it off.',
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
        # Reports open and past commitment right now. Not part of the saved
        # record: it is a fact about the board, so whoever holds the board
        # supplies it, and a career with no board has none.
        self.open_overdue: Callable[[], int] = lambda: 0
        self.qualifications: List[str] = ['loop']
        self.index_history: List[float] = []
        # The wire centre this career is assigned to. Chosen the first time
        # a session opens and then kept: the switching machine at an office
        # is drawn at random, so the COMMON LANGUAGE code was coming out
        # different every session and a craftsperson was turning up at a
        # different building each morning. Nothing noticed until a shift
        # started surviving the session and refused to load into the wrong
        # office.
        self.office: Dict[str, str] = {}
        # Set when the last tour has been signed off. There is nobody to
        # relieve you twice on the last day of the Bell System.
        self.finished = False
        # How the assists in the settings bend the profile. Not part of the
        # saved record: the setting is the authority, and whoever holds the
        # settings supplies them, as with open_overdue above.
        self._assists: Dict[str, Any] = {}
        # How many times each fault type has been seen across the career.
        self.fault_sightings: Dict[str, int] = {}
        # Named, earned, never lost.
        self.commendations: List[str] = []
        # Fragments of the machine the player has read.
        self.finds: List[str] = []
        # Unix groups the player has been added to.
        self.groups: List[str] = []
        # Goodwill with the other craft, by login.
        self.rapport: Dict[str, int] = {}
        # Story beats that have already been played.
        self.beats_seen: List[str] = []
        # Qualifications whose practical has been passed.
        self.practicals_passed: List[str] = []
        # Qualifications whose practical has been offered by mail, once.
        self.offered: List[str] = []
        # Where the career was assigned at the end of it. Nothing sets it:
        # the plan's assignment form was dropped, and the epilogue reads the
        # office's own company instead.
        self.assignment: str = ''
        # What the audit at the end of the last tour found, kept so that the
        # last day can be read again: the verdict, the reports that went
        # over open with the craftsperson's name on them, and how many of
        # those were past commitment. Empty until the career is signed off.
        self.audit_verdict: str = ''
        self.audit_open: List[str] = []
        self.audit_late: int = 0
        # What a later version wrote that this one does not understand, held
        # so that saving does not delete it. See load().
        self._unknown: Dict[str, Any] = {}
        self._unknown_qualifications: List[str] = []
        self._unknown_practicals: List[str] = []
        self._schema_seen = 0
        if path:
            self.load()

    # -- difficulty ------------------------------------------------------

    @property
    def difficulty(self) -> Difficulty:
        """Return the active difficulty profile, with the assists applied."""
        profile = DIFFICULTIES.get(self.difficulty_key,
                                   DIFFICULTIES[DEFAULT_DIFFICULTY])
        return profile._replace(**self._assists) if self._assists else profile

    def set_assists(self, overrides: Dict[str, Any]) -> None:
        """
        Replace the assists in force.

        Args:
            overrides: Difficulty field to the value that takes the place
                of the profile's own, as Settings.assist_overrides gives it
        """
        known = set(Difficulty._fields)
        self._assists = {field: value for field, value in overrides.items()
                         if field in known}

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

    def offer_available(self) -> List[Qualification]:
        """Return qualifications whose count is met but are not yet held."""
        threshold = self.difficulty.reports_per_qualification
        return [
            qualification for qualification in QUALIFICATIONS
            if qualification.key not in self.qualifications
            and self.reports_correct >= qualification.requires_reports * threshold
        ]

    def pass_practical(self, key: str) -> Optional[Qualification]:
        """
        Sign off a qualification whose practical has been passed.

        The count only offers it, and 'qual take' will not stage a practical
        before the count is met. Once it is up, passing it is what counts:
        the count may have moved while it was (a pace or difficulty change
        raises the bar), and a practical that was passed is not undone by
        that. Returns None for a key that is not a sign-off, or is already
        held, and changes nothing.
        """
        qualification = QUALIFICATIONS_BY_KEY.get(key)
        if qualification is None or key in self.qualifications:
            return None
        if key not in self.practicals_passed:
            self.practicals_passed.append(key)
        self.qualifications.append(key)
        self.save()
        return qualification

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

        The ways to lose it are the ways the work goes wrong: a wrong
        disposition, a report that came back, a commitment missed, and a
        report still sitting open past its commitment. A wrong close weighs
        heaviest because it is the one that leaves a customer out of
        service believing they have been dealt with. A commitment passes
        whether or not anybody was working the report, so it is counted when
        it passes, and counted softly on the forgiving setting and in full
        on the other.

        The 55/35/20 apportionment (and the 50 for a board left to age) was
        the simulation's own and, for a long time, untested. It has now been
        played: tools/index_calibration.py
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
        return score_index(self.reports_closed, self.reports_wrong,
                           self.repeat_reports, self.missed_commitments,
                           self.open_overdue(), self.difficulty)

    def scored(self) -> bool:
        """
        Whether there is anything yet for the index to be a score of.

        Nothing closed and nothing open past its commitment is not a perfect
        record, it is no record, and it is not banked as one.
        """
        return bool(self.reports_closed + self.open_overdue())

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

    def record_closure(self, correct: bool) -> None:
        """Record a closed trouble report."""
        self.reports_closed += 1
        if correct:
            self.reports_correct += 1
        else:
            self.reports_wrong += 1
        self.save()

    def sight_fault(self, fault_code: str) -> int:
        """
        Count one more sighting of a fault type and return which it was.

        Args:
            fault_code: The condition on the line the player has just read

        Returns:
            1 for the first time this career has seen the condition
        """
        seen = self.fault_sightings.get(fault_code, 0) + 1
        self.fault_sightings[fault_code] = seen
        self.save()
        return seen

    def record_missed(self, count: int = 1) -> None:
        """Record reports that have gone past their commitment."""
        self.missed_commitments += count
        self.save()

    def record_repeat(self) -> None:
        """Record a report that came back after being closed."""
        self.repeat_reports += 1
        self.save()

    def end_shift(self) -> None:
        """Close the shift, banking the index and advancing the count."""
        if self.scored():
            self.index_history.append(round(self.service_index(), 1))
        self.shift += 1
        self.save()

    # -- persistence -----------------------------------------------------

    def load(self) -> None:
        """
        Read the career record, ignoring anything unreadable.

        Each field falls back to its default on its own, so one damaged
        entry costs that entry and not the career. What this version does
        not know - keys a later one wrote, qualifications it has not heard
        of - is held and written back, so playing here never deletes it.
        """
        stored = read_json(self.path)
        if not isinstance(stored, dict):
            return

        self.shift = _whole(stored.get('shift'), 1, 1)
        self.reports_closed = _whole(stored.get('reports_closed'), 0, 0)
        self.reports_correct = _whole(stored.get('reports_correct'), 0, 0)
        self.reports_wrong = _whole(stored.get('reports_wrong'), 0, 0)
        self.repeat_reports = _whole(stored.get('repeat_reports'), 0, 0)
        self.missed_commitments = _whole(
            stored.get('missed_commitments'), 0, 0)

        self.qualifications = [
            key for key in _names(stored.get('qualifications'))
            if key in QUALIFICATIONS_BY_KEY] or ['loop']
        self.finished = stored.get('finished') is True

        for field in _LIST_FIELDS:
            setattr(self, field, _names(stored.get(field)))
        for field in _COUNT_FIELDS:
            setattr(self, field, _counts(stored.get(field)))
        self.practicals_passed = [key for key in self.practicals_passed
                                  if key in QUALIFICATIONS_BY_KEY]
        assignment = stored.get('assignment')
        self.assignment = assignment if isinstance(assignment, str) else ''
        verdict = stored.get('audit_verdict')
        self.audit_verdict = verdict if isinstance(verdict, str) else ''
        self.audit_late = _whole(stored.get('audit_late'), 0, 0)

        office = stored.get('office')
        if isinstance(office, dict):
            self.office = {str(key): str(value)
                           for key, value in office.items()}

        history = stored.get('index_history')
        if isinstance(history, list):
            self.index_history = [
                float(entry) for entry in history
                if isinstance(entry, (int, float))
                and not isinstance(entry, bool) and math.isfinite(entry)
            ][-40:]

        difficulty = stored.get('difficulty')
        if isinstance(difficulty, str) and difficulty in DIFFICULTIES:
            self.difficulty_key = difficulty

        # Held for save(): whatever a later version added.
        self._unknown = {key: value for key, value in stored.items()
                         if key not in _KNOWN_KEYS}
        self._unknown_qualifications = [
            key for key in _names(stored.get('qualifications'))
            if key not in QUALIFICATIONS_BY_KEY]
        self._unknown_practicals = [
            key for key in _names(stored.get('practicals_passed'))
            if key not in QUALIFICATIONS_BY_KEY]
        schema = stored.get('schema')
        if isinstance(schema, int) and not isinstance(schema, bool):
            self._schema_seen = schema

    def save(self) -> None:
        """Write the career record, ignoring a read-only filesystem."""
        if not self.path:
            return
        record = {
            **self._unknown,
            'schema': max(SCHEMA, self._schema_seen),
            'difficulty': self.difficulty_key,
            'shift': self.shift,
            'reports_closed': self.reports_closed,
            'reports_correct': self.reports_correct,
            'reports_wrong': self.reports_wrong,
            'repeat_reports': self.repeat_reports,
            'missed_commitments': self.missed_commitments,
            'qualifications': self.qualifications
                              + self._unknown_qualifications,
            'index_history': self.index_history[-40:],
            'office': self.office,
            'finished': self.finished,
            'assignment': self.assignment,
            'audit_verdict': self.audit_verdict,
            'audit_late': self.audit_late,
            **{field: getattr(self, field)
               for field in _LIST_FIELDS + _COUNT_FIELDS},
        }
        record['practicals_passed'] = (self.practicals_passed
                                       + self._unknown_practicals)
        try:
            write_text_atomically(
                self.path, json.dumps(record, indent=2, sort_keys=True) + '\n')
        except OSError:
            return


def _whole(stored: Any, default: int, floor: int) -> int:
    """Read a saved whole number, or the default if it is anything else."""
    if isinstance(stored, bool):
        return default
    try:
        return max(floor, int(stored))
    except (TypeError, ValueError, OverflowError):
        return default


def _names(stored: Any) -> List[str]:
    """Read a saved list of names: strings only, once each, in order."""
    if not isinstance(stored, list):
        return []
    seen = set()
    names: List[str] = []
    for entry in stored:
        if isinstance(entry, str) and entry not in seen:
            seen.add(entry)
            names.append(entry)
    return names


def _counts(stored: Any) -> Dict[str, int]:
    """Read a saved count for each name: whole numbers, never below zero."""
    if not isinstance(stored, dict):
        return {}
    return {str(name): max(0, value) for name, value in stored.items()
            if isinstance(value, int) and not isinstance(value, bool)}


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
