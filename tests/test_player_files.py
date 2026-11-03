"""
What the player writes survives a restart.

The shipped filesystem is rebuilt every time the terminal starts, so the only
thing worth saving is the difference: files and directories under the home
directories, and the moo scoreboard.
"""

import json

import pytest

from bell_system import save
from bell_system.filesystem import FILESYSTEM, MOO_SCORES, PLAYER_LIMIT
from bell_system.settings import state_dir
from bell_system.terminal import BellSystemTerminal


def restart(terminal):
    """Do what the interactive loop does after a command, then start again."""
    terminal.save_shift()
    return BellSystemTerminal()


def test_a_note_written_with_echo_survives_a_restart(raw_terminal):
    raw_terminal.execute_command('echo remember the sulog > ~/note')
    again = restart(raw_terminal)
    assert again.execute_command('cat ~/note') == 'remember the sulog'


def test_a_file_written_with_ed_survives_a_restart(raw_terminal):
    raw_terminal.write_file('/usr/users/sysop/draft', 'one\ntwo\n')
    assert restart(raw_terminal).execute_command(
        'cat ~/draft').splitlines() == ['one', 'two']


def test_a_directory_and_what_is_in_it_survive(raw_terminal):
    raw_terminal.execute_command('mkdir ~/work')
    raw_terminal.execute_command('echo x > ~/work/a')
    again = restart(raw_terminal)
    assert again.execute_command('ls ~/work') == 'a'


def test_the_moo_scoreboard_survives(raw_terminal):
    raw_terminal.username = 'sysop'
    raw_terminal._moo_secret = '1234'
    raw_terminal.execute_command('moo 1234')
    board = raw_terminal.filesystem[MOO_SCORES].content
    assert board != FILESYSTEM[MOO_SCORES].content
    again = restart(raw_terminal)
    assert again.filesystem[MOO_SCORES].content == board


def test_a_file_the_player_removed_stays_removed(raw_terminal):
    shipped = [path for path in FILESYSTEM
               if path.startswith('/usr/users/') and not FILESYSTEM[path].is_dir]
    assert shipped
    del raw_terminal.filesystem[shipped[0]]
    again = restart(raw_terminal)
    assert shipped[0] not in again.filesystem


def test_nothing_is_written_for_a_player_who_wrote_nothing(raw_terminal):
    raw_terminal.save_shift()
    import os
    assert not os.path.exists(raw_terminal.home_file)


def test_it_survives_the_handoff_that_clears_the_shift(raw_terminal):
    raw_terminal.execute_command('echo kept > ~/note')
    raw_terminal.save_shift()
    save.discard(raw_terminal.shift_file)
    assert BellSystemTerminal().execute_command('cat ~/note') == 'kept'


class TestTheCap:
    def test_a_write_past_the_cap_is_refused_with_a_message(self, raw_terminal):
        error = raw_terminal.write_file('/usr/users/sysop/big',
                                        'x' * (PLAYER_LIMIT + 1))
        assert error and 'no space left' in error and '64 KB' in error
        assert '/usr/users/sysop/big' not in raw_terminal.filesystem

    def test_a_write_to_the_cap_is_taken(self, raw_terminal):
        assert raw_terminal.write_file('/usr/users/sysop/full',
                                       'x' * PLAYER_LIMIT) is None

    def test_the_cap_is_for_everything_together(self, raw_terminal):
        assert raw_terminal.write_file('/usr/users/sysop/a',
                                       'x' * (PLAYER_LIMIT - 10)) is None
        assert raw_terminal.write_file('/usr/users/sysop/b',
                                       'y' * 20) is not None

    def test_rewriting_a_file_does_not_count_it_twice(self, raw_terminal):
        for _ in range(3):
            assert raw_terminal.write_file('/usr/users/sysop/a',
                                           'x' * (PLAYER_LIMIT - 10)) is None

    def test_the_refusal_reaches_the_shell(self, raw_terminal):
        raw_terminal.write_file('/usr/users/sysop/a', 'x' * PLAYER_LIMIT)
        said = raw_terminal.execute_command('echo more > ~/b')
        assert 'no space left' in said

    def test_elsewhere_is_not_capped_and_not_kept(self, raw_terminal):
        assert raw_terminal.write_file('/tmp/scratch',
                                       'x' * (PLAYER_LIMIT * 2)) is None
        assert '/tmp/scratch' not in save.capture_home(raw_terminal)['nodes']


class TestAHandEditedFile:
    def home(self):
        import os
        return os.path.join(state_dir(), 'home.json')

    def write(self, record):
        with open(self.home(), 'w') as handle:
            json.dump(record, handle)

    def node(self, text='x'):
        return {'kind': 'file', 'owner': 'a', 'group': 'b',
                'mode': '-rw-r--r--', 'content': text}

    def test_it_cannot_rewrite_the_rest_of_the_machine(self, isolated_state):
        self.write({'version': save.HOME_VERSION, 'removed': ['/bin/ls'],
                    'nodes': {'/bin/ls': self.node('evil'),
                              '/usr/users/sysop/ok': self.node('fine')}})
        terminal = BellSystemTerminal()
        # Nothing in it is applied, because part of it was refused.
        assert terminal.filesystem['/bin/ls'].content != 'evil'
        assert '/usr/users/sysop/ok' not in terminal.filesystem

    def test_a_record_over_the_cap_is_ignored(self, isolated_state):
        self.write({'version': save.HOME_VERSION, 'removed': [],
                    'nodes': {'/usr/users/sysop/big':
                              self.node('x' * (PLAYER_LIMIT + 1))}})
        assert '/usr/users/sysop/big' not in BellSystemTerminal().filesystem

    @pytest.mark.parametrize('text', ['{not json', '[]', '{"version": 99}',
                                      '{"version": 1}',
                                      '{"version": 1, "nodes": 4, '
                                      '"removed": []}'])
    def test_damage_does_not_stop_a_session(self, isolated_state, text):
        with open(self.home(), 'w') as handle:
            handle.write(text)
        assert BellSystemTerminal().filesystem

    def test_a_file_in_a_home_that_is_gone_is_dropped(self, isolated_state):
        self.write({'version': save.HOME_VERSION, 'removed': [],
                    'nodes': {'/usr/users/nobody/note': self.node()}})
        assert '/usr/users/nobody/note' not in BellSystemTerminal().filesystem
