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

    def test_only_whole_words_match(self, terminal):
        assert 'No procedures match' in terminal.execute_command(
            'bsp search resist')
        assert '660-001' in terminal.execute_command(
            'bsp search resistance')

    def test_a_topic_needs_three_characters(self, terminal):
        for short in ('bsp search lo', 'bsp search a'):
            assert 'at least 3' in terminal.execute_command(short)

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
        # What the listing pinned, not the board after it: a report can
        # arrive while the command runs.
        return list(terminal.desk.listed)

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

    def test_a_row_that_has_closed_says_so(self, terminal):
        listed = self._board(terminal)
        terminal.desk.find('1').status = 'CLOSED'
        for command in ('report show 1', 'report dispatch 1 outside',
                        'report close 1 8', 'mlt 1'):
            said = terminal.execute_command(command)
            assert f"{listed[0]} is closed; 'report' relists" in said, command

    def test_a_board_listed_empty_does_not_fall_back_to_live_order(
            self, terminal):
        for report in list(terminal.desk.pending()):
            report.status = 'CLOSED'
        terminal.execute_command('report')
        terminal.desk.receive(terminal.clock.now())
        said = terminal.execute_command('report show 1')
        assert "'report' relists" in said

    def test_a_new_tour_clears_the_pin(self, terminal):
        self._board(terminal)
        assert terminal.desk.listed
        terminal.execute_command('handoff relieve')
        assert terminal.desk.listed is None
        assert terminal.desk.find('2') is terminal.desk.pending()[1]
        assert 'MECHANISED LOOP TEST' in terminal.execute_command('mlt 2')

    def test_before_any_listing_a_position_is_the_board_as_it_stands(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(3))
        first = desk.receive(datetime(1983, 11, 14), fault='OPEN')
        assert desk.find('1') is first


class TestARefusedRedispatchKeepsTheFirstOne:
    def test_the_report_stays_dispatched(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        report = desk.receive(datetime(1983, 11, 14), fault='WET')
        first, went = desk.send_crew(report, 'Cable repair', 0)
        assert went
        # Whoever else answers cable repair is out as well.
        for number in ('TR-00001', 'TR-00002'):
            desk.force.send('Cable repair', number, 600, 0)
        kept = (report.status, report.dispatched_to, report.crew,
                report.field_finding, report.travel_minutes)
        said, went = desk.send_crew(report, 'Cable repair', 0)
        assert not went and said.startswith('Nobody free')
        assert (report.status, report.dispatched_to, report.crew,
                report.field_finding, report.travel_minutes) == kept
        assert report.dispatched_to == 'Cable repair'

    def test_the_screen_calls_in_nothing_for_a_refusal(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} cable')
        assert report.dispatched_to == 'Cable repair'
        for number in ('TR-00001', 'TR-00002'):
            terminal.desk.force.send('Cable repair', number, 600,
                                     terminal.shift_minutes)
        queued = len(terminal._queued_messages)
        said = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Nobody free' in said
        assert len(terminal._queued_messages) == queued
        assert report.dispatched_to == 'Cable repair' and report.crew


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


class TestTheManualAgreesWithTheCode:
    def test_the_set_page_says_two_sightings_not_four(self):
        from bell_system.data.man_pages import MAN_PAGES
        text = ' '.join(MAN_PAGES['set'].split())
        assert 'first two sightings' in text
        assert 'first four times' not in text
        assert 'first four sightings' not in text

    @staticmethod
    def _section(page, heading):
        lines = page.splitlines()
        start = lines.index(heading) + 1
        end = next((i for i in range(start, len(lines))
                    if lines[i] and lines[i] == lines[i].upper()
                    and not lines[i].startswith(' ')), len(lines))
        return lines[start:end]

    def test_the_set_page_lists_every_setting_under_its_heading(self):
        from bell_system.data.man_pages import MAN_PAGES
        from bell_system.settings import OPTIONS
        page = MAN_PAGES['set']
        settings = self._section(page, 'SETTINGS')
        assists = self._section(page, 'ASSISTS')
        for option in OPTIONS:
            rows = assists if option.key.startswith('assist.') else settings
            entries = [line.split()[0] for line in rows
                       if line.startswith('     ') and
                       not line.startswith('      ')]
            assert option.key in entries, option.key

    def test_the_named_settings_are_in_the_settings_section(self):
        from bell_system.data.man_pages import MAN_PAGES
        settings = '\n'.join(self._section(MAN_PAGES['set'], 'SETTINGS'))
        for key in ('game.ambience', 'game.prompts', 'game.difficulty',
                    'display.pacing'):
            assert key in settings, key
        assert 'assist.sections' in '\n'.join(
            self._section(MAN_PAGES['set'], 'ASSISTS'))
