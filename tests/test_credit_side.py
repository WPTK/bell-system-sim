"""
The credit side: KPIs, a per-tour index, and commendations.

The service index only ever takes marks off, and it is a rate. These are the
measures and the names that sit beside it. Nothing here uses chance: the
careers are scripted close by close, and the terminal tests put the faults on
the board themselves.
"""

import pytest

from bell_system.data.commendations import (
    COMMENDATIONS, COMMENDATIONS_BY_KEY, MINIMUM_CLOSES, Evidence)
from bell_system.progression import (
    Career, compute_kpis, career_path, score_index)

RELIEVE = 'handoff relieve'
KPI_LABELS = ('Mean time to repair', 'Commitments met',
              'Right first dispatch', 'Repeat rate', 'Backlog age')


def clean_board(terminal):
    """Take every report off the board, so nothing ages into a miss."""
    for report in list(terminal.desk.pending()):
        terminal.desk.discard(report)


def close_clean(career, count, minutes=60):
    """Close ``count`` reports, each measured, matching the line."""
    for _ in range(count):
        career.record_closure(True, minutes, True)


class TestTheFiveKpis:
    """A scripted career gives the expected values, by table."""

    # (closes as (correct, minutes, measured), first dispatches as right?,
    #  repeats, missed, overdue and open now, ages of the open ones, expected)
    CAREERS = [
        pytest.param(
            [(True, 60, True), (True, 120, True), (False, 90, False),
             (True, 150, True), (True, 30, True)],
            [True, True, False, True], 1, 1, 1, [100, 200, 300],
            dict(mttr=90.0, commitments_met=83.3, first_time_right=75.0,
                 repeat_rate=20.0, backlog_age=200.0, provisional=False),
            id='five closes, one of everything'),
        pytest.param(
            [(True, 45, True)] * 4, [True] * 4, 0, 0, 0, [],
            dict(mttr=45.0, commitments_met=100.0, first_time_right=100.0,
                 repeat_rate=0.0, backlog_age=None, provisional=True),
            id='four clean closes are still provisional'),
        pytest.param(
            [], [], 0, 0, 0, [],
            dict(mttr=None, commitments_met=None, first_time_right=None,
                 repeat_rate=None, backlog_age=None, provisional=True),
            id='nothing yet is none yet, not zero and not perfect'),
        pytest.param(
            [(False, 200, False)] * 2, [False, False], 2, 2, 3, [50, 70, 90],
            dict(mttr=200.0, commitments_met=60.0, first_time_right=0.0,
                 repeat_rate=100.0, backlog_age=70.0, provisional=True),
            id='a board left to age counts against the commitments'),
    ]

    @pytest.mark.parametrize(
        'closes, dispatches, repeats, missed, overdue, ages, expected',
        CAREERS)
    def test_the_career_reads_back_what_was_scripted(
            self, closes, dispatches, repeats, missed, overdue, ages,
            expected):
        career = Career()
        career.open_overdue = lambda: overdue
        career.open_ages = lambda: ages
        for correct, minutes, measured in closes:
            career.record_closure(correct, minutes, measured)
        for right in dispatches:
            career.record_dispatch(right)
        for _ in range(repeats):
            career.record_repeat()
        career.record_missed(missed)

        found = career.kpis()._asdict()
        found.pop('closed')
        assert found == expected

    def test_one_function_measures_the_career_and_a_tour(self):
        counts = {'closed': 10, 'repeats': 1, 'missed': 2, 'repairs': 10,
                  'repair_minutes': 600, 'dispatches': 8,
                  'dispatches_right': 6}
        kpis = compute_kpis(counts, backlog=0, ages=[])
        assert (kpis.mttr, kpis.commitments_met, kpis.first_time_right,
                kpis.repeat_rate) == (60.0, 80.0, 75.0, 10.0)

    def test_a_miss_is_never_more_than_the_reports_decided(self):
        kpis = compute_kpis({'closed': 2, 'missed': 9}, backlog=0, ages=[])
        assert kpis.commitments_met == 0.0

    def test_the_fun_setting_counts_a_miss_softly_but_reports_it_whole(self):
        """Assists change what a miss costs the index, not what happened."""
        fun, craft = Career(difficulty='fun'), Career(difficulty='craft')
        for career in (fun, craft):
            close_clean(career, 5)
            career.record_missed(1)
        assert fun.kpis().commitments_met == craft.kpis().commitments_met
        assert fun.service_index() > craft.service_index()


