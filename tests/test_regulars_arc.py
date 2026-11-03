"""
The four lines you keep coming back to have a year to get through.

C16: each regular has beats on named tours, the card says the latest one,
and every one of them is resolved or abandoned before the last tour. The
card may say what happened to a line. It may not say what the next report
off it will turn out to be: that stays in the readings.
"""

import json
import random
import re

import pytest

from bell_system import save
from bell_system.clock import TOURS_TO_DIVESTITURE
from bell_system.data.regulars import (
    ABANDONED,
    OPEN,
    REGULARS,
    RESOLVED,
    faults_at,
    note_at,
    reporting_at,
    status_at,
)
from bell_system.data.trouble import FAULTS
from bell_system.progression import Career
from bell_system.reports import ReportDesk

TOURS = range(1, TOURS_TO_DIVESTITURE + 1)

# W16: after the opening card, a beat is paperwork and people. It names no
# diagnosis, force or close code, and none of the symptoms or conditions a
# report is drawn from (water, weather, the handset), because those would say
# what the next report will be. Whole words and stems, so "ground" is caught
# and "background" is not.
NAMING = re.compile(
    r"\b(open|short|ground|cross|wet|emf|off hook|central office|"
    r"outside plant|cable repair|station|disposition|no trouble found|"
    r"fcg|femf|roh|co_equip|none|weather|water\w*|rain\w*|pump\w*|"
    r"hook\w*|handset|hang\w*|storm\w*|sheath)\b", re.IGNORECASE)


def draw(terminal, tour, count=400):
    terminal.career.shift = tour
    for _ in range(count):
        terminal.desk.receive(terminal.clock.now(), 0)
    return list(terminal.desk.reports.values())


class TestTheTable:
    """Every regular has an arc, and every arc ends."""

    @pytest.mark.parametrize('key', sorted(REGULARS))
    def test_beats_are_on_named_tours_in_order(self, key):
        tours = [beat.tour for beat in REGULARS[key].arc]
        assert len(tours) >= 3
        assert tours == sorted(set(tours))
        assert all(2 <= tour <= TOURS_TO_DIVESTITURE for tour in tours)

    @pytest.mark.parametrize('key', sorted(REGULARS))
    def test_only_the_last_beat_ends_it(self, key):
        arc = REGULARS[key].arc
        assert [beat.ends for beat in arc[:-1]] == [OPEN] * (len(arc) - 1)
        assert arc[-1].ends in (RESOLVED, ABANDONED)

    def test_all_four_end_resolved_or_abandoned_by_tour_13(self):
        for key, regular in REGULARS.items():
            assert status_at(regular, TOURS_TO_DIVESTITURE) in (
                RESOLVED, ABANDONED), key
        assert reporting_at(TOURS_TO_DIVESTITURE) == ()

    def test_they_do_not_all_end_on_the_same_tour(self):
        ends = {regular.arc[-1].tour for regular in REGULARS.values()}
        assert len(ends) == len(REGULARS)

    def test_an_ended_line_stays_ended(self):
        for regular in REGULARS.values():
            states = [status_at(regular, tour) for tour in TOURS]
            first = next(i for i, s in enumerate(states) if s != OPEN)
            assert all(state == states[first] for state in states[first:])

    def test_both_endings_are_used(self):
        endings = {regular.arc[-1].ends for regular in REGULARS.values()}
        assert endings == {RESOLVED, ABANDONED}

    def test_every_regular_starts_with_its_opening_card(self):
        for regular in REGULARS.values():
            assert note_at(regular, 1) == regular.note
            assert faults_at(regular, 1) == regular.faults

    def test_the_card_changes_on_the_beat_and_not_before(self):
        for regular in REGULARS.values():
            for beat in regular.arc:
                assert note_at(regular, beat.tour) == beat.note
                assert note_at(regular, beat.tour - 1) != beat.note

    def test_a_changed_fault_mix_names_faults_that_exist(self):
        for regular in REGULARS.values():
            for beat in regular.arc:
                for code, weight in beat.faults or ():
                    assert code in FAULTS and weight > 0

    @pytest.mark.parametrize('key', sorted(REGULARS))
    def test_a_beat_never_names_what_a_report_turns_out_to_be(self, key):
        """Pillar 1: the card is the history of a line, not a reading."""
        for beat in REGULARS[key].arc:
            assert not NAMING.search(beat.note), beat.note

    def test_a_beat_fits_a_line_of_the_card(self):
        for regular in REGULARS.values():
            for beat in regular.arc:
                assert all(len(word) < 58 for word in beat.note.split())


