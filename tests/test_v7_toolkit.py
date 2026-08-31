"""
The rest of the Seventh Edition: filters, deferred work, and the document
preprocessors that used to be stubs.

These are the commands that make the machine feel like a machine rather than
a menu with a UNIX prompt drawn on it. They are tested the way a user finds
them: by running them and looking at what comes back.
"""

from datetime import timedelta

import pytest

from bell_system.constants import UNIMPLEMENTED_COMMANDS


class TestPaginating:
    """pr(1), which is how a listing got onto paper."""

    def test_a_heading_carries_the_date_and_a_page_number(self, terminal):
        result = terminal.execute_command('pr /etc/group')
        assert 'Page 1' in result
        assert '/etc/group' in result

    def test_dash_t_drops_the_heading(self, terminal):
        result = terminal.execute_command('pr -t /etc/group')
        assert 'Page 1' not in result
        assert 'craft' in result

    def test_a_long_file_runs_to_several_pages(self, terminal):
        result = terminal.execute_command('pr /usr/dict/words')
        assert 'Page 2' in result

    def test_columns_put_more_on_a_page(self, terminal):
        one = terminal.execute_command('pr -t /usr/dict/words')
        two = terminal.execute_command('pr -t -2 /usr/dict/words')
        assert len(two.split('\n')) < len(one.split('\n'))

    def test_the_heading_can_be_replaced(self, terminal):
        result = terminal.execute_command('pr -h "TROUBLE BOARD" /etc/group')
        assert 'TROUBLE BOARD' in result


class TestComparingSortedFiles:
    """comm(1) and join(1)."""

    def setup_files(self, terminal):
        terminal.write_file('/tmp/a', 'apple\nbanana\ncherry\n')
        terminal.write_file('/tmp/b', 'banana\ncherry\ndamson\n')

    def test_comm_shows_three_columns(self, terminal):
        self.setup_files(terminal)
        result = terminal.execute_command('comm /tmp/a /tmp/b')
        assert 'apple' in result and 'damson' in result and 'banana' in result

    def test_comm_can_show_only_what_is_in_both(self, terminal):
        self.setup_files(terminal)
        result = terminal.execute_command('comm -12 /tmp/a /tmp/b')
        assert 'banana' in result and 'cherry' in result
        assert 'apple' not in result and 'damson' not in result

    def test_comm_can_show_only_what_has_gone_away(self, terminal):
        self.setup_files(terminal)
        result = terminal.execute_command('comm -23 /tmp/a /tmp/b')
        assert result.strip() == 'apple'

    def test_comm_wants_exactly_two_files(self, terminal):
        assert 'usage' in terminal.execute_command('comm /etc/group')

    def test_join_puts_two_lists_beside_each_other(self, terminal):
        terminal.write_file('/tmp/left', '212 New York\n312 Chicago\n')
        terminal.write_file('/tmp/right', '212 crossbar\n312 ESS\n')
        result = terminal.execute_command('join /tmp/left /tmp/right')
        assert 'New York crossbar' in result
        assert '312 Chicago ESS' in result

    def test_join_drops_what_does_not_match(self, terminal):
        terminal.write_file('/tmp/left', '212 New York\n999 Nowhere\n')
        terminal.write_file('/tmp/right', '212 crossbar\n')
        result = terminal.execute_command('join /tmp/left /tmp/right')
        assert 'Nowhere' not in result


class TestDictionary:
    """look(1), and the dictionary spell(1) now shares with it."""

    def test_a_prefix_finds_words(self, terminal):
        result = terminal.execute_command('look tel')
        assert 'telephone' in result

    def test_a_prefix_nothing_starts_with_finds_nothing(self, terminal):
        assert terminal.execute_command('look zzzz').strip() == ''

    def test_spell_and_look_agree(self, terminal):
        """
        Anything look(1) finds is a word spell(1) accepts. They read the
        same file, and this is the test that keeps them reading it.
        """
        words = terminal.execute_command('look tr').split()
        terminal.write_file('/tmp/words', ' '.join(words) + '\n')
        assert terminal.execute_command('spell /tmp/words').strip() == ''

    def test_the_dictionary_is_an_ordinary_file(self, terminal):
        assert 'telephone' in terminal.execute_command('cat /usr/dict/words')

    def test_spell_says_when_the_dictionary_is_gone(self, terminal):
        del terminal.filesystem['/usr/dict/words']
        assert 'cannot open' in terminal.execute_command('spell /etc/motd')


