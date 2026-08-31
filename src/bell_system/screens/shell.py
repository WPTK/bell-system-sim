"""
The shell: moving around, reading things, and joining commands with pipes.

None of this existed. There was an ``ls`` that printed a directory's claimed
contents and a ``pwd`` that printed a string, and no way to go anywhere or
read anything. Sitting at a Seventh Edition machine is most of what this
simulation is for, so these are the commands that make it a machine rather
than a menu.

Everything here is Seventh Edition behaviour where it can be. ``cat`` takes
several files, ``grep`` takes a pattern and reads standard input when given no
file, ``wc`` prints lines, words and characters in that order, ``head`` and
``tail`` default to ten lines, and a pipeline feeds one command's output into
the next.
"""

from typing import List, Optional

from ..filesystem import Node, children, normalise
from .session import SessionState


class ShellCommands(SessionState):
    """
    Navigation, file reading and text handling.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`, which owns
    the working directory and the filesystem.
    """

    # -- helpers ---------------------------------------------------------

    def _node(self, path: str) -> Optional[Node]:
        """Return the filesystem entry at a path, or None."""
        return self.filesystem.get(normalise(path, self.current_directory))

    def _read(self, path: str) -> Optional[str]:
        """
        Return a file's text.

        Content may be a callable, so a file can render live state - the
        line records under /usr/lmos are the reports actually on the board.
        """
        node = self._node(path)
        if node is None or node.is_dir:
            return None
        content = node.content
        if callable(content):
            return content(self)
        return content or ''

    def _gather(self, args: List[str], command: str) -> tuple:
        """
        Return (text, error) for commands that read files or standard input.

        With no file arguments a command reads what the previous stage of the
        pipeline produced, which is what makes a pipeline work.
        """
        files = [a for a in args if not a.startswith('-')]
        if not files:
            return getattr(self, '_pipe_input', '') or '', None
        chunks = []
        for name in files:
            text = self._read(name)
            if text is None:
                node = self._node(name)
                if node is not None and node.is_dir:
                    return None, f"{command}: {name}: is a directory"
                return None, f"{command}: {name}: no such file or directory"
            chunks.append(text)
        return ''.join(chunks), None

    # -- moving around ---------------------------------------------------

    def cmd_cd(self, args: Optional[List[str]] = None) -> str:
        """Change the working directory."""
        args = args or []
        target = args[0] if args else '/usr/users/sysop'
        path = normalise(target, self.current_directory)
        node = self.filesystem.get(path)
        if node is None:
            return f"cd: {target}: no such file or directory"
        if not node.is_dir:
            return f"cd: {target}: not a directory"
        self.current_directory = path
        return ''

    def cmd_pwd(self, args: Optional[List[str]] = None) -> str:
        """Print the working directory."""
        return self.current_directory

    def cmd_ls(self, args: Optional[List[str]] = None) -> str:
        """
        List directory contents.

        ``-l`` gives the long form, ``-a`` includes dot files.
        """
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        targets = [a for a in args if not a.startswith('-')] or ['.']

        blocks = []
        for target in targets:
            path = normalise(target, self.current_directory)
            node = self.filesystem.get(path)
            if node is None:
                blocks.append(f"ls: {target}: no such file or directory")
                continue

            if not node.is_dir:
                names, base = [path.rsplit('/', 1)[-1]], path.rsplit('/', 1)[0]
            else:
                names = children(path, self.filesystem)
                base = path
            if 'a' not in flags:
                names = [n for n in names if not n.startswith('.')]

            if 'l' not in flags:
                # Down a pipe, ls prints one entry to a line, which is what
                # makes ls | grep work. To a terminal it columnates.
                joiner = '\n' if getattr(self, '_in_pipeline', False) else '  '
                blocks.append(joiner.join(names) if names else '')
                continue

            rows = []
            for name in names:
                child = self.filesystem.get(normalise(name, base))
                if child is None:
                    continue
                size = (len(child.content) if isinstance(child.content, str)
                        else 512 if child.is_dir else 0)
                rows.append(f"{child.mode} 1 {child.owner:<9} {child.group:<7} "
                            f"{size:>6} Nov 14 08:00 {name}")
            blocks.append('\n'.join(rows))

        header = len(targets) > 1
        if not header:
            return '\n'.join(b for b in blocks if b is not None)
        return '\n\n'.join(f"{t}:\n{b}" for t, b in zip(targets, blocks))

    # -- reading ---------------------------------------------------------

    def cmd_cat(self, args: Optional[List[str]] = None) -> str:
        """Concatenate and print files."""
        text, error = self._gather(args or [], 'cat')
        return error if error else text.rstrip('\n')

    def cmd_more(self, args: Optional[List[str]] = None) -> str:
        """
        Print a file a screen at a time.

        There is no interactive pager here: the terminal this runs in scrolls
        on its own, so more(1) prints the file and says how long it was.
        """
        text, error = self._gather(args or [], 'more')
        if error:
            return error
        lines = text.rstrip('\n').split('\n')
        if len(lines) <= 23:
            return '\n'.join(lines)
        return ('\n'.join(lines[:23])
                + f"\n--More--({len(lines) - 23} more lines; "
                  f"cat(1) prints the rest)")

    def cmd_head(self, args: Optional[List[str]] = None) -> str:
        """Print the first lines of a file."""
        args = args or []
        count = 10
        for arg in args:
            if arg.startswith('-') and arg[1:].isdigit():
                count = int(arg[1:])
        text, error = self._gather(args, 'head')
        if error:
            return error
        return '\n'.join(text.rstrip('\n').split('\n')[:count])

    def cmd_tail(self, args: Optional[List[str]] = None) -> str:
        """Print the last lines of a file."""
        args = args or []
        count = 10
        for arg in args:
            if arg.startswith('-') and arg[1:].isdigit():
                count = int(arg[1:])
        text, error = self._gather(args, 'tail')
        if error:
            return error
        return '\n'.join(text.rstrip('\n').split('\n')[-count:])

    def cmd_file(self, args: Optional[List[str]] = None) -> str:
        """Say what kind of thing each argument is."""
        args = args or []
        if not args:
            return "file: usage: file <name>..."
        rows = []
        for name in args:
            node = self._node(name)
            if node is None:
                rows.append(f"{name}: cannot open")
            elif node.is_dir:
                rows.append(f"{name}: directory")
            elif name.endswith('.c'):
                rows.append(f"{name}: c program text")
            elif node.mode.startswith(('c', 'b')):
                rows.append(f"{name}: special file")
            elif 'x' in node.mode:
                rows.append(f"{name}: executable")
            elif not node.content:
                rows.append(f"{name}: empty")
            else:
                rows.append(f"{name}: ascii text")
        return '\n'.join(rows)

    # -- text handling ---------------------------------------------------

    def cmd_grep(self, args: Optional[List[str]] = None) -> str:
        """
        Print lines matching a pattern.

        ``-i`` ignores case, ``-n`` numbers the lines, ``-v`` inverts the
        match, ``-c`` counts instead of printing.
        """
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        rest = [a for a in args if not a.startswith('-')]
        if not rest:
            return "grep: usage: grep [-inv] pattern [file]..."

        pattern, files = rest[0], rest[1:]
        text, error = self._gather(files, 'grep')
        if error:
            return error

        needle = pattern.lower() if 'i' in flags else pattern
        found = []
        for number, line in enumerate(text.rstrip('\n').split('\n'), 1):
            subject = line.lower() if 'i' in flags else line
            hit = needle in subject
            if hit == ('v' not in flags):
                found.append(f"{number}:{line}" if 'n' in flags else line)

        if 'c' in flags:
            return str(len(found))
        return '\n'.join(found)

    def cmd_wc(self, args: Optional[List[str]] = None) -> str:
        """Count lines, words and characters."""
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        text, error = self._gather(args, 'wc')
        if error:
            return error
        body = text.rstrip('\n')
        lines = len(body.split('\n')) if body else 0
        words = len(body.split())
        chars = len(text)
        if flags:
            picked = []
            if 'l' in flags:
                picked.append(lines)
            if 'w' in flags:
                picked.append(words)
            if 'c' in flags:
                picked.append(chars)
            return ' '.join(f"{n:>7}" for n in picked).strip()
        return f"{lines:>7}{words:>8}{chars:>8}"

    def cmd_sort(self, args: Optional[List[str]] = None) -> str:
        """Sort lines. ``-r`` reverses, ``-u`` drops duplicates."""
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        text, error = self._gather(args, 'sort')
        if error:
            return error
        lines = text.rstrip('\n').split('\n') if text.strip() else []
        if 'u' in flags:
            lines = sorted(set(lines))
        lines = sorted(lines, reverse='r' in flags)
        return '\n'.join(lines)

    def cmd_uniq(self, args: Optional[List[str]] = None) -> str:
        """Drop repeated adjacent lines. ``-c`` prefixes a count."""
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        text, error = self._gather(args, 'uniq')
        if error:
            return error
        out, previous, run = [], None, 0
        for line in text.rstrip('\n').split('\n'):
            if line == previous:
                run += 1
                continue
            if previous is not None:
                out.append(f"{run:>4} {previous}" if 'c' in flags else previous)
            previous, run = line, 1
        if previous is not None:
            out.append(f"{run:>4} {previous}" if 'c' in flags else previous)
        return '\n'.join(out)

    def cmd_echo(self, args: Optional[List[str]] = None) -> str:
        """Write its arguments."""
        return ' '.join(args or [])

    def cmd_cal(self, args: Optional[List[str]] = None) -> str:
        """
        Print a calendar for the simulated month.

        The Bell System has forty-eight days left when the shift starts, and
        a calendar is the plainest way to see that.
        """
        import calendar

        now = self.clock.now()
        args = args or []
        try:
            month = int(args[0]) if args else now.month
            year = int(args[1]) if len(args) > 1 else now.year
        except ValueError:
            return "cal: usage: cal [month [year]]"
        if not 1 <= month <= 12:
            return "cal: bad month"

        text = calendar.TextCalendar(calendar.SUNDAY).formatmonth(year, month)
        if (year, month) == (1983, 12):
            text += "\n  The Bell System is dissolved on 1 January 1984.\n"
        return text.rstrip('\n')
