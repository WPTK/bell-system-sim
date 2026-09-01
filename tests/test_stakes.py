"""
The divestiture, and the people who notice you.

The Bell System dissolves on 1 January 1984 and that is the emotional
centre of the whole simulation. It used to be a memo in /usr/doc that a
player had to know to open. These cover it being where it will be seen,
and the three other things that make a career feel like it happened to
somebody: a wire chief who has been watching, four lines you have been out
to before, and a last day.
"""

from datetime import datetime

import pytest

from bell_system.clock import (
    DAYS_PER_TOUR,
    DIVESTITURE,
    TOURS_TO_DIVESTITURE,
    SimClock,
    days_to_divestiture,
)
from bell_system.data.regulars import REGULARS, REGULAR_SHARE
from bell_system.npc import Switchroom


class TestTheCountdown:
    """Forty-eight days, computed rather than written down."""

    def test_the_opening_shift_is_forty_eight_days_out(self):
        assert days_to_divestiture(datetime(1983, 11, 14)) == 48

    def test_it_reaches_zero_on_the_day(self):
        assert days_to_divestiture(DIVESTITURE) == 0

    def test_it_goes_negative_afterwards(self):
        """A state the simulation can reach and should not lie about."""
        assert days_to_divestiture(datetime(1984, 1, 5)) == -4

    def test_the_login_banner_carries_it(self, raw_terminal):
        assert '48 days to divestiture' in '\n'.join(
            raw_terminal._getty_banner())

    def test_the_banner_follows_the_epoch(self, raw_terminal):
        raw_terminal.settings.set('date.epoch', '1983-12-30')
        raw_terminal.clock.reset_session()
        raw_terminal.clock.set_tour(1)
        assert '2 days to divestiture' in '\n'.join(
            raw_terminal._getty_banner())

    @pytest.mark.parametrize('epoch,expected', [
        ('1983-12-31', 'is tomorrow'),
        ('1984-01-01', 'is today'),
        ('1984-01-03', 'was 2 days ago'),
    ])
    def test_the_banner_says_the_right_thing_at_the_end(
            self, raw_terminal, epoch, expected):
        raw_terminal.settings.set('date.epoch', epoch)
        raw_terminal.clock.reset_session()
        raw_terminal.clock.set_tour(1)
        assert expected in raw_terminal._divestiture_line()

    def test_the_handoff_record_carries_it(self, terminal):
        assert 'days to divestiture' in terminal.execute_command('handoff')


class TestTheCalendar:
    """A career walks from 14 November to the last day of the company."""

    def clock_at(self, settings, tour):
        clock = SimClock(settings)
        clock.set_tour(tour)
        return clock

    def test_the_first_tour_is_the_epoch(self, terminal):
        assert self.clock_at(terminal.settings, 1).now().date() == \
            terminal.settings.epoch().date()

    def test_tours_are_four_days_apart(self, terminal):
        first = self.clock_at(terminal.settings, 1).now().date()
        second = self.clock_at(terminal.settings, 2).now().date()
        assert (second - first).days == DAYS_PER_TOUR

    def test_the_last_tour_is_the_last_day_of_the_bell_system(self, terminal):
        clock = self.clock_at(terminal.settings, TOURS_TO_DIVESTITURE)
        assert clock.now().date() == datetime(1983, 12, 31).date()

    def test_there_is_no_tour_after_the_last_one(self, terminal):
        """There is no Bell System to work a fourteenth tour in."""
        last = self.clock_at(terminal.settings, TOURS_TO_DIVESTITURE)
        beyond = self.clock_at(terminal.settings, TOURS_TO_DIVESTITURE + 9)
        assert beyond.now().date() == last.now().date()

    def test_the_countdown_actually_moves(self, terminal):
        """A countdown that never moves is not a countdown."""
        seen = {days_to_divestiture(self.clock_at(terminal.settings, n).now())
                for n in range(1, TOURS_TO_DIVESTITURE + 1)}
        assert len(seen) == TOURS_TO_DIVESTITURE

    def test_signing_off_a_shift_moves_the_day(self, terminal):
        before = terminal.clock.now().date()
        terminal.execute_command('handoff relieve')
        assert terminal.clock.now().date() > before

    def test_the_last_tour_says_so(self, terminal):
        terminal.career.shift = TOURS_TO_DIVESTITURE - 1
        assert 'last working day of the Bell System' in \
            terminal.execute_command('handoff relieve')

    def test_an_ordinary_tour_does_not(self, terminal):
        terminal.career.shift = 2
        assert 'last working day' not in \
            terminal.execute_command('handoff relieve')