class TestSplittingAndChecking:
    """split(1), sum(1) and dd(1)."""

    def test_split_makes_pieces_named_in_order(self, terminal):
        terminal.execute_command('cd /tmp')
        result = terminal.execute_command('split -100 /usr/dict/words')
        assert 'xaa' in result and 'xab' in result
        assert terminal.filesystem.get('/tmp/xaa') is not None

    def test_a_piece_holds_the_asked_for_number_of_lines(self, terminal):
        terminal.execute_command('cd /tmp')
        terminal.execute_command('split -10 /usr/dict/words')
        assert terminal.execute_command('wc -l /tmp/xaa').split()[0] == '10'

    def test_split_can_be_given_a_name(self, terminal):
        terminal.execute_command('cd /tmp')
        result = terminal.execute_command('split -50 /usr/dict/words part')
        assert 'partaa' in result

    def test_sum_is_stable_and_changes_with_the_file(self, terminal):
        terminal.write_file('/tmp/one', 'the same text\n')
        terminal.write_file('/tmp/two', 'the same text\n')
        terminal.write_file('/tmp/three', 'the samee text\n')
        first = terminal.execute_command('sum /tmp/one')
        assert first == terminal.execute_command('sum /tmp/two')
        assert first != terminal.execute_command('sum /tmp/three')

    def test_sum_notices_two_bytes_swapped_over(self, terminal):
        """
        The rotation before each addition is the whole reason sum(1) is not
        a plain total. Without it these two files check the same.
        """
        terminal.write_file('/tmp/ab', 'ab')
        terminal.write_file('/tmp/ba', 'ba')
        assert (terminal.execute_command('sum /tmp/ab')
                != terminal.execute_command('sum /tmp/ba'))

    def test_sum_names_each_file_when_given_several(self, terminal):
        result = terminal.execute_command('sum /etc/motd /etc/group')
        assert '/etc/motd' in result and '/etc/group' in result

    def test_dd_copies(self, terminal):
        terminal.execute_command('dd if=/etc/motd of=/tmp/copy')
        assert (terminal.execute_command('cat /tmp/copy')
                == terminal.execute_command('cat /etc/motd'))

    def test_dd_converts_case(self, terminal):
        terminal.write_file('/tmp/lower', 'wire centre\n')
        result = terminal.execute_command('dd if=/tmp/lower conv=ucase')
        assert 'WIRE CENTRE' in result

    def test_dd_reports_its_record_counts(self, terminal):
        result = terminal.execute_command('dd if=/etc/motd')
        assert 'records in' in result and 'records out' in result


class TestShellArithmetic:
    """expr(1), basename(1), true(1) and false(1)."""

    @pytest.mark.parametrize('line,answer', [
        ('expr 6 + 7', '13'),
        ('expr 100 - 1', '99'),
        ('expr 100 / 7', '14'),
        ('expr 100 % 7', '2'),
        ('expr 12 "*" 12', '144'),
    ])
    def test_arithmetic(self, terminal, line, answer):
        assert terminal.execute_command(line).strip() == answer

    @pytest.mark.parametrize('line,answer', [
        ('expr 5 ">" 3', '1'),
        ('expr 3 ">" 5', '0'),
        ('expr abc = abc', '1'),
        ('expr abc != abc', '0'),
    ])
    def test_comparisons(self, terminal, line, answer):
        assert terminal.execute_command(line).strip() == answer

    def test_division_by_zero_is_refused(self, terminal):
        assert 'zero' in terminal.execute_command('expr 5 / 0')

    def test_arithmetic_on_words_is_refused(self, terminal):
        assert 'non-numeric' in terminal.execute_command('expr apple + 1')

    def test_basename_strips_the_directories(self, terminal):
        assert terminal.execute_command(
            'basename /usr/src/cmd/hello.c').strip() == 'hello.c'

    def test_basename_strips_a_suffix_too(self, terminal):
        assert terminal.execute_command(
            'basename /usr/src/cmd/hello.c .c').strip() == 'hello'

    def test_true_and_false_say_nothing(self, terminal):
        assert terminal.execute_command('true') == ''
        assert terminal.execute_command('false') == ''


