"""
Fixes from the end-of-wave playtest (issue 63).

A refused dispatch changes nothing, a position means the row the player last
read, ``bsp search`` is a search, and the screens say what they will do.
"""

import random
from datetime import datetime

from bell_system.data.practices import SHEETS
from bell_system.reports import ReportDesk


def _busy_desk(seed=7):
    """A desk whose cable repair crews are both out for a long time."""
    desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(seed))
    for number in ('TR-00001', 'TR-00002'):
        desk.force.send('Cable repair', number, 600, 0)
    return desk


class TestBspSearch:
    def test_a_topic_lists_the_sheets_that_are_about_it(self, terminal):
        found = terminal.execute_command('bsp search loop')
        assert '660-001' in found and '660-003' in found

    def test_mlt_finds_the_reading_sheet(self, terminal):
        assert '660-001' in terminal.execute_command('bsp search mlt')

    def test_the_topic_filters(self, terminal):
        microwave = terminal.execute_command('bsp search microwave')
        assert 'TH-3 Microwave Alignment' in microwave
        assert '3A Central Control' not in microwave
        assert not any(number in microwave for number in SHEETS)
        loop = terminal.execute_command('bsp search loop')
        assert 'TH-3 Microwave Alignment' not in loop
        assert loop != microwave

    def test_every_word_of_the_topic_has_to_match(self, terminal):
        assert 'No procedures match' in terminal.execute_command(
            'bsp search loop microwave')

    def test_a_topic_with_no_match_says_so(self, terminal):
        found = terminal.execute_command('bsp search zzzz')
        assert 'No procedures match' in found
        assert 'BSP 200-455-100' not in found

    def test_a_procedure_is_still_found_by_its_number(self, terminal):
        found = terminal.execute_command('bsp search 400-200')
        assert 'Traffic Analysis Procedures' in found
        assert 'bsp section' in found


class TestARefusedDispatchChangesNothing:
    def test_a_measured_report_stays_measured(self):
        desk = _busy_desk()
        report = desk.receive(datetime(1983, 11, 14), fault='WET')
        desk.record_test(report, 'MLT')
        assert report.status == 'TESTED'
        said = desk.dispatch(report, 'Cable repair', 10)
        assert said.startswith('Nobody free')
        assert report.status == 'TESTED'
        assert report.tested
        assert report.dispatched_to is None and report.crew is None

    def test_a_report_nobody_has_measured_stays_pending(self):
        desk = _busy_desk()
        report = desk.receive(datetime(1983, 11, 14), fault='WET')
        desk.dispatch(report, 'Cable repair', 10)
        assert report.status == 'PEND'

    def test_the_wrong_force_with_nobody_free_changes_nothing_either(self):
        desk = _busy_desk()
        report = desk.receive(datetime(1983, 11, 14), fault='OPEN')
        desk.record_test(report, 'MLT')
        before = report.minutes_spent
        said = desk.dispatch(report, 'Cable repair', 10)
        assert said.startswith('Nobody free')
        assert report.status == 'TESTED'
        assert report.dispatched_to is None and report.crew is None
        # The call is charged; the wrong trip nobody made is not.
        assert 0 < report.minutes_spent - before < 45

    def test_on_the_board_it_still_reads_tested(self, terminal):
        for number in ('TR-00001', 'TR-00002'):
            terminal.desk.force.send('Cable repair', number, 600,
                                     terminal.shift_minutes)
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} cable')
        assert 'TESTED' in terminal.execute_command(f'report show {report.number}')


class TestPositionsHoldUntilTheNextListing:
    def _board(self, terminal, count=4):
        for _ in range(count):
            terminal.desk.receive(terminal.clock.now())
        terminal.execute_command('report')
        return [report.number for report in terminal.desk.pending()]

    def test_a_position_is_the_row_that_was_listed(self, terminal):
        listed = self._board(terminal)
        assert terminal.desk.find('2').number == listed[1]

    def test_an_arrival_that_resorts_the_board_does_not_move_it(
            self, terminal):
        listed = self._board(terminal)
        # A report due before everything else lands at the top.
        urgent = terminal.desk.receive(terminal.clock.now())
        urgent.commitment = min(
            report.commitment for report in terminal.desk.pending()
        ).replace(year=1983, month=1)
        assert terminal.desk.pending()[0] is urgent
        for position, number in enumerate(listed, 1):
            assert terminal.desk.find(str(position)).number == number

    def test_the_next_listing_repins(self, terminal):
        self._board(terminal)
        urgent = terminal.desk.receive(terminal.clock.now())
        urgent.commitment = urgent.commitment.replace(year=1983, month=1)
        terminal.execute_command('report')
        assert terminal.desk.find('1') is urgent

    def test_a_closed_row_is_no_longer_there(self, terminal):
        listed = self._board(terminal)
        terminal.desk.find('1').status = 'CLOSED'
        assert terminal.desk.find('1') is None
        assert terminal.desk.find('2').number == listed[1]

    def test_a_position_past_the_listing_is_nothing(self, terminal):
        listed = self._board(terminal)
        terminal.desk.receive(terminal.clock.now())
        assert terminal.desk.find(str(len(listed) + 1)) is None

    def test_before_any_listing_a_position_is_the_board_as_it_stands(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(3))
        first = desk.receive(datetime(1983, 11, 14), fault='OPEN')
        assert desk.find('1') is first


class TestThePreviewDoesNotLookMissed:
    def test_goals_are_marked_as_judged_at_sign_off(self, terminal):
        rows = terminal.goal_lines(final=False)
        assert len(rows) > 1
        assert all(row.strip().startswith('[?]') for row in rows)
        assert any('judged at sign-off' in row for row in rows)

    def test_the_handoff_preview_says_so(self, terminal):
        shown = terminal.execute_command('handoff')
        assert '[?]' in shown and 'judged at sign-off' in shown
        assert '[ ]' not in shown.split('TOUR GOALS')[1].split('REPORTS')[0]


class TestTheFaultTableSaysHowToCloseRoh:
    def test_the_roh_row_says_five_not_eight(self, terminal):
        shown = terminal.execute_command('report faults')
        assert 'close 5 ROH, not 8' in shown
        # Only the one condition that reads like nothing found.
        assert shown.count(', not 8') == 1


class TestTheDocsAgreeWithTheCode:
    def test_the_readme_says_two_sightings_not_four(self):
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'README.md'), encoding='utf-8') as f:
            text = ' '.join(f.read().split())
        assert 'first two times' in text
        assert 'first four times' not in text
        assert 'first four sightings' not in text

    def test_the_curve_names_every_tours_kind(self):
        import os
        from bell_system.data import tours
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, 'docs', 'design', 'difficulty-curve.md')
        with open(path, encoding='utf-8') as f:
            rows = [line for line in f.read().splitlines()
                    if line.startswith('| ') and line[2:3].isdigit()]
        shapes = {}
        for row in rows:
            cells = [cell.strip() for cell in row.strip('|').split('|')]
            if len(cells) == 7:
                shapes[int(cells[0])] = cells[6]
        for entry in tours.TOURS:
            shape = shapes[entry.number]
            assert shape.startswith(entry.kind.capitalize()), entry.number
            assert entry.theme in shape, entry.number
