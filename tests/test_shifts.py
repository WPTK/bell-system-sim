"""
Who is on tonight (A12).

Some of the building is a day job. On a tour worked on the evening or night
watch ``who`` stops listing them, ``write`` says they are not logged on, and
nothing they would have said turns up on the mail, the write(1) traffic or
the order wire. The watch is the tour's (``tours.watch_of``), not the hour
on the clock, which starts every tour at 08:00: so these tests drive a tour
and never touch the clock. Nothing depends on chance: the draws are seeded
or the assertion is about every draw.
"""

import random
from datetime import datetime

import pytest

from bell_system import npc
from bell_system.data.tours import TOURS, WATCHES, watch_of
from bell_system.field import CREWS
from bell_system.npc import (
    _CHATTER, _POSITION_CHATTER, ARC_BEATS, AWAY, CRAFT, CRAFT_BY_NAME,
    FAVOUR_AT, WATCH_LABELS,
    ArcBeat, Switchroom, favour_due, is_away, on_shift, watch_at,
)

DAY_TOUR = 1
EVENING_TOUR = 3
NIGHT_TOUR = 4
# Okafor is out on 12 (a night tour) and 13 (a day one).
AWAY_TOURS = (12, 13)

DAY_ONLY = sorted(login for login, person in CRAFT.items()
                  if person.watches == ('day',))
OFF_AT_NIGHT = sorted(login for login, person in CRAFT.items()
                      if 'night' not in person.watches)
OFF_IN_THE_EVENING = sorted(login for login, person in CRAFT.items()
                            if 'evening' not in person.watches)


def on_tour(terminal, tour):
    """Put the terminal on a tour. The clock is the clock's own business."""
    terminal.career.shift = tour
    terminal.clock.set_tour(tour)
    return terminal


def logins(terminal):
    return {line.split()[0] for line in terminal.cmd_who().splitlines()}


class TestTheWatches:
    def test_every_tour_has_a_watch_that_is_one_of_three(self):
        assert [tour.watch for tour in TOURS] == [
            watch_of(n) for n in range(1, len(TOURS) + 1)]
        assert {tour.watch for tour in TOURS} <= set(WATCHES)

    def test_all_three_are_worked_and_none_is_a_one_off(self):
        for watch in WATCHES:
            assert sum(tour.watch == watch for tour in TOURS) >= 3, watch

    def test_the_first_tour_is_a_day(self):
        """The first tour is one report and the wire chief, by day."""
        assert watch_of(1) == 'day'

    def test_a_tour_off_the_end_of_the_table_is_a_day(self):
        assert watch_of(0) == watch_of(99) == 'day'

    @pytest.mark.parametrize('hour,watch', [
        (0, 'night'), (7, 'night'), (8, 'day'), (15, 'day'),
        (16, 'evening'), (23, 'evening')])
    def test_the_hour_on_a_real_clock_has_these_bands(self, hour, watch):
        assert watch_at(datetime(1983, 11, 14, hour, 30)) == watch

    @pytest.mark.parametrize('tour', range(1, 14))
    def test_the_briefing_and_the_roster_agree(self, terminal, tour):
        on_tour(terminal, tour)
        assert terminal._get_shift_hours() == WATCH_LABELS[watch_of(tour)]

    def test_a_simulated_clock_never_leaves_the_morning(self, terminal):
        """Why the tour has to say: the hour on the clock cannot."""
        on_tour(terminal, NIGHT_TOUR)
        assert terminal.clock.now().hour == 8

    def test_a_real_clock_is_decided_by_its_hour(self, terminal):
        terminal.settings.set('date.source', 'real')
        terminal.clock.now = lambda: datetime(1983, 11, 14, 2, 0)
        on_tour(terminal, DAY_TOUR)
        assert terminal.current_watch() == 'night'
        assert not terminal.is_in('tnakamura')

    def test_most_of_the_building_is_there_all_round_the_clock(self):
        round_the_clock = [p for p in CRAFT.values()
                           if p.watches == WATCHES]
        assert len(round_the_clock) > len(CRAFT) // 2

    def test_some_of_it_is_a_day_job(self):
        assert DAY_ONLY

    def test_every_watch_listed_is_a_real_one(self):
        for person in CRAFT.values():
            assert person.watches
            assert set(person.watches) <= set(WATCHES)

    def test_the_machines_never_go_home(self):
        for login in ('adm', 'carot'):
            assert CRAFT[login].watches == WATCHES

    def test_the_people_the_story_needs_at_night_are_there(self):
        """Reyes at 03:47 and Halloran at 06:15 (narrative-bible T2)."""
        for login in ('mreyes', 'ehalloran'):
            assert on_shift(login, 'night')

    def test_the_chief_operator_is_in_the_evening_and_not_at_night(self):
        assert on_shift('jhaverty', 'evening')
        assert not on_shift('jhaverty', 'night')

    def test_a_name_not_on_the_roster_is_always_on(self):
        assert on_shift('nobody', 'night')
        assert on_shift('nobody', 'night', 12)