class TestAt:
    """at(1): work you set going and come back to."""

    def test_a_job_is_queued_and_listed(self, terminal):
        assert 'job 1' in terminal.execute_command('at 2359 who')
        assert 'who' in terminal.execute_command('at -l')

    def test_a_queued_job_is_a_file_in_the_spool(self, terminal):
        terminal.execute_command('at 2359 who')
        spooled = [path for path in terminal.filesystem
                   if path.startswith('/usr/spool/at/')]
        assert len(spooled) == 1

    def test_a_time_that_has_gone_by_is_refused(self, terminal):
        assert 'gone by' in terminal.execute_command('at 0001 who')

    def test_a_bad_time_is_refused(self, terminal):
        assert 'bad time' in terminal.execute_command('at 9999 who')
        assert 'bad time' in terminal.execute_command('at teatime who')

    def test_a_job_can_be_taken_back_out(self, terminal):
        terminal.execute_command('at 2359 who')
        assert 'removed' in terminal.execute_command('at -r 1')
        assert 'no jobs' in terminal.execute_command('at -l')

    def test_an_unknown_job_number_is_reported(self, terminal):
        assert 'no such job' in terminal.execute_command('at -r 99')

    def test_a_job_fires_when_the_clock_reaches_it(self, terminal):
        terminal.execute_command('at 2359 uuname -l')
        terminal._at_jobs[0]['due'] = terminal.clock.now() - timedelta(minutes=1)
        result = terminal.execute_command('pwd')
        assert 'at: job 1' in result
        assert 'mhuxco' in result
        assert terminal._at_jobs == []

    def test_a_job_arrives_even_with_ambience_off(self, terminal):
        """
        The operator asked for this one, so it is not building noise and is
        not suppressed with the building noise.
        """
        assert terminal.settings.get('game.ambience') == 'off'
        terminal.execute_command('at 2359 logname')
        terminal._at_jobs[0]['due'] = terminal.clock.now() - timedelta(minutes=1)
        assert 'at: job 1' in terminal.execute_command('pwd')

    def test_a_job_may_not_queue_another_job(self, terminal):
        terminal.execute_command('at 2359 at 2358 who')
        terminal._at_jobs[0]['due'] = terminal.clock.now() - timedelta(minutes=1)
        result = terminal.execute_command('pwd')
        assert 'may not queue another job' in result


class TestMake:
    """make(1), and the makefile under /usr/src/cmd."""

    def test_it_builds_what_is_out_of_date(self, terminal):
        terminal.execute_command('cd /usr/src/cmd')
        result = terminal.execute_command('make')
        assert 'cc -o hello hello.c' in result
        assert terminal.filesystem.get('/usr/src/cmd/hello') is not None

    def test_it_leaves_alone_what_is_current(self, terminal):
        terminal.execute_command('cd /usr/src/cmd')
        terminal.execute_command('make')
        assert 'up to date' in terminal.execute_command('make')

    def test_what_it_builds_runs(self, terminal):
        terminal.execute_command('cd /usr/src/cmd')
        terminal.execute_command('make')
        assert 'hello, world' in terminal.execute_command('hello')

    def test_a_named_target_builds_only_that(self, terminal):
        terminal.execute_command('cd /usr/src/cmd')
        result = terminal.execute_command('make hello')
        assert 'hello.c' in result and 'testlog.c' not in result

    def test_an_unknown_target_is_reported(self, terminal):
        terminal.execute_command('cd /usr/src/cmd')
        assert "don't know how" in terminal.execute_command('make nonsense')

    def test_a_missing_makefile_is_reported(self, terminal):
        terminal.execute_command('cd /tmp')
        assert 'cannot open' in terminal.execute_command('make')

    def test_rules_that_refer_round_to_each_other_are_reported(self, terminal):
        terminal.execute_command('cd /tmp')
        terminal.write_file('/tmp/makefile', 'a:\tb\n\techo one\n\nb:\ta\n\techo two\n')
        assert 'circular' in terminal.execute_command('make')


