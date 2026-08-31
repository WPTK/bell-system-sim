"""
Tests for the command-line interface.

The console script previously pointed at a module that did not exist, so
``bell-system`` failed with ModuleNotFoundError on every documented command.
"""

import pytest

from bell_system import __version__
from bell_system.cli import build_parser, main


def test_version_flag_reports_the_package_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['--version'])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help_lists_every_documented_option(capsys):
    with pytest.raises(SystemExit):
        main(['--help'])
    out = capsys.readouterr().out
    for option in ('--tutorial', '--role', '--simple', '--version'):
        assert option in out


@pytest.mark.parametrize('role', range(1, 13))
def test_role_argument_accepts_every_valid_role(role):
    assert build_parser().parse_args(['--role', str(role)]).role == role


@pytest.mark.parametrize('role', ['0', '13', '99'])
def test_role_argument_rejects_out_of_range(role):
    with pytest.raises(SystemExit):
        build_parser().parse_args(['--role', role])


def test_role_is_passed_through_to_the_terminal(monkeypatch, isolated_state):
    """
    ``--role N`` reaches the simulation.

    It previously set attributes nothing read, and run() re-prompted anyway.
    """
    seen = {}

    class FakeTerminal:
        def run(self, role=None):
            seen['role'] = role

    monkeypatch.setattr('bell_system.terminal.BellSystemTerminal', FakeTerminal)
    assert main(['--role', '7']) == 0
    assert seen['role'] == 7


def test_simple_flag_selects_the_simplified_terminal(monkeypatch, isolated_state):
    started = {}

    class FakeSimple:
        def run(self):
            started['ran'] = True

    monkeypatch.setattr('bell_system.simple_terminal.SimpleTerminal', FakeSimple)
    assert main(['--simple']) == 0
    assert started['ran']


def test_tutorial_flag_selects_the_tutorial(monkeypatch, isolated_state):
    started = {}

    class FakeTutorial:
        def run(self):
            started['ran'] = True

    monkeypatch.setattr('bell_system.tutorial.BellSystemTutorial', FakeTutorial)
    assert main(['--tutorial']) == 0
    assert started['ran']


def test_keyboard_interrupt_exits_cleanly(monkeypatch, isolated_state):
    """Ctrl-C ends the session with status 0 rather than a traceback."""
    class Interrupting:
        def run(self, role=None):
            raise KeyboardInterrupt

    monkeypatch.setattr('bell_system.terminal.BellSystemTerminal', Interrupting)
    assert main([]) == 0


def test_eof_exits_cleanly(monkeypatch, isolated_state):
    """Ctrl-D ends the session cleanly; the tutorial used to crash on it."""
    class EndOfFile:
        def run(self, role=None):
            raise EOFError

    monkeypatch.setattr('bell_system.terminal.BellSystemTerminal', EndOfFile)
    assert main([]) == 0
