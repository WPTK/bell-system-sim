"""
One clock for every stamp, and the files that carry it (#93, the clocks).

A stamp the player reads is the tour's start plus the shift minutes worked,
and nothing that happened before the tour is ever dated after it: an alarm
raised, a login, a file. These tests hold that across the places a stamp
could slip: a tour boundary, midnight on an evening watch, a resume.
"""

import io
import json
import random
import re
from contextlib import redirect_stdout
from datetime import timedelta

import pytest

from bell_system import save
from bell_system.data import tours
from bell_system.filesystem import PLAYER_LIMIT, normalise
from bell_system.progression import QUALIFICATIONS
from bell_system.terminal import BellSystemTerminal

SEED = 20


def tour_of(watch):
    return next(n for n in range(2, 14) if tours.watch_of(n) == watch)


def build(role=None, tour=2, signed=True):
    instance = BellSystemTerminal(rng=random.Random(SEED))
    instance.settings.set('game.ambience', 'off')
    instance.settings.set('display.pacing', 'off')
    instance.settings.set('game.prompts', 'off')
    if signed:
        instance.career.qualifications = [q.key for q in QUALIFICATIONS]
    instance.career.shift = tour
    instance.start_tour_clock()
    if role:
        with redirect_stdout(io.StringIO()):
            instance.take_position(role)
    return instance


def mtime(terminal, name):
    return terminal.filesystem[normalise(name, terminal.current_directory)].mtime


# -- who ---------------------------------------------------------------------

@pytest.mark.parametrize('watch', ['day', 'evening', 'night'])
def test_nobody_logged_in_after_the_tour_opened(watch):
    terminal = build(tour=tour_of(watch))
    opened = terminal.clock.tour_start()
    logins = terminal.execute_command('who').splitlines()
    assert logins
    for line in logins:
        clock = re.search(r'\b(\d\d):(\d\d)\b', line)
        said = opened.replace(hour=int(clock.group(1)),
                              minute=int(clock.group(2)))
        if said > opened:
            said -= timedelta(days=1)
        # Before the tour opened, and not by more than the longest offset.
        assert timedelta(0) < opened - said <= timedelta(hours=3), line


def test_who_does_not_slide_with_the_shift():
    terminal = build()
    first = terminal.execute_command('who')
    terminal.execute_command('sleep 3000')
    again = terminal.execute_command('who')
    times = lambda text: {line.split()[0]: line.split()[2]  # noqa: E731
                          for line in text.splitlines()}
    before, after = times(first), times(again)
    assert before and set(before) & set(after)
    for user in set(before) & set(after):
        assert before[user] == after[user]


# -- time --------------------------------------------------------------------

def test_time_reports_the_minutes_the_command_charged(terminal):
    reads = [terminal.execute_command('time date') for _ in range(3)]
    for read in reads:
        real = re.search(r'real\s+(\d+\.\d)', read)
        assert float(real.group(1)) == 60.0
    long = terminal.execute_command('time sleep 600')
    seconds = float(re.search(r'real\s+(\d+\.\d)', long).group(1))
    assert seconds >= 600 and seconds % 60 == 0


# -- alarms ------------------------------------------------------------------

def stamps(terminal):
    return {alarm['id']: alarm['timestamp'] for alarm in terminal.active_alarms}


def resumed(terminal):
    captured = json.loads(json.dumps(save.capture(terminal)))
    fresh = BellSystemTerminal(rng=random.Random(SEED))
    fresh.settings.set('game.prompts', 'off')
    fresh.career.shift = terminal.career.shift
    fresh.career.qualifications = list(terminal.career.qualifications)
    fresh.start_tour_clock()
    assert save.restore(fresh, captured)
    with redirect_stdout(io.StringIO()):
        fresh.take_position('switch')
    return fresh


@pytest.mark.parametrize('watch', ['day', 'evening', 'night'])
def test_alarms_were_raised_before_the_tour_and_never_after_it(watch):
    terminal = build('switch', tour=tour_of(watch))
    opened = terminal.clock.tour_start()
    assert terminal.active_alarms
    for alarm in terminal.active_alarms:
        assert alarm['timestamp'] < opened
    for row in terminal.lamp_panel():
        assert row[0]['timestamp'] <= terminal.clock.now()


