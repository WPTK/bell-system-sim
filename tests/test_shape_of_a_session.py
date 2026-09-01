"""
A tour that survives being closed, and a career that gets heavier.

A shift used to be one process. Closing the window threw away the board,
the weather, where every crew was standing and how much of every
commitment had been spent, and the next session opened on a fresh tour
with only the career record carried over. That is the single most likely
reason somebody plays this once.
"""

import json

import pytest

from bell_system import save
from bell_system.clock import (
    TOURS_TO_DIVESTITURE,
    career_progress,
)
from bell_system.terminal import BellSystemTerminal


@pytest.fixture
def worked(terminal):
    """A tour with something on it: measured, dispatched, time spent."""
    terminal.settings.set('game.prompts', 'off')
    for _ in range(12):
        terminal.execute_command('pwd')
    report = terminal.desk.pending()[0]
    terminal.execute_command(f'mlt {report.number}')
    terminal.execute_command(f'report dispatch {report.number} outside')
    terminal.save_shift()
    return terminal


def reopen(terminal):
    """Construct a fresh session against the same state directory."""
    fresh = BellSystemTerminal()
    fresh.career.qualifications = list(terminal.career.qualifications)
    return fresh


class TestPuttingAShiftDown:
    """The board comes back the way it was left."""

    def test_a_fresh_session_picks_it_up(self, worked):
        assert reopen(worked).resumed

    def test_the_board_is_the_same_board(self, worked):
        assert ([report.number for report in reopen(worked).desk.pending()]
                == [report.number for report in worked.desk.pending()])

    def test_the_shift_clock_carries(self, worked):
        assert reopen(worked).shift_minutes == worked.shift_minutes

    def test_what_was_spent_stays_spent(self, worked):
        """
        A resume that gave the commitments back would be a way to play the
        same tour twice with none of the cost.
        """
        before = {report.number: report.minutes_spent
                  for report in worked.desk.pending()}
        after = {report.number: report.minutes_spent
                 for report in reopen(worked).desk.pending()}
        assert after == before

    def test_a_measured_report_is_still_measured(self, worked):
        tested = {report.number for report in worked.desk.pending()
                  if report.tested}
        assert tested
        assert {report.number for report in reopen(worked).desk.pending()
                if report.tested} == tested

    def test_the_crew_that_is_out_is_still_out(self, worked):
        assert sorted(reopen(worked).desk.force.out) == \
            sorted(worked.desk.force.out)

    def test_the_weather_carries(self, worked):
        after = reopen(worked).desk.weather
        assert (after.key, after.regime, after.temperature) == (
            worked.desk.weather.key, worked.desk.weather.regime,
            worked.desk.weather.temperature)

    def test_the_water_in_the_cable_carries(self, worked):
        worked.desk.receive(worked.clock.now(), 0, fault='WET')
        worked.save_shift()
        after = reopen(worked).desk.plant
        assert len(after.sections) == len(worked.desk.plant.sections)
        assert ([section.pairs for section in after.sections]
                == [section.pairs for section in worked.desk.plant.sections])

    def test_the_regulars_are_still_the_same_lines(self, worked):
        for _ in range(300):
            worked.desk.receive(worked.clock.now(), 0)
        worked.save_shift()
        after = reopen(worked).desk._regulars
        assert set(after) == set(worked.desk._regulars)
        assert all(after[key].telephone_number
                   == worked.desk._regulars[key].telephone_number
                   for key in after)

    def test_the_wire_chief_does_not_start_over(self, worked):
        """Otherwise the walkthrough replays every time you come back."""
        worked._tour_nudges = {'open', 'board'}
        worked.save_shift()
        assert reopen(worked)._tour_nudges == {'open', 'board'}

    def test_the_hint_level_does_not_start_over(self, worked):
        worked.execute_command('hint')
        worked.execute_command('hint')
        worked.save_shift()
        assert reopen(worked)._hint_level == worked._hint_level

    def test_the_session_says_it_resumed(self, worked, capsys):
        fresh = reopen(worked)
        fresh.role = 'cro'
        fresh.show_shift_briefing()
        assert 'Resumed' in capsys.readouterr().out