class TestTheTourOnItsOwn:
    """A per-tour index beside the cumulative one."""

    def test_a_bad_tour_after_a_good_record_shows_in_its_own_index(self):
        career = Career()
        close_clean(career, 20)
        career.end_shift()
        for correct in (True, False, False, True, True):
            career.record_closure(correct, 60, True)
        career.end_shift()

        penalty = career.difficulty
        assert career.tour_index_history == [
            100.0, score_index(5, 2, 0, 0, 0, penalty)]
        assert career.index_history == [
            100.0, score_index(25, 2, 0, 0, 0, penalty)]
        assert career.tour_index_history[1] < career.index_history[1]

    def test_the_next_tour_starts_from_nothing(self):
        career = Career()
        close_clean(career, 6)
        career.end_shift()
        assert career.tour_counts()['closed'] == 0
        assert career.tour_kpis().mttr is None
        assert not career.tour_scored()

    def test_the_label_reads_provisional_until_five_closes(self):
        career = Career()
        for closed in range(1, 8):
            career.record_closure(True, 60, True)
            assert career.tour_provisional() is (closed < MINIMUM_CLOSES)
            assert career.kpis().provisional is (closed < MINIMUM_CLOSES)

    def test_a_tour_nobody_closed_or_let_go_late_banks_no_index(self):
        career = Career()
        career.end_shift()
        assert career.tour_index_history == []

    def test_the_tour_figures_survive_a_session_that_ends_mid_tour(
            self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path)
        close_clean(career, 3)
        career.end_shift()
        close_clean(career, 2, minutes=30)
        again = Career(path)
        assert again.tour_counts()['closed'] == 2
        assert again.tour_kpis().mttr == 30.0
        assert again.kpis().mttr == 48.0
        assert again.tour_index_history == career.tour_index_history

    def test_a_record_from_before_the_marks_starts_its_tour_where_it_is(
            self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            handle.write('{"shift": 6, "reports_closed": 40, '
                         '"reports_correct": 38, "reports_wrong": 2}')
        career = Career(path)
        assert career.tour_counts()['closed'] == 0
        assert career.kpis().closed == 40


class TestCommendations:
    """Named, earned, never lost, and never for volume or for a guess."""

    def test_a_perfect_tour_earns_first_clean_tour_once(self):
        career = Career()
        close_clean(career, 5)
        assert 'first_clean_tour' in career.end_shift()
        assert career.commendations.count('first_clean_tour') == 1
        close_clean(career, 6)
        again = career.end_shift()
        assert 'first_clean_tour' not in again
        assert career.commendations.count('first_clean_tour') == 1

    def test_a_tour_of_one_proves_nothing(self):
        career = Career()
        close_clean(career, MINIMUM_CLOSES - 1)
        assert career.end_shift() == []
        assert career.commendations == []

    def test_volume_alone_earns_nothing(self):
        """Thirty-two closes with two wrong, and some left late."""
        career = Career()
        for number in range(32):
            career.record_closure(number not in (7, 20), 60, True)
        career.record_missed(3)
        # A run of five correct closes is accuracy, and is the only thing
        # in thirty-two that earns a name.
        assert set(career.end_shift()) == {'five_straight'}

    def test_guessing_earns_nothing(self):
        """Closing every report fast, unmeasured and wrong, in volume."""
        career = Career()
        for _ in range(40):
            career.record_closure(False, 5, False)
            career.record_dispatch(False)
        assert career.end_shift() == []

    def test_a_late_report_left_open_spoils_the_tour(self):
        career = Career()
        career.open_overdue = lambda: 1
        close_clean(career, 6)
        assert 'first_clean_tour' not in career.end_shift()

    def test_a_miss_or_a_repeat_spoils_the_tour(self):
        for spoil in ('record_missed', 'record_repeat'):
            career = Career()
            close_clean(career, 6)
            getattr(career, spoil)()
            assert 'first_clean_tour' not in career.end_shift(), spoil

    def test_one_is_never_lost_to_a_bad_tour_after(self):
        career = Career()
        close_clean(career, 5)
        career.end_shift()
        held = list(career.commendations)
        for _ in range(10):
            career.record_closure(False, 400, False)
        career.record_missed(10)
        career.end_shift()
        assert career.commendations[:len(held)] == held

    def test_five_correct_in_a_row_across_a_tour_boundary(self):
        career = Career()
        close_clean(career, 3)
        career.end_shift()
        close_clean(career, 1)
        assert 'five_straight' not in career.commendations
        close_clean(career, 1)
        assert 'five_straight' in career.commendations

    def test_a_wrong_close_breaks_the_run(self):
        career = Career()
        close_clean(career, 4)
        career.record_closure(False, 60, True)
        close_clean(career, 4)
        assert 'five_straight' not in career.commendations

    def test_right_first_time_asks_for_every_first_dispatch(self):
        career = Career()
        for _ in range(MINIMUM_CLOSES):
            career.record_dispatch(True)
        assert 'right_first_time' in career.end_shift()
        other = Career()
        for right in (True, True, True, True, False):
            other.record_dispatch(right)
        assert 'right_first_time' not in other.end_shift()

    def test_one_trip_two_lines(self):
        career = Career()
        career.record_dispatch(True, cleared_by_one_trip=0)
        assert 'one_trip' not in career.commendations
        career.record_dispatch(True, cleared_by_one_trip=2)
        assert 'one_trip' in career.commendations

    def test_every_line_measured_needs_them_right_as_well(self):
        career = Career()
        close_clean(career, 5)
        career.record_closure(False, 60, True)
        assert 'every_line_measured' not in career.end_shift()

    def test_they_round_trip_and_an_unknown_one_is_kept(self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path)
        close_clean(career, 5)
        career.end_shift()
        career.commendations.append('from_a_later_version')
        career.save()
        again = Career(path)
        assert again.commendations == career.commendations
        assert 'first_clean_tour' in again.commendations

    def test_every_commendation_is_named_and_unique(self):
        keys = [commendation.key for commendation in COMMENDATIONS]
        assert len(keys) == len(set(keys)) == len(COMMENDATIONS_BY_KEY)
        for commendation in COMMENDATIONS:
            assert commendation.name and commendation.description
            assert commendation.when in ('close', 'dispatch', 'tour')

    def test_none_is_earned_by_an_empty_record(self):
        nothing = Evidence(*([0] * len(Evidence._fields)))
        assert not [c for c in COMMENDATIONS if c.test(nothing)]


class TestTheTerminal:
    """What the player sees: qual, the handoff preview and the sign-off."""

    def test_qual_shows_the_five_kpis_and_the_tour_index(self, terminal):
        text = terminal.execute_command('qual')
        for label in KPI_LABELS:
            assert label in text, label
        assert 'Tour index' in text
        assert 'Board cleared' in text
        assert 'COMMENDATIONS' in text

    def test_qual_says_provisional_until_five_closes(self, terminal):
        clean_board(terminal)
        close_clean(terminal.career, MINIMUM_CLOSES - 1)
        assert 'PROVISIONAL' in terminal.execute_command('qual')
        close_clean(terminal.career, 1)
        assert 'PROVISIONAL' not in terminal.execute_command('qual')

    def test_qual_lists_every_commendation_and_marks_the_held(self, terminal):
        clean_board(terminal)
        close_clean(terminal.career, 5)
        terminal.execute_command('report')
        terminal.execute_command(RELIEVE)
        text = terminal.execute_command('qual')
        for commendation in COMMENDATIONS:
            assert commendation.name in text
        assert '[x] First clean tour' in text
        assert '[ ] One trip, two lines' in text

    def test_the_handoff_prints_what_the_tour_earned(self, terminal):
        clean_board(terminal)
        close_clean(terminal.career, 5)
        text = terminal.execute_command(RELIEVE)
        assert 'COMMENDATIONS EARNED THIS TOUR' in text
        assert 'First clean tour' in text
        assert 'TOUR CREDIT' in text

    def test_and_does_not_print_it_a_second_time(self, terminal):
        clean_board(terminal)
        close_clean(terminal.career, 5)
        terminal.execute_command(RELIEVE)
        clean_board(terminal)
        close_clean(terminal.career, 5)
        text = terminal.execute_command(RELIEVE)
        assert 'First clean tour' not in text

    def test_a_dirty_tour_prints_no_commendation_section(self, terminal):
        clean_board(terminal)
        for correct in (True, False, True, True, True):
            terminal.career.record_closure(correct, 60, True)
        text = terminal.execute_command(RELIEVE)
        assert 'COMMENDATIONS EARNED' not in text

    def test_the_preview_shows_the_credit_before_you_sign(self, terminal):
        clean_board(terminal)
        close_clean(terminal.career, 3)
        text = terminal.execute_command('handoff')
        assert 'TOUR CREDIT' in text
        assert 'PROVISIONAL (3 of 5 closes)' in text

    def test_the_meter_shows_the_board_not_just_the_rate(self, terminal):
        """Five perfect closes of twelve are not five of five."""
        clean_board(terminal)
        close_clean(terminal.career, 5)
        for _ in range(7):
            terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        assert '5 of 12' in terminal.board_meter()
        clean_board(terminal)
        assert '5 of 5' in terminal.board_meter()

    def test_a_dispatch_and_a_close_feed_the_kpis(self, terminal):
        clean_board(terminal)
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        number = report.number
        terminal.execute_command(f'mlt {number}')
        terminal.execute_command(f'report dispatch {number} outside')
        terminal.execute_command(f'report close {number} 5 OPEN')
        career = terminal.career
        assert career.kpi['dispatches'] == 1
        assert career.kpi['dispatches_right'] == 1
        assert career.kpi['measured'] == 1
        assert career.kpis().mttr == float(report.minutes_spent)
        assert career.kpis().first_time_right == 100.0

    def test_a_wrong_force_first_is_the_judgement_and_a_retry_is_not(
            self, terminal):
        clean_board(terminal)
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} cable')
        terminal.execute_command(f'report dispatch {report.number} outside')
        assert terminal.career.kpi['dispatches'] == 1
        assert terminal.career.kpi.get('dispatches_right', 0) == 0

    def test_the_board_ages_are_the_customers_not_a_practical(self, terminal):
        clean_board(terminal)
        terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        assert len(terminal.career.open_ages()) == 1
