"""
The other craft: what they say, in what order, and on which tours.

Nothing here depends on chance. Where the building picks at random the
tests either seed the generator or assert something true of every draw.
"""

import random
from datetime import datetime

import pytest

from bell_system import npc
from bell_system.data import tours
from bell_system.npc import ArcBeat, Switchroom
from bell_system.progression import QUALIFICATIONS

NOW = datetime(1983, 11, 14, 9, 0)


def pool_with_windows():
    """Every windowed line of ambient talk, as (first line, window)."""
    every = list(npc._CHATTER)
    for position in npc._POSITION_CHATTER.values():
        every.extend(position)
    return [(item[2][0], item[3]) for item in every if len(item) > 3]


class TestNoUnaskedAdvice:
    """R5: the older hands do not read the meter to you."""

    def test_the_ambient_advice_channel_is_gone(self):
        assert not hasattr(npc, '_HINTS')
        assert not hasattr(Switchroom, 'hint')

    def test_the_prompt_line_is_off_unless_asked_for(self, raw_terminal):
        assert not raw_terminal.settings.is_on('game.prompts')

    def test_asking_for_it_brings_the_line_back(self, raw_terminal):
        raw_terminal.career.shift = 2
        raw_terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
        raw_terminal.settings.set('game.ambience', 'off')
        raw_terminal.desk.reports.clear()
        raw_terminal.desk.order.clear()
        raw_terminal.desk.open_shift(raw_terminal.clock.now(), 0, count=3)
        assert 'Next:' not in raw_terminal.execute_command('pwd')
        raw_terminal.settings.set('game.prompts', 'on')
        assert 'Next:' in raw_terminal.execute_command('pwd')

    @pytest.mark.parametrize('tour', range(2, 14))
    def test_a_working_tour_has_no_next_line_and_no_advice(
            self, raw_terminal, tour):
        raw_terminal.career.shift = tour
        raw_terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
        raw_terminal.career.set_difficulty('craft')
        raw_terminal.clock.set_tour(tour)
        raw_terminal.desk.reports.clear()
        raw_terminal.desk.order.clear()
        raw_terminal.desk.open_shift(raw_terminal.clock.now(), 0, count=4)
        for _ in range(40):
            assert 'Next:' not in raw_terminal.execute_command('pwd')
        assert all(m.kind != 'hint' for m in raw_terminal.switchroom.log)


class TestTourWindows:
    """C18: a line tagged for some tours is not said on the others."""

    def test_the_windows_cover_the_career_without_overlap(self):
        spans = [tours.EARLY, tours.MIDDLE, tours.LATE, tours.LAST]
        covered = [t for first, last in spans for t in range(first, last + 1)]
        assert covered == list(range(1, len(tours.TOURS) + 1))

    def test_some_lines_are_tagged(self):
        assert {window for _, window in pool_with_windows()} >= {
            tours.EARLY, tours.MIDDLE, tours.LATE, tours.LAST}

    @pytest.mark.parametrize('tour', range(1, 14))
    def test_every_draw_fits_the_tour(self, tour):
        windows = dict(pool_with_windows())
        for seed in range(30):
            room = Switchroom(random.Random(seed))
            for _ in range(12):
                message = room.chatter(NOW, tour=tour)
                if message is None:
                    continue
                window = windows.get(message.lines[0])
                assert window is None or tours.heard_on(window, tour)

    def test_a_middle_line_never_comes_on_tour_two(self):
        middle = {first for first, window in pool_with_windows()
                  if window == tours.MIDDLE}
        assert middle
        for seed in range(60):
            room = Switchroom(random.Random(seed))
            for _ in range(12):
                message = room.chatter(NOW, tour=2)
                if message is not None:
                    assert message.lines[0] not in middle

    def test_with_no_tour_given_every_line_is_on_offer(self):
        windowed = {first for first, _ in pool_with_windows()}
        heard = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed))
            for _ in range(20):
                message = room.chatter(NOW)
                if message is not None:
                    heard.add(message.lines[0])
        assert heard & windowed


class TestTheOrderOfSaying:
    """C18: a beat, then the board, then the building."""

    BEAT = ArcBeat('test.one', npc.CHANNEL_WRITE, 'jsandoval', (5, 8),
                   ('One line.',))

    def room(self):
        return Switchroom(random.Random(1), arcs=[self.BEAT])

    def test_a_beat_that_is_due_beats_the_random_pool(self):
        message = self.room().next_message(NOW, 6)
        assert message.beat == 'test.one'
        assert message.kind == 'beat'
        assert message.lines == ['One line.']

    def test_a_beat_that_is_due_beats_the_board_too(self):
        message = self.room().next_message(
            NOW, 6, overdue=[('TR-00001', '201-555-0100')])
        assert message.beat == 'test.one'

    def test_a_beat_is_not_said_outside_its_tours(self):
        for tour in (1, 2, 4, 9, 13):
            message = self.room().next_message(NOW, tour)
            assert message is None or not message.beat

    def test_a_beat_that_was_said_is_not_said_again(self):
        message = self.room().next_message(NOW, 6, seen=['test.one'])
        assert message is None or not message.beat

    def test_the_board_comes_before_the_building(self):
        message = Switchroom(random.Random(1), arcs=()).next_message(
            NOW, 6, overdue=[('TR-00001', '201-555-0100')])
        assert message.kind == 'chase'
        assert message.about == 'TR-00001'

    def test_a_late_report_is_asked_after_once(self):
        room = Switchroom(random.Random(1), arcs=())
        late = [('TR-00001', '201-555-0100')]
        assert room.next_message(NOW, 6, overdue=late).kind == 'chase'
        again = room.next_message(NOW, 6, overdue=late)
        assert again is None or again.kind == 'chatter'

    def test_with_nothing_due_it_is_the_building(self):
        message = Switchroom(random.Random(1), arcs=()).next_message(NOW, 6)
        assert message.kind == 'chatter'

    def test_a_said_beat_is_filed_in_the_career(self, terminal):
        terminal.switchroom.arcs = [self.BEAT]
        terminal.career.shift = 6
        message = terminal._craft_interruption(terminal._difficulty())
        assert message.beat == 'test.one'
        assert 'test.one' in terminal.career.beats_seen
        again = terminal._craft_interruption(terminal._difficulty())
        assert again is None or not again.beat
