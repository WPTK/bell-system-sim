"""Shared pytest fixtures for the Bell System simulation test suite."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """
    Point logs and command history at a temporary directory.

    Keeps the suite from writing into the developer's real state directory
    and guarantees each test starts from a clean slate.
    """
    monkeypatch.setenv('BELL_SYSTEM_HOME', str(tmp_path / 'state'))


@pytest.fixture
def terminal(isolated_state):
    """
    A constructed main Bell System terminal, fully qualified and quiet.

    Qualification gating, ambient traffic from the other craft and the
    standing what-to-do-next prompt are all real behaviour, but they make
    every other command's output conditional on progression, on a dice roll
    and on the state of the board. Tests that exercise a command want the
    command. Progression, ambience and guidance have their own tests, which
    build their own terminals.
    """
    from bell_system.progression import QUALIFICATIONS
    from bell_system.terminal import BellSystemTerminal

    instance = BellSystemTerminal()
    instance.settings.set('game.ambience', 'off')
    instance.settings.set('game.prompts', 'off')
    instance.career.qualifications = [q.key for q in QUALIFICATIONS]
    # Somebody signed off on everything is not on their first tour, and a
    # first tour holds the board at one report and keeps the building quiet.
    # Tests of the working shift want the working shift.
    instance.career.shift = 2
    # Persisted, because it is on disk everywhere else: the career is only
    # ever written when it changes, so a fixture that moves the shift and
    # does not write it leaves the record disagreeing with the session.
    instance.career.save()
    # The clock reads the tour at construction, before the fixture moved
    # it. Real sessions load the career first; this keeps the two agreeing.
    instance.clock.set_tour(instance.career.shift)
    return instance


@pytest.fixture
def raw_terminal(isolated_state):
    """A terminal as a new player gets it: one qualification, ambience on."""
    from bell_system.terminal import BellSystemTerminal
    return BellSystemTerminal()


@pytest.fixture
def simple(isolated_state):
    """A constructed simplified four-role terminal."""
    from bell_system.simple_terminal import SimpleTerminal
    return SimpleTerminal()
