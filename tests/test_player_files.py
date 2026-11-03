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


def room_for(terminal, path):
    """How long a file at this path may be before the home is full."""
    terminal.write_file(path, '')
    return PLAYER_LIMIT - save.home_size(terminal.filesystem)


class TestTheCap:
    def test_a_write_past_the_cap_is_refused_with_a_message(self, raw_terminal):
        error = raw_terminal.write_file('/usr/users/sysop/big',
                                        'x' * (PLAYER_LIMIT + 1))
        assert error and 'no space left' in error and '64 KB' in error
        assert '/usr/users/sysop/big' not in raw_terminal.filesystem

    def test_a_write_to_the_cap_is_taken_and_one_byte_over_is_not(
            self, raw_terminal):
        room = room_for(raw_terminal, '/usr/users/sysop/full')
        assert raw_terminal.write_file('/usr/users/sysop/full',
                                       'x' * room) is None
        assert save.home_size(raw_terminal.filesystem) == PLAYER_LIMIT
        assert raw_terminal.write_file('/usr/users/sysop/full',
                                       'x' * (room + 1)) is not None

    def test_the_cap_is_for_everything_together(self, raw_terminal):
        room = room_for(raw_terminal, '/usr/users/sysop/a')
        assert raw_terminal.write_file('/usr/users/sysop/a',
                                       'x' * (room - 10)) is None
        assert raw_terminal.write_file('/usr/users/sysop/b',
                                       'y' * 20) is not None

    def test_rewriting_a_file_does_not_count_it_twice(self, raw_terminal):
        room = room_for(raw_terminal, '/usr/users/sysop/a')
        for _ in range(3):
            assert raw_terminal.write_file('/usr/users/sysop/a',
                                           'x' * (room - 10)) is None

    def test_the_refusal_reaches_the_shell(self, raw_terminal):
        room = room_for(raw_terminal, '/usr/users/sysop/a')
        raw_terminal.write_file('/usr/users/sysop/a', 'x' * room)
        said = raw_terminal.execute_command('echo more > ~/b')
        assert 'no space left' in said

    def test_elsewhere_is_not_capped_and_not_kept(self, raw_terminal):
        assert raw_terminal.write_file('/tmp/scratch',
                                       'x' * (PLAYER_LIMIT * 2)) is None
        assert '/tmp/scratch' not in save.home_record(
            raw_terminal.filesystem)['nodes']


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
        # What was refused is refused; what was fine is kept.
        assert terminal.filesystem['/bin/ls'].content != 'evil'
        assert terminal.filesystem['/usr/users/sysop/ok'].content == 'fine'

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


def home_file():
    import os
    return os.path.join(state_dir(), 'home.json')


def put(text):
    with open(home_file(), 'w') as handle:
        handle.write(text)


def node(text='x', kind='file'):
    return {'kind': kind, 'owner': 'a', 'group': 'b',
            'mode': '-rw-r--r--' if kind == 'file' else 'drwxr-xr-x',
            'content': text if kind == 'file' else None}


def record(nodes, removed=()):
    return json.dumps({'version': save.HOME_VERSION, 'nodes': nodes,
                       'removed': list(removed)})


