"""
The shell: moving around, reading files, and pipes.

None of this existed. The filesystem was ten directories whose listings named
files that were not there, 724 bytes of content in total, and no way to change
directory or read anything. Sitting at a Seventh Edition machine is what the
simulation is for, so these cover the part that makes it a machine.
"""

import pytest

from bell_system.filesystem import FILESYSTEM, children, normalise


class TestPathResolution:
    """Paths behave the way a shell resolves them."""

    @pytest.mark.parametrize('path,cwd,expected', [
        ('/etc', '/', '/etc'),
        ('etc', '/', '/etc'),
        ('doc', '/usr', '/usr/doc'),
        ('..', '/usr/doc', '/usr'),
        ('../src', '/usr/doc', '/usr/src'),
        ('.', '/usr', '/usr'),
        ('./doc', '/usr', '/usr/doc'),
        ('~', '/', '/usr/users/sysop'),
        ('~/notes', '/etc', '/usr/users/sysop/notes'),
        ('/usr/../etc', '/', '/etc'),
        ('', '/usr', '/usr'),
    ])
    def test_paths_resolve(self, path, cwd, expected):
        assert normalise(path, cwd) == expected

    def test_you_cannot_climb_above_the_root(self):
        assert normalise('../../../..', '/usr') == '/'


class TestTheTreeIsReal:
    """Every listed entry exists, which was not true before."""

    def test_children_come_from_the_tree_not_a_list(self):
        assert 'doc' in children('/usr', FILESYSTEM)
        assert 'divestiture' in children('/usr/doc', FILESYSTEM)

    def test_every_node_has_a_parent_directory(self):
        for path in FILESYSTEM:
            if path == '/':
                continue
            parent = path.rsplit('/', 1)[0] or '/'
            assert parent in FILESYSTEM, f'{path} has no parent {parent}'
            assert FILESYSTEM[parent].is_dir, f'{parent} is not a directory'

    def test_there_is_something_to_read(self):
        readable = sum(len(n.content) for n in FILESYSTEM.values()
                       if isinstance(n.content, str))
        assert readable > 5000, 'the filesystem is a stage set again'

    def test_a_listing_never_names_a_missing_file(self, terminal):
        for path, node in terminal.filesystem.items():
            if not node.is_dir:
                continue
            for name in children(path, terminal.filesystem):
                child = normalise(name, path)
                assert child in terminal.filesystem


class TestNavigation:
    """cd, pwd and ls."""

    def test_cd_changes_the_directory(self, terminal):
        assert terminal.execute_command('cd /usr/doc') == ''
        assert terminal.execute_command('pwd') == '/usr/doc'

    def test_cd_with_no_argument_goes_home(self, terminal):
        terminal.execute_command('cd /etc')
        terminal.execute_command('cd')
        assert terminal.execute_command('pwd') == '/usr/users/sysop'

    def test_cd_understands_dot_dot(self, terminal):
        terminal.execute_command('cd /usr/doc')
        terminal.execute_command('cd ..')
        assert terminal.execute_command('pwd') == '/usr'

    def test_cd_to_nowhere_is_reported(self, terminal):
        assert 'no such file' in terminal.execute_command('cd /nowhere')

    def test_cd_to_a_file_is_reported(self, terminal):
        assert 'not a directory' in terminal.execute_command('cd /etc/motd')

    def test_ls_lists_the_working_directory(self, terminal):
        terminal.execute_command('cd /usr/doc')
        listing = terminal.execute_command('ls')
        assert 'divestiture' in listing and 'bulletin' in listing

    def test_ls_long_form_shows_mode_and_owner(self, terminal):
        listing = terminal.execute_command('ls -l /usr/doc')
        assert '-rw-r--r--' in listing
        assert 'root' in listing

    def test_ls_hides_dot_files_without_a(self, terminal):
        assert '.profile' not in terminal.execute_command('ls /usr/users/sysop')
        assert '.profile' in terminal.execute_command('ls -a /usr/users/sysop')

    def test_bin_lists_commands_that_exist(self, terminal):
        listing = terminal.execute_command('ls /bin').split()
        for name in listing:
            assert name in terminal._command_handlers, \
                f'/bin/{name} is not a real command'


class TestReading:
    """cat, more, head, tail, file."""

    def test_cat_reads_a_file(self, terminal):
        assert 'Bell Telephone Laboratories' in terminal.execute_command(
            'cat /etc/motd')

    def test_cat_takes_several_files(self, terminal):
        both = terminal.execute_command('cat /etc/motd /etc/passwd')
        assert 'Bell Telephone Laboratories' in both
        assert 'sysop' in both

    def test_cat_of_a_directory_is_reported(self, terminal):
        assert 'is a directory' in terminal.execute_command('cat /usr')

    def test_cat_of_nothing_is_reported(self, terminal):
        assert 'no such file' in terminal.execute_command('cat /usr/nope')

    def test_head_defaults_to_ten_lines(self, terminal):
        assert len(terminal.execute_command(
            'head /usr/doc/divestiture').splitlines()) == 10

    def test_head_takes_a_count(self, terminal):
        assert len(terminal.execute_command(
            'head -3 /usr/doc/divestiture').splitlines()) == 3

    def test_tail_takes_the_end(self, terminal):
        tail = terminal.execute_command('tail -2 /usr/adm/messages')
        assert len(tail.splitlines()) == 2
        assert 'tour 1 logins enabled' in tail

    def test_more_says_how_much_is_left(self, terminal):
        assert '--More--' in terminal.execute_command('more /usr/doc/divestiture')

    def test_file_knows_what_things_are(self, terminal):
        assert 'directory' in terminal.execute_command('file /usr')
        assert 'c program text' in terminal.execute_command(
            'file /usr/src/cmd/hello.c')
        assert 'executable' in terminal.execute_command('file /bin/cat')


