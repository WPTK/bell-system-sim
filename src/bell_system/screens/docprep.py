"""
The document tools, and a C compiler that goes as far as honesty allows.

The Document Preparation Specialist was one of twelve advertised roles and
every one of its seven commands was a placeholder. They are UNIX tools, which
makes them the part of the plant this simulation should have built first.

nroff and troff format text through the ms and man macro packages. tbl
formats tables and hands its output on, the way it did in a pipeline -
tbl | nroff was the ordinary way to use it. eqn is present and says plainly
that it cannot typeset mathematics on this terminal.

cc reads C and produces a runnable a.out. It understands printf and little
else, and the manual page says so: pretending to be a compiler would be the
kind of thing this project has spent its whole life removing.
"""

import re
from typing import List, Optional

from ..filesystem import Node, normalise
from .session import SessionState

# Requests both formatters understand. Anything else is passed over, which
# is what a formatter does with a macro it has not been given.
FILL_WIDTH = 65


class DocumentCommands(SessionState):
    """
    nroff, troff, tbl, eqn and cc.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- formatting ------------------------------------------------------

    def _format(self, text: str, wide: bool) -> str:
        """
        Run text through the formatter.

        Args:
            text: The unformatted source, macros and all
            wide: Whether to typeset for a phototypesetter rather than fill
                for a terminal

        Returns:
            The formatted page
        """
        width = 72 if wide else FILL_WIDTH
        out: List[str] = []
        buffer: List[str] = []
        fill = True
        indent = 0

        def flush() -> None:
            """Empty the fill buffer onto the page."""
            if not buffer:
                return
            line = ''
            pad = ' ' * indent
            for word in buffer:
                if line and len(line) + 1 + len(word) > width - indent:
                    out.append(pad + line)
                    line = word
                else:
                    line = f"{line} {word}".strip()
            if line:
                out.append(pad + line)
            buffer.clear()

        for raw in text.replace('\\-', '-').replace('\\&', '').split('\n'):
            if not raw.startswith('.'):
                if not fill:
                    out.append(raw)
                elif raw.strip():
                    buffer.extend(raw.split())
                else:
                    flush()
                    out.append('')
                continue

            request, _, argument = raw[1:].partition(' ')
            argument = argument.strip().strip('"')
            request = request.strip()

            if request in ('TH', 'TL'):
                flush()
                pieces = argument.split()
                title = pieces[0] if pieces else ''
                section = pieces[1] if len(pieces) > 1 else ''
                heading = f"{title}({section})" if section else title
                out.append(f"{heading}{' ' * max(1, width - 2 * len(heading))}"
                           f"{heading}")
                out.append('')
            elif request in ('SH', 'NH'):
                flush()
                out.append('')
                out.append(argument.upper() if request == 'SH' else argument)
                indent = 5
            elif request in ('PP', 'LP', 'P'):
                flush()
                out.append('')
            elif request == 'B':
                buffer.extend(argument.upper().split())
            elif request == 'I':
                buffer.extend(f"_{word}_" for word in argument.split())
            elif request == 'br':
                flush()
            elif request == 'sp':
                flush()
                out.extend([''] * max(1, int(argument) if argument.isdigit() else 1))
            elif request == 'nf':
                flush()
                fill = False
            elif request == 'fi':
                fill = True
            elif request == 'ce':
                flush()
                fill = True
            elif request in ('IP', 'TP'):
                flush()
                out.append('')
                indent = 5
                if argument:
                    out.append(argument)
            # Anything else is a request this formatter does not implement,
            # and is dropped rather than printed as if it were text.

        flush()
        while out and not out[0].strip():
            out.pop(0)
        return '\n'.join(out)

    def cmd_nroff(self, args: Optional[List[str]] = None) -> str:
        """Format a document for a terminal or a printer."""
        args = args or []
        text, error = self._gather(args, 'nroff')
        if error:
            return error
        if not text.strip():
            return ("nroff: usage: nroff [-ms|-man] file\n"
                    "Reads standard input when given no file, so\n"
                    "tbl table | nroff works.")
        return self._format(text, wide=False)

    def cmd_troff(self, args: Optional[List[str]] = None) -> str:
        """
        Format a document for a phototypesetter.

        There is no typesetter on this machine, so troff formats to a wider
        measure and says where the output would have gone.
        """
        args = args or []
        text, error = self._gather(args, 'troff')
        if error:
            return error
        if not text.strip():
            return "troff: usage: troff [-ms|-man] file"
        return (self._format(text, wide=True)
                + "\n\n[troff: no typesetter on this machine; "
                  "output shown as formatted]")

    def cmd_tbl(self, args: Optional[List[str]] = None) -> str:
        """
        Format tables for the formatters.

        Reads the region between .TS and .TE, takes the row format line, and
        lays the columns out. Meant to be piped into nroff, which is how it
        was used.
        """
        args = args or []
        text, error = self._gather(args, 'tbl')
        if error:
            return error
        if '.TS' not in text:
            return ("tbl: no .TS in the input.\n"
                    "A table looks like:\n"
                    "  .TS\n  l l r.\n  Office\tType\tLines\n  .TE")

        out: List[str] = []
        for block in text.split('.TS')[1:]:
            body, _, _ = block.partition('.TE')
            rows = [line for line in body.strip().split('\n') if line.strip()]
            if not rows:
                continue
            spec = rows[0].rstrip('.').split()
            cells = [row.split('\t') for row in rows[1:]]
            if not cells:
                continue
            widths = [
                max(len(row[column]) for row in cells if column < len(row))
                for column in range(max(len(row) for row in cells))
            ]
            out.append('.nf')
            for row in cells:
                pieces = []
                for column, cell in enumerate(row):
                    align = spec[column] if column < len(spec) else 'l'
                    pieces.append(cell.rjust(widths[column])
                                  if align.startswith('r')
                                  else cell.center(widths[column])
                                  if align.startswith('c')
                                  else cell.ljust(widths[column]))
                out.append('  '.join(pieces).rstrip())
            out.append('.fi')
        return '\n'.join(out)

    def cmd_eqn(self, args: Optional[List[str]] = None) -> str:
        """Typeset mathematics, which this terminal cannot do."""
        return ("eqn: this terminal cannot set mathematics.\n\n"
                "eqn produced typesetter output for troff, and there is no\n"
                "typesetter here. The input is passed through unchanged so a\n"
                "pipeline does not break:\n\n"
                + (getattr(self, '_pipe_input', '') or ''))

    # -- compiling -------------------------------------------------------

    def cmd_cc(self, args: Optional[List[str]] = None) -> str:
        """
        Compile a C program.

        This understands printf and nothing else. It reads the calls out of
        main and builds a program that prints them, which is enough for
        hello.c and honest about being no more than that.
        """
        args = args or []
        sources = [a for a in args if a.endswith('.c')]
        output = 'a.out'
        for index, arg in enumerate(args):
            if arg == '-o' and index + 1 < len(args):
                output = args[index + 1]
        if not sources:
            return "cc: usage: cc [-o name] file.c"

        text = self._read(sources[0])
        if text is None:
            return f"cc: cannot open {sources[0]}"
        if 'main' not in text:
            return f"cc: {sources[0]}: undefined: _main"

        printed: List[str] = []
        for call in re.findall(r'printf\s*\(\s*"((?:[^"\\]|\\.)*)"', text):
            printed.append(call.replace('\\n', '\n').replace('\\t', '\t')
                           .replace('\\"', '"').replace('\\\\', '\\'))
        if not printed:
            printed = ['']

        program = ''.join(printed)
        path = normalise(output, self.current_directory)
        self.filesystem[path] = Node(
            'file', self.username or 'sysop', 'craft', '-rwxr-xr-x', program)
        self._compiled[path] = program
        return ''

    def run_compiled(self, path: str) -> Optional[str]:
        """Return the output of a compiled program, or None if it is not one."""
        return self._compiled.get(path)
