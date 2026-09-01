"""
Knowing what to do next.

Playing a fresh shift the way a new player would turned up the finding this
module exists to answer: the loop is four commands and mlt(1) names both the
fault and the crew, so the game is not hard, it is undiscoverable. These
cover the three places that now say what to do, and the one function all
three of them ask.
"""

import pytest

from bell_system.progression import QUALIFICATIONS
from bell_system.screens.guidance import FIRST_TOUR


@pytest.fixture
def working(raw_terminal):
    """A craftsperson past their first tour, with a board to work."""
    raw_terminal.career.shift = 2
    raw_terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
    raw_terminal.settings.set('game.ambience', 'off')
    return raw_terminal


def board(terminal, count=3):
    """Put a known number of untouched reports on the board."""
    terminal.desk.reports.clear()
    terminal.desk.order.clear()
    terminal.desk.open_shift(terminal.clock.now(), 0, count=count)
    return terminal.desk.pending()


class TestWhatToDoNext:
    """One function decides, and it decides by what would actually cost you."""

    def test_an_untested_report_wants_measuring(self, working):
        board(working)
        action = working.next_action()
        assert action.step == 'measure'
        assert action.command.startswith('mlt ')

    def test_a_cleared_report_beats_an_untested_one(self, working):
        """
        The field has been and gone. Closing it costs two minutes; leaving it
        costs the customer the rest of the day.
        """
        pending = board(working)
        pending[-1].field_finding = 'OPEN'
        action = working.next_action()
        assert action.step == 'close'
        assert pending[-1].number in action.command

    def test_an_overdue_report_beats_one_still_in_time(self, working):
        pending = board(working)
        late = pending[-1]
        late.tested = True
        late.spend(int((late.commitment - late.received).total_seconds() // 60)
                   + 1)
        assert late.overdue()
        action = working.next_action()
        assert late.number in action.command

    def test_a_clear_board_is_not_a_failure_state(self, working):
        working.desk.reports.clear()
        working.desk.order.clear()
        assert 'Board clear' in working.next_action().reason

    def test_the_crew_is_only_named_after_the_measurement(self, working):
        """
        Naming the right force before the test would hand over the answer,
        and the measurement is the part worth doing.
        """
        pending = board(working, count=1)
        report = pending[0]
        assert working.next_action().step == 'measure'
        report.tested = True
        assert working.next_action().step == 'dispatch'


class TestTheStandingPrompt:
    """The line printed after a command that leaves you with nothing."""

    def test_it_says_what_to_type(self, working):
        board(working)
        line = working.next_line()
        assert line.startswith('Next: ')
        assert working.next_action().command in line

    def test_it_can_be_turned_off(self, working):
        board(working)
        working.settings.set('game.prompts', 'off')
        assert working.next_line() == ''

    def test_it_is_on_by_default(self, raw_terminal):
        assert raw_terminal.settings.is_on('game.prompts')

    def test_it_follows_a_command_that_shows_nothing(self, working):
        board(working)
        assert 'Next:' in working.execute_command('pwd')

    def test_it_keeps_off_a_command_that_shows_something(self, working):
        """A prompt under the board is arguing with the board."""
        board(working)
        assert 'Next:' not in working.execute_command('report')


class TestHelpLeadsWithTheWork:
    """
    help(1) used to open on forty commands and close on the sixteen you were
    not signed off on, so a new craftsperson's first impression of the job
    was a list of things they could not do.
    """

    def test_the_first_section_is_what_to_do_now(self, working):
        board(working)
        sections = [line for line in working.execute_command('help').split('\n')
                    if line[:1].isalpha() and line == line.upper()]
        assert sections[0] == 'WHAT TO DO NOW'

    def test_it_names_the_loop_outright(self, working):
        text = working.execute_command('help')
        for command in ('report', 'mlt', 'report dispatch', 'report close'):
            assert command in text

    def test_it_agrees_with_the_standing_prompt(self, working):
        """Same function, so they cannot drift apart."""
        board(working)
        assert working.next_action().command in working.execute_command('help')

    def test_the_locked_list_moved_to_qual(self, working):
        working.career.qualifications = ['central_office']
        assert 'Not signed off:' not in working.execute_command('help')
        assert 'NOT SIGNED OFF' in working.execute_command('qual')

    def test_help_still_counts_what_is_locked(self, working):
        working.career.qualifications = ['central_office']
        assert 'not signed off on' in working.execute_command('help')


class TestTheWireChief:
    """FIRST_TOUR is the whole of the tutorial that replaced tutorial.py."""

    def test_each_line_names_something_to_type(self):
        """A step that does not say what to type is not guidance."""
        for step, lines in FIRST_TOUR.items():
            if step in ('open', 'board'):
                assert any("'" in line for line in lines), step

    def test_nobody_shouts_step_one_of_seven(self):
        """It is a colleague on write(1), not a tutorial box."""
        for lines in FIRST_TOUR.values():
            for line in lines:
                assert 'STEP' not in line.upper()

    def test_he_arrives_on_write(self, raw_terminal):
        raw_terminal.career.shift = 1
        raw_terminal.career.reports_closed = 0
        raw_terminal._tour_nudges.clear()
        nudge = raw_terminal.first_tour_nudge('board')
        assert 'Message from ehalloran' in nudge

class TestEveryRefusalNamesAWayOut:
    """
    A refusal that names nothing is where a player stops.

    Mistyping a command, or reaching for one you are not signed off on,
    should not cost anybody their place in the job.
    """

    def test_an_unknown_command_still_points_at_the_work(self, working):
        board(working)
        assert 'Meanwhile:' in working.execute_command('frobnicate')

    def test_a_command_you_may_not_use_points_at_the_work(self, working):
        board(working)
        working.career.qualifications = ['central_office']
        refusal = working.execute_command('connect')
        assert 'not signed off' in refusal
        assert 'Meanwhile:' in refusal

    def test_an_unknown_report_verb_points_at_the_work(self, working):
        board(working)
        assert 'Meanwhile:' in working.execute_command('report wibble')

    def test_the_way_out_goes_quiet_with_the_prompt(self, working):
        board(working)
        working.settings.set('game.prompts', 'off')
        assert 'Meanwhile:' not in working.execute_command('frobnicate')

    def test_a_clear_board_adds_nothing_to_a_refusal(self, working):
        """There is no way out to name when nothing is waiting."""
        working.desk.reports.clear()
        working.desk.order.clear()
        working.career.qualifications = []
        assert 'Meanwhile:' not in working.dead_end('no')


class TestReportNext:
    """One word instead of reading a table."""

    def test_it_shows_the_report_the_prompt_points_at(self, working):
        board(working)
        wanted = working.next_action()
        shown = working.execute_command('report next')
        assert wanted.command.split()[-1] in shown
        assert f"Type: {wanted.command}" in shown

    def test_it_falls_back_to_the_board_when_nothing_is_pending(self, working):
        working.desk.reports.clear()
        working.desk.order.clear()
        assert 'Board is clear' in working.execute_command('report next')

    def test_the_board_names_it(self, working):
        board(working)
        assert "'report next'" in working.execute_command('report')

    def test_the_board_stays_quiet_with_the_prompt_off(self, working):
        board(working)
        working.settings.set('game.prompts', 'off')
        assert "'report next'" not in working.execute_command('report')

    def test_the_manual_documents_it(self):
        from bell_system.data.man_pages import MAN_PAGES
        assert 'report next' in MAN_PAGES['report']
