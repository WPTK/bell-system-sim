"""
Difficulty, qualification and the service index.

These cover what a player actually experiences moving between the two ways of
working a shift: what each difficulty permits, what qualification gates, and
how a wrong close out scores.
"""

import importlib
import json
import os

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

    def test_craft_counts_missed_commitments_in_full_and_fun_softly(self):
        assert DIFFICULTIES['craft'].missed_commitment_scale == 1.0
        assert 0 < DIFFICULTIES['fun'].missed_commitment_scale < 1.0

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

    def test_correct_closures_offer_the_next_sign_off_and_a_practical_gives_it(
            self):
        career = Career(difficulty='fun')
        threshold = DIFFICULTIES['fun'].reports_per_qualification
        for _ in range(threshold):
            career.record_closure(correct=True)
        assert 'frame' in [q.key for q in career.offer_available()]
        assert not career.may_use('cosmos')
        assert career.pass_practical('frame').key == 'frame'
        assert career.may_use('cosmos')
        assert career.practicals_passed == ['frame']

    def test_wrong_closures_earn_nothing(self):
        career = Career(difficulty='fun')
        for _ in range(20):
            career.record_closure(correct=False)
        assert career.offer_available() == []
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

    def test_missed_commitments_count_softly_on_fun_and_fully_on_craft(self):
        fun = Career(difficulty='fun')
        fun.record_closure(correct=True)
        fun.record_missed()
        craft = Career(difficulty='craft')
        craft.record_closure(correct=True)
        craft.record_missed()
        assert craft.service_index() < fun.service_index() < 100.0

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


class TestHelpAndBriefing:
    """The on-ramp: what a new craftsperson is told there is to do."""

    def test_every_role_command_actually_exists(self, terminal):
        """
        This list once named two commands that had never been implemented.
        """
        from bell_system.terminal import BellSystemTerminal
        for role, commands in BellSystemTerminal.ROLE_COMMANDS.items():
            for command in commands:
                assert command in terminal._command_handlers, \
                    f'{role} help lists {command}, which does not exist'

    def test_every_help_command_has_a_manual_page(self, terminal):
        from bell_system.terminal import BellSystemTerminal
        listed = set()
        for commands in BellSystemTerminal.ROLE_COMMANDS.values():
            listed.update(commands)
        for name, _ in BellSystemTerminal.BUREAU_COMMANDS:
            listed.add(name)
        for name, _ in BellSystemTerminal.PEOPLE_COMMANDS:
            listed.add(name)
        undocumented = sorted(listed - set(terminal.man_pages))
        assert not undocumented, f'no manual page for {undocumented}'

    def test_help_leads_with_the_work(self, raw_terminal):
        result = raw_terminal.execute_command('help')
        assert 'THE WORK' in result
        assert 'report' in result
        assert 'trouble report(s) on your board' in result

    def test_help_marks_what_is_not_signed_off(self, raw_terminal):
        result = raw_terminal.execute_command('help')
        assert '*testcall' in result
        assert 'not signed off on' in result.lower()

    def test_help_stops_marking_once_qualified(self, terminal):
        result = terminal.execute_command('help')
        assert '*' not in result.split('THE SYSTEM')[0]

    def test_help_on_one_command_summarises_it(self, terminal):
        result = terminal.execute_command('help mlt')
        assert 'mechanised loop testing' in result
        assert 'man mlt' in result

    def test_help_on_a_locked_command_says_so(self, raw_terminal):
        result = raw_terminal.execute_command('help tnds')
        assert 'not signed off' in result
        assert 'Toll Network' in result

    def test_help_resolves_an_alias(self, terminal):
        assert 'No help available' not in terminal.execute_command('help board')

    def test_help_on_a_stranger_says_so(self, terminal):
        assert 'No help available' in terminal.execute_command('help frobnicate')

    def test_the_briefing_shows_the_board(self, raw_terminal, capsys):
        raw_terminal._apply_role('field', 'Field Support Liaison')
        raw_terminal.show_shift_briefing()
        printed = capsys.readouterr().out
        assert 'Repair Service Bureau' in printed
        assert 'Reports on your board' in printed
        assert 'Service index' in printed
        assert 'Fun Simulation' in printed

    def test_the_briefing_offers_the_harder_setting_on_a_first_shift(
            self, raw_terminal, capsys):
        raw_terminal._apply_role('field', 'Field Support Liaison')
        raw_terminal.show_shift_briefing()
        assert 'game.difficulty craft' in capsys.readouterr().out

    def test_the_briefing_stops_offering_it_once_you_have_worked(
            self, raw_terminal, capsys):
        raw_terminal.career.reports_closed = 5
        raw_terminal._apply_role('field', 'Field Support Liaison')
        raw_terminal.show_shift_briefing()
        assert 'game.difficulty craft' not in capsys.readouterr().out

