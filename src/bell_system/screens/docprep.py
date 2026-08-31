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

    # -- pic(1) -----------------------------------------------------------

    def cmd_pic(self, args: Optional[List[str]] = None) -> str:
        """
        Set simple diagrams for troff.

        Reads the .PS/.PE blocks out of a file and draws what they describe.
        The real pic(1) is a language with variables, positions and splines
        that hands troff a page of drawing commands; this one understands
        boxes, circles, arrows, lines and moves in a left-to-right or
        downward chain, and draws them in characters because a terminal is
        what is here rather than a typesetter.

        Anything outside a .PS block passes through unchanged, which is how
        pic behaved when it sat in front of troff.
        """
        args = args or []
        text, error = self._gather(args, 'pic')
        if error:
            return error

        out: List[str] = []
        block: List[str] = []
        inside = False
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('.PS'):
                inside, block = True, []
                continue
            if stripped.startswith('.PE'):
                out.extend(self._draw_pic(block))
                inside = False
                continue
            if inside:
                block.append(stripped)
            else:
                out.append(line)
        if inside:
            return "pic: .PS without .PE"
        return '\n'.join(out)

    # What a pic statement can start with, and how wide the shape is drawn.
    _PIC_SHAPES = ('box', 'circle', 'ellipse')

    def _draw_pic(self, block: List[str]) -> List[str]:
        """
        Draw one .PS block.

        Statements run left to right until a ``down`` is seen, after which
        each shape goes under the last. That is two of pic's four directions
        and covers the diagrams anybody actually drew in a memo.
        """
        chain: List[tuple] = []
        vertical = False
        for line in block:
            if not line or line.startswith('#'):
                continue
            word = line.split()[0].lower()
            label = ''
            if '"' in line:
                label = line.split('"')[1]
            if word == 'down':
                vertical = True
                continue
            if word == 'right':
                vertical = False
                continue
            if word in self._PIC_SHAPES:
                chain.append((word, label))
            elif word in ('arrow', 'line', 'move'):
                chain.append((word, label))
        if not chain:
            return []
        return (self._draw_pic_down(chain) if vertical
                else self._draw_pic_across(chain))

    @staticmethod
    def _shape_rows(kind: str, label: str) -> List[str]:
        """Return the three rows a shape occupies, drawn in characters."""
        body = f" {label} " if label else '    '
        if kind == 'box':
            return [f"+{'-' * len(body)}+", f"|{body}|", f"+{'-' * len(body)}+"]
        if kind in ('circle', 'ellipse'):
            return [f" {'_' * len(body)} ", f"({body})", f" {'-' * len(body)} "]
        if kind == 'arrow':
            return ['     ', '---->', '     ']
        if kind == 'line':
            return ['     ', '-----', '     ']
        return ['     ', '     ', '     ']

    def _draw_pic_across(self, chain: List[tuple]) -> List[str]:
        """Lay the chain out left to right, three rows deep."""
        rows = ['', '', '']
        for kind, label in chain:
            piece = self._shape_rows(kind, label)
            width = max(len(row) for row in piece)
            for index in range(3):
                rows[index] += piece[index].ljust(width)
        return [row.rstrip() for row in rows]

    def _draw_pic_down(self, chain: List[tuple]) -> List[str]:
        """Lay the chain out downward, one shape under the last."""
        rows: List[str] = []
        for kind, label in chain:
            if kind == 'arrow':
                rows.extend(['  |', '  v'])
                continue
            if kind == 'line':
                rows.extend(['  |', '  |'])
                continue
            if kind == 'move':
                rows.append('')
                continue
            rows.extend(self._shape_rows(kind, label))
        return rows

    # -- refer(1) ---------------------------------------------------------

    def cmd_refer(self, args: Optional[List[str]] = None) -> str:
        """
        Fill in citations from a bibliography.

        Text between .[ and .] names a paper. refer looks it up in
        /usr/dict/papers, replaces the citation with a bracketed number, and
        puts a numbered reference list at the end. The real refer(1) searched
        an inverted index built by indxbib; this one scans the file, which is
        the same answer more slowly on a bibliography this size.
        """
        args = args or []
        text, error = self._gather(args, 'refer')
        if error:
            return error
        bibliography = self._read('/usr/dict/papers')
        if bibliography is None:
            return "refer: cannot open /usr/dict/papers"
        records = [record for record in bibliography.split('\n\n')
                   if record.strip()]

        cited: List[str] = []
        out: List[str] = []
        pending: List[str] = []
        inside = False
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped == '.[':
                inside, pending = True, []
                continue
            if stripped == '.]':
                inside = False
                key = ' '.join(pending)
                found = self._find_paper(key, records)
                if found is None:
                    out.append(f"[refer: no reference for {key}]")
                    continue
                if found not in cited:
                    cited.append(found)
                out.append(f"[{cited.index(found) + 1}]")
                continue
            if inside:
                pending.append(stripped)
            else:
                out.append(line)

        body = self._join_citations(out)
        if not cited:
            return body
        # A .br before each entry so that a formatter downstream keeps them
        # apart. refer's output is troff input, not finished text: without
        # this the whole reference list fills into one paragraph.
        listing = ['', 'References', '']
        for number, record in enumerate(cited, 1):
            listing.append('.br')
            listing.append(f"{number}. {self._format_paper(record)}")
        return body.rstrip() + '\n' + '\n'.join(listing) + '\n'

    @staticmethod
    def _join_citations(lines: List[str]) -> str:
        """Put a bracketed number back onto the end of the line before it."""
        joined: List[str] = []
        for line in lines:
            if line.startswith('[') and joined:
                joined[-1] = joined[-1].rstrip() + ' ' + line
            else:
                joined.append(line)
        return '\n'.join(joined)

    @staticmethod
    def _find_paper(key: str, records: List[str]) -> Optional[str]:
        """Return the record matching every word of the citation, or None."""
        wanted = [word.lower() for word in key.split() if len(word) > 1]
        if not wanted:
            return None
        for record in records:
            haystack = record.lower()
            if all(word in haystack for word in wanted):
                return record
        return None

    @staticmethod
    def _format_paper(record: str) -> str:
        """Turn a %-keyed record into one line of a reference list."""
        fields: dict = {}
        for line in record.split('\n'):
            if len(line) > 2 and line.startswith('%'):
                fields.setdefault(line[1], []).append(line[3:].strip())
        pieces = []
        if 'A' in fields:
            pieces.append(' and '.join(fields['A']))
        for key, wrap in (('T', '"{}"'), ('J', '{}'), ('V', '{}'),
                          ('D', '{}'), ('P', 'pp. {}')):
            if key in fields:
                pieces.append(wrap.format(fields[key][0]))
        return ', '.join(pieces) + '.'
