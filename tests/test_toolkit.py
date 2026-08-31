"""
The rest of the toolkit: writing files, filters, games, ed, cc and nroff.

The point of all of it is that this feels like a machine somebody lived on
rather than a menu with a UNIX skin.
"""

import pytest


class TestWritingFiles:
    """A filesystem you can put things in."""

    def test_a_directory_can_be_made_and_removed(self, terminal):
        terminal.execute_command('cd')
        assert terminal.execute_command('mkdir work') == ''
        assert 'work' in terminal.execute_command('ls')
        assert terminal.execute_command('rmdir work') == ''
        assert 'work' not in terminal.execute_command('ls')

    def test_rmdir_refuses_a_full_directory(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('mkdir box')
        terminal.execute_command('touch box/thing')
        assert 'not empty' in terminal.execute_command('rmdir box')

    def test_rm_r_takes_the_whole_tree(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('mkdir box')
        terminal.execute_command('touch box/thing')
        assert terminal.execute_command('rm -r box') == ''
        assert 'box' not in terminal.execute_command('ls')

    def test_rm_refuses_a_directory_without_r(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('mkdir box')
        assert 'is a directory' in terminal.execute_command('rm box')

    def test_cp_then_mv_then_rm(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('cp /etc/motd banner')
        assert 'Bell Telephone' in terminal.execute_command('cat banner')
        terminal.execute_command('mv banner moved')
        assert 'moved' in terminal.execute_command('ls')
        terminal.execute_command('rm moved')
        assert 'moved' not in terminal.execute_command('ls')

    def test_chmod_changes_what_ls_shows(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('touch private')
        terminal.execute_command('chmod 600 private')
        assert '-rw-------' in terminal.execute_command('ls -l private')

    def test_you_cannot_write_into_a_missing_directory(self, terminal):
        assert 'no such directory' in terminal.execute_command(
            'echo x > /nowhere/at/all')


class TestRedirection:
    """> and >>."""

    def test_output_goes_to_a_file(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('echo hello > note')
        assert terminal.execute_command('cat note') == 'hello'

    def test_append_adds_to_the_end(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('echo one > note')
        terminal.execute_command('echo two >> note')
        assert terminal.execute_command('cat note').split('\n') == ['one', 'two']

    def test_a_command_can_be_captured(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('who > users')
        assert int(terminal.execute_command('wc -l users').strip()) > 1

    def test_a_missing_target_is_a_syntax_error(self, terminal):
        assert 'syntax error' in terminal.execute_command('echo hi >')


class TestFilters:
    """The text tools, and that they compose."""

    def test_tr_translates(self, terminal):
        assert terminal.execute_command('echo abc | tr a-z A-Z') == 'ABC'

    def test_tr_deletes(self, terminal):
        assert terminal.execute_command('echo a1b2c3 | tr -d 0-9') == 'abc'

    def test_cut_takes_a_field(self, terminal):
        result = terminal.execute_command('cat /etc/passwd | cut -d: -f1')
        assert 'sysop' in result.split('\n')

    def test_sed_substitutes(self, terminal):
        assert terminal.execute_command(
            "echo hello | sed 's/hello/goodbye/'") == 'goodbye'

    def test_sed_deletes_matching_lines(self, terminal):
        result = terminal.execute_command("cat /etc/group | sed '/uucp/d'")
        assert 'uucp' not in result

    def test_rev_reverses(self, terminal):
        assert terminal.execute_command('echo abc | rev') == 'cba'

    def test_tee_writes_and_passes_on(self, terminal):
        terminal.execute_command('cd')
        result = terminal.execute_command('echo kept | tee copy')
        assert result.strip() == 'kept'
        assert terminal.execute_command('cat copy') == 'kept'

    def test_cmp_is_silent_on_identical_files(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('cp /etc/group a')
        terminal.execute_command('cp /etc/group b')
        assert terminal.execute_command('cmp a b') == ''

    def test_cmp_reports_a_difference(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('echo one > a')
        terminal.execute_command('echo two > b')
        assert 'differ' in terminal.execute_command('cmp a b')

    def test_diff_reports_in_ed_form(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('echo one > a')
        terminal.execute_command('echo two > b')
        result = terminal.execute_command('diff a b')
        assert '<' in result and '>' in result

    def test_quotes_hold_an_argument_together(self, terminal):
        assert terminal.execute_command("echo 'two words' | wc -w") == '2'

    def test_od_dumps_octal(self, terminal):
        assert terminal.execute_command('echo A | od').startswith('0000000')


class TestSmallPrograms:
    """The utilities that are not filters."""

    def test_banner_is_five_rows(self, terminal):
        assert len(terminal.execute_command('banner HI').split('\n')) == 5

    def test_factor_factors(self, terminal):
        assert terminal.execute_command('factor 12').split() == \
            ['12', '2', '2', '3']

    def test_factor_complains_the_way_it_did(self, terminal):
        assert 'ouch' in terminal.execute_command('factor 1')

    def test_primes_are_prime(self, terminal):
        for number in terminal.execute_command('primes 10 30').split():
            value = int(number)
            assert all(value % d for d in range(2, value))

    def test_bc_calculates(self, terminal):
        assert terminal.execute_command('bc 6 * 7') == '42'

    def test_bc_refuses_anything_but_arithmetic(self, terminal):
        assert 'syntax error' in terminal.execute_command('bc __import__')

    def test_units_converts(self, terminal):
        assert '15.84' in terminal.execute_command('units 3 mile kft')

    def test_units_refuses_what_it_does_not_know(self, terminal):
        assert 'conformability' in terminal.execute_command('units 3 furlong pc')

    def test_sleep_charges_the_shift(self, terminal):
        before = terminal.shift_minutes
        terminal.execute_command('sleep 300')
        assert terminal.shift_minutes > before + 1

    def test_mesg_reports_and_sets(self, terminal):
        terminal.execute_command('mesg n')
        assert terminal.execute_command('mesg') == 'is n'
        terminal.execute_command('mesg y')
        # Messages are on again, so the craft may well interrupt this one.
        assert terminal.execute_command('mesg').startswith('is y')

    def test_wall_reaches_everybody_and_somebody_answers(self, terminal):
        result = terminal.execute_command('wall coffee is on')
        assert 'Broadcast Message' in result
        assert 'coffee is on' in result

    def test_passwd_is_honest_about_what_it_cannot_do(self, terminal):
        assert 'nothing was changed' in terminal.execute_command('passwd')


class TestGames:
    """Section 6."""

    def test_fortune_prints_something(self, terminal):
        assert terminal.execute_command('fortune').strip()

    def test_bcd_punches_a_card(self, terminal):
        card = terminal.execute_command('bcd AB')
        assert card.count('\n') >= 12
        assert ']' in card

    def test_bcd_uses_the_right_zones(self, terminal):
        from bell_system.screens.games import _BCD_PUNCH
        assert _BCD_PUNCH['A'] == ('12', '1')
        assert _BCD_PUNCH['J'] == ('11', '1')
        assert _BCD_PUNCH['S'] == ('0', '2')
        assert _BCD_PUNCH['7'] == ('7',)

    def test_ppt_punches_tape(self, terminal):
        tape = terminal.execute_command('ppt HI')
        assert 'o' in tape and '.' in tape

    def test_moo_plays(self, terminal):
        assert 'New game' in terminal.execute_command('moo')
        result = terminal.execute_command('moo 1234')
        assert 'bulls' in result and 'cows' in result

    def test_moo_refuses_a_bad_guess(self, terminal):
        terminal.execute_command('moo')
        assert 'four digits' in terminal.execute_command('moo 12')

    def test_moo_needs_a_game_first(self, terminal):
        terminal._moo_secret = None
        assert 'no game' in terminal.execute_command('moo 1234')

    def test_the_scoreboard_somebody_kept_is_there(self, terminal):
        assert 'gvasquez' in terminal.execute_command(
            'cat /usr/games/lib/moo.scores')


class TestNetnews:
    """A uucp feed, which is what a machine like this had in 1983."""

    def test_articles_are_waiting(self, terminal):
        listing = terminal.execute_command('readnews')
        assert 'articles waiting' in listing
        assert 'net.unix-wizards' in listing

    def test_one_can_be_read(self, terminal):
        article = terminal.execute_command('readnews 1')
        assert 'Newsgroups:' in article

    def test_a_group_can_be_picked(self, terminal):
        assert 'net.jokes' in terminal.execute_command('readnews -n net.jokes')

    def test_articles_are_files_too(self, terminal):
        assert 'Relay-Version' in terminal.execute_command(
            'cat /usr/spool/news/net.general/207')


class TestEd:
    """The editor, question marks and all."""

    def test_a_session_takes_over_the_terminal(self, terminal):
        terminal.execute_command('ed')
        assert terminal._editor is not None
        terminal.execute_command('Q')
        assert terminal._editor is None

    def test_text_can_be_appended_and_printed(self, terminal):
        for line in ('ed', 'a', 'first', 'second', '.'):
            terminal.execute_command(line)
        assert terminal.execute_command('1,$p') == 'first\nsecond'
        terminal.execute_command('Q')

    def test_numbered_printing(self, terminal):
        for line in ('ed', 'a', 'only', '.'):
            terminal.execute_command(line)
        assert terminal.execute_command('1,$n') == '1\tonly'
        terminal.execute_command('Q')

    def test_substitution_over_a_range(self, terminal):
        for line in ('ed', 'a', 'the quick fox', '.', '1,$s/quick/slow/'):
            terminal.execute_command(line)
        assert terminal.execute_command('1,$p') == 'the slow fox'
        terminal.execute_command('Q')

    def test_deletion(self, terminal):
        for line in ('ed', 'a', 'one', 'two', '.', '1d'):
            terminal.execute_command(line)
        assert terminal.execute_command('1,$p') == 'two'
        terminal.execute_command('Q')

    def test_writing_a_file_prints_the_byte_count(self, terminal):
        for line in ('ed', 'a', 'saved', '.'):
            terminal.execute_command(line)
        assert terminal.execute_command('w /tmp/kept') == '6'
        terminal.execute_command('Q')
        assert terminal.execute_command('cat /tmp/kept') == 'saved'

    def test_a_mistake_gets_a_question_mark_and_nothing_else(self, terminal):
        terminal.execute_command('ed')
        assert terminal.execute_command('zzz') == '?'
        terminal.execute_command('Q')

    def test_h_explains_the_last_question_mark(self, terminal):
        terminal.execute_command('ed')
        terminal.execute_command('zzz')
        assert terminal.execute_command('h').startswith('ed:')
        terminal.execute_command('Q')

    def test_three_mistakes_and_it_relents(self, terminal):
        terminal.execute_command('ed')
        for _ in range(2):
            terminal.execute_command('zzz')
        assert 'q quits' in terminal.execute_command('zzz')
        terminal.execute_command('Q')

    def test_q_refuses_once_on_a_modified_buffer(self, terminal):
        for line in ('ed', 'a', 'unsaved', '.'):
            terminal.execute_command(line)
        assert terminal.execute_command('q') == '?'
        assert terminal.execute_command('q') == ''
        assert terminal._editor is None


class TestCc:
    """A compiler that is honest about its reach."""

    def test_hello_world_compiles_and_runs(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('cp /usr/src/cmd/hello.c hello.c')
        assert terminal.execute_command('cc hello.c') == ''
        assert terminal.execute_command('a.out').strip() == 'hello, world'

    def test_the_output_name_can_be_chosen(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('cp /usr/src/cmd/hello.c hello.c')
        terminal.execute_command('cc -o greet hello.c')
        assert terminal.execute_command('greet').strip() == 'hello, world'

    def test_a_program_with_no_main_is_rejected(self, terminal):
        terminal.execute_command('cd')
        terminal.write_file('/usr/users/sysop/bad.c', 'int x;\n')
        assert 'undefined' in terminal.execute_command('cc bad.c')

    def test_a_missing_source_is_reported(self, terminal):
        assert 'cannot open' in terminal.execute_command('cc nothing.c')

    def test_the_compiled_file_is_executable(self, terminal):
        terminal.execute_command('cd')
        terminal.execute_command('cp /usr/src/cmd/hello.c hello.c')
        terminal.execute_command('cc hello.c')
        assert 'executable' in terminal.execute_command('file a.out')


class TestDocumentTools:
    """nroff, troff and tbl, which used to be placeholders."""

    def test_nroff_formats_a_man_page(self, terminal):
        terminal.write_file('/tmp/d', '.TH THING 1\n.SH NAME\nthing \\- a thing\n')
        result = terminal.execute_command('nroff /tmp/d')
        assert 'THING(1)' in result
        assert 'NAME' in result
        assert '\\-' not in result

    def test_nroff_fills_to_a_measure(self, terminal):
        terminal.write_file('/tmp/d', '.PP\n' + 'word ' * 60)
        for line in terminal.execute_command('nroff /tmp/d').split('\n'):
            assert len(line) <= 72

    def test_tbl_lays_out_columns(self, terminal):
        terminal.write_file('/tmp/t', '.TS\nl r.\nab\t1\ncdef\t22\n.TE\n')
        result = terminal.execute_command('tbl /tmp/t')
        assert 'ab' in result and 'cdef' in result

    def test_tbl_pipes_into_nroff(self, terminal):
        terminal.write_file('/tmp/t', '.TS\nl l.\nOffice\tType\n.TE\n')
        result = terminal.execute_command('tbl /tmp/t | nroff')
        assert 'Office' in result and '.TS' not in result

    def test_tbl_says_what_it_wants(self, terminal):
        terminal.write_file('/tmp/plain', 'no table here\n')
        assert '.TS' in terminal.execute_command('tbl /tmp/plain')

    def test_troff_says_there_is_no_typesetter(self, terminal):
        terminal.write_file('/tmp/d', '.PP\nsome text\n')
        assert 'no typesetter' in terminal.execute_command('troff /tmp/d')

    def test_eqn_says_why_it_cannot(self, terminal):
        assert 'cannot set mathematics' in terminal.execute_command('eqn')

    @pytest.mark.parametrize('command', ['nroff', 'troff', 'tbl', 'eqn'])
    def test_they_are_no_longer_stubs(self, command):
        from bell_system.constants import UNIMPLEMENTED_COMMANDS
        assert command not in UNIMPLEMENTED_COMMANDS
