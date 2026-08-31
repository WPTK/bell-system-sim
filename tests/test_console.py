"""
Tests for the terminal output layer.

Screen clearing previously shelled out to ``clear``/``cls`` from three
different modules, which bandit flagged as three high-severity findings and
which fails wherever the external binary is absent.
"""

import io

from bell_system import console


def test_clear_screen_writes_the_control_sequence():
    stream = io.StringIO()
    console.clear_screen(stream)
    assert stream.getvalue() == console.CLEAR_SCREEN


def test_clear_sequence_erases_and_homes_the_cursor():
    """ANSI: erase the whole display, then move the cursor to 1,1."""
    assert console.CLEAR_SCREEN == '\033[2J\033[H'


def test_no_module_shells_out_to_clear():
    """No module may launch a subprocess to clear the screen."""
    import ast
    from pathlib import Path

    import bell_system

    package_root = Path(bell_system.__file__).parent
    offenders = []
    for path in package_root.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            # os.system(...) / os.popen(...)
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'os'
                    and node.func.attr in {'system', 'popen', 'spawnl'}):
                offenders.append(f'{path.name}:{node.lineno} os.{node.func.attr}')
            # import subprocess
            if isinstance(node, ast.Import):
                offenders += [
                    f'{path.name}:{node.lineno} import {a.name}'
                    for a in node.names if a.name == 'subprocess'
                ]
    assert not offenders, f'modules shelling out: {offenders}'


def test_terminal_clear_command_uses_the_console_layer(terminal, monkeypatch):
    calls = []
    monkeypatch.setattr(
        'bell_system.terminal.clear_screen', lambda *a, **k: calls.append(1)
    )
    assert terminal.execute_command('clear') == ''
    assert calls, 'clear command did not reach the console layer'
