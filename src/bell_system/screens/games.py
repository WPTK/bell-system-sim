"""
Section 6 of the manual, and the things people left lying around.

The Seventh Edition shipped with games, and a working machine had people's
half-finished business on it. Both are here for the same reason: a system you
only ever use for work does not feel like a system anybody lived on.

bcd(6) and ppt(6) are real Seventh Edition commands that print their argument
as a punched card and as punched paper tape. factor, primes, arithmetic and
moo were all in section 6 too. Nothing here needs any telephony.
"""

import random
from typing import Dict, List, Optional, Tuple

from .session import SessionState

# Column punches for bcd(6). A card has twelve rows: two zone rows above
# the digits, then zero through nine. An IBM 026 keypunch encoded letters as
# a zone plus a digit - A to I on the 12 zone, J to R on the 11 zone, S to Z
# on the 0 zone - and digits as a single punch in their own row.
_BCD_ROWS = ('12', '11', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')

_BCD_PUNCH: Dict[str, Tuple[str, ...]] = {}
for _index, _letter in enumerate('ABCDEFGHI', start=1):
    _BCD_PUNCH[_letter] = ('12', str(_index))
for _index, _letter in enumerate('JKLMNOPQR', start=1):
    _BCD_PUNCH[_letter] = ('11', str(_index))
for _index, _letter in enumerate('STUVWXYZ', start=2):
    _BCD_PUNCH[_letter] = ('0', str(_index))
for _digit in '0123456789':
    _BCD_PUNCH[_digit] = (_digit,)
_BCD_PUNCH.update({
    ' ': (), '-': ('11',), '&': ('12',), '.': ('12', '3', '8'),
    ',': ('0', '3', '8'), '/': ('0', '1'), '#': ('3', '8'),
})


class GameCommands(SessionState):
    """
    Section 6 commands.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    def cmd_fortune(self, args: Optional[List[str]] = None) -> str:
        """Print a random adage from /usr/games/fortunes."""
        text = self._read('/usr/games/fortunes')
        if not text:
            return "fortune: cannot open fortunes file"
        sayings = [block.strip() for block in text.split('\n\n')
                   if block.strip()]
        return random.choice(sayings) if sayings else "fortune: no fortunes"

    def cmd_bcd(self, args: Optional[List[str]] = None) -> str:
        """
        Print its argument as a punched card.

        A real Seventh Edition command, and the plainest reminder of what
        this machine's ancestors read their programs from.
        """
        text = (' '.join(args or []) or
                getattr(self, '_pipe_input', '').strip())[:48].upper()
        if not text:
            return "bcd: usage: bcd text"

        width = len(text)
        rows = [' ' + ' '.join(text) + ' ',
                '/' + '-' * (width * 2 + 1)]
        for row in _BCD_ROWS:
            line = '|'
            for character in text:
                punched = row in _BCD_PUNCH.get(character, ())
                line += ' ]' if punched else '  '
            rows.append(line + ' |')
        rows.append('|' + ' ' * (width * 2 + 1) + '|')
        rows.append('+' + '-' * (width * 2 + 1))
        return '\n'.join(rows)

    def cmd_ppt(self, args: Optional[List[str]] = None) -> str:
        """Print its argument as punched paper tape."""
        text = (' '.join(args or []) or
                getattr(self, '_pipe_input', '').strip())[:60]
        if not text:
            return "ppt: usage: ppt text"
        rows = ['_' * (len(text) + 2)]
        for bit in range(7, -1, -1):
            line = '|'
            for character in text:
                if bit == 2:
                    line += '.'
                    continue
                line += 'o' if (ord(character) >> bit) & 1 else ' '
            rows.append(line + '|')
        rows.append('|' + '_' * len(text) + '|')
        return '\n'.join(rows)

    def cmd_arithmetic(self, args: Optional[List[str]] = None) -> str:
        """
        Pose an arithmetic problem, the way the drill program did.

        The terminal takes one line at a time, so this asks and gives the
        answer rather than waiting for one.
        """
        left, right = random.randint(2, 99), random.randint(2, 99)
        operator = random.choice('+-*')
        answer = {'+': left + right, '-': left - right,
                  '*': left * right}[operator]
        return f"{left} {operator} {right} = {answer}"

    def cmd_moo(self, args: Optional[List[str]] = None) -> str:
        """
        Bulls and cows, guessed one line at a time.

        ``moo`` starts a game, ``moo <four digits>`` guesses. The number has
        four different digits.
        """
        args = args or []
        secret: Optional[str] = getattr(self, '_moo_secret', None)

        if not args:
            digits = random.sample('123456789', 4)
            self._moo_secret: Optional[str] = ''.join(digits)
            self._moo_guesses = 0
            return ("New game. I have a four digit number, all digits\n"
                    "different. Guess with 'moo 1234'.\n"
                    "A bull is a right digit in the right place, a cow is a\n"
                    "right digit in the wrong place.")

        if secret is None:
            return "moo: no game in progress. Type 'moo' to start one."

        guess = args[0]
        if len(guess) != 4 or not guess.isdigit():
            return "moo: guess four digits"

        bulls = sum(1 for a, b in zip(guess, secret) if a == b)
        cows = sum(1 for d in set(guess) if d in secret) - bulls
        self._moo_guesses = getattr(self, '_moo_guesses', 0) + 1

        if bulls == 4:
            count = self._moo_guesses
            self._moo_secret = None
            return f"{guess}: 4 bulls. Got it in {count}."
        return f"{guess}: {bulls} bulls, {cows} cows"

    def cmd_readnews(self, args: Optional[List[str]] = None) -> str:
        """
        Read netnews.

        The machine takes a nightly feed over uucp. Articles live under
        /usr/spool/news, one file to an article, so cat(1) and grep(1) work
        on them as well.
        """
        args = args or []
        spool = '/usr/spool/news'
        articles = sorted(
            path for path in self.filesystem
            if path.startswith(spool + '/') and not self.filesystem[path].is_dir)
        if not articles:
            return "readnews: no news is good news."

        if args and args[0] == '-n' and len(args) > 1:
            wanted = args[1]
            picked = [a for a in articles if wanted in a]
            if not picked:
                return f"readnews: no articles in {wanted}"
            articles = picked
        elif args and args[0].isdigit():
            index = int(args[0]) - 1
            if not 0 <= index < len(articles):
                return f"readnews: no article {args[0]}"
            return self._read(articles[index]) or ''

        rows = [f"{len(articles)} articles waiting, fed nightly over uucp.",
                '']
        for number, path in enumerate(articles, 1):
            body = self._read(path) or ''
            subject = next((line[9:] for line in body.split('\n')
                            if line.startswith('Subject: ')), path)
            group = path[len(spool) + 1:].split('/')[0]
            rows.append(f"{number:>3}  {group:<18}{subject}")
        rows.extend(['', "readnews <n> to read one, readnews -n <group> to "
                         "pick a group."])
        return '\n'.join(rows)
