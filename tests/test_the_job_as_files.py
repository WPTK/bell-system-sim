"""
The job reached through the shell rather than through twelve screens.

Everything the position works on is state the terminal holds, and the
terminal is a UNIX machine. A board you can only see through report(1) is
a quiz with a UNIX theme; a board that is also files is a job done on a
computer, and cat(1), grep(1), sort(1) and a pipe are the second way to
do all of it.
"""

import pytest

from bell_system.terminal import LMOS_DIR, RESERVED_LMOS_NAMES


@pytest.fixture
def board(terminal):
    """A tour with a worked board: measured, dispatched, one closed."""
    terminal.settings.set('game.prompts', 'off')
    for _ in range(8):
        terminal.execute_command('pwd')
    # A report with a fault actually on it, so the close-out in this
    # fixture is a correct one - code 5 naming NONE is not - and asked for
    # rather than hunted, because a board can come up all clear.
    report = terminal.desk.receive(terminal.clock.now(), 0, fault='SHORT')
    terminal.execute_command(f'mlt {report.number}')
    terminal.execute_command(f'report dispatch {report.number} outside')
    terminal.execute_command(
        f'report close {report.number} 5 {report.record.fault}')
    return terminal


class TestOneFilePerReport:
    """A report is a record, and a record was a piece of paper."""

    def test_the_directory_is_the_board(self, board):
        """
        Read without running a command in between: a command costs a minute
        and work arrives in minutes, so two observations either side of one
        are two different boards.
        """
        from bell_system.filesystem import children
        board._sync_report_files()
        listed = set(children('/usr/lmos', board.filesystem))
        assert listed == ({report.number for report in board.desk.pending()}
                          | set(RESERVED_LMOS_NAMES))

    def test_ls_shows_them(self, board):
        listed = set(board.execute_command('ls /usr/lmos').split())
        assert any(name.startswith('TR-') for name in listed)
        assert RESERVED_LMOS_NAMES <= listed

    def test_a_closed_report_leaves_the_directory(self, board):
        """A listing that still names it is worse than not having it."""
        gone = board.desk.closed()[0].number
        assert gone not in board.execute_command('ls /usr/lmos').split()

    def test_the_file_is_the_whole_record(self, board):
        report = board.desk.pending()[0]
        text = board.execute_command(f'cat {LMOS_DIR}{report.number}')
        assert report.record.telephone_number in text
        assert report.record.cable_pair() in text
        assert report.symptom in text

    def test_it_carries_the_measurements(self, board):
        report = next(r for r in board.desk.pending() if not r.tested)
        assert 'has not been run' in board.execute_command(
            f'cat {LMOS_DIR}{report.number}')
        board.execute_command(f'mlt {report.number}')
        assert 'insulation' in board.execute_command(
            f'cat {LMOS_DIR}{report.number}')

    def test_it_says_when_the_line_is_one_you_know(self, board):
        for _ in range(400):
            board.desk.receive(board.clock.now(), 0)
        board.execute_command('pwd')
        known = next((r for r in board.desk.pending() if r.record.regular),
                     None)
        if known is None:
            pytest.skip('no regular on the board this run')
        assert 'known' in board.execute_command(f'cat {LMOS_DIR}{known.number}')

    def test_a_pipeline_works_on_it(self, board):
        """One name to a line, so wc(1) counts what ls(1) listed."""
        listing = board.execute_command('ls /usr/lmos')
        counted = int(board.execute_command('ls /usr/lmos | wc -l'))
        assert counted >= len(listing.split()) - 1
        assert counted > len(RESERVED_LMOS_NAMES)

    def test_the_reserved_names_are_always_there(self, board):
        listed = set(board.execute_command('ls /usr/lmos').split())
        assert RESERVED_LMOS_NAMES <= listed


class TestTheOtherRecords:
    """What is closed, and where the water is."""

    def test_what_you_got_wrong_is_greppable(self, board):
        report = board.desk.pending()[0]
        wrong = 'SHORT' if report.record.fault != 'SHORT' else 'WET'
        board.execute_command(f'mlt {report.number}')
        board.execute_command(f'report close {report.number} 5 {wrong}')
        assert report.number in board.execute_command(
            'grep WRONG /usr/lmos/closed')

    def test_a_correct_close_is_not_in_that_list(self, board):
        right = board.desk.closed()[0]
        assert right.number not in board.execute_command(
            'grep WRONG /usr/lmos/closed')

    def test_the_cable_record_names_the_wet_sections(self, board):
        for _ in range(4):
            board.desk.receive(board.clock.now(), 0, fault='WET')
        board.execute_command('pwd')
        text = board.execute_command('cat /usr/lmos/cable')
        section = board.desk.plant.sections[0]
        assert str(section.cable) in text
        assert all(number in text for number in section.pairs.values())

    def test_it_says_so_when_the_plant_is_dry(self, terminal):
        terminal.desk.plant.sections = []
        assert 'no wet sections' in terminal.execute_command(
            'cat /usr/lmos/cable')

    def test_the_cable_record_carries_the_weather(self, board):
        assert board.desk.weather.key in board.execute_command(
            'cat /usr/lmos/cable')

    def test_the_shift_log_is_still_a_file(self, board):
        assert 'closed' in board.execute_command('cat /usr/adm/shiftlog')


class TestTheMailbox:
    """Seventh Edition kept mail in a file and mail(1) read it."""

    def test_it_is_made_out_to_whoever_is_at_the_position(self, raw_terminal):
        """
        The filesystem is built before anybody has logged in, so it was
        being made out to sysop and left there.
        """
        raw_terminal._apply_role('cro', 'Central Office Repair',
                                 announce=False)
        assert raw_terminal.execute_command(
            'ls /usr/spool/mail').split() == ['cro']

    def test_mail_can_be_read_with_cat(self, terminal):
        terminal.switchroom.qualification_notice(
            terminal.clock.now(), 'Main Distributing Frame', ['cosmos'])
        assert 'signed off' in terminal.execute_command(
            f'cat /usr/spool/mail/{terminal.username}')

    def test_it_can_be_grepped(self, terminal):
        terminal.switchroom.qualification_notice(
            terminal.clock.now(), 'Main Distributing Frame', ['cosmos'])
        assert 'signed off' in terminal.execute_command(
            f'grep signed /usr/spool/mail/{terminal.username}')

    def test_reading_it_with_mail_empties_it(self, terminal):
        """Which is also what Seventh Edition did."""
        terminal.switchroom.qualification_notice(
            terminal.clock.now(), 'Main Distributing Frame', ['cosmos'])
        terminal.execute_command('mail')
        assert not terminal.execute_command(
            f'cat /usr/spool/mail/{terminal.username}').strip()

    def test_nobody_else_can_read_it(self, terminal):
        assert '-rw-------' in terminal.execute_command('ls -l /usr/spool/mail')


class TestItIsDiscoverable:
    """A second way to do everything is no use if nothing says so."""

    def test_help_names_the_directory(self, terminal):
        assert '/usr/lmos' in terminal.execute_command('help')

    def test_help_names_the_mailbox(self, terminal):
        assert '/usr/spool/mail' in terminal.execute_command('help')

    def test_the_practices_are_still_readable(self, terminal):
        assert 'BELL SYSTEM PRACTICE' in terminal.execute_command(
            'cat /usr/bsp/660')