class TestTheDesk:
    """Lines that have ended stop reporting, and the others carry on."""

    def test_a_line_stops_reporting_when_it_ends(self, terminal):
        seen = {r.record.regular for r in draw(terminal, 8)}
        assert 'ferrante' not in seen
        assert seen >= {'kowalczyk', 'whitcomb', 'duchesne'}

    def test_nobody_reports_after_the_last_one_ends(self, terminal):
        reports = draw(terminal, TOURS_TO_DIVESTITURE)
        assert not any(report.record.regular for report in reports)

    def test_what_a_line_is_like_to_work_follows_its_beat(self):
        kowalczyk, duchesne = REGULARS['kowalczyk'], REGULARS['duchesne']
        assert faults_at(kowalczyk, 6) == kowalczyk.faults
        assert faults_at(kowalczyk, 7) != kowalczyk.faults
        assert faults_at(kowalczyk, 11) == faults_at(kowalczyk, 7)
        assert faults_at(duchesne, 7) == duchesne.faults
        assert faults_at(duchesne, 8) != duchesne.faults

    def test_the_desk_draws_from_the_mix_for_the_tour(self, terminal):
        """Duchesne at tour 8 is drawn with no fault the beat dropped."""
        terminal.desk.tour_of = lambda: 8
        reports = [terminal.desk.receive(terminal.clock.now(), 0)
                   for _ in range(600)]
        allowed = {code for code, _ in faults_at(REGULARS['duchesne'], 8)}
        faults = {r.record.fault for r in reports
                  if r.record.regular == 'duchesne'}
        assert faults and faults <= allowed

    def test_the_tour_is_read_when_a_report_comes_in(self, terminal):
        """The desk outlives a handoff, so it must not cache the tour."""
        terminal.career.shift = 2
        assert 'ferrante' in {r.record.regular for r in draw(terminal, 2)}
        terminal.career.shift = 9
        fresh = [terminal.desk.receive(terminal.clock.now(), 0)
                 for _ in range(300)]
        assert 'ferrante' not in {r.record.regular for r in fresh}

    def test_the_share_does_not_pile_onto_whoever_is_left(self, terminal):
        terminal.career.shift = 9
        terminal.desk.tour_of = lambda: 9
        reports = [terminal.desk.receive(terminal.clock.now(), 0)
                   for _ in range(1000)]
        share = sum(1 for r in reports if r.record.regular) / len(reports)
        # Two of four are live. Eighteen per cent was for four.
        assert share < 0.13


