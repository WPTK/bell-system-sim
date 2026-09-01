"""
What is actually different about sitting at one desk rather than another.

Before this, the answer was a home directory and one starting sign-off. The
board was the same twelve ways over, the same people said the same things,
and a planning desk was judged on repair commitments it had no part in.

The rule these tests exist to hold: a desk gets a different MIX of work,
never less of it, and never work whose vocabulary it has not been taught.
"""

import io
import random
import statistics
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime

import pytest

from bell_system.constants import BELL_SYSTEM_ROLES
from bell_system.data.positions import NEUTRAL, POSITIONS, get as get_position
from bell_system.data.trouble import (
    FAULTS,
    NSPMP_WEIGHTS,
    REAL_FAULTS,
)
from bell_system.npc import CRAFT, _CHATTER, _POSITION_CHATTER
from bell_system.reports import MAX_PENDING, OPENING_BACKLOG, ReportDesk
from bell_system.screens.position import _COUNTERS
from bell_system.terminal import BellSystemTerminal

SHIFT_START = datetime(1983, 11, 14, 8, 0)
ROLE_KEYS = [key for key, _ in BELL_SYSTEM_ROLES.values()]


@pytest.fixture
def at_desk(isolated_state):
    """Return a factory that puts a fully qualified terminal at a desk."""
    from bell_system.progression import QUALIFICATIONS

    def put(role_key):
        instance = BellSystemTerminal()
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
    def test_every_desk_gets_tickets(self, at_desk, role):
        _, tickets = self.arrivals(at_desk, role)
        assert tickets >= 1.0, f'{role} hears nothing from the control centre'

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
            for _, sender, _ in pool:
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
        shared = {lines[0][:40] for _, _, lines in _CHATTER}
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
        terminal.desk.dispatch(report, 'Outside plant', terminal.clock.now())
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
        terminal.desk.dispatch(report, 'Outside plant', terminal.clock.now())
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
