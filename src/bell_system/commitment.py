"""
How a report stands against its commitment, in words.

``TroubleReport.age_label()`` is signed: a minus in front of a figure is how
the board's narrow column says a report is overdue. Beside the word "past" or
"remaining" the sign says it twice and reads "-3:28 past". Every sentence that
gives a report's standing uses this one form instead.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checking
    from .reports import TroubleReport


def commitment_label(report: 'TroubleReport') -> str:
    """Return "3:28 past" or "1:05 remaining": the span, then which side."""
    stamp = report.age_label().lstrip('-')
    return f"{stamp} {'past' if report.overdue() else 'remaining'}"