class TestWhoIsLoggedOn:
    def test_by_day_everyone_is_listed(self, terminal):
        on_tour(terminal, DAY_TOUR)
        assert logins(terminal) == set(CRAFT)

    def test_on_a_night_tour_the_day_staff_are_not(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        listed = logins(terminal)
        assert listed.isdisjoint(OFF_AT_NIGHT)
        assert listed == set(CRAFT) - set(OFF_AT_NIGHT)

    def test_it_is_the_tour_that_counts_not_the_clock(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        assert terminal.clock.now().hour == 8
        assert 'tnakamura' not in logins(terminal)

    def test_the_evening_man_is_there_in_the_evening_and_not_at_night(
            self, terminal):
        assert 'wfinch' in logins(on_tour(terminal, EVENING_TOUR))
        assert 'wfinch' not in logins(on_tour(terminal, NIGHT_TOUR))
        assert 'tnakamura' not in logins(on_tour(terminal, EVENING_TOUR))

    def test_write_lists_the_same_people(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        listing = terminal.cmd_write([])
        for login in OFF_AT_NIGHT:
            assert login not in listing
        assert 'mreyes' in listing

    def test_the_manual_says_who_is_reachable_depends_on_the_watch(self):
        from bell_system.data.man_pages import MAN_PAGES
        users = MAN_PAGES['write'].split('USERS')[1]
        assert 'depends on the watch' in users

    def test_write_to_someone_who_has_gone_home_says_so(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        assert 'not logged on' in terminal.cmd_write(['tnakamura', 'hello'])

    def test_write_to_someone_who_is_in_goes_through(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        assert 'Message sent to mreyes' in terminal.cmd_write(
            ['mreyes', 'hello'])


class TestWhatIsSaid:
    @pytest.mark.parametrize('tour', [EVENING_TOUR, NIGHT_TOUR])
    def test_nobody_off_shift_speaks(self, terminal, tour):
        on_tour(terminal, tour)
        off = {login for login in CRAFT if not terminal.is_in(login)}
        assert off
        for seed in range(60):
            room = Switchroom(random.Random(seed),
                              present=terminal.switchroom.present)
            for _ in range(15):
                message = room.chatter(terminal.clock.now())
                if message is not None:
                    assert message.sender not in off

    def test_and_by_day_the_day_staff_do(self, terminal):
        on_tour(terminal, DAY_TOUR)
        heard = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed),
                              present=terminal.switchroom.present)
            for _ in range(15):
                message = room.chatter(terminal.clock.now())
                if message is not None:
                    heard.add(message.sender)
        assert 'tnakamura' in heard

    def test_the_order_wire_on_a_night_tour_is_only_who_is_on(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        off = {login for login in CRAFT if not terminal.is_in(login)}
        wire = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed),
                              present=terminal.switchroom.present)
            for _ in range(20):
                message = room.chatter(terminal.clock.now())
                if message is not None and message.channel == 'orderwire':
                    wire.add(message.sender)
        assert wire
        assert wire.isdisjoint(off)

    def test_the_order_wire_by_day_carries_a_day_man(self, terminal):
        on_tour(terminal, DAY_TOUR)
        wire = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed),
                              present=terminal.switchroom.present)
            for _ in range(20):
                message = room.chatter(terminal.clock.now())
                if message is not None and message.channel == 'orderwire':
                    wire.add(message.sender)
        assert wire & set(OFF_AT_NIGHT)

    def test_the_terminals_own_room_goes_by_the_tour(self, terminal):
        """The room the terminal built, not one a test made."""
        on_tour(terminal, NIGHT_TOUR)
        off = {login for login in CRAFT if not terminal.is_in(login)}
        for _ in range(200):
            message = terminal.switchroom.chatter(terminal.clock.now())
            if message is not None:
                assert message.sender not in off

    @pytest.mark.parametrize('position', sorted(_POSITION_CHATTER))
    def test_every_desk_hears_its_own_people_on_a_night_tour(
            self, terminal, position):
        """A message from the position's own senders arrives at night."""
        on_tour(terminal, NIGHT_TOUR)
        own = {item[2][0] for item in _POSITION_CHATTER[position]
               if terminal.is_in(item[1])}
        assert own, f'{position} has nobody on at night'
        heard = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed),
                              present=terminal.switchroom.present)
            for _ in range(10):
                message = room.chatter(terminal.clock.now(),
                                       position=position)
                if message is not None:
                    heard.add(message.lines[0])
        assert heard & own

    def test_a_beat_from_somebody_who_is_not_in_waits(self):
        beat = ArcBeat('test.day', npc.CHANNEL_MAIL, 'tnakamura', (1, 13),
                       ('One line.',))
        night = Switchroom(random.Random(1), arcs=[beat],
                           present=lambda login, _: on_shift(login, 'night'))
        silent = night.next_message(datetime(1983, 11, 14, 8), 6)
        assert silent is None or not silent.beat
        day = Switchroom(random.Random(1), arcs=[beat],
                         present=lambda login, _: on_shift(login, 'day'))
        assert day.next_message(datetime(1983, 11, 14, 8), 6).beat == 'test.day'

    def test_every_story_beat_is_from_somebody_on_every_watch(self):
        """Else the beat would be lost on the tours worked on that watch."""
        for beat in ARC_BEATS:
            for watch in WATCHES:
                assert on_shift(beat.sender, watch), (beat.key, watch)


