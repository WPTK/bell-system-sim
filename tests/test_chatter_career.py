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
from bell_system.data.trouble import FAULTS
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


def recycled(desk, seed, tries):
    """Lines said again inside the rest, over a career of `tries` a tour."""
    room = Switchroom(random.Random(seed))
    ledger = []
    said = collections.defaultdict(list)
    quiet = 0
    for tour in range(1, len(tours.TOURS) + 1):
        seated(room, tour)
        for _ in range(tries):
            # The ledger is the only thing keeping a line from coming round.
            room._recent.clear()
            message = room.chatter(NOW, position=desk, tour=tour, seen=ledger)
            if message is None:
                quiet += 1
                continue
            forget_rested(ledger, tour)
            key = chatter_key(tour, message.lines)
            if key not in ledger:
                ledger.append(key)
            said[tuple(message.lines)].append(tour)
    again = [(lines[0], on) for lines, on in said.items()
             for earlier, later in zip(on, on[1:])
             if later - earlier <= CHATTER_REST_TOURS]
    return again, quiet, len(said)


@pytest.mark.parametrize('desk', DESKS, ids=lambda d: d or 'no desk')
@pytest.mark.parametrize('seed', [1, 2, 3])
def test_a_career_never_says_a_line_inside_its_rest(desk, seed):
    """Far busier than craft: sixty tries a tour, so pools do run dry."""
    again, _, said = recycled(desk, seed, 60)
    assert said, 'the building said nothing in thirteen tours'
    assert again == []


def test_the_busy_career_does_run_pools_dry_into_silence():
    quiet = sum(recycled(desk, 1, 60)[1] for desk in DESKS)
    assert quiet > 0


def test_the_recycling_check_can_fail(monkeypatch):
    """With the rest switched off the same career does come round."""
    monkeypatch.setattr(npc, 'rested', lambda lines, tour, seen: True)
    again, _, _ = recycled('sysop', 1, 60)
    assert again


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
# close code. What counts is derived from the data the game answers from
# (data/trouble.py), so a new fault or force is covered without editing this:
# every fault's name, every force it dispatches to, and every three words in a
# row of its mlt signature or its description. A few plain words are added by
# hand: the ones a line says without quoting the data.
STOPWORDS = {'a', 'an', 'and', 'at', 'be', 'by', 'for', 'in', 'is', 'it',
             'its', 'of', 'on', 'or', 'the', 'to', 'with', 'no', 'not', 'one',
             'than', 'that', 'there', 'rather'}


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _runs(text, size=3):
    words = _words(text)
    return {' '.join(words[i:i + size]) for i in range(len(words) - size + 1)}


def _named_by_the_data():
    phrases = set()
    for fault in FAULTS.values():
        phrases.add(' '.join(_words(fault.name)))
        if not fault.dispatch.lower().startswith('none'):
            phrases.add(' '.join(_words(fault.dispatch)))
        phrases |= _runs(fault.mlt_signature) | _runs(fault.description)
    # Runs that are only grammar say nothing about a fault.
    return {run for run in phrases
            if len(set(run.split()) - STOPWORDS) >= 2}


# An idiom of the trade, and Johnson's canonical line about the marker (bible
# section 4): it says a number is in limits, not what is wrong with a loop.
DENIED = _named_by_the_data() - {'out of limits'}
PLAIN = re.compile(
    r"\bground(ed|s)?\b|\bcross(ed)?\b(?!-connect)|\bntf\b|"
    r"no trouble found|send (anybody|anyone|somebody) out|"
    r"\bforeign\b|\bclose code\b",
    re.IGNORECASE)


def _found_in(text):
    spoken = ' '.join(_words(text))
    hits = [run for run in DENIED if run in spoken]
    match = PLAIN.search(text)
    return hits + ([match.group(0)] if match else [])


def test_the_net_catches_what_it_should():
    """The deny-list is not empty or blind to the data it is built on."""
    assert len(DENIED) > 40
    for said in ('If it is a false cross or ground, do not dispatch.',
                 'closed as no trouble found', 'the loop measures clean to it',
                 'do not send anybody out on it', 'NTF again',
                 'it is the cable repair gang',
                 'infinite resistance tip to ring'):
        assert _found_in(said), said


def test_no_line_names_a_fault_a_force_or_a_close_code():
    for item in every_line():
        text = ' '.join(item[2])
        assert _found_in(text) == [], text


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