class TestOneBadEntryCostsOneEntry:
    def test_the_good_files_are_kept(self, isolated_state):
        put(record({'/usr/users/sysop/good': node('kept'),
                    '/usr/users/sysop/odd': node('x', kind='pipe'),
                    '/usr/users/sysop/none': 'not a node'}))
        terminal = BellSystemTerminal()
        assert terminal.filesystem['/usr/users/sysop/good'].content == 'kept'
        assert '/usr/users/sysop/odd' not in terminal.filesystem
        assert '/usr/users/sysop/none' not in terminal.filesystem

    def test_the_player_is_told_once_and_the_original_is_kept(
            self, isolated_state):
        import os
        original = record({'/usr/users/sysop/good': node(),
                           '/usr/users/sysop/odd': node(kind='pipe')})
        put(original)
        terminal = BellSystemTerminal()
        assert 'home.json.bad' in terminal.home_notice
        assert '1 of your saved files' in terminal.home_notice
        with open(home_file() + '.bad') as handle:
            assert handle.read() == original
        terminal.save_shift()
        # The cleaned record is what is on disk now; the original is aside.
        with open(home_file()) as handle:
            assert list(json.load(handle)['nodes']) == [
                '/usr/users/sysop/good']
        assert os.path.exists(home_file() + '.bad')

    def test_nothing_to_say_when_nothing_is_wrong(self, raw_terminal):
        raw_terminal.execute_command('echo hi > ~/a')
        raw_terminal.save_shift()
        assert BellSystemTerminal().home_notice is None

    @pytest.mark.parametrize('key', [
        '/usr/users/sysop/../sysop/x',
        '/usr/users//sysop/x',
        '/usr/users/sysop/./x',
        '/usr/users/sysop/x/',
    ])
    def test_a_key_the_shell_would_not_spell_is_left_out(
            self, isolated_state, key):
        put(record({key: node()}))
        terminal = BellSystemTerminal()
        assert key not in terminal.filesystem
        assert '/usr/users/sysop/x' not in terminal.filesystem

    def test_a_file_with_no_directory_is_left_out(self, isolated_state):
        put(record({'/usr/users/sysop/nodir/file': node()}))
        assert '/usr/users/sysop/nodir/file' not in (
            BellSystemTerminal().filesystem)

    def test_a_directory_in_the_file_makes_its_contents_welcome(
            self, isolated_state):
        put(record({'/usr/users/sysop/work/file': node(),
                    '/usr/users/sysop/work': node(kind='dir')}))
        terminal = BellSystemTerminal()
        assert '/usr/users/sysop/work/file' in terminal.filesystem
        assert terminal.home_notice is None


class TestAFileThatDidNotLoadIsNotWrittenOver:
    @pytest.mark.parametrize('text', [
        '{not json', '[]', '{"version": 99, "nodes": {}, "removed": []}',
        '{"version": 1, "nodes": 4, "removed": []}'])
    def test_it_is_set_aside_and_the_player_goes_on(self, isolated_state, text):
        import os
        put(text)
        terminal = BellSystemTerminal()
        assert 'could not be read' in terminal.home_notice
        assert not os.path.exists(home_file())
        terminal.execute_command('echo new > ~/note')
        terminal.save_shift()
        with open(home_file() + '.bad') as handle:
            assert handle.read() == text
        assert BellSystemTerminal().execute_command('cat ~/note') == 'new'

    def test_over_the_cap_is_set_aside_too(self, isolated_state):
        import os
        put(record({'/usr/users/sysop/big': node('x' * PLAYER_LIMIT)}))
        terminal = BellSystemTerminal()
        assert '/usr/users/sysop/big' not in terminal.filesystem
        assert os.path.exists(home_file() + '.bad')

    def test_if_it_cannot_be_set_aside_nothing_is_written(
            self, isolated_state, monkeypatch):
        import os
        put('{not json')

        def refuse(*args, **kwargs):
            raise OSError('read-only')
        monkeypatch.setattr(os, 'replace', refuse)
        terminal = BellSystemTerminal()
        assert 'none will be saved' in terminal.home_notice
        terminal.execute_command('echo new > ~/note')
        terminal.save_shift()
        with open(home_file()) as handle:
            assert handle.read() == '{not json'


class TestWritingIsAllOrNothing:
    def test_a_failure_part_way_leaves_the_old_file(
            self, raw_terminal, monkeypatch):
        import os
        raw_terminal.execute_command('echo first > ~/note')
        raw_terminal.save_shift()
        with open(home_file()) as handle:
            before = handle.read()

        def refuse(*args, **kwargs):
            raise OSError('disk full')
        monkeypatch.setattr(os, 'replace', refuse)
        raw_terminal.execute_command('echo second > ~/note')
        raw_terminal.save_shift()
        with open(home_file()) as handle:
            assert handle.read() == before
        assert [name for name in os.listdir(state_dir())
                if name.endswith('.tmp')] == []

    def test_a_crash_while_writing_never_shortens_the_file(
            self, tmp_path, monkeypatch):
        from bell_system import jsonfile
        target = tmp_path / 'f.json'
        target.write_text('old')
        real_fdopen = jsonfile.os.fdopen

        def dying(descriptor, *args, **kwargs):
            handle = real_fdopen(descriptor, *args, **kwargs)
            handle.write('ne')
            handle.close()
            raise KeyboardInterrupt
        monkeypatch.setattr(jsonfile.os, 'fdopen', dying)
        with pytest.raises(KeyboardInterrupt):
            jsonfile.write_text_atomically(str(target), 'new text')
        assert target.read_text() == 'old'
        assert [path.name for path in tmp_path.iterdir()] == ['f.json']


