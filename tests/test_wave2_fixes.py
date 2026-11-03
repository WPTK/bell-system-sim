"""
Fixes from the end-of-wave-2 playtest (issues 75 and 76).

A refusal is the same whichever force it names, the overdue notice is said
once across a quit, a night tour is named and stamped as one, and the same
line of chatter does not come round again within a few tours.
"""

import random
import re
from datetime import datetime

from bell_system import npc
from bell_system.clock import SimClock
from bell_system.data import tours
from bell_system.npc import (
    CHATTER_REST_TOURS, Switchroom, chatter_key, halloran_quiet, rested,
)
from bell_system.progression import QUALIFICATIONS
from bell_system.reports import ReportDesk
from bell_system.settings import Settings
from bell_system.terminal import BellSystemTerminal

NOW = datetime(1983, 11, 14, 9, 0)
FORCES = ('Cable repair', 'Outside plant', 'Station', 'Central office')


def _blank(text, force, crew):
    """A refusal with what is the force's own and the clock's taken out."""
    text = text.replace(force.lower(), 'FORCE').replace(crew, 'CREW')
    return re.sub(r'\d+:\d\d', 'T', text)


class TestARefusalIsTheSameForEveryForce:
    """P1: a refused dispatch is not a free crew oracle."""

    def _refusals(self, fault):
        texts = {}
        for force in FORCES:
            desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
            report = desk.receive(datetime(1983, 11, 14), fault=fault)
            for number in ('TR-00001', 'TR-00002', 'TR-00003'):
                desk.force.send(force, number, 600, 0)
            said = desk.dispatch(report, force, 10)
            assert report.dispatched_to is None
            crew = said.split('. ')[1].split(' is on ')[0]
            texts[force] = _blank(said, force, crew).replace(
                report.number, 'TR')
        return texts

    def test_the_right_force_and_a_wrong_one_read_alike(self):
        for fault in ('WET', 'NONE'):
            texts = self._refusals(fault)
            assert len(set(texts.values())) == 1, texts

    def test_the_suffix_that_named_the_wrong_force_is_gone(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        report = desk.receive(datetime(1983, 11, 14), fault='WET')
        for force in FORCES:
            for number in ('TR-00001', 'TR-00002', 'TR-00003'):
                desk.force.send(force, number, 600, 0)
            said = desk.dispatch(report, force, 10)
            assert 'just as well' not in said and 'not theirs' not in said

    def test_both_are_charged_the_same_desk_time(self):
        spent = []
        for force in ('Cable repair', 'Station'):
            desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
            report = desk.receive(datetime(1983, 11, 14), fault='WET')
            for number in ('TR-00001', 'TR-00002', 'TR-00003'):
                desk.force.send(force, number, 600, 0)
            before = report.minutes_spent
            desk.dispatch(report, force, 10)
            spent.append(report.minutes_spent - before)
        assert spent[0] == spent[1] > 0


class TestTheOverdueNoticeIsSaid:
    """Once, and it stays said across a quit and a resume."""

    def _terminal(self):
        terminal = BellSystemTerminal()
        terminal.settings.set('game.prompts', 'off')
        terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
        terminal.career.shift = 3
        terminal.career.save()
        terminal.start_tour_clock()
        terminal.select_role(1)
        terminal.emit = lambda *a, **k: None
        return terminal

    def test_a_resume_does_not_say_it_again(self):
        first = self._terminal()
        said = first.execute_command('sleep 100000')
        assert 'has gone' in said
        late = [r.number for r in first.desk.pending() if r.overdue()]
        assert late
        first.save_shift()

        second = BellSystemTerminal()
        second.settings.set('game.prompts', 'off')
        second.select_role(1)
        second.emit = lambda *a, **k: None
        for number in late:
            assert f'chased:{number}' in second.career.beats_seen
        # The board is dealt again and its reports flag as late once more;
        # missed is counted again but she does not say it again.
        board = [r for r in second.desk.pending() if r.number in late]
        assert board
        missed = second.career.missed_commitments
        assert second._report_late(board) == []
        assert second.career.missed_commitments == missed + len(board)

    def test_there_is_one_way_of_saying_it(self):
        room = Switchroom(random.Random(1))
        from bell_system.data.consequences import Late
        for out in (True, False):
            late = Late('TR-00001', '201-555-0100', '1FR', out, '08:30')
            lines = room.overdue_notice(NOW, 'TR-00001', late).lines
            assert len(lines) == 2
            assert 'was due 08:30 and has gone' in lines[0]
            assert not any('past its commitment' in line for line in lines)


class TestTheWatchIsNamedAndStamped:
    """A night tour starts at midnight and an evening one at four."""

    def test_the_clock_opens_on_the_watch(self):
        settings = Settings()
        clock = SimClock(settings)
        for tour, hour in ((1, 8), (3, 16), (4, 0)):
            clock.set_tour(tour, tours.start_hour(tour))
            assert clock.now().hour == hour
            assert clock.tour_day() == settings.epoch().date().replace(
                day=settings.epoch().date().day + (tour - 1) * 4)

    def test_every_tour_start_hour_is_its_watchs(self):
        for entry in tours.TOURS:
            assert tours.start_hour(entry.number) == \
                tours.WATCH_START_HOUR[entry.watch]

    def test_the_briefing_names_the_watch_and_shows_its_hour(self, terminal):
        for tour, label, hour in ((3, 'Evening Shift', '16:'),
                                  (4, 'Night Shift', '00:'),
                                  (2, 'Day Shift', '08:')):
            terminal.career.shift = tour
            terminal.start_tour_clock()
            lines = []
            terminal.emit = lambda text='', lines=lines: lines.append(text)
            terminal.role = 'sysop'
            terminal.show_shift_briefing()
            text = '\n'.join(lines)
            assert f'Watch: {label}' in text
            assert f'Shift Start Time: {hour}' in text

    def test_message_stamps_follow_the_watch(self, terminal):
        terminal.career.shift = 4
        terminal.start_tour_clock()
        assert terminal._stamp().startswith('00:')

    def test_events_are_timed_on_the_watch_too(self, terminal):
        for tour in (3, 4):
            terminal.career.shift = tour
            terminal.start_tour_clock()
            terminal.generate_shift_events()
            low = tours.WATCH_START_HOUR[tours.watch_of(tour)]
            for event in terminal.shift_events:
                hour = int(event['time'][:2])
                assert low <= hour < low + 8, (tour, event['time'])

    def test_no_chatter_names_a_time_of_day_it_cannot_know(self):
        pools = list(npc._CHATTER)
        for position in npc._POSITION_CHATTER.values():
            pools.extend(position)
        for item in pools:
            text = ' '.join(item[2])
            for word in ('morning', 'afternoon', 'evening', 'tonight'):
                assert word not in text, text
            if '11/14' in text:  # a dated log line, in the past
                continue
            assert not re.search(r'\b0[0-9]:[0-5][0-9]\b', text), text


class TestChatterDoesNotComeRoundAgain:
    def test_a_line_said_is_rested_for_three_tours(self):
        lines = ['Frame is warm again in aisle four.']
        seen = [chatter_key(4, lines)]
        for tour in range(4, 4 + CHATTER_REST_TOURS + 1):
            assert not rested(lines, tour, seen), tour
        assert rested(lines, 4 + CHATTER_REST_TOURS + 1, seen)
        assert rested(['another line'], 4, seen)

    def test_the_room_offers_nothing_the_ledger_says_was_said(self):
        room = Switchroom(random.Random(3))
        ledger = []
        for tour in (5, 6, 7, 8):
            for _ in range(3):
                message = room.chatter(NOW, position='sysop', tour=tour,
                                       seen=ledger)
                if message is None:
                    continue
                ledger.append(chatter_key(tour, message.lines))
            # Nothing offered on this tour was said on an earlier one within
            # the rest.
        for tour in (5, 6, 7, 8):
            keys = [e for e in ledger if e.startswith(f'said:{tour}:')]
            for key in keys:
                tail = key.split(':')[2]
                earlier = [e for e in ledger
                           if e.endswith(tail)
                           and 0 < tour - int(e.split(':')[1])
                           <= CHATTER_REST_TOURS]
                assert not earlier, key

    def test_a_busy_desk_is_never_silent_while_it_has_lines(self):
        """Craft hears more; across four tours the rest must not run it dry."""
        room = Switchroom(random.Random(5))
        ledger = []
        for tour in (5, 6, 7, 8):
            for _ in range(60):
                room._recent.clear()
                message = room.chatter(NOW, position='sysop', tour=tour,
                                       seen=ledger)
                assert message is not None, tour
                ledger.append(chatter_key(tour, message.lines))

    def test_the_line_said_longest_ago_is_the_one_that_comes_back(self):
        room = Switchroom(random.Random(5))
        pool = [item for item in npc._CHATTER if len(item) < 4
                and item[1] in ('rjohnson', 'gvasquez', 'lokafor', 'dpetrak',
                                'tnakamura', 'carot', 'mreyes')]
        ledger = [chatter_key(5 + (i % 2), item[2])
                  for i, item in enumerate(pool)]
        oldest = tuple(item for i, item in enumerate(pool) if i % 2 == 0)
        found = room._longest_ago(tuple(pool), ledger)
        assert [item[2] for item in found] == [item[2] for item in oldest]

    def test_the_ledger_is_in_the_career_save(self, terminal):
        terminal.career.shift = 5
        terminal.settings.set('game.ambience', 'on')
        terminal.career.set_difficulty('craft')
        terminal.switchroom.rng = random.Random(1)
        for _ in range(60):
            terminal._craft_interruption(terminal._difficulty())
        saved = terminal.career.beats_seen
        assert any(entry.startswith('said:5:') for entry in saved)
        reread = type(terminal.career)(terminal.career.path)
        assert reread.beats_seen == saved

    def test_he_says_less_as_the_end_nears(self):
        assert halloran_quiet(1) == halloran_quiet(8) == 0
        assert 0 < halloran_quiet(10) < halloran_quiet(13) < 1

    def test_halloran_chatter_thins_in_the_last_tours(self):
        def count(tour):
            room = Switchroom(random.Random(11))
            total = 0
            for _ in range(400):
                message = room.chatter(NOW, position='sysop', tour=tour)
                room._recent.clear()
                if message and message.sender == 'ehalloran':
                    total += 1
            return total
        assert count(13) < count(5) * 0.6


class TestTheDebriefAndTheTutorialSayWhatIsTrue:
    def test_the_measure_step_names_no_crew_on_craft(self, raw_terminal):
        raw_terminal.career.set_difficulty('craft')
        raw_terminal.career.shift = 1
        raw_terminal.career.reports_closed = 0
        raw_terminal._tour_nudges.clear()
        nudge = raw_terminal.first_tour_nudge('measure')
        assert 'names a crew' not in nudge
        assert "report faults" in nudge

    def test_the_measure_step_names_a_crew_on_fun(self, raw_terminal):
        raw_terminal.career.set_difficulty('fun')
        raw_terminal.career.shift = 1
        raw_terminal.career.reports_closed = 0
        raw_terminal._tour_nudges.clear()
        assert 'names a crew' in raw_terminal.first_tour_nudge('measure')

    def test_the_mlt_lecture_only_follows_an_unmeasured_close(self, terminal):
        measured = ' '.join(terminal.tour_summary(
            closed=6, correct=2, missed=0, repeats=0, unmeasured=0))
        unmeasured = ' '.join(terminal.tour_summary(
            closed=6, correct=2, missed=0, repeats=0, unmeasured=1))
        assert 'Four minutes of mlt' not in measured
        assert 'Four minutes of mlt' in unmeasured
        assert "'report faults'" in measured

    def _handoff_after(self, terminal, measured):
        terminal.settings.set('game.ambience', 'off')
        terminal.career.record_closure(False, measured=measured)
        terminal.career.record_closure(True, measured=measured)
        return terminal.execute_command('handoff relieve')

    def test_a_tour_of_measured_closes_gets_no_lecture(self, terminal):
        said = self._handoff_after(terminal, measured=True)
        assert 'named a condition the line did not have' in said
        assert 'Four minutes of mlt' not in said

    def test_a_tour_with_an_unmeasured_close_does(self, terminal):
        said = self._handoff_after(terminal, measured=False)
        assert 'named a condition the line did not have' in said
        assert 'Four minutes of mlt' in said