class TestUucp:
    """The network this machine's news and mail arrive over."""

    def test_uuname_lists_the_neighbours(self, terminal):
        result = terminal.execute_command('uuname')
        assert 'research' in result and 'ihnp4' in result

    def test_uuname_l_is_this_machine(self, terminal):
        assert terminal.execute_command('uuname -l').strip() == 'mhuxco'

    def test_the_neighbours_are_the_sites_in_the_log(self, terminal):
        """
        uuname must not name a machine the log has never called. These two
        drifting apart is exactly the kind of thing nobody notices.
        """
        log = terminal.execute_command('cat /usr/adm/uucplog')
        for site in terminal.execute_command('uuname').split():
            assert site in log, f'uuname names {site}, uucplog has never called it'

    def test_uulog_prints_the_log(self, terminal):
        assert 'uucico' in terminal.execute_command('uulog')

    def test_uulog_can_pick_one_site(self, terminal):
        result = terminal.execute_command('uulog -sihnp4')
        assert 'ihnp4' in result
        assert 'research' not in result

    def test_uux_queues_a_job(self, terminal):
        result = terminal.execute_command('uux research!date')
        assert 'queued' in result
        assert '04:00' in result

    def test_uux_refuses_a_site_we_do_not_call(self, terminal):
        assert 'unknown site' in terminal.execute_command('uux ucbvax!date')

    def test_uux_wants_a_site(self, terminal):
        assert 'no site' in terminal.execute_command('uux date')


class TestSuAndTheLog:
    """su(1), which writes to a file that is already on this machine."""

    def test_root_is_refused(self, terminal):
        assert 'Sorry' in terminal.execute_command('su root')

    def test_the_attempt_lands_in_the_log(self, terminal):
        before = terminal.execute_command('cat /usr/adm/sulog')
        terminal.execute_command('su root')
        after = terminal.execute_command('cat /usr/adm/sulog')
        assert len(after) > len(before)
        assert '-root' in after

    def test_an_unknown_user_is_reported_and_still_logged(self, terminal):
        assert 'unknown id' in terminal.execute_command('su nobody')
        assert '-nobody' in terminal.execute_command('cat /usr/adm/sulog')

    def test_logname_is_who_you_logged_in_as(self, terminal):
        assert terminal.execute_command('logname').strip() == terminal.username


class TestRemoteJobEntry:
    """send(1) and rjestat(1), which replaced a stub called rje."""

    def test_the_link_reports_itself(self, terminal):
        result = terminal.execute_command('rjestat')
        assert 'RAO1' in result and 'ACTIVE' in result

    def test_a_submitted_job_appears_in_the_queue(self, terminal):
        assert 'queued' in terminal.execute_command('send /usr/doc/bulletin')
        assert '/usr/doc/bulletin' in terminal.execute_command('rjestat')

    def test_a_job_is_measured_in_cards(self, terminal):
        assert 'cards' in terminal.execute_command('send /etc/motd')

    def test_an_unknown_host_is_refused(self, terminal):
        assert 'no such host' in terminal.execute_command(
            'send -h RAO9 /etc/motd')

    def test_a_missing_file_is_reported(self, terminal):
        assert 'cannot open' in terminal.execute_command('send /tmp/nothing')


