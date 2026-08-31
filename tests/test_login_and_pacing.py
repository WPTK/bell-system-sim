"""
Sitting down at the terminal: the login sequence, and the speed it prints at.

Two things a 1983 position had that this one did not. It did not offer you
a menu - getty put a banner and a login prompt on the line, login(1) took a
name, asked for a password only if the account had one, printed the message
of the day and handed you to a shell that read your .profile. And it did
not print instantly: a Model 43 at this desk ran at 300 baud, thirty
characters a second, and you watched the line arrive.
"""

import io
import sys

import pytest

from bell_system.constants import BELL_SYSTEM_ROLES
from bell_system.settings import OPTIONS_BY_KEY, Settings


class TestPacingIsAccurateByDefault:
    """The project's rule: accuracy is the default, and you opt out."""

    def test_the_default_is_the_speed_the_position_ran_at(self):
        option = OPTIONS_BY_KEY['display.pacing']
        assert option.default == option.accurate == '300'

    def test_off_is_available_and_is_a_deviation(self, isolated_state):
        settings = Settings()
        assert 'off' in OPTIONS_BY_KEY['display.pacing'].choices
        settings.set('display.pacing', 'off')
        assert 'display.pacing' in str(settings.deviations())

    def test_both_teletype_speeds_are_offered(self):
        """
        The Model 33 ran at 110 and the Model 43 is switchable to 110 or
        300. Both are here because both were on desks in 1983.
        """
        choices = OPTIONS_BY_KEY['display.pacing'].choices
        assert '110' in choices and '300' in choices


class TestPacingArithmetic:
    """Eleven bits to the character on an asynchronous line."""

    @pytest.mark.parametrize('baud,cps', [('110', 10), ('300', 30),
                                          ('1200', 120)])
    def test_the_character_rate_matches_the_published_speed(
            self, terminal, baud, cps):
        """
        A Model 33 at 110 baud did ten characters a second and a Model 43
        at 300 did thirty. Those are published figures and they only come
        out right if the frame is eleven bits at 110 and ten above it: a
        mechanical printer needed two stop bits, and faster lines did not.
        """
        terminal.settings.set('display.pacing', baud)
        rate = (11.0 if int(baud) <= 110 else 10.0) / int(baud)
        assert round(1 / rate) == cps

    def test_off_paces_nothing(self, terminal):
        terminal.settings.set('display.pacing', 'off')
        assert terminal._pace_rate() is None

    def test_a_pipe_is_never_paced(self, terminal):
        """
        Nobody is watching a redirect. Slowing one down would be a strange
        program, and the speed was a property of the printer anyway.
        """
        terminal.settings.set('display.pacing', '110')
        assert not sys.stdout.isatty()
        assert terminal._pace_rate() is None

    def test_output_is_unchanged_by_pacing(self, terminal, capsys):
        terminal.settings.set('display.pacing', '300')
        terminal.emit('Bell System')
        assert capsys.readouterr().out.strip() == 'Bell System'


class TestTheLoginSequence:
    """getty, login, motd, .profile - in that order."""

    def test_the_banner_says_where_you_are(self, terminal):
        banner = '\n'.join(terminal._getty_banner())
        assert terminal.home_office['clli'] in banner
        assert 'UNIX Version 7' in banner

    def test_the_banner_says_what_speed_the_line_is(self, terminal):
        terminal.settings.set('display.pacing', '300')
        assert '300 baud' in '\n'.join(terminal._getty_banner())
        terminal.settings.set('display.pacing', 'off')
        assert 'no pacing' in '\n'.join(terminal._getty_banner())

    def test_the_roster_lists_every_position(self, terminal):
        roster = terminal._login_roster()
        for number, (key, name) in BELL_SYSTEM_ROLES.items():
            assert key in roster
            assert name in roster
            assert str(number) in roster

    @pytest.mark.parametrize('typed', ['radio', 'RADIO', '9'])
    def test_a_position_answers_to_its_name_or_its_number(self, terminal,
                                                          typed):
        resolved = terminal._resolve_login(typed)
        assert resolved is not None
        assert resolved[1] == 'radio'

    def test_an_unknown_name_resolves_to_nothing(self, terminal):
        assert terminal._resolve_login('nobody') is None
        assert terminal._resolve_login('99') is None

    def test_every_position_can_be_logged_into(self, terminal):
        for number, (key, name) in BELL_SYSTEM_ROLES.items():
            assert terminal._resolve_login(key) == (number, key, name)


