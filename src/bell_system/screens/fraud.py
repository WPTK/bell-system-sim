"""
The toll-fraud thread on the screens that have the counts.

``traffic`` and ``tnds analysis`` print the exception while it is there, and
a note from the transmission engineer arrives in the mail once. Nothing
here changes what a desk does: the thread is something to read.
"""

from typing import List

from ..data.fraud import LEDGER, exception_block, live, mail_due, note
from ..npc import Message
from .session import SessionState


class FraudThread(SessionState):
    """The anomaly in the counts and the note about it."""

    def _fraud_block(self) -> str:
        """The exception for the foot of a count, or nothing."""
        if not live(self.career.shift, self.shift_minutes):
            return ''
        return '\n\n' + '\n'.join(exception_block(self.career.shift))

    def _fraud_events(self) -> List[Message]:
        """Let the note come in, once, when its time has come."""
        tour = self.career.shift
        if not mail_due(tour, self.shift_minutes):
            return []
        if LEDGER in self.career.beats_seen:
            return []
        self.career.beats_seen.append(LEDGER)
        return [self.switchroom.fraud_note(self.clock.now(), note(tour))]
