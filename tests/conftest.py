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
    """A constructed main Bell System terminal."""
    from bell_system.terminal import BellSystemTerminal
    return BellSystemTerminal()


@pytest.fixture
def simple(isolated_state):
    """A constructed simplified four-role terminal."""
    from bell_system.simple_terminal import SimpleTerminal
    return SimpleTerminal()
