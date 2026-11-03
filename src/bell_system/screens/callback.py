"""
Ringing a customer back from the repair service bureau.

``report callback <number>`` asks for the customer's own account.
``report callback <number> <topic>`` asks one question of it. Each call
costs the same, so a question is chosen and not asked for the sake of it.
"""

from typing import Optional

from ..console import wrap
from ..data.callbacks import CADENCE_HEARD, asked, general, topics
from ..data.trouble import FAULTS
from ..reports import COST_CALLBACK
from .session import SessionState

# What a customer says, wrapped. Narrower than the post-mortem because it
# is indented and quoted, which is how a note of a call reads on paper.
CALLBACK_WIDTH = 64


class CallbackCommands(SessionState):
    """Calling a customer back."""

    def _report_callback(self, token: str, topic: Optional[str] = None
                         ) -> str:
        """Call the customer back and get more out of them than the card has."""
        report = self.desk.find(token)
        if report is None:
            return (self.desk.stale_position(token)
                    or f"report: no report matching '{token}'")
        if report.status == 'CLOSED':
            return f"{report.number} is already closed."
        if topic is not None and asked(topic, report.record.fault,
                                       report.symptom) is None:
            # Refused before the call is made, so a mistyped question does
            # not cost the clock anything.
            return (f"report: callback: no such question '{topic}'\n"
                    f"Ask one of: {topics()}")

        report.spend(COST_CALLBACK)
        # The chief's next line is about this call, and the board one that
        # would otherwise follow the command is no longer true to say.
        self._tour_nudges.add('board')

        by_ear = False
        if topic is None:
            said, by_ear = general(
                report.record.fault, report.symptom,
                FAULTS[report.record.fault].description)
        else:
            said = asked(topic, report.record.fault, report.symptom) or ''
            by_ear = (topic.lower() == 'hear'
                      and 'complete' in report.symptom.lower()
                      and report.record.fault in CADENCE_HEARD)

        lines = [f"Call back on {report.record.telephone_number} "
                 f"({report.record.name}).", '']
        if topic is not None:
            lines.extend([f"  Asked: {topic.lower()}", ''])
        lines.extend(f"  {line}" for line in
                     wrap(f'"{said}"', CALLBACK_WIDTH))
        if by_ear:
            lines.extend(['', "tone(1) will make both of those if you want "
                              "to hear them side by side."])
        lines.extend(['', f"{COST_CALLBACK} minutes charged. "
                          f"{report.age_label()} "
                          f"{'past' if report.overdue() else 'remaining'}."])
        if topic is None:
            lines.append(f"You could also ask: {topics()}")
        nudge = self.first_tour_nudge('callback')
        if nudge:
            lines.extend(['', nudge])
        return '\n'.join(lines)