class TestPic:
    """pic(1), which used to say it was unavailable."""

    def test_it_draws_the_loop_diagram(self, terminal):
        result = terminal.execute_command('pic /usr/doc/loop.pic')
        assert 'station' in result and 'switch' in result
        assert '---->' in result
        assert '.PS' not in result and '.PE' not in result

    def test_text_outside_a_block_passes_through(self, terminal):
        result = terminal.execute_command('pic /usr/doc/loop.pic')
        assert 'That is a loop' in result

    def test_a_box_is_drawn_as_a_box(self, terminal):
        terminal.write_file('/tmp/d', '.PS\nbox "frame"\n.PE\n')
        rows = terminal.execute_command('pic /tmp/d').split('\n')
        assert rows[0].startswith('+') and rows[0].endswith('+')
        assert 'frame' in rows[1]

    def test_a_circle_is_not_a_box(self, terminal):
        terminal.write_file('/tmp/d', '.PS\ncircle "office"\n.PE\n')
        assert '(' in terminal.execute_command('pic /tmp/d')

    def test_down_stacks_the_chain(self, terminal):
        terminal.write_file(
            '/tmp/d', '.PS\ndown\nbox "one"\narrow\nbox "two"\n.PE\n')
        rows = [row for row in terminal.execute_command('/bin/cat /tmp/d')
                .split('\n')]
        assert rows  # the file is there
        drawn = terminal.execute_command('pic /tmp/d')
        assert drawn.index('one') < drawn.index('two')
        assert 'v' in drawn

    def test_an_unclosed_block_is_reported(self, terminal):
        terminal.write_file('/tmp/d', '.PS\nbox "one"\n')
        assert 'without .PE' in terminal.execute_command('pic /tmp/d')

    def test_it_pipes_into_nroff(self, terminal):
        result = terminal.execute_command('pic /usr/doc/loop.pic | nroff')
        assert 'station' in result


class TestRefer:
    """refer(1), and a bibliography of papers that exist."""

    def test_citations_become_numbers(self, terminal):
        result = terminal.execute_command('refer /usr/doc/why.unix')
        assert '[1]' in result
        assert '.[' not in result and '.]' not in result

    def test_a_reference_list_is_added(self, terminal):
        result = terminal.execute_command('refer /usr/doc/why.unix')
        assert 'References' in result
        assert 'Communications of the ACM' in result
        assert '365-375' in result

    def test_the_same_paper_cited_twice_keeps_one_number(self, terminal):
        terminal.write_file(
            '/tmp/d',
            'One.\n.[\nbourne shell\n.]\nTwo.\n.[\nbourne shell\n.]\n')
        result = terminal.execute_command('refer /tmp/d')
        assert result.count('[1]') == 2
        assert '[2]' not in result

    def test_a_citation_nothing_matches_is_reported(self, terminal):
        terminal.write_file('/tmp/d', 'Text.\n.[\nnobody nothing\n.]\n')
        assert 'no reference' in terminal.execute_command('refer /tmp/d')

    def test_a_document_without_citations_comes_back_unchanged(self, terminal):
        terminal.write_file('/tmp/d', 'Just text.\n')
        assert 'References' not in terminal.execute_command('refer /tmp/d')

    def test_every_record_in_the_bibliography_has_the_fields(self, terminal):
        """
        A record refer cannot format is worse than a missing one: it prints
        a half-empty line rather than saying anything.
        """
        text = terminal.execute_command('cat /usr/dict/papers')
        for record in text.split('\n\n'):
            if not record.strip():
                continue
            keys = {line[1] for line in record.split('\n') if line.startswith('%')}
            assert {'A', 'T', 'J', 'V', 'D', 'P'} <= keys, record

    def test_it_pipes_into_nroff(self, terminal):
        result = terminal.execute_command('refer /usr/doc/why.unix | nroff')
        assert 'References' in result
        assert '.br' not in result


class TestNothingIsStillAStub:
    """The four commands this work took off the unavailable list."""

    @pytest.mark.parametrize('command', ['pic', 'refer'])
    def test_they_are_no_longer_stubs(self, command):
        assert command not in UNIMPLEMENTED_COMMANDS

    @pytest.mark.parametrize('command', ['pwb', 'rje'])
    def test_the_ones_that_never_existed_are_gone(self, terminal, command):
        """
        PWB was a system rather than a program: there was no pwb(1) to run,
        and its remote job entry was reached through send(1) and rjestat(1).
        Removing them beats implementing something that never existed.
        """
        assert command not in terminal._command_handlers
        assert command not in UNIMPLEMENTED_COMMANDS

    def test_what_replaced_them_is_real(self, terminal):
        for command in ('send', 'rjestat'):
            assert command in terminal._command_handlers
            result = terminal.execute_command(command)
            assert 'not available in this release' not in result
