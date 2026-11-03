"""
The tour ledger places a tour against simulated peers (A14).

The tour's counts are set on the career directly and the peers are the
table's, so no test depends on how a board happens to be dealt.
"""

import re
from types import SimpleNamespace

import pytest

from bell_system import ledger
from bell_system.data import peers
from bell_system.data.peers import PEERS
from bell_system.progression import DIFFICULTIES


@pytest.fixture
def played(monkeypatch):
    """The peers as they are once tools/index_calibration.py has made them."""
    monkeypatch.setattr(peers, 'GENERATED', True)


def tour(terminal, closed=10, wrong=1, repairs=9, minutes=100, difficulty='craft'):
    """Give the career a tour with these counts, from nothing."""
    career = terminal.career
    career.set_difficulty(difficulty)
    career.tour_mark = {}
    career.reports_closed = closed
    career.reports_wrong = wrong
    career.kpi = {'repairs': repairs, 'repair_minutes': repairs * minutes}
    return career


def written(lines):
    return '\n'.join(lines)


class TestThePeers:
    def test_every_difficulty_has_ten_ordered_peers_on_both_measures(self):
        for key in DIFFICULTIES:
            for measure in ('mttr', 'accuracy'):
                ranked = PEERS[key][measure]
                assert len(ranked) == ledger.PEER_COUNT, (key, measure)
                assert list(ranked) == sorted(ranked), (key, measure)

    def test_accuracy_is_a_percentage(self):
        for table in PEERS.values():
            assert all(0 <= value <= 100 for value in table['accuracy'])


class TestPlacing:
    peers = (60.0, 75.0, 90.0, 105.0, 120.0, 135.0, 150.0, 170.0, 195.0, 230.0)

    def test_a_lower_figure_beats_the_peers_above_it(self):
        assert ledger.place_lower(100.0, self.peers) == 7
        assert ledger.place_lower(50.0, self.peers) == 10
        assert ledger.place_lower(300.0, self.peers) == 0

    def test_a_higher_figure_matches_or_beats_the_peers_below_it(self):
        assert ledger.place_higher(100.0, self.peers) == 3
        assert ledger.place_higher(300.0, self.peers) == 10
        assert ledger.place_higher(10.0, self.peers) == 0

    def test_a_time_that_ties_beats_nobody(self):
        assert ledger.place_lower(90.0, self.peers) == 7

    def test_an_accuracy_that_ties_counts_as_matched(self):
        assert ledger.place_higher(90.0, self.peers) == 3

    def test_a_perfect_tour_places_ten_of_ten(self):
        peers_at_the_top = (100.0,) * 3 + (90.0,) * 7
        assert ledger.place_higher(100.0, peers_at_the_top) == 10

    def test_nothing_measured_places_nothing(self):
        assert ledger.place_lower(None, self.peers) is None
        assert ledger.place_higher(None, self.peers) is None

    def test_accuracy_is_the_share_of_closes_that_matched(self):
        assert ledger.accuracy_of({'closed': 10, 'wrong': 1}) == 90.0
        assert ledger.accuracy_of({'closed': 0, 'wrong': 0}) is None


@pytest.mark.usefixtures('played')
class TestTheLedger:
    def test_it_places_both_figures_and_says_the_peers_are_simulated(
            self, terminal):
        text = written(ledger.lines(tour(terminal)))
        assert text.startswith('TOUR LEDGER')
        assert re.search(r'quicker than \d+ of 10', text)
        assert re.search(
            r'Closes matched the line +\d+%   as often as or more often '
            r'than \d+ of 10', text)
        assert 'simulation' in text and 'Not scored' in text

    def test_too_few_closes_places_nothing(self, terminal):
        text = written(ledger.lines(tour(terminal, closed=3, wrong=0)))
        assert 'Too few closes' in text
        assert 'quicker than' not in text and 'as often as' not in text

    def test_a_tour_of_no_repairs_places_only_the_accuracy(self, terminal):
        text = written(ledger.lines(tour(terminal, repairs=0, minutes=0)))
        assert 'quicker than' not in text
        assert 'as often as or more often than' in text

    def test_each_difficulty_is_placed_against_its_own_peers(self, terminal):
        for key in DIFFICULTIES:
            text = written(ledger.lines(tour(terminal, difficulty=key)))
            assert DIFFICULTIES[key].name in text

    def test_a_perfect_tour_reads_ten_of_ten(self, terminal):
        text = written(ledger.lines(tour(terminal, wrong=0)))
        assert '100%   as often as or more often than 10 of 10' in text

    def test_assists_in_force_place_nothing_and_say_so(self, terminal):
        career = tour(terminal)
        career.set_assists({'annotation_sightings': 99})
        assert career.assisted
        assert ledger.lines(career) == [
            'TOUR LEDGER - not placed: assists in force']

    def test_it_is_aggregates_only(self, terminal):
        """Pillar 1: nothing in it can be read as an answer to a report."""
        text = written(ledger.lines(tour(terminal)))
        assert not re.search(r'TR-\d|\d{3}-\d{3}-\d{4}', text)
        for word in ('fault', 'open', 'short', 'ground', 'cross', 'code'):
            assert word not in text.lower(), word


class TestHeldBack:
    def test_nothing_is_printed_while_the_peers_are_placeholders(
            self, terminal, monkeypatch):
        monkeypatch.setattr(peers, 'GENERATED', False)
        assert ledger.lines(tour(terminal)) == []
        assert 'TOUR LEDGER' not in terminal.execute_command('handoff')

    def test_signing_off_prints_nothing_while_they_are_placeholders(
            self, terminal, monkeypatch):
        monkeypatch.setattr(peers, 'GENERATED', False)
        tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'TOUR CREDIT' in out
        assert 'TOUR LEDGER' not in out

    def test_a_difficulty_missing_from_the_table_prints_nothing(
            self, terminal, monkeypatch):
        monkeypatch.setattr(peers, 'GENERATED', True)
        monkeypatch.setattr(peers, 'PEERS', {})
        assert ledger.lines(tour(terminal)) == []
        terminal.execute_command('report')
        assert 'TOUR LEDGER' not in terminal.execute_command(
            'handoff relieve')


@pytest.mark.usefixtures('played')
class TestOnTheScreen:
    def test_a_mid_tour_handoff_does_not_show_it(self, terminal):
        tour(terminal)
        assert 'TOUR LEDGER' not in terminal.execute_command('handoff')

    def test_signing_off_shows_the_tour_that_was_worked(self, terminal):
        tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'TOUR LEDGER' in out
        assert out.index('TOUR CREDIT') < out.index('TOUR LEDGER')

    def test_a_tour_with_nothing_in_it_still_signs_off(self, terminal):
        tour(terminal, closed=0, wrong=0, repairs=0, minutes=0)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'Too few closes' in out


@pytest.mark.usefixtures('played')
def test_a_ledger_never_raises_on_an_unknown_difficulty():
    stranger = SimpleNamespace(difficulty=SimpleNamespace(key='nonesuch'))
    assert ledger.lines(stranger) == []
