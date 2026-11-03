"""
Ambient chatter over a whole career.

A line is not said again inside CHATTER_REST_TOURS, so a voice that speaks
once a tour for thirteen tours needs four lines it can say. These tests hold
the pools to that, hold the room to never saying a line over (silence is what
a pool said dry gets), and keep the new lines inside the narrative bible:
nothing in them names a fault, a force or a close code, and nobody says a
time of day the watch has not reached.
"""

import collections
import random
import re
from datetime import datetime

import pytest

from bell_system import npc
from bell_system.data import tours
from bell_system.npc import (
    CHATTER_REST_TOURS, Switchroom, chatter_key, forget_rested, heard_on,
    on_shift, rested)

NOW = datetime(1983, 11, 14, 9, 0)
DESKS = [None] + sorted(npc._POSITION_CHATTER)


def pool_for(desk, tour):
    """What a desk could hear on a tour, before the ledger and the dice."""
    pool = list(npc._CHATTER) + list(npc._POSITION_CHATTER.get(desk or '', ()))
    return [item for item in pool
            if len(item) < 4 or heard_on(item[3], tour)]


def seated(room, tour):
    """A room that knows which tour it is: who is in follows the watch."""
    watch = tours.watch_of(tour)
    room.present = lambda login, now: on_shift(login, watch, tour)


def every_line():
    pools = list(npc._CHATTER)
    for position in npc._POSITION_CHATTER.values():
        pools.extend(position)
    return pools


@pytest.mark.parametrize('desk', DESKS, ids=lambda d: d or 'no desk')
def test_each_voice_has_a_line_for_every_tour_of_a_career(desk):
    """Four lines, so one a tour never comes round inside the rest."""
    need = CHATTER_REST_TOURS + 1
    for tour in range(1, len(tours.TOURS) + 1):
        watch = tours.watch_of(tour)
        voices = collections.Counter(
            item[1] for item in pool_for(desk, tour)
            if on_shift(item[1], watch, tour))
        for voice, lines in voices.items():
            assert lines >= need, (desk, tour, voice, lines)


@pytest.mark.parametrize('desk', DESKS, ids=lambda d: d or 'no desk')
@pytest.mark.parametrize('seed', [1, 2, 3])
def test_a_busy_career_never_says_a_line_inside_its_rest(desk, seed):
    """Craft rates: fifteen tries a tour, thirteen tours, three seeds."""
    room = Switchroom(random.Random(seed))
    ledger = []
    said = collections.defaultdict(list)
    for tour in range(1, len(tours.TOURS) + 1):
        seated(room, tour)
        for _ in range(15):
            message = room.chatter(NOW, position=desk, tour=tour, seen=ledger)
            if message is None:
                continue
            forget_rested(ledger, tour)
            key = chatter_key(tour, message.lines)
            if key not in ledger:
                ledger.append(key)
            said[tuple(message.lines)].append(tour)
    assert said, 'the building said nothing in thirteen tours'
    for lines, on in said.items():
        for earlier, later in zip(on, on[1:]):
            assert later - earlier > CHATTER_REST_TOURS, (lines[0], on)


def test_every_voice_is_heard_across_a_career():
    """Quiet is allowed. Mute is not: nobody drops out of the building."""
    heard = collections.Counter()
    for desk in DESKS:
        room = Switchroom(random.Random(7))
        ledger = []
        for tour in range(1, len(tours.TOURS) + 1):
            seated(room, tour)
            for _ in range(15):
                message = room.chatter(NOW, position=desk, tour=tour,
                                       seen=ledger)
                if message is not None:
                    forget_rested(ledger, tour)
                    ledger.append(chatter_key(tour, message.lines))
                    heard[message.sender] += 1
    wanted = {item[1] for item in every_line()}
    assert wanted <= set(heard), wanted - set(heard)


def test_a_line_is_in_the_pool_once():
    firsts = collections.Counter(item[2][0] for item in every_line())
    assert [line for line, n in firsts.items() if n > 1] == []


def test_no_line_is_wider_than_the_bible_allows():
    for item in every_line():
        for line in item[2]:
            assert len(line) <= 72, line
            assert len(line) <= 120, line


# Pillar 1: nothing but mlt or a field finding names a fault, a force or a
# close code. One line predates the check and is left to its own fix (the
# switch desk's wire chief, who says what a false cross or ground reads as).
NAMES = re.compile(
    r'false cross|foreign emf|wet cable|outside plant|cable repair|'
    r'station force|central office force|code [0-9]|disposition',
    re.IGNORECASE)
PREDATES = {'If it is a false cross or ground the loop will measure clean to'}


def test_no_line_names_a_fault_a_force_or_a_close_code():
    for item in every_line():
        text = ' '.join(item[2])
        if item[2][0] in PREDATES:
            continue
        assert not NAMES.search(text), text


@pytest.mark.parametrize('login', ['adm', 'carot'])
def test_the_machines_never_say_you(login):
    for item in every_line():
        if item[1] == login:
            assert not re.search(r'\byou\b|\byour\b', ' '.join(item[2]),
                                 re.IGNORECASE), item[2]


def test_the_chief_operator_counts_in_people_not_in_technical_words():
    for item in every_line():
        if item[1] == 'jhaverty':
            assert not re.search(r'\b(dB|dial tone|marker|trunk|loop)\b',
                                 ' '.join(item[2]), re.IGNORECASE), item[2]


def test_the_splicer_never_speaks_in_decibels_or_percentages():
    for item in every_line():
        if item[1] == 'lokafor':
            text = ' '.join(item[2])
            assert not re.search(r'\bdB\b|percent|%', text), text


def test_the_transmission_engineer_never_says_about():
    for item in every_line():
        if item[1] == 'tnakamura':
            assert not re.search(r'\babout\b', ' '.join(item[2]),
                                 re.IGNORECASE), item[2]


def test_the_wire_chief_is_still_quiet_at_the_end():
    def count(tour):
        total = 0
        for seed in range(30):
            room = Switchroom(random.Random(seed))
            seated(room, tour)
            for _ in range(40):
                message = room.chatter(NOW, position='sysop', tour=tour)
                room._recent.clear()
                if message and message.sender == 'ehalloran':
                    total += 1
        return total
    assert count(13) < count(5)


def test_a_line_just_said_is_not_rested():
    lines = npc._CHATTER[0][2]
    assert not rested(lines, 6, [chatter_key(5, lines)])
