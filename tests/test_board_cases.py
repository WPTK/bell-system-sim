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


def _wet(terminal):
    """A wet report, and the cable and binder group its pair is in."""
    from bell_system.cable import binder_of
    report = terminal.desk.receive(terminal.clock.now(), fault='WET')
    return report, f"{report.record.cable}/{binder_of(report.record.pair)}"


def _craft(terminal):
    terminal.execute_command('set assist.sections named')


class TestNamingTheSection:
    """C21: a splicer is told where, and a wrong group is a wrong trip."""

    def test_the_right_section_repairs(self, terminal):
        report, section = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {section}')
        assert 'resealed' in result
        assert report.field_finding == 'WET'

    def test_a_wrong_section_returns_the_crews_finding(self, terminal):
        report, section = _wet(terminal)
        cable, binder = section.split('/')
        wrong = f"{cable}/{(int(binder) % 24) + 1}"
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {wrong}')
        assert 'found it dry' in result
        assert 'resealed' not in result
        assert report.field_finding is None
        assert terminal.desk.plant.section_at(
            report.record.cable, report.record.pair) is not None

    def test_a_wrong_section_costs_the_wrong_trip(self, terminal):
        right, section = _wet(terminal)
        cable, binder = section.split('/')
        wrong = f"{cable}/{(int(binder) % 24) + 1}"
        before = right.minutes_spent
        terminal.execute_command(
            f'report dispatch {right.number} cable {wrong}')
        assert right.minutes_spent - before >= 45

    def test_the_old_form_still_works_in_fun(self, terminal):
        report, _ = _wet(terminal)
        terminal.execute_command('set assist.sections assumed')
        result = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'resealed' in result
        assert report.field_finding == 'WET'

    def test_craft_asks_where_and_charges_nothing(self, terminal):
        report, _ = _wet(terminal)
        _craft(terminal)
        before = report.desk_minutes
        result = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Which one?' in result
        assert report.desk_minutes == before
        assert report.dispatched_to is None

    def test_the_question_is_the_same_for_a_report_that_is_not_wet(
            self, terminal):
        wet, _ = _wet(terminal)
        dry = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        _craft(terminal)
        asked = [terminal.execute_command(
            f'report dispatch {report.number} cable') for report in (wet, dry)]
        assert asked[0] == asked[1]

    def test_another_force_is_not_asked_for_a_section(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        _craft(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} outside')
        assert 'Which one?' not in result

    def test_a_section_for_the_wrong_force_finds_the_same_dry_sheath(
            self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        cable = (report.record.cable % 80) + 1
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {cable}/3')
        assert 'found it dry' in result

    def test_a_group_with_other_water_is_cleared_for_its_own_reports(
            self, terminal):
        wet, section = _wet(terminal)
        other = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        result = terminal.execute_command(
            f'report dispatch {other.number} cable {section}')
        assert 'resealed' in result
        assert wet.sheath_repaired
        assert other.field_finding is None

    @pytest.mark.parametrize('token', ['81', '81/', '/8', '81/x', '81/8/2'])
    def test_something_that_is_not_a_section_is_refused(self, terminal, token):
        report, _ = _wet(terminal)
        if '/' not in token:
            return
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {token}')
        assert 'not a cable and binder group' in result
        assert report.dispatched_to is None

    def test_there_is_no_binder_group_twenty_five(self, terminal):
        report, _ = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable 81/25')
        assert 'There is no group 25' in result

    def test_the_pair_form_is_not_a_section(self, terminal):
        """0081/0181 is the answer on the card; it is not accepted as one."""
        report, _ = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable '
            f'{report.record.cable_pair()}')
        assert 'not a cable and binder group' in result \
            or 'There is no group' in result

    def test_the_setting_reads_off_the_profile_by_default(self, terminal):
        from bell_system.progression import DIFFICULTIES
        assert not DIFFICULTIES['fun'].section_required
        assert DIFFICULTIES['craft'].section_required
