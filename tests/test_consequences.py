"""
What the board does to a person, and what they do back.

C17 (consequences in a person's voice), A6 (rapport and the story beats).
Nothing here depends on chance: the one random draw is given a stub, and
the rest is invariants over the tables.
"""

import random
import re
from datetime import datetime, timedelta

import pytest

from bell_system import npc
from bell_system.data import consequences
from bell_system.field import CREWS
from bell_system.data.consequences import Late
from bell_system.npc import (
    ARC_BEATS, CRAFT, FAVOUR_AT, FAVOUR_MINUTES, FAVOURS, RAPPORT_MAX,
    Switchroom, adjust_rapport, favour_due, rapport_with,
)
from bell_system.progression import Career
from bell_system.reports import CLASSES_OF_SERVICE

NOW = datetime(1983, 11, 14, 9, 0)
LATE = Late('TR-00001', '201-555-0100', '1FR', True, '08:30')
LINE_LIMIT = 120

# Words that name a fault, a plant item or a cause. Reyes never says them
# (bible section 4): that is the player's to work out.
CAUSE_WORDS = re.compile(
    r'\b(cable|sheath|pair|splice|relay|fuse|bridge|ground|short|open|'
    r'corroded|wet|marker|frame|central office)\b', re.I)


class Stub(random.Random):
    """A generator whose next draw is whatever it was told."""

    def __init__(self, value):
        super().__init__(0)
        self.value = value

    def random(self):
        return self.value


def table_lines():
    for table in (consequences.OVERDUE, consequences.SECOND_CALL,
                  consequences.CALL_BACK):
        yield from table.values()


class TestTheTables:
    @pytest.mark.parametrize('table', [
        consequences.OVERDUE, consequences.SECOND_CALL,
        consequences.CALL_BACK])
    def test_every_class_of_service_has_a_line(self, table):
        assert set(table) == set(CLASSES_OF_SERVICE)

    def test_the_lines_fit_the_screen(self):
        assert all(len(line) <= LINE_LIMIT for line in table_lines())

    @pytest.mark.parametrize('table', [
        consequences.SECOND_CALL, consequences.CALL_BACK])
    def test_what_she_passes_on_ends_on_a_question(self, table):
        """Every message of hers asks one."""
        for line in table.values():
            assert line.endswith('?'), line

    def test_no_line_names_a_cause(self):
        for line in table_lines():
            assert not CAUSE_WORDS.search(line), line

    def test_an_unknown_class_falls_back_instead_of_failing(self):
        assert consequences.second_call('??') == consequences.SECOND_CALL['1FR']
        assert consequences.call_back('??') == consequences.CALL_BACK['1FR']
        assert consequences.overdue('??') == consequences.OVERDUE['1FR']

    def test_the_classes_do_not_all_say_the_same_thing(self):
        for table in (consequences.OVERDUE, consequences.SECOND_CALL,
                      consequences.CALL_BACK):
            assert len(set(table.values())) == len(table)


