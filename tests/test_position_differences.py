"""
What is actually different about sitting at one desk rather than another.

Before this, the answer was a home directory and one starting sign-off. The
board was the same twelve ways over, the same people said the same things,
and a planning desk was judged on repair commitments it had no part in.

The rule these tests exist to hold: a desk gets a different MIX of work,
never less of it, and never work whose vocabulary it has not been taught.
"""

import io
import itertools
import random
import statistics
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timedelta

import pytest

from bell_system.constants import BELL_SYSTEM_ROLES
from bell_system.data.man_pages import MAN_PAGES
from bell_system.data.positions import NEUTRAL, POSITIONS, get as get_position
from bell_system.data.trouble import (
    FAULTS,
    NSPMP_WEIGHTS,
    REAL_FAULTS,
)
from bell_system.npc import CRAFT, _CHATTER, _POSITION_CHATTER
from bell_system.reports import MAX_PENDING, OPENING_BACKLOG, ReportDesk
from bell_system.screens.remote import (
    LAMP_MINUTES, LAMPS, WORK_COST, WORK_REMOTE,
)
from bell_system.screens.position import _COUNTERS
from bell_system.special_services import (
    LOOP_REMOTE_MINUTES,
    LOOP_VISIT_MINUTES,
    OUTAGE_WINDOW,
    PLACE_WEIGHTS,
    PLACES,
    WRONG_FORCE_MINUTES,
    SartsInventory,
    fault_place_for,
)
from bell_system.terminal import BellSystemTerminal

SHIFT_START = datetime(1983, 11, 14, 8, 0)


def skew_the_wall_clock(terminal, monkeypatch, hours=9):
    """
    Make the host's clock run hours ahead, as a long lunch would.

    The desks count the shift clock and nothing else, so nothing may move.
    Checks that the skew is real for anything that does read the host (the
    clock module's own datetime), and that the shift's time stood still.
    """
    from bell_system import clock as clock_module

    before = terminal.clock.now()

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now() + timedelta(hours=hours)

    monkeypatch.setattr(clock_module, 'datetime', Later)
    assert clock_module.datetime.now() - datetime.now() >= timedelta(
        hours=hours - 1)
    assert terminal.clock.now() == before


ROLE_KEYS = [key for key, _ in BELL_SYSTEM_ROLES.values()]


# One seed for every desk test. The board and the SARTS inventory take it
# through the terminal; what arrives, interrupts and rings during a command
# comes from the module's own generator, so the module seeds that too (below).
# A test that passes passes every time, and one that depends on luck is a
# failing test to fix, not a flake to rerun.
SEED = 1983


@pytest.fixture(autouse=True)
def _seeded_chance():
    state = random.getstate()
    random.seed(SEED)
    yield
    random.setstate(state)


@pytest.fixture
def at_desk(isolated_state):
    """Return a factory that puts a fully qualified terminal at a desk."""
    from bell_system.progression import QUALIFICATIONS

    def put(role_key):
        instance = BellSystemTerminal(rng=random.Random(SEED))
        instance.settings.set('game.ambience', 'off')
        instance.settings.set('display.pacing', 'off')
        instance.settings.set('game.prompts', 'off')
        instance.career.qualifications = [q.key for q in QUALIFICATIONS]
        # Past the first tour, which holds the board at one report.
        instance.career.shift = 2
        if role_key is not None:
            with redirect_stdout(io.StringIO()):
                instance.take_position(role_key)
        return instance
    return put


class TestTheTable:
    """One record per desk, and every field of it has to mean something."""

    def test_the_table_and_the_roster_agree(self):
        assert set(POSITIONS) == set(ROLE_KEYS)

    def test_every_position_names_itself_consistently(self):
        for key, position in POSITIONS.items():
            assert position.key == key
            name = next(n for k, n in BELL_SYSTEM_ROLES.values() if k == key)
            assert position.name == name

    def test_an_unknown_or_absent_position_is_neutral(self):
        assert get_position(None) is NEUTRAL
        assert get_position('') is NEUTRAL
        assert get_position('nobody') is NEUTRAL

    def test_the_neutral_position_is_todays_behaviour(self):
        """
        Almost the whole suite runs without a role. Every default here has
        to be what the simulation did before positions differed.
        """
        assert NEUTRAL.fault_bias == {}
        assert NEUTRAL.board_share == 0.5
        assert NEUTRAL.ticket_categories == ()
        assert NEUTRAL.nspmp == 'customer_reports'

    def test_every_biased_fault_is_a_real_fault(self):
        for key, position in POSITIONS.items():
            for fault in position.fault_bias:
                assert fault in FAULTS, (key, fault)

    def test_no_bias_is_ever_zero(self):
        """
        A bias and never a filter. A zero would make a desk one that never
        sees a kind of trouble, which is a different game rather than a
        different desk.
        """
        for key, position in POSITIONS.items():
            for fault, weight in position.fault_bias.items():
                assert weight > 0, (key, fault)

    def test_every_board_share_leaves_a_workable_board(self):
        """
        A depth at or below the opening backlog means the desk starts full
        and refuses work for the whole tour. That happened.
        """
        for key, position in POSITIONS.items():
            depth = round(MAX_PENDING - 3 + 6 * position.board_share)
            assert depth > max(OPENING_BACKLOG), (key, depth)

    def test_every_ticket_category_is_a_real_one(self, terminal):
        for key, position in POSITIONS.items():
            for category in position.ticket_categories:
                assert category in terminal.ticket_categories, (key, category)

    def test_every_voice_is_somebody_on_the_machine(self):
        for key, position in POSITIONS.items():
            for login in position.voices:
                assert login in CRAFT, (key, login)

    def test_every_nspmp_component_is_a_real_one(self):
        for key, position in POSITIONS.items():
            if position.nspmp is not None:
                assert position.nspmp in NSPMP_WEIGHTS, (key, position.nspmp)

    def test_every_tally_key_resolves_to_a_counter(self):
        for key, position in POSITIONS.items():
            for name in position.tally:
                assert name in _COUNTERS, (key, name)

    def test_every_counter_is_used_by_somebody(self):
        """A counter nothing reads is dead code."""
        used = {name for position in POSITIONS.values()
                for name in position.tally}
        assert set(_COUNTERS) == used


class TestTheFaultMix:
    """A different mix of trouble, never a narrower vocabulary."""

    def mix(self, bias, draws=6000):
        """Draw a lot of faults with a given bias and count them."""
        desk = ReportDesk('201', '555', 'X', random.Random(5))
        desk.fault_bias = dict(bias)
        return Counter(desk._choose_fault() for _ in range(draws))

    def test_no_bias_is_the_flat_draw_it_always_was(self):
        counts = self.mix({})
        share = [counts[fault] / 6000 for fault in REAL_FAULTS]
        assert max(share) - min(share) < 0.03

    def test_a_bias_makes_its_fault_commoner(self):
        plain = self.mix({})
        biased = self.mix({'FCG': 3.0})
        assert biased['FCG'] > plain['FCG'] * 1.5

    @pytest.mark.parametrize('role,fault', [
        ('switch', 'FCG'), ('switch', 'CO_EQUIP'),
        ('field', 'WET'), ('dba', 'CO_EQUIP'),
    ])
    def test_each_desk_sees_more_of_its_own(self, role, fault):
        plain = self.mix({})
        biased = self.mix(POSITIONS[role].fault_bias)
        assert biased[fault] > plain[fault]

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_every_fault_stays_reachable_at_every_desk(self, role):
        """
        The rule the whole design rests on. A desk that could never see wet
        cable would be a desk playing a different game.
        """
        counts = self.mix(POSITIONS[role].fault_bias)
        for fault in REAL_FAULTS:
            assert counts[fault] > 0, (role, fault)
        assert counts['NONE'] > 0 and counts['ROH'] > 0

    def test_the_no_trouble_share_stays_sane_however_biased(self):
        counts = self.mix({'NONE': 99.0, 'ROH': 99.0})
        assert counts['NONE'] / 6000 <= 0.46
        assert sum(counts[f] for f in REAL_FAULTS) > 0


class TestNobodyGetsLessWork:
    """
    The failure this design had to be measured into avoiding, twice.

    Scaling the report arrival rate made board-heavy desks carry a third
    less total work, because the board is saturated and the rate does
    nothing. Making depth the lever then starved a planning desk of reports
    entirely. What is here is one gentle lever.
    """

    def arrivals(self, at_desk, role, commands=250, trials=4):
        """Reports and tickets that arrive over a run of commands."""
        totals = []
        for seed in range(trials):
            random.seed(7000 + seed)
            terminal = at_desk(role)
            terminal.settings.set('game.ambience', 'on')
            before = (len(terminal.desk.reports),
                      len(terminal._assigned_tickets))
            for _ in range(commands):
                terminal.execute_command('pwd')
            totals.append((len(terminal.desk.reports) - before[0],
                           len(terminal._assigned_tickets) - before[1]))
        return (statistics.fmean(r for r, _ in totals),
                statistics.fmean(t for _, t in totals))

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_every_desk_gets_reports(self, at_desk, role):
        reports, _ = self.arrivals(at_desk, role)
        assert reports >= 1.0, f'{role} board barely moves'

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_every_desk_gets_tickets(self, at_desk, role, monkeypatch):
        """
        A desk is handed a ticket when the draw comes up, which it can.

        The rate is small enough that counting arrivals over a few hundred
        commands is a measurement of the random stream. This holds the
        draw at its lowest instead: the first command after the first tour
        must assign one, whichever desk it is.
        """
        terminal = at_desk(role)
        terminal.settings.set('game.ambience', 'on')
        before = len(terminal._assigned_tickets)
        monkeypatch.setattr(random, 'random', lambda: 0.0)
        terminal.execute_command('pwd')
        assert len(terminal._assigned_tickets) > before, (
            f'{role} hears nothing from the control centre')

    def test_the_report_rate_is_not_scaled_at_all(self):
        """
        Measuring showed the board runs saturated, so the arrival rate
        changes nothing and scaling it only ever removed tickets. The knob
        is gone rather than left in looking useful.
        """
        from bell_system.screens import position as module
        assert not hasattr(module.PositionCommands, 'report_rate')

    def test_a_board_heavy_desk_carries_a_deeper_board(self, at_desk):
        light = at_desk('netplan').desk.depth_limit
        heavy = at_desk('custserv').desk.depth_limit
        assert heavy > light

    def test_no_desk_starts_full(self, at_desk):
        for role in ROLE_KEYS:
            terminal = at_desk(role)
            assert not terminal.desk.full(), role


class TestTicketsArePreferredNotFiltered:
    """A desk with nothing of its own waiting takes what there is."""

    def test_its_own_kind_comes_first(self, at_desk):
        terminal = at_desk('radio')
        pool = [{'category': 'MAINTENANCE', 'id': 'a'},
                {'category': 'EQUIPMENT_FAILURE', 'id': 'b'}]
        assert [t['id'] for t in terminal.prefer_tickets(pool)] == ['b']

    def test_nothing_of_its_own_means_it_takes_what_there_is(self, at_desk):
        terminal = at_desk('radio')
        pool = [{'category': 'MAINTENANCE', 'id': 'a'}]
        assert terminal.prefer_tickets(pool) == pool

    def test_a_desk_with_no_preference_takes_everything(self, at_desk):
        terminal = at_desk(None)
        pool = [{'category': 'MAINTENANCE', 'id': 'a'}]
        assert terminal.prefer_tickets(pool) == pool


class TestWhoTalksToYou:
    """Its own people on top of the whole building, never instead of it."""

    def test_every_desk_has_its_own_lines(self):
        assert set(_POSITION_CHATTER) == set(ROLE_KEYS)
        for key, pool in _POSITION_CHATTER.items():
            assert len(pool) >= 3, key

    def test_every_line_comes_from_somebody_on_the_machine(self):
        for key, pool in _POSITION_CHATTER.items():
            for _, sender, *_ in pool:
                assert sender in CRAFT, (key, sender)

    def test_a_desk_still_hears_the_whole_building(self, terminal):
        """
        Added and never replacing. A document preparation desk still gets
        CAROT printing trunk exceptions, because the teletype does not care
        who is sitting there.
        """
        room = terminal.switchroom
        heard = set()
        for _ in range(80):
            message = room.chatter(terminal.clock.now(), position='docprep')
            if message:
                heard.add(message.subject)
        shared = {item[2][0][:40] for item in _CHATTER}
        assert shared & heard, 'the shared pool went missing'

    def test_a_desk_hears_things_no_other_desk_does(self, terminal):
        room = terminal.switchroom

        def heard(position):
            seen = set()
            for _ in range(80):
                message = room.chatter(terminal.clock.now(),
                                       position=position)
                if message:
                    seen.add(message.subject)
            return seen

        assert heard('tsps') - heard(None)
        assert heard('radio') - heard(None)

    def test_the_chief_operator_talks_to_the_operator_position(self):
        senders = {sender for _, sender, _ in _POSITION_CHATTER['tsps']}
        assert 'jhaverty' in senders

    def test_no_position_lines_are_identical_to_another_desks(self):
        seen = {}
        for key, pool in _POSITION_CHATTER.items():
            for _, _, lines in pool:
                assert lines[0] not in seen, (key, seen.get(lines[0]))
                seen[lines[0]] = key


class TestTheRosterIsComplete:
    """Everybody who can be dispatched or can ring you has a voice."""

    def test_every_dispatchable_crew_is_on_the_roster(self):
        from bell_system.field import CREWS
        names = {person.name for person in CRAFT.values()}
        for crew in CREWS:
            assert crew.name in names, crew.name

    def test_every_dispatch_force_is_answered_by_the_right_trade(self):
        from bell_system.npc import Switchroom
        senders = Switchroom.FORCE_SENDERS
        assert CRAFT[senders['Station']].title == 'Station Installer'
        assert CRAFT[senders['Cable repair']].title == 'Cable Splicer'

    def test_a_field_call_names_who_actually_went(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        terminal.desk.dispatch(report, 'Outside plant', terminal.shift_minutes)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), report.number, 'cleared',
            force='Outside plant', crew=report.crew)
        assert CRAFT[message.sender].name == report.crew

    def test_every_craft_login_has_a_password_file_entry(self, terminal):
        passwd = terminal.execute_command('cat /etc/passwd')
        for login in CRAFT:
            if login == 'carot':
                continue  # A system, not an account.
            assert f'{login}:' in passwd, login


class TestTheMeasure:
    """What a desk is judged on, and what it is honestly not."""

    def test_a_desk_the_plan_covers_says_which_component(self, at_desk):
        note = '\n'.join(at_desk('custserv').position_measure())
        assert 'customer reports' in note

    def test_a_desk_the_plan_does_not_cover_says_so(self, at_desk):
        note = '\n'.join(at_desk('netplan').position_measure())
        assert 'No component' in note
        assert 'carried for the record' in note

    def test_most_desks_are_outside_the_plan(self):
        """
        The honest finding, and worth holding: NSPMP measures a switching
        machine. Forcing a component onto a planning desk would be the
        invention this project exists not to make.
        """
        outside = [key for key, p in POSITIONS.items() if p.nspmp is None]
        assert len(outside) >= 7

    def test_the_component_is_still_the_default_everywhere_else(self, tmp_path):
        from bell_system.progression import Career
        career = Career(str(tmp_path / 'c.json'))
        career.reports_closed = 10
        career.reports_correct = 10
        assert career.office_contribution() == career.office_contribution(
            'customer_reports')

    def test_an_unknown_component_falls_back_rather_than_raising(self, tmp_path):
        from bell_system.progression import Career
        career = Career(str(tmp_path / 'c.json'))
        career.reports_closed = 4
        career.reports_correct = 4
        assert career.office_contribution('nonsense') > 0

    def test_the_index_itself_is_unchanged(self, tmp_path):
        """No second score. The index is the index."""
        from bell_system.progression import Career
        career = Career(str(tmp_path / 'c.json'))
        career.reports_closed = 20
        career.reports_wrong = 4
        before = career.service_index()
        career.position = POSITIONS['netplan']
        assert career.service_index() == before


