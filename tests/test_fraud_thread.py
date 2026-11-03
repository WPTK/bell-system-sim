"""
A11: a toll-fraud thread that is detection and history and nothing else.

Each test sets the tour and the clock it needs. None relies on what a board
happens to be dealt.
"""

import re

import pytest

from bell_system.data import fraud


def _at(terminal, tour=9, minutes=200):
    terminal.career.shift = tour
    terminal.shift_minutes = minutes
    return terminal


def _all_the_words(tour=9):
    return '\n'.join(fraud.exception_block(tour) + fraud.note(tour))


class TestTheAnomalyOnTheCounts:
    """`traffic` and `tnds analysis` show it, while there is something to see."""

    def test_traffic_shows_it_when_the_thread_is_live(self, terminal):
        shown = _at(terminal).execute_command('traffic')
        assert 'HOLDING-TIME EXCEPTION' in shown
        assert fraud.GROUP in shown

    def test_the_analysis_shows_it_too(self, terminal):
        shown = _at(terminal).execute_command('tnds analysis')
        assert 'HOLDING-TIME EXCEPTION' in shown

    def test_nothing_before_the_thread_begins(self, terminal):
        shown = _at(terminal, tour=fraud.FIRST_TOUR - 1).execute_command(
            'traffic')
        assert 'HOLDING-TIME EXCEPTION' not in shown

    def test_nothing_after_it_ends(self, terminal):
        shown = _at(terminal, tour=fraud.LAST_TOUR + 1).execute_command(
            'traffic')
        assert 'HOLDING-TIME EXCEPTION' not in shown

    def test_nothing_until_the_tour_is_under_way(self, terminal):
        shown = _at(terminal, minutes=fraud.SHOWS_AFTER - 1).execute_command(
            'traffic')
        assert 'HOLDING-TIME EXCEPTION' not in shown

    def test_the_counts_are_the_same_every_time_they_are_looked_at(self):
        assert fraud.exception_block(9) == fraud.exception_block(9)

    def test_the_counts_are_set_against_what_is_usual(self):
        text = '\n'.join(fraud.exception_block(9))
        assert str(fraud.NORMAL_SEIZURES) in text
        assert str(fraud.NORMAL_HOLD) in text

    def test_looking_changes_nothing_that_is_kept(self, terminal):
        # Short of the note's time, which the clock the command runs on
        # would otherwise bring in.
        _at(terminal, minutes=fraud.SHOWS_AFTER + 5)
        before = list(terminal.career.beats_seen)
        terminal.execute_command('traffic')
        terminal.execute_command('tnds analysis')
        assert terminal.career.beats_seen == before


class TestTheNote:
    """The finding reaches the player by mail, once."""

    def test_it_comes_when_its_time_has_come(self, terminal):
        _at(terminal, minutes=fraud.MAIL_AFTER)
        assert len(terminal._fraud_events()) == 1

    def test_not_before(self, terminal):
        _at(terminal, minutes=fraud.MAIL_AFTER - 1)
        assert terminal._fraud_events() == []

    def test_only_once(self, terminal):
        _at(terminal)
        assert len(terminal._fraud_events()) == 1
        assert terminal._fraud_events() == []

    def test_it_is_in_the_mail(self, terminal):
        _at(terminal)
        terminal._fraud_events()
        read = terminal.execute_command('mail')
        assert 'Holding times' in read or fraud.GROUP in read

    def test_it_is_remembered_across_a_resume(self, terminal):
        _at(terminal)
        terminal._fraud_events()
        assert fraud.LEDGER in terminal.career.beats_seen

    def test_it_comes_on_a_tour_pass(self, terminal):
        """Through the shift clock and not only by being called."""
        _at(terminal, minutes=fraud.MAIL_AFTER - 5)
        terminal.shift_minutes = fraud.MAIL_AFTER
        got = terminal._case_events()
        assert [m.kind for m in got] == ['fraud']

    def test_not_outside_the_tours(self, terminal):
        _at(terminal, tour=fraud.LAST_TOUR + 1)
        assert terminal._fraud_events() == []


class TestWhatItIsNot:
    """Detection and history. Nothing in it works, and the plot says so."""

    # A tone, a frequency, a dialled code or a way to do it would be an
    # instruction. None of these words has a place in the thread.
    FORBIDDEN = (
        'hz', 'khz', 'tone', '2600', 'whistle', 'blue box', 'box', 'mf ',
        'dial', 'press', 'then ', 'step', 'how to', 'you can', 'you should',
        'pulse', 'sequence', 'seize', 'trunk test', 'phreak',
    )

    def test_no_instruction_or_tone_words(self):
        for tour in range(fraud.FIRST_TOUR, fraud.LAST_TOUR + 1):
            low = _all_the_words(tour).lower()
            found = [word for word in self.FORBIDDEN if word in low]
            assert found == [], (tour, found)

    def test_no_number_that_could_be_dialled_or_keyed(self):
        for tour in range(fraud.FIRST_TOUR, fraud.LAST_TOUR + 1):
            text = _all_the_words(tour)
            # Counts, the group's name and a year are fine; a telephone
            # number or a code is not.
            assert not re.search(r'\d{3}[- ]\d{3,4}', text)
            assert set(re.findall(r'\d{4,}', text)) <= {'0417', '1976'}

    def test_the_plot_is_marked_invented_where_it_is_shown(self):
        assert 'invented' in '\n'.join(fraud.exception_block(9))
        assert 'invented' in '\n'.join(fraud.note(9))

    def test_the_note_asks_nothing_of_the_player(self):
        assert 'not a trouble on any line or trunk' in ' '.join(
            fraud.note(9))

    def test_the_only_date_is_the_sourced_one(self):
        years = set(re.findall(r'\b(1[89]\d\d)\b', _all_the_words()))
        assert years == {'1976'}

    @pytest.mark.parametrize('tour', range(fraud.FIRST_TOUR,
                                           fraud.LAST_TOUR + 1))
    def test_the_counts_say_it_is_not_congestion_and_not_what_it_is(
            self, tour):
        low = _all_the_words(tour).lower()
        assert 'not congestion' in low
        assert 'fraud' in low and 'caught' not in low
