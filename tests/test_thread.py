"""
The thread of the last holder of the position.

The files that tell it are shut behind groups, one more group with each
sign-off, so that a career has a new file to read when it passes one and the
su log, which asks a question, is answered four sign-offs later. These check
that each sign-off opens something, that the order is the story's order,
and that the machine records the player in the group it gives.
"""

import pytest

from bell_system.data import finds as data
from bell_system.screens import shell

LETTER = '/usr/users/sysop/dead.letter'
SENT = '/usr/spool/uucp/D.mhuxcoB0212'
SULOG = '/usr/adm/sulog'
LMOSLOG = '/usr/adm/lmoslog'
REOPENED = '/usr/users/ehalloran/reopened'

# What each sign-off opens, by how many are held.
OPENED_BY = {1: LETTER, 2: SENT, 3: SULOG, 4: LMOSLOG, 5: REOPENED}


def held(terminal, count):
    """Put a position in the state of having passed this many sign-offs."""
    terminal.username = 'switch'
    terminal.career.groups = []
    terminal.career.granted = {}
    terminal.career.qualifications = ['q%d' % n for n in range(count)]
    return terminal


def at_tour(terminal, tour):
    """Move a position to a tour and file what arrives by it."""
    terminal.career.shift = tour
    terminal.deliver_news()
    return terminal


def readable(terminal):
    """Every file this position may read."""
    return {path for path, node in terminal.filesystem.items()
            if not node.is_dir and terminal._may_read(path)}


class TestEachSignOffOpensAFile:
    """The predecessor thread is gated by groups, one more with each."""

    @pytest.mark.parametrize('count', [1, 2, 3, 4, 5])
    def test_each_sign_off_makes_a_new_file_readable(
            self, raw_terminal, count):
        before = readable(held(raw_terminal, count - 1))
        after = readable(held(raw_terminal, count))
        assert after - before

    @pytest.mark.parametrize('count,path', sorted(OPENED_BY.items()))
    def test_and_it_is_the_one_the_thread_says(
            self, raw_terminal, count, path):
        assert path not in readable(held(raw_terminal, count - 1))
        assert path in readable(held(raw_terminal, count))

    def test_the_files_open_in_order(self, raw_terminal):
        """Nothing later in the thread is readable ahead of its turn."""
        for count in range(0, 5):
            opened = readable(held(raw_terminal, count))
            for later, path in OPENED_BY.items():
                if later > count:
                    assert path not in opened

    def test_the_refusal_is_the_one_every_unix_gives(self, raw_terminal):
        held(raw_terminal, 0)
        assert raw_terminal.execute_command(f'cat {REOPENED}') == (
            f'cat: {REOPENED}: permission denied')

    def test_the_listing_shows_why(self, raw_terminal):
        listing = raw_terminal.execute_command('ls -l /usr/adm')
        sulog = [row for row in listing.splitlines() if 'sulog' in row][0]
        assert sulog.startswith('-rw-r-----')
        assert ' adm ' in sulog

    def test_the_position_that_owns_a_file_always_reads_it(
            self, raw_terminal):
        held(raw_terminal, 0)
        raw_terminal.username = 'sysop'
        assert LETTER in readable(raw_terminal)

    def test_nothing_unrelated_is_shut(self, raw_terminal):
        """
        A mode column that means something on a handful of files is a
        puzzle. One that means something on forty is an obstacle course.
        """
        shut = {path for path, node in held(raw_terminal, 0).filesystem.items()
                if not node.is_dir and not raw_terminal._may_read(path)
                and not path.startswith(('/dev/', '/usr/spool/mail/'))}
        assert shut == set(OPENED_BY.values()) | {
            '/usr/users/ehalloran/reopened'}

    def test_a_full_career_reads_everything(self, raw_terminal):
        everything = {path for path, node in
                      held(raw_terminal, 5).filesystem.items()
                      if not node.is_dir
                      and not path.startswith(('/dev/', '/usr/spool/mail/'))}
        assert readable(raw_terminal) >= everything


class TestTheGroupsAreRecorded:
    """The wire chief puts you in a group, and the log has your name."""

    def test_a_sign_off_puts_you_in_its_group(self, raw_terminal):
        held(raw_terminal, 2)
        raw_terminal.sync_groups()
        assert {'craft', 'uucp'} <= set(raw_terminal.career.groups)
        assert 'adm' not in raw_terminal.career.groups

    def test_the_log_has_your_name_at_three(self, raw_terminal):
        held(raw_terminal, 3)
        raw_terminal.sync_groups()
        said = raw_terminal._read(SULOG) or ''
        assert 'ehalloran-switch' in said
        assert '+ tty01 ehalloran-switch' in said

    def test_the_log_does_not_have_it_at_two(self, raw_terminal):
        held(raw_terminal, 2)
        raw_terminal.sync_groups()
        assert 'ehalloran-switch' not in (raw_terminal._read(SULOG) or '')

    def test_syncing_again_does_not_write_it_twice(self, raw_terminal):
        held(raw_terminal, 3)
        for _ in range(3):
            raw_terminal.sync_groups()
        assert (raw_terminal._read(SULOG) or '').count('ehalloran-switch') == 1

    def test_the_group_file_has_you_in_what_you_hold(self, raw_terminal):
        held(raw_terminal, 3)
        rows = {row.split(':')[0]: row.split(':')[3].split(',')
                for row in (raw_terminal._read('/etc/group') or '').split()}
        assert 'switch' in rows['adm'] and 'switch' in rows['craft']
        assert 'switch' not in rows['sys']

    def test_a_sign_off_taken_at_the_practical_syncs(self, raw_terminal):
        """Passing a practical is where the groups are given."""
        import inspect
        from bell_system.screens import practical
        assert 'sync_groups' in inspect.getsource(practical)


class TestTheRegistry:
    """The data holds together."""

    def test_the_third_group_is_the_one_the_shell_names(self):
        assert data.ADM_GROUP_QUALIFICATIONS == shell.ADM_GROUP_QUALIFICATIONS
        assert data.GROUP_FOR_SIGN_OFF[data.ADM_GROUP_QUALIFICATIONS] == 'adm'

    def test_nobody_gives_alvarez_a_pronoun(self):
        """The last holder is never she, he or they in the machine's voice."""
        import re
        from bell_system.data.homes import HOMES
        pronoun = re.compile(r'\b(he|she|his|her|him|hers|himself|herself)\b',
                             re.IGNORECASE)
        texts = [f.text or '' for f in data.FRAGMENTS]
        texts.append(HOMES['sysop'].get('dead.letter', ''))
        for text in texts:
            if 'alvarez' in text.lower() and 'halloran' not in text.lower():
                assert not pronoun.search(text)

    def test_the_twenty_nine_adds_up(self):
        """Halloran's number is Alvarez's log's number."""
        rows = [line.split() for line in data.TESTLOG.splitlines()]
        week = [int(row[4]) for row in rows if row[0] >= '11/07']
        assert sum(week) == 29
        assert 'twenty-nine no trouble found' in data.REOPENED