class TestWhatIsNotPickedUp:
    """A half-applied resume is worse than none."""

    def test_a_file_from_another_version_is_refused(self, worked):
        stored = save.read(worked.shift_file)
        stored['version'] = save.VERSION + 99
        with open(worked.shift_file, 'w') as handle:
            json.dump(stored, handle)
        assert not reopen(worked).resumed

    def test_a_file_from_another_tour_is_refused(self, worked):
        stored = save.read(worked.shift_file)
        stored['shift'] = worked.career.shift + 1
        with open(worked.shift_file, 'w') as handle:
            json.dump(stored, handle)
        assert not reopen(worked).resumed

    def test_a_file_from_another_wire_centre_is_refused(self, worked):
        stored = save.read(worked.shift_file)
        stored['clli'] = 'NWRKNJ02X'
        with open(worked.shift_file, 'w') as handle:
            json.dump(stored, handle)
        assert not reopen(worked).resumed

    def test_rubbish_is_refused_rather_than_raised(self, worked):
        with open(worked.shift_file, 'w') as handle:
            handle.write('{"version": 1, "shift": ')
        assert not reopen(worked).resumed

    def test_a_truncated_board_is_refused(self, worked):
        stored = save.read(worked.shift_file)
        del stored['board']['reports'][0]['received']
        with open(worked.shift_file, 'w') as handle:
            json.dump(stored, handle)
        assert not reopen(worked).resumed

    def test_a_refused_file_leaves_a_working_board(self, worked):
        with open(worked.shift_file, 'w') as handle:
            handle.write('not json at all')
        fresh = reopen(worked)
        assert not fresh.resumed
        assert fresh.execute_command('report')

    def test_a_refused_file_is_thrown_away(self, worked):
        import os
        with open(worked.shift_file, 'w') as handle:
            handle.write('not json at all')
        reopen(worked)
        assert not os.path.exists(worked.shift_file)

    def test_signing_off_throws_the_tour_away(self, worked):
        import os
        worked.execute_command('handoff relieve')
        assert not os.path.exists(worked.shift_file)
        assert not worked.resumed


class TestWhereYouAreInTheTour:
    """shift(1): the four numbers you want in the middle of one."""

    def test_it_says_how_far_in_you_are(self, worked):
        assert f"Worked              {worked.shift_time()}" in \
            worked.execute_command('shift')

    def test_it_counts_the_board(self, worked):
        listing = worked.execute_command('shift')
        # Read back off the same output: running shift(1) costs a minute
        # like anything else, and a report can arrive in it.
        counted = next(int(row.split()[-1]) for row in listing.split('\n')
                       if row.strip().startswith('On the board'))
        assert counted == len(worked.desk.pending())

    def test_it_names_who_is_out(self, worked):
        assert 'OUT NOW' in worked.execute_command('shift')

    def test_it_carries_the_countdown(self, worked):
        assert 'days to divestiture' in worked.execute_command('shift')

    def test_it_points_at_the_full_record(self, worked):
        assert 'handoff' in worked.execute_command('shift')

    def test_the_manual_documents_it(self):
        from bell_system.data.man_pages import MAN_PAGES
        assert 'where you are in the tour' in MAN_PAGES['shift']