class TestAnAbsence:
    def test_okafor_is_out_on_the_last_two_tours(self):
        assert AWAY == {'lokafor': (12, 13)}
        assert [n for n in range(1, 14) if is_away('lokafor', n)] == [12, 13]

    @pytest.mark.parametrize('tour', AWAY_TOURS)
    def test_who_does_not_list_her(self, terminal, tour):
        on_tour(terminal, tour)
        assert 'lokafor' not in logins(terminal)

    @pytest.mark.parametrize('tour', AWAY_TOURS)
    def test_write_says_she_is_not_logged_on(self, terminal, tour):
        on_tour(terminal, tour)
        assert 'not logged on' in terminal.cmd_write(['lokafor', 'hello'])
        assert 'lokafor' not in terminal.cmd_write([])

    def test_before_that_she_is_there(self, terminal):
        on_tour(terminal, 11)
        assert 'lokafor' in logins(terminal)
        assert 'Message sent to lokafor' in terminal.cmd_write(
            ['lokafor', 'hello'])

    @pytest.mark.parametrize('tour', AWAY_TOURS)
    def test_the_crew_pool_cannot_send_her(self, terminal, tour):
        on_tour(terminal, tour)
        force = terminal.desk.force
        assert [c.key for c in force.crews_for('Cable repair')] == ['sandoval']
        assert 'okafor' not in {c.key for c in force.roster()}
        crew, _, _ = force.send('Cable repair', 'TR-1', 30, 0)
        assert crew.key == 'sandoval'

    def test_the_rest_of_the_force_is_unchanged(self, terminal):
        on_tour(terminal, 12)
        force = terminal.desk.force
        assert {c.key for c in CREWS} - {c.key for c in force.roster()} == {
            'okafor'}

    def test_before_that_she_can_be_sent(self, terminal):
        on_tour(terminal, 11)
        keys = [c.key for c in terminal.desk.force.crews_for('Cable repair')]
        assert 'okafor' in keys

    def test_nobody_speaks_as_her_while_she_is_out(self, terminal):
        on_tour(terminal, 12)
        for _ in range(300):
            message = terminal.switchroom.chatter(terminal.clock.now())
            if message is not None:
                assert message.sender != 'lokafor'

    def test_sandovals_line_about_the_sheath_is_then_true(self, terminal):
        beat = next(b for b in ARC_BEATS if b.key == 'sandoval.3')
        assert beat.window == AWAY['lokafor']
        for tour in AWAY_TOURS:
            on_tour(terminal, tour)
            assert not terminal.is_in('lokafor')
            assert terminal.is_in(beat.sender)

    def test_a_field_call_with_nobody_named_is_a_splicer_who_is_in(
            self, terminal):
        on_tour(terminal, 12)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), 'TR-1', 'open', force='Outside plant')
        assert message.sender == 'jsandoval'


    def test_nobody_answers_for_her_on_the_scoreboard_while_she_is_out(
            self, terminal):
        """Her eleven is hers to defend, and nobody else has the line."""
        on_tour(terminal, 12)
        assert terminal.switchroom.moo_beaten(terminal.clock.now(), 6) is None

    def test_and_before_that_she_does(self, terminal):
        on_tour(terminal, 11)
        message = terminal.switchroom.moo_beaten(terminal.clock.now(), 6)
        assert message.sender == 'lokafor'

    def test_every_field_crew_is_somebody_on_the_roster(self):
        for crew in CREWS:
            assert crew.name in CRAFT_BY_NAME, crew.name
            assert CRAFT_BY_NAME[crew.name] in CRAFT

    def test_a_station_call_when_nobody_is_in_to_make_it_is_sandovals(
            self, terminal):
        """Finch is off at night and Okafor is away: the other splicer."""
        on_tour(terminal, 12)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), 'TR-1', 'drop open', force='Station')
        assert message.sender == 'jsandoval'


