"""
The qualification ladder can be climbed, and not by everybody.

index_calibration.py plays whole careers through the real terminal. Those are
slow and random, so these run a few and keep the bars wide: a bot that gets the
fault right nine times in ten should be signed off on all six by the last tour,
and one that gets it right six times in ten should not reach Toll.
"""

import importlib.util
import os

import pytest

from bell_system.progression import QUALIFICATIONS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='module')
def calibration():
    spec = importlib.util.spec_from_file_location(
        'index_calibration',
        os.path.join(ROOT, 'tools', 'index_calibration.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toll_reached(held):
    return held[-1] >= len(QUALIFICATIONS)


def test_the_ladder_needs_more_closes_for_each_step():
    needed = [q.requires_reports for q in QUALIFICATIONS]
    assert needed == sorted(needed)
    assert len(set(needed)) == len(needed)


def test_a_strong_craft_bot_signs_off_on_all_six(calibration):
    careers = [calibration.play_career(0.9, 'craft', seed)
               for seed in range(4)]
    assert sum(toll_reached(held) for held in careers) >= 3
    for held in careers:
        assert held == sorted(held)


def test_a_middling_craft_bot_does_not_reach_toll(calibration):
    careers = [calibration.play_career(0.6, 'craft', seed)
               for seed in range(4)]
    assert sum(toll_reached(held) for held in careers) <= 1
