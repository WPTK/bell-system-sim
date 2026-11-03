"""
The thread of the last holder of the position.

The files that tell it are shut behind groups, one more group with each
sign-off, so that a career has a new file to read when it passes one and the
su log, which asks a question, is answered four sign-offs later. These check
that each sign-off opens something, that the order is the story's order,
and that the machine records the player in the group it gives.
"""

from datetime import datetime

import pytest

from bell_system.data import finds as data
from bell_system.screens import shell

from bell_system.progression import QUALIFICATIONS_BY_KEY

LETTER = '/usr/users/sysop/dead.letter'
SENT = '/usr/spool/mail/ehalloran'
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
                and not path.startswith('/dev/')
                and (path == SENT or not path.startswith('/usr/spool/mail/'))}
        assert shut == set(OPENED_BY.values())

    def test_a_full_career_reads_everything(self, raw_terminal):
        everything = {path for path, node in
                      held(raw_terminal, 5).filesystem.items()
                      if not node.is_dir
                      and not path.startswith('/dev/')
                      and (path == SENT
                           or not path.startswith('/usr/spool/mail/'))}
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

    def test_a_practical_that_is_passed_gives_the_group(self, terminal):
        """Passing the third practical is where adm and the log line are."""
        career = terminal.career
        career.qualifications = ['loop', 'frame']
        career.groups = []
        career.granted = {}
        career.reports_correct = (
            QUALIFICATIONS_BY_KEY['office'].requires_reports
            * career.difficulty.reports_per_qualification)
        terminal.execute_command('qual take office')
        _, report = terminal._practical_open()
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'switch clear {report.number}')
        assert 'passed' in terminal.execute_command('qual submit')
        assert 'adm' in terminal.career.groups
        assert 'adm' in terminal.career.granted
        assert f'ehalloran-{terminal.username}' in (
            terminal._read(SULOG) or '')

    def test_membership_is_the_sign_offs_and_not_the_record(
            self, raw_terminal):
        """What is written in career.groups cannot add a group."""
        held(raw_terminal, 1)
        raw_terminal.career.groups = ['craft', 'sys', 'mgmt']
        assert raw_terminal._groups() == frozenset({'craft'})

    def test_the_line_is_not_written_before_there_is_a_position(
            self, raw_terminal):
        held(raw_terminal, 3)
        raw_terminal.career.granted = {'adm': 600}
        raw_terminal._add_generated_files()
        assert 'ehalloran-switch' not in (raw_terminal._read(SULOG) or '')

    def test_the_line_stays_where_it_was_put(self, raw_terminal):
        held(raw_terminal, 3)
        raw_terminal.sync_groups()
        before = raw_terminal._read(SULOG)
        raw_terminal.sync_groups()
        assert raw_terminal._read(SULOG) == before

    def test_the_line_is_after_the_last_shipped_one(self, raw_terminal):
        """A grant is never stamped before Halloran's 06:15 su."""
        held(raw_terminal, 3)
        raw_terminal.clock.now = lambda: datetime(1983, 11, 14, 5, 0)
        raw_terminal.sync_groups()
        rows = (raw_terminal._read(SULOG) or '').splitlines()
        mine = [n for n, row in enumerate(rows) if 'ehalloran-switch' in row]
        assert mine and rows[mine[0]][3:14] >= '11/14 06:16'
        assert rows == sorted(rows, key=lambda row: row[3:14])

    def test_a_real_clock_is_clamped_into_the_game(self, raw_terminal):
        held(raw_terminal, 3)
        raw_terminal.clock.now = lambda: datetime(2026, 11, 3, 9, 0)
        raw_terminal.sync_groups()
        rows = (raw_terminal._read(SULOG) or '').splitlines()
        mine = [row for row in rows if 'ehalloran-switch' in row][0]
        assert mine[3:14] == '12/31 23:59'
        assert raw_terminal.career.granted['adm'] > 0


class TestTheLadderIsNotOpenedByChmod:
    """A file the position does not own is not its to change."""

    def test_chmod_does_not_open_the_next_file(self, raw_terminal):
        held(raw_terminal, 1)
        reply = raw_terminal.execute_command(f'chmod 644 {SENT}')
        assert reply == f'chmod: {SENT}: not owner'
        assert SENT not in readable(raw_terminal)

    def test_rm_and_mv_are_refused_too(self, raw_terminal):
        held(raw_terminal, 3)
        assert raw_terminal.execute_command(f'rm {SULOG}') == (
            f'rm: {SULOG}: permission denied')
        assert raw_terminal.execute_command(f'mv {SULOG} /tmp/x') == (
            f'mv: {SULOG}: permission denied')
        assert SULOG in raw_terminal.filesystem

    def test_the_position_still_manages_its_own_files(self, raw_terminal):
        raw_terminal.username = 'sysop'
        assert raw_terminal.execute_command(f'chmod 600 {LETTER}') == ''
        assert raw_terminal.filesystem[LETTER].mode == '-rw-------'

    def test_the_handover_is_in_the_chiefs_mailbox(self, raw_terminal):
        """In the mail spool, where mail is, and on the second rung."""
        node = held(raw_terminal, 2).filesystem[SENT]
        assert (node.owner, node.group) == ('ehalloran', 'uucp')
        assert SENT in readable(raw_terminal)
        assert SENT not in readable(held(raw_terminal, 1))


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

    def test_halloran_does_not_say_why(self):
        """He reopened them; the reader works out the rest."""
        text = data.REOPENED.lower()
        for word in ('no trouble found', 'ntf', 'twenty', 'closed',
                     'alvarez', 'those are'):
            assert word not in text