class TestTheWireChief:
    """He signs every sign-off, so a fixed line makes him a form letter."""

    def notice(self, held, days_left=48):
        return ' '.join(Switchroom().qualification_notice(
            datetime(1983, 11, 14), 'Main Distributing Frame',
            ['cosmos', 'lmos'], held=held, days_left=days_left).lines)

    def test_the_first_is_business(self):
        assert 'not signed off on' in self.notice(1)

    def test_he_notices_the_third(self):
        assert 'I do not sign three' in self.notice(3)

    def test_every_one_of_them_reads_differently(self):
        assert len({self.notice(n) for n in range(1, 6)}) == 5

    def test_a_sixth_falls_back_rather_than_inventing(self):
        """He is not effusive, and there is nothing further to say."""
        assert self.notice(6) == self.notice(1)

    def test_close_to_the_end_he_says_what_it_is_worth(self):
        assert 'days left of the company' in self.notice(3, days_left=5)

    def test_early_on_he_does_not(self):
        assert 'days left of the company' not in self.notice(3, days_left=48)


class TestTheRegulars:
    """Four lines the bureau knows by heart."""

    def draw(self, terminal, count=400):
        for _ in range(count):
            terminal.desk.receive(terminal.clock.now(), 0)
        return terminal.desk.reports.values()

    def test_every_regular_declares_a_fault_that_exists(self):
        from bell_system.data.trouble import FAULTS
        for regular in REGULARS.values():
            for code, weight in regular.faults:
                assert code in FAULTS, f'{regular.key} wants {code}'
                assert weight > 0

    def test_they_turn_up(self, terminal):
        seen = {report.record.regular for report in self.draw(terminal)}
        assert seen >= set(REGULARS)

    def test_a_regular_is_always_the_same_line(self, terminal):
        """The point of a regular is that it is the same line."""
        numbers = {}
        for report in self.draw(terminal):
            key = report.record.regular
            if key:
                numbers.setdefault(key, set()).add(
                    report.record.telephone_number)
        assert all(len(seen) == 1 for seen in numbers.values())

    def test_the_history_piles_up_on_one_card(self, terminal):
        self.draw(terminal)
        cards = terminal.lmos_console.lmos.line_cards()
        known = [card for card in cards.values() if card.record.regular]
        assert any(card.report_count > 1 for card in known)

    def test_their_trouble_varies(self, terminal):
        """A chronic line is not chronic in one way only."""
        faults = {}
        for report in self.draw(terminal):
            key = report.record.regular
            if key:
                faults.setdefault(key, set()).add(report.record.fault)
        assert any(len(seen) > 1 for seen in faults.values())

    def test_the_line_card_says_you_have_been_here_before(self, terminal):
        self.draw(terminal)
        number = next(report.record.telephone_number
                      for report in self.draw(terminal, count=0)
                      if report.record.regular == 'whitcomb')
        card = terminal.execute_command(f'custdb {number}')
        assert 'Known since' in card
        assert 'bus route' in card

    def test_the_index_marks_them(self, terminal):
        self.draw(terminal)
        assert '(known)' in terminal.execute_command('custdb')

    def test_most_reports_are_still_strangers(self, terminal):
        """A bureau is not four customers."""
        reports = list(self.draw(terminal))
        known = sum(1 for report in reports if report.record.regular)
        assert known / len(reports) < REGULAR_SHARE * 2
