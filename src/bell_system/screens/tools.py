"""
The rest of the Seventh Edition toolkit: filters, and small useful programs.

These are the commands that make a UNIX machine feel like one. Each is small,
does one thing, reads standard input when given no file, and composes with the
others through a pipe - which is the whole argument the system was making.

Behaviour follows the Seventh Edition where it sensibly can. ``tr`` takes two
character sets and translates between them, ``cut`` takes a field or character
range, ``sed`` here does substitution and deletion rather than the whole
language, ``od`` dumps octal because that is what the o stands for, and
``diff`` reports the line numbers that differ in ed(1) command form, which is
how diff output was meant to be fed back into ed.
"""

import random
from typing import List, Optional

from ..filesystem import normalise
from .session import SessionState


class ToolCommands(SessionState):
    """
    Filters and small utilities.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- filters ---------------------------------------------------------

    def cmd_tr(self, args: Optional[List[str]] = None) -> str:
        """
        Translate characters.

        ``tr a-z A-Z`` upper-cases; ``-d`` deletes the first set instead.
        """
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        sets = [a for a in args if not a.startswith('-')]
        if not sets:
            return "tr: usage: tr [-d] set1 [set2]"

        def expand(spec: str) -> str:
            """Expand a-z style ranges."""
            out, index = '', 0
            while index < len(spec):
                if (index + 2 < len(spec) and spec[index + 1] == '-'
                        and spec[index + 2] >= spec[index]):
                    out += ''.join(chr(c) for c in
                                   range(ord(spec[index]), ord(spec[index + 2]) + 1))
                    index += 3
                else:
                    out += spec[index]
                    index += 1
            return out

        text = getattr(self, '_pipe_input', '') or ''
        source = expand(sets[0])
        if 'd' in flags:
            return ''.join(c for c in text if c not in source)
        if len(sets) < 2:
            return "tr: usage: tr [-d] set1 [set2]"
        target = expand(sets[1])
        if not target:
            return text
        target += target[-1] * (len(source) - len(target))
        return text.translate(str.maketrans(source[:len(target)], target))

    def cmd_cut(self, args: Optional[List[str]] = None) -> str:
        """
        Cut columns out of each line.

        ``-f`` takes fields with ``-d`` as the separator; ``-c`` takes
        character positions.
        """
        args = args or []
        fields = chars = None
        delimiter = '\t'
        for arg in args:
            if arg.startswith('-f'):
                fields = arg[2:] or None
            elif arg.startswith('-c'):
                chars = arg[2:] or None
            elif arg.startswith('-d'):
                delimiter = arg[2:] or '\t'

        text, error = self._gather([a for a in args if not a.startswith('-')],
                                   'cut')
        if error:
            return error

        def positions(spec: str, width: int) -> List[int]:
            """Turn 1,3-5 into zero-based indexes."""
            picked: List[int] = []
            for piece in spec.split(','):
                if '-' in piece:
                    low, _, high = piece.partition('-')
                    start = int(low) if low else 1
                    end = int(high) if high else width
                    picked.extend(range(start - 1, end))
                elif piece.isdigit():
                    picked.append(int(piece) - 1)
            return picked

        out = []
        for line in text.rstrip('\n').split('\n'):
            if fields:
                parts = line.split(delimiter)
                out.append(delimiter.join(
                    parts[i] for i in positions(fields, len(parts))
                    if 0 <= i < len(parts)))
            elif chars:
                out.append(''.join(
                    line[i] for i in positions(chars, len(line))
                    if 0 <= i < len(line)))
            else:
                return "cut: usage: cut [-dc] -f list [file]"
        return '\n'.join(out)

    def cmd_sed(self, args: Optional[List[str]] = None) -> str:
        """
        Edit a stream.

        Supports ``s/old/new/`` with an optional ``g``, and ``/pattern/d``.
        Not the whole language, and it says so rather than pretending.
        """
        args = args or []
        scripts = [a for a in args if a.startswith(('s', '/'))
                   and not a.startswith('-')]
        if not scripts:
            return ("sed: usage: sed 's/old/new/[g]' [file]\n"
                    "This sed does substitution and deletion only.")
        script = scripts[0]
        rest = [a for a in args if a is not script and not a.startswith('-')]
        text, error = self._gather(rest, 'sed')
        if error:
            return error
        lines = text.rstrip('\n').split('\n')

        if script.startswith('s') and len(script) > 1:
            sep = script[1]
            parts = script[2:].split(sep)
            if len(parts) < 2:
                return "sed: bad substitution"
            old, new = parts[0], parts[1]
            flags = parts[2] if len(parts) > 2 else ''
            count = 0 if 'g' in flags else 1
            return '\n'.join(line.replace(old, new, count) for line in lines)

        if script.startswith('/') and script.endswith('d'):
            pattern = script[1:script.rfind('/')]
            return '\n'.join(line for line in lines if pattern not in line)

        return "sed: command not understood"

    def cmd_tee(self, args: Optional[List[str]] = None) -> str:
        """Copy standard input to a file and to the output."""
        args = args or []
        text = getattr(self, '_pipe_input', '') or ''
        for name in [a for a in args if not a.startswith('-')]:
            path = normalise(name, self.current_directory)
            error = self.write_file(path, text, append='-a' in args)
            if error:
                return error
        return text

    def cmd_rev(self, args: Optional[List[str]] = None) -> str:
        """Reverse the characters of every line."""
        text, error = self._gather(args or [], 'rev')
        if error:
            return error
        return '\n'.join(line[::-1] for line in text.rstrip('\n').split('\n'))

    def cmd_cmp(self, args: Optional[List[str]] = None) -> str:
        """Compare two files and say where they first differ."""
        args = args or []
        if len(args) < 2:
            return "cmp: usage: cmp file1 file2"
        first, second = self._read(args[0]), self._read(args[1])
        if first is None:
            return f"cmp: {args[0]}: cannot open"
        if second is None:
            return f"cmp: {args[1]}: cannot open"
        if first == second:
            return ''
        for offset, (a, b) in enumerate(zip(first, second), 1):
            if a != b:
                line = first[:offset].count('\n') + 1
                return (f"{args[0]} {args[1]} differ: char {offset}, "
                        f"line {line}")
        return (f"cmp: EOF on "
                f"{args[0] if len(first) < len(second) else args[1]}")

    def cmd_diff(self, args: Optional[List[str]] = None) -> str:
        """
        Report the lines that differ between two files.

        Output is in ed(1) command form, which is what diff was for: the
        result could be fed straight back into the editor.
        """
        args = args or []
        if len(args) < 2:
            return "diff: usage: diff file1 file2"
        first, second = self._read(args[0]), self._read(args[1])
        if first is None:
            return f"diff: {args[0]}: cannot open"
        if second is None:
            return f"diff: {args[1]}: cannot open"

        import difflib
        left = first.rstrip('\n').split('\n')
        right = second.rstrip('\n').split('\n')
        out: List[str] = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                None, left, right).get_opcodes():
            if tag == 'equal':
                continue
            span = f"{i1 + 1}" if i2 - i1 <= 1 else f"{i1 + 1},{i2}"
            other = f"{j1 + 1}" if j2 - j1 <= 1 else f"{j1 + 1},{j2}"
            letter = {'replace': 'c', 'delete': 'd', 'insert': 'a'}[tag]
            out.append(f"{span}{letter}{other}")
            out.extend(f"< {line}" for line in left[i1:i2])
            if tag == 'replace':
                out.append('---')
            out.extend(f"> {line}" for line in right[j1:j2])
        return '\n'.join(out)

    def cmd_od(self, args: Optional[List[str]] = None) -> str:
        """Dump a file in octal, which is what the o is for."""
        args = args or []
        text, error = self._gather(args, 'od')
        if error:
            return error
        raw = text.encode('utf-8', 'replace')[:512]
        rows = []
        for offset in range(0, len(raw), 16):
            chunk = raw[offset:offset + 16]
            words = [f"{chunk[i] | (chunk[i + 1] << 8):06o}"
                     if i + 1 < len(chunk) else f"{chunk[i]:06o}"
                     for i in range(0, len(chunk), 2)]
            rows.append(f"{offset:07o} " + ' '.join(words))
        rows.append(f"{len(raw):07o}")
        return '\n'.join(rows)

    def cmd_spell(self, args: Optional[List[str]] = None) -> str:
        """
        Print words that are not in the dictionary.

        Checks against /usr/dict/words, which is the same file look(1)
        searches, so the two agree. The real one held some twenty-five
        thousand entries against this one's few hundred: spell(1) here will
        call a word wrong that a real V7 machine knew, and the dictionary is
        readable so you can see exactly which words it does know.
        """
        text, error = self._gather(args or [], 'spell')
        if error:
            return error
        dictionary = self._read('/usr/dict/words')
        if dictionary is None:
            return "spell: cannot open /usr/dict/words"
        known = set(dictionary.split())
        odd = sorted({
            word.strip('.,:;()"\'').lower()
            for word in text.split()
            if word.strip('.,:;()"\'').isalpha()
        } - known)
        return '\n'.join(odd)

    # -- small programs --------------------------------------------------

    def cmd_banner(self, args: Optional[List[str]] = None) -> str:
        """Print its argument in large letters."""
        glyphs = {
            'A': ['  #  ', ' # # ', '#####', '#   #', '#   #'],
            'B': ['#### ', '#   #', '#### ', '#   #', '#### '],
            'C': [' ####', '#    ', '#    ', '#    ', ' ####'],
            'D': ['#### ', '#   #', '#   #', '#   #', '#### '],
            'E': ['#####', '#    ', '#### ', '#    ', '#####'],
            'F': ['#####', '#    ', '#### ', '#    ', '#    '],
            'G': [' ####', '#    ', '#  ##', '#   #', ' ####'],
            'H': ['#   #', '#   #', '#####', '#   #', '#   #'],
            'I': ['#####', '  #  ', '  #  ', '  #  ', '#####'],
            'J': ['   ##', '    #', '    #', '#   #', ' ### '],
            'K': ['#   #', '#  # ', '###  ', '#  # ', '#   #'],
            'L': ['#    ', '#    ', '#    ', '#    ', '#####'],
            'M': ['#   #', '## ##', '# # #', '#   #', '#   #'],
            'N': ['#   #', '##  #', '# # #', '#  ##', '#   #'],
            'O': [' ### ', '#   #', '#   #', '#   #', ' ### '],
            'P': ['#### ', '#   #', '#### ', '#    ', '#    '],
            'Q': [' ### ', '#   #', '# # #', '#  # ', ' ## #'],
            'R': ['#### ', '#   #', '#### ', '#  # ', '#   #'],
            'S': [' ####', '#    ', ' ### ', '    #', '#### '],
            'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  '],
            'U': ['#   #', '#   #', '#   #', '#   #', ' ### '],
            'V': ['#   #', '#   #', '#   #', ' # # ', '  #  '],
            'W': ['#   #', '#   #', '# # #', '## ##', '#   #'],
            'X': ['#   #', ' # # ', '  #  ', ' # # ', '#   #'],
            'Y': ['#   #', ' # # ', '  #  ', '  #  ', '  #  '],
            'Z': ['#####', '   # ', '  #  ', ' #   ', '#####'],
            '0': [' ### ', '#  ##', '# # #', '##  #', ' ### '],
            '1': ['  #  ', ' ##  ', '  #  ', '  #  ', '#####'],
            '2': [' ### ', '#   #', '   # ', '  #  ', '#####'],
            '3': ['#### ', '    #', ' ### ', '    #', '#### '],
            '4': ['#   #', '#   #', '#####', '    #', '    #'],
            '5': ['#####', '#    ', '#### ', '    #', '#### '],
            '6': [' ####', '#    ', '#### ', '#   #', ' ### '],
            '7': ['#####', '    #', '   # ', '  #  ', ' #   '],
            '8': [' ### ', '#   #', ' ### ', '#   #', ' ### '],
            '9': [' ### ', '#   #', ' ####', '    #', ' ### '],
            ' ': ['     ', '     ', '     ', '     ', '     '],
            '-': ['     ', '     ', '#####', '     ', '     '],
            '.': ['     ', '     ', '     ', '     ', '  #  '],
            '&': [' ##  ', '#  # ', ' ##  ', '#  ##', ' ## #'],
        }
        text = ' '.join(args or []).upper()[:12]
        if not text:
            return "banner: usage: banner text"
        rows = []
        for line in range(5):
            rows.append(' '.join(
                glyphs.get(character, glyphs[' '])[line] for character in text))
        return '\n'.join(rows)

    def cmd_factor(self, args: Optional[List[str]] = None) -> str:
        """Factor a number into primes."""
        args = args or []
        if not args:
            return "factor: usage: factor number"
        try:
            number = int(args[0])
        except ValueError:
            return "factor: ouch"
        if number < 2:
            return "factor: ouch"
        factors, remainder, divisor = [], number, 2
        while divisor * divisor <= remainder:
            while remainder % divisor == 0:
                factors.append(divisor)
                remainder //= divisor
            divisor += 1
        if remainder > 1:
            factors.append(remainder)
        return f"{number}    " + ' '.join(str(f) for f in factors)

    def cmd_primes(self, args: Optional[List[str]] = None) -> str:
        """Print the primes in a range."""
        args = args or []
        try:
            low = int(args[0]) if args else 2
            high = int(args[1]) if len(args) > 1 else low + 100
        except ValueError:
            return "primes: usage: primes [start [stop]]"
        high = min(high, low + 2000)
        found = []
        for candidate in range(max(2, low), high + 1):
            if all(candidate % d for d in range(2, int(candidate ** 0.5) + 1)):
                found.append(str(candidate))
        return '\n'.join(found)

    def cmd_bc(self, args: Optional[List[str]] = None) -> str:
        """
        A calculator.

        Takes an expression on the command line rather than reading a
        session, because this terminal has no way to feed it one.
        """
        expression = ' '.join(args or []) or getattr(self, '_pipe_input', '')
        expression = expression.strip()
        if not expression:
            return "bc: usage: bc <expression>"
        if not all(c in '0123456789+-*/%()^. \t\n' for c in expression):
            return "bc: syntax error"
        try:
            value = eval(  # noqa: S307 - the character set above is the guard
                expression.replace('^', '**'), {'__builtins__': {}}, {})
        except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
            return "bc: syntax error"
        return str(int(value) if float(value).is_integer() else value)

    def cmd_units(self, args: Optional[List[str]] = None) -> str:
        """
        Convert between units, including the ones this plant is measured in.
        """
        table = {
            ('mile', 'kft'): 5.28, ('kft', 'mile'): 1 / 5.28,
            ('mile', 'foot'): 5280.0, ('foot', 'mile'): 1 / 5280,
            ('mile', 'km'): 1.609344, ('km', 'mile'): 1 / 1.609344,
            ('inch', 'cm'): 2.54, ('cm', 'inch'): 1 / 2.54,
            ('pound', 'kg'): 0.45359237, ('kg', 'pound'): 1 / 0.45359237,
        }
        args = args or []
        if len(args) < 3:
            return ("units: usage: units <number> <from> <to>\n"
                    "known: " + ', '.join(sorted({u for pair in table
                                                  for u in pair})))
        try:
            amount = float(args[0])
        except ValueError:
            return "units: conformability"
        factor = table.get((args[1].lower().rstrip('s'),
                            args[2].lower().rstrip('s')))
        if factor is None:
            return "units: conformability"
        return f"\t* {amount * factor:g}\n\t/ {amount / factor:g}"

    def cmd_sleep(self, args: Optional[List[str]] = None) -> str:
        """
        Wait.

        Nothing here actually blocks the terminal; the shift clock is what
        time means in this simulation, so sleep charges it and says so.
        """
        args = args or []
        try:
            seconds = int(args[0]) if args else 1
        except ValueError:
            return "sleep: bad time"
        minutes = max(1, seconds // 60)
        self.shift_minutes += minutes
        return ''

    def cmd_mesg(self, args: Optional[List[str]] = None) -> str:
        """Permit or deny messages from write(1)."""
        args = args or []
        if not args:
            return 'is y' if self.settings.is_on('game.ambience') else 'is n'
        if args[0] == 'n':
            self.settings.set('game.ambience', 'off')
            return ''
        if args[0] == 'y':
            self.settings.set('game.ambience', 'on')
            return ''
        return "mesg: usage: mesg [y|n]"

    def cmd_wall(self, args: Optional[List[str]] = None) -> str:
        """Write to everybody logged on."""
        message = ' '.join(args or [])
        if not message:
            return "wall: usage: wall <message>"
        stamp = self.clock.log_stamp()
        replies = {
            'rjohnson': 'Heard.',
            'gvasquez': 'Heard you.',
            'mreyes': 'Some of us are on the telephone, you know.',
            'ehalloran': 'Use write(1) unless it is an emergency.',
        }
        who, reply = random.choice(list(replies.items()))
        return (f"Broadcast Message from {self.username} tty01 [{stamp}]...\n"
                f"{message}\n\n"
                f"Message from {who} tty02 [{stamp}]...\n{reply}\nEOT")

    def cmd_passwd(self, args: Optional[List[str]] = None) -> str:
        """Change the login password."""
        return ("Changing password for " + (self.username or 'sysop') + "\n"
                "Old password:\n"
                "passwd: this terminal cannot read a password without echo,\n"
                "so nothing was changed. The account has no password anyway -\n"
                "see /etc/passwd, where the second field is empty for every\n"
                "login on this machine. It was 1983.")

    def cmd_stty(self, args: Optional[List[str]] = None) -> str:
        """Set or report terminal options."""
        args = args or []
        if args and args[0] == 'everything':
            return ("speed 300 baud; -parity hupcl\n"
                    "erase = '^h'; kill = '^u'; intr = '^?'; eof = '^d'\n"
                    "even odd -raw -nl echo -lcase tabs")
        if args:
            return ''
        return "speed 300 baud; erase = '^h'; kill = '^u'"
