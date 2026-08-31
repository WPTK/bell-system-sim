"""
ed, the editor.

The Seventh Edition editor is the one everybody remembers for answering every
mistake with a single question mark, and that is faithfully reproduced here
because softening it would be missing the point.

The terminal reads one line at a time, which is exactly how ed worked on a
teletype, so this needs no special handling: once ed is running every line
goes to it until you type q. Append mode ends with a lone full stop, the same
as the real thing.

Supported: line numbers, ``.``, ``$``, ranges, ``a`` ``i`` ``c`` ``d`` ``p``
``n`` ``s`` ``w`` ``q`` ``Q`` ``=`` and ``/pattern/``. Not the whole editor,
and ``h`` says so instead of pretending.
"""

from typing import List, Optional

from ..filesystem import normalise
from .session import SessionState


class Ed:
    """One editing session: a buffer, a current line and a filename."""

    def __init__(self, name: str = '', text: str = ''):
        self.name = name
        self.lines: List[str] = text.split('\n') if text else []
        if self.lines and self.lines[-1] == '':
            self.lines.pop()
        self.dot = len(self.lines)
        self.appending = False
        self.append_at = 0
        self.modified = False
        self.last_error = ''
        self.explain = False
        self.warned = False
        self.strikes = 0


class EditorCommands(SessionState):
    """
    ed(1).

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`, which routes
    input here while a session is open.
    """

    def cmd_ed(self, args: Optional[List[str]] = None) -> str:
        """Start the editor, optionally on a file."""
        args = args or []
        name = args[0] if args else ''
        text = ''
        if name:
            text = self._read(name) or ''
            if self._node(name) is None:
                self._editor = Ed(name)
                return '?'
        self._editor = Ed(name, text)
        return str(len(text)) if name else ''

    # -- the session -----------------------------------------------------

    def editor_input(self, line: str) -> str:
        """
        Hand one line to the running editor.

        Returns:
            Whatever ed has to say, which is usually nothing
        """
        session = self._editor
        if session is None:
            return ''

        if session.appending:
            if line == '.':
                session.appending = False
                return ''
            session.lines.insert(session.append_at, line)
            session.append_at += 1
            session.dot = session.append_at
            session.modified = True
            return ''

        return self._ed_command(session, line.strip())

    def _ed_address(self, session: Ed, spec: str) -> Optional[int]:
        """Resolve a single ed address to a one-based line number."""
        spec = spec.strip()
        if spec == '' or spec == '.':
            return session.dot
        if spec == '$':
            return len(session.lines)
        if spec.isdigit():
            return int(spec)
        if spec.startswith('/') and spec.endswith('/') and len(spec) > 1:
            pattern = spec[1:-1]
            order = (list(range(session.dot, len(session.lines)))
                     + list(range(0, session.dot)))
            for index in order:
                if pattern in session.lines[index]:
                    return index + 1
            return None
        if spec.startswith('+'):
            return session.dot + (int(spec[1:]) if spec[1:].isdigit() else 1)
        if spec.startswith('-'):
            return session.dot - (int(spec[1:]) if spec[1:].isdigit() else 1)
        return None

    def _ed_range(self, session: Ed, spec: str):
        """Resolve an address or a comma range."""
        if not spec:
            return session.dot, session.dot
        if spec == ',' or spec == '%':
            return 1, len(session.lines)
        if ',' in spec:
            left, _, right = spec.partition(',')
            start = self._ed_address(session, left or '1')
            end = self._ed_address(session, right or '$')
            return start, end
        one = self._ed_address(session, spec)
        return one, one

    def _ed_command(self, session: Ed, line: str) -> str:
        """Run one ed command line."""
        if line == '':
            session.dot = min(session.dot + 1, len(session.lines))
            if not session.lines:
                return '?'
            return session.lines[session.dot - 1]

        # Split the address from the command letter.
        index = 0
        while index < len(line) and line[index] not in 'aicdpnwqQ=hHsr':
            index += 1
        spec, rest = line[:index], line[index:]
        letter = rest[0] if rest else 'p'
        argument = rest[1:].strip()

        if letter == 'h':
            return session.last_error or ('ed: this ed does a, i, c, d, p, n, '
                                          's, w, q, = and /pattern/.')
        if letter == 'H':
            session.explain = not session.explain
            return ''

        start, end = self._ed_range(session, spec)
        if start is None or end is None:
            return self._ed_fail(session, 'no match')

        if letter == 'q':
            if session.modified and not getattr(session, 'warned', False):
                session.warned = True
                return self._ed_fail(session, 'buffer modified; q again to quit')
            self._editor = None
            return ''
        if letter == 'Q':
            self._editor = None
            return ''

        if letter == '=':
            return str(len(session.lines) if spec == '$' else start)

        if letter in 'ai':
            session.appending = True
            session.append_at = start if letter == 'a' else max(0, start - 1)
            if not session.lines:
                session.append_at = 0
            return ''

        if not session.lines:
            return self._ed_fail(session, 'buffer empty')
        if not (1 <= start <= len(session.lines)
                and 1 <= end <= len(session.lines) and start <= end):
            return self._ed_fail(session, 'line out of range')

        if letter == 'p':
            session.dot = end
            return '\n'.join(session.lines[start - 1:end])
        if letter == 'n':
            session.dot = end
            return '\n'.join(f"{number}\t{session.lines[number - 1]}"
                             for number in range(start, end + 1))
        if letter == 'd':
            del session.lines[start - 1:end]
            session.dot = min(start, len(session.lines))
            session.modified = True
            return ''
        if letter == 'c':
            del session.lines[start - 1:end]
            session.appending = True
            session.append_at = start - 1
            session.modified = True
            return ''
        if letter == 's':
            return self._ed_substitute(session, start, end, argument)
        if letter == 'w':
            return self._ed_write(session, argument)
        if letter == 'r':
            text = self._read(argument) if argument else None
            if text is None:
                return self._ed_fail(session, 'cannot read that file')
            added = text.rstrip('\n').split('\n')
            session.lines[end:end] = added
            session.dot = end + len(added)
            session.modified = True
            return str(len(text))
        return self._ed_fail(session, 'unknown command')

    def _ed_substitute(self, session: Ed, start: int, end: int,
                       argument: str) -> str:
        """Run an s command over a range."""
        if not argument or len(argument) < 2:
            return self._ed_fail(session, 'bad substitution')
        sep = argument[0]
        pieces = argument[1:].split(sep)
        if len(pieces) < 2:
            return self._ed_fail(session, 'bad substitution')
        old, new = pieces[0], pieces[1]
        flags = pieces[2] if len(pieces) > 2 else ''
        count = 0 if 'g' in flags else 1
        hits = 0
        for number in range(start, end + 1):
            line = session.lines[number - 1]
            if old in line:
                session.lines[number - 1] = line.replace(old, new, count)
                session.dot = number
                hits += 1
        if not hits:
            return self._ed_fail(session, 'no match')
        session.modified = True
        return ''

    def _ed_write(self, session: Ed, argument: str) -> str:
        """Write the buffer out."""
        name = argument or session.name
        if not name:
            return self._ed_fail(session, 'no current filename')
        text = '\n'.join(session.lines) + ('\n' if session.lines else '')
        error = self.write_file(normalise(name, self.current_directory), text)
        if error:
            return self._ed_fail(session, error)
        session.name = name
        session.modified = False
        return str(len(text))

    def _ed_fail(self, session: Ed, why: str) -> str:
        """
        Report an error the way ed does.

        A question mark, and nothing else, unless the operator has turned
        explanations on with H or asked for one with h. That terseness is
        the single most remembered thing about this editor.

        One deviation, deliberately: after three question marks in a row it
        says how to get out. The real editor let you sit there as long as you
        liked, but a player who wandered in and cannot leave is not having
        the good kind of 1983 experience.
        """
        session.last_error = f"ed: {why}"
        session.strikes += 1
        if session.explain:
            return session.last_error
        if session.strikes >= 3:
            session.strikes = 0
            return ("?\n(h explains the last ?, H leaves explanations on, "
                    "q quits, Q quits without writing)")
        return '?'
