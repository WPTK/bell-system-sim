"""
The small fixes from the wave 3 playtest (#93, the P3 batch), one test each.
"""

from datetime import timedelta

import pytest

from bell_system.data import tours
from bell_system.data.finds import FRAGMENTS_BY_KEY
from bell_system.npc import FAVOUR_AT, FAVOUR_MINUTES, FAVOURS, WATCH_LABELS


def draw(terminal, tour, count=400):
    terminal.career.shift = tour
    for _ in range(count):
        terminal.desk.receive(terminal.clock.now(), 0)


def test_the_night_watch_opens_at_midnight_not_at_twenty_four():
    assert WATCH_LABELS['night'] == 'Night Shift (00:00-08:00)'


def test_no_filler_claims_a_peak_hour_on_a_watch_that_has_none():
    """The same board is drawn for every watch, so it can't say 'peak-hour'."""
    for row in tours._FILLER:
        assert 'peak' not in row[4].lower()


def test_the_briefing_never_prints_a_negative_time(terminal):
    report = terminal.desk.pending()[0]
    report.commitment = report.received - timedelta(hours=3)
    lines = []
    terminal.emit = lines.append
    terminal._emit_board_briefing()
    row = next(line for line in lines if 'Nearest commitment' in line)
    assert 'in -' not in row
    assert row.endswith('past')


def test_the_briefing_says_remaining_for_a_report_not_yet_due(terminal):
    report = terminal.desk.pending()[0]
    report.commitment = report.received + timedelta(hours=3)
    lines = []
    terminal.emit = lines.append
    terminal._emit_board_briefing()
    row = next(line for line in lines if 'Nearest commitment' in line)
    assert row.endswith('remaining')


class TestAResolvedRegularIsNotChronic:

    def card(self, terminal, key):
        number = terminal.desk.regular_record(key).telephone_number
        return terminal.execute_command(f'custdb {number}')

    def test_an_open_line_with_three_reports_is_flagged(
            self, terminal, monkeypatch):
        from bell_system.lmos import LineCard
        monkeypatch.setattr(LineCard, 'is_chronic', lambda self: True)
        draw(terminal, 7)
        assert 'CHRONIC' in self.card(terminal, 'kowalczyk')

    def test_a_resolved_line_keeps_its_count_and_loses_the_flag(
            self, terminal, monkeypatch):
        from bell_system.lmos import LineCard
        monkeypatch.setattr(LineCard, 'is_chronic', lambda self: True)
        terminal.career.regular_closed['kowalczyk'] = 3
        terminal.career.shift = 11
        card = self.card(terminal, 'kowalczyk')
        assert 'RESOLVED' in card
        assert 'CHRONIC' not in card
        row = next(line for line in terminal.execute_command(
            'custdb').splitlines() if 'Kowalczyk' in line)
        assert 'CHRONIC' not in row and '(resolved)' in row

    def test_a_line_that_is_not_a_regular_is_still_flagged(
            self, terminal, monkeypatch):
        from bell_system.lmos import LineCard
        monkeypatch.setattr(LineCard, 'is_chronic', lambda self: True)
        terminal.career.regular_closed['kowalczyk'] = 3
        draw(terminal, 11)
        rows = [line for line in terminal.execute_command(
            'custdb').splitlines() if 'Kowalczyk' not in line]
        assert any('CHRONIC' in line for line in rows)


def test_qual_says_nothing_of_next_with_prompts_off(terminal):
    terminal.career.qualifications = terminal.career.qualifications[:1]
    terminal.settings.set('game.prompts', 'off')
    assert 'Next:' not in terminal.execute_command('qual')


def test_qual_names_the_next_sign_off_with_prompts_on(terminal):
    terminal.career.qualifications = terminal.career.qualifications[:1]
    terminal.settings.set('game.prompts', 'on')
    assert 'Next:' in terminal.execute_command('qual')


class TestTouch:

    def test_touch_on_a_shut_file_says_so(self, terminal):
        said = terminal.execute_command('touch /etc/passwd')
        assert said == 'touch: /etc/passwd: not owner'

    def test_touch_on_a_file_you_own_marks_it_written_now(self, terminal):
        terminal.execute_command('echo hi > /tmp/mine')
        written = terminal.filesystem['/tmp/mine'].mtime
        terminal.execute_command('sleep 3600')
        assert terminal.execute_command('touch /tmp/mine') == ''
        stamp = terminal.filesystem['/tmp/mine'].mtime
        assert stamp - written >= timedelta(minutes=60)
        assert terminal.execute_command('cat /tmp/mine') == 'hi'

    def test_touch_still_makes_a_new_file(self, terminal):
        assert terminal.execute_command('touch /tmp/new') == ''
        assert '/tmp/new' in terminal.filesystem


class TestAFavourIsDoneOnceForAReport:

    def near(self, terminal, target):
        target.commitment = target.received + timedelta(minutes=30)

    def test_a_second_favour_does_not_stack_an_hour_on_the_same_report(
            self, terminal):
        terminal.settings.set('game.ambience', 'on')
        terminal.career.shift = 4
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=3)
        first, second = list(FAVOURS)[:2]
        for login in (first, second):
            terminal.career.rapport[login] = FAVOUR_AT
        for report in terminal.desk.customers():
            report.commitment = report.received + timedelta(
                minutes=FAVOUR_MINUTES + 240)
        target = terminal.desk.customers()[0]
        self.near(terminal, target)
        terminal.is_in = lambda login: True
        assert len(terminal._settle_people(quiet=False)) == 1
        helped = target.commitment
        assert f'favoured:{target.number}' in terminal.career.beats_seen
        # The hour has gone by and it is close again; the other asks.
        self.near(terminal, target)
        helped = target.commitment
        assert terminal._settle_people(quiet=False) == []
        assert target.commitment == helped

    def test_the_next_report_gets_the_next_favour(self, terminal):
        terminal.settings.set('game.ambience', 'on')
        terminal.career.shift = 4
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=3)
        first, second = list(FAVOURS)[:2]
        for login in (first, second):
            terminal.career.rapport[login] = FAVOUR_AT
        terminal.is_in = lambda login: True
        a, b, c = terminal.desk.customers()[:3]
        for report in (b, c):
            report.commitment = report.received + timedelta(
                minutes=FAVOUR_MINUTES + 240)
        self.near(terminal, a)
        terminal._settle_people(quiet=False)
        self.near(terminal, a)
        self.near(terminal, b)
        before = b.commitment
        terminal._settle_people(quiet=False)
        assert b.commitment == before + timedelta(minutes=FAVOUR_MINUTES)


class TestTheStoryFilesAreNotThePlayers:
    """A beat points at the log and the scratch file, so they stay put."""

    @pytest.mark.parametrize('key', ['testlog', 'scratch'])
    def test_the_fragment_is_owned_by_the_machine(self, key):
        assert FRAGMENTS_BY_KEY[key].owner == 'sys'

    def test_the_test_log_cannot_be_removed_or_overwritten(self, terminal):
        before = terminal.filesystem['/usr/adm/testlog'].content
        assert 'permission denied' in terminal.execute_command(
            'rm /usr/adm/testlog')
        terminal.execute_command('echo gone > /usr/adm/testlog')
        assert terminal.filesystem['/usr/adm/testlog'].content == before

    def test_the_scratch_file_cannot_be_removed(self, terminal):
        terminal.career.shift = 2
        terminal.deliver_fragments()
        assert '/tmp/.f' in terminal.filesystem
        assert 'permission denied' in terminal.execute_command('rm /tmp/.f')
        assert '/tmp/.f' in terminal.filesystem