class TestTheSameLineEveryTour:
    """A desk is built fresh each session, and the line has to be the same."""

    def lines(self, seed, clli='NWRKNJ02'):
        desk = ReportDesk('201', '555', clli, rng=random.Random(seed))
        return {key: desk.regular_record(key) for key in REGULARS}

    def test_another_session_has_the_same_number_cable_and_pair(self):
        a, b = self.lines(1), self.lines(2)
        for key in REGULARS:
            assert a[key].telephone_number == b[key].telephone_number
            assert a[key].cable_pair() == b[key].cable_pair()
            assert a[key].line_equipment == b[key].line_equipment

    def test_the_four_are_four_different_lines(self):
        numbers = {r.telephone_number for r in self.lines(1).values()}
        assert len(numbers) == len(REGULARS)

    def test_another_office_is_another_set_of_numbers(self):
        a, b = self.lines(1), self.lines(1, clli='JRCYNJ01')
        assert [r.telephone_number for r in a.values()] != [
            r.telephone_number for r in b.values()]

    def test_looking_one_up_leaves_nothing_behind(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', rng=random.Random(1))
        desk.regular_record('whitcomb')
        assert desk._regulars == {}

    def test_water_is_in_the_sheath_the_line_is_on(self, terminal):
        reports = draw(terminal, 2)
        wet = next(r for r in reports if r.record.regular == 'kowalczyk'
                   and r.record.fault == 'WET')
        assert terminal.desk.plant.section_at(
            wet.record.cable, wet.record.pair) is not None

    def test_one_splicer_trip_clears_every_report_on_the_pair(self, terminal):
        """Two reports from one line on one pair are one sheath."""
        desk = terminal.desk
        now = terminal.clock.now()
        line = desk.regular_record('kowalczyk')
        desk.plant.wet_over(line.cable, line.pair, now)
        first = desk.receive(now, 0, fault='WET', record=line)
        second = desk.receive(now, 0, fault='WET',
                              record=desk.regular_record('kowalczyk'))
        assert (first.record.cable, first.record.pair) == (
            second.record.cable, second.record.pair)
        assert desk.plant.section_at(
            first.record.cable, first.record.pair) is not None
        # The section remembers only the later report on the pair.
        message = desk._repair_sheath(second, 'Outside plant', 30)
        assert first.number in message
        assert first.sheath_repaired
        assert desk.plant.section_at(
            first.record.cable, first.record.pair) is None

    def test_a_shift_saved_with_its_own_lines_picks_them_back_up(
            self, terminal):
        """A save from before the lines were fixed still loads."""
        terminal.desk._regulars['whitcomb'] = terminal.desk.regular_record(
            'whitcomb')
        stored = json.loads(json.dumps(save.capture(terminal)))
        assert 'whitcomb' in stored['board']['regulars']
        stored['board']['regulars']['whitcomb']['line'] = '7777'
        assert save.restore(terminal, stored)
        assert terminal.desk.regular_record('whitcomb').line == '7777'


class TestTheCard:
    """custdb says the latest thing the bureau knows."""

    def number(self, terminal, key):
        return terminal.desk.regular_record(key).telephone_number

    def test_it_says_the_note_for_this_tour(self, terminal):
        draw(terminal, 7)
        card = terminal.execute_command(
            f"custdb {self.number(terminal, 'kowalczyk')}")
        assert 'before the holidays' in card
        assert 'Sheath is in water' not in card

    def test_it_says_the_opening_note_before_the_first_beat(self, terminal):
        draw(terminal, 2)
        card = terminal.execute_command(
            f"custdb {self.number(terminal, 'whitcomb')}")
        assert 'bus route' in card

    def test_a_resolved_line_says_so_on_its_card(self, terminal):
        terminal.career.regular_closed['kowalczyk'] = 3
        terminal.career.shift = 11
        card = terminal.execute_command(
            f"custdb {self.number(terminal, 'kowalczyk')}")
        assert 'RESOLVED' in card
        assert 'New cable in' in card

    def test_an_abandoned_line_says_so_on_its_card(self, terminal):
        terminal.career.shift = 5
        draw(terminal, 5, count=0)
        terminal.career.regular_closed['ferrante'] = 1
        terminal.career.shift = 8
        card = terminal.execute_command(
            f"custdb {self.number(terminal, 'ferrante')}")
        assert 'ABANDONED' in card
        assert 'Coin telephone pulled' in card

    def test_a_line_that_has_gone_quiet_is_still_in_the_file(self, terminal):
        terminal.career.regular_closed['ferrante'] = 2
        terminal.career.shift = 9
        index = terminal.execute_command('custdb')
        assert '(abandoned)' in index
        assert self.number(terminal, 'ferrante') in index
        card = terminal.execute_command(
            f"custdb {self.number(terminal, 'ferrante')}")
        assert 'Closed by you   2' in card
        assert 'Reports' not in card and 'Repeats' not in card

    def test_a_line_you_have_not_met_is_not_handed_to_you(self, terminal):
        terminal.career.shift = 9
        number = self.number(terminal, 'ferrante')
        assert number not in terminal.execute_command('custdb')
        assert 'no record' in terminal.execute_command(f'custdb {number}')

    def test_looking_is_read_only(self, terminal):
        draw(terminal, 9, count=50)
        terminal.career.regular_closed['ferrante'] = 1
        number = self.number(terminal, 'ferrante')

        def held():
            return (dict(terminal.desk._regulars),
                    dict(terminal.career.regular_closed),
                    sorted(terminal.desk.reports),
                    len(terminal.desk.plant.sections))

        before = held()
        terminal.execute_command('custdb')
        terminal.execute_command(f'custdb {number}')
        assert held() == before

    def test_a_report_points_at_the_card(self, terminal):
        reports = draw(terminal, 2)
        report = next(r for r in reports if r.record.regular)
        shown = terminal.execute_command(f'report show {report.number}')
        assert f'custdb {report.record.telephone_number}' in shown
        plain = next(r for r in reports if not r.record.regular)
        assert 'Known line' not in terminal.execute_command(
            f'report show {plain.number}')


class TestWhatTheCareerKeeps:
    """One count per regular, saved with the career."""

    def test_closing_a_regular_counts_it(self, terminal):
        reports = draw(terminal, 2)
        report = next(r for r in reports if r.record.regular == 'whitcomb')
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report close {report.number} 8')
        assert terminal.career.regular_closed == {'whitcomb': 1}

    def test_closing_a_stranger_does_not(self, terminal):
        reports = draw(terminal, 2)
        report = next(r for r in reports if not r.record.regular)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report close {report.number} 8')
        assert terminal.career.regular_closed == {}

    def test_it_survives_a_restart(self, tmp_path):
        path = str(tmp_path / 'career.json')
        career = Career(path)
        career.record_closure(True, regular='duchesne')
        career.record_closure(True, regular='duchesne')
        again = Career(path)
        again.load()
        assert again.regular_closed == {'duchesne': 2}

    def test_a_career_from_before_it_loads_without_it(self, tmp_path):
        path = tmp_path / 'career.json'
        path.write_text(json.dumps({'schema': 3, 'shift': 4}))
        career = Career(str(path))
        career.load()
        assert career.shift == 4
        assert career.regular_closed == {}

    def test_a_damaged_count_costs_only_itself(self, tmp_path):
        path = tmp_path / 'career.json'
        path.write_text(json.dumps(
            {'shift': 4, 'regular_closed': {'whitcomb': 'many', 'x': -1}}))
        career = Career(str(path))
        career.load()
        assert career.shift == 4
        assert 'whitcomb' not in career.regular_closed
