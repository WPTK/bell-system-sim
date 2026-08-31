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
    # cmd_clear lives in the unix screens module, so that is where the name
    # is looked up at call time.
    monkeypatch.setattr(
        'bell_system.screens.unix.clear_screen', lambda *a, **k: calls.append(1)
    )
    assert terminal.execute_command('clear') == ''
    assert calls, 'clear command did not reach the console layer'


class TestCharacterSet:
    """
    Output must be printable 7-bit ASCII by default.

    Bell System terminals of 1978-1983 were ASCII-1967 devices: a Teletype
    Model 43 or DATASPEED 40 could not render a block glyph, a box-drawing
    rule or an emoji. The simulation may still be written with them, but they
    are transliterated on the way out unless a player opts into unicode.
    """

    def test_transliteration_yields_pure_ascii(self):
        source = 'Bar: ██░ 75% ± 2° → ✓ ✅ ⚠ \U0001f527'
        rendered = console.to_ascii(source)
        assert console.non_ascii_characters(rendered) is None

    def test_bars_keep_their_visual_weight(self):
        assert console.to_ascii('███░░') == '###..'

    def test_status_marks_become_words(self):
        assert 'OK' in console.to_ascii('✓')
        assert '[OK]' in console.to_ascii('✅')
        assert '[XX]' in console.to_ascii('❌')

    def test_units_are_preserved_readably(self):
        assert console.to_ascii('±2°') == '+/-2 deg'

    def test_ascii_passes_through_unchanged(self):
        plain = 'TRUNK GROUP TG-001-NYC  utilization 74%'
        assert console.to_ascii(plain) == plain

    def test_newlines_and_tabs_survive(self):
        assert console.to_ascii('a\n\tb') == 'a\n\tb'

    def test_unicode_mode_passes_glyphs_through(self):
        source = '██░'
        assert console.render(source, 'unicode') == source

    def test_ascii_mode_transliterates(self):
        assert console.render('█', 'ascii') == '#'

    def test_every_glyph_in_the_source_has_a_substitution(self):
        """
        No character the simulation writes may fall through untranslated.

        Unmapped characters are dropped rather than passed through, so a new
        glyph would silently vanish from output; this catches that at source.
        """
        from pathlib import Path

        import bell_system

        package_root = Path(bell_system.__file__).parent
        used = set()
        for path in package_root.rglob('*.py'):
            used.update(c for c in path.read_text() if ord(c) > 0x7E)
        unmapped = sorted(used - set(console.ASCII_SUBSTITUTIONS))
        assert not unmapped, (
            'characters with no ASCII substitution: '
            + ', '.join(f'{c!r} U+{ord(c):04X}' for c in unmapped)
        )
