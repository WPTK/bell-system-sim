"""
The rest of the Seventh Edition text tools.

What was already here - tr, cut, sed, sort, uniq, grep, wc - covers the
filters people reach for first. These are the ones they reach for second,
and their absence was felt: pr(1) is how you got a listing onto paper with
a heading, comm(1) and join(1) are how you compared two sorted files before
anyone had a database on a desk, and expr(1) is the only arithmetic the
Bourne shell had.

Everything here is a Seventh Edition command. paste(1), dirname(1) and
nl(1) are deliberately absent: they arrived with PWB and System III, after
the period this machine is set in, and putting them here would be a nicer
machine than the one being depicted.
"""

from typing import List, Optional, Tuple

from ..filesystem import normalise
from .session import SessionState

# pr(1) puts sixty-six lines on a page because that is a US letter sheet at
# six lines to the inch, five of which go to the heading and five to the
# foot. The numbers are the Seventh Edition defaults.
PAGE_LENGTH = 66
HEAD_LINES = 5
FOOT_LINES = 5


class FilterCommands(SessionState):
    """
    Text filters and the small programs shell scripts are built out of.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- paginating ------------------------------------------------------

    def cmd_pr(self, args: Optional[List[str]] = None) -> str:
        """
        Paginate a file for printing.

        Sixty-six lines to the page with a five-line heading carrying the
        date, the file name and the page number. ``-t`` drops the heading and
        the foot, ``-h`` replaces the file name in it, ``-l`` sets the page
        length, and ``-2`` (or any small number) sets that many columns.
        """
        args = args or []
        plain = '-t' in args
        length = PAGE_LENGTH
        columns = 1
        heading = ''
        rest: List[str] = []
        index = 0
        while index < len(args):
            item = args[index]
            if item == '-t':
                pass
            elif item == '-h' and index + 1 < len(args):
                index += 1
                heading = args[index]
            elif item.startswith('-l') and item[2:].isdigit():
                length = max(int(item[2:]), HEAD_LINES + FOOT_LINES + 1)
            elif len(item) == 2 and item[0] == '-' and item[1].isdigit():
                columns = max(int(item[1]), 1)
            elif not item.startswith('-'):
                rest.append(item)
            index += 1

        text, error = self._gather(rest, 'pr')
        if error:
            return error
        lines = text.split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        if not heading:
            heading = rest[0] if rest else ''

        if columns > 1:
            lines = self._columnate(lines, columns)
        if plain:
            return '\n'.join(lines) + '\n' if lines else ''

        body = length - HEAD_LINES - FOOT_LINES
        stamp = self.clock.date_command()
        out: List[str] = []
        for page, start in enumerate(range(0, max(len(lines), 1), body), 1):
            out.extend(['', ''])
            out.append(f"{stamp}  {heading}  Page {page}")
            out.extend(['', ''])
            out.extend(lines[start:start + body])
            out.extend([''] * FOOT_LINES)
        return '\n'.join(out) + '\n'

    @staticmethod
    def _columnate(lines: List[str], columns: int) -> List[str]:
        """Lay lines out down one column and then the next, as pr does."""
        width = max(72 // columns, 8)
        depth = -(-len(lines) // columns)
        rows = []
        for row in range(depth):
            pieces = []
            for column in range(columns):
                index = column * depth + row
                pieces.append(lines[index][:width - 1] if index < len(lines) else '')
            rows.append('  '.join(pieces).rstrip())
        return rows

    # -- comparing sorted files -----------------------------------------

    def cmd_comm(self, args: Optional[List[str]] = None) -> str:
        """
        Print the lines common to two sorted files, and those in only one.

        Three columns: lines only in the first file, lines only in the
        second, lines in both. ``-1``, ``-2`` and ``-3`` suppress a column.
        """
        args = args or []
        # comm takes its flags run together: -12 is both, not a flag called
        # "12". Collecting the digits handles -1 -2, -12 and -123 alike.
        suppress = {digit for item in args if item.startswith('-')
                    for digit in item[1:] if digit in '123'}
        names = [item for item in args if not item.startswith('-')]
        if len(names) != 2:
            return "comm: usage: comm [-123] file1 file2"
        left, error = self._lines_of(names[0], 'comm')
        if error:
            return error
        right, error = self._lines_of(names[1], 'comm')
        if error:
            return error

        out: List[str] = []
        first = second = 0
        indent = {'1': '', '2': '\t', '3': '\t\t'}
        while first < len(left) or second < len(right):
            if second >= len(right) or (first < len(left)
                                        and left[first] < right[second]):
                column, line, first = '1', left[first], first + 1
            elif first >= len(left) or right[second] < left[first]:
                column, line, second = '2', right[second], second + 1
            else:
                column, line = '3', left[first]
                first, second = first + 1, second + 1
            if column not in suppress:
                out.append(indent[column] + line)
        return '\n'.join(out) + '\n' if out else ''

    def cmd_join(self, args: Optional[List[str]] = None) -> str:
        """
        Join two sorted files on a common first field.

        For every line in the first file whose first field matches a line in
        the second, print the field followed by the rest of both lines.
        """
        args = args or []
        names = [item for item in args if not item.startswith('-')]
        if len(names) != 2:
            return "join: usage: join file1 file2"
        left, error = self._lines_of(names[0], 'join')
        if error:
            return error
        right, error = self._lines_of(names[1], 'join')
        if error:
            return error

        table: dict = {}
        for line in right:
            fields = line.split()
            if fields:
                table.setdefault(fields[0], []).append(' '.join(fields[1:]))
        out = []
        for line in left:
            fields = line.split()
            if not fields or fields[0] not in table:
                continue
            for tail in table[fields[0]]:
                out.append(' '.join(
                    [fields[0]] + fields[1:] + ([tail] if tail else [])))
        return '\n'.join(out) + '\n' if out else ''

    def _lines_of(self, name: str, command: str) -> Tuple[List[str], Optional[str]]:
        """Read a file and return its lines, or an error in the second slot."""
        text = self._read(name)
        if text is None:
            return [], f"{command}: cannot open {name}"
        lines = text.split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        return lines, None

    # -- dictionary ------------------------------------------------------

    def cmd_look(self, args: Optional[List[str]] = None) -> str:
        """
        Print the words in the dictionary that begin with a given prefix.

        Reads /usr/dict/words, which is the file spell(1) checks against, so
        what look(1) finds and what spell(1) accepts are the same list.
        """
        args = args or []
        if not args:
            return "look: usage: look prefix [file]"
        prefix = args[0].lower()
        source = args[1] if len(args) > 1 else '/usr/dict/words'
        text = self._read(source)
        if text is None:
            return f"look: cannot open {source}"
        found = [word for word in text.split('\n')
                 if word.lower().startswith(prefix)]
        return '\n'.join(found) + '\n' if found else ''

    # -- splitting and checking -----------------------------------------

    def cmd_split(self, args: Optional[List[str]] = None) -> str:
        """
        Split a file into pieces of a thousand lines.

        ``split -n file`` uses pieces of n lines. The pieces are named xaa,
        xab and so on in the working directory, which is where the x in the
        name comes from.
        """
        args = args or []
        size = 1000
        rest = []
        for item in args:
            if item.startswith('-') and item[1:].isdigit():
                size = max(int(item[1:]), 1)
            else:
                rest.append(item)
        if not rest:
            return "split: usage: split [-n] file [name]"
        text = self._read(rest[0])
        if text is None:
            return f"split: cannot open {rest[0]}"
        stem = rest[1] if len(rest) > 1 else 'x'

        lines = text.split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        made = []
        letters = 'abcdefghijklmnopqrstuvwxyz'
        for piece, start in enumerate(range(0, len(lines), size)):
            if piece >= len(letters) * len(letters):
                return "split: too many pieces"
            name = (f"{stem}{letters[piece // len(letters)]}"
                    f"{letters[piece % len(letters)]}")
            path = normalise(name, self.current_directory)
            error = self.write_file(
                path, '\n'.join(lines[start:start + size]) + '\n')
            if error:
                return error
            made.append(name)
        return ' '.join(made) + '\n' if made else ''

    def cmd_sum(self, args: Optional[List[str]] = None) -> str:
        """
        Print a checksum and a block count for a file.

        The Seventh Edition sum(1) adds the bytes into a sixteen-bit total,
        rotating the accumulator right by one bit before each addition so
        that a pair of transposed bytes does not go unnoticed. Blocks are
        512 bytes, rounded up.
        """
        args = args or []
        text, error = self._gather(args, 'sum')
        if error:
            return error
        names = [item for item in args if not item.startswith('-')]
        if len(names) > 1:
            rows = []
            for name in names:
                one = self._read(name)
                if one is None:
                    rows.append(f"sum: cannot open {name}")
                    continue
                rows.append(f"{self._checksum(one)} {name}")
            return '\n'.join(rows) + '\n'
        return self._checksum(text) + '\n'

    @staticmethod
    def _checksum(text: str) -> str:
        """Return the sum(1) checksum and block count for some text."""
        data = text.encode('latin-1', 'replace')
        total = 0
        for byte in data:
            total = (total >> 1) | ((total & 1) << 15)
            total = (total + byte) & 0xFFFF
        blocks = -(-len(data) // 512)
        return f"{total:5d} {blocks:5d}"

    def cmd_dd(self, args: Optional[List[str]] = None) -> str:
        """
        Copy a file, converting it on the way.

        ``dd if=source of=target`` copies; ``conv=ucase`` and ``conv=lcase``
        change the case; ``count=`` and ``skip=`` work in blocks of ``bs=``
        bytes, 512 by default. The record counts print on standard error on
        a real machine, which here means they print after the copy.
        """
        args = args or []
        options = dict(item.split('=', 1) for item in args if '=' in item)
        source = options.get('if')
        if source is None:
            return "dd: usage: dd if=file [of=file] [bs=n] [count=n] [conv=...]"
        text = self._read(source)
        if text is None:
            return f"dd: cannot open {source}"

        size = int(options['bs']) if options.get('bs', '').isdigit() else 512
        data = text
        if options.get('skip', '').isdigit():
            data = data[int(options['skip']) * size:]
        if options.get('count', '').isdigit():
            data = data[:int(options['count']) * size]
        conversion = options.get('conv', '')
        if 'ucase' in conversion:
            data = data.upper()
        if 'lcase' in conversion:
            data = data.lower()

        full, part = divmod(len(data), size)
        counts = (f"{full}+{1 if part else 0} records in\n"
                  f"{full}+{1 if part else 0} records out")
        target = options.get('of')
        if target is None:
            return data + ('\n' if data and not data.endswith('\n') else '') + counts
        error = self.write_file(
            normalise(target, self.current_directory), data)
        return error if error else counts

    # -- what shell scripts are made of ----------------------------------

    def cmd_expr(self, args: Optional[List[str]] = None) -> str:
        """
        Evaluate an expression and print the result.

        The shell has no arithmetic of its own, so ``i=`expr $i + 1``` is how
        a loop counted in 1983. Handles + - \\* / % and the comparisons,
        which is what people actually used it for.
        """
        args = args or []
        if len(args) == 1:
            return args[0] + '\n'
        if len(args) != 3:
            return "expr: syntax error"
        left, operator, right = args

        comparisons = {'=': lambda a, b: a == b, '!=': lambda a, b: a != b,
                       '<': lambda a, b: a < b, '<=': lambda a, b: a <= b,
                       '>': lambda a, b: a > b, '>=': lambda a, b: a >= b}
        if operator in comparisons:
            if self._numeric(left) and self._numeric(right):
                answer = comparisons[operator](int(left), int(right))
            else:
                answer = comparisons[operator](left, right)
            return ('1' if answer else '0') + '\n'

        if not (self._numeric(left) and self._numeric(right)):
            return "expr: non-numeric argument"
        first, second = int(left), int(right)
        if operator == '+':
            return f"{first + second}\n"
        if operator == '-':
            return f"{first - second}\n"
        if operator in ('*', 'x'):
            return f"{first * second}\n"
        if operator in ('/', '%'):
            if second == 0:
                return "expr: division by zero"
            return f"{first // second if operator == '/' else first % second}\n"
        return "expr: syntax error"

    @staticmethod
    def _numeric(value: str) -> bool:
        """True if a string is an integer expr(1) would accept."""
        return value.lstrip('-').isdigit()

    def cmd_basename(self, args: Optional[List[str]] = None) -> str:
        """
        Strip the directories, and an optional suffix, off a path.

        ``basename /usr/src/cmd/hello.c .c`` prints hello.
        """
        args = args or []
        if not args:
            return "basename: usage: basename string [suffix]"
        name = args[0].rstrip('/').rsplit('/', 1)[-1]
        if len(args) > 1 and name.endswith(args[1]) and name != args[1]:
            name = name[:-len(args[1])]
        return name + '\n'

    def cmd_true(self, args: Optional[List[str]] = None) -> str:
        """Do nothing, successfully. Half of every ``while`` loop ever written."""
        return ''

    def cmd_false(self, args: Optional[List[str]] = None) -> str:
        """Do nothing, unsuccessfully."""
        return ''
