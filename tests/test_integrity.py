"""
Structural integrity tests.

These guard the whole class of defects that made the simulation unrunnable:
imports trapped inside docstrings, dispatch entries pointing at handlers that
do not exist, aliases expanding to unknown commands, unreachable code after
``return``, and methods called but never defined. Each is checked mechanically
so the defect cannot silently return.
"""

import ast
import collections
import importlib
import pkgutil
from pathlib import Path

import pytest

import bell_system

PACKAGE_ROOT = Path(bell_system.__file__).parent
SOURCE_FILES = sorted(PACKAGE_ROOT.rglob('*.py'))
MODULE_NAMES = [
    f'bell_system.{m.name}' for m in pkgutil.iter_modules([str(PACKAGE_ROOT)])
]


@pytest.mark.parametrize('module_name', MODULE_NAMES)
def test_every_module_imports(module_name):
    """Every module imports cleanly - catches imports stranded in docstrings."""
    assert importlib.import_module(module_name) is not None


@pytest.mark.parametrize('path', SOURCE_FILES, ids=lambda p: p.name)
def test_no_imports_stranded_in_docstring(path):
    """
    A module docstring must not contain its import block.

    This is the exact defect that left seven modules unrunnable: the imports
    parsed as a string literal, so the names were never bound.
    """
    tree = ast.parse(path.read_text())
    docstring = ast.get_docstring(tree) or ''
    offenders = []
    for line in docstring.splitlines():
        if not line.startswith(('import ', 'from ')):
            continue
        # Prose can begin with those words. Only a line that actually parses
        # as an import statement is the defect this guards against.
        try:
            parsed = ast.parse(line.strip())
        except SyntaxError:
            continue
        if parsed.body and isinstance(parsed.body[0],
                                      (ast.Import, ast.ImportFrom)):
            offenders.append(line)
    assert not offenders, f'{path.name} has imports inside its docstring: {offenders}'


@pytest.mark.parametrize('path', SOURCE_FILES, ids=lambda p: p.name)
def test_no_unreachable_code_after_return(path):
    """No statement may follow a ``return`` in the same block."""
    tree = ast.parse(path.read_text())
    dead = []

    def scan(body, where):
        for i, stmt in enumerate(body):
            if isinstance(stmt, ast.Return) and i < len(body) - 1:
                dead.append(f'{where} line {body[i + 1].lineno}')
            for field in ('body', 'orelse', 'finalbody'):
                sub = getattr(stmt, field, None)
                if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                    scan(sub, where)
            for handler in getattr(stmt, 'handlers', []):
                scan(handler.body, where)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scan(node.body, f'{path.name}:{node.name}')

    assert not dead, f'unreachable code after return: {dead}'