class TestNoTonightOnADayTour:
    """A tour may be worked by day, so nobody says it is tonight."""

    def test_no_chatter_says_it(self):
        for item in list(_CHATTER) + [
                i for lines in _POSITION_CHATTER.values() for i in lines]:
            assert 'tonight' not in ' '.join(item[2]), item[2][0]

    def test_the_wire_chiefs_chase_does_not(self):
        late = npc.Late('TR-1', '201-555-0100', '1FR', False, '08:30')
        message = Switchroom(random.Random(1)).chase(datetime(1983, 11, 14),
                                                      late)
        assert 'tonight' not in ' '.join(message.lines)

    def test_nor_do_the_replies_to_write(self, terminal):
        on_tour(terminal, DAY_TOUR)
        for login in CRAFT:
            for _ in range(4):
                assert 'tonight' not in terminal.cmd_write(
                    [login, 'hello']).lower()


class TestFieldCalls:
    def test_by_day_the_station_force_is_the_installer(self, terminal):
        on_tour(terminal, DAY_TOUR)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), 'TR-1', 'drop open', force='Station')
        assert message.sender == 'wfinch'

    def test_on_a_night_tour_a_station_call_with_no_crew_named_is_a_splicer(
            self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), 'TR-1', 'drop open', force='Station')
        assert message.sender == 'lokafor'

    def test_a_crew_that_was_sent_is_the_crew_that_calls(self, terminal):
        """A callout is not an offer: the dispatcher said who went."""
        on_tour(terminal, NIGHT_TOUR)
        message = terminal.switchroom.field_call(
            terminal.clock.now(), 'TR-1', 'drop open', force='Station',
            crew=CRAFT['wfinch'].name)
        assert message.sender == 'wfinch'

    def test_dispatch_does_not_care_who_is_on_the_watch(self, terminal):
        """Crews are called out, so only the voice follows the watch."""
        on_tour(terminal, NIGHT_TOUR)
        assert not terminal.is_in('abright')
        crew, _, _ = terminal.desk.force.send('Outside plant', 'TR-1', 30, 0)
        assert crew.key == 'bright'


class TestAFavourWaitsForTheDoor:
    @staticmethod
    def night(login):
        return on_shift(login, 'night')

    def test_it_is_not_asked_of_somebody_who_has_gone_home(self):
        rapport = {'abright': FAVOUR_AT}
        assert favour_due(rapport, [], self.night) is None
        assert favour_due(rapport, [], lambda login: True) == 'abright'

    def test_with_nobody_named_it_is_as_before(self):
        assert favour_due({'abright': FAVOUR_AT}, []) == 'abright'

    def test_it_goes_to_the_next_person_who_is_in(self):
        rapport = {'abright': FAVOUR_AT, 'mreyes': FAVOUR_AT}
        assert favour_due(rapport, [], self.night) == 'mreyes'

    def test_the_terminal_asks_who_is_in_on_this_tour(self, terminal):
        on_tour(terminal, NIGHT_TOUR)
        assert not terminal.is_in('abright')
        assert favour_due({'abright': FAVOUR_AT}, [], terminal.is_in) is None
