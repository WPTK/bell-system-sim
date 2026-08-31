"""
Difficulty, qualification and the service index.

These cover what a player actually experiences moving between the two ways of
working a shift: what each difficulty permits, what qualification gates, and
how a wrong close out scores.
"""

import json

import pytest

from bell_system.data.trouble import NSPMP_WEIGHTS
from bell_system.progression import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    MISSED_COMMITMENT_WEIGHT,
    REPEAT_REPORT_WEIGHT,
    WRONG_DISPOSITION_WEIGHT,
    QUALIFICATIONS,
    QUALIFICATIONS_BY_KEY,
    ROLE_QUALIFICATIONS,
    Career,
    career_path,
)
from bell_system.settings import OPTIONS_BY_KEY


class TestDifficulties:
    """The two ways of working a shift."""

    def test_both_difficulties_exist_and_are_named(self):
        assert DIFFICULTIES['fun'].name == 'Fun Simulation'
        assert DIFFICULTIES['craft'].name == 'I Hate Myself'

    def test_default_is_the_forgiving_one(self):
        assert DEFAULT_DIFFICULTY == 'fun'
        assert OPTIONS_BY_KEY['game.difficulty'].default == 'fun'

    def test_the_setting_offers_exactly_the_two(self):
        assert OPTIONS_BY_KEY['game.difficulty'].choices == ['fun', 'craft']

    @pytest.mark.parametrize('field,harder', [
        ('repeat_report_chance', 'greater'),
        ('reports_per_qualification', 'greater'),
        ('index_penalty', 'greater'),
        ('interruption_rate', 'greater'),
    ])
    def test_craft_is_harder_on_every_axis(self, field, harder):
        assert harder == 'greater'
        assert getattr(DIFFICULTIES['craft'], field) > \
            getattr(DIFFICULTIES['fun'], field)

    def test_only_craft_requires_a_measurement_before_close(self):
        assert DIFFICULTIES['craft'].require_test_before_close
        assert not DIFFICULTIES['fun'].require_test_before_close

    def test_only_craft_counts_missed_commitments(self):
        assert DIFFICULTIES['craft'].count_missed_commitments
        assert not DIFFICULTIES['fun'].count_missed_commitments

    def test_only_fun_gives_slack_on_commitments(self):
        assert DIFFICULTIES['fun'].commitment_slack_minutes > 0
        assert DIFFICULTIES['craft'].commitment_slack_minutes == 0


class TestQualifications:
    """What a craftsperson is signed off to work on."""

    def test_a_new_career_holds_only_the_loop(self):
        assert Career().qualifications == ['loop']

    def test_every_qualification_unlocks_something(self):
        for qualification in QUALIFICATIONS:
            assert qualification.unlocks

    def test_no_command_is_unlocked_by_two_qualifications(self):
        seen = set()
        for qualification in QUALIFICATIONS:
            for command in qualification.unlocks:
                assert command not in seen, f'{command} unlocked twice'
                seen.add(command)

    def test_requirements_only_ever_increase(self):
        needed = [q.requires_reports for q in QUALIFICATIONS]
        assert needed == sorted(needed)

    def test_an_unheld_command_is_refused(self):
        career = Career()
        assert career.may_use('mlt')
        assert not career.may_use('tnds')

    def test_an_ungated_command_is_always_allowed(self):
        assert Career().may_use('help')
        assert Career().may_use('ls')

    def test_correct_closures_earn_the_next_sign_off(self):
        career = Career(difficulty='fun')
        threshold = DIFFICULTIES['fun'].reports_per_qualification
        for _ in range(threshold):
            career.record_closure(correct=True)
        granted = career.grant_available()
        assert 'frame' in [q.key for q in granted]
        assert career.may_use('cosmos')

    def test_wrong_closures_earn_nothing(self):
        career = Career(difficulty='fun')
        for _ in range(20):
            career.record_closure(correct=False)
        assert career.grant_available() == []
        assert not career.may_use('cosmos')

    def test_craft_needs_far_more_closures_than_fun(self):
        fun = Career(difficulty='fun')
        craft = Career(difficulty='craft')
        assert craft.reports_until_next() > fun.reports_until_next()

    def test_every_role_qualification_is_a_real_one(self):
        for key in ROLE_QUALIFICATIONS.values():
            assert key in QUALIFICATIONS_BY_KEY