def test_an_alarm_keeps_its_stamp_across_a_resume():
    terminal = build('switch', tour=tour_of('evening'))
    before = stamps(terminal)
    terminal.execute_command('sleep 5400')
    assert terminal.shift_minutes > 90
    # Still the stamps it was raised with after the shift moved on.
    assert stamps(terminal) == before
    fresh = resumed(terminal)
    assert fresh.shift_minutes == terminal.shift_minutes
    assert stamps(fresh) == before
    for alarm in fresh.active_alarms:
        assert alarm['timestamp'] < fresh.clock.tour_start()


# -- the panel on a tour the lamps are not running ---------------------------

def test_a_grace_tour_panel_says_the_lamps_are_not_running():
    terminal = build('switch', tour=3, signed=False)
    terminal.career.qualifications = [
        q.key for q in QUALIFICATIONS if q.key != 'scc']
    terminal.start_tour_clock()
    terminal.deal_alarms()
    terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
    panel = terminal.execute_command('connect work')
    assert 'lamps are not running this tour' in panel
    assert 'NEXT' not in panel
    assert re.search(r'\b40m\b', panel) is None
    assert 'lights one lamp higher' not in panel


def test_a_running_panel_has_the_next_column_and_no_grace_line():
    terminal = build('switch', tour=4)
    panel = terminal.execute_command('connect work')
    assert 'NEXT' in panel
    assert 'not running' not in panel
    assert 'lights one lamp higher' in panel


# -- the lamp book opens with the tour ---------------------------------------

def test_the_lamp_book_is_opened_when_the_tour_opens():
    terminal = build(tour=3, signed=False)
    terminal.career.qualifications = [
        q.key for q in QUALIFICATIONS if q.key != 'scc']
    terminal._lamp_book = None
    terminal.start_tour_clock()
    book = terminal._lamp_book
    assert book is not None and book['tour'] == 3 and book['live'] is False
    # A sign-off passed later in the tour cannot change what it was.
    terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
    assert terminal.lamp_book() is book and book['live'] is False


def test_a_practical_does_not_have_to_open_the_book():
    """The tour's opening has already settled it, signed off or not."""
    terminal = build(tour=3, signed=False)
    terminal.career.qualifications = [
        q.key for q in QUALIFICATIONS if q.key not in ('scc', 'connect')]
    terminal._lamp_book = None
    terminal.start_tour_clock()
    assert terminal._lamp_book is not None
    assert terminal._lamp_book['live'] == terminal.career.may_use('connect')


# -- files -------------------------------------------------------------------

def test_cp_stamps_the_copy_now_and_leaves_the_original_alone(terminal):
    terminal.execute_command('echo one > note')
    made = mtime(terminal, 'note')
    terminal.execute_command('sleep 3600')
    terminal.execute_command('cp note copy')
    assert mtime(terminal, 'note') == made
    assert mtime(terminal, 'copy') > made
    assert mtime(terminal, 'copy') - made >= timedelta(minutes=60)


def an_old_home_file(terminal, name):
    """A file from a home written before files carried their times."""
    terminal.execute_command(f'echo one > {name}')
    path = normalise(name, terminal.current_directory)
    terminal.filesystem[path] = terminal.filesystem[path]._replace(mtime=None)
    return path


def test_mv_keeps_the_mtime(terminal):
    terminal.execute_command('echo one > note')
    made = mtime(terminal, 'note')
    terminal.execute_command('sleep 3600')
    terminal.execute_command('mv note moved')
    assert mtime(terminal, 'moved') == made


def test_mv_does_not_date_a_file_that_has_no_mtime(terminal):
    an_old_home_file(terminal, 'note')
    terminal.execute_command('sleep 3600')
    terminal.execute_command('mv note moved')
    assert mtime(terminal, 'moved') is None
    # Still as old as the epoch, which is what ls says of it.
    assert 'Nov 14 08:00' in terminal.execute_command('ls -l moved')


def test_mkdir_and_cc_stamp_what_they_make(terminal):
    terminal.execute_command('sleep 600')
    terminal.execute_command('mkdir work')
    assert mtime(terminal, 'work') is not None
    assert mtime(terminal, 'work') >= terminal.clock.tour_start() + timedelta(
        minutes=10)


def test_chmod_does_not_make_a_file_newer(terminal):
    terminal.execute_command('echo one > note')
    made = mtime(terminal, 'note')
    terminal.execute_command('sleep 3600')
    terminal.execute_command('chmod 600 note')
    assert mtime(terminal, 'note') == made


