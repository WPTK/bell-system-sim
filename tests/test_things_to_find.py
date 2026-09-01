"""
Things to find.

The simulation already rewards curiosity well - the netnews spool, the
fortunes, the previous holder's notes in every home directory. These cover
the four added on top: a scoreboard you can actually get onto, a file that
opens partway through a career, a question that has to be answered by ear,
and saying anywhere at all that the games exist.
"""

import pytest

from bell_system.screens.games import MOO_SCORES, OKAFOR_ELEVEN
from bell_system.screens.shell import ADM_GROUP_QUALIFICATIONS

SULOG = '/usr/adm/sulog'


def win_moo(terminal, guesses):
    """Win a game of moo in a known number of guesses."""
    terminal.execute_command('moo')
    terminal._moo_secret = '1234'
    terminal._moo_guesses = guesses - 1
    return terminal.execute_command('moo 1234')


class TestTheScoreboard:
    """A scoreboard you cannot get onto is scenery."""

    def test_the_board_was_there_all_along(self, terminal):
        assert 'lokafor' in (terminal._read(MOO_SCORES) or '')

    def test_winning_puts_you_on_it(self, terminal):
        win_moo(terminal, 6)
        assert terminal.username in (terminal._read(MOO_SCORES) or '')

    def test_a_worse_game_does_not_take_the_place_of_a_better_one(
            self, terminal):
        win_moo(terminal, 4)
        assert 'Scoreboard stands at 4' in win_moo(terminal, 9)
        assert ' 9' not in (terminal._read(MOO_SCORES) or '')

    def test_a_better_game_does(self, terminal):
        win_moo(terminal, 9)
        win_moo(terminal, 3)
        rows = [row for row in (terminal._read(MOO_SCORES) or '').split('\n')
                if row.startswith(terminal.username)]
        assert len(rows) == 1
        assert rows[0].split()[1] == '3'

    def test_beating_okafor_gets_a_response(self, terminal):
        """Her position on that eleven is a matter of record."""
        assert 'lokafor' in win_moo(terminal, OKAFOR_ELEVEN - 1)

    def test_not_beating_her_does_not(self, terminal):
        assert 'lokafor' not in win_moo(terminal, OKAFOR_ELEVEN + 2)

    def test_she_still_disputes_it(self, terminal):
        assert 'dropping characters' in win_moo(terminal, 3)


class TestTheLockedFile:
    """One file that opens partway through a career."""

    def test_it_is_shut_at_the_start(self, raw_terminal):
        assert 'permission denied' in raw_terminal.execute_command(
            f'cat {SULOG}')

    def test_the_listing_says_why(self, raw_terminal):
        assert '-rw-------' in raw_terminal.execute_command('ls -l /usr/adm')

    def test_the_wire_chief_opens_it(self, raw_terminal):
        raw_terminal.career.qualifications = (
            ['q%d' % n for n in range(ADM_GROUP_QUALIFICATIONS)])
        assert 'SU ' in raw_terminal.execute_command(f'cat {SULOG}')

    def test_he_says_so_when_he_does(self):
        from datetime import datetime
        from bell_system.npc import Switchroom
        notice = Switchroom().qualification_notice(
            datetime(1983, 11, 14), 'Central Office Switching', ['switch'],
            held=ADM_GROUP_QUALIFICATIONS)
        assert 'adm group' in ' '.join(notice.lines)

    def test_your_own_name_is_in_it(self, raw_terminal):
        """The payoff is that the machine was recording you all along."""
        raw_terminal.execute_command('su')
        raw_terminal.career.qualifications = (
            ['q%d' % n for n in range(ADM_GROUP_QUALIFICATIONS)])
        assert raw_terminal.username in raw_terminal.execute_command(
            f'cat {SULOG}')

    def test_a_refused_read_does_not_empty_it(self, raw_terminal):
        """
        The log is appended by the machine, not by the operator. Writing it
        through the operator's own read once silently emptied it for
        anybody who could not read it, which is everybody at the start.
        """
        raw_terminal.execute_command('su')
        raw_terminal.execute_command('su rjohnson')
        raw_terminal.career.qualifications = (
            ['q%d' % n for n in range(ADM_GROUP_QUALIFICATIONS)])
        assert 'ehalloran' in raw_terminal.execute_command(f'cat {SULOG}')

    def test_nothing_else_on_the_machine_is_shut(self, raw_terminal):
        """
        A mode column that means something on one file is a puzzle. One
        that means something on forty is an obstacle course.
        """
        shut = [path for path, node in raw_terminal.filesystem.items()
                if not node.is_dir and not raw_terminal._may_read(path)
                and not path.startswith('/dev/')]
        assert shut == [SULOG]


