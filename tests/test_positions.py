"""
What is different about being put at one position rather than another.

The answer used to be: the help text, one qualification, and a home
directory that did not exist. pwd(1) named it and ls(1) said it was not
there, for eleven of the twelve positions.

Now each one has a home with a .profile that opens the desk on its own
work and a file left by whoever sat there last. These tests hold that
together: every role in the roster has a home, every home is reachable,
and no position opens on a command it is not signed off for.
"""

import pytest

from bell_system.constants import BELL_SYSTEM_ROLES
from bell_system.data.homes import HOMES
from bell_system.progression import ROLE_QUALIFICATIONS
from bell_system.terminal import BellSystemTerminal

ROLE_KEYS = [key for key, _ in BELL_SYSTEM_ROLES.values()]


@pytest.fixture
def at_position(isolated_state):
    """Return a factory that puts a fresh terminal at a named position."""
    def put(role_key):
        instance = BellSystemTerminal()
        instance.settings.set('game.ambience', 'off')
        name = next(name for key, name in BELL_SYSTEM_ROLES.values()
                    if key == role_key)
        instance._apply_role(role_key, name)
        return instance
    return put


class TestEveryPositionHasAHome:
    """The bug: pwd named a directory ls could not find."""

    def test_the_roster_and_the_homes_agree(self):
        """
        A role with no home is the bug this file exists for, and a home
        with no role is a directory nobody can ever be standing in.
        """
        assert set(HOMES) == set(ROLE_KEYS)

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_the_home_is_there_when_you_arrive(self, at_position, role_key):
        terminal = at_position(role_key)
        assert terminal.execute_command('pwd').strip() == f'/usr/users/{role_key}'
        listing = terminal.execute_command('ls')
        assert 'no such file or directory' not in listing

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_the_home_is_in_the_password_file(self, at_position, role_key):
        terminal = at_position(role_key)
        passwd = terminal.execute_command('cat /etc/passwd')
        assert f'{role_key}::' in passwd
        assert f'/usr/users/{role_key}' in passwd

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_each_home_has_a_profile(self, at_position, role_key):
        terminal = at_position(role_key)
        assert 'PATH' in terminal.execute_command('cat .profile')

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_each_home_has_something_left_in_it(self, at_position, role_key):
        """
        A position is different because of what the last person left, so
        every one of them has to have left something.
        """
        terminal = at_position(role_key)
        left = [name for name in HOMES[role_key] if name.endswith('notes')]
        assert left, role_key
        text = terminal.execute_command(f'cat {left[0]}')
        assert len(text.split('\n')) > 8


class TestTheProfileRuns:
    """login(1) reads .profile once, and each desk's does something else."""

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_a_position_opens_on_something(self, at_position, capsys, role_key):
        at_position(role_key)
        assert capsys.readouterr().out.strip()

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_nothing_opens_on_a_command_it_cannot_run(self, at_position,
                                                      capsys, role_key):
        """
        The profile runs after the position's own sign-off. It used to run
        before, so the switching desk opened by being told it was not
        signed off on switching.
        """
        at_position(role_key)
        opening = capsys.readouterr().out
        assert 'not signed off' not in opening, role_key
        assert 'command not found' not in opening, role_key
        assert 'no such file' not in opening, role_key

    def test_two_positions_open_differently(self, at_position, capsys):
        at_position('switch')
        switching = capsys.readouterr().out
        at_position('radio')
        radio = capsys.readouterr().out
        assert switching != radio
        assert 'Alarm' in switching
        assert 'MICROWAVE' in radio

    def test_the_profile_is_read_from_the_home_it_belongs_to(self, at_position):
        terminal = at_position('tsps')
        assert 'tsps' in terminal.execute_command('cat .profile')

    def test_assignments_are_not_run_as_commands(self, at_position, capsys):
        """
        There are no shell variables here to hold a PATH, so the assignment
        lines are passed over rather than being run and failing.
        """
        at_position('sysop')
        assert 'PATH' not in capsys.readouterr().out


class TestPositionsCarryTheirSignOff:
    """Being put at a desk qualifies you for that desk and nothing else."""

    @pytest.mark.parametrize('role_key,qualification',
                             sorted(ROLE_QUALIFICATIONS.items()))
    def test_the_desk_signs_you_off_for_itself(self, at_position, role_key,
                                               qualification):
        terminal = at_position(role_key)
        assert terminal.career.is_qualified(qualification)

    def test_it_does_not_sign_you_off_for_everything(self, at_position):
        terminal = at_position('custserv')
        held = set(terminal.career.qualifications)
        assert 'toll' not in held

    @pytest.mark.parametrize('role_key', ROLE_KEYS)
    def test_the_username_and_the_home_agree(self, at_position, role_key):
        terminal = at_position(role_key)
        assert terminal.username == role_key
        assert terminal.execute_command('logname').strip() == role_key


class TestTheSeparator:
    """A semicolon runs two commands, which is what the profiles need."""

    def test_two_commands_run_in_order(self, terminal):
        assert terminal.execute_command('echo one; echo two') == 'one\ntwo'

    def test_a_quoted_semicolon_is_not_a_separator(self, terminal):
        """sed 's/a/b/;s/c/d/' is one command, not two."""
        terminal.write_file('/tmp/t', 'abc\n')
        result = terminal.execute_command("echo 'one; two'")
        assert result.strip() == 'one; two'

    def test_an_empty_half_is_skipped(self, terminal):
        assert terminal.execute_command('echo one;').strip() == 'one'
        assert terminal.execute_command('; echo two').strip() == 'two'

    def test_it_composes_with_a_pipe(self, terminal):
        result = terminal.execute_command('echo one; who | wc -l')
        assert result.split('\n')[0] == 'one'
        assert result.split('\n')[1].strip().isdigit()
