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

import fnmatch
from datetime import datetime, timedelta
from typing import FrozenSet, List, Optional

from ..data.finds import GROUP_FOR_SIGN_OFF, groups_for
from ..filesystem import (
    GROUP,
    PLAYER_LIMIT,
    Node,
    children,
    is_player_path,
    normalise,
)
from ..save import home_size
from .finds import FindsCommands

# How many sign-offs the wire chief wants behind somebody before he puts
# them in the group that owns /usr/adm/sulog. The simulation's own figure:
# it is the third, which is the one he says he notices. The ladder of
# groups it belongs to is data/finds.py GROUP_FOR_SIGN_OFF.
ADM_GROUP_QUALIFICATIONS = 3

# The first morning of the game, which the career counts group grants from.
GRANT_EPOCH = datetime(1983, 11, 14)

SULOG = '/usr/adm/sulog'
DEV_NULL = '/dev/null'
# The su log's last shipped line is Halloran's at 06:15 on the first morning,
# so a grant is never stamped before 06:16 that day or after the last night.
FIRST_GRANT = 6 * 60 + 16
LAST_GRANT = (datetime(1983, 12, 31) - GRANT_EPOCH).days * 1440 + 1439
# Halloran's terminal, which he is on when he puts someone in a group.
CHIEF_LINE = 'tty01'