class TestFirstTour:
    """
    The tutorial is the first tour, not a mode you run beforehand.

    There was a --tutorial flag and a five-hundred-line script behind it
    that walked a radio desk through commands in a terminal that was not
    the game. It is gone. What replaced it is the wire chief on write(1),
    one message per step of the loop, on the board you actually work.
    """

    def _fresh(self, raw_terminal):
        raw_terminal.career.shift = 1
        raw_terminal.career.reports_closed = 0
        raw_terminal._tour_nudges.clear()
        return raw_terminal

    def _one_report(self, terminal):
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=1)

    def test_the_first_board_holds_one_report(self, raw_terminal):
        terminal = self._fresh(raw_terminal)
        self._one_report(terminal)
        assert len(terminal.desk.pending()) == 1

    def test_the_board_does_not_fill_during_a_first_tour(self, raw_terminal):
        """The chief says he is holding the rest off. He has to mean it."""
        terminal = self._fresh(raw_terminal)
        self._one_report(terminal)
        for _ in range(200):
            terminal.execute_command('pwd')
        assert len(terminal.desk.pending()) == 1

    def test_every_step_of_the_loop_has_something_to_say(self):
        from bell_system.screens.guidance import FIRST_TOUR
        assert set(FIRST_TOUR) == {'open', 'board', 'measure', 'dispatch',
                                   'closed'}

    def test_each_step_speaks_once(self, raw_terminal):
        terminal = self._fresh(raw_terminal)
        assert terminal.first_tour_nudge('board') is not None
        assert terminal.first_tour_nudge('board') is None

    def test_the_chief_is_silent_after_the_first_tour(self, raw_terminal):
        terminal = self._fresh(raw_terminal)
        terminal.career.shift = 2
        assert terminal.first_tour_nudge('board') is None

    def test_the_parting_line_survives_the_first_closure(self, raw_terminal):
        """
        Every other step is gated on nothing being closed yet. The last one
        is said on the way out of the first closure, so it needs the one
        closure of slack that `after_close` gives it.
        """
        terminal = self._fresh(raw_terminal)
        terminal.career.reports_closed = 1
        assert terminal.first_tour_nudge('measure') is None
        assert terminal.first_tour_nudge('closed') is not None

    def test_the_standing_prompt_keeps_out_of_the_way(self, raw_terminal):
        """Two voices saying what to do next is one too many."""
        terminal = self._fresh(raw_terminal)
        assert 'Next:' not in terminal._add_guidance('', 'pwd')

    def test_the_flag_is_gone(self):
        from bell_system.cli import build_parser
        options = {action.dest for action in build_parser()._actions}
        assert 'tutorial' not in options

    def test_the_module_is_gone(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module('bell_system.tutorial')


class TestCareerSchema:
    """One schema bump carries every field later work wants to keep."""

    NEW_LISTS = ('commendations', 'finds', 'groups', 'beats_seen',
                 'practicals_passed')
    NEW_COUNTS = ('fault_sightings', 'rapport')

    def test_a_record_from_before_the_bump_loads_with_defaults(self, tmp_path):
        """The file the current version writes, which has no schema key."""
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({
                'difficulty': 'craft', 'shift': 5, 'reports_closed': 40,
                'reports_correct': 33, 'reports_wrong': 7,
                'repeat_reports': 2, 'missed_commitments': 3,
                'qualifications': ['loop', 'frame', 'office'],
                'index_history': [91.0, 94.5], 'office': {'clli': 'X'},
                'finished': False,
            }, handle)
        career = Career(path)
        assert (career.shift, career.reports_closed) == (5, 40)
        assert career.qualifications == ['loop', 'frame', 'office']
        for field in self.NEW_LISTS:
            assert getattr(career, field) == [], field
        for field in self.NEW_COUNTS:
            assert getattr(career, field) == {}, field
        assert career.assignment == ''

    def test_the_new_fields_round_trip(self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path)
        career.fault_sightings = {'OPEN': 3, 'WET': 1}
        career.commendations = ['first clean tour']
        career.finds = ['sulog', 'drawer']
        career.groups = ['craft', 'adm']
        career.rapport = {'mreyes': 2}
        career.beats_seen = ['t2-sandoval']
        career.practicals_passed = ['frame']
        career.assignment = 'somewhere'
        career.save()

        again = Career(path)
        assert again.fault_sightings == {'OPEN': 3, 'WET': 1}
        assert again.commendations == ['first clean tour']
        assert again.finds == ['sulog', 'drawer']
        assert again.groups == ['craft', 'adm']
        assert again.rapport == {'mreyes': 2}
        assert again.beats_seen == ['t2-sandoval']
        assert again.practicals_passed == ['frame']
        assert again.assignment == 'somewhere'

    def test_the_file_says_which_schema_wrote_it(self, tmp_path):
        from bell_system.progression import SCHEMA
        path = career_path(str(tmp_path))
        Career(path).save()
        with open(path) as handle:
            assert json.load(handle)['schema'] == SCHEMA

    def test_a_file_from_a_later_schema_still_loads(self, tmp_path):
        """Unknown keys are ignored, as they were before the bump."""
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({'schema': 99, 'shift': 4, 'from_the_future': [1]},
                      handle)
        assert Career(path).shift == 4

    def test_damaged_new_fields_fall_back_one_by_one(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({
                'shift': 3,
                'finds': 'not a list',
                'commendations': ['ok', 7, 'ok', None, 'also'],
                'fault_sightings': {'OPEN': 2, 'WET': -4, 'FCG': 'x',
                                    'ROH': True},
                'rapport': [1, 2],
                'practicals_passed': ['loop', 'warp_drive'],
                'assignment': 12,
            }, handle)
        career = Career(path)
        assert career.shift == 3
        assert career.finds == []
        assert career.commendations == ['ok', 'also']
        assert career.fault_sightings == {'OPEN': 2, 'WET': 0}
        assert career.rapport == {}
        assert career.practicals_passed == ['loop']
        assert career.assignment == ''

    def test_a_career_never_shares_its_lists(self):
        first, second = Career(), Career()
        first.finds.append('x')
        first.fault_sightings['OPEN'] = 1
        assert second.finds == [] and second.fault_sightings == {}

    def test_the_count_floor_is_offered_before_it_is_granted(self, tmp_path):
        career = Career(career_path(str(tmp_path)), difficulty='fun')
        career.reports_correct = 3
        assert [q.key for q in career.offer_available()] == ['frame']
        assert career.qualifications == ['loop']
        assert career.pass_practical('frame') is not None
        assert 'frame' in career.qualifications
        assert career.pass_practical('frame') is None
        assert career.pass_practical('nonesuch') is None

    def test_a_practical_passed_stands_if_the_count_moves_under_it(
            self, tmp_path):
        career = Career(career_path(str(tmp_path)), difficulty='fun')
        career.reports_correct = 3
        assert [q.key for q in career.offer_available()] == ['frame']
        career.set_difficulty('craft')
        assert career.offer_available() == []
        assert career.pass_practical('frame').key == 'frame'
        assert career.practicals_passed == ['frame']

    def test_the_offer_is_remembered_on_the_record(self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path, difficulty='fun')
        career.offered.append('frame')
        career.save()
        assert Career(path).offered == ['frame']


class TestAssistsApplyToTheCareer:
    def test_an_override_changes_the_count_floor(self, tmp_path):
        career = Career(career_path(str(tmp_path)), difficulty='fun')
        career.reports_correct = 3
        assert [q.key for q in career.offer_available()] == ['frame']
        career.set_assists({'reports_per_qualification': 12})
        assert career.offer_available() == []
        assert career.reports_until_next() == 9

    def test_an_unknown_field_is_ignored(self):
        career = Career()
        career.set_assists({'warp_factor': 9})
        assert career.difficulty == DIFFICULTIES[DEFAULT_DIFFICULTY]


class TestWhatQualificationClaims:
    """The ladder is the simulation's own and the documents say so."""

    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def read(self, name):
        with open(os.path.join(self.ROOT, name), encoding='utf-8') as handle:
            return handle.read()

    def test_the_readme_does_not_say_qualification_governed_the_job(self):
        readme = self.read('README.md')
        assert 'was governed by qualification' not in readme
        ladder = readme.split('A career, and its last day')[1][:900]
        assert "simulation's own" in ladder

    def test_the_progression_module_does_not_either(self):
        import bell_system.progression as module
        assert 'actually governed' not in module.__doc__

    def test_sources_records_the_close_code_simplification(self):
        sources = self.read('SOURCES.md')
        assert 'code 5' in sources and 'code 8' in sources
        assert 'simplification' in sources.lower()


class TestACareerKeepsWhatItDoesNotKnow:
    def test_a_later_versions_keys_survive_a_save(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({'schema': 99, 'shift': 4, 'from_the_future': {'a': [1]},
                       'qualifications': ['loop', 'warp'],
                       'practicals_passed': ['loop', 'warp_drive']}, handle)
        career = Career(path)
        assert career.qualifications == ['loop']
        assert career.practicals_passed == ['loop']
        career.record_closure(True)
        with open(path) as handle:
            written = json.load(handle)
        assert written['from_the_future'] == {'a': [1]}
        assert written['schema'] == 99
        assert written['qualifications'] == ['loop', 'warp']
        assert written['practicals_passed'] == ['loop', 'warp_drive']
        assert written['reports_closed'] == 1

    def test_this_versions_own_schema_is_what_it_writes(self, tmp_path):
        from bell_system.progression import SCHEMA
        path = career_path(str(tmp_path))
        Career(path).save()
        with open(path) as handle:
            assert json.load(handle)['schema'] == SCHEMA

    def test_what_it_does_know_is_not_held_back_as_unknown(self, tmp_path):
        path = career_path(str(tmp_path))
        career = Career(path)
        career.qualifications.append('frame')
        career.practicals_passed.append('frame')
        career.save()
        again = Career(path)
        again.save()
        with open(path) as handle:
            written = json.load(handle)
        assert written['qualifications'] == ['loop', 'frame']
        assert written['practicals_passed'] == ['frame']


class TestAnOldFieldWithTheWrongTypeCostsOnlyThatField:
    def test_each_falls_back_on_its_own(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            handle.write(
                '{"shift": null, "difficulty": ["craft"], '
                '"reports_closed": "many", "reports_correct": 7, '
                '"qualifications": [["x"], {"a": 1}, null, "frame"], '
                '"index_history": [90.5, NaN, Infinity, true, "x"], '
                '"office": 5, "finished": "yes", "missed_commitments": 1e999}')
        career = Career(path)
        assert career.shift == 1
        assert career.difficulty_key == DEFAULT_DIFFICULTY
        assert career.reports_closed == 0
        assert career.reports_correct == 7
        assert career.qualifications == ['frame']
        assert career.index_history == [90.5]
        assert career.office == {}
        assert career.finished is False
        assert career.missed_commitments == 0

    def test_a_list_for_every_scalar_does_not_crash(self, tmp_path):
        path = career_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({key: [1] for key in (
                'shift', 'reports_closed', 'reports_correct', 'reports_wrong',
                'repeat_reports', 'missed_commitments', 'difficulty',
                'finished', 'assignment')}, handle)
        assert Career(path).shift == 1


class TestNamesAreReadInLinearTime:
    def test_a_long_list_reads_at_once(self):
        import time
        from bell_system.progression import _names
        names = [f'n{number}' for number in range(100000)]
        started = time.perf_counter()
        assert _names(names + names) == names
        assert time.perf_counter() - started < 2.0
