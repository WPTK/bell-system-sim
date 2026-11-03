"""
A finished career hands on to the next one (A13).

Every career here is built by setting the saved fields the command reads, and
every state directory is the test's own (the autouse fixture sets
BELL_SYSTEM_HOME), so no test touches a real save.
"""

import json
import os

import pytest

from bell_system import legacy, save
from bell_system.filesystem import PRIOR, Node
from bell_system.npc import AUDIT_PASSED
from bell_system.settings import state_dir
from bell_system.terminal import BellSystemTerminal

PLAYER_FILE = '/usr/users/sysop/notes'


def finish(terminal, text='the sheath is wet on tuesdays\n'):
    """A career signed off at the last tour, with one file the player wrote."""
    career = terminal.career
    career.shift = 13
    career.reports_closed = 120
    career.finished = True
    career.audit_verdict = AUDIT_PASSED
    career.save()
    terminal.filesystem[PLAYER_FILE] = Node(
        'file', 'sysop', 'craft', '-rw-r--r--', text)
    save.write_home(terminal.home_file, terminal)


def state_files():
    return sorted(os.listdir(state_dir()))


class TestCareerStillWorks:
    def test_career_with_nothing_after_it_is_the_record(self, terminal):
        # Not compared with qual line for line: a command takes time, and
        # the standing advice at the foot moves with it.
        out = terminal.execute_command('career')
        assert out.startswith('Craft Record')
        assert 'Reports closed' in out

    def test_career_index_is_qual_index(self, terminal):
        assert terminal.execute_command('career index') \
            == terminal.execute_command('qual index')


class TestNewNeedsAFinishedCareer:
    def test_an_open_career_is_refused_and_untouched(self, terminal):
        before = state_files()
        out = terminal.execute_command('career new confirm')
        assert 'still open' in out
        assert state_files() == before
        assert not os.path.exists(legacy.legacy_path(state_dir()))

    def test_the_plan_moves_nothing_and_says_what_it_will_do(self, terminal):
        finish(terminal)
        before = state_files()
        out = terminal.execute_command('career new')
        assert 'career new confirm' in out
        assert 'not deleted' in out
        assert 'Nothing has been moved' in out
        assert state_files() == before

    def test_anything_but_the_exact_word_is_only_the_plan(self, terminal):
        finish(terminal)
        before = state_files()
        for line in ('career new yes', 'career new confirm now',
                     'career new CONFIRMED', 'career new CONFIRM',
                     'career new Confirm'):
            assert 'Nothing has been moved' in terminal.execute_command(line)
        assert state_files() == before


