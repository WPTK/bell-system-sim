"""
Where on the plant a crew is told to go, and the cases a board can hold.

A dispatch used to name a force and nothing else, and a splicer sent to
Cable repair opened the right sheath because the desk knew which one it was.
A person at the position would have said where. These are the parts of that
which are the player's to say: which cable and which binder group, in the
words the assignment record uses for them.
"""

import re
from typing import List, Optional, Tuple

from ..cable import BINDERS_PER_UNIT, PAIRS_PER_BINDER, binder_of
from ..reports import TroubleReport
from .session import SessionState

# A section as the player writes it: the cable, a slash and the binder
# group, as in 81/8. Not the cable and pair the report carries, which is
# 0081/0181 and would be the answer to be copied.
_SECTION = re.compile(r'^(\d{1,4})/(\d{1,2})$')


class CaseCommands(SessionState):
    """Naming a section for a crew, and the shared causes behind reports."""

    def _named_section(self, words: str
                       ) -> Tuple[str, Optional[Tuple[int, int]], str]:
        """
        Split a cable and binder group off the end of a dispatch.

        Args:
            words: What followed the report number: a force, and perhaps a
                section after it

        Returns:
            The force's words, the section if one was named, and a refusal
            if what looked like a section is not one
        """
        parts: List[str] = words.split()
        if not parts or '/' not in parts[-1]:
            return words, None, ''
        token = parts.pop()
        found = _SECTION.match(token)
        if found is None:
            return ' '.join(parts), None, (
                f"report: '{token}' is not a cable and binder group.\n"
                f"Write it cable/binder, as in 81/8.")
        cable, binder = int(found.group(1)), int(found.group(2))
        if not 1 <= binder <= BINDERS_PER_UNIT:
            return ' '.join(parts), None, (
                f"report: binder groups run 1 to {BINDERS_PER_UNIT}, in "
                f"twenty-fives of pairs. There is no group {binder}.")
        return ' '.join(parts), (cable, binder), ''

    def _section_asked(self, force: str,
                       section: Optional[Tuple[int, int]]) -> str:
        """
        Refuse a splicer's dispatch that does not say where to go.

        Asked of every Cable repair dispatch, whatever the report is, so the
        question carries no information about it. Nothing is charged.
        """
        if (force != 'Cable repair' or section is not None
                or not self._difficulty().section_required):
            return ''
        return ("The splicers will not open a sheath on a guess. Which one?\n"
                "  report dispatch <number> cable <cable>/<binder>\n"
                f"A binder group is {PAIRS_PER_BINDER} pairs, counted from "
                "1. 'man cable' has the colour code.")

    def _is_own_section(self, report: TroubleReport,
                        section: Optional[Tuple[int, int]]) -> bool:
        """Whether a dispatch's section is the one the report's pair is in."""
        return (section is None
                or section == (report.record.cable,
                               binder_of(report.record.pair)))