class TestTextHandling:
    """grep, wc, sort, uniq, echo."""

    def test_grep_finds_lines(self, terminal):
        assert 'sysop' in terminal.execute_command('grep sysop /etc/passwd')

    def test_grep_counts(self, terminal):
        count = terminal.execute_command('grep -c : /etc/passwd')
        assert count.isdigit() and int(count) > 5

    def test_grep_inverts(self, terminal):
        assert 'sysop' not in terminal.execute_command(
            'grep -v sysop /etc/passwd')

    def test_grep_ignores_case(self, terminal):
        assert terminal.execute_command('grep -i SYSOP /etc/passwd')

    def test_grep_numbers_lines(self, terminal):
        assert terminal.execute_command(
            'grep -n root /etc/passwd').startswith('1:')

    def test_wc_counts_in_the_right_order(self, terminal):
        # Prose, so lines < words < characters actually holds. /etc/group has
        # one word per line and would not distinguish the first two columns.
        counts = terminal.execute_command('wc /usr/doc/bulletin').split()
        assert len(counts) == 3
        lines, words, chars = (int(c) for c in counts)
        assert lines < words < chars

    def test_wc_selects_single_counts(self, terminal):
        lines = terminal.execute_command('wc -l /etc/group').strip()
        assert lines == "8"

    def test_sort_orders_lines(self, terminal):
        lines = terminal.execute_command('sort /etc/group').splitlines()
        assert lines == sorted(lines)

    def test_sort_reverses(self, terminal):
        lines = terminal.execute_command('sort -r /etc/group').splitlines()
        assert lines == sorted(lines, reverse=True)

    def test_echo_writes_its_arguments(self, terminal):
        assert terminal.execute_command('echo hello world') == 'hello world'

    def test_cal_prints_the_month(self, terminal):
        assert 'November 1983' in terminal.execute_command('cal')

    def test_cal_marks_the_end_of_the_bell_system(self, terminal):
        assert '1 January 1984' in terminal.execute_command('cal 12 1983')


class TestPipes:
    """Joining commands together, which is most of what a shell is for."""

    def test_output_flows_from_one_stage_to_the_next(self, terminal):
        assert terminal.execute_command('who | wc -l').strip().isdigit()

    def test_a_three_stage_pipeline_works(self, terminal):
        result = terminal.execute_command('cat /etc/passwd | grep sysop | wc -l')
        assert result.strip() == '1'

    def test_ls_prints_one_per_line_into_a_pipe(self, terminal):
        listing = terminal.execute_command('ls /usr/doc').split()
        piped = terminal.execute_command('ls /usr/doc | wc -l')
        assert piped.strip() == str(len(listing))
        assert len(listing) > 1, 'the test needs a directory with several files'

    def test_a_pipeline_counts_as_one_command(self, terminal):
        before = terminal.shift_minutes
        terminal.execute_command('cat /etc/passwd | grep : | sort | wc -l')
        assert terminal.shift_minutes == before + 1

    def test_an_empty_stage_is_a_syntax_error(self, terminal):
        assert 'syntax error' in terminal.execute_command('who | | wc')

    def test_grep_reads_standard_input(self, terminal):
        assert 'sysop' in terminal.execute_command('cat /etc/passwd | grep sysop')


class TestTheJobIsReadableAsFiles:
    """The board and the shift log are files, not only screens."""

    def test_the_board_is_a_file(self, terminal):
        expected = [r.number for r in terminal.desk.pending()]
        board = terminal.execute_command('cat /usr/lmos/board')
        for number in expected:
            assert number in board

    def test_the_board_can_be_grepped(self, terminal):
        terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        result = terminal.execute_command(
            'cat /usr/lmos/board | grep -c PEND')
        assert int(result) >= 1

    def test_the_shift_log_reports_the_index(self, terminal):
        log = terminal.execute_command('cat /usr/adm/shiftlog')
        assert 'index' in log
        assert terminal.career.index_band() in log

    def test_the_practices_are_readable(self, terminal):
        listing = terminal.execute_command('ls /usr/bsp')
        assert listing.strip()
        first = listing.split()[0]
        assert 'BELL SYSTEM PRACTICE' in terminal.execute_command(
            f'cat /usr/bsp/{first}')


class TestTheCompanyIsEnding:
    """The shift is forty-eight days before the Bell System stops existing."""

    def test_the_motd_says_so(self, terminal):
        assert '1 January 1984' in terminal.execute_command('cat /etc/motd')

    def test_there_is_a_memo_explaining_it(self, terminal):
        memo = terminal.execute_command('cat /usr/doc/divestiture')
        assert 'consent decree' in memo
        assert 'Your employment continues' in memo

    def test_the_memo_says_not_to_clear_the_board_dishonestly(self, terminal):
        memo = terminal.execute_command('cat /usr/doc/divestiture')
        assert 'Disposition codes are audited' in memo

    def test_the_previous_operator_left_notes(self, terminal):
        notes = terminal.execute_command('cat /usr/users/sysop/notes')
        assert 'cable and pair' in notes