class TestTheOverdueChase:
    def test_an_out_of_service_customer_reaches_reyes(self):
        message = Switchroom(random.Random(1)).chase(NOW, LATE)
        assert message.sender == 'mreyes'
        assert message.kind == 'chase'
        assert message.about == 'TR-00001'

    def test_she_gives_the_report_the_number_and_the_time(self):
        first = Switchroom(random.Random(1)).chase(NOW, LATE).lines[0]
        assert 'TR-00001' in first
        assert '201-555-0100' in first
        assert '08:30' in first
        assert first.endswith('?')

    def test_her_second_line_is_the_customers_by_class(self):
        for cls in CLASSES_OF_SERVICE:
            late = LATE._replace(class_of_service=cls)
            message = Switchroom(random.Random(1)).chase(NOW, late)
            assert message.lines[1] == consequences.overdue(cls)

    def test_a_customer_with_service_is_the_wire_chiefs_question(self):
        late = LATE._replace(out_of_service=False)
        message = Switchroom(random.Random(1)).chase(NOW, late)
        assert message.sender == 'ehalloran'
        assert 'TR-00001' in message.lines[0]

    def test_the_notice_and_the_chase_never_say_it_twice(self):
        """Said when the commitment passed, so the board need not ask."""
        room = Switchroom(random.Random(1))
        room.overdue_notice(NOW, LATE.number, LATE)
        assert room._board_driven(NOW, [LATE]) is None

    def test_a_notice_for_a_line_out_is_the_customers_by_class(self):
        notice = Switchroom(random.Random(1)).overdue_notice(
            NOW, LATE.number, LATE)
        assert notice.lines == Switchroom._gone_lines(LATE)
        assert notice.lines[1] == consequences.overdue('1FR')

    def test_a_notice_for_a_line_with_service_is_the_plain_one(self):
        notice = Switchroom(random.Random(1)).overdue_notice(
            NOW, LATE.number, LATE._replace(out_of_service=False))
        assert notice.lines == Switchroom._gone_lines(
            LATE._replace(out_of_service=False))
        assert 'was due' in notice.lines[0]
        assert 'neighbour' not in ' '.join(notice.lines)
        assert 'working' not in ' '.join(notice.lines)

    def test_a_chase_the_ledger_has_is_not_made_again(self):
        room = Switchroom(random.Random(1))
        assert room._board_driven(NOW, [LATE], [f'chased:{LATE.number}']) is None
        assert room._board_driven(NOW, [LATE]).kind == 'chase'

    def test_no_chase_line_is_longer_than_the_screen(self):
        for cls in CLASSES_OF_SERVICE:
            for out in (True, False):
                late = LATE._replace(class_of_service=cls, out_of_service=out)
                for line in Switchroom(random.Random(1)).chase(NOW, late).lines:
                    assert len(line) <= LINE_LIMIT


class TestTheSecondCall:
    def repeat(self, cls, committed='15:30'):
        return Switchroom(random.Random(1)).repeat_notice(
            NOW, 'TR-00002', 'code 3', '201-555-0100', cls, committed)

    def test_it_is_reyes_with_the_report_and_the_new_time(self):
        message = self.repeat('1FB')
        assert message.sender == 'mreyes'
        assert message.kind == 'repeat'
        assert 'TR-00002' in message.lines[0]
        assert 'code 3' in message.lines[0]
        assert 'Due 15:30' in message.lines[0]

    @pytest.mark.parametrize('cls', sorted(CLASSES_OF_SERVICE))
    def test_the_customers_words_are_the_classes(self, cls):
        assert self.repeat(cls).lines[1] == consequences.second_call(cls)

    def test_with_no_class_given_it_still_speaks(self):
        message = Switchroom(random.Random(1)).repeat_notice(
            NOW, 'TR-00002', 'code 3', '201-555-0100')
        assert len(message.lines) == 2
        assert 'Due' not in message.lines[0]

    def test_saying_it_again_replaces_the_log_entry(self):
        room = Switchroom(random.Random(1))
        first = room.repeat_notice(NOW, 'TR-00002', 'code 3', '201-555-0100')
        again = room.with_class(first, 'code 3', '201-555-0100', 'PBX', '15:30')
        assert again.lines[1] == consequences.second_call('PBX')
        assert room.log == [again]


class TestTheCallBack:
    def test_it_comes_from_reyes_with_the_close_time(self):
        message = Switchroom(random.Random(1)).call_back(
            NOW, 'TR-00003', '201-555-0100', 'COIN', '10:05')
        assert message.sender == 'mreyes'
        assert message.kind == 'callback'
        assert '10:05' in message.lines[0]
        assert message.lines[1] == consequences.call_back('COIN')

    def test_a_clean_close_draws_a_call_at_most_once(self):
        room, ledger = Switchroom(Stub(0.0)), []
        assert room.rings_back('TR-00003', ledger) is True
        assert room.rings_back('TR-00003', ledger) is False

    def test_a_fresh_room_with_the_same_ledger_does_not_ring_again(self):
        ledger = []
        Switchroom(Stub(0.0)).rings_back('TR-00003', ledger)
        assert Switchroom(Stub(0.0)).rings_back('TR-00003', ledger) is False

    def test_the_chance_is_a_surprise_not_a_habit(self):
        assert 0 < consequences.CALL_BACK_CHANCE <= 0.5
        assert Switchroom(Stub(0.99)).rings_back('TR-00003', []) is False


