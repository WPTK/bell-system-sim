"""
Finds: what reading a file records, how a pattern reaches a directory, and
the files that turn up on a later tour.

A find is a file the player has put in front of themselves with cat or grep.
Some are on the machine from the first tour and some arrive on a later tour
in a place nobody browses, which is what grep with a pattern is for. These
check that they are where they should be and that reading them is recorded.
What the files say is the narrative bible's business and not this file's.
"""

import pytest

from bell_system.data import finds as data
from bell_system.filesystem import MOO_SCORES
from bell_system.screens.finds import FIRST_FIND

SULOG = '/usr/adm/sulog'


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


class TestFinds:
    """Reading a find records it; finds lists what has been read."""

    def test_nothing_at_the_start(self, raw_terminal):
        assert raw_terminal.execute_command('finds') == 'Nothing found yet.'

    def test_cat_records_a_fragment(self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        assert 'memo' in raw_terminal.career.finds

    def test_a_file_that_is_not_a_fragment_is_not_recorded(self, raw_terminal):
        raw_terminal.execute_command('cat /etc/passwd')
        assert raw_terminal.career.finds == []

    def test_finds_lists_titles_by_number(self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        number = 1 + [f.key for f in data.FRAGMENTS].index('memo')
        listing = raw_terminal.execute_command('finds')
        assert 'Found so far: 1' in listing
        assert f'{number:>3}  The January memo' in listing

    def test_a_number_keeps_its_place_whatever_order_they_were_read(
            self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        raw_terminal.execute_command('cat /usr/users/sysop/notes')
        titles = [row.split(None, 1)[1] for row in
                  raw_terminal.execute_command('finds').splitlines()[2:]]
        assert titles == ['Notes for whoever has the position',
                          'The January memo']

    def test_finds_with_a_number_says_where(self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        number = 1 + [f.key for f in data.FRAGMENTS].index('memo')
        assert '/usr/doc/divestiture' in raw_terminal.execute_command(
            f'finds {number}')

    def test_finds_with_a_number_not_found_says_nothing_of_the_file(
            self, raw_terminal):
        number = 1 + [f.key for f in data.FRAGMENTS].index('memo')
        said = raw_terminal.execute_command(f'finds {number}')
        assert 'nothing found' in said
        assert 'January' not in said and '/usr/doc' not in said

    def test_finds_wants_a_number(self, raw_terminal):
        assert 'usage' in raw_terminal.execute_command('finds memo')

    def test_the_first_find_is_noted_once(self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        assert raw_terminal.take_find_notice() == FIRST_FIND
        raw_terminal.execute_command('cat /usr/users/sysop/notes')
        assert raw_terminal.take_find_notice() == ''

    def test_the_note_is_not_in_the_output(self, raw_terminal):
        said = raw_terminal.execute_command('cat /usr/doc/divestiture')
        assert FIRST_FIND not in said
        assert said == raw_terminal._read('/usr/doc/divestiture').rstrip(chr(10))

    def test_head_counts_the_file_and_not_the_note(self, raw_terminal):
        said = raw_terminal.execute_command('head -3 /usr/doc/divestiture')
        assert len(said.splitlines()) == 3

    def test_a_pipe_carries_the_file_and_not_the_note(self, raw_terminal):
        said = raw_terminal.execute_command('cat /usr/doc/divestiture | wc -l')
        assert said.split()[0] == str(len(
            raw_terminal._read('/usr/doc/divestiture').splitlines()))

    def test_the_note_is_never_written_into_a_file(self, raw_terminal):
        assert raw_terminal.execute_command(
            'cat /usr/doc/divestiture > memo.copy') == ''
        copied = raw_terminal._read(
            raw_terminal.current_directory + '/memo.copy')
        assert copied.strip() == raw_terminal._read(
            '/usr/doc/divestiture').strip()
        assert FIRST_FIND not in copied

    def test_the_note_waits_for_the_screen_after_a_redirect(
            self, raw_terminal):
        raw_terminal.execute_command('cat /usr/doc/divestiture > memo.copy')
        assert raw_terminal.take_find_notice() == FIRST_FIND

    def test_the_repl_says_it_after_the_output(
            self, raw_terminal, monkeypatch, capsys):
        lines = iter(['cat /usr/doc/divestiture', 'exit'])
        monkeypatch.setattr('builtins.input', lambda *_: next(lines))
        raw_terminal.run(role=1)
        out = capsys.readouterr().out
        assert out.index('RECORDS RETENTION') < out.index(FIRST_FIND)

    def test_wc_od_and_sum_do_not_make_a_find(self, raw_terminal):
        for command in ('wc /usr/doc/divestiture', 'od /usr/doc/divestiture',
                        'sum /usr/doc/divestiture'):
            raw_terminal.execute_command(command)
        assert raw_terminal.career.finds == []

    def test_grep_c_and_l_do_not_make_a_find(self, raw_terminal):
        raw_terminal.execute_command('grep -c BELL /usr/doc/divestiture')
        raw_terminal.execute_command('grep -l BELL /usr/doc/divestiture')
        assert raw_terminal.career.finds == []

    def test_uulog_dd_and_look_that_print_it_make_a_find(self, raw_terminal):
        raw_terminal.execute_command('uulog')
        assert 'uucplog' in raw_terminal.career.finds
        raw_terminal.execute_command('dd if=/usr/doc/divestiture')
        assert 'memo' in raw_terminal.career.finds
        raw_terminal.execute_command('dd if=/usr/users/sysop/notes of=copy')
        assert 'notes' not in raw_terminal.career.finds

    def test_a_find_that_arrived_is_not_saved_with_the_player(
            self, raw_terminal):
        from bell_system.filesystem import player_changes
        at_tour(raw_terminal, 5)
        changed, _ = player_changes(raw_terminal.filesystem)
        assert '/usr/users/rjohnson/.trial' not in changed

    def test_a_find_is_recorded_once(self, raw_terminal):
        for _ in range(3):
            raw_terminal.execute_command('cat /usr/doc/divestiture')
        assert raw_terminal.career.finds.count('memo') == 1

    def test_grep_records_only_the_files_it_found_something_in(
            self, raw_terminal):
        raw_terminal.execute_command('grep zzqqxx /usr/doc/divestiture')
        assert raw_terminal.career.finds == []
        raw_terminal.execute_command('grep BELL /usr/doc/divestiture')
        assert raw_terminal.career.finds == ['memo']

    def test_head_and_more_record_too(self, raw_terminal):
        raw_terminal.execute_command('head -2 /usr/doc/divestiture')
        raw_terminal.execute_command('more /usr/users/sysop/notes')
        assert set(raw_terminal.career.finds) == {'memo', 'notes'}

    def test_a_refused_read_is_not_a_find(self, raw_terminal):
        held(raw_terminal, 0)
        raw_terminal.execute_command(f'cat {SULOG}')
        assert 'sulog' not in raw_terminal.career.finds

    def test_readnews_counts_a_read_article(self, raw_terminal):
        at_tour(raw_terminal, 10)
        articles = raw_terminal._news_articles()
        number = articles.index('/usr/spool/news/net.misc/88') + 1
        raw_terminal.execute_command(f'readnews {number}')
        assert 'strike' in raw_terminal.career.finds

    def test_finds_survive_a_restart(self, raw_terminal):
        from bell_system.progression import Career
        raw_terminal.execute_command('cat /usr/doc/divestiture')
        again = Career(raw_terminal.career.path)
        assert again.finds == ['memo']

    def test_finds_is_a_command_and_has_a_page(self, raw_terminal):
        assert 'finds' in raw_terminal._command_handlers
        assert 'finds' in raw_terminal.man_pages


class TestGlobs:
    """The shell expands a pattern, so one grep can read a directory."""

    def test_star_reads_every_file_in_a_directory(self, raw_terminal):
        said = raw_terminal.execute_command('grep -l . /usr/adm/*')
        assert '/usr/adm/shiftlog' in said
        assert '/usr/adm/uucplog' in said

    def test_a_name_is_put_in_front_when_there_is_more_than_one(
            self, raw_terminal):
        said = raw_terminal.execute_command('grep rjohnson /usr/adm/*')
        assert '/usr/adm/messages:' in said or '/usr/adm/sulog:' in said

    def test_h_leaves_the_name_off(self, raw_terminal):
        held(raw_terminal, 4)
        said = raw_terminal.execute_command('grep -h mreyes /usr/adm/*')
        assert '/usr/adm' not in said

    def test_one_file_has_no_name(self, raw_terminal):
        said = raw_terminal.execute_command('grep rjohnson /usr/adm/uucplog')
        assert not said.startswith('/usr/adm')

    def test_a_pattern_that_matches_nothing_is_taken_as_typed(
            self, raw_terminal):
        assert 'no such file' in raw_terminal.execute_command(
            'cat /usr/adm/zz*')

    def test_a_star_does_not_match_a_dotfile(self, raw_terminal):
        at_tour(raw_terminal, 10)
        assert '.retain' not in raw_terminal.execute_command(
            'grep -l . /usr/adm/*')
        assert '.retain' in raw_terminal.execute_command(
            'grep -l . /usr/adm/.*')

    def test_a_star_stays_within_one_directory(self, raw_terminal):
        said = raw_terminal.execute_command('grep -l . /usr/*')
        assert '/usr/adm' not in said

    def test_relative_patterns_work(self, raw_terminal):
        raw_terminal.execute_command('cd /usr/adm')
        said = raw_terminal.execute_command('grep -l . sh*')
        assert said == 'shiftlog'

    def test_an_unreadable_file_does_not_stop_the_search(self, raw_terminal):
        held(raw_terminal, 0)
        said = raw_terminal.execute_command('grep -h . /usr/adm/*')
        assert 'permission denied' in said
        assert 'uucico' in said

    def test_grep_counts_per_file(self, raw_terminal):
        held(raw_terminal, 3)
        said = raw_terminal.execute_command('grep -c . /usr/adm/*')
        assert '/usr/adm/sulog:' in said

    def test_a_directory_cannot_be_read(self, raw_terminal):
        assert 'is a directory' in raw_terminal.execute_command('cat /usr/adm')


class TestHiddenFragments:
    """A fragment in a place nobody browses is in grep only once its tour."""

    @pytest.mark.parametrize('path,tour', [
        ('/tmp/.f', 2),
        ('/usr/users/rjohnson/.trial', 5),
        ('/usr/adm/.retain', 8),
        ('/usr/lib/.xfer', 10),
    ])
    def test_it_arrives_on_its_tour(self, raw_terminal, path, tour):
        at_tour(raw_terminal, tour - 1)
        assert path not in raw_terminal.filesystem
        at_tour(raw_terminal, tour)
        assert path in raw_terminal.filesystem

    def test_it_is_not_in_the_search_before_its_tour(self, raw_terminal):
        at_tour(raw_terminal, 1)
        said = raw_terminal.execute_command('grep -l . /tmp/.?')
        assert '/tmp/.f' not in said

    def test_it_is_in_the_search_on_its_tour(self, raw_terminal):
        at_tour(raw_terminal, 2)
        said = raw_terminal.execute_command('grep -l franklin /tmp/.?')
        assert said.splitlines()[0] == '/tmp/.f'

    def test_ls_does_not_show_it_unless_asked(self, raw_terminal):
        at_tour(raw_terminal, 2)
        assert '.f' not in raw_terminal.execute_command('ls /tmp').split()
        assert '.f' in raw_terminal.execute_command('ls -a /tmp').split()

    def test_it_stays_once_it_has_come(self, raw_terminal):
        at_tour(raw_terminal, 5)
        raw_terminal.deliver_news()
        assert '/usr/users/rjohnson/.trial' in raw_terminal.filesystem

    def test_reading_it_is_a_find(self, raw_terminal):
        at_tour(raw_terminal, 5)
        raw_terminal.execute_command('grep seconds /usr/users/rjohnson/.trial')
        assert 'trial' in raw_terminal.career.finds

    def test_a_session_resumed_late_has_what_has_arrived(self, raw_terminal):
        """The tree is built fresh each session; the tour is the career's."""
        raw_terminal.career.shift = 9
        raw_terminal._initialize_filesystem()
        raw_terminal.deliver_news()
        assert '/usr/adm/.retain' in raw_terminal.filesystem
        assert '/usr/lib/.xfer' not in raw_terminal.filesystem


class TestTheRegistry:
    """The data holds together."""

    def test_the_scoreboard_is_where_the_game_keeps_it(self):
        assert data.MOO_SCORES_PATH == MOO_SCORES

    def test_every_fragment_is_a_file_on_the_machine_by_its_tour(
            self, raw_terminal):
        at_tour(raw_terminal, 10)
        for fragment in data.FRAGMENTS:
            assert fragment.path in raw_terminal.filesystem, fragment.key

    def test_keys_and_paths_are_unique(self):
        assert len({f.key for f in data.FRAGMENTS}) == len(data.FRAGMENTS)
        assert len({f.path for f in data.FRAGMENTS}) == len(data.FRAGMENTS)

    def test_a_title_names_the_file_not_the_answer(self):
        for fragment in data.FRAGMENTS:
            assert len(fragment.title) <= 40, fragment.key

    def test_the_new_files_have_no_long_lines(self):
        for fragment in data.FRAGMENTS:
            for line in (fragment.text or '').splitlines():
                assert len(line) <= 78, (fragment.key, line)


class TestWhatIsPrintedIsWhatIsFound:
    """A find is made by text that was shown, whichever command showed it."""

    def test_uulog_with_no_such_site_records_nothing(self, raw_terminal):
        raw_terminal.execute_command('uulog -snosuch')
        assert raw_terminal.career.finds == []

    def test_a_sed_script_that_is_refused_records_nothing(self, raw_terminal):
        raw_terminal.execute_command('sed /x/p /usr/doc/divestiture')
        assert raw_terminal.career.finds == []

    def test_dd_that_copies_nothing_records_nothing(self, raw_terminal):
        raw_terminal.execute_command('dd if=/usr/doc/divestiture count=0')
        assert raw_terminal.career.finds == []

    @pytest.mark.parametrize('line', [
        'sort /usr/doc/divestiture', 'uniq /usr/doc/divestiture',
        'sed s/a/b/ /usr/doc/divestiture', 'rev /usr/doc/divestiture',
        'pr /usr/doc/divestiture', 'spell /usr/doc/divestiture',
    ])
    def test_a_filter_that_prints_the_file_makes_the_find(
            self, raw_terminal, line):
        raw_terminal.execute_command(line)
        assert 'memo' in raw_terminal.career.finds

    def test_the_decimal_check_is_not_fooled_by_a_superscript(
            self, raw_terminal):
        assert raw_terminal.execute_command(
            'head -\u00b2 /usr/doc/divestiture') is not None
        assert raw_terminal.execute_command('chmod 6\u00b2\u00b2 x') == (
            'chmod: 6\u00b2\u00b2: bad mode')

    def test_the_test_log_ends_on_an_empty_board_and_says_no_more(self):
        rows = [line.split() for line in data.TESTLOG.splitlines()]
        assert rows[-1][-2:] == ['board', '0']
        assert 'clear' not in data.TESTLOG
        week = [row for row in rows if row[0] >= '11/07']
        ntf = [int(row[4]) for row in week]
        closed = [int(row[2]) for row in week]
        assert ntf == sorted(ntf) and ntf[-1] > ntf[0]
        assert all(n < c for n, c in zip(ntf, closed))
