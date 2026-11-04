"""
career(1): the record, and starting the next one.

``career`` with nothing after it is ``qual``, as it always was. ``career new``
is the one thing it adds: it closes a finished career, files its record away
and leaves a handover for whoever starts next (``bell_system.legacy``).

It is the only command that moves a save file, so it is slow on purpose. It
works on a finished career only, shows what it will do first, and does
nothing until the player types ``career new confirm``. Nothing is deleted:
the career's files are moved into an archive directory beside them.
"""

import os
from typing import List, Optional

from .. import legacy
from ..filesystem import player_changes
from ..settings import state_dir
from .session import SessionState


class CareerCommands(SessionState):
    """The career command."""

    def cmd_career(self, args: Optional[List[str]] = None) -> str:
        """Show the craft record, or close a finished career with 'new'."""
        args = args or []
        if not args or args[0].lower() != 'new':
            return self.cmd_qual(args)
        if not self.career.finished:
            return ("Your career is still open. 'career new' closes a "
                    "career that has been signed off\nat the last tour, "
                    "and starts the next from a first tour.")
        if self._career_filed:
            return ("This career has been filed. Start the game again to "
                    "begin the next one.")
        if args[1:] != ['confirm']:
            return self._career_new_plan()
        return self._career_new()

    def _handed_on(self) -> legacy.Legacy:
        """What the career would leave for the next one."""
        state = state_dir()
        generation = legacy.generation_of(state)
        changed, _removed = player_changes(self.filesystem)
        return legacy.Legacy(
            generation, legacy.handover_note(self.career, generation),
            legacy.carried(changed))

    def _career_new_plan(self) -> str:
        """What 'career new confirm' would do, said before it does it."""
        handed = self._handed_on()
        career = self.career
        files = sum(1 for content in handed.files.values()
                    if content is not None)
        where, _number = legacy.next_archive(state_dir())
        return '\n'.join([
            f"Career {handed.generation} is finished: {career.shift} tours,"
            f" {career.reports_closed} report"
            f"{'' if career.reports_closed == 1 else 's'} closed, audit "
            f"{(career.audit_verdict or 'not recorded').lower()}.",
            "",
            "Starting the next one will:",
            f"  - file this career's record in {where}",
            "    (moved there, not deleted; you can put it back by hand)",
            "  - leave a handover note and "
            f"{files} of your files in {legacy.PRIOR}/",
            "    for the next holder of the desk, who will not know whose",
            "  - end this session; run the game again for tour 1",
            "",
            "Type 'career new confirm' to go ahead. Nothing has been moved.",
        ])

    def _career_new(self) -> str:
        """Close the finished career: file it, hand on, and retire it."""
        state = state_dir()
        handed = self._handed_on()
        # This process stops owning the career before a file is moved, so
        # that an interrupt part of the way through cannot have it write
        # the files back next to the archive. Undone only if the move is.
        held = (self.career.path, self.shift_file, self._home_locked,
                self._career_filed)
        self.career.path = None
        self.shift_file = ''
        self._home_locked = True
        self._career_filed = True
        where, _number = legacy.next_archive(state)
        moved: List[str] = []
        try:
            legacy.set_aside(state, where, moved)
            legacy.write(legacy.legacy_path(state), handed)
        except BaseException as error:
            stuck = legacy.put_back(state, where, moved)
            if not stuck:
                (self.career.path, self.shift_file, self._home_locked,
                 self._career_filed) = held
            if not isinstance(error, OSError):
                raise
            why = error.strerror or str(error)
            if stuck:
                return (f"The career could not be filed ({why}), and "
                        f"{', '.join(stuck)} could not be moved back. "
                        f"They are in {where}. Put them back by hand.")
            return f"The career could not be filed ({why}). Nothing was moved."
        return '\n'.join([
            f"Career {handed.generation} filed in "
            f"{os.path.relpath(where, state)}.",
            f"The handover is in {legacy.PRIOR}/ for whoever starts next.",
            "",
            "Run the game again for the next career. This session is over.",
        ])