class TestRapport:
    def test_a_gain_is_one_step(self):
        rapport, ledger = {}, []
        assert adjust_rapport(rapport, ledger, 'mreyes', 2, 1)
        assert rapport == {'mreyes': 1}

    def test_a_second_gain_in_the_same_tour_is_not_counted(self):
        rapport, ledger = {}, []
        adjust_rapport(rapport, ledger, 'mreyes', 2, 1)
        assert not adjust_rapport(rapport, ledger, 'mreyes', 2, 1)
        assert rapport == {'mreyes': 1}

    def test_another_tour_counts_again(self):
        rapport, ledger = {}, []
        adjust_rapport(rapport, ledger, 'mreyes', 2, 1)
        adjust_rapport(rapport, ledger, 'mreyes', 3, 1)
        assert rapport == {'mreyes': 2}

    def test_another_person_counts_in_the_same_tour(self):
        rapport, ledger = {}, []
        adjust_rapport(rapport, ledger, 'mreyes', 2, 1)
        adjust_rapport(rapport, ledger, 'lokafor', 2, 1)
        assert rapport == {'mreyes': 1, 'lokafor': 1}

    def test_it_never_goes_below_nothing(self):
        rapport, ledger = {}, []
        for tour in range(1, 8):
            adjust_rapport(rapport, ledger, 'mreyes', tour, -1)
        assert rapport['mreyes'] == 0

    def test_it_never_goes_above_the_ceiling(self):
        rapport, ledger = {}, []
        for tour in range(1, 14):
            adjust_rapport(rapport, ledger, 'mreyes', tour, 1)
        assert rapport['mreyes'] == RAPPORT_MAX

    def test_a_loss_and_a_gain_in_one_tour_are_each_allowed_once(self):
        rapport, ledger = {'mreyes': 2}, []
        adjust_rapport(rapport, ledger, 'mreyes', 4, -1)
        adjust_rapport(rapport, ledger, 'mreyes', 4, 1)
        adjust_rapport(rapport, ledger, 'mreyes', 4, -1)
        assert rapport['mreyes'] == 2
        assert sorted(entry for entry in ledger) == [
            'rapport+:mreyes:4', 'rapport-:mreyes:4']

    def test_a_crew_is_owed_the_close_and_the_bureau_otherwise(self):
        assert rapport_with(None) == 'mreyes'
        assert rapport_with('nobody in particular') == 'mreyes'
        assert rapport_with(CRAFT['lokafor'].name) == 'lokafor'


class TestTheFavour:
    def test_nothing_is_due_below_the_threshold(self):
        assert favour_due({'mreyes': FAVOUR_AT - 1}, []) is None

    def test_it_is_due_at_the_threshold(self):
        assert favour_due({'lokafor': FAVOUR_AT}, []) == 'lokafor'

    def test_it_is_done_once(self):
        assert favour_due({'lokafor': RAPPORT_MAX},
                          ['favour:lokafor']) is None

    def test_everyone_who_can_do_one_has_the_words(self):
        assert set(FAVOURS) <= set(CRAFT)
        for login, lines in FAVOURS.items():
            assert 1 <= len(lines) <= 2
            for line in lines:
                assert len(line) <= LINE_LIMIT
                assert '{number}' in ''.join(lines)
                assert '{until}' in ''.join(lines)

    def test_it_is_said_in_their_voice_with_the_report_and_the_time(self):
        message = Switchroom(random.Random(1)).favour(
            NOW, 'lokafor', 'TR-00004', '11:30')
        assert message.sender == 'lokafor'
        assert 'TR-00004' in ''.join(message.lines)
        assert '11:30' in ''.join(message.lines)