class TestTheCapHoldsOnEveryRoute:
    FULL = PLAYER_LIMIT - 4000

    def test_mv_from_elsewhere_cannot_get_round_it(self, raw_terminal):
        raw_terminal.write_file('/tmp/big', 'x' * (PLAYER_LIMIT * 2))
        said = raw_terminal.execute_command('mv /tmp/big ~/big')
        assert 'no space left' in said and '64 KB' in said
        assert '/usr/users/sysop/big' not in raw_terminal.filesystem
        assert '/tmp/big' in raw_terminal.filesystem

    def test_cc_cannot_get_round_it(self, raw_terminal):
        raw_terminal.write_file(
            '/tmp/t.c', 'main() { printf("%s"); }'.replace(
                '%s', 'x' * (PLAYER_LIMIT * 2)))
        said = raw_terminal.execute_command('cc /tmp/t.c -o ~/a.out')
        assert 'no space left' in said
        assert '/usr/users/sysop/a.out' not in raw_terminal.filesystem
        assert raw_terminal.run_compiled('/usr/users/sysop/a.out') is None

    def test_directories_and_long_names_count(self, raw_terminal):
        refused = ''
        for number in range(2000):
            refused = raw_terminal.cmd_mkdir(
                [f"~/{'d' * 200}{number}"])
            if refused:
                break
        assert 'no space left' in refused
        assert save.home_size(raw_terminal.filesystem) <= PLAYER_LIMIT

    def test_the_file_never_holds_more_than_the_cap(self, raw_terminal):
        """What it holds is held to the cap; the stamps ride on top of it."""
        import json
        import os
        for number in range(200):
            raw_terminal.write_file(f'/usr/users/sysop/f{number}',
                                    'x' * 1000)
        raw_terminal.save_shift()
        written = os.path.getsize(raw_terminal.home_file)
        with open(raw_terminal.home_file, encoding='utf-8') as handle:
            record = json.load(handle)
        unstamped = len(json.dumps(save.home_record(
            raw_terminal.filesystem, times=False), indent=1,
            sort_keys=True).encode()) + 1
        assert unstamped <= PLAYER_LIMIT
        # A stamp is a short string a file; it is bounded by the file count.
        assert written <= PLAYER_LIMIT + 40 * len(record['nodes'])

    def test_a_refused_mv_puts_the_source_back(self, raw_terminal):
        raw_terminal.write_file('/usr/users/sysop/a', 'x' * self.FULL)
        raw_terminal.write_file('/tmp/b', 'y' * 9000)
        raw_terminal.execute_command('mv /tmp/b ~/b')
        assert '/tmp/b' in raw_terminal.filesystem
        assert raw_terminal.filesystem['/usr/users/sysop/a'].content == (
            'x' * self.FULL)

    def test_chmod_goes_through_the_same_door(self, raw_terminal):
        raw_terminal.write_file('/usr/users/sysop/a', 'x' * 10)
        assert raw_terminal.execute_command('chmod 600 ~/a') == ''
        assert raw_terminal.filesystem['/usr/users/sysop/a'].mode == (
            '-rw-------')


class TestDeeplyNestedJson:
    NEST = '[' * 100000

    @pytest.mark.parametrize('name', ['home.json', 'career.json',
                                      'settings.json', 'shift.json'])
    def test_it_is_a_bad_file_and_not_a_crash(self, isolated_state, name):
        import os
        with open(os.path.join(state_dir(), name), 'w') as handle:
            handle.write(self.NEST)
        assert BellSystemTerminal().filesystem

    def test_the_shared_reader_says_nothing_rather_than_raise(self, tmp_path):
        from bell_system.jsonfile import read_json
        target = tmp_path / 'deep.json'
        target.write_text(self.NEST)
        assert read_json(str(target)) is None
        assert read_json(str(tmp_path / 'missing.json')) is None
        assert read_json(None) is None
        target.write_bytes(b'\xff\xfe not text')
        assert read_json(str(target)) is None