class TestConfirming:
    def test_the_career_is_moved_and_never_deleted(self, terminal):
        finish(terminal)
        kept = open(os.path.join(state_dir(), 'career.json')).read()
        out = terminal.execute_command('career new confirm')
        assert 'filed in' in out
        archive = os.path.join(state_dir(), 'archive', 'career-1')
        assert open(os.path.join(archive, 'career.json')).read() == kept
        assert os.path.exists(os.path.join(archive, 'home.json'))
        assert not os.path.exists(os.path.join(state_dir(), 'career.json'))
        assert os.path.exists(legacy.legacy_path(state_dir()))

    def test_the_session_writes_nothing_back_over_the_archive(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        terminal.execute_command('echo more > /usr/users/sysop/after')
        terminal.career.save()
        terminal.save_shift()
        assert not os.path.exists(os.path.join(state_dir(), 'career.json'))
        assert not os.path.exists(os.path.join(state_dir(), 'home.json'))
        assert not os.path.exists(os.path.join(state_dir(), 'shift.json'))

    def test_a_second_confirm_does_nothing(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        out = terminal.execute_command('career new confirm')
        assert 'already' in out.lower() or 'filed' in out
        assert not os.path.exists(
            os.path.join(state_dir(), 'archive', 'career-2'))

    def test_the_next_career_finds_the_files_and_the_note(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        nxt = BellSystemTerminal()
        assert nxt.career.shift == 1 and not nxt.career.finished
        assert nxt.filesystem[f'{PRIOR}/sysop/notes'].content \
            == 'the sheath is wet on tuesdays\n'
        note = nxt.filesystem[f'{PRIOR}/HANDOVER'].content
        assert 'Tours worked       13' in note
        assert 'Reports closed     120' in note
        assert 'passed' in note

    def test_they_are_not_the_next_players_own_files(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        nxt = BellSystemTerminal()
        nxt.execute_command('echo mine > /usr/users/sysop/mine')
        nxt.save_shift()
        text = open(nxt.home_file).read()
        assert 'mine' in text
        assert 'prior' not in text
        assert 'sheath' not in text

    def test_the_second_career_archives_beside_the_first(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        nxt = BellSystemTerminal()
        nxt.career.shift = 13
        nxt.career.finished = True
        nxt.career.audit_verdict = AUDIT_PASSED
        nxt.career.save()
        nxt.execute_command('career new confirm')
        assert sorted(os.listdir(os.path.join(state_dir(), 'archive'))) \
            == ['career-1', 'career-2']
        # The first legacy went with the first archive, not over the second.
        assert os.path.exists(os.path.join(
            state_dir(), 'archive', 'career-2', 'legacy.json'))
        third = BellSystemTerminal()
        assert third.filesystem[f'{PRIOR}/HANDOVER'].content.count('2') >= 1

    def test_nothing_is_moved_if_the_handover_cannot_be_written(
            self, terminal, monkeypatch):
        finish(terminal)
        before = state_files()

        def refuse(path, handed):
            raise OSError(28, 'No space left on device')

        monkeypatch.setattr(legacy, 'write', refuse)
        out = terminal.execute_command('career new confirm')
        assert 'Nothing was moved' in out
        assert state_files() == before
        assert not terminal._career_filed
        assert terminal.career.finished


class TestTheSessionEnds:
    def test_the_repl_ends_after_the_career_is_filed(
            self, terminal, monkeypatch, capsys):
        finish(terminal)
        lines = iter(['career new confirm'])

        def typed(*_):
            try:
                return next(lines)
            except StopIteration:
                raise AssertionError('the session kept going')

        monkeypatch.setattr('builtins.input', typed)
        terminal.run(role=1)
        assert 'Session terminated.' in capsys.readouterr().out
        assert not os.path.exists(os.path.join(state_dir(), 'career.json'))

    def test_the_locks_are_on_before_anything_is_moved(
            self, terminal, monkeypatch):
        finish(terminal)
        seen = {}

        def interrupted(state, where, moved):
            seen.update(path=terminal.career.path, shift=terminal.shift_file,
                        locked=terminal._home_locked)
            raise KeyboardInterrupt

        monkeypatch.setattr(legacy, 'set_aside', interrupted)
        with pytest.raises(KeyboardInterrupt):
            terminal.execute_command('career new confirm')
        assert seen == {'path': None, 'shift': '', 'locked': True}
        # Nothing was moved, so the session owns its career again.
        assert terminal.career.path and terminal.shift_file
        assert not terminal._home_locked and not terminal._career_filed

    def test_an_interrupt_after_a_move_puts_it_back(
            self, terminal, monkeypatch):
        finish(terminal)
        before = state_files()

        def half(state, where, moved):
            os.makedirs(where)
            os.replace(os.path.join(state, 'career.json'),
                       os.path.join(where, 'career.json'))
            moved.append('career.json')
            raise KeyboardInterrupt

        monkeypatch.setattr(legacy, 'set_aside', half)
        with pytest.raises(KeyboardInterrupt):
            terminal.execute_command('career new confirm')
        assert state_files() == before

    def test_a_file_that_cannot_be_put_back_is_said_where_it_is(
            self, terminal, monkeypatch):
        finish(terminal)

        def refuse(path, handed):
            raise OSError(28, 'No space left on device')

        real = os.replace

        def stubborn(source, target):
            if os.path.basename(target) == 'career.json' and \
                    'archive' in source:
                raise OSError(13, 'Permission denied')
            return real(source, target)

        monkeypatch.setattr(legacy, 'write', refuse)
        monkeypatch.setattr(legacy.os, 'replace', stubborn)
        out = terminal.execute_command('career new confirm')
        assert 'Nothing was moved' not in out
        assert 'career.json could not be moved back' in out
        assert 'archive' in out
        # Still locked: part of the career is in the archive.
        assert terminal._career_filed


class TestTheirFilesAreReadOnly:
    def next_career(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        return BellSystemTerminal()

    def test_nothing_can_be_written_under_prior(self, terminal):
        nxt = self.next_career(terminal)
        for line in (f'echo x > {PRIOR}/new', f'echo x >> {PRIOR}/sysop/notes',
                     f'mkdir {PRIOR}/dir', f'touch {PRIOR}/t'):
            assert 'permission denied' in nxt.execute_command(line), line
        nxt.execute_command('echo mine > /usr/users/sysop/mine')
        assert 'permission denied' in nxt.execute_command(
            f'mv /usr/users/sysop/mine {PRIOR}/mine')
        assert 'permission denied' in nxt.execute_command(
            f'cp /usr/users/sysop/mine {PRIOR}/copy')
        assert f'{PRIOR}/mine' not in nxt.filesystem
        assert f'{PRIOR}/new' not in nxt.filesystem

    def test_they_cannot_be_moved_or_removed_either(self, terminal):
        nxt = self.next_career(terminal)
        assert 'denied' in nxt.execute_command(
            f'mv {PRIOR}/sysop/notes /usr/users/sysop/n')
        nxt.execute_command(f'rm {PRIOR}/sysop/notes')
        assert f'{PRIOR}/sysop/notes' in nxt.filesystem

    def test_they_can_be_read_and_copied_out(self, terminal):
        nxt = self.next_career(terminal)
        assert 'sheath' in nxt.execute_command(f'cat {PRIOR}/sysop/notes')
        assert nxt.execute_command(
            f'cp {PRIOR}/sysop/notes /usr/users/sysop/mine') == ''
        assert 'sheath' in nxt.execute_command('cat /usr/users/sysop/mine')


class TestTheNoteCannotBeShadowed:
    def test_a_player_file_called_handover_is_not_carried(self, terminal):
        finish(terminal)
        terminal.filesystem['/usr/users/HANDOVER'] = Node(
            'file', 'sysop', 'craft', '-rw-r--r--', 'forged')
        assert legacy.NOTE_PATH not in terminal._handed_on().files

    def test_a_crafted_entry_does_not_replace_it(self, isolated_state):
        os.makedirs(state_dir(), exist_ok=True)
        with open(legacy.legacy_path(state_dir()), 'w') as handle:
            json.dump({'version': 1, 'generation': 1,
                       'note': ['real note'],
                       'files': {legacy.NOTE_PATH: {
                           'kind': 'file', 'content': 'forged'}}}, handle)
        started = BellSystemTerminal()
        assert started.filesystem[legacy.NOTE_PATH].content == 'real note\n'


class TestSeedingRefusesAFileAsADirectory:
    def test_an_entry_under_a_file_is_left_out(self):
        tree = {}
        handed = legacy.Legacy(1, ['n'], {
            f'{PRIOR}/a': 'file', f'{PRIOR}/a/b': 'under a file',
            f'{PRIOR}/c': None, f'{PRIOR}/c/d': 'fine'})
        legacy.seed(tree, handed)
        assert tree[f'{PRIOR}/a'].content == 'file'
        assert f'{PRIOR}/a/b' not in tree
        assert tree[f'{PRIOR}/c/d'].content == 'fine'

    def test_a_path_outside_prior_is_not_seeded(self):
        tree = {}
        legacy.seed(tree, legacy.Legacy(1, ['n'], {'/etc/x': 'no'}))
        assert '/etc/x' not in tree


class TestWhatIsHandedOn:
    def test_the_note_carries_totals_and_no_report(self, terminal):
        finish(terminal)
        note = '\n'.join(legacy.handover_note(terminal.career, 1))
        for word in ('TR-', 'open', 'short', 'ground', 'fault', 'code'):
            assert word not in note.lower().replace('open', '')

    def test_moo_and_other_players_paths_are_not_carried(self, terminal):
        finish(terminal)
        terminal.filesystem['/usr/games/moo_scores'] = Node(
            'file', 'root', 'other', '-rw-rw-rw-', 'sysop 7\n')
        terminal.execute_command('career new confirm')
        stored = json.load(open(legacy.legacy_path(state_dir())))
        assert all(path.startswith(PRIOR + '/') for path in stored['files'])
        assert not any('moo' in path for path in stored['files'])

    def test_files_over_the_cap_are_left_behind_and_the_rest_go(
            self, terminal):
        finish(terminal)
        terminal.filesystem['/usr/users/sysop/big'] = Node(
            'file', 'sysop', 'craft', '-rw-r--r--', 'x' * 70000)
        handed = terminal._handed_on()
        assert f'{PRIOR}/sysop/big' not in handed.files
        assert f'{PRIOR}/sysop/notes' in handed.files
        legacy.write(legacy.legacy_path(state_dir()), handed)
        assert os.path.getsize(legacy.legacy_path(state_dir())) \
            <= legacy.LEGACY_LIMIT

    def test_prior_files_are_not_handed_on_again(self, terminal):
        finish(terminal)
        terminal.execute_command('career new confirm')
        nxt = BellSystemTerminal()
        nxt.career.shift = 13
        nxt.career.finished = True
        nxt.career.audit_verdict = AUDIT_PASSED
        nxt.career.save()
        handed = nxt._handed_on()
        assert not any(path.startswith(f'{PRIOR}/prior')
                       or path == f'{PRIOR}/sysop/notes'
                       for path in handed.files)


class TestLoadingIsTolerant:
    def write(self, text):
        os.makedirs(state_dir(), exist_ok=True)
        with open(legacy.legacy_path(state_dir()), 'w') as handle:
            handle.write(text)

    def test_a_career_with_no_legacy_loads_as_before(self, raw_terminal):
        assert PRIOR not in raw_terminal.filesystem

    def test_a_save_from_before_this_existed_loads(self, terminal):
        # career.json and home.json as an older version wrote them, no
        # legacy.json beside them.
        terminal.career.save()
        again = BellSystemTerminal()
        assert again.career.shift == terminal.career.shift
        assert PRIOR not in again.filesystem

    def test_garbage_is_ignored(self, isolated_state):
        for text in ('', 'not json', '[]', '{"version": 9}',
                     '{"version": 1, "generation": "x", "files": {}}',
                     '{"version": 1, "generation": 1, "files": []}'):
            self.write(text)
            assert PRIOR not in BellSystemTerminal().filesystem, text

    def test_an_oversize_file_is_ignored(self, isolated_state):
        self.write(' ' * (legacy.LEGACY_LIMIT + 1))
        assert legacy.load(legacy.legacy_path(state_dir())) is None

    def test_a_path_outside_prior_is_refused(self, isolated_state):
        entry = {'kind': 'file', 'content': 'x'}
        self.write(json.dumps({
            'version': 1, 'generation': 1, 'note': ['hi'],
            'files': {'/bin/sh': entry, '/usr/users/sysop/x': entry,
                      f'{PRIOR}/../../bin/sh': entry,
                      f'{PRIOR}/ok': entry}}))
        started = BellSystemTerminal()
        assert getattr(started.filesystem.get('/bin/sh'), 'content', '') != 'x'
        assert '/usr/users/sysop/x' not in started.filesystem
        assert started.filesystem[f'{PRIOR}/ok'].content == 'x'

    def test_a_damaged_entry_costs_only_itself(self, isolated_state):
        self.write(json.dumps({
            'version': 1, 'generation': 2, 'note': ['hi', 7],
            'files': {f'{PRIOR}/a': {'kind': 'file', 'content': 5},
                      f'{PRIOR}/b': {'kind': 'file', 'content': 'kept'},
                      f'{PRIOR}/c': 'nope'}}))
        started = BellSystemTerminal()
        assert started.filesystem[f'{PRIOR}/b'].content == 'kept'
        assert f'{PRIOR}/a' not in started.filesystem
        assert f'{PRIOR}/c' not in started.filesystem