class TestTheTourAccount:
    """A tally beside the index, and never a second score."""

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_every_desk_can_account_for_its_tour(self, at_desk, role):
        rows = at_desk(role).position_tally()
        assert rows
        for label, value in rows:
            assert label and isinstance(value, str)

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_the_handoff_renders_at_every_desk(self, at_desk, role):
        output = at_desk(role).execute_command('handoff')
        assert 'WHAT THIS DESK DID' in output
        assert 'Command execution error' not in output

    @pytest.mark.parametrize('role', ROLE_KEYS)
    def test_the_handoff_fits_the_terminal(self, at_desk, role):
        output = at_desk(role).execute_command('handoff')
        assert max(len(line) for line in output.split('\n')) <= 74, role

    def test_it_says_it_is_not_scored(self, at_desk):
        assert 'Not scored' in at_desk('field').execute_command('handoff')

    def test_a_session_with_no_position_prints_no_tally(self, at_desk):
        assert 'WHAT THIS DESK DID' not in at_desk(None).execute_command(
            'handoff')

    def test_the_tally_reads_real_state(self, at_desk):
        terminal = at_desk('field')
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        terminal.desk.dispatch(report, 'Outside plant', terminal.shift_minutes)
        rows = dict(terminal.position_tally())
        assert rows['crews dispatched'] == '1'


class TestNothingChangedForASessionWithNoPosition:
    """
    Almost the whole suite runs role-less. Every default has to be what the
    simulation did before this table existed.
    """

    def test_the_desk_takes_no_bias(self, at_desk):
        assert at_desk(None).desk.fault_bias == {}

    def test_the_board_is_the_depth_it_always_was(self, at_desk):
        assert at_desk(None).desk.depth_limit == MAX_PENDING

    def test_taking_a_position_does_not_re_deal_the_board(self, at_desk):
        """
        You inherit the last tour's board. What arrives on yours is yours.
        """
        terminal = at_desk(None)
        before = [report.number for report in terminal.desk.pending()]
        with redirect_stdout(io.StringIO()):
            terminal.take_position('custserv')
        after = [report.number for report in terminal.desk.pending()]
        assert after == before


# The desks that play differently. The other eight are unchanged, and
# TestTheFourDesks holds that. Each desk gets a PR; the set grows with them.
FOUR_DESKS = ('noc', 'sarts', 'custserv', 'switch')


class TestTheFourDesks:
    """One command only the desk has, and one pressure only it feels."""

    def test_only_these_desks_have_a_verb_or_a_pressure(self):
        for key, position in POSITIONS.items():
            has = bool(position.verb or position.pressure)
            assert has == (key in FOUR_DESKS), key

    def test_a_verb_and_a_pressure_come_together(self):
        for key in FOUR_DESKS:
            assert POSITIONS[key].verb and POSITIONS[key].pressure, key

    def test_a_desk_outside_the_four_is_otherwise_untouched(self):
        """No relabel and no new bias: it keeps what it had."""
        for key, position in POSITIONS.items():
            if key not in FOUR_DESKS:
                assert position.verb == '' and position.pressure == ''


def put_tickets(terminal, *specs):
    """Replace the ticket pool with tickets of a given class and size."""
    random.seed(11)
    terminal.active_tickets.clear()
    made = []
    for priority, customers in specs:
        ticket = terminal._create_realistic_ticket()
        ticket['priority'] = priority
        ticket['customer_impact'] = customers
        ticket['status'] = 'OPEN'
        ticket['escalation_level'] = 1
        made.append(ticket)
    terminal.shift_minutes = 0
    for ticket in made:
        terminal.triage_stamp(ticket, 0)
    return made


def resume_onto_fresh(terminal, role=None, mutate=None, dealt=None):
    """
    Resume a saved shift the way the game does.

    A new session is built, the saved shift is restored onto it with no desk
    taken, and only then does the player choose a role (terminal.py makes
    the session first and `_resume_shift` runs before anybody has sat down).
    A helper that took the desk first would test an order nobody can reach.

    ``mutate`` is handed what was written, to damage or age it; ``dealt``
    is handed the new session before the restore, to say what it was dealt.
    """
    import json
    from bell_system import save
    captured = json.loads(json.dumps(save.capture(terminal)))
    if mutate is not None:
        mutate(captured)
    fresh = BellSystemTerminal(rng=random.Random(SEED))
    fresh.career.shift = terminal.career.shift
    fresh.career.reports_closed = terminal.career.reports_closed
    if dealt is not None:
        dealt(fresh)
    assert save.restore(fresh, captured)
    if role is not None:
        with redirect_stdout(io.StringIO()):
            fresh.take_position(role)
    return fresh


class TestTheNocQueue:
    """
    The triage verb and the clock behind it.

    The pressure is the shift clock and nothing else: it moves on what is
    typed and what is run, never on how fast anybody types.
    """

    def test_the_verb_is_the_nocs_alone(self, at_desk):
        for role in ROLE_KEYS:
            if role == 'noc':
                continue
            output = at_desk(role).execute_command('trouble triage')
            assert 'not at this position' in output, role
            assert 'National NOC Analyst' in output, role

    def test_a_session_with_no_desk_is_refused_too(self, at_desk):
        assert 'not at this position' in at_desk(None).execute_command(
            'trouble triage')

    def test_a_refused_verb_changes_nothing(self, at_desk):
        terminal = at_desk('field')
        made = put_tickets(terminal, ('CRITICAL', 900))
        terminal.execute_command('trouble triage ' + made[0]['id'])
        assert made[0]['status'] == 'OPEN'
        assert made[0]['id'] not in terminal._assigned_tickets

    def test_the_queue_leads_with_the_soonest_window(self, at_desk):
        terminal = at_desk('noc')
        minor, critical, major = put_tickets(
            terminal, ('MINOR', 50), ('CRITICAL', 10), ('MAJOR', 700))
        queue = [t['id'] for t in terminal.triage_queue()]
        assert queue == [critical['id'], major['id'], minor['id']]

    def test_the_same_window_goes_to_the_bigger_outage_first(self, at_desk):
        terminal = at_desk('noc')
        small, big = put_tickets(terminal, ('MAJOR', 40), ('MAJOR', 4000))
        assert [t['id'] for t in terminal.triage_queue()] == [
            big['id'], small['id']]

    def test_the_queue_prints_its_rule_and_says_it_is_the_sims_own(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 40))
        output = terminal.execute_command('trouble triage')
        assert 'CRITICAL 15' in output and "simulation's own" in output
        assert max(len(line) for line in output.split('\n')) <= 78

    def test_taking_a_ticket_costs_the_shift_its_call(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 40))
        before = terminal.shift_minutes
        output = terminal.execute_command('trouble triage ' + major['id'])
        assert terminal.shift_minutes - before >= 4
        assert major['status'] == 'IN_PROGRESS'
        assert 'in time' in output
        assert major['id'] in terminal._assigned_tickets
        assert major['id'] not in [t['id'] for t in terminal.triage_queue()]

    def test_a_window_closes_on_the_shift_clock(self, at_desk):
        terminal = at_desk('noc')
        (critical,) = put_tickets(terminal, ('CRITICAL', 900))
        terminal.shift_minutes = 15
        terminal.triage_sweep()
        assert critical['escalation_level'] == 1
        terminal.shift_minutes = 16
        terminal.triage_sweep()
        assert critical['escalation_level'] == 2
        assert 'nobody on it' in critical['resolution_steps'][-1]

    def test_a_missed_window_escalates_once(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 200
        for _ in range(3):
            terminal.triage_sweep()
        assert major['escalation_level'] == 2

    def test_taking_late_says_so_and_counts(self, at_desk):
        terminal = at_desk('noc')
        (minor,) = put_tickets(terminal, ('MINOR', 10))
        base = terminal.career.open_overdue()
        terminal.shift_minutes = 75
        output = terminal.execute_command('trouble triage ' + minor['id'])
        assert 'after the window closed' in output
        assert len(terminal.triage_book()['lapsed']) == 1
        assert terminal.career.open_overdue() == base + 1

    def test_the_first_tour_is_a_grace(self, at_desk):
        terminal = at_desk('noc')
        terminal.career.shift = 1
        (critical,) = put_tickets(terminal, ('CRITICAL', 900))
        terminal.shift_minutes = 400
        terminal.triage_sweep()
        assert critical['escalation_level'] == 1
        assert terminal.triage_lapsed() == 0

    def test_the_clock_is_the_shift_clock_and_not_the_wall_clock(
            self, at_desk, monkeypatch):
        """Anti-pillar: no outcome turns on how fast anybody types."""
        terminal = at_desk('noc')
        (critical,) = put_tickets(terminal, ('CRITICAL', 900))
        due = terminal.triage_due(critical)
        skew_the_wall_clock(terminal, monkeypatch)
        terminal.triage_sweep()
        assert terminal.triage_due(critical) == due
        assert critical['escalation_level'] == 1

    def test_a_ticket_entered_mid_tour_gets_a_full_window(self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal)
        terminal.shift_minutes = 100
        terminal.execute_command('trouble create MAINTENANCE CRITICAL Test')
        (entered,) = terminal.active_tickets
        assert terminal.triage_due(entered) == 115

    def test_the_tally_counts_what_ran_past(self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('CRITICAL', 900), ('MINOR', 5))
        terminal.shift_minutes = 20
        rows = dict(terminal.position_tally())
        assert rows['tickets past their response window'] == '1'
        assert 'WHAT THIS DESK DID' in terminal.execute_command('handoff')

    def test_counting_changes_nothing(self, at_desk):
        """The tally reads; only the queue and a take notice a window."""
        terminal = at_desk('noc')
        (critical,) = put_tickets(terminal, ('CRITICAL', 900))
        terminal.shift_minutes = 90
        for _ in range(2):
            terminal.position_tally()
            terminal.triage_lapsed()
            terminal.triage_queue()
        assert critical['escalation_level'] == 1
        assert terminal.triage_book()['lapsed'] == {}
        assert critical['resolution_steps'] == []

    def test_resolve_still_works_on_a_ticket_you_took(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 40))
        terminal.execute_command('trouble triage ' + major['id'])
        output = terminal.execute_command('trouble resolve ' + major['id'])
        assert 'Trouble Ticket Resolved' in output


def failing_circuit(terminal, place='FACILITY', access='SMAS', read=True):
    """
    Make one circuit the only one failing, at a known place, and return it.

    Read by default, so that a force can be sent to it; a test of the gate
    asks for it unread.
    """
    inventory = terminal.special_services
    for other in inventory.circuits.values():
        other.status, other.impaired, other.fault_place = 'IS', False, None
    circuit = next(iter(inventory.circuits.values()))
    circuit.impaired = True
    circuit.access = access
    circuit.status = 'TRBL'
    circuit.fault_place = place
    circuit.out_minutes = 0
    terminal.shift_minutes = 0
    inventory.settle(terminal.career.shift, 0)
    inventory._read.clear()
    if read:
        inventory.mark_read(circuit.circuit_id)
    return circuit


