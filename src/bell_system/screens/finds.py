"""
Finds: the files worth reading, and a list of the ones you have read.

The machine holds a story (data/finds.py) in files you reach with ls, cat and
grep. Reading one of them is all it takes to find it: the shell notes the read
(``_note_read``, called wherever a command has put a file's text in front of
the player), and ``finds`` is the list of what has been turned up, by the
number each has always had.

Nothing here tells the player a file exists. A find that has not been read is
not on the list, its title is not printed, and the numbers that are missing
are the only trace of it.
"""

from typing import List, Optional

from ..data.finds import FRAGMENTS, FRAGMENTS_BY_KEY, FRAGMENTS_BY_PATH
from ..filesystem import Node, fragment_node, normalise
from .session import SessionState

# Said once, after the first file in the career that turns out to be a find.
# The command is the only thing it names.
FIRST_FIND = "[Noted. 'finds' lists what you have turned up.]"


class FindsCommands(SessionState):
    """
    Recording what has been read, bringing in files on their tour, and the
    ``finds`` command.

    Mixed into :class:`~bell_system.screens.shell.ShellCommands`, whose
    reading commands are what call ``_note_read``.
    """

    # Set when the first find is made, and said by the REPL after the output
    # of the command that made it (take_find_notice).
    _find_pending: str = ''

    def _note_read(self, path: str) -> None:
        """
        Record that a file has been put in front of the player.

        Args:
            path: The file as typed or already resolved; it is resolved
                against the working directory either way
        """
        fragment = FRAGMENTS_BY_PATH.get(normalise(path, self.current_directory))
        if fragment is not None:
            self.note_find(fragment.key)

    def note_find(self, key: str) -> None:
        """Record a find by its key, once, and keep the career."""
        if key not in FRAGMENTS_BY_KEY or key in self.career.finds:
            return
        first = not self.career.finds
        self.career.finds.append(key)
        self.career.save()
        if first:
            self._find_pending = FIRST_FIND

    def take_find_notice(self) -> str:
        """
        Return the one-time note, once, when the first find has been made.

        The REPL asks for it after it has printed a command's output, so it
        is said on the screen and never in the output: not in a file the
        output was sent to, not fed to the next stage of a pipeline, and not
        counted by head. Nothing else calls it.
        """
        notice, self._find_pending = self._find_pending, ''
        return notice

    def deliver_fragments(self) -> None:
        """
        Put the files that have arrived by this tour on the machine.

        A file that was there from the first tour is in the tree already.
        The rest turn up on their tour and stay, the way netnews does
        (``deliver_news``), so that a grep on tour 2 and a grep on tour 9 do
        not find the same things. Safe to call again.
        """
        for fragment in FRAGMENTS:
            if (fragment.text is None or fragment.tour > self.career.shift
                    or fragment.path in self.filesystem):
                continue
            parent = fragment.path.rsplit('/', 1)[0]
            while parent and parent not in self.filesystem:
                self.filesystem[parent] = Node(
                    'dir', fragment.owner or 'root',
                    fragment.group or 'other', 'drwxr-xr-x')
                parent = parent.rsplit('/', 1)[0]
            self.filesystem[fragment.path] = fragment_node(fragment)

    def cmd_finds(self, args: Optional[List[str]] = None) -> str:
        """
        List what has been turned up, by number.

        ``finds <n>`` says where number n was found.
        """
        args = args or []
        found = [FRAGMENTS_BY_KEY[key] for key in self.career.finds
                 if key in FRAGMENTS_BY_KEY]
        numbers = {fragment.key: number
                   for number, fragment in enumerate(FRAGMENTS, 1)}

        if args:
            if not args[0].isdecimal():
                return "finds: usage: finds [number]"
            for fragment in found:
                if numbers[fragment.key] == int(args[0]):
                    return f"{args[0]:>3}  {fragment.title}\n     {fragment.path}"
            return f"finds: {args[0]}: nothing found under that number"

        if not found:
            return "Nothing found yet."
        rows = [f"Found so far: {len(found)}", '']
        for fragment in sorted(found, key=lambda held: numbers[held.key]):
            rows.append(f"{numbers[fragment.key]:>3}  {fragment.title}")
        return '\n'.join(rows)
