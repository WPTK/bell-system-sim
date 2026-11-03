"""
Who is on tonight (A12).

Some of the building is a day job. After the day watch ends ``who`` stops
listing them, ``write`` says they are not logged on, and nothing they would
have said turns up on the mail, the write(1) traffic or the order wire.
Nothing here depends on chance: the draws are seeded or the assertion is
about every draw.
"""

import random
from datetime import datetime

import pytest

from bell_system import npc
from bell_system.npc import (
    ARC_BEATS, CRAFT, FAVOUR_AT, WATCH_LABELS, WATCHES, ArcBeat, Switchroom,
    favour_due, on_shift, watch_at,
)

DAY = datetime(1983, 11, 14, 10, 0)
EVENING = datetime(1983, 11, 14, 20, 0)
NIGHT = datetime(1983, 11, 15, 2, 0)

DAY_ONLY = sorted(login for login, person in CRAFT.items()
                  if person.watches == ('day',))
OFF_AT_NIGHT = sorted(login for login, person in CRAFT.items()
                      if 'night' not in person.watches)


def at(terminal, when):
    """Put the terminal's clock on a time of day."""
    terminal.clock.now = lambda: when
    return terminal


class TestTheWatches:
    @pytest.mark.parametrize('hour,watch', [
        (0, 'night'), (7, 'night'), (8, 'day'), (15, 'day'),
        (16, 'evening'), (23, 'evening')])
    def test_the_bands_are_the_briefings(self, hour, watch):
        assert watch_at(datetime(1983, 11, 14, hour, 30)) == watch

    @pytest.mark.parametrize('hour', range(24))
    def test_the_briefing_and_the_roster_agree(self, terminal, hour):
        at(terminal, datetime(1983, 11, 14, hour, 0))
        assert terminal._get_shift_hours() == WATCH_LABELS[
            watch_at(terminal.clock.now())]

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
            assert on_shift(login, NIGHT)

    def test_a_name_not_on_the_roster_is_always_on(self):
        assert on_shift('nobody', NIGHT)


class TestWhoIsLoggedOn:
    def logins(self, terminal, when):
        at(terminal, when)
        return {line.split()[0] for line in terminal.cmd_who().splitlines()}

    def test_by_day_everyone_is_listed(self, terminal):
        assert self.logins(terminal, DAY) == set(CRAFT)

    def test_at_night_the_day_staff_are_not(self, terminal):
        listed = self.logins(terminal, NIGHT)
        assert listed.isdisjoint(OFF_AT_NIGHT)
        assert listed == set(CRAFT) - set(OFF_AT_NIGHT)

    def test_an_evening_man_is_there_in_the_evening_and_not_at_night(
            self, terminal):
        assert 'wfinch' in self.logins(terminal, EVENING)
        assert 'wfinch' not in self.logins(terminal, NIGHT)
        assert 'tnakamura' not in self.logins(terminal, EVENING)

    def test_write_lists_the_same_people(self, terminal):
        at(terminal, NIGHT)
        listing = terminal.cmd_write([])
        for login in OFF_AT_NIGHT:
            assert login not in listing
        assert 'mreyes' in listing

    def test_write_to_someone_who_has_gone_home_says_so(self, terminal):
        at(terminal, NIGHT)
        assert 'not logged on' in terminal.cmd_write(['tnakamura', 'hello'])

    def test_write_to_someone_who_is_in_goes_through(self, terminal):
        at(terminal, NIGHT)
        assert 'Message sent to mreyes' in terminal.cmd_write(
            ['mreyes', 'hello'])


class TestWhatIsSaid:
    @pytest.mark.parametrize('when', [EVENING, NIGHT])
    def test_nobody_off_shift_speaks(self, when):
        off = {login for login in CRAFT if not on_shift(login, when)}
        for seed in range(60):
            room = Switchroom(random.Random(seed))
            for _ in range(15):
                message = room.chatter(when)
                if message is not None:
                    assert message.sender not in off

    def test_and_by_day_the_day_staff_do(self):
        heard = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed))
            for _ in range(15):
                message = room.chatter(DAY)
                if message is not None:
                    heard.add(message.sender)
        assert 'tnakamura' in heard

    def test_the_order_wire_at_night_is_only_who_is_on(self):
        off = {login for login in CRAFT if not on_shift(login, NIGHT)}
        wire = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed))
            for _ in range(20):
                message = room.chatter(NIGHT)
                if message is not None and message.channel == 'orderwire':
                    wire.add(message.sender)
        assert wire
        assert wire.isdisjoint(off)

    def test_the_order_wire_by_day_carries_a_day_man(self):
        wire = set()
        for seed in range(80):
            room = Switchroom(random.Random(seed))
            for _ in range(20):
                message = room.chatter(DAY)
                if message is not None and message.channel == 'orderwire':
                    wire.add(message.sender)
        assert wire & set(OFF_AT_NIGHT)

    def test_a_desk_still_hears_its_own_people_at_night(self):
        room = Switchroom(random.Random(1))
        assert any(room.chatter(NIGHT, position='tsps') for _ in range(40))

    def test_a_beat_from_somebody_who_is_not_in_waits(self):
        beat = ArcBeat('test.day', npc.CHANNEL_MAIL, 'tnakamura', (1, 13),
                       ('One line.',))
        room = Switchroom(random.Random(1), arcs=[beat])
        silent = room.next_message(NIGHT, 6)
        assert silent is None or not silent.beat
        assert room.next_message(DAY, 6).beat == 'test.day'

    def test_every_story_beat_is_from_somebody_who_is_on_at_some_hour(self):
        for beat in ARC_BEATS:
            assert any(on_shift(beat.sender, datetime(1983, 11, 14, h))
                       for h in range(24))

    def test_the_nightly_voices_of_the_story_are_there_at_night(self):
        for beat in ARC_BEATS:
            assert on_shift(beat.sender, NIGHT), beat.key


class TestFieldCalls:
    def test_by_day_the_station_force_is_the_installer(self):
        message = Switchroom(random.Random(1)).field_call(
            DAY, 'TR-1', 'drop open', force='Station')
        assert message.sender == 'wfinch'

    def test_at_night_a_station_call_with_no_crew_named_is_the_splicer(self):
        message = Switchroom(random.Random(1)).field_call(
            NIGHT, 'TR-1', 'drop open', force='Station')
        assert message.sender == 'lokafor'

    def test_a_crew_that_was_sent_is_the_crew_that_calls(self):
        """A callout is not an offer: the dispatcher said who went."""
        message = Switchroom(random.Random(1)).field_call(
            NIGHT, 'TR-1', 'drop open', force='Station',
            crew=CRAFT['wfinch'].name)
        assert message.sender == 'wfinch'


class TestAFavourWaitsForTheDoor:
    def test_it_is_not_asked_of_somebody_who_has_gone_home(self):
        rapport = {'tnakamura': FAVOUR_AT}
        assert favour_due(rapport, [], NIGHT) is None
        assert favour_due(rapport, [], DAY) == 'tnakamura'

    def test_with_no_time_given_it_is_as_before(self):
        assert favour_due({'tnakamura': FAVOUR_AT}, []) == 'tnakamura'

    def test_it_goes_to_the_next_person_who_is_in(self):
        rapport = {'tnakamura': FAVOUR_AT, 'mreyes': FAVOUR_AT}
        assert favour_due(rapport, [], NIGHT) == 'mreyes'