class TestServiceIndex:
    """Scoring against the published measurement weights."""

    def test_an_untouched_record_scores_full_marks(self):
        career = Career()
        assert career.service_index() == 100.0
        assert career.index_band() == 'EXCELLENT'

    def test_a_wrong_close_costs_more_on_craft_than_on_fun(self):
        scores = {}
        for key in ('fun', 'craft'):
            career = Career(difficulty=key)
            career.record_closure(correct=False)
            scores[key] = career.service_index()
        assert scores['craft'] < scores['fun']

    def test_repeats_tell_against_the_index(self):
        without = Career(difficulty='craft')
        without.record_closure(correct=True)

        with_repeat = Career(difficulty='craft')
        with_repeat.record_closure(correct=True)
        with_repeat.record_repeat()

        assert with_repeat.service_index() < without.service_index()

    def test_missed_commitments_only_count_on_craft(self):
        fun = Career(difficulty='fun')
        fun.record_closure(correct=True, missed_commitment=True)
        assert fun.service_index() == 100.0

        craft = Career(difficulty='craft')
        craft.record_closure(correct=True, missed_commitment=True)
        assert craft.service_index() < 100.0

    def test_total_failure_actually_reaches_unsatisfactory(self):
        """
        The whole point of scoring the component out of 100.

        Scored across the plan's full hundred, closing every report wrongly
        could cost only the ten points customer reports carried, leaving a
        catastrophic shift reading in the eighties.
        """
        career = Career(difficulty='craft')
        assert career.index_band() == 'EXCELLENT'
        for _ in range(40):
            career.record_closure(correct=False)
            career.record_repeat()
        assert career.service_index() < 30
        assert career.index_band() == 'UNSATISFACTORY'

    def test_a_perfect_board_scores_full_marks_on_either_setting(self):
        for key in ('fun', 'craft'):
            career = Career(difficulty=key)
            for _ in range(30):
                career.record_closure(correct=True)
            assert career.service_index() == 100.0

    def test_the_office_contribution_is_the_published_weight(self):
        career = Career()
        assert career.office_contribution() == \
            NSPMP_WEIGHTS['customer_reports']

    def test_the_office_contribution_tracks_the_score(self):
        career = Career(difficulty='craft')
        for _ in range(10):
            career.record_closure(correct=False)
        expected = round(NSPMP_WEIGHTS['customer_reports']
                         * career.service_index() / 100, 1)
        assert career.office_contribution() == expected

    def test_a_wrong_close_costs_more_than_a_repeat(self):
        wrong = Career(difficulty='craft')
        for _ in range(10):
            wrong.record_closure(correct=False)

        repeats = Career(difficulty='craft')
        for _ in range(10):
            repeats.record_closure(correct=True)
            repeats.record_repeat()

        assert wrong.service_index() < repeats.service_index()

    def test_the_three_penalty_weights_are_ordered_as_documented(self):
        assert WRONG_DISPOSITION_WEIGHT > REPEAT_REPORT_WEIGHT
        assert REPEAT_REPORT_WEIGHT > MISSED_COMMITMENT_WEIGHT


class TestPersistence:
    """A career must survive the shift and a damaged file."""

    def test_a_career_round_trips_through_disk(self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path, difficulty='craft')
        career.record_closure(correct=True)
        career.record_repeat()
        career.qualifications.append('frame')
        career.save()

        restored = Career(path)
        assert restored.difficulty_key == 'craft'
        assert restored.reports_closed == 1
        assert restored.repeat_reports == 1
        assert 'frame' in restored.qualifications

    def test_a_corrupt_file_does_not_stop_a_shift(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            handle.write('{not json at all')
        career = Career(path)
        assert career.qualifications == ['loop']
        assert career.reports_closed == 0

    def test_an_unknown_qualification_on_disk_is_discarded(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({'qualifications': ['loop', 'warp_drive']}, handle)
        assert Career(path).qualifications == ['loop']

    def test_ending_a_shift_banks_the_index(self, tmp_path):
        career = Career(career_path(str(tmp_path)))
        career.record_closure(correct=True)
        career.end_shift()
        assert career.shift == 2
        assert career.index_history == [100.0]


class TestQualificationGating:
    """The terminal refuses what the craftsperson is not signed off on."""

    def test_an_unqualified_command_is_refused_by_a_person(self, raw_terminal):
        result = raw_terminal.execute_command('tnds')
        assert 'not signed off' in result
        assert 'Toll Network' in result

    def test_the_refusal_says_how_far_off_it_is(self, raw_terminal):
        result = raw_terminal.execute_command('cosmos')
        assert 'Correct closures still needed' in result

    def test_a_qualified_command_runs(self, raw_terminal):
        result = raw_terminal.execute_command('report')
        assert 'Repair Service Bureau' in result

    def test_selecting_a_role_signs_you_off_for_that_desk(self, raw_terminal):
        assert not raw_terminal.career.is_qualified('toll')
        raw_terminal._apply_role('tnds', 'TNDS Analyst')
        assert raw_terminal.career.is_qualified('toll')
        assert 'not signed off' not in raw_terminal.execute_command('tnds')

    def test_changing_difficulty_reaches_the_career(self, raw_terminal):
        raw_terminal.execute_command('set game.difficulty craft')
        assert raw_terminal.career.difficulty_key == 'craft'
        assert raw_terminal.career.difficulty.require_test_before_close

    def test_the_craft_record_renders(self, raw_terminal):
        result = raw_terminal.execute_command('qual')
        assert 'Craft Record' in result
        assert 'Fun Simulation' in result
        for qualification in QUALIFICATIONS:
            assert qualification.name in result

    def test_the_index_screen_shows_the_published_weights(self, raw_terminal):
        result = raw_terminal.execute_command('qual index')
        assert 'Customer Reports' in result
        assert '100' in result

    def test_the_index_screen_separates_the_two_numbers(self, raw_terminal):
        result = raw_terminal.execute_command('qual index')
        assert 'of 100' in result
        assert 'Worth to the office' in result
