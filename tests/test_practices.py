"""
The Practices binder in /usr/bsp, and the prompt that sends a player to the
frame when a loop reads clean.

Plan rows A3 and C12. A3: /usr/bsp is not empty after the first tour, and
every sheet says its number is the simulation's own. C12: when the readings
are clean, help and hint name the frame lookup instead of guessing a crew.
"""

import re

import pytest

from bell_system.data.hints import HINTS
from bell_system.data.practices import NUMBER_NOTICE, SHEETS, index, render
from bell_system.data.trouble import FAULTS, REAL_FAULTS
from bell_system.filesystem import FILESYSTEM
from bell_system.loop_testing import measure_loop, reading_is_clean
from bell_system.progression import QUALIFICATIONS


class TestTheBinder:
    def test_usr_bsp_is_not_empty(self, raw_terminal):
        listing = raw_terminal.execute_command('ls /usr/bsp')
        assert 'index' in listing
        for number in SHEETS:
            assert number in listing

    def test_every_sheet_is_a_file(self):
        for number in SHEETS:
            assert FILESYSTEM[f'/usr/bsp/{number}'].content == render(number)

    def test_every_sheet_says_its_number_is_the_simulations_own(self):
        for number in SHEETS:
            text = ' '.join(render(number).split())
            assert NUMBER_NOTICE in text, number

    def test_every_sheet_says_where_each_figure_comes_from(self):
        for number, sheet in SHEETS.items():
            text = render(number)
            assert sheet.basis, number
            for what, source in sheet.basis:
                assert what in text
                assert source.split(':')[0] in ' '.join(text.split())

    def test_the_index_lists_every_sheet(self):
        for number, sheet in SHEETS.items():
            assert f'{number}  {sheet.title}' in index()

    def test_the_resistance_table_agrees_with_the_faults_it_describes(self):
        text = render('660-001')
        for code in REAL_FAULTS:
            assert code in text
            assert FAULTS[code].mlt_signature in text

    def test_the_binder_can_be_read_at_the_terminal(self, raw_terminal):
        assert 'SHEET 660-001' in raw_terminal.execute_command(
            'cat /usr/bsp/660-001')


class TestHintsCiteTheBinder:
    def test_every_sheet_a_hint_names_exists(self):
        named = set()
        for levels in HINTS.values():
            for _, lines in levels:
                named.update(re.findall(r'\b\d{3}-\d{3}\b', ' '.join(lines)))
        assert named
        assert named <= set(SHEETS)

    @pytest.mark.parametrize('situation', ['measure', 'dispatch', 'close',
                                           'callback', 'frame'])
    def test_level_three_cites_a_sheet(self, situation):
        _, lines = HINTS[situation][2]
        assert re.search(r'\b\d{3}-\d{3}\b', ' '.join(lines))


class TestReadingClean:
    @pytest.mark.parametrize('code', ['FCG', 'CO_EQUIP', 'NONE'])
    def test_these_conditions_read_clean(self, code):
        assert reading_is_clean(measure_loop('555-0123', code,
                                             name_fault=False))

    @pytest.mark.parametrize('code', ['OPEN', 'SHORT', 'GROUND', 'CROSS',
                                      'FEMF', 'WET', 'ROH'])
    def test_these_do_not(self, code):
        assert not reading_is_clean(measure_loop('555-0123', code,
                                                 name_fault=False))


def _only(terminal, report):
    """Drop whatever else has arrived, so the board is just this report."""
    terminal.desk.reports = {report.number: report}
    terminal.desk.order[:] = [report.number]


def _clean_report(terminal, fault='CO_EQUIP'):
    """
    Put one measured, undispatched report on a clear board.

    Measuring spends minutes and the building keeps sending reports, so the
    board is cleared again afterwards: the test is about this one report.
    """
    terminal.desk.reports.clear()
    terminal.desk.order.clear()
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    terminal.execute_command(f'mlt {report.number}')
    _only(terminal, report)
    return report


@pytest.fixture
def working(raw_terminal):
    """A craftsperson past their first tour, signed off on everything."""
    raw_terminal.career.shift = 2
    raw_terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
    raw_terminal.settings.set('game.ambience', 'off')
    return raw_terminal


class TestAnAmbiguousReadingSendsThemToTheFrame:
    @pytest.mark.parametrize('code', ['FCG', 'CO_EQUIP', 'NONE'])
    def test_help_names_the_lookup_on_a_clean_reading(self, working, code):
        report = _clean_report(working, code)
        action = working.next_action()
        assert action.step == 'frame'
        assert action.command == (
            f'cosmos jumper {report.record.telephone_number}')

    def test_it_is_the_same_for_all_three(self, working):
        steps = set()
        for code in ('FCG', 'CO_EQUIP', 'NONE'):
            _clean_report(working, code)
            steps.add(working.next_action().step)
        assert steps == {'frame'}

    def test_hint_agrees(self, working):
        report = _clean_report(working)
        assert working._situation() == 'frame'
        first = working.execute_command('hint')
        assert 'gvasquez' in first
        _only(working, report)
        working.execute_command('hint')
        _only(working, report)
        third = working.execute_command('hint')
        assert 'cosmos jumper' in third
        assert '660-003' in third

    def test_a_reading_with_a_fault_in_it_is_not_sent_there(self, working):
        _clean_report(working, 'OPEN')
        assert working.next_action().step != 'frame'

    def test_not_before_the_report_is_measured(self, working):
        working.desk.reports.clear()
        working.desk.order.clear()
        report = working.desk.receive(working.clock.now(), fault='CO_EQUIP')
        _only(working, report)
        assert working.next_action().step == 'measure'

    def test_without_the_frame_sign_off_it_is_not_offered(self, working):
        working.career.qualifications = [
            q for q in working.career.qualifications if q != 'frame']
        _clean_report(working)
        assert not working.career.may_use('cosmos')
        action = working.next_action()
        assert action.step != 'frame'
        assert 'cosmos' not in action.command

    def test_once_the_record_has_been_read_it_stops_asking(self, working):
        report = _clean_report(working)
        working.execute_command(
            f'cosmos jumper {report.record.telephone_number}')
        _only(working, report)
        assert working.next_action().step != 'frame'
        assert working._situation() != 'frame'

    def test_looking_up_another_line_does_not_count(self, working):
        report = _clean_report(working)
        working.execute_command('cosmos jumper 555-9999')
        _only(working, report)
        assert report.record.telephone_number != '555-9999'
        assert working.next_action().step == 'frame'

    def test_the_lookup_does_not_name_the_condition(self, working):
        for code in ('FCG', 'CO_EQUIP', 'NONE'):
            _clean_report(working, code)
            action = working.next_action()
            assert FAULTS[code].name.lower() not in (
                action.reason.lower() + action.command.lower())