class TestTheCadence:
    """The one question on the board that has to be answered by ear."""

    def callback(self, terminal, fault):
        """Return the call-back text with the wrapping taken back out."""
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        for _ in range(200):
            report = terminal.desk.receive(terminal.clock.now(), 0,
                                           fault=fault)
            if 'complete' in report.symptom.lower():
                break
        else:
            pytest.fail(f'{fault} never produced the shared symptom')
        said = terminal.execute_command(
            f'report callback {report.number}')
        return ' '.join(said.split())

    def test_two_conditions_share_the_symptom(self):
        """Otherwise the words alone would answer it."""
        from bell_system.data.trouble import REPORT_SYMPTOMS
        sharing = [code for code, symptoms in REPORT_SYMPTOMS.items()
                   if 'Calls do not complete' in symptoms]
        assert sorted(sharing) == ['CO_EQUIP', 'FCG', 'NONE']

    def test_every_condition_that_shares_it_has_something_to_hear(self):
        """
        One of the three without a description would be the answer: a
        report with no cadence on it could only be that one.
        """
        from bell_system.data.trouble import REPORT_SYMPTOMS
        from bell_system.screens.bureau import CADENCE_HEARD
        sharing = {code for code, symptoms in REPORT_SYMPTOMS.items()
                   if 'Calls do not complete' in symptoms}
        assert sharing <= set(CADENCE_HEARD)

    def test_the_office_test_fault_has_nothing_to_hear(self, terminal):
        """Which is itself something to notice."""
        said = self.callback(terminal, 'FCG')
        assert 'goes quiet' in said

    def test_the_office_fault_is_the_fast_one(self, terminal):
        assert 'twice as fast' in self.callback(terminal, 'CO_EQUIP')

    def test_no_trouble_is_the_ordinary_one(self, terminal):
        assert 'the slow one' in self.callback(terminal, 'NONE')

    def test_neither_of_them_names_the_tone(self, terminal):
        """Naming it would be the answer."""
        for fault in ('CO_EQUIP', 'NONE'):
            said = self.callback(terminal, fault)
            assert 'reorder' not in said.lower()

    def test_it_points_at_the_command_that_makes_both(self, terminal):
        assert 'tone(1)' in self.callback(terminal, 'CO_EQUIP')

    def test_the_two_tones_really_are_the_same_frequencies(self):
        """Which is why the words cannot separate them and the ear can."""
        from bell_system.tones import catalogue
        rows = dict(catalogue())
        assert '480 Hz + 620 Hz' in rows['busy']
        assert '480 Hz + 620 Hz' in rows['reorder']
        assert '60 IPM' in rows['busy']
        assert '120 IPM' in rows['reorder']

    def test_an_ordinary_report_says_nothing_about_tones(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), 0, fault='WET')
        assert 'tone(1)' not in terminal.execute_command(
            f'report callback {report.number}')


class TestSayingTheGamesAreThere:
    """Zachtronics puts the solitaire game on the box."""

    def test_the_motd_names_them(self, terminal):
        motd = terminal._read('/etc/motd') or ''
        assert '/usr/games' in motd

    def test_help_names_them(self, terminal):
        listing = terminal.execute_command('help')
        for game in ('moo', 'fortune', 'arithmetic'):
            assert game in listing

    def test_the_motd_names_the_hint_command(self, terminal):
        assert 'hint(1)' in (terminal._read('/etc/motd') or '')

    def test_all_three_actually_run(self, terminal):
        for game in ('moo', 'fortune', 'arithmetic'):
            assert terminal.execute_command(game).strip()