class TestTheSartsRepair:
    """
    A repair verb for a failing circuit, and an outage clock behind it.

    Reading is what pays: the loops say where, and a guess costs a trip and
    the minutes the customer sits out.
    """

    def test_the_verb_is_the_sarts_desks_alone(self, at_desk):
        for role in ROLE_KEYS:
            if role == 'sarts':
                continue
            output = at_desk(role).execute_command('sarts repair 1')
            assert 'not at this position' in output, role
            assert 'SARTS' in output, role

    def test_the_field_desk_still_reads_the_inventory(self, at_desk):
        """It shares the sarts command; only the repair verb is refused."""
        output = at_desk('field').execute_command('sarts trouble')
        assert 'not at this position' not in output

    def test_every_impaired_circuit_has_a_place_and_no_other_does(
            self, terminal):
        for circuit in terminal.special_services.circuits.values():
            if circuit.impaired:
                assert circuit.fault_place in PLACES, circuit.circuit_id
            else:
                assert circuit.fault_place is None, circuit.circuit_id

    def test_a_place_does_not_move_the_rest_of_the_inventory(self):
        """The place has its own generator, so no later draw shifted."""
        from bell_system.special_services import SartsInventory
        inventory = SartsInventory('NWRKNJ01', random.Random(3))
        circuits = list(inventory.circuits.values())
        # Pinned: if a draw moves, the place has leaked into the inventory.
        assert [c.circuit_id for c in circuits[:6]] == [
            '0001-PBX-718', '0002-PBX-581', '0003-PBX-499', '0004-PBX-375',
            '0005-PL-237', '0006-WATS-897']
        assert [c.access for c in circuits[:6]] == [
            'SMAS', 'SMAS', 'SMAS', 'DACS', 'SMAS', 'SMAS']
        assert {c.circuit_id: c.fault_place for c in circuits
                if c.impaired} == {'0012-PBX-517': 'FACILITY',
                                   '0021-PL-441': 'FACILITY',
                                   '0024-CTX-912': 'FACILITY'}

    def test_the_loops_bracket_the_trouble(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'FACILITY')
        output = terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        verdicts = [line.split()[-1] for line in output.split('\n')
                    if line.startswith('  Loop at')]
        assert verdicts == ['PASS', 'FAIL', 'FAIL']

    @pytest.mark.parametrize('place,expected', [
        ('OFFICE', ['FAIL', 'FAIL', 'FAIL']),
        ('FACILITY', ['PASS', 'FAIL', 'FAIL']),
        ('PREMISES', ['PASS', 'PASS', 'FAIL']),
    ])
    def test_each_place_reads_differently(self, at_desk, place, expected):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, place)
        output = terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        assert [line.split()[-1] for line in output.split('\n')
                if line.startswith('  Loop at')] == expected

    def test_reading_the_loops_always_finds_the_place(self, at_desk):
        """The invariant a guessing bot cannot meet: read, then send."""
        terminal = at_desk('sarts')
        for circuit in terminal.special_services.circuits.values():
            circuit.impaired = True
            circuit.status = 'TRBL'
            circuit.fault_place = random.Random(circuit.circuit_id).choice(
                list(PLACES))
        for circuit in list(terminal.special_services.circuits.values()):
            truth = circuit.fault_place
            output = terminal.execute_command(
                f'sarts repair {circuit.circuit_id}')
            verdicts = [line.split()[-1] for line in output.split('\n')
                        if line.startswith('  Loop at')]
            place = list(PLACES)[verdicts.index('FAIL')]
            assert place == truth
            terminal.execute_command(
                f'sarts repair {circuit.circuit_id} {place.lower()}')
            assert circuit.status == 'IS' and circuit.fault_place is None

    def test_the_right_force_clears_it(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'PREMISES')
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} premises')
        assert 'back in service' in output
        assert circuit.status == 'IS' and not circuit.impaired

    def test_the_wrong_force_finds_nothing_and_costs_the_trip(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        before = terminal.shift_minutes
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} facility')
        assert 'found nothing' in output
        assert circuit.status == 'TRBL' and circuit.fault_place == 'OFFICE'
        assert terminal.shift_minutes - before >= (
            PLACES['FACILITY'][1] + WRONG_FORCE_MINUTES)
        assert circuit.out_minutes >= (
            PLACES['FACILITY'][1] + WRONG_FORCE_MINUTES)

    def test_a_relay_loop_is_cheap_and_a_jack_needs_a_visit(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, access='SMAS')
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        by_relay = terminal.shift_minutes
        circuit = failing_circuit(terminal, access='JACK')
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        by_visit = terminal.shift_minutes
        assert by_visit > by_relay
        assert by_visit >= LOOP_VISIT_MINUTES
        assert LOOP_REMOTE_MINUTES <= by_relay < LOOP_VISIT_MINUTES

    def test_a_circuit_that_has_not_failed_is_sent_back_to_the_test(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        circuit.status = 'IS'
        circuit.impaired = False
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id}')
        assert 'not held in trouble' in output
        assert f'sarts test {circuit.circuit_id}' in output

    def test_a_place_that_is_not_one_is_refused_without_a_trip(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        before = terminal.shift_minutes
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} moon')
        assert 'not a place' in output
        assert terminal.shift_minutes - before <= 1

    def test_a_failed_test_points_at_the_verb(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        circuit.status = 'IS'
        output = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert f'sarts repair {circuit.circuit_id}' in output


class TestTheOutageClock:
    """The pressure: a circuit in trouble is out for as long as it stays."""

    def test_a_circuit_in_trouble_accrues_shift_minutes(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        terminal.shift_minutes = 30
        assert out_now(terminal, circuit) >= 30
        assert ' 30m' in terminal.execute_command('sarts trouble')
        # A look is not a charge; the next thing that spends time makes it.
        assert circuit.out_minutes == 0
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        assert circuit.out_minutes >= 30

    def test_a_circuit_in_service_accrues_nothing(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        healthy = [c for c in terminal.special_services.circuits.values()
                   if c.status == 'IS']
        terminal.shift_minutes = 90
        terminal.execute_command('sarts trouble')
        assert all(c.out_minutes == 0 for c in healthy)

    def test_a_repaired_circuit_stops_the_clock(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        stopped = circuit.out_minutes
        terminal.shift_minutes += 200
        terminal.execute_command('sarts trouble')
        assert circuit.out_minutes == stopped

    def test_a_circuit_the_test_finds_is_not_charged_for_before(
            self, at_desk):
        """Out from when it is found, not from the start of the tour."""
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        circuit.status = 'IS'
        circuit.out_minutes = 0
        terminal.shift_minutes = 120
        terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert circuit.out_minutes == 0

    def test_it_is_the_shift_clock_and_not_the_wall_clock(self, at_desk, monkeypatch):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        skew_the_wall_clock(terminal, monkeypatch)
        terminal.execute_command('sarts trouble')
        assert out_now(terminal, circuit) <= 2

    def test_a_new_tour_starts_the_count_again(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        terminal.shift_minutes = 50
        assert out_now(terminal, circuit) >= 50
        terminal.career.shift += 1
        terminal.shift_minutes = 5
        assert 5 <= out_now(terminal, circuit) < 50
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        assert 5 <= circuit.out_minutes < 50

    def test_the_tally_counts_the_minutes(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 40
        rows = dict(terminal.position_tally())
        assert int(rows['circuit-minutes out of service']) >= 40

    def test_the_board_fits_the_terminal(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        output = terminal.execute_command('sarts trouble')
        assert max(len(line) for line in output.split('\n')) <= 74


def hold(terminal, *waits):
    """
    Put customers on hold with known waits, and return their reports.

    Each wait is (out of service, shift minutes already waited). The
    reports are the board's own; only their fault, elapsed time and what
    has been learned about them are set, and the book starts empty.
    """
    while len(terminal.desk.customers()) < len(waits):
        terminal.desk.receive(terminal.clock.now())
    reports = terminal.desk.customers()
    for report in terminal.desk.pending():
        if report not in reports[:len(waits)]:
            report.status = 'CLOSED'
    chosen = reports[:len(waits)]
    for report, (out, waited) in zip(chosen, waits):
        report.record.fault = 'OPEN' if out else 'NONE'
        report.minutes_spent = waited
        report.tested = False
        report.found = None
        report.field_finding = None
        report.dispatched_to = None
        report.crew = None
        report.test_notes = []
    from bell_system.screens.repairdesk import _new_book
    terminal._patience_book = _new_book(terminal.career.shift)
    return chosen


def ring_messages(terminal):
    """The attendant's ring notices on the log."""
    return [m for m in terminal.switchroom.log if m.kind == 'ring']


class TestTheRepairDeskHolds:
    """
    The repair desk's customers ring again, and advise is the answer.

    Reading pays: a report with a finding or a crew out gives the desk
    something to say, and a call with nothing to say costs more and settles
    less.
    """

    def test_the_verb_is_the_repair_desks_alone(self, at_desk):
        for role in ROLE_KEYS:
            if role == 'custserv':
                continue
            output = at_desk(role).execute_command('trouble advise')
            assert 'not at this position' in output, role
            assert 'Customer Service Interface' in output, role

    def test_the_other_trouble_verbs_are_not_taken_from_anyone(self, at_desk):
        # Pinned: only advise is the repair desk's. The rest of the verb
        # stays open at every desk, this one included.
        for role in ('noc', 'custserv'):
            output = at_desk(role).execute_command('trouble list')
            assert 'not at this position' not in output, role

    def test_a_line_out_of_service_rings_sooner(self, at_desk):
        terminal = at_desk('custserv')
        down, noisy = hold(terminal, (True, 20), (False, 20))
        assert terminal.patience(down)[0] == 1
        assert terminal.patience(noisy)[0] == 0
        noisy.minutes_spent = 45
        assert terminal.patience(noisy)[0] == 1

    def test_rings_are_counted_from_the_last_call_and_stop_at_three(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 10_000))
        assert terminal.patience(down)[0] == 3
        terminal.patience_book()['told'][down.number] = 10_000 - 20
        assert terminal.patience(down)[0] == 1

    def test_the_queue_is_most_rings_first(self, at_desk):
        terminal = at_desk('custserv')
        calm, angry, middling = hold(
            terminal, (False, 5), (True, 70), (True, 25))
        order = [row[0] for row in terminal.patience_queue()]
        assert order == [angry, middling, calm]

    def test_a_call_with_something_to_tell_costs_the_base_and_the_rings(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 45))  # Two rings.
        down.field_finding = 'OPEN'
        before = terminal.shift_minutes
        output = terminal.execute_command(f'trouble advise {down.number}')
        assert 'it has been found: OPEN.' in output
        spent = terminal.shift_minutes - before
        assert spent >= 3 + 2 * 2
        assert terminal.patience(down)[0] == 0

    def test_a_call_with_nothing_to_tell_costs_more_and_settles_half(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 30))
        before = terminal.shift_minutes
        output = terminal.execute_command(f'trouble advise {down.number}')
        assert 'nothing to tell' in output
        assert 'report next' in output
        assert terminal.shift_minutes - before >= 3 + 2 * 1 + 3
        # Thirty minutes and the eight-minute call: half of 38 is still owed.
        assert terminal.patience_book()['told'][down.number] == 38 - 19

    def test_a_crew_on_the_job_is_something_to_tell(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 20))
        # A crew out on the right force is one that has a finding.
        down.dispatched_to = 'splicer'
        down.field_finding = 'OPEN'
        down.crew = 'Wheeler'
        output = terminal.execute_command(f'trouble advise {down.number}')
        assert 'Wheeler is on it' in output
        # One ring, so the call was 3 + 2 minutes, and they are told from
        # the end of it.
        assert terminal.patience_book()['told'][down.number] == 20 + 5

    def test_a_number_that_is_not_holding_costs_nothing(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 20))
        before = terminal.shift_minutes
        output = terminal.execute_command('trouble advise TR-99999')
        assert 'no customer holding' in output
        assert terminal.shift_minutes - before <= 1

    def test_a_customer_is_found_by_the_number_they_rang_from(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 20))
        telephone = down.record.telephone_number
        output = terminal.execute_command(f'trouble advise {telephone}')
        assert f'{down.number}: rang {telephone}' in output

    def test_it_is_the_shift_clock_and_not_the_wall_clock(
            self, at_desk, monkeypatch):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 5))
        skew_the_wall_clock(terminal, monkeypatch)
        assert terminal.patience(down)[0] == 0
        terminal._advance_shift()
        assert ring_messages(terminal) == []
        assert terminal.rings_total() == 0

    def test_a_passing_shift_is_what_brings_the_ring(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        assert terminal.patience(down)[0] == 0
        terminal._pass_time(25)
        assert terminal.patience(down)[0] == 1

    def test_the_first_tour_is_a_grace(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 500))
        terminal.career.shift = 1
        terminal.career.reports_closed = 0
        assert terminal.patience(down)[0] == 0
        assert terminal.ring_sweep() == []
        assert terminal.career.missed_commitments == 0

    def test_the_grace_is_the_whole_first_tour_not_only_until_a_close(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 500))
        terminal.career.shift = 1
        terminal.career.reports_closed = 1  # first_tour() has ended.
        assert not terminal.first_tour()
        assert terminal.patience(down)[0] == 0
        assert terminal.ring_sweep() == []
        assert terminal.career.missed_commitments == 0
        terminal.career.shift = 2
        assert terminal.patience(down)[0] == 3

    def test_the_tally_keeps_a_ring_when_the_report_closes(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 45))
        terminal.execute_command('trouble list')  # The clock moves; they ring.
        rows = dict(terminal.position_tally())
        assert rows['customer ringbacks'] == '2'
        down.status = 'CLOSED'
        rows = dict(terminal.position_tally())
        assert rows['customer ringbacks'] == '2'

    def test_the_board_fits_the_terminal(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 45), (False, 10))
        output = terminal.execute_command('trouble advise')
        assert max(len(line) for line in output.split('\n')) <= 74


def office_desk(at_desk, tour=None):
    """
    The office desk with four known alarms standing at home.

    The tour's deal is seeded but not one a test can name, so the home
    office's list is replaced with one it can. A test that changes the
    tour afterwards gets that tour's own deal, not these.
    """
    terminal = at_desk('switch')
    if tour is not None:
        terminal.career.shift = tour
        terminal.deal_alarms()
    terminal.active_alarms[:] = [
        {'id': f'AL-70{index}', 'type': 'TEST', 'severity': severity,
         'system': f'SYS-{index}', 'description': 'A standing alarm',
         'acknowledged': False, 'timestamp': terminal.clock.now()}
        for index, severity in enumerate(
            ('MINOR', 'MINOR', 'MAJOR', 'CRITICAL'))]
    for severity in ('CRITICAL', 'MAJOR', 'MINOR'):
        terminal.system_health[f'{severity.lower()}_alarms'] = sum(
            1 for a in terminal.active_alarms if a['severity'] == severity)
    return terminal


def symptom_desk(at_desk, *kinds):
    """The office desk with one standing alarm of each type named, at home."""
    from bell_system.screens.remote import ALARM_CANDIDATES
    systems = {'TRUNK_DEGRADED': 'TG-004', 'CARRIER_LOSS': 'T1-PENTAGON',
               'RADIO_FADE': 'TH3-CHI-007', 'MEMORY_PARITY': '3A-CCU-D',
               'POWER_SUPPLY': 'PWR-NYC-002'}
    terminal = at_desk('switch')
    terminal.active_alarms[:] = [
        dict(next(c for c in ALARM_CANDIDATES if c['type'] == kind),
             id=f'AL-71{index}', system=systems[kind], acknowledged=False,
             timestamp=terminal.clock.now())
        for index, kind in enumerate(kinds)]
    terminal._recount_health()
    return terminal


def ids(terminal):
    return [alarm['id'] for alarm in terminal.active_alarms]


