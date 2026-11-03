"""
Phase 8: trouble that comes and goes, and a board that has causes in it.

Each test builds the report it needs. None depends on which reports a board
happens to be dealt, and the transient ones set the clock on the report they
build instead of hoping a draw produced one.
"""

import random
from datetime import datetime

import pytest

from bell_system.reports import (
    TRANSIENT_FAULTS,
    TRANSIENT_WINDOW,
    ReportDesk,
    transient_after,
)

SHIFT_START = datetime(1983, 11, 14, 8, 0)


@pytest.fixture
def desk():
    """A report desk with a fixed generator, so a test can reason about it."""
    return ReportDesk('201', '555', 'NWRKNJ02', random.Random(1983))


def _transient(terminal, fault='GROUND', after=30):
    """A report on a line whose trouble goes by itself, ``after`` minutes on."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    report.clears_after = after
    return report


class TestTransientTrouble:
    """A9: read faulty at the first test, clean an hour later."""

    def test_which_reports_are_transient_is_the_numbers_to_say(self):
        """Asked twice it answers the same, whoever else drew from the dice."""
        for index in range(200):
            number = f"TR-{index:05d}"
            assert transient_after(number, 'GROUND') == transient_after(
                number, 'GROUND')

    def test_only_the_faults_that_come_and_go_can_be_transient(self):
        for index in range(300):
            number = f"TR-{index:05d}"
            for fault in ('OPEN', 'SHORT', 'WET', 'FCG', 'CO_EQUIP', 'NONE'):
                assert transient_after(number, fault) is None

    def test_some_are_and_most_are_not(self):
        found = [transient_after(f"TR-{index:05d}", 'CROSS')
                 for index in range(400)]
        kinds = [value for value in found if value is not None]
        assert 40 < len(kinds) < 200
        low, high = TRANSIENT_WINDOW
        assert all(low <= value <= high for value in kinds)
        assert set(TRANSIENT_FAULTS) == {'GROUND', 'CROSS', 'FEMF'}

    def test_dealing_a_board_takes_nothing_from_the_dice(self):
        """The same seed deals the same board with or without the feature."""
        first = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        second = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        opened = [r.record.fault for r in first.open_shift(SHIFT_START)]
        again = [r.record.fault for r in second.open_shift(SHIFT_START)]
        assert opened == again

    def test_a_forced_condition_is_never_transient(self, desk):
        for fault in TRANSIENT_FAULTS:
            report = desk.receive(SHIFT_START, fault=fault)
            assert report.clears_after is None

    def test_the_clock_starts_at_the_first_test_and_not_before(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        report.clears_after = 30
        report.age(500)
        assert report.record.fault == 'GROUND'
        assert report.clears_at is None
        desk.record_test(report, 'mlt')
        assert report.clears_at == report.minutes_spent - 4 + 30

    def test_it_reads_faulty_at_first_and_clean_an_hour_later(self, terminal):
        report = _transient(terminal)
        first = terminal.execute_command(f'mlt {report.number}')
        assert 'Every reading was within limits' not in first
        terminal.execute_command('sleep 3600')
        again = terminal.execute_command(f'mlt {report.number}')
        assert 'Every reading was within limits' in again
        assert report.record.fault == 'NONE'

    def test_closing_it_no_trouble_after_the_retest_is_not_a_repeat(
            self, terminal):
        report = _transient(terminal)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command('sleep 3600')
        terminal.execute_command(f'mlt {report.number}')
        before = terminal.desk.repeat_count
        result = terminal.execute_command(f'report close {report.number} 8')
        assert 'matches what was on the line' in result
        assert terminal.desk.repeat_count == before
        assert report.correct

    def test_calling_it_trouble_found_after_it_cleared_is_wrong(
            self, terminal):
        report = _transient(terminal)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command('sleep 3600')
        result = terminal.execute_command(
            f'report close {report.number} 5 GROUND')
        assert report.correct is False
        assert 'Nothing was actually wrong' in result

    def test_a_crew_that_reached_it_while_it_was_there_cleared_it(
            self, terminal):
        report = _transient(terminal, after=20)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} outside')
        assert report.record.fault == 'GROUND'
        terminal.execute_command('sleep 3600')
        assert report.record.fault == 'GROUND'
        result = terminal.execute_command(
            f'report close {report.number} 5 GROUND')
        assert report.correct, result

    def test_a_closed_line_stops_changing(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        report.clears_after = 20
        desk.record_test(report, 'mlt')
        desk.close(report, 5, 'GROUND', SHIFT_START)
        report.age(600)
        assert report.record.fault == 'GROUND'

    def test_the_clock_survives_a_save(self, terminal):
        from bell_system.save import _report_in, _report_out
        report = _transient(terminal, after=45)
        terminal.desk.record_test(report, 'mlt')
        restored = _report_in(_report_out(report))
        assert (restored.clears_after, restored.clears_at) == (
            report.clears_after, report.clears_at)

    def test_a_report_saved_before_this_is_the_usual_kind(self, terminal):
        from bell_system.save import _report_in, _report_out
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        written = _report_out(report)
        del written['clears_after'], written['clears_at']
        restored = _report_in(written)
        assert restored.clears_after is None
        assert restored.clears_at is None

    def test_reading_the_board_does_not_start_the_clock(self, terminal):
        report = _transient(terminal)
        terminal.execute_command('report')
        terminal.execute_command(f'report show {report.number}')
        assert report.clears_at is None