class TestEscalationAcrossACareer:
    """
    Tour one is quiet and tour thirteen is not.

    The difficulty setting still governs only how forgiving the scoring is,
    which is the line this must not cross.
    """

    def test_progress_runs_from_nothing_to_everything(self):
        assert career_progress(1) == 0.0
        assert career_progress(TOURS_TO_DIVESTITURE) == 1.0

    def test_it_does_not_run_past_the_end(self):
        assert career_progress(TOURS_TO_DIVESTITURE + 40) == 1.0

    def test_the_board_gets_deeper(self, terminal):
        terminal.career.shift = 1
        early = terminal.board_depth()
        terminal.career.shift = TOURS_TO_DIVESTITURE
        assert terminal.board_depth() > early

    def test_the_board_never_starts_full(self, terminal):
        """
        A depth near the opening backlog gives a desk that refuses work for
        the whole tour, which is how this lever went wrong the last time.
        """
        from bell_system.data.positions import POSITIONS
        for tour in range(1, TOURS_TO_DIVESTITURE + 1):
            terminal.career.shift = tour
            for key in POSITIONS:
                terminal.take_position(key)
                assert terminal.board_depth() >= 7

    def test_later_tours_are_wetter(self):
        import random
        from bell_system.weather import Weather
        wet = {'DRIZZLE', 'RAIN', 'HEAVY'}

        def share(bias):
            drawn = [Weather(random.Random(n), wet_bias=bias).regime
                     for n in range(2000)]
            return sum(1 for regime in drawn if regime in wet) / len(drawn)

        assert share(1.0) > share(0.0) + 0.05

    def test_a_dry_tour_is_never_impossible(self):
        """A lever that closes off an outcome is not a lever."""
        import random
        from bell_system.weather import Weather
        drawn = {Weather(random.Random(n), wet_bias=1.0).regime
                 for n in range(500)}
        assert 'CLEAR' in drawn

    def test_signing_off_draws_the_new_day_weather(self, terminal):
        """Four days on is a different day, not the same one continued."""
        terminal.career.shift = 1
        before = terminal.desk.weather
        terminal.execute_command('handoff relieve')
        assert terminal.desk.weather is not before

    def test_the_water_does_not_dry_up_overnight(self, terminal):
        """Which is the whole reason a sheath is worth a trip."""
        terminal.desk.receive(terminal.clock.now(), 0, fault='WET')
        sections = len(terminal.desk.plant.sections)
        terminal.execute_command('handoff relieve')
        assert len(terminal.desk.plant.sections) == sections

    def test_difficulty_still_only_governs_scoring(self, terminal):
        """
        The line this must not cross. Nothing about how much is happening
        may depend on the difficulty setting.
        """
        from bell_system.progression import DIFFICULTIES
        depths = set()
        for key in DIFFICULTIES:
            terminal.career.set_difficulty(key)
            depths.add(terminal.board_depth())
        assert len(depths) == 1


class TestTheLastTour:
    """
    A career walks the calendar, so it has an end.

    There is no fourteenth tour of the Bell System. Signing off the
    thirteenth closes the career rather than opening a board, and it
    happens once.
    """

    @pytest.fixture
    def ending(self, terminal):
        terminal.career.shift = TOURS_TO_DIVESTITURE
        terminal.career.reports_closed = 84
        terminal.career.reports_correct = 74
        terminal.career.index_history = [60.0 + n for n in range(12)]
        terminal.career.save()
        terminal.clock.set_tour(terminal.career.shift)
        return terminal

    def test_it_closes_the_career(self, ending):
        assert 'THE CAREER' in ending.execute_command('handoff relieve')

    def test_it_does_not_open_another_board(self, ending):
        signed_off = ending.execute_command('handoff relieve')
        assert 'begins' not in signed_off

    def test_the_tour_count_stops(self, ending):
        ending.execute_command('handoff relieve')
        assert ending.career.shift == TOURS_TO_DIVESTITURE

    def test_the_wire_chief_has_the_last_word(self, ending):
        assert 'ehalloran' in ending.execute_command('handoff relieve')

    def test_it_draws_the_whole_career(self, ending):
        assert 'Every tour of it' in ending.execute_command('handoff relieve')

    def test_the_index_is_banked_once(self, ending):
        before = len(ending.career.index_history)
        ending.execute_command('handoff relieve')
        ending.execute_command('handoff relieve')
        ending.execute_command('handoff relieve')
        assert len(ending.career.index_history) == before + 1

    def test_nobody_relieves_you_twice(self, ending):
        ending.execute_command('handoff relieve')
        assert 'relieve you twice' in ending.execute_command('handoff relieve')

    def test_the_ending_survives_the_session(self, ending):
        ending.execute_command('handoff relieve')
        assert reopen(ending).career.finished

    def test_the_board_is_still_there_afterwards(self, ending):
        """The machine did not stop on the first of January either."""
        ending.execute_command('handoff relieve')
        assert 'Pending Trouble Reports' in ending.execute_command('report')

    def test_an_ordinary_tour_still_opens_a_board(self, terminal):
        terminal.career.shift = 2
        assert 'begins' in terminal.execute_command('handoff relieve')

    def test_the_manual_says_there_is_an_end(self):
        from bell_system.data.man_pages import MAN_PAGES
        assert 'no fourteenth' in MAN_PAGES['handoff']