class TestTheOfficeAlarmPanel:
    """
    Alarm lamps rise on the shift clock, and connect work clears them.

    Reading pays: the panel says which lamp is about to rise and what each
    costs, and the order you clear them in is the whole of the decision.
    """

    def test_the_verb_is_the_office_desks_alone(self, at_desk):
        for role in ROLE_KEYS:
            if role == 'switch':
                continue
            output = at_desk(role).execute_command('connect work')
            assert 'not at this position' in output, role
            assert 'Switching Station' in output, role

    def test_the_other_connect_verbs_are_not_taken_from_anyone(
            self, at_desk):
        output = at_desk('noc').execute_command('connect')
        assert 'not at this position' not in output

    def test_a_lamp_is_deterministic_and_never_below_its_class(
            self, at_desk):
        terminal = office_desk(at_desk)
        for alarm, lamp, *_ in terminal.lamp_panel():
            assert lamp in LAMPS
            assert LAMPS.index(lamp) >= LAMPS.index(alarm['severity'])
            assert terminal.lamp(alarm)[0] == lamp

    def test_an_alarm_rises_one_lamp_per_span_and_stops_at_critical(
            self, at_desk):
        terminal = office_desk(at_desk)
        alarm = {'id': 'AL-1', 'severity': 'MINOR'}
        seen = []
        for minutes in range(0, 400, 5):
            terminal.shift_minutes = minutes
            seen.append(LAMPS.index(terminal.lamp(alarm)[0]))
        assert seen == sorted(seen)
        assert seen[0] <= 1 and seen[-1] == 2
        assert all(b - a <= 1 for a, b in zip(seen, seen[1:]))

    def test_alarms_do_not_all_rise_together(self, at_desk):
        terminal = office_desk(at_desk)
        starts = {terminal.lamp({'id': f'AL-{n}', 'severity': 'MINOR'})[1]
                  for n in range(40)}
        assert len(starts) > 5

    def test_it_is_the_shift_clock_and_not_the_wall_clock(
            self, at_desk, monkeypatch):
        terminal = office_desk(at_desk)
        before = [(a['id'], lamp) for a, lamp, *_ in terminal.lamp_panel()]
        skew_the_wall_clock(terminal, monkeypatch)
        after = [(a['id'], lamp) for a, lamp, *_ in terminal.lamp_panel()]
        assert before == after

    def test_a_passing_shift_is_what_lights_them(self, at_desk):
        terminal = office_desk(at_desk)
        before = {a['id']: lamp for a, lamp, *_ in terminal.lamp_panel()}
        terminal._pass_time(LAMP_MINUTES)
        after = {a['id']: lamp for a, lamp, *_ in terminal.lamp_panel()}
        assert any(LAMPS.index(after[i]) > LAMPS.index(before[i])
                   for i in before)

    def test_nothing_runs_while_connect_work_is_refused(self, at_desk):
        # An alarm the desk cannot clear does not climb, is not held and is
        # not on the index, however late in the tour it is.
        terminal = at_desk('switch')
        terminal.career.qualifications.remove('scc')
        terminal.career.shift = 3
        terminal.deal_alarms()
        assert not terminal.career.may_use('connect')
        terminal.shift_minutes = 470
        for alarm, lamp, *_ in terminal.lamp_panel():
            assert lamp == alarm['severity']
            assert not terminal.lamp_held(alarm)
        assert terminal.alarms_risen() == 0
        assert terminal.alarms_overdue() == 0

    def test_the_tour_the_sign_off_arrives_in_stays_a_grace(self, at_desk):
        terminal = at_desk('switch')
        terminal.career.qualifications.remove('scc')
        terminal.career.shift = 3
        terminal.deal_alarms()
        terminal.shift_minutes = 300
        assert terminal.alarms_overdue() == 0
        terminal.lamp_book()
        terminal.career.qualifications.append('scc')
        terminal.shift_minutes = 470
        assert terminal.alarms_overdue() == 0 and terminal.alarms_risen() == 0
        # The next tour began with the sign-off in hand, so it runs.
        terminal.career.shift = 4
        terminal.deal_alarms()
        terminal.shift_minutes = 470
        assert terminal.alarms_overdue() > 0

    def test_a_dead_panel_stays_dead_across_a_resume(self, at_desk):
        import json
        from bell_system import save
        terminal = at_desk('switch')
        terminal.career.qualifications.remove('scc')
        terminal.career.shift = 3
        terminal.deal_alarms()
        terminal.career.qualifications.append('scc')
        captured = json.loads(json.dumps(save.capture(terminal)))
        assert captured['tour']['lamps']['live'] is False
        fresh = BellSystemTerminal(rng=random.Random(SEED))
        fresh.career.shift = 3
        fresh.career.qualifications = list(terminal.career.qualifications)
        assert save.restore(fresh, captured)
        fresh.shift_minutes = 470
        assert fresh.lamp_book()['live'] is False
        assert fresh.alarms_overdue() == 0

    def test_the_first_tour_is_a_grace(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.career.shift = 1
        terminal.career.reports_closed = 0
        terminal.shift_minutes = 500
        for alarm, lamp, *_ in terminal.lamp_panel():
            assert lamp == alarm['severity']

    def test_clearing_one_costs_its_lamp_and_removes_it(self, at_desk):
        terminal = office_desk(at_desk)
        home = terminal.home_office['clli']
        row = next(r for r in terminal.lamp_panel() if r[2]['clli'] == home)
        alarm, lamp, _, _, cost = row
        assert cost == WORK_COST[lamp]
        before = terminal.shift_minutes
        output = terminal.execute_command(f"connect work {alarm['id']}")
        assert 'cleared at the cause' in output
        assert terminal.shift_minutes - before >= cost
        assert alarm not in terminal.active_alarms
        assert alarm['id'] not in [r[0]['id'] for r in terminal.lamp_panel()]

    def test_clearing_the_home_office_keeps_its_health_counts_honest(
            self, at_desk):
        terminal = office_desk(at_desk)
        health = terminal.system_health
        alarm = terminal.active_alarms[0]
        key = {'CRITICAL': 'critical_alarms', 'MAJOR': 'major_alarms',
               'MINOR': 'minor_alarms'}[alarm['severity']]
        was = health[key]
        terminal.execute_command(f"connect work {alarm['id']}")
        assert health[key] == was - 1

    def test_another_building_costs_the_console_two_more(self, at_desk):
        terminal = office_desk(at_desk)
        home = terminal.home_office['clli']
        others = [o for o in terminal.watched_offices()
                  if o['clli'] != home]
        assert others, 'a console that watches only its own building'
        terminal.office_alarms(others[0]).append({
            'id': 'AL-9999', 'type': 'POWER_SUPPLY', 'severity': 'MINOR',
            'system': 'PWR', 'description': 'Backup power supply low',
            'acknowledged': False, 'timestamp': terminal.clock.now()})
        row = next(r for r in terminal.lamp_panel()
                   if r[0]['id'] == 'AL-9999')
        assert row[4] == WORK_COST[row[1]] + WORK_REMOTE
        before = terminal.shift_minutes
        terminal.execute_command('connect work AL-9999')
        assert terminal.shift_minutes - before >= row[4]

    def test_a_number_that_is_not_standing_costs_nothing(self, at_desk):
        terminal = office_desk(at_desk)
        before = terminal.shift_minutes
        output = terminal.execute_command('connect work AL-0')
        assert 'no alarm' in output
        assert terminal.shift_minutes - before <= 1

    def test_acknowledging_does_not_stop_the_lamp(self, at_desk):
        terminal = office_desk(at_desk)
        alarm = terminal.active_alarms[0]
        before = terminal.lamp(alarm)
        terminal.execute_command(f"alarm ack {alarm['id']}")
        assert alarm in terminal.active_alarms
        assert (LAMPS.index(terminal.lamp(alarm)[0])
                >= LAMPS.index(before[0]))

    def test_the_tally_counts_clears_and_lamps_that_rose(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 3 * LAMP_MINUTES
        rows = dict(terminal.position_tally())
        assert int(rows['alarm lamps that rose']) > 0
        alarm = terminal.active_alarms[0]
        terminal.execute_command(f"connect work {alarm['id']}")
        rows = dict(terminal.position_tally())
        assert rows['alarms cleared at the cause'] == '1'

    def test_the_panel_fits_the_terminal(self, at_desk):
        terminal = office_desk(at_desk)
        output = terminal.execute_command('connect work')
        assert max(len(line) for line in output.split('\n')) <= 74

    def test_the_grace_is_the_first_tour_and_not_the_first_close(
            self, at_desk):
        terminal = office_desk(at_desk, tour=1)
        terminal.career.reports_closed = 1
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.alarms_overdue() == 0
        for alarm, lamp, *_ in terminal.lamp_panel():
            assert lamp == alarm['severity']
        later = office_desk(at_desk, tour=2)
        later.career.reports_closed = 0
        later.shift_minutes = 10 * LAMP_MINUTES
        assert later.alarms_overdue() == 4

    def test_a_symptom_reads_the_system_of_its_cause(self, at_desk):
        terminal = symptom_desk(at_desk, 'TRUNK_DEGRADED', 'CARRIER_LOSS',
                                'POWER_SUPPLY')
        output = terminal.execute_command('connect work')
        assert 'reads: Failures are all on trunks riding T1-PENTAGON' in output
        # The cause itself, and an alarm nothing explains, read their own.
        assert 'reads: Loss of carrier signal' in output
        assert 'reads: Backup power supply voltage low' in output

    def test_a_symptom_matches_the_nearest_cause_standing(self, at_desk):
        terminal = symptom_desk(at_desk, 'TRUNK_DEGRADED', 'RADIO_FADE')
        trunk = terminal.active_alarms[0]
        assert terminal.alarm_reads(trunk, terminal.active_alarms) == (
            'Failures are all on trunks riding TH3-CHI-007')

    def test_clearing_the_cause_clears_what_it_explains_for_no_more_time(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'RADIO_FADE', 'CARRIER_LOSS',
                                'TRUNK_DEGRADED', 'POWER_SUPPLY')
        cost = next(r[4] for r in terminal.lamp_panel()
                    if r[0]['id'] == 'AL-710')
        before = terminal.shift_minutes
        output = terminal.execute_command('connect work AL-710')
        assert ids(terminal) == ['AL-713']
        assert cost <= terminal.shift_minutes - before <= cost + 1
        assert 'cause of AL-711 (CARRIER_LOSS), AL-712 (TRUNK_DEGRADED)' in output
        assert sorted(terminal.lamp_book()['cleared']) == [
            'AL-710', 'AL-711', 'AL-712']
        counts = terminal.system_health
        assert (counts['critical_alarms'], counts['major_alarms'],
                counts['minor_alarms']) == (0, 0, 1)

    def test_clearing_only_a_symptom_leaves_the_cause_standing(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'CARRIER_LOSS', 'TRUNK_DEGRADED')
        output = terminal.execute_command('connect work AL-711')
        assert ids(terminal) == ['AL-710', 'AL-711']
        assert 'only a symptom' in output and 'AL-710' in output
        assert 'clears the cause' in output

    def test_working_a_symptom_costs_the_minutes_and_clears_nothing(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'CARRIER_LOSS', 'TRUNK_DEGRADED')
        row = next(r for r in terminal.lamp_panel()
                   if r[0]['id'] == 'AL-711')
        before = terminal.shift_minutes
        health = dict(terminal.system_health)
        terminal.execute_command('connect work AL-711')
        assert row[4] <= terminal.shift_minutes - before <= row[4] + 1
        assert terminal.system_health == health
        book = terminal.lamp_book()
        assert (book['cleared'], book['held'], book['rose']) == ([], [], [])
        rows = dict(terminal.position_tally())
        assert rows['alarms cleared at the cause'] == '0'

    def test_a_symptom_worked_late_is_not_recorded_as_held(self, at_desk):
        terminal = symptom_desk(at_desk, 'CARRIER_LOSS', 'TRUNK_DEGRADED')
        terminal.shift_minutes = 10 * LAMP_MINUTES
        owed = terminal.alarms_overdue()
        terminal.execute_command('connect work AL-711')
        assert terminal.lamp_book()['held'] == []
        assert terminal.lamp_book()['rose'] == []
        assert terminal.alarms_overdue() == owed == 2

    def test_a_symptom_is_cleared_with_its_cause_after_being_worked(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'CARRIER_LOSS', 'TRUNK_DEGRADED')
        terminal.execute_command('connect work AL-711')
        terminal.execute_command('connect work AL-710')
        assert ids(terminal) == []
        assert sorted(terminal.lamp_book()['cleared']) == ['AL-710', 'AL-711']

    def test_a_cause_with_nothing_to_explain_says_nothing_of_the_kind(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'POWER_SUPPLY', 'RADIO_FADE')
        output = terminal.execute_command('connect work AL-710')
        assert 'cause of' not in output and 'symptom' not in output

    def test_the_summary_follows_what_is_standing(self, at_desk):
        terminal = symptom_desk(at_desk, 'POWER_SUPPLY', 'RADIO_FADE',
                                'CARRIER_LOSS')
        terminal.system_health['overall_status'] = 'DEGRADED'
        terminal.execute_command('connect work AL-710')
        assert terminal.system_health['overall_status'] == 'OPERATIONAL'

    def test_the_connect_page_shows_the_panel_only_at_the_office_desk(
            self, at_desk):
        for role in ROLE_KEYS:
            page = at_desk(role).execute_command('man connect')
            assert ('ALARM PANEL' in page) == (role == 'switch'), role
        assert 'ALARM PANEL' not in MAN_PAGES['connect']


class TestTheOfficeAlarmsCostTheIndex:
    """
    An alarm left at the top lamp costs something, whether or not anyone
    looks at the panel.
    """

    def test_a_standing_alarm_is_a_missed_commitment_at_the_handoff(
            self, at_desk):
        terminal = office_desk(at_desk)
        base = terminal.career.open_overdue()
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.alarms_overdue() == 4
        assert terminal.career.open_overdue() == base + 4

    def test_a_critical_alarm_is_held_a_span_after_it_is_dealt(
            self, at_desk):
        terminal = office_desk(at_desk)
        (critical,) = [a for a in terminal.active_alarms
                       if a['severity'] == 'CRITICAL']
        terminal.shift_minutes = 0
        assert not terminal.lamp_held(critical)
        terminal.shift_minutes = LAMP_MINUTES - 1
        assert not terminal.lamp_held(critical)
        terminal.shift_minutes = LAMP_MINUTES
        assert terminal.lamp_held(critical)

    def test_an_alarm_is_held_a_full_span_after_its_lamp_reached_the_top(
            self, at_desk):
        terminal = office_desk(at_desk)
        for alarm in terminal.active_alarms:
            top = next(m for m in range(0, 20 * LAMP_MINUTES)
                       if (setattr(terminal, 'shift_minutes', m)
                           or terminal.lamp(alarm)[0] == 'CRITICAL'))
            terminal.shift_minutes = top
            assert not terminal.lamp_held(alarm), alarm['id']
            terminal.shift_minutes = top + LAMP_MINUTES - 1
            assert not terminal.lamp_held(alarm), alarm['id']
            terminal.shift_minutes = top + LAMP_MINUTES
            assert terminal.lamp_held(alarm), alarm['id']

    def test_a_handoff_before_the_tour_is_out_banks_the_lamps(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 14
        assert terminal.alarms_overdue() == 0
        seen = []
        real = terminal.career.service_index

        def banked():
            seen.append(terminal.alarms_overdue())
            return real()

        terminal.career.service_index = banked
        terminal._end_shift()
        assert seen and seen[0] == 4

    def test_a_minor_alarm_has_longer_than_a_critical_one(self, at_desk):
        terminal = office_desk(at_desk)
        minor = {'id': 'AL-1', 'severity': 'MINOR'}
        critical = {'id': 'AL-1', 'severity': 'CRITICAL'}
        terminal.shift_minutes = 2 * LAMP_MINUTES
        assert terminal.lamp_held(critical) and not terminal.lamp_held(minor)
        terminal.shift_minutes = 4 * LAMP_MINUTES
        assert terminal.lamp_held(minor)

    def test_only_this_buildings_alarms_are_on_the_index(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        home = terminal.home_office['clli']
        others = [o for o in terminal.watched_offices()
                  if o['clli'] != home]
        for office in others:
            terminal.office_alarms(office).append({
                'id': f"AL-8{others.index(office):03d}",
                'type': 'TEST', 'severity': 'CRITICAL', 'system': 'X',
                'description': 'Standing in another building',
                'acknowledged': False, 'timestamp': terminal.clock.now()})
        held_elsewhere = sum(
            1 for a, _, o, *_ in terminal.lamp_panel()
            if o['clli'] != home and terminal.lamp_held(a))
        assert held_elsewhere >= len(others)
        assert terminal.alarms_overdue() == 4

    def test_clearing_before_the_span_is_out_costs_nothing(self, at_desk):
        terminal = office_desk(at_desk)
        base = terminal.career.open_overdue()
        for alarm in list(terminal.active_alarms):
            terminal.execute_command(f"connect work {alarm['id']}")
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.alarms_overdue() == 0
        assert terminal.career.open_overdue() == base

    def test_the_cost_does_not_need_a_look(self, at_desk):
        terminal = office_desk(at_desk)
        before = terminal.lamp_state()
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.alarms_overdue() == 4
        assert terminal.lamp_state() == before

    def test_the_first_tour_is_never_charged(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.career.shift = 1
        terminal.career.reports_closed = 0
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.alarms_overdue() == 0

    def test_other_desks_have_no_console_to_hold(self, at_desk):
        for role in ('noc', 'custserv', 'sarts'):
            terminal = at_desk(role)
            terminal.shift_minutes = 10 * LAMP_MINUTES
            assert terminal.alarms_overdue() == 0, role

    def test_the_handoff_row_says_how_many(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        rows = dict(terminal.position_tally())
        assert rows['alarms held at the top lamp'] == '4'


class TestALateClearStillCosts:
    """An alarm cleared after it was held has gone from the panel, not
    from the span it stood at the top lamp."""

    def test_clearing_it_late_leaves_the_count_where_it_was(self, at_desk):
        terminal = office_desk(at_desk)
        base = terminal.career.open_overdue()
        terminal.shift_minutes = 2 * LAMP_MINUTES
        (critical,) = [a for a in terminal.active_alarms
                       if a['severity'] == 'CRITICAL']
        assert terminal.lamp_held(critical)
        held = terminal.alarms_overdue()
        assert held >= 1
        terminal.execute_command(f"connect work {critical['id']}")
        assert terminal.lamp_book()['held'] == [critical['id']]
        assert terminal.alarms_overdue() >= held
        assert terminal.career.open_overdue() >= base + held

    def test_clearing_it_in_time_is_not_recorded(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 0
        for alarm in list(terminal.active_alarms):
            terminal.execute_command(f"connect work {alarm['id']}")
        assert terminal.lamp_book()['held'] == []

    def test_a_cause_cleared_late_records_the_symptoms_it_freed(
            self, at_desk):
        terminal = symptom_desk(at_desk, 'RADIO_FADE', 'CARRIER_LOSS')
        terminal.shift_minutes = 10 * LAMP_MINUTES
        terminal.execute_command('connect work AL-710')
        assert sorted(terminal.lamp_book()['held']) == ['AL-710', 'AL-711']
        assert terminal.alarms_overdue() == 2

    def test_another_buildings_clear_is_never_recorded(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        home = terminal.home_office['clli']
        office, alarm = next(
            (o, a) for o in terminal.watched_offices()
            if o['clli'] != home for a in terminal.office_alarms(o))
        terminal.execute_command(f"connect work {alarm['id']}")
        assert terminal.lamp_book()['held'] == []


class TestTheOfficeBookIsHonest:
    """What the review found: per tour, read only."""

    def test_a_new_tour_is_a_new_book(self, at_desk):
        terminal = office_desk(at_desk)
        alarm = terminal.active_alarms[0]
        terminal.execute_command(f"connect work {alarm['id']}")
        assert terminal.lamp_book()['cleared'] == [alarm['id']]
        terminal.career.shift += 1
        book = terminal.lamp_book()
        assert book['tour'] == terminal.career.shift
        assert book['cleared'] == [] and book['rose'] == []

    def test_looking_does_not_change_the_book(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        before = terminal.lamp_state()
        terminal.lamp_panel()
        terminal.alarms_risen()
        terminal.position_tally()
        terminal.execute_command('connect work')
        assert terminal.lamp_state() == before

    def test_a_lamp_that_rose_is_counted_standing_or_cleared(self, at_desk):
        terminal = office_desk(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        risen = terminal.alarms_risen()
        assert risen > 0
        # One that is not a symptom: working a symptom clears nothing.
        rose = next(a for a, lamp, office, *_ in terminal.lamp_panel()
                    if lamp != a['severity']
                    and terminal.alarm_cause(
                        a, terminal.office_alarms(office)) is None)
        terminal.execute_command(f"connect work {rose['id']}")
        assert terminal.alarms_risen() == risen
        assert rose['id'] in terminal.lamp_book()['rose']


class TestTheOfficeDealsEachTour:
    """
    Five alarms ever and a panel that is the same every tour would be a
    puzzle solved once. The deal is seeded from the building and the tour.
    """

    def deal(self, terminal, tour):
        terminal.career.shift = tour
        terminal.deal_alarms()
        return ids(terminal)

    def test_a_tour_is_dealt_the_same_every_time(self, at_desk):
        for tour in (2, 5, 9):
            assert (self.deal(at_desk('switch'), tour)
                    == self.deal(at_desk('switch'), tour))

    def test_the_tours_are_not_all_dealt_alike(self, at_desk):
        terminal = at_desk('switch')
        deals = {tuple(self.deal(terminal, tour)) for tour in range(2, 14)}
        assert len(deals) > 3

    def test_the_building_always_has_a_panel_to_work(self, at_desk):
        from bell_system.screens.remote import HOME_FLOOR
        terminal = at_desk('switch')
        for tour in range(1, 40):
            assert len(self.deal(terminal, tour)) >= HOME_FLOOR, tour

    def test_the_summary_is_counted_from_the_deal(self, at_desk):
        terminal = at_desk('switch')
        for tour in range(2, 12):
            self.deal(terminal, tour)
            health = terminal.system_health
            for level, key in (('CRITICAL', 'critical_alarms'),
                               ('MAJOR', 'major_alarms'),
                               ('MINOR', 'minor_alarms')):
                assert health[key] == sum(
                    1 for a in terminal.active_alarms
                    if a['severity'] == level)
            assert health['overall_status'] == (
                'OPERATIONAL' if len(terminal.active_alarms) < 3
                else 'DEGRADED')

    def test_a_new_tour_is_dealt_when_the_panel_is_next_read(self, at_desk):
        terminal = at_desk('switch')
        terminal.career.shift = 2
        terminal.deal_alarms()
        terminal.career.shift = 3
        panel = {row[0]['id'] for row in terminal.lamp_panel()
                 if row[2]['clli'] == terminal.home_office['clli']}
        assert panel == set(ids(terminal))
        assert panel == set(self.deal(at_desk('switch'), 3))

    def test_the_other_buildings_are_dealt_again_too(self, at_desk):
        terminal = at_desk('switch')
        home = terminal.home_office['clli']
        others = [o for o in terminal.watched_offices()
                  if o['clli'] != home]
        seen = set()
        for tour in range(2, 14):
            terminal.career.shift = tour
            seen.add(tuple(sorted(
                a['id'] for o in others for a in terminal.office_alarms(o))))
        assert len(seen) > 3

    def test_a_lamp_ripens_differently_on_a_different_tour(self, at_desk):
        terminal = at_desk('switch')
        alarm = {'id': 'AL-4474', 'severity': 'MINOR'}
        starts = set()
        for tour in range(2, 14):
            terminal.career.shift = tour
            starts.add(terminal.lamp(alarm)[1])
        assert len(starts) > 3

    def test_the_other_desks_keep_the_deal_they_were_given(self, at_desk):
        terminal = at_desk('noc')
        before = [dict(a) for a in terminal.active_alarms]
        terminal.career.shift = 7
        terminal.office_alarms(terminal.home_office)
        assert terminal.active_alarms == before


class TestTheOfficeAcrossAResume:
    """The same alarms are dealt again on a resume, and a cleared one stays
    cleared."""

    def capture(self, terminal):
        import json
        from bell_system import save
        return json.loads(json.dumps(save.capture(terminal)))

    def resumed(self, terminal, captured):
        from bell_system import save
        fresh = BellSystemTerminal(rng=random.Random(SEED))
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        # The geography is not saved; it is the same console.
        fresh._watched = list(terminal.watched_offices())
        assert save.restore(fresh, captured)
        with redirect_stdout(io.StringIO()):
            fresh.take_position('switch')
        return fresh

    def at_tour(self, at_desk, tour=4):
        terminal = at_desk('switch')
        terminal.career.shift = tour
        terminal.deal_alarms()
        return terminal

    @staticmethod
    def a_cause(terminal):
        """A standing alarm at home that is not a symptom of another."""
        return next(a for a in terminal.active_alarms
                    if terminal.alarm_cause(a, terminal.active_alarms)
                    is None)

    def test_a_resume_deals_the_alarms_that_were_standing(self, at_desk):
        terminal = self.at_tour(at_desk)
        fresh = self.resumed(terminal, self.capture(terminal))
        assert ids(fresh) == ids(terminal)

    def test_a_held_alarm_is_still_held_and_the_count_is_the_same(
            self, at_desk):
        terminal = self.at_tour(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        before = terminal.alarms_overdue()
        assert before == len(terminal.active_alarms)
        fresh = self.resumed(terminal, self.capture(terminal))
        assert fresh.shift_minutes == terminal.shift_minutes
        assert fresh.alarms_overdue() == before

    def test_a_fresh_alarm_does_not_appear_already_held(self, at_desk):
        terminal = self.at_tour(at_desk)
        terminal.shift_minutes = 2 * LAMP_MINUTES
        held = {a['id'] for a in terminal.active_alarms
                if terminal.lamp_held(a)}
        fresh = self.resumed(terminal, self.capture(terminal))
        assert {a['id'] for a in fresh.active_alarms
                if fresh.lamp_held(a)} == held

    def test_a_cleared_alarm_does_not_come_back(self, at_desk):
        terminal = self.at_tour(at_desk)
        dealt = ids(terminal)
        gone = self.a_cause(terminal)
        terminal.execute_command(f"connect work {gone['id']}")
        fresh = self.resumed(terminal, self.capture(terminal))
        assert ids(fresh) == ids(terminal)
        assert gone['id'] not in ids(fresh)
        assert set(dealt) - set(ids(fresh)) == set(
            terminal.lamp_book()['cleared'])
        for key in ('critical_alarms', 'major_alarms', 'minor_alarms',
                    'overall_status'):
            assert fresh.system_health[key] == terminal.system_health[key]
        assert fresh.lamp_book()['cleared'] == terminal.lamp_book()['cleared']

    def test_a_late_clear_is_still_charged_after_a_resume(self, at_desk):
        terminal = self.at_tour(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        for alarm in list(terminal.active_alarms):
            terminal.execute_command(f"connect work {alarm['id']}")
        owed = terminal.alarms_overdue()
        assert owed > 0
        fresh = self.resumed(terminal, self.capture(terminal))
        assert fresh.active_alarms == []
        assert fresh.lamp_book()['held'] == terminal.lamp_book()['held']
        assert fresh.alarms_overdue() == owed

    def test_a_cleared_alarm_in_another_building_does_not_come_back(
            self, at_desk):
        terminal = self.at_tour(at_desk)
        home = terminal.home_office['clli']
        office, alarm = next(
            (o, a) for o in terminal.watched_offices()
            if o['clli'] != home for a in terminal.office_alarms(o)
            if terminal.alarm_cause(a, terminal.office_alarms(o)) is None)
        terminal.execute_command(f"connect work {alarm['id']}")
        fresh = self.resumed(terminal, self.capture(terminal))
        assert alarm['id'] not in [a['id']
                                   for a in fresh.office_alarms(office)]

    def test_the_lamp_that_rose_is_remembered(self, at_desk):
        terminal = self.at_tour(at_desk)
        terminal.shift_minutes = 10 * LAMP_MINUTES
        rose = next(a for a, lamp, office, *_ in terminal.lamp_panel()
                    if lamp != a['severity']
                    and terminal.alarm_cause(
                        a, terminal.office_alarms(office)) is None)
        terminal.execute_command(f"connect work {rose['id']}")
        fresh = self.resumed(terminal, self.capture(terminal))
        assert rose['id'] in fresh.lamp_book()['rose']
        assert fresh.lamp_book()['rose'] == terminal.lamp_book()['rose']

    def test_no_record_damaged_or_other_tour_brings_nothing_back(
            self, at_desk):
        terminal = self.at_tour(at_desk)
        dealt = ids(terminal)
        terminal.execute_command(f"connect work {dealt[0]}")
        for junk in (None, 7, 'x', {'tour': 99, 'cleared': ['AL-4472']},
                     {'tour': terminal.career.shift, 'cleared': 4,
                      'held': 'x'}):
            captured = self.capture(terminal)
            if junk is None:
                del captured['tour']['lamps']
            else:
                captured['tour']['lamps'] = junk
            fresh = self.resumed(terminal, captured)
            assert ids(fresh) == dealt, junk
            assert fresh.lamp_book()['held'] == []


class TestTheRepairDeskCostsTheIndex:
    """
    A customer left holding costs something, whether or not anyone looks.

    The clock moving is what rings them: the attendant says so on the next
    prompt, and a third ring is a missed commitment through the same path a
    late report takes.
    """

    def test_a_ring_is_said_without_anyone_looking(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 15))
        assert ring_messages(terminal) == []
        terminal._pass_time(10)
        terminal.ring_sweep()
        (message,) = ring_messages(terminal)
        assert message.about == down.number
        assert 'ring 1' in ' '.join(message.lines)
        assert 'second call' not in ' '.join(message.lines)

    def test_the_notice_comes_with_the_next_prompt(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 15))
        terminal._pass_time(10)
        pieces = terminal._advance_shift()
        assert any(down.number in piece for piece in pieces)

    def test_a_ring_is_counted_once(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 15))
        terminal._pass_time(10)
        terminal.ring_sweep()
        terminal.ring_sweep()
        assert len(ring_messages(terminal)) == 1
        assert terminal.rings_total() == 1

    def test_the_third_ring_is_one_missed_commitment(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        before = terminal.career.missed_commitments
        terminal._pass_time(40)
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == before
        terminal._pass_time(25)
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == before + 1
        assert 'writing in' in ' '.join(ring_messages(terminal)[-1].lines)
        terminal._pass_time(500)
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == before + 1
        assert terminal.patience(down)[0] == 0  # given up, not ringing

    def test_a_clock_skipping_straight_to_three_still_costs_once(
            self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 0))
        before = terminal.career.missed_commitments
        terminal._pass_time(500)
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == before + 1
        assert terminal.rings_total() == 3

    def test_the_cost_runs_through_the_command_prompt(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        before = terminal.career.missed_commitments
        terminal._pass_time(500)
        terminal.execute_command('trouble list')
        # Others arrive in those minutes and ring too; this one is charged.
        assert terminal.career.missed_commitments >= before + 1
        assert down.missed_commitment

    def test_a_call_in_time_is_a_cost_not_paid(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        down.field_finding = 'OPEN'
        terminal._pass_time(50)
        terminal.execute_command(f'trouble advise {down.number}')
        terminal._pass_time(10)
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == 0

    def test_other_desks_have_no_customers_to_ring(self, at_desk):
        terminal = at_desk('noc')
        terminal._pass_time(600)
        before = terminal.career.missed_commitments
        assert terminal.ring_sweep() == []
        assert ring_messages(terminal) == []
        assert terminal.career.missed_commitments == before

    def test_the_giving_up_is_said_and_charged_once_per_report(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        down.field_finding = 'OPEN'
        before = terminal.career.missed_commitments
        terminal._pass_time(65)
        terminal.ring_sweep()
        assert terminal.patience_book()['rings'][down.number] == 3
        # Told something, they wait again, and are past the third again.
        terminal.execute_command(f'trouble advise {down.number}')
        for _ in range(3):
            terminal._pass_time(65)
            terminal.ring_sweep()
        mine = [m for m in ring_messages(terminal) if m.about == down.number]
        assert len(mine) == 1
        assert 'writing in' in ' '.join(mine[0].lines)
        assert down.missed_commitment
        assert terminal.patience_book()['rings'][down.number] == 3
        assert terminal.career.missed_commitments >= before + 1

    def test_rings_stop_at_three_a_report_whatever_it_is_told(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        down.field_finding = 'OPEN'
        terminal._pass_time(25)
        terminal.ring_sweep()
        terminal.execute_command(f'trouble advise {down.number}')
        for _ in range(6):
            terminal._pass_time(25)
            terminal.ring_sweep()
            book = terminal.patience_book()
            assert book['rings'][down.number] <= 3
            assert max(book['rings'].values()) <= 3
            # Everything counted is what the book holds: nothing pending.
            assert terminal.rings_total() == sum(book['rings'].values())
        assert terminal.patience_book()['rings'][down.number] == 3
        mine = [m for m in ring_messages(terminal) if m.about == down.number]
        assert len(mine) == 3

    def test_the_first_tour_is_never_charged_close_or_no_close(
            self, at_desk):
        for closed in (0, 1):
            terminal = at_desk('custserv')
            (down,) = hold(terminal, (True, 0))
            terminal.career.shift = 1
            terminal.career.reports_closed = closed
            terminal._pass_time(600)
            late = terminal.career.missed_commitments
            flagged = down.missed_commitment
            terminal.ring_sweep()
            assert terminal.career.missed_commitments == late, closed
            assert down.missed_commitment == flagged
            assert ring_messages(terminal) == []

    def test_the_first_tour_is_never_charged(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        terminal.career.shift = 1
        terminal.career.reports_closed = 0
        terminal._pass_time(600)
        late = terminal.career.missed_commitments
        flagged = down.missed_commitment
        terminal.ring_sweep()
        assert terminal.career.missed_commitments == late
        assert down.missed_commitment == flagged
        assert ring_messages(terminal) == []


class TestTheRepairDeskBookIsHonest:
    """What the review found: saved, per tour, read only, finding first."""

    def test_a_new_tour_is_a_new_book(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 10))
        terminal.patience_book()['told'][down.number] = 10
        terminal.patience_book()['rings'][down.number] = 2
        terminal.career.shift += 1
        book = terminal.patience_book()
        assert book['tour'] == terminal.career.shift
        # Nothing carried from the last tour's book, and the customer
        # holding is told as of now, not from the minute they rang in.
        assert book['rings'] == {}
        assert book['told'] == {down.number: down.minutes_spent}
        assert terminal.rings_total() == 0

    def test_looking_does_not_change_who_rang(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 500), (False, 100))
        terminal.ring_sweep()
        before = terminal.patience_state()
        terminal.patience_queue()
        terminal.rings_total()
        terminal.position_tally()
        terminal.patience(terminal.desk.customers()[0])
        terminal.execute_command('trouble advise')
        assert terminal.patience_state()['rings'] == before['rings']
        assert terminal.patience_state()['seen'] == before['seen']

    def test_a_test_alone_is_nothing_yet(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 45))
        down.tested = True
        down.test_notes = ['loop reads open at the pair']
        output = terminal.execute_command('trouble advise')
        assert 'nothing yet' in output
        before = terminal.patience_book()['told'].get(down.number, 0)
        said = terminal.execute_command(f'trouble advise {down.number}')
        assert 'nothing to tell' in said
        assert terminal.patience_book()['told'][down.number] > before

    def test_a_finding_or_a_crew_is_a_status(self, at_desk):
        terminal = at_desk('custserv')
        found, sent = hold(terminal, (True, 10), (True, 10))
        found.field_finding = 'OPEN'
        sent.dispatched_to = 'splicer'
        sent.field_finding = 'OPEN'
        output = terminal.execute_command('trouble advise')
        assert output.count('status') >= 2
        assert 'nothing yet' not in output


    def test_a_handoff_does_not_ring_every_carried_report(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 10), (False, 10), (True, 30))
        terminal._end_shift()
        assert terminal.career.shift == 3
        carried = terminal.desk.customers()
        assert carried
        terminal._advance_shift()
        assert ring_messages(terminal) == []
        assert terminal.rings_total() == 0
        for report in carried:
            assert terminal.patience(report)[0] == 0, report.number

    def test_a_customer_carried_over_rings_on_their_own_wait(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 10))
        terminal._end_shift()
        terminal._advance_shift()
        assert terminal.patience(down)[0] == 0
        terminal._pass_time(25)
        terminal._advance_shift()
        assert terminal.patience(down)[0] == 1
        assert [m.about for m in ring_messages(terminal)
                if m.about == down.number] == [down.number]

    def test_only_the_right_force_gives_the_desk_something_to_say(
            self, at_desk):
        from bell_system.reports import FAULTS
        terminal = at_desk('custserv')
        right, wrong = hold(terminal, (True, 5), (True, 5))
        wanted = FAULTS[right.record.fault].dispatch
        other = next(fault.dispatch for fault in FAULTS.values()
                     if fault.dispatch.lower() != wanted.lower())
        terminal.desk.dispatch(right, wanted, terminal.shift_minutes)
        terminal.desk.dispatch(wrong, other, terminal.shift_minutes)
        assert wrong.dispatched_to is not None and not wrong.field_finding
        assert terminal._has_reading(right)
        assert not terminal._has_reading(wrong)
        said = terminal.execute_command(f'trouble advise {wrong.number}')
        assert 'nothing to tell' in said and 'is on it' not in said

    def test_a_report_is_charged_once_for_giving_up_and_for_passing(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        before = terminal.career.missed_commitments
        terminal._pass_time(65)
        terminal.ring_sweep()
        assert terminal.patience(down)[0] == 0  # given up, not ringing
        assert not down.overdue()
        assert terminal.career.missed_commitments == before + 1
        assert down.missed_commitment
        down.minutes_spent += 100_000
        terminal._pass_time(1)
        assert down.overdue()
        assert terminal.career.missed_commitments == before + 1

    def test_a_report_already_late_is_not_charged_again_at_the_third_ring(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        before = terminal.career.missed_commitments
        down.minutes_spent += 100_000
        terminal._pass_time(1)
        assert terminal.career.missed_commitments == before + 1
        terminal.ring_sweep()
        assert terminal.patience(down)[0] == 0  # given up, not ringing
        assert ring_messages(terminal)
        assert terminal.career.missed_commitments == before + 1

    def test_the_handoff_does_not_charge_a_given_up_report_again(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        terminal._pass_time(65)
        terminal.ring_sweep()
        # Near enough to its commitment that the rest of the tour passes it.
        allowed = int((down.commitment - down.received).total_seconds() // 60)
        down.minutes_spent = allowed - 100
        assert not down.overdue()
        charged = terminal.career.missed_commitments
        terminal._end_shift()
        assert down.overdue()
        assert terminal.career.missed_commitments == charged

    def test_the_countdown_is_gone_after_the_third_ring(self, at_desk):
        terminal = at_desk('custserv')
        gone, calm = hold(terminal, (True, 10_000), (False, 5))
        terminal.ring_sweep()  # The clock has moved on; they have rung.
        rows = {}
        for line in terminal.execute_command('trouble advise').split('\n'):
            for report in (gone, calm):
                if line.startswith(report.number):
                    rows[report.number] = line.split()
        # Given up: not ringing, so no rings shown and no next one.
        assert rows[gone.number][2:5] == ['0', 'gave', 'up']
        assert rows[calm.number][3].endswith('m')


class TestTheRepairDeskAcrossAResume:
    """The book is saved with the tour, so a resume does not ring at once."""

    def capture(self, terminal):
        import json
        from bell_system import save
        return json.loads(json.dumps(save.capture(terminal)))

    def resumed(self, terminal, captured):
        from bell_system import save
        fresh = BellSystemTerminal(rng=random.Random(SEED))
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        with redirect_stdout(io.StringIO()):
            fresh.take_position('custserv')
        return fresh

    def test_a_call_made_before_the_save_still_counts(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 60))
        down.field_finding = 'OPEN'
        terminal.execute_command(f'trouble advise {down.number}')
        told = terminal.patience_book()['told'][down.number]
        fresh = self.resumed(terminal, self.capture(terminal))
        back = fresh.patience_book()
        assert back['tour'] == terminal.career.shift
        assert back['told'] == terminal.patience_book()['told']
        assert back['told'][down.number] == told
        # No instant rings on the first command after the resume.
        before = fresh.career.missed_commitments
        fresh.execute_command('trouble list')
        assert fresh.rings_total() == 0
        assert fresh.career.missed_commitments == before

    def test_rings_already_made_are_not_made_again(self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 0))
        terminal._pass_time(500)
        terminal.ring_sweep()
        missed = terminal.career.missed_commitments
        captured = self.capture(terminal)
        fresh = self.resumed(terminal, captured)
        fresh.career.missed_commitments = missed
        fresh.ring_sweep()
        assert fresh.career.missed_commitments == missed
        assert fresh.rings_total() == 3

    def test_no_record_damaged_or_other_tour_forgives_the_wait(
            self, at_desk):
        terminal = at_desk('custserv')
        hold(terminal, (True, 400))
        for junk in (None, 7, 'x', {'tour': 99, 'told': {}},
                     {'tour': terminal.career.shift + 1, 'told': {}}):
            captured = self.capture(terminal)
            if junk is None:
                del captured['tour']['patience']
            else:
                captured['tour']['patience'] = junk
            fresh = self.resumed(terminal, captured)
            before = fresh.career.missed_commitments
            fresh.execute_command('trouble list')
            customers = fresh.desk.customers()
            assert customers, junk
            for report in customers:
                assert fresh.patience(report)[0] == 0, junk
            assert fresh.career.missed_commitments == before, junk


def reading_costs(loop):
    """Expected minutes to clear a circuit by looping it, then sending."""
    total = sum(PLACE_WEIGHTS)
    return loop + sum(weight * PLACES[place][1] for place, weight
                      in zip(PLACES, PLACE_WEIGHTS)) / total


def guessing_costs(order):
    """Expected minutes to clear it by sending forces in this order."""
    total = sum(PLACE_WEIGHTS)
    spent = expected = 0
    for place in order:
        weight = PLACE_WEIGHTS[list(PLACES).index(place)]
        minutes = PLACES[place][1]
        expected += weight / total * (spent + minutes)
        spent += minutes + WRONG_FORCE_MINUTES
    return expected


def out_now(terminal, circuit):
    """What a screen would say a circuit has been out, changing nothing."""
    return terminal.special_services.out_for(
        circuit, terminal.career.shift, terminal.shift_minutes)


class TestTheSartsRepairIsHonest:
    """What the review of the SARTS desk found, one test each."""

    def test_a_row_number_is_a_row_of_the_board(self, at_desk):
        terminal = at_desk('sarts')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        board = [c for c in terminal.special_services.listing()
                 if c.status == 'TRBL']
        # The substring match used to win: '1' is in 0001-PL-961.
        assert terminal.special_services.find('1').circuit_id == '0001-PL-961'
        assert board[0].circuit_id == '0002-PL-352'
        output = terminal.execute_command('sarts repair 1')
        assert 'SARTS Loop-back - 0002-PL-352' in output
        output = terminal.execute_command('sarts repair 2')
        assert f'SARTS Loop-back - {board[1].circuit_id}' in output

    def test_a_number_past_the_board_or_with_a_zero_is_an_identifier(
            self, at_desk):
        terminal = at_desk('sarts')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        inventory = terminal.special_services
        board = [c for c in inventory.listing() if c.status == 'TRBL']
        assert inventory.find('0006', board).circuit_id.startswith('0006')
        assert inventory.find('166', board).circuit_id == '0006-FX-166'

    def test_the_list_numbers_work_at_the_desk_that_prints_them(
            self, at_desk):
        terminal = at_desk('sarts')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        first = terminal.special_services.listing()[0]
        assert first.circuit_id in terminal.execute_command('sarts circuit 1')

    def test_a_force_is_refused_for_a_circuit_nobody_has_read(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'FACILITY', read=False)
        before = terminal.shift_minutes
        terminal.execute_command('sarts trouble')
        tick = terminal.shift_minutes - before
        before = terminal.shift_minutes
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} facility')
        assert terminal.shift_minutes - before == tick
        assert 'has not been read this tour' in output
        assert f'sarts test {circuit.circuit_id}' in output
        assert circuit.status == 'TRBL'

    def test_a_jack_circuit_is_told_it_must_be_looped(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, access='JACK', read=False)
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} facility')
        assert 'manual jack access' in output
        assert f'sarts repair {circuit.circuit_id}' in output
        assert 'sarts test' not in output.split('First:')[1]

    def test_a_test_or_a_loop_back_is_a_reading(self, at_desk):
        terminal = at_desk('sarts')
        tested = failing_circuit(terminal, 'FACILITY', read=False)
        tested.status = 'IS'
        terminal.execute_command(f'sarts test {tested.circuit_id}')
        assert tested.status == 'TRBL'
        out = terminal.execute_command(
            f'sarts repair {tested.circuit_id} facility')
        assert 'back in service' in out
        jack = failing_circuit(terminal, 'PREMISES', access='JACK',
                               read=False)
        terminal.execute_command(f'sarts repair {jack.circuit_id}')
        out = terminal.execute_command(
            f'sarts repair {jack.circuit_id} premises')
        assert 'back in service' in out

    def test_a_reading_does_not_carry_to_the_next_tour(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        terminal.career.shift += 1
        terminal.shift_minutes = 3
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} facility')
        assert 'has not been read this tour' in output

    @pytest.mark.parametrize('access,loop', [
        ('SMAS', LOOP_REMOTE_MINUTES), ('JACK', LOOP_VISIT_MINUTES)])
    def test_reading_beats_the_best_order_of_guesses(self, access, loop):
        """Worked from the constants, for either way of getting at it."""
        best_guess = min(guessing_costs(order)
                         for order in itertools.permutations(PLACES))
        assert reading_costs(loop) < best_guess

    def test_the_console_charges_what_the_constants_say(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE', access='JACK')
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        looped = out_now(terminal, circuit)
        assert looped >= LOOP_VISIT_MINUTES
        terminal.execute_command(
            f'sarts repair {circuit.circuit_id} premises')
        assert out_now(terminal, circuit) - looped >= (
            PLACES['PREMISES'][1] + WRONG_FORCE_MINUTES)

    # -- the other desks ---------------------------------------------------

    def test_the_field_desks_status_and_board_are_what_they_were(
            self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 25
        mine = terminal.execute_command('sarts status').split('\n')
        board = terminal.execute_command('sarts trouble')
        assert 'Held In Trouble' in board
        terminal.position = get_position('field')
        theirs = terminal.execute_command('sarts status').split('\n')
        # The office line carries the clock; compare everything else.
        strip = [line for line in mine
                 if not line.startswith('  Circuit-minutes')
                 and 'sarts repair' not in line]
        assert [line for i, line in enumerate(theirs) if i != 1] == [
            line for i, line in enumerate(strip) if i != 1]
        assert not any('Circuit-minutes' in line or 'sarts repair' in line
                       for line in theirs)
        assert theirs[-4:] == [
            "  sarts list        The inventory",
            "  sarts trouble     Circuits reported in trouble",
            "  sarts test <id>   Reach a circuit and measure it",
            "  sarts categories  What counts as a special service",
        ]
        listing = terminal.execute_command('sarts trouble')
        assert listing == terminal.sarts_console.inventory('TRBL')
        assert listing.startswith('Special Services Circuits\n')
        assert 'Held In Trouble' not in listing

    def test_the_field_desk_gets_no_repair_pointers(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, read=False)
        circuit.status = 'IS'
        terminal.position = get_position('field')
        assert 'sarts repair' not in terminal.execute_command(
            f'sarts test {circuit.circuit_id}')
        assert 'sarts repair' not in terminal.execute_command(
            f'sarts circuit {circuit.circuit_id}')

    def test_the_field_desk_still_finds_a_circuit_the_old_way(self, at_desk):
        terminal = at_desk('field')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        assert '0001-PL-961' in terminal.execute_command('sarts circuit 1')

    # -- the nits ----------------------------------------------------------

    def test_a_circuit_marked_in_trouble_always_has_a_place(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, read=False)
        circuit.status = 'IS'
        circuit.fault_place = None
        terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert circuit.status == 'TRBL'
        assert circuit.fault_place == fault_place_for(circuit.circuit_id)

    def test_a_circuit_in_trouble_points_at_the_verb(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        assert (f'sarts repair {circuit.circuit_id}'
                in terminal.execute_command(
                    f'sarts circuit {circuit.circuit_id}'))
        circuit.status = 'IS'
        assert 'sarts repair' not in terminal.execute_command(
            f'sarts circuit {circuit.circuit_id}')


class TestTheOutageCostsTheIndex:
    """A circuit left out past its window is a missed commitment."""

    def test_a_circuit_left_past_the_window_costs_the_index_unseen(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        terminal.shift_minutes = OUTAGE_WINDOW
        assert terminal.outages_overdue() == 0
        terminal.shift_minutes = OUTAGE_WINDOW + 1
        held = terminal.career.open_overdue()
        circuit.status = 'IS'
        assert held == terminal.career.open_overdue() + 1

    def test_the_cost_is_counted_once_however_often_the_desk_is_taken(
            self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 90
        before = terminal.career.open_overdue()
        terminal.take_position('sarts')
        assert terminal.career.open_overdue() == before

    def test_another_desk_does_not_pay_for_it(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 90
        terminal.position = get_position('field')
        assert terminal.outages_overdue() == 0

    def test_the_whole_first_tour_is_a_grace(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.career.shift = 1
        terminal.special_services.settle(1, 0)
        terminal.shift_minutes = 500
        assert terminal.outages_overdue() == 0

    def test_a_circuit_cleared_in_time_costs_nothing(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        missed = terminal.career.missed_commitments
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} office')
        assert 'back in service' in output
        assert terminal.career.missed_commitments == missed

    def test_a_circuit_cleared_late_is_a_missed_commitment(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        before = terminal.career.open_overdue()
        output = terminal.execute_command(
            f'sarts repair {circuit.circuit_id} office')
        assert 'missed commitment' in output
        # Cleared, but the miss stays on the desk's figure and on the index
        # (the same one the circuit was on while it stood out), and it is
        # not a second charge on the career's own count.
        assert terminal.outages_overdue() == 1
        assert terminal.career.open_overdue() == before
        assert terminal.special_services.late == {circuit.circuit_id}

    def test_a_late_clear_is_counted_once_however_often_it_is_asked(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        terminal.shift_minutes += 200
        for _ in range(3):
            assert terminal.outages_overdue() == 1

    def test_a_clear_in_time_is_not_on_the_late_list(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        assert terminal.special_services.late == set()
        assert terminal.outages_overdue() == 0

    def test_a_new_tour_forgets_the_late_list(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        inventory = terminal.special_services
        assert inventory.past_window(terminal.career.shift, 100) == 1
        assert inventory.past_window(terminal.career.shift + 1, 0) == 0
        inventory.accrue(terminal.career.shift + 1, 0)
        assert inventory.late == set()

    def test_a_wrong_force_pushes_a_circuit_past_the_window(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW - 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} '
                                 f'premises')
        assert terminal.outages_overdue() == 1

    def test_it_is_the_shift_clock_and_not_the_wall_clock(self, at_desk, monkeypatch):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        skew_the_wall_clock(terminal, monkeypatch)
        assert terminal.outages_overdue() == 0

    def test_a_handoff_before_the_tour_is_out_banks_the_circuits_held(
            self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 14
        assert terminal.outages_overdue() == 0
        seen = []
        real = terminal.career.service_index

        def banked():
            seen.append(terminal.outages_overdue())
            return real()

        terminal.career.service_index = banked
        terminal._end_shift()
        assert seen and seen[0] == 1

    def test_the_handoff_counts_what_ran_past(self, at_desk):
        terminal = at_desk('sarts')
        failing_circuit(terminal)
        terminal.shift_minutes = 90
        rows = dict(terminal.position_tally())
        assert rows['circuits out past the window'] == '1'
        assert 'WHAT THIS DESK DID' in terminal.execute_command('handoff')

    def test_counting_changes_nothing(self, at_desk):
        """Screens and the tally read; only a test or a repair charges."""
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal)
        terminal.shift_minutes = 90
        for _ in range(2):
            terminal.position_tally()
            terminal.outages_overdue()
            terminal.career.open_overdue()
            terminal.execute_command('sarts status')
            terminal.execute_command('sarts trouble')
            terminal.execute_command('sarts list')
        assert circuit.out_minutes == 0
        assert terminal.special_services._clocked_to == 0


class TestTheOutageClockAcrossAResume:
    """The inventory is dealt again on a resume; it must not be charged."""

    def capture(self, terminal):
        import json
        from bell_system import save
        return json.loads(json.dumps(save.capture(terminal)))

    def resumed(self, terminal, captured):
        from bell_system import save
        fresh = BellSystemTerminal(rng=random.Random(SEED))
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        with redirect_stdout(io.StringIO()):
            fresh.take_position('sarts')
        return fresh

    def test_the_saved_circuits_come_back_with_their_minutes(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'FACILITY', access='JACK',
                                  read=False)
        terminal.shift_minutes = 40
        terminal.execute_command(f'sarts repair {circuit.circuit_id}')
        spent = circuit.out_minutes
        now = terminal.shift_minutes
        fresh = self.resumed(terminal, self.capture(terminal))
        back = fresh.special_services.circuits[circuit.circuit_id]
        assert back.status == 'TRBL' and back.fault_place == 'FACILITY'
        assert back.out_minutes == spent
        assert fresh.shift_minutes == now
        assert fresh.special_services.was_read(circuit.circuit_id)
        assert out_now(fresh, back) == out_now(terminal, circuit)

    def test_a_repair_made_before_the_save_is_still_made(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        fresh = self.resumed(terminal, self.capture(terminal))
        back = fresh.special_services.circuits[circuit.circuit_id]
        assert back.status == 'IS' and back.fault_place is None

    def test_a_fresh_inventory_is_never_charged_from_minute_zero(
            self, at_desk):
        terminal = at_desk('sarts')
        terminal.shift_minutes = 300
        captured = self.capture(terminal)
        del captured['tour']['sarts']
        fresh = BellSystemTerminal(rng=random.Random(SEED))
        fresh.career.shift = terminal.career.shift
        dealt = failing_circuit(fresh)
        from bell_system import save
        assert save.restore(fresh, captured)
        with redirect_stdout(io.StringIO()):
            fresh.take_position('sarts')
        assert fresh.shift_minutes == 300
        assert out_now(fresh, dealt) == 0
        assert fresh.outages_overdue() == 0
        assert fresh.special_services.minutes_out(
            fresh.career.shift, fresh.shift_minutes) == 0

    def test_a_damaged_record_is_forgiven(self, at_desk):
        terminal = at_desk('sarts')
        terminal.shift_minutes = 300
        for junk in (None, 7, 'x', {'tour': 2}, {'tour': 2, 'circuits': 4},
                     {'tour': 2, 'circuits': [{'id': 'A'}]},
                     {'tour': 2, 'clocked_to': 'no', 'read': [],
                      'circuits': [{'id': 'A', 'category': 'NOPE',
                                    'customer': 'x', 'from': 'a', 'to': 'b',
                                    'access': 'SMAS', 'status': 'IS',
                                    'impaired': False, 'place': None,
                                    'out': 0, 'last': None}]}):
            captured = self.capture(terminal)
            captured['tour']['sarts'] = junk
            fresh = self.resumed(terminal, captured)
            assert fresh.special_services.minutes_out(
                fresh.career.shift, fresh.shift_minutes) == 0

    def test_a_save_before_any_command_is_the_saved_tour_not_the_last(
            self, at_desk):
        """
        Nothing has touched the inventory this tour, so it still carries the
        last tour's number; the save is of this tour and must read as one.
        """
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'FACILITY', read=False)
        terminal.career.shift += 1
        terminal.shift_minutes = 25
        assert terminal.special_services._tour != terminal.career.shift
        captured = self.capture(terminal)
        assert captured['tour']['sarts']['tour'] == terminal.career.shift
        fresh = self.resumed(terminal, captured)
        back = fresh.special_services.circuits[circuit.circuit_id]
        assert back.status == 'TRBL' and back.fault_place == 'FACILITY'
        # Nothing was charged this tour yet, and what the last tour charged
        # is not carried; the circuit has been out since the tour began.
        assert back.out_minutes == 0
        assert out_now(fresh, back) == out_now(terminal, circuit) == 25

    def test_a_late_clear_survives_a_resume(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        assert terminal.outages_overdue() == 1
        before = terminal.career.open_overdue()
        fresh = self.resumed(terminal, self.capture(terminal))
        assert fresh.special_services.late == {circuit.circuit_id}
        assert fresh.outages_overdue() == 1
        assert fresh.career.open_overdue() == before

    def test_a_late_list_that_will_not_read_is_forgiven(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        for junk in (None, 7, 'x', {'a': 1}, ['not-a-circuit']):
            captured = self.capture(terminal)
            captured['tour']['sarts']['late'] = junk
            fresh = self.resumed(terminal, captured)
            assert fresh.outages_overdue() == 0, junk
        captured = self.capture(terminal)
        del captured['tour']['sarts']['late']
        assert self.resumed(terminal, captured).outages_overdue() == 0

    def test_a_late_clear_from_another_tour_is_not_carried_over(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        captured = self.capture(terminal)
        captured['tour']['sarts']['tour'] = terminal.career.shift + 1
        fresh = self.resumed(terminal, captured)
        assert fresh.special_services.late == set()
        assert fresh.outages_overdue() == 0

    def test_a_reading_from_the_saved_tour_survives_but_no_other(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'FACILITY')
        captured = self.capture(terminal)
        assert captured['tour']['sarts']['read'] == [circuit.circuit_id]
        captured['tour']['sarts']['tour'] = terminal.career.shift + 1
        fresh = self.resumed(terminal, captured)
        assert not fresh.special_services.was_read(circuit.circuit_id)


class TestTheNocQueueIsHonest:
    """What the review of the queue found, one test each."""

    def test_a_ticket_somebody_has_is_not_waiting(self, at_desk):
        terminal = at_desk('noc')
        given, named, resolved, closed, free = put_tickets(
            terminal, ('MAJOR', 1), ('MAJOR', 2), ('MAJOR', 3),
            ('MAJOR', 4), ('MAJOR', 5))
        terminal._assigned_tickets.add(given['id'])
        terminal.execute_command(
            f"trouble assign {named['id']} Outside Plant")
        # A resolved ticket leaves the active list, as `trouble resolve`
        # does it; a status alone never takes one out (see the leftovers).
        for done, status in ((resolved, 'RESOLVED'), (closed, 'CLOSED')):
            done['status'] = status
            terminal.active_tickets.remove(done)
        waiting = [t['id'] for t in terminal.triage_queue()]
        assert waiting == [free['id']]
        terminal.shift_minutes = 500
        terminal.triage_sweep()
        assert given['escalation_level'] == 1
        assert named['escalation_level'] == 1

    def test_the_whole_first_tour_is_a_grace_not_only_until_a_close(
            self, at_desk):
        terminal = at_desk('noc')
        terminal.career.shift = 1
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.career.reports_closed = 1  # first_tour() has ended.
        terminal.shift_minutes = 20
        terminal.triage_sweep()
        assert major['escalation_level'] == 1
        terminal.shift_minutes = 500
        assert terminal.triage_lapsed() == 0
        output = terminal.execute_command('trouble triage ' + major['id'])
        assert 'grace' in output

    def test_escalating_does_not_shorten_the_window(self, at_desk):
        terminal = at_desk('noc')
        (minor,) = put_tickets(terminal, ('MINOR', 900))
        due = terminal.triage_due(minor)
        terminal.execute_command('trouble escalate ' + minor['id'])
        assert minor['priority'] != 'MINOR'
        assert terminal.triage_due(minor) == due == 60

    def test_a_ticket_left_waiting_costs_the_index_unseen(self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('CRITICAL', 900), ('MAJOR', 5))
        before = terminal.career.open_overdue()
        terminal.shift_minutes = 20
        assert terminal.career.open_overdue() == before + 1
        terminal.shift_minutes = 40
        assert terminal.career.open_overdue() == before + 2

    def test_taking_a_ticket_in_time_costs_nothing(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 5))
        missed = terminal.career.missed_commitments
        terminal.shift_minutes = 29
        terminal.execute_command('trouble triage ' + major['id'])
        assert terminal.career.missed_commitments == missed

    def test_the_cost_is_counted_once_however_often_the_desk_is_taken(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('CRITICAL', 900))
        terminal.shift_minutes = 20
        before = terminal.career.open_overdue()
        terminal.take_position('noc')
        assert terminal.career.open_overdue() == before

    def test_a_resumed_shift_does_not_start_every_window_late(self, at_desk):
        terminal = at_desk('noc')
        terminal.shift_minutes = 45
        before = terminal.triage_lapsed()
        fresh = resume_onto_fresh(terminal, 'noc')
        assert fresh.shift_minutes == 45
        # The windows go on from where they stood: what was past its window
        # still is, and nothing is added or taken away by the resume.
        assert fresh.triage_lapsed() == before
        assert fresh.career.open_overdue() == terminal.career.open_overdue()

    def test_the_book_itself_survives_a_resume(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 5))
        terminal.shift_minutes = 10
        terminal.execute_command('trouble triage ' + major['id'])
        assert terminal.triage_state()['taken'][major['id']] == 10
        fresh = resume_onto_fresh(terminal, 'noc')
        assert fresh.triage_book()['taken'] == {major['id']: 10}

    def test_a_save_from_before_the_book_opens_every_window_from_now(
            self, at_desk):
        terminal = at_desk('noc')
        terminal.shift_minutes = 300
        fresh = resume_onto_fresh(
            terminal, 'noc',
            mutate=lambda captured: captured['tour'].pop('triage'))
        assert fresh.triage_overdue() == []

    def test_a_damaged_book_is_forgiven(self, at_desk):
        terminal = at_desk('noc')
        for junk in (None, 7, 'x', {'tour': 2, 'opened': 'no',
                                    'klass': {'TKT': 'BOGUS'},
                                    'taken': [1], 'lapsed': {'T': -4}}):
            terminal.restore_triage(junk)
            assert terminal.triage_overdue() == []

    def test_a_lapse_is_a_cost_that_survives_the_take(self, at_desk):
        """
        The index scores nothing for a tour with no closes and no backlog,
        so a late take that only left the backlog would have cost nothing.
        """
        terminal = at_desk('noc')
        terminal.career.reports_closed = 0
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 31
        waiting = terminal.career.service_index()
        assert waiting < 100
        output = terminal.execute_command('trouble triage ' + major['id'])
        assert 'after the window closed' in output
        assert terminal.career.service_index() == waiting

    def test_a_lapse_costs_the_same_taken_late_as_left_waiting(
            self, at_desk):
        late, never = at_desk('noc'), at_desk('noc')
        for terminal in (late, never):
            terminal.career.reports_closed = 0
            put_tickets(terminal, ('MAJOR', 900))
            terminal.shift_minutes = 31
        late.execute_command('trouble triage ' + late.active_tickets[0]['id'])
        assert late.career.service_index() == never.career.service_index()

    def test_a_late_assign_is_a_lapse(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        base = terminal.career.open_overdue()
        terminal.shift_minutes = 31
        terminal.execute_command(f"trouble assign {major['id']} Outside Plant")
        assert major['id'] in terminal._assigned_tickets
        assert terminal.triage_lapsed() == 1
        assert terminal.career.open_overdue() == base + 1

    def test_an_assign_in_time_is_not(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 29
        terminal.execute_command(f"trouble assign {major['id']} Outside Plant")
        assert terminal.triage_lapsed() == 0

    def test_the_control_centre_assigning_late_is_a_lapse(self, at_desk):
        """The clock notices the window before the switching control
        centre gets to hand the ticket to somebody."""
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 31
        terminal._advance_shift()
        terminal._assigned_tickets.add(major['id'])
        assert terminal.triage_lapsed() == 1
        assert major['escalation_level'] == 2

    def test_only_the_nocs_assign_is_ever_noticed(self, at_desk):
        terminal = at_desk('field')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 31
        terminal.execute_command(f"trouble assign {major['id']} Outside Plant")
        terminal._advance_shift()
        assert terminal.triage_book()['lapsed'] == {}
        assert major['escalation_level'] == 1

    def test_resuming_keeps_an_overdue_ticket_nobody_looked_at(
            self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 45
        assert terminal.triage_book()['lapsed'] == {}
        fresh = resume_onto_fresh(terminal, 'noc')
        assert fresh.triage_lapsed() >= 1
        assert fresh.career.open_overdue() >= 1

    def test_a_resumed_ticket_reusing_an_assigned_number_can_lapse(
            self, at_desk):
        """A save from before the pool was kept: the session is dealt its
        own, and the numbers it reuses belong to other tickets."""
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 5))
        terminal.execute_command('trouble triage ' + major['id'])
        assert major['id'] in terminal._assigned_tickets
        other = dict(major, title='a different ticket', status='OPEN',
                     assigned_team='UNASSIGNED', resolution_steps=[])

        def forget_the_pool(captured):
            del captured['tour']['tickets']
            del captured['tour']['ticket_counter']

        fresh = resume_onto_fresh(
            terminal, 'noc', mutate=forget_the_pool,
            dealt=lambda session: session.active_tickets.__setitem__(
                slice(None), [other]))
        assert other['id'] not in fresh._assigned_tickets
        assert [t['id'] for t in fresh.triage_queue()] == [other['id']]

    def test_a_ticket_entered_late_in_a_new_tour_is_not_born_overdue(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal)
        terminal.triage_book()
        terminal.career.shift += 1  # A new tour, and no call has made its book.
        terminal.shift_minutes = 31
        terminal.execute_command('trouble create MAINTENANCE MAJOR Test')
        (entered,) = terminal.active_tickets
        assert terminal.triage_due(entered) == 61
        assert terminal.triage_overdue() == []

    def test_the_table_and_the_call_use_the_class_fixed_at_the_stamp(
            self, at_desk):
        terminal = at_desk('noc')
        (minor,) = put_tickets(terminal, ('MINOR', 900))
        terminal.execute_command('trouble escalate ' + minor['id'])
        assert minor['priority'] != 'MINOR'
        terminal.shift_minutes = 0
        row = next(line for line in
                   terminal.execute_command('trouble triage').split('\n')
                   if line.startswith(minor['id']))
        assert 'MINOR' in row and '60m left' in row and ' 2m ' in row
        before = terminal.shift_minutes
        terminal.execute_command('trouble triage ' + minor['id'])
        spent = terminal.shift_minutes - before
        plain = at_desk('noc')
        (same,) = put_tickets(plain, ('MINOR', 900))
        plain.execute_command('trouble triage ' + same['id'])
        assert spent == plain.shift_minutes

    def test_help_names_the_desks_verb_and_pressure(self, at_desk):
        for key in FOUR_DESKS:
            terminal = at_desk(key)
            terminal.role, terminal.role_name = key, POSITIONS[key].name
            output = terminal.execute_command('help')
            assert POSITIONS[key].verb in output, key
            assert POSITIONS[key].pressure in output, key
        radio = at_desk('radio')
        radio.role, radio.role_name = 'radio', POSITIONS['radio'].name
        assert 'Only this desk' not in radio.execute_command('help')


# Frozen from before the four desks, so that "unchanged" means unchanged and
# not "has no verb": commands, bias, share and tally of the other eight.
FROZEN = {
    'sysop': (('ps', 'df', 'who', 'uucp', 'uulog', 'at', 'date', 'ls'), {},
              0.42, ('at_jobs', 'uucp_queue', 'commands_run')),
    'field': (('trace', 'dialtone', 'emergency', 'ticket', 'provision',
               'sarts'),
              {'WET': 2.5, 'OPEN': 1.6, 'GROUND': 1.6, 'CROSS': 1.4}, 0.72,
              ('dispatches', 'wasted_trips', 'sheaths_cleared')),
    'tsps': (('tsps', 'operator', 'directory', 'collect', 'billing'),
             {'ROH': 3.0, 'NONE': 1.4, 'SHORT': 1.3}, 0.62,
             ('no_trouble_found', 'off_hook_caught', 'commitments_met')),
    'dba': (('dbquery', 'custdb', 'billing', 'service'),
            {'CO_EQUIP': 3.0, 'FCG': 1.5}, 0.42,
            ('found_in_records', 'orders_raised', 'office_faults')),
    'netplan': (('netplan', 'traffic', 'routing', 'capacity', 'billing',
                 'tnds'), {}, 0.25,
                ('groups_over', 'tickets_worked', 'commands_run')),
    'radio': (('radio', 'microwave', 'satellite', 'alarm'), {}, 0.3,
              ('alarms_open', 'weather_now', 'tickets_worked')),
    'tnds': (('tnds', 'traffic', 'capacity', 'trace'), {}, 0.3,
             ('groups_over', 'commands_run', 'tickets_worked')),
    'docprep': (('nroff', 'troff', 'tbl', 'eqn', 'pic', 'refer', 'spell'),
                {}, 0.35, ('documents_set', 'commands_run', 'files_written')),
}


def test_the_other_eight_match_a_frozen_snapshot():
    for key, (commands, bias, share, tally) in FROZEN.items():
        position = POSITIONS[key]
        assert (position.commands, position.fault_bias,
                position.board_share, position.tally) == (
                    commands, bias, share, tally), key
        assert key not in FOUR_DESKS


class TestTheNocQueueGatesAndResumes:
    """What the third review found: resolve, the pool, the early handoff."""

    def test_a_waiting_ticket_cannot_be_resolved_for_free(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        output = terminal.execute_command('trouble resolve ' + major['id'])
        assert 'trouble triage' in output and 'Resolved' not in output
        assert major in terminal.active_tickets
        assert major['status'] == 'OPEN'

    def test_the_queue_cannot_be_emptied_by_resolving_it(self, at_desk):
        terminal = at_desk('noc')
        tickets = put_tickets(terminal, ('MAJOR', 900), ('MINOR', 100),
                              ('CRITICAL', 300))
        for ticket in tickets:
            terminal.execute_command('trouble resolve ' + ticket['id'])
        assert len(terminal.active_tickets) == 3
        assert len(terminal.triage_queue()) == 3

    def test_a_taken_ticket_resolves(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.execute_command('trouble triage ' + major['id'])
        output = terminal.execute_command('trouble resolve ' + major['id'])
        assert 'Resolved' in output
        assert major not in terminal.active_tickets

    def test_a_ticket_somebody_was_given_resolves(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.execute_command(
            f"trouble assign {major['id']} Outside Plant")
        output = terminal.execute_command('trouble resolve ' + major['id'])
        assert 'Resolved' in output

    def test_a_refused_resolve_still_notices_the_lapse(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 60
        terminal.execute_command('trouble resolve ' + major['id'])
        assert major['id'] in terminal.triage_book()['lapsed']
        assert terminal.triage_lapsed() == 1

    def test_the_other_desks_resolve_as_they_always_did(self, at_desk):
        terminal = at_desk('field')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        output = terminal.execute_command('trouble resolve ' + major['id'])
        assert 'Resolved' in output

    def test_a_resume_brings_the_same_pool_back(self, at_desk):
        import json
        terminal = at_desk('noc')
        terminal.execute_command('trouble create MAINTENANCE MAJOR Test')
        fresh = resume_onto_fresh(terminal, 'noc')
        assert ([t['id'] for t in fresh.active_tickets]
                == [t['id'] for t in terminal.active_tickets])
        assert fresh.ticket_counter == terminal.ticket_counter
        for kept, was in zip(fresh.active_tickets, terminal.active_tickets):
            assert kept['created_time'].replace(microsecond=0) == (
                was['created_time'].replace(microsecond=0))
            # A tuple is a list once it has been through the file.
            assert kept['affected_office'] == json.loads(
                json.dumps(was['affected_office']))
            assert kept['status'] == was['status']

    def test_a_window_nearly_out_is_not_reset_by_a_resume(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 25
        fresh = resume_onto_fresh(terminal, 'noc')
        (kept,) = fresh.active_tickets
        assert fresh.triage_due(kept) == 30
        assert fresh.triage_overdue() == []
        fresh.shift_minutes = 31
        assert [t['id'] for t in fresh.triage_overdue()] == [major['id']]

    def test_a_new_ticket_after_a_resume_is_not_born_late(self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MINOR', 100))
        terminal.shift_minutes = 200
        fresh = resume_onto_fresh(terminal, 'noc')
        fresh.execute_command('trouble create MAINTENANCE MAJOR Test')
        entered = fresh.active_tickets[-1]
        assert entered['id'] not in [t['id'] for t in terminal.active_tickets]
        assert fresh.triage_due(entered) == terminal.shift_minutes + 30

    def test_entries_for_tickets_that_are_gone_are_retired(self, at_desk):
        terminal = at_desk('noc')
        gone, kept = put_tickets(terminal, ('MAJOR', 900), ('MINOR', 100))
        terminal.execute_command('trouble triage ' + gone['id'])
        terminal.execute_command('trouble resolve ' + gone['id'])
        assert gone['id'] in terminal.triage_book()['opened']
        fresh = resume_onto_fresh(terminal, 'noc')
        book = fresh.triage_book()
        for key in ('opened', 'klass', 'sig', 'taken', 'lapsed'):
            assert gone['id'] not in book[key], key
        assert gone['id'] not in fresh._assigned_tickets
        # The take still counts toward the tour's running total.
        assert fresh.execute_command('trouble triage').count('taken') >= 1
        assert (len(book['taken']) + book['earlier']['taken']) == 1
        assert kept['id'] in book['opened']

    def test_admitting_a_ticket_clears_what_the_book_held_under_its_number(
            self, at_desk):
        terminal = at_desk('noc')
        (old,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.execute_command('trouble triage ' + old['id'])
        terminal.active_tickets.clear()
        newer = dict(old, title='another', status='OPEN',
                     assigned_team='UNASSIGNED', resolution_steps=[])
        terminal.shift_minutes = 100
        terminal.triage_admit(newer)
        book = terminal.triage_book()
        assert old['id'] not in book['taken']
        assert book['opened'][newer['id']] == 100
        assert book['earlier']['taken'] == 1

    def test_a_damaged_pool_leaves_the_pool_the_session_was_dealt(
            self, at_desk):
        terminal = at_desk('noc')
        for junk in (7, 'x', [{'id': 'TK-1'}], [None]):
            def damage(captured, junk=junk):
                captured['tour']['tickets'] = junk
            fresh = resume_onto_fresh(terminal, 'noc', mutate=damage)
            assert fresh.active_tickets, junk

    def test_a_handoff_before_the_tour_is_out_banks_the_lapses(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 900), ('MINOR', 100))
        terminal.shift_minutes = 14
        assert terminal.triage_lapsed() == 0
        seen = []
        real = terminal.career.service_index

        def banked():
            seen.append(terminal.triage_lapsed())
            return real()

        terminal.career.service_index = banked
        terminal._end_shift()
        assert seen and seen[0] == 2
        assert terminal._relieving == 0

    def test_the_end_of_the_tour_is_counted_only_while_signing_off(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 900))
        terminal.shift_minutes = 14
        assert terminal.tour_minute() == 14
        terminal._end_shift()
        assert terminal.tour_minute() == terminal.shift_minutes


class TestTheNocQueueAcrossAResume:
    """A resumed pool reuses ticket numbers; the book must not be fooled."""

    def test_a_saved_entry_for_a_different_ticket_is_retired(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 5))
        terminal.shift_minutes = 5
        terminal.execute_command('trouble triage ' + major['id'])
        state = terminal.triage_state()
        state['sig'][major['id']] = 'a ticket that was something else|1'
        terminal.shift_minutes = 500
        terminal.restore_triage(state)
        assert major['id'] not in terminal.triage_book()['taken']
        assert terminal.triage_book()['earlier']['taken'] == 1
        assert terminal.triage_book()['opened'][major['id']] == 500
        assert terminal.triage_overdue() == []

    def test_a_saved_entry_for_the_same_ticket_is_kept(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 5))
        terminal.shift_minutes = 5
        terminal.execute_command('trouble triage ' + major['id'])
        terminal.restore_triage(terminal.triage_state())
        assert terminal.triage_book()['taken'] == {major['id']: 5}
        assert terminal.triage_book()['earlier'] == {'taken': 0, 'lapsed': 0}


class TestSartsRepairByRow:

    def test_a_row_past_a_shrunken_board_is_not_an_identifier(self, at_desk):
        terminal = at_desk('sarts')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        board = [c for c in terminal.special_services.listing()
                 if c.status == 'TRBL']
        assert len(board) >= 1
        past = len(board) + 1
        assert past <= len(terminal.special_services.listing())
        said = terminal.execute_command(f'sarts repair {past}')
        assert f'no row {past} on the board' in said
        assert 'Loop-back' not in said

    def test_an_identifier_still_works_whole_or_as_a_zero_led_number(
            self, at_desk):
        terminal = at_desk('sarts')
        terminal.special_services = SartsInventory('NWRKNJ01', random.Random(5))
        first = next(c for c in terminal.special_services.listing()
                     if c.status == 'TRBL')
        said = terminal.execute_command(f'sarts repair {first.circuit_id}')
        assert f'SARTS Loop-back - {first.circuit_id}' in said


class TestTheLeftoversFromPhaseNine:
    """Issue 84: the five that the third round left."""

    def test_trouble_update_cannot_take_a_ticket_out_of_the_queue(
            self, at_desk):
        terminal = at_desk('noc')
        tickets = put_tickets(terminal, ('MAJOR', 900), ('MINOR', 100),
                              ('CRITICAL', 300))
        for ticket, status in zip(tickets,
                                  ('CLOSED', 'RESOLVED', 'IN_PROGRESS')):
            terminal.execute_command(
                f"trouble update {ticket['id']} {status}")
        assert len(terminal.triage_queue()) == 3
        # And so a window still runs on them, with nobody on them.
        terminal.shift_minutes = 500
        terminal.career.shift = 2
        assert terminal.triage_lapsed() == 3

    def test_taking_a_ticket_still_empties_the_queue_of_it(self, at_desk):
        terminal = at_desk('noc')
        (major,) = put_tickets(terminal, ('MAJOR', 900))
        terminal.execute_command('trouble triage ' + major['id'])
        assert terminal.triage_queue() == []

    def test_a_customer_who_gave_up_shows_and_costs_no_rings(self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        terminal._pass_time(65)
        terminal.ring_sweep()
        assert terminal.gave_up(down)
        terminal.patience_book()['told'][down.number] = down.minutes_spent
        terminal._pass_time(65)
        assert terminal.patience(down)[0] == 0
        assert terminal.patience_queue()[0][1] == 0
        row = next(line for line in
                   terminal.execute_command('trouble advise').split('\n')
                   if line.startswith(down.number))
        assert row.split()[2:5] == ['0', 'gave', 'up']
        assert terminal.rings_total() == 3
        before = terminal.shift_minutes
        said = terminal.execute_command('trouble advise ' + down.number)
        assert 'will not ring for' not in said
        spent = terminal.shift_minutes - before
        known = terminal._has_reading(down)
        # The command's own minute on top of the call, and nothing for rings.
        assert spent <= terminal._advise_cost(0, known) + 1
        assert spent < terminal._advise_cost(3, known)

    def test_a_save_missing_a_ticket_field_falls_back_to_the_dealt_pool(
            self, at_desk):
        from bell_system import save
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 900))
        assert 'business_impact' in save.TICKET_KEYS
        for key in save.TICKET_KEYS:
            def damage(captured, key=key):
                del captured['tour']['tickets'][0][key]
            fresh = resume_onto_fresh(terminal, 'noc', mutate=damage)
            assert fresh.active_tickets
            for ticket in fresh.active_tickets:
                for needed in save.TICKET_KEYS:
                    assert needed in ticket, (key, needed)

    def test_the_check_is_every_key_a_ticket_is_made_with(self, at_desk):
        from bell_system import save
        terminal = at_desk('noc')
        (made,) = put_tickets(terminal, ('MAJOR', 900))
        assert set(save.TICKET_KEYS) <= set(made)
        assert set(made) - set(save.TICKET_KEYS) <= {
            'resolution_time', 'actual_duration'}

    def test_the_man_page_says_the_noc_refuses_an_untaken_ticket(self):
        from bell_system.data.man_pages import MAN_PAGES
        text = MAN_PAGES['trouble']
        rows = text.split('\n')
        at = next(i for i, row in enumerate(rows)
                  if row.lstrip().startswith('resolve ID'))
        assert 'taken' in ' '.join(rows[at:at + 2])

    def test_a_late_sarts_clear_is_a_desk_lapse_not_a_commitment(
            self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        base = terminal._tour_worked()[2]
        charged = terminal.career.missed_commitments
        terminal.shift_minutes = OUTAGE_WINDOW + 5
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        assert terminal.desk_overdue() == 1
        # The goal, `shift` and the career screens count commitments only.
        assert terminal._tour_worked()[2] == base
        assert terminal.goal_counts()['missed'] == base
        assert terminal.career.missed_commitments == charged
        shift = terminal.cmd_shift()
        assert f'Missed commitments  {base}' in shift
        assert 'Desk lapses         1' in shift
        assert terminal.desk_lapse_lines() and 'Desk lapses 1' in (
            terminal.desk_lapse_lines()[0])

    def test_a_circuit_cleared_in_time_has_no_desk_lapse(self, at_desk):
        terminal = at_desk('sarts')
        circuit = failing_circuit(terminal, 'OFFICE')
        terminal.execute_command(f'sarts repair {circuit.circuit_id} office')
        assert terminal.desk_overdue() == 0
        assert 'Desk lapses' not in terminal.cmd_shift()
        assert terminal.desk_lapse_lines() == []

    def test_a_lapsed_noc_ticket_is_a_desk_lapse_not_a_commitment(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 900), ('MINOR', 100))
        terminal.career.shift = 2
        base = terminal._tour_worked()[2]
        terminal.shift_minutes = 500
        assert terminal.desk_overdue() == 2
        assert terminal._tour_worked()[2] == base
        assert terminal.goal_counts()['missed'] == base
        assert 'Desk lapses         2' in terminal.cmd_shift()
        assert 'Desk lapses 2' in terminal.desk_lapse_lines()[0]

    def test_an_office_alarm_lapse_is_a_desk_lapse_not_a_commitment(
            self, at_desk):
        terminal = office_desk(at_desk)
        base = terminal._tour_worked()[2]
        terminal.shift_minutes = 10 * LAMP_MINUTES
        assert terminal.desk_overdue() == terminal.alarms_overdue() == 4
        assert terminal._tour_worked()[2] == base
        assert terminal.goal_counts()['missed'] == base
        assert 'Desk lapses         4' in terminal.cmd_shift()
        assert 'Desk lapses 4' in terminal.desk_lapse_lines()[0]

    def test_the_goal_count_is_the_commitments_the_career_counted(
            self, at_desk):
        terminal = at_desk('noc')
        put_tickets(terminal, ('MAJOR', 900))
        terminal.career.shift = 2
        terminal.shift_minutes = 500
        terminal.career.record_missed(2)
        assert terminal.desk_overdue() == 1
        assert terminal.goal_counts()['missed'] == 2
        assert 'Missed commitments  2' in terminal.cmd_shift()
        # The summary's advice is for report misses; desk lapses get a line.
        said = ' '.join(terminal.tour_summary(5, 5, 0, 0))
        assert 'went past' not in said
        assert terminal.desk_lapse_lines()

    def test_a_desk_with_no_window_shows_no_desk_lapses(self, at_desk):
        terminal = at_desk('custserv')
        assert terminal.desk_overdue() == 0
        assert 'Desk lapses' not in terminal.cmd_shift()

    def test_a_customer_who_gave_up_is_not_told_when_they_will_ring(
            self, at_desk):
        terminal = at_desk('custserv')
        (down,) = hold(terminal, (True, 0))
        terminal._pass_time(65)
        terminal.ring_sweep()
        assert terminal.gave_up(down)
        down.field_finding = 'a finding'
        down.dispatched_to = None
        assert terminal._has_reading(down)
        said = terminal.execute_command('trouble advise ' + down.number)
        assert 'will not ring for' not in said
        assert 'written in' in said
