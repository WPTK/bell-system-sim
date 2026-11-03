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
        if [word.lower() for word in args[1:]] != ['confirm']:
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
            f" {career.reports_closed} reports closed, audit "
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
        try:
            where, moved = legacy.set_aside(state)
        except OSError as error:
            return (f"The career could not be filed ({error.strerror or error})"
                    f". Nothing was moved.")
        try:
            legacy.write(legacy.legacy_path(state), handed)
        except OSError as error:
            legacy.put_back(state, where, moved)
            return (f"The handover could not be written "
                    f"({error.strerror or error}). Nothing was moved.")
        # This process no longer owns a career: nothing it does from here
        # writes to the files that were just filed.
        self.career.path = None
        self.shift_file = ''
        self._home_locked = True
        self._career_filed = True
        return '\n'.join([
            f"Career {handed.generation} filed in {os.path.relpath(where, state)}.",
            f"The handover is in {legacy.PRIOR}/ for whoever starts next.",
            "",
            "Run the game again for the next career. This session is over.",
        ])
