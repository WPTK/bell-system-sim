"""
Two cheaper ways to find a fault, and the index that judges what you do
with them.

A frame trouble is visible in the records, and finding it there costs a
lookup rather than a measurement and a trip. A plant test number is aural
rather than electrical, and hears things a loss measurement passes. Neither
replaces mechanised loop testing; both are alternatives to reaching for it
first, which is what a craftsperson actually had.
"""

import random
from datetime import datetime

import pytest

from bell_system.data.testlines import (
    PLANT_TESTS,
    PLANT_TEST_ORDER,
    PLANT_TEST_RESULTS,
)
from bell_system.data.trouble import FAULTS, FRAME_DEFECTS, FRAME_DEFECT_CODES
from bell_system.progression import (
    DIFFICULTIES,
    MISSED_COMMITMENT_WEIGHT,
    REPEAT_REPORT_WEIGHT,
    WRONG_DISPOSITION_WEIGHT,
)
from bell_system.reports import ReportDesk

SHIFT_START = datetime(1983, 11, 14, 8, 0)


@pytest.fixture
def desk():
    return ReportDesk('201', '555', 'NWRKNJ02', random.Random(1983))


class TestFrameDefects:
    """Central office equipment trouble, as it appears on the frame."""

    def test_every_defect_says_what_the_record_shows_and_what_to_do(self):
        for code, defect in FRAME_DEFECTS.items():
            assert defect.code == code
            assert defect.record_note
            assert defect.remedy.endswith('.')

    def test_a_central_office_fault_always_has_one(self, desk):
        for _ in range(12):
            report = desk.receive(SHIFT_START, fault='CO_EQUIP')
            assert report.record.frame_defect in FRAME_DEFECT_CODES

    def test_nothing_else_has_one(self, desk):
        for code in FAULTS:
            if code == 'CO_EQUIP':
                continue
            report = desk.receive(SHIFT_START, fault=code)
            assert report.record.frame_defect is None, code