def test_chmod_does_not_date_a_file_that_has_no_mtime(terminal):
    an_old_home_file(terminal, 'note')
    terminal.execute_command('sleep 3600')
    terminal.execute_command('chmod 600 note')
    assert mtime(terminal, 'note') is None
    assert 'Nov 14 08:00' in terminal.execute_command('ls -l note')


def assert_never_goes_back(terminal, names):
    stamped = [mtime(terminal, name) for name in names]
    assert stamped == sorted(stamped)
    assert len(set(stamped)) == len(stamped)


def test_stamps_climb_across_a_tour_boundary(terminal):
    terminal.execute_command('echo a > first')
    terminal.execute_command('sleep 300')
    terminal._end_shift()
    assert terminal.shift_minutes == 0
    terminal.execute_command('echo b > second')
    assert mtime(terminal, 'second') > mtime(terminal, 'first')
    assert terminal.clock.now() > mtime(terminal, 'first')


def test_stamps_climb_through_midnight_on_an_evening_tour():
    terminal = build(tour=tour_of('evening'))
    names = []
    for index in range(4):
        terminal.execute_command(f'echo x > f{index}')
        names.append(f'f{index}')
        terminal.execute_command('sleep 3600')
    terminal.execute_command('sleep 14400')
    terminal.execute_command('echo x > after')
    names.append('after')
    assert_never_goes_back(terminal, names)
    # Past midnight into the next calendar day, and still later.
    assert mtime(terminal, 'after').date() > mtime(terminal, 'f0').date()


def test_stamps_climb_across_a_resume():
    terminal = build('switch', tour=tour_of('evening'))
    terminal.execute_command('echo x > before')
    terminal.execute_command('sleep 1800')
    fresh = resumed(terminal)
    # The files are kept apart from the shift: put back as a new session does.
    assert save.restore_home(fresh, json.loads(json.dumps(
        save.home_record(terminal.filesystem)))) == 0
    fresh.current_directory = terminal.current_directory
    fresh.execute_command('echo y > after')
    assert mtime(fresh, 'before') == mtime(terminal, 'before')
    assert mtime(fresh, 'after') > mtime(fresh, 'before')


def test_a_home_without_stamps_still_loads_and_lists():
    """A home written before files carried their times has no mtime keys."""
    terminal = build()
    terminal.execute_command('echo old > oldnote')
    record = save.home_record(terminal.filesystem)
    path = normalise('oldnote', terminal.current_directory)
    assert record['nodes'][path]['mtime']
    for entry in record['nodes'].values():
        entry.pop('mtime', None)
    fresh = build()
    save.restore_home(fresh, json.loads(json.dumps(record)))
    node = fresh.filesystem[path]
    assert node.mtime is None and node.content == 'old\n'
    listing = fresh.execute_command('ls -l oldnote')
    assert 'oldnote' in listing and 'Nov 14 08:00' in listing


def test_stamps_do_not_count_against_the_limit(terminal):
    terminal.execute_command('echo x > a')
    path = normalise('a', terminal.current_directory)
    stamped = save.home_size(terminal.filesystem)
    assert terminal.filesystem[path].mtime is not None
    terminal.filesystem[path] = terminal.filesystem[path]._replace(mtime=None)
    assert save.home_size(terminal.filesystem) == stamped


def test_a_home_filled_to_the_limit_is_still_written(terminal, tmp_path):
    """The cap is on content: the stamps on many small files cannot beat it."""
    for index in range(300):
        name = normalise(f'f{index}', terminal.current_directory)
        assert terminal.write_file(name, 'x') is None
    # Less than the whole of what is left: the file's own entry takes room.
    room = PLAYER_LIMIT - save.home_size(terminal.filesystem) - 300
    assert terminal.write_file(
        normalise('big', terminal.current_directory), 'x' * room) is None
    assert save.home_size(terminal.filesystem) <= PLAYER_LIMIT
    # With its stamps the record is over the limit; it is still kept.
    assert len(save.home_text(terminal.filesystem).encode()) > PLAYER_LIMIT
    where = tmp_path / 'home.json'
    save.write_home(str(where), terminal)
    assert where.exists()
    # And one more byte of content is what is refused, not a stamp.
    over = terminal.write_file(normalise('more', terminal.current_directory),
                               'x' * 200)
    assert over and 'no space left' in over