class TestPasswordsFollowTheFile:
    """
    login(1) asked for a password only when the account had one, and an
    empty second field in /etc/passwd means it does not.
    """

    def test_the_craft_positions_have_no_password(self, terminal):
        for _, (key, _) in BELL_SYSTEM_ROLES.items():
            assert not terminal._password_needed(key), key

    def test_root_does(self, terminal):
        assert terminal._password_needed('root')

    def test_an_unknown_account_does_not(self, terminal):
        """
        Which is why login(1) asked anyway on an unknown name: a wrong name
        and a wrong password had to look the same from the outside.
        """
        assert not terminal._password_needed('nobody')

    def test_the_password_file_says_so_out_loud(self, terminal):
        passwd = terminal.execute_command('cat /etc/passwd')
        assert passwd.startswith('root:')
        assert not passwd.split('\n')[0].startswith('root::')
        for _, (key, _) in BELL_SYSTEM_ROLES.items():
            assert f'{key}::' in passwd, key


class TestLoggingIn:
    """The whole sequence, driven from a script."""

    def run_login(self, terminal, typed, monkeypatch):
        """Log in with a scripted set of answers and return what printed."""
        answers = iter(typed)
        monkeypatch.setattr('builtins.input', lambda _='': next(answers))
        monkeypatch.setattr('getpass.getpass', lambda _='': 'x')
        captured = io.StringIO()
        monkeypatch.setattr('sys.stdout', captured)
        terminal.login()
        return captured.getvalue()

    def test_it_prints_the_message_of_the_day(self, terminal, monkeypatch):
        output = self.run_login(terminal, ['radio'], monkeypatch)
        assert 'UNIX Version 7' in output
        assert 'the Bell System is dissolved' in output

    def test_it_runs_the_position_s_profile(self, terminal, monkeypatch):
        output = self.run_login(terminal, ['radio'], monkeypatch)
        assert 'MICROWAVE' in output

    def test_it_leaves_you_in_your_own_home(self, terminal, monkeypatch):
        self.run_login(terminal, ['switch'], monkeypatch)
        assert terminal.current_directory == '/usr/users/switch'
        assert terminal.username == 'switch'

    def test_a_wrong_name_is_refused_and_asked_again(self, terminal,
                                                     monkeypatch):
        output = self.run_login(terminal, ['nobody', 'radio'], monkeypatch)
        assert 'Login incorrect' in output
        assert terminal.username == 'radio'

    def test_root_is_refused(self, terminal, monkeypatch):
        output = self.run_login(terminal, ['root', 'sysop'], monkeypatch)
        assert 'Login incorrect' in output
        assert terminal.username == 'sysop'

    def test_a_question_mark_prints_the_roster(self, terminal, monkeypatch):
        output = self.run_login(terminal, ['?', 'tsps'], monkeypatch)
        assert 'Positions on this machine' in output

    def test_it_does_not_announce_what_you_just_typed(self, terminal,
                                                      monkeypatch):
        """
        A real machine does not tell you who you just said you were. The
        role picker's announcement belongs to --role, which nobody asked.
        """
        output = self.run_login(terminal, ['radio'], monkeypatch)
        assert 'Role selected:' not in output
        assert 'User ID:' not in output

    def test_role_still_announces_itself(self, terminal, capsys):
        """--role did not ask, so it says."""
        terminal.select_role(preselected=9)
        assert 'Role selected:' in capsys.readouterr().out

    def test_the_order_is_banner_then_motd_then_profile(self, terminal,
                                                        monkeypatch):
        """
        A real login did these three things in this order and nothing else
        in between. Getting the order wrong is how the switching desk once
        opened by being told it was not signed off on switching.
        """
        output = self.run_login(terminal, ['switch'], monkeypatch)
        assert (output.index('UNIX Version 7   tty01')
                < output.index('Copyright (c) 1979')
                < output.index('Alarm'))