class TestTheCrossConnectRecord:
    """cosmos jumper, which used to invent its answer every time."""

    def test_it_reads_the_line_record(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        record = report.record
        result = terminal.execute_command(
            f'cosmos jumper {record.telephone_number}')
        assert record.cable_pair() in result
        assert record.line_equipment in result
        assert record.clli in result

    def test_the_same_line_gives_the_same_answer_twice(self, terminal):
        """
        It used to generate a new vertical, horizontal and jumper length on
        every call, so two looks at one line disagreed and neither meant
        anything.
        """
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        number = report.record.telephone_number
        first = terminal.execute_command(f'cosmos jumper {number}')
        second = terminal.execute_command(f'cosmos jumper {number}')
        assert first == second

    def test_a_frame_trouble_shows_in_the_record(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='CO_EQUIP')
        result = terminal.execute_command(
            f'cosmos jumper {report.record.telephone_number}')
        assert 'DOES NOT AGREE' in result
        assert FRAME_DEFECTS[report.record.frame_defect].remedy in result

    def test_a_loop_trouble_does_not(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        result = terminal.execute_command(
            f'cosmos jumper {report.record.telephone_number}')
        assert 'DOES NOT AGREE' not in result
        assert 'not on' in result

    def test_finding_it_on_the_frame_counts_as_testing_it(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='CO_EQUIP')
        assert not report.tested
        terminal.execute_command(
            f'cosmos jumper {report.record.telephone_number}')
        assert report.tested
        assert 'frame record' in report.test_notes[0]

    def test_the_lookup_costs_desk_time(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='CO_EQUIP')
        before = report.minutes_spent
        terminal.execute_command(
            f'cosmos jumper {report.record.telephone_number}')
        assert report.minutes_spent > before

    def test_it_is_cheaper_than_a_measurement(self, terminal):
        """The whole reason to check the records first."""
        frame = terminal.desk.receive(terminal.clock.now(), fault='CO_EQUIP')
        meter = terminal.desk.receive(terminal.clock.now(), fault='CO_EQUIP')
        terminal.execute_command(
            f'cosmos jumper {frame.record.telephone_number}')
        terminal.execute_command(f'mlt {meter.record.telephone_number}')
        assert frame.minutes_spent < meter.minutes_spent

    def test_a_line_this_centre_does_not_serve_is_reported(self, terminal):
        assert 'no assignment record' in terminal.execute_command(
            'cosmos jumper 555-0000')


class TestPlantTestNumbers:
    """ANAC, milliwatt, quiet termination, loop around and ringback."""

    def test_every_test_has_a_purpose_and_a_good_answer(self):
        for key, test in PLANT_TESTS.items():
            assert test.key == key
            assert test.purpose.endswith('.')
            assert test.good.endswith('.')
            assert test.attested

    def test_every_fault_has_an_answer_for_every_test(self):
        """
        A test with nothing to say on a fault is a hole a player falls into.
        """
        for fault in FAULTS:
            for key in PLANT_TEST_ORDER:
                assert PLANT_TEST_RESULTS[fault][key], (fault, key)

    def test_the_listing_names_both_kinds(self, terminal):
        listing = terminal.execute_command('testline')
        assert 'ROTL' in listing
        assert 'ANAC' in listing
        assert 'Plant test numbers' in listing

    def test_one_can_be_described_on_its_own(self, terminal):
        result = terminal.execute_command('testline anac')
        assert '1004' not in result
        assert 'reads back' in result.lower()

    def test_it_answers_against_the_line_s_real_fault(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        result = terminal.execute_command(
            f'testline quiet {report.record.telephone_number}')
        assert PLANT_TEST_RESULTS['GROUND']['QUIET'] in result

    def test_a_good_line_says_so_and_says_what_that_is_worth(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='NONE')
        result = terminal.execute_command(
            f'testline quiet {report.record.telephone_number}')
        assert 'does not mean the line is good' in result

    def test_it_counts_as_testing_the_report(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        terminal.execute_command(
            f'testline mw {report.record.telephone_number}')
        assert report.tested

    def test_it_is_cheaper_than_mechanised_loop_testing(self, terminal):
        dialled = terminal.desk.receive(terminal.clock.now(), fault='WET')
        measured = terminal.desk.receive(terminal.clock.now(), fault='WET')
        terminal.execute_command(
            f'testline mw {dialled.record.telephone_number}')
        terminal.execute_command(f'mlt {measured.record.telephone_number}')
        assert dialled.minutes_spent < measured.minutes_spent

    def test_the_quiet_termination_hears_a_ground(self):
        """
        The reason to have both kinds of test: an aural check finds things a
        loss measurement passes, and this is the clearest case.
        """
        assert 'Not quiet' in PLANT_TEST_RESULTS['GROUND']['QUIET']
        assert 'Not quiet' in PLANT_TEST_RESULTS['CROSS']['QUIET']

    def test_a_dead_pair_answers_nothing_anywhere(self):
        for key in PLANT_TEST_ORDER:
            assert 'No' in PLANT_TEST_RESULTS['OPEN'][key]

    def test_an_unknown_line_is_reported(self, terminal):
        assert 'no line record' in terminal.execute_command(
            'testline anac 555-0000')

    def test_an_unknown_code_lists_both_kinds(self, terminal):
        result = terminal.execute_command('testline nonsense')
        assert 'Trunks:' in result and 'Lines:' in result


class TestTheIndexIsCalibrated:
    """
    The penalty weights, played rather than argued.

    tools/index_calibration.py is the exercise; these hold the conclusions
    it reached, so that a change to the weights has to face them.
    """

    def test_the_weights_are_ordered_by_how_bad_the_mistake_is(self):
        assert (WRONG_DISPOSITION_WEIGHT
                > REPEAT_REPORT_WEIGHT
                > MISSED_COMMITMENT_WEIGHT)

    def test_the_forgiving_setting_still_discriminates(self):
        """
        At 0.4 an ordinary player scored EXCELLENT in 89 shifts out of 100
        and the bands meant nothing. A forgiving setting is meant to be
        forgiving, not uninformative.
        """
        assert DIFFICULTIES['fun'].index_penalty >= 0.6

    def test_the_strict_setting_takes_the_full_penalty(self):
        assert DIFFICULTIES['craft'].index_penalty == 1.0

    def test_a_perfect_tour_scores_full_marks_on_either(self, tmp_path):
        from bell_system.progression import Career
        for key in ('fun', 'craft'):
            career = Career(str(tmp_path / f'{key}.json'), difficulty=key)
            career.reports_closed = 20
            career.reports_correct = 20
            assert career.service_index() == 100.0

    def test_the_same_mistakes_cost_less_on_the_forgiving_setting(
            self, tmp_path):
        from bell_system.progression import Career
        scores = []
        for key in ('fun', 'craft'):
            career = Career(str(tmp_path / f'{key}.json'), difficulty=key)
            career.reports_closed = 20
            career.reports_wrong = 4
            career.repeat_reports = 2
            career.missed_commitments = 3
            scores.append(career.service_index())
        assert scores[0] > scores[1]

    def test_an_ordinary_tour_is_not_excellent_on_either_setting(
            self, tmp_path):
        """
        The calibration's central finding. An ordinary tour - six wrong
        calls in forty, a couple of repeats - used to read EXCELLENT on the
        forgiving setting, which made the band meaningless.
        """
        from bell_system.progression import Career
        for key in ('fun', 'craft'):
            career = Career(str(tmp_path / f'{key}.json'), difficulty=key)
            career.reports_closed = 40
            career.reports_wrong = 6
            career.repeat_reports = 2
            assert career.index_band() != 'EXCELLENT', key