class TestOnTheShift:
    """The simulation's own bookkeeping, end to end through the terminal."""

    @pytest.fixture
    def shift(self, terminal):
        terminal.settings.set('game.ambience', 'on')
        terminal.career.shift = 4
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=3)
        return terminal

    def close(self, terminal, report, correct, crew=None):
        terminal.desk.close(report, 8, None, terminal.clock.now())
        report.correct = correct
        report.crew = crew

    def test_a_right_close_earns_the_crew_that_worked_it(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        assert shift.career.rapport['lokafor'] == 1

    def test_a_central_office_close_builds_johnsons_rapport_and_nobodys_else(
            self, shift):
        crew = next(c for c in CREWS if c.force == 'Central office')
        report = shift.desk.customers()[0]
        self.close(shift, report, True, crew.name)
        shift._settle_people(quiet=True)
        assert shift.career.rapport == {'rjohnson': 1}

    def test_every_crew_on_the_force_is_owed_its_own_closes(self):
        for crew in CREWS:
            assert CRAFT[rapport_with(crew.name)].name == crew.name

    def test_a_wrong_close_costs_them(self, shift):
        shift.career.rapport['lokafor'] = 2
        report = shift.desk.customers()[0]
        self.close(shift, report, False, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        assert shift.career.rapport['lokafor'] == 1

    def test_a_close_with_no_crew_is_the_bureaus(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True)
        shift._settle_people(quiet=True)
        assert shift.career.rapport['mreyes'] == 1

    def test_one_gain_a_tour_however_many_are_closed(self, shift):
        for report in shift.desk.customers():
            self.close(shift, report, True, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        shift._settle_people(quiet=True)
        assert shift.career.rapport['lokafor'] == 1

    def test_the_gain_is_remembered_across_a_save(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        assert 'rapport+:lokafor:4' in shift.career.beats_seen

    def test_a_practical_does_not_count(self, shift):
        report = shift.desk.customers()[0]
        report.practical = 'some sign-off'
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        assert shift.career.rapport.get('lokafor', 0) == 0

    def reload(self, terminal, rng=None):
        """Save, read the career back and start a fresh room, as a resume."""
        terminal.career.save()
        terminal.career = Career(terminal.career.path)
        terminal.switchroom = Switchroom(rng or random.Random(1))

    def test_a_save_and_a_resume_settle_nothing_twice(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift._settle_people(quiet=True)
        assert shift.career.rapport['lokafor'] == 1
        self.reload(shift)
        shift.career.shift = 5
        shift._settle_people(quiet=True)
        assert shift.career.rapport['lokafor'] == 1
        assert f'settled:{report.number}' in shift.career.beats_seen

    def test_a_close_is_settled_in_the_tour_it_was_closed(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift.career.shift = 5
        shift.clock.set_tour(5)
        shift._settle_people(quiet=True)
        assert shift.career.rapport.get('lokafor', 0) == 0

    def test_the_first_tours_closes_do_not_move_anyone_in_the_second(
            self, shift):
        shift.career.shift = 1
        shift.clock.set_tour(1)
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift.execute_command('pwd')
        shift.career.shift = 2
        shift.clock.set_tour(2)
        shift._settle_people(quiet=True)
        assert shift.career.rapport.get('lokafor', 0) == 0

    def test_a_call_back_is_made_once_across_a_resume(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift.switchroom = Switchroom(Stub(0.0))
        shift._settle_people(quiet=False)
        assert len(shift._queued_messages) == 1
        shift._queued_messages.clear()
        self.reload(shift, Stub(0.0))
        shift._settle_people(quiet=False)
        assert not shift._queued_messages
        assert f'rang:{report.number}' in shift.career.beats_seen

    def test_a_call_back_is_not_made_on_a_quiet_shift(self, shift):
        report = shift.desk.customers()[0]
        self.close(shift, report, True, CRAFT['lokafor'].name)
        shift.switchroom = Switchroom(Stub(0.0))
        shift._settle_people(quiet=True)
        assert not shift._queued_messages

    def test_the_favour_is_done_once_across_a_resume(self, shift):
        shift.career.rapport['lokafor'] = FAVOUR_AT
        self.near(shift)
        assert len(shift._settle_people(quiet=False)) == 1
        commitments = {r.number: r.commitment for r in shift.desk.customers()}
        self.reload(shift)
        assert shift._settle_people(quiet=False) == []
        assert {r.number: r.commitment
                for r in shift.desk.customers()} == commitments
        assert shift.career.beats_seen.count('favour:lokafor') == 1

    def near(self, terminal):
        """Bring the earliest report to within the hour of its commitment."""
        target = min(terminal.desk.customers(), key=lambda r: r.commitment)
        target.commitment = target.received + timedelta(minutes=30)
        return target

    def test_the_favour_waits_until_a_report_is_nearly_due(self, shift):
        shift.career.rapport['lokafor'] = FAVOUR_AT
        for report in shift.desk.customers():
            report.commitment = report.received + timedelta(
                minutes=FAVOUR_MINUTES + 120)
        assert shift._settle_people(quiet=False) == []
        assert 'favour:lokafor' not in shift.career.beats_seen
        target = self.near(shift)
        assert len(shift._settle_people(quiet=False)) == 1
        assert target.commitment == target.received + timedelta(
            minutes=30 + FAVOUR_MINUTES)

    def test_the_favour_moves_the_earliest_commitment_an_hour_once(self, shift):
        shift.career.rapport['lokafor'] = FAVOUR_AT
        target = self.near(shift)
        before = target.commitment
        spoken = shift._settle_people(quiet=False)
        assert target.commitment == before + timedelta(minutes=FAVOUR_MINUTES)
        assert len(spoken) == 1
        assert target.number in spoken[0]
        assert shift._settle_people(quiet=False) == []
        assert target.commitment == before + timedelta(minutes=FAVOUR_MINUTES)

    def test_a_quiet_shift_gets_no_favour_and_loses_none(self, shift):
        shift.career.rapport['lokafor'] = FAVOUR_AT
        assert shift._settle_people(quiet=True) == []
        assert 'favour:lokafor' not in shift.career.beats_seen

    def test_the_first_tour_is_left_alone(self, shift):
        shift.career.shift = 1
        shift.career.rapport['lokafor'] = FAVOUR_AT
        self.near(shift)
        before = [r.commitment for r in shift.desk.customers()]
        shift.execute_command('pwd')
        assert [r.commitment for r in shift.desk.customers()] == before


class TestTheArcs:
    def test_the_keys_are_unique(self):
        keys = [beat.key for beat in ARC_BEATS]
        assert len(keys) == len(set(keys))

    def test_the_windows_are_inside_the_career(self):
        for beat in ARC_BEATS:
            first, last = beat.window
            assert 1 <= first <= last <= 13

    def test_a_beat_is_one_or_two_lines_that_fit(self):
        for beat in ARC_BEATS:
            assert 1 <= len(beat.lines) <= 2
            assert all(len(line) <= LINE_LIMIT for line in beat.lines)

    def test_sandoval_alvarez_and_reyes_each_have_an_arc(self):
        keys = {beat.key.split('.')[0] for beat in ARC_BEATS}
        assert {'sandoval', 'alvarez', 'reyes'} <= keys

    def test_each_arc_runs_in_order_and_its_windows_do_not_run_backward(self):
        for name in ('sandoval', 'alvarez', 'reyes'):
            mine = [b for b in ARC_BEATS if b.key.startswith(f'{name}.')]
            assert [b.key for b in mine] == sorted(b.key for b in mine)
            firsts = [b.window[0] for b in mine]
            assert firsts == sorted(firsts)

    def test_the_speakers_are_people_on_the_machine(self):
        for beat in ARC_BEATS:
            assert beat.sender in CRAFT

    def test_alvarez_is_spoken_of_never_heard_and_has_no_pronoun(self):
        for beat in ARC_BEATS:
            if beat.key.startswith('alvarez'):
                assert beat.sender == 'ehalloran'
                text = ' '.join(beat.lines)
                assert not re.search(r'\b(he|she|his|her|him)\b', text, re.I)

    def test_reyes_asks_a_question_and_does_not_guess_a_cause(self):
        for beat in ARC_BEATS:
            if beat.key.startswith('reyes'):
                text = ' '.join(beat.lines)
                assert beat.sender == 'mreyes'
                assert '?' in text
                assert not CAUSE_WORDS.search(text)

    def test_a_beat_only_comes_up_in_its_window(self):
        for beat in ARC_BEATS:
            for tour in range(1, 14):
                room = Switchroom(random.Random(1), arcs=[beat])
                said = room.next_message(NOW, tour)
                if said is not None and said.beat == beat.key:
                    assert beat.window[0] <= tour <= beat.window[1]

    def test_every_beat_is_heard_by_playing_the_whole_career(self):
        room = Switchroom(random.Random(1))
        seen = []
        for tour in range(1, 14):
            for _ in range(len(ARC_BEATS)):
                said = room.next_message(NOW, tour, seen=seen, recall=LATE)
                if said is not None and said.beat:
                    seen.append(said.beat)
        assert sorted(seen) == sorted(beat.key for beat in ARC_BEATS)

    def test_reyes_gives_the_report_the_number_and_the_time(self):
        for beat in ARC_BEATS:
            if beat.key.startswith('reyes'):
                text = ''.join(beat.lines)
                assert '{number}' in text
                assert '{tel}' in text
                assert '{time}' in text

    def test_a_beat_about_a_report_waits_until_there_is_one(self):
        beat = next(b for b in ARC_BEATS if b.key == 'reyes.1')
        room = Switchroom(random.Random(1), arcs=[beat])
        silent = room.next_message(NOW, 6)
        assert silent is None or not silent.beat
        said = room.next_message(NOW, 6, recall=LATE)
        assert said.beat == 'reyes.1'
        assert 'TR-00001' in said.lines[0]
        assert '201-555-0100' in said.lines[0]
        assert '{' not in ''.join(said.lines)

    def test_the_terminal_speaks_of_the_report_closed_last(self, terminal):
        terminal.career.shift = 6
        terminal.switchroom.arcs = [b for b in ARC_BEATS if b.key == 'reyes.1']
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=2)
        assert terminal._last_closed() is None
        report = terminal.desk.customers()[0]
        terminal.desk.close(report, 8, None, terminal.clock.now())
        said = terminal._craft_interruption(terminal._difficulty())
        assert said.beat == 'reyes.1'
        assert report.number in said.lines[0]

    def test_two_beats_do_not_tell_the_same_report_twice(self, terminal):
        terminal.career.shift = 6
        terminal.switchroom.arcs = [b for b in ARC_BEATS
                                    if b.key in ('reyes.1', 'reyes.2')]
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=3)
        first = terminal.desk.customers()[0]
        terminal.desk.close(first, 8, None, terminal.clock.now())
        one = terminal._craft_interruption(terminal._difficulty())
        assert one.beat == 'reyes.1'
        assert first.number in one.lines[0]
        assert f'about:{first.number}' in terminal.career.beats_seen
        terminal.career.shift = 10
        assert terminal._last_closed() is None
        waiting = terminal._craft_interruption(terminal._difficulty())
        assert waiting is None or not waiting.beat
        second = terminal.desk.customers()[0]
        terminal.desk.close(second, 8, None,
                            terminal.clock.now() + timedelta(minutes=5))
        two = terminal._craft_interruption(terminal._difficulty())
        assert two.beat == 'reyes.2'
        assert second.number in two.lines[0]
        assert first.number not in two.lines[0]

    def test_the_machine_still_keeps_t2_and_t3_for_the_player(self):
        """No beat explains the 03:47 su or what Sandoval is carrying."""
        text = ' '.join(line for beat in ARC_BEATS for line in beat.lines)
        for word in ('03:47', 'su ', 'strike', 'mhuxt', 'Reyes was'):
            assert word not in text

    def test_the_module_still_owns_the_table(self):
        assert npc.ARC_BEATS is ARC_BEATS