@pytest.mark.parametrize('path', SOURCE_FILES, ids=lambda p: p.name)
def test_no_duplicate_definitions(path):
    """No class may define the same method name twice."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names = [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            duplicates = [n for n, c in collections.Counter(names).items() if c > 1]
            assert not duplicates, f'{path.name}:{node.name} redefines {duplicates}'


def _self_calls(source):
    """Return every ``self.x()`` call in a source file, with its line."""
    called = {}
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'self'):
            called.setdefault(node.func.attr, node.lineno)
    return called


def test_no_calls_to_undefined_methods():
    """
    Every ``self.x()`` call resolves to a method the terminal actually has.

    Nine methods were called but never defined, so whole command branches
    raised AttributeError at runtime.

    The screens live in mixins now, so a call in one file legitimately
    resolves to a definition in another. Resolution therefore runs against
    the constructed class's own method resolution order, which is what
    Python will do at runtime - a stricter check than scanning one file, not
    a looser one.
    """
    from bell_system.terminal import BellSystemTerminal

    sources = {'terminal.py': (PACKAGE_ROOT / 'terminal.py').read_text()}
    for path in sorted((PACKAGE_ROOT / 'screens').glob('*.py')):
        sources[f'screens/{path.name}'] = path.read_text()

    missing = {}
    for where, source in sources.items():
        for name, line in _self_calls(source).items():
            if not hasattr(BellSystemTerminal, name):
                missing[f'{where}:{line}'] = name

    assert not missing, f'called but never defined: {missing}'


def test_every_screen_module_is_mixed_in():
    """
    A screens module that nothing inherits from is dead code.

    Splitting the monolith made it possible to leave a module behind without
    noticing, because nothing would fail - the commands would simply be gone.
    """
    from bell_system.terminal import BellSystemTerminal

    inherited = {base.__module__ for base in BellSystemTerminal.__mro__}
    for path in sorted((PACKAGE_ROOT / 'screens').glob('*.py')):
        if path.name == '__init__.py':
            continue
        module = f'bell_system.screens.{path.stem}'
        assert module in inherited, f'{path.name} is not mixed into the terminal'


def test_no_screen_module_is_oversized():
    """
    No screens module may grow back into a monolith.

    terminal.py reached 11,241 lines because there was nothing stopping it.
    """
    limit = 1000
    oversized = {}
    for path in sorted((PACKAGE_ROOT / 'screens').glob('*.py')):
        length = len(path.read_text().splitlines())
        if length > limit:
            oversized[path.name] = length
    assert not oversized, (
        f'modules over {limit} lines: {oversized}. Split by subsystem.')


def test_the_terminal_itself_stays_small():
    """The terminal is dispatch and session, not a place to put screens."""
    length = len((PACKAGE_ROOT / 'terminal.py').read_text().splitlines())
    assert length < 2000, (
        f'terminal.py is {length} lines. Screens belong in screens/.')


def test_every_alias_resolves_to_a_real_command(terminal):
    """
    Command aliases must expand to commands that exist.

    Eight aliases pointed at handlers that were never registered, so ``ls``,
    ``ll``, ``la`` and ``dir`` all failed with 'command not found'.
    """
    handlers = terminal._command_handlers
    builtin = {'quit', 'clear'}
    broken = {
        alias: target
        for alias, target in terminal.COMMAND_ALIASES.items()
        if target.split()[0] not in handlers and target not in builtin
    }
    assert not broken, f'aliases with no matching handler: {broken}'


def test_every_dispatch_entry_is_callable(terminal):
    """Every registered command maps to something callable."""
    for name, handler in terminal._command_handlers.items():
        assert callable(handler), f'{name} is not callable'


def test_advertised_subcommands_are_implemented(terminal):
    """
    A command must implement every subcommand its own error message lists.

    ``trunk status`` was rejected as an unknown option by the very message
    that listed the available options, and the manual page advertised four
    more subcommands that did not exist.
    """
    import re

    broken = []
    for name in sorted(terminal._command_handlers):
        if name in {'quit', 'clear', 'test'}:
            continue
        probe = terminal.execute_command(f'{name} __unlikely_subcommand__')
        match = re.search(r'Available commands?:\s*(.+)', probe)
        if not match:
            continue
        for sub in (s.strip() for s in match.group(1).split(',')):
            if not sub or ' ' in sub:
                continue
            # Many subcommands require one or two arguments, so a bare call
            # correctly falls through. A subcommand rejected at every arity
            # has no branch at all.
            attempts = [
                terminal.execute_command(f'{name} {sub}'),
                terminal.execute_command(f'{name} {sub} PROBE'),
                terminal.execute_command(f'{name} {sub} PROBE VALUE'),
            ]
            if all('Unknown option' in attempt for attempt in attempts):
                broken.append(f'{name} {sub}')

    assert not broken, f'advertised but not implemented: {broken}'


def test_dispatch_table_is_built_once(terminal):
    """
    The dispatch table is built during construction, not per command.

    It was previously rebuilt from scratch on every keystroke.
    """
    before = id(terminal._command_handlers)
    terminal.execute_command('ps')
    terminal.execute_command('who')
    assert id(terminal._command_handlers) == before