class ShellCommands(FindsCommands):
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
        Return a file's text, or None if there is none to return.

        Content may be a callable, so a file can render live state - the
        line records under /usr/lmos are the reports actually on the board.

        A file whose mode denies this position also reads as None, and
        callers turn that into a refusal by looking at the mode themselves
        (``_refusal``).

        Reading is not finding: the commands that show a file to the player
        call ``_note_read`` themselves, because ``_read`` is also how the
        machine reads its own files.
        """
        node = self._node(path)
        if node is None or node.is_dir or not self._may_read(path):
            return None
        content = node.content
        if callable(content):
            return content(self)
        return content or ''

    def _may_read(self, path: str) -> bool:
        """
        Return whether this position may read a file.

        The mode column means what it says: anybody reads a file that is
        readable by others, its owner reads it, and a member of its group
        reads it when the group bit is set. The groups are the ones the
        wire chief has put this position in (``_groups``), one more with
        each sign-off, so the files that are shut are the next chapter of
        the story and not the same wall.
        """
        node = self._node(path)
        if node is None:
            return True
        if node.mode[7:8] == 'r' or node.owner == (self.username or 'sysop'):
            return True
        return node.mode[4:5] == 'r' and node.group in self._groups()

    def _groups(self) -> FrozenSet[str]:
        """
        Return which groups this position is in.

        Only what the held sign-offs give (data/finds.py). ``career.groups``
        and ``career.granted`` are a record of when each group was given,
        kept for the su log, and are not a second source of membership: a
        career signed off before they were kept has its groups from the
        first command, and nothing that is written there can add one.
        """
        return groups_for(len(self.career.qualifications))

    def sync_groups(self) -> None:
        """
        Record when each group was given, and put the player in the su log.

        Halloran says the log "has your name in it" when he adds someone to
        adm. This makes it true: one successful su, from his login to the
        player's, at the moment of the third sign-off (narrative bible T5).
        Called when a sign-off is passed and when a position is taken (the
        login is the position). The record is the career's; the log is
        rebuilt every session, and the line is put back once, in its place
        by the clock, and left where it is.
        """
        career = self.career
        held = groups_for(len(career.qualifications))
        minutes = int((self.clock.now() - GRANT_EPOCH).total_seconds() // 60)
        minutes = min(max(minutes, FIRST_GRANT), LAST_GRANT)
        changed = False
        for number in sorted(GROUP_FOR_SIGN_OFF):
            group = GROUP_FOR_SIGN_OFF[number]
            if group in held and group not in career.groups:
                career.groups.append(group)
                career.granted[group] = minutes
                changed = True
        if changed:
            career.save()
        node = self.filesystem.get(SULOG)
        if 'adm' not in career.granted or node is None:
            return
        if not isinstance(node.content, str):
            return
        when = min(max(career.granted['adm'], FIRST_GRANT), LAST_GRANT)
        stamp = (GRANT_EPOCH + timedelta(minutes=when)).strftime('%m/%d %H:%M')
        line = (f"SU {stamp} + {CHIEF_LINE} "
                f"ehalloran-{self.username or 'sysop'}")
        lines = [row for row in node.content.split('\n') if row]
        if line in lines:
            return
        # In its place: the log is in the order things happened.
        place = next((n for n, row in enumerate(lines)
                      if row[3:14] > stamp), len(lines))
        lines.insert(place, line)
        self.filesystem[SULOG] = node._replace(
            content='\n'.join(lines) + '\n')

    def _render_group(self) -> str:
        """Render /etc/group with this position in the groups it holds."""
        mine = self.username or 'sysop'
        rows = []
        for row in GROUP.splitlines():
            name, password, number, members = row.split(':')
            names = members.split(',') if members else []
            if name in self._groups() and mine not in names:
                names.append(mine)
            rows.append(f"{name}:{password}:{number}:{','.join(names)}")
        return '\n'.join(rows) + '\n'

    def _refusal(self, name: str, command: str) -> str:
        """Say why a file could not be read."""
        node = self._node(name)
        if node is not None and node.is_dir:
            return f"{command}: {name}: is a directory"
        if node is not None and not self._may_read(name):
            return f"{command}: {name}: permission denied"
        return f"{command}: {name}: no such file or directory"

    def _operands(self, args: List[str]) -> List[str]:
        """
        Return the files a command was given, with patterns expanded.

        The shell does this and the command never sees the pattern, which
        is why ``grep pwba /usr/adm/*`` reads every file in the directory.
        ``*``, ``?`` and ``[`` match within one name and never across a
        slash, a leading dot has to be typed, and a pattern that matches
        nothing is passed on as typed, as sh did. Only files match:
        a command cannot read a directory.
        """
        base = self.current_directory.rstrip('/') + '/'
        names: List[str] = []
        for arg in args:
            if arg.startswith('-') or not any(c in arg for c in '*?['):
                names.append(arg)
                continue
            wanted = normalise(arg, self.current_directory).split('/')[1:]
            found = []
            for path, node in sorted(self.filesystem.items()):
                parts = path.split('/')[1:]
                if node.is_dir or len(parts) != len(wanted):
                    continue
                if all(fnmatch.fnmatchcase(part, piece)
                       and (piece.startswith('.') or not part.startswith('.'))
                       for part, piece in zip(parts, wanted)):
                    shown = path
                    if not arg.startswith('/') and path.startswith(base):
                        shown = path[len(base):]
                    found.append(shown)
            names.extend(found or [arg])
        return names

    def _gather(self, args: List[str], command: str,
                note: bool = False) -> tuple:
        """
        Return (text, error) for commands that read files or standard input.

        With no file arguments a command reads what the previous stage of the
        pipeline produced, which is what makes a pipeline work. ``note`` is
        for the commands that print the text of what they read: only those
        make a find, and wc, od and sum read a file without reading it.
        """
        files = self._operands([a for a in args if not a.startswith('-')])
        if not files:
            return getattr(self, '_pipe_input', '') or '', None
        chunks = []
        for name in files:
            text = self._read(name)
            if text is None:
                return None, self._refusal(name, command)
            chunks.append(text)
        if note:
            for name in files:
                self._note_read(name)
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
        text, error = self._gather(args or [], 'cat', note=True)
        return error if error else text.rstrip('\n')

    def cmd_more(self, args: Optional[List[str]] = None) -> str:
        """
        Print a file a screen at a time.

        There is no interactive pager here: the terminal this runs in scrolls
        on its own, so more(1) prints the file and says how long it was.
        """
        text, error = self._gather(args or [], 'more', note=True)
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
            if arg.startswith('-') and arg[1:].isdecimal():
                count = int(arg[1:])
        text, error = self._gather(args, 'head', note=True)
        if error:
            return error
        return '\n'.join(text.rstrip('\n').split('\n')[:count])

    def cmd_tail(self, args: Optional[List[str]] = None) -> str:
        """Print the last lines of a file."""
        args = args or []
        count = 10
        for arg in args:
            if arg.startswith('-') and arg[1:].isdecimal():
                count = int(arg[1:])
        text, error = self._gather(args, 'tail', note=True)
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
        match, ``-c`` counts instead of printing, ``-l`` names the files
        that match and ``-h`` leaves the names off. Given more than one
        file, as it is by a pattern like ``/usr/adm/*``, it puts the file's
        name in front of each line, and a file it cannot read costs a line
        of complaint and not the whole search.
        """
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        rest = [a for a in args if not a.startswith('-')]
        if not rest:
            return "grep: usage: grep [-chilnv] pattern [file]..."

        pattern = rest[0]
        needle = pattern.lower() if 'i' in flags else pattern
        names = self._operands(rest[1:])
        if names:
            sources = [(name, self._read(name)) for name in names]
        else:
            sources = [('', getattr(self, '_pipe_input', '') or '')]
        labelled = len(names) > 1 and 'h' not in flags

        found: List[str] = []
        problems: List[str] = []
        for name, text in sources:
            if text is None:
                problems.append(self._refusal(name, 'grep'))
                continue
            hits = []
            for number, line in enumerate(text.rstrip('\n').split('\n'), 1):
                subject = line.lower() if 'i' in flags else line
                if (needle in subject) == ('v' not in flags):
                    hits.append(f"{number}:{line}" if 'n' in flags else line)
            # -c and -l report on a file without showing it.
            if hits and name and not set('cl') & set(flags):
                self._note_read(name)
            label = f"{name}:" if labelled else ''
            if 'l' in flags:
                if hits:
                    found.append(name)
            elif 'c' in flags:
                found.append(f"{label}{len(hits)}")
            else:
                found.extend(f"{label}{hit}" for hit in hits)

        return '\n'.join(found + problems)

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
        text, error = self._gather(args, 'sort', note=True)
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
        text, error = self._gather(args, 'uniq', note=True)
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

    # -- writing ---------------------------------------------------------

    def _writable(self, path: str, command: str) -> Optional[str]:
        """
        Return an error if a path cannot be written, or None if it can.

        The parent has to exist and the target must not already be a
        directory, which is the same pair of conditions the real thing
        enforces.
        """
        node = self.filesystem.get(path)
        if node is not None and node.is_dir:
            return f"{command}: {path}: is a directory"
        parent = path.rsplit('/', 1)[0] or '/'
        holder = self.filesystem.get(parent)
        if holder is None:
            return f"{command}: {parent}: no such directory"
        if not holder.is_dir:
            return f"{command}: {parent}: not a directory"
        return None

    def _owns(self, node: Node) -> bool:
        """
        Return whether this position owns a file.

        chmod, rm and mv act on a file the way its owner may, which keeps a
        file the player can read (and so, by a group, one the next sign-off
        was meant to open) from being made readable by chmod 644 and moved
        or removed out of its turn.
        """
        return node.owner == (self.username or 'sysop')

    def write_file(self, path: str, text: str,
                   append: bool = False) -> Optional[str]:
        """
        Create or replace a file. Returns an error string, or None on success.

        Args:
            path: Where to write, already resolved
            text: What to write
            append: Add to the end rather than replacing
        """
        if path == DEV_NULL:
            return None
        error = self._writable(path, 'sh')
        if error:
            return error
        existing = self.filesystem.get(path)
        if existing is not None and not self._owns(existing):
            return f"sh: {path}: not owner"
        return self.put_file(path, text, append)

    def put_file(self, path: str, text: str,
                 append: bool = False) -> Optional[str]:
        """
        Write a file as the machine does: no owner, no permission.

        write_file is what the player's commands use and is the owner's to
        change; this is for what the simulation itself writes (the moo
        scoreboard), which belongs to somebody else and is changed by play.
        """
        existing = self.filesystem.get(path)
        if append and existing is not None and isinstance(existing.content, str):
            text = existing.content + text
        if existing is None:
            node = Node('file', self.username or 'sysop', 'craft',
                        '-rw-r--r--', text)
        else:
            node = existing._replace(content=text)
        return self.store_node(path, node, 'sh')

    def store_node(self, path: str, node: Node,
                   command: str = 'sh') -> Optional[str]:
        """
        Put a node in the tree, unless it would not fit in a saved home.

        Every command that adds to the player's files comes through here, so
        the limit is kept in one place and by one measure (save.home_size):
        a file made by mv or cc or mkdir counts the same as one made by echo.

        Returns:
            An error string if the node was refused, else None
        """
        held = self.filesystem.get(path)
        self.filesystem[path] = node
        if is_player_path(path) and home_size(self.filesystem) > PLAYER_LIMIT:
            if held is None:
                del self.filesystem[path]
            else:
                self.filesystem[path] = held
            return (f"{command}: {path}: no space left on device "
                    f"(your files may hold {PLAYER_LIMIT // 1024} KB)")
        return None

    def cmd_mkdir(self, args: Optional[List[str]] = None) -> str:
        """Make directories."""
        args = args or []
        if not args:
            return "mkdir: usage: mkdir directory ..."
        problems = []
        for name in args:
            path = normalise(name, self.current_directory)
            if path in self.filesystem:
                problems.append(f"mkdir: {name}: file exists")
                continue
            parent = path.rsplit('/', 1)[0] or '/'
            if parent not in self.filesystem:
                problems.append(f"mkdir: {name}: no such file or directory")
                continue
            error = self.store_node(path, Node(
                'dir', self.username or 'sysop', 'craft', 'drwxr-xr-x'),
                'mkdir')
            if error:
                problems.append(error)
        return '\n'.join(problems)

    def cmd_rmdir(self, args: Optional[List[str]] = None) -> str:
        """Remove empty directories."""
        args = args or []
        if not args:
            return "rmdir: usage: rmdir directory ..."
        problems = []
        for name in args:
            path = normalise(name, self.current_directory)
            node = self.filesystem.get(path)
            if node is None:
                problems.append(f"rmdir: {name}: no such file or directory")
            elif not node.is_dir:
                problems.append(f"rmdir: {name}: not a directory")
            elif children(path, self.filesystem):
                problems.append(f"rmdir: {name}: directory not empty")
            else:
                del self.filesystem[path]
        return '\n'.join(problems)

    def cmd_rm(self, args: Optional[List[str]] = None) -> str:
        """Remove files. ``-r`` removes a directory and everything under it."""
        args = args or []
        flags = ''.join(a[1:] for a in args if a.startswith('-'))
        names = [a for a in args if not a.startswith('-')]
        if not names:
            return "rm: usage: rm [-r] file ..."
        problems = []
        for name in names:
            path = normalise(name, self.current_directory)
            node = self.filesystem.get(path)
            if node is None:
                problems.append(f"rm: {name}: no such file or directory")
                continue
            if not self._owns(node):
                problems.append(f"rm: {name}: permission denied")
                continue
            if node.is_dir:
                if 'r' not in flags:
                    problems.append(f"rm: {name}: is a directory")
                    continue
                doomed = [p for p in self.filesystem
                          if p == path or p.startswith(path + '/')]
                if not all(self._owns(self.filesystem[v]) for v in doomed):
                    problems.append(f"rm: {name}: permission denied")
                    continue
                for victim in doomed:
                    del self.filesystem[victim]
                continue
            del self.filesystem[path]
        return '\n'.join(problems)

    def cmd_cp(self, args: Optional[List[str]] = None) -> str:
        """Copy a file."""
        args = args or []
        if len(args) < 2:
            return "cp: usage: cp source target"
        text = self._read(args[0])
        if text is None:
            return f"cp: {args[0]}: cannot open"
        target = normalise(args[1], self.current_directory)
        if target in self.filesystem and self.filesystem[target].is_dir:
            target = f"{target}/{args[0].rsplit('/', 1)[-1]}"
        return self.write_file(target, text) or ''

    def cmd_mv(self, args: Optional[List[str]] = None) -> str:
        """Move or rename a file."""
        args = args or []
        if len(args) < 2:
            return "mv: usage: mv source target"
        source = normalise(args[0], self.current_directory)
        node = self.filesystem.get(source)
        if node is None:
            return f"mv: {args[0]}: cannot access"
        if not self._owns(node):
            return f"mv: {args[0]}: permission denied"
        target = normalise(args[1], self.current_directory)
        if target in self.filesystem and self.filesystem[target].is_dir:
            target = f"{target}/{source.rsplit('/', 1)[-1]}"
        error = self._writable(target, 'mv')
        if error:
            return error
        held = self.filesystem.get(target)
        if held is not None and not self._owns(held):
            return f"mv: {target}: not owner"
        del self.filesystem[source]
        error = self.store_node(target, node, 'mv')
        if error:
            self.filesystem[source] = node
            return error
        return ''

    def cmd_touch(self, args: Optional[List[str]] = None) -> str:
        """Create a file if it does not exist."""
        args = args or []
        if not args:
            return "touch: usage: touch file ..."
        for name in args:
            path = normalise(name, self.current_directory)
            if path not in self.filesystem:
                error = self.write_file(path, '')
                if error:
                    return error
        return ''

    def cmd_chmod(self, args: Optional[List[str]] = None) -> str:
        """
        Change a file's mode.

        Takes the octal form, and only on a file the position owns. The mode
        is what decides who may read it (``_may_read``), so a mode that
        anybody could change would open the whole of the machine at once.
        """
        args = args or []
        if len(args) < 2:
            return "chmod: usage: chmod mode file ..."
        octal = args[0]
        if not (octal.isdecimal() and len(octal) in (3, 4)):
            return f"chmod: {octal}: bad mode"
        bits = octal[-3:]
        letters = ''.join(
            ('r' if int(d) & 4 else '-') + ('w' if int(d) & 2 else '-')
            + ('x' if int(d) & 1 else '-') for d in bits)
        problems = []
        for name in args[1:]:
            path = normalise(name, self.current_directory)
            node = self.filesystem.get(path)
            if node is None:
                problems.append(f"chmod: {name}: cannot access")
                continue
            if not self._owns(node):
                problems.append(f"chmod: {name}: not owner")
                continue
            head = 'd' if node.is_dir else '-'
            error = self.store_node(
                path, node._replace(mode=head + letters), 'chmod')
            if error:
                problems.append(error)
        return '\n'.join(problems)

    def cmd_du(self, args: Optional[List[str]] = None) -> str:
        """Report space used, in 512-byte blocks as V7 did."""
        args = args or []
        names = [a for a in args if not a.startswith('-')] or ['.']
        rows = []
        for name in names:
            base = normalise(name, self.current_directory)
            if base not in self.filesystem:
                rows.append(f"du: {name}: cannot access")
                continue
            total = 0
            for path, node in self.filesystem.items():
                if path != base and not path.startswith(base.rstrip('/') + '/'):
                    continue
                size = (len(node.content) if isinstance(node.content, str)
                        else 512 if node.is_dir else 0)
                total += max(1, (size + 511) // 512)
            rows.append(f"{total}\t{base}")
        return '\n'.join(rows)

    def cmd_find(self, args: Optional[List[str]] = None) -> str:
        """
        Walk a directory tree.

        Supports ``-name`` and ``-type f`` or ``-type d``, which is most of
        what find gets used for.
        """
        args = args or []
        start = normalise(args[0] if args and not args[0].startswith('-')
                          else '.', self.current_directory)
        pattern = kind = None
        for index, arg in enumerate(args):
            if arg == '-name' and index + 1 < len(args):
                pattern = args[index + 1].strip('"\'*')
            if arg == '-type' and index + 1 < len(args):
                kind = args[index + 1]

        found = []
        for path, node in sorted(self.filesystem.items()):
            if path != start and not path.startswith(start.rstrip('/') + '/'):
                continue
            if kind == 'f' and node.is_dir:
                continue
            if kind == 'd' and not node.is_dir:
                continue
            if pattern and pattern not in path.rsplit('/', 1)[-1]:
                continue
            found.append(path)
        return '\n'.join(found)

    def cmd_tty(self, args: Optional[List[str]] = None) -> str:
        """Print the terminal name."""
        return '/dev/tty01'

    def cmd_sync(self, args: Optional[List[str]] = None) -> str:
        """Flush the buffer cache. Prints nothing, as it should."""
        return ''

    def run_profile(self) -> str:
        """
        Run the .profile in the home directory, the way login does.

        The Bourne shell reads .profile once when you log in and not again.
        This is the same: assignments and exports are noted rather than
        obeyed, because there are no shell variables here to hold them, and
        anything that is an actual command is run.

        It is the reason each position starts by showing you something
        different. The switching desk opens with its alarms because whoever
        sat there put that line in their profile.
        """
        text = self._read(f"{self.current_directory}/.profile")
        if text is None:
            return ''
        outputs: List[str] = []
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            first = stripped.split()[0]
            if '=' in first and not first.startswith(('echo', 'stty')):
                continue
            if first in ('export', 'stty', 'umask'):
                continue
            produced = self.execute_command(stripped)
            if produced.strip():
                outputs.append(produced.rstrip())
        return '\n'.join(outputs)
