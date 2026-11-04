"""
Every stamp the player can read comes from the shift clock.

The simulated time is the tour's start plus the shift minutes the work has
charged, and nothing else. These tests read the stamps the game prints and
ask them the same question: what minute of the shift is it?
"""

from datetime import timedelta

import pytest


def clock_reads(terminal) -> str:
    """The time of day the shift minutes say it is, in date(1)'s order."""
    return terminal.clock.date_command(
        terminal.settings.epoch()
        + timedelta(days=terminal.clock._day_offset,
                    hours=terminal.clock._hour_offset,
                    minutes=terminal.shift_minutes))


def date_and_expected(terminal):
    """What date prints, and what the shift minutes before it say."""
    expected = clock_reads(terminal)
    return terminal.execute_command('date'), expected


def test_date_follows_the_shift_minutes(terminal):
    terminal.execute_command('sleep 1800')
    printed, expected = date_and_expected(terminal)
    assert printed == expected
    assert terminal.shift_minutes >= 30
    assert '08:3' in printed


def test_date_moves_one_shift_minute_a_command_and_no_more(terminal):
    """
    Every command is a minute of the shift. Each date reads the minute it was
    typed at, so the host's seconds between them change nothing.
    """
    for _ in range(3):
        before = terminal.shift_minutes
        printed, expected = date_and_expected(terminal)
        assert printed == expected
        assert terminal.shift_minutes == before + 1


def test_a_message_is_stamped_with_the_minute_it_is(terminal):
    terminal.execute_command('sleep 3600')
    stamp = terminal._stamp()
    assert stamp == terminal.clock.log_stamp()
    assert stamp.startswith('09:')


def test_the_stamp_is_the_date_command_s_time(terminal):
    terminal.execute_command('sleep 600')
    assert terminal._stamp().split()[0] in terminal.execute_command('date')


def test_a_file_written_in_play_carries_the_shift_minute(terminal):
    terminal.execute_command('sleep 3600')
    terminal.execute_command('echo hello > note')
    listing = terminal.execute_command('ls -l note')
    stamp = terminal.clock.now()
    assert f"{stamp:%b} {stamp.day:>2} 09:" in listing
    assert 'Nov 14 08:00' not in listing


def test_a_file_rewritten_later_takes_the_later_minute(terminal):
    terminal.execute_command('echo one > note')
    early = terminal.execute_command('ls -l note')
    terminal.execute_command('sleep 7200')
    terminal.execute_command('echo two > note')
    late = terminal.execute_command('ls -l note')
    assert early.split()[-2] != late.split()[-2]
    assert ' 10:' in late


def test_a_directory_made_in_play_is_stamped(terminal):
    terminal.execute_command('sleep 600')
    terminal.execute_command('mkdir work')
    assert ' 08:1' in terminal.execute_command('ls -l work/..')


def test_a_shipped_file_is_as_old_as_the_epoch(terminal):
    terminal.execute_command('sleep 7200')
    listing = terminal.execute_command('ls -l /etc/passwd')
    assert 'Nov 14 08:00' in listing


def test_a_rendered_file_is_as_new_as_the_clock(terminal):
    terminal.execute_command('sleep 7200')
    listing = terminal.execute_command('ls -l /usr/lmos/board')
    assert ' 10:' in listing


def test_a_stamp_survives_the_saved_home(terminal):
    from bell_system import save
    terminal.execute_command('sleep 3600')
    terminal.execute_command('echo kept > /usr/users/sysop/keep')
    record = save.home_record(terminal.filesystem)
    node = record['nodes']['/usr/users/sysop/keep']
    assert node['mtime'] is not None
    restored = save._home_node('/usr/users/sysop/keep', node)
    assert restored.mtime == terminal.filesystem['/usr/users/sysop/keep'].mtime


def test_a_new_tour_starts_the_files_where_the_clock_is(terminal):
    terminal.execute_command('echo old > note')
    terminal.career.shift = 2
    terminal.shift_minutes = 0
    terminal.start_tour_clock()
    terminal.execute_command('echo new > note')
    stamp = terminal.clock.now()
    assert f"{stamp:%b} {stamp.day:>2} 08:" in terminal.execute_command(
        'ls -l note')
    assert stamp.day == 18


@pytest.mark.parametrize('format_', ['iso', 'us'])
def test_the_layouts_agree_with_the_shift(terminal, format_):
    terminal.settings.set('date.format', format_)
    terminal.execute_command('sleep 600')
    printed, expected = date_and_expected(terminal)
    assert printed == expected
