"""
Tests for the simplified four-role terminal reached via ``--simple``.

Its ``date`` command raised NameError and its ``__main__`` block instantiated
a class that did not exist.
"""

import pytest


def test_date_command_works(simple):
    """``date`` used to raise NameError: datetime was never imported."""
    result = simple.cmd_date([])
    assert 'EST' in result
    assert len(result.split()) == 6


@pytest.mark.parametrize('command,expected', [
    ('pwd', '/usr'),
    ('ls', 'usr'),
    ('cat /etc/motd', 'Bell Telephone Laboratories'),
    ('echo hello world', 'hello world'),
    ('who', 'root'),
    ('ps', 'PID'),
])
def test_commands_produce_expected_output(simple, command, expected):
    assert expected in simple.execute_command(command)


def test_filesystem_navigation(simple):
    """cd/pwd actually move through the simulated filesystem."""
    simple.execute_command('cd /usr/bin')
    assert simple.execute_command('pwd').strip() == '/usr/bin'
    assert 'awk' in simple.execute_command('ls')


def test_grep_finds_content(simple):
    assert 'root' in simple.execute_command('grep root /etc/passwd')


def test_exported_class_name_is_importable():
    """The public name is SimpleTerminal, distinct from BellSystemTerminal."""
    from bell_system import BellSystemTerminal, SimpleTerminal
    assert SimpleTerminal is not BellSystemTerminal
    assert SimpleTerminal.__name__ == 'SimpleTerminal'
