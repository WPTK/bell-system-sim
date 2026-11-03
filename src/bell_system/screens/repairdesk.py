"""
The repair desk's customers, and what happens when they are left holding.

A customer whose report is open rings again after a wait that runs on the
shift clock. Nothing here waits for the player to look: the clock moving is
what rings them, the attendant says so on the next prompt the way she does
for a commitment that has passed, and a customer who has rung three times
and been left is a missed commitment on the index through the same path a
late report takes.

This is a mixin ahead of the shift screens because it has to notice the
clock move, and the clock moves in ``_advance_shift``. It adds to that and
changes none of it, and at any other desk it adds nothing at all.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..data.positions import desk_only
from ..npc import CHANNEL_WRITE, Message, render as render_message
from ..reports import TroubleReport
from .session import SessionState

# How long a customer waits, in shift minutes, before ringing the repair
# desk again. A line that is out of service rings sooner than one that is
# only noisy. The simulation's own figures: nothing sourced says how long a
# 1983 customer held on.
PATIENCE = {True: 20, False: 45}

# Most rings a customer makes before they stop ringing and start writing.
# The third is the one that counts against the desk.
MAX_RINGS = 3

# What an advise call costs in shift minutes: the call itself, each ring the
# customer has already made on the report (they are not calm), and the
# extra it takes to tell somebody you have nothing to tell them.
ADVISE_CALL = 3
ADVISE_RING = 2
ADVISE_EMPTY = 3


def _new_book(tour: int) -> Dict[str, Any]:
    """
    An empty book of customers.

    ``told`` is the report's elapsed time when the customer was last
    advised. ``seen`` is how many rings the clock has counted in the wait
    since, and ``rings`` how many the report has had in all this tour, so
    that closing it does not take them away. Whether a customer who gave up
    has been charged for it is the report's own ``missed_commitment`` flag,
    the one the commitment itself sets, so a report is charged once.
    """
    return {'tour': tour, 'told': {}, 'seen': {}, 'rings': {}}


def _whole_minutes(value: Any) -> Dict[str, int]:
    """Read a saved map of report to whole minutes, dropping what is not."""
    if not isinstance(value, dict):
        return {}
    return {str(k): v for k, v in value.items()
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0}


class RepairDeskCommands(SessionState):
    """
    The customers holding, the book of what they have been told, and the
    sweep that rings them.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`, ahead of
    the shift screens.
    """

    _patience_book: Optional[Dict[str, Any]] = None

    # -- the book ----------------------------------------------------------

    def patience_book(self) -> Dict[str, Any]:
        """
        What the repair desk has told its customers, and who has rung.

        Keyed on the tour, like the NOC's book: the shift clock starts again
        at zero with each tour, so what was told at minute 40 of the last
        one means nothing now.
        """
        book = self._patience_book
        if book is None or book['tour'] != self.career.shift:
            book = self._opening_book()
            self._patience_book = book
        return book

    def _opening_book(self) -> Dict[str, Any]:
        """
        A book for a tour that is just starting, or for a save that has none.

        Every customer already holding is taken to have been told just now.
        A report carried over a handoff has all of its elapsed time on it,
        and counting their wait from the minute the report was received
        would ring every one of them three times on the first prompt.
        """
        book = _new_book(self.career.shift)
        for report in self.desk.customers():
            book['told'][report.number] = report.minutes_spent
        return book

    def patience_state(self) -> Dict[str, Any]:
        """The book as the save file keeps it."""
        book = self.patience_book()
        return {'tour': book['tour'], 'told': dict(book['told']),
                'seen': dict(book['seen']), 'rings': dict(book['rings'])}

    def restore_patience(self, stored: Any) -> None:
        """
        Put a saved book back.

        A save from before the book existed, from another tour or damaged
        brings none, and then it is a book for a tour just starting (see
        _opening_book).
        """
        if isinstance(stored, dict) and stored.get('tour') == self.career.shift:
            book = _new_book(self.career.shift)
            for key in ('told', 'seen', 'rings'):
                book[key] = _whole_minutes(stored.get(key))
        else:
            book = self._opening_book()
        self._patience_book = book

    # -- the clock -----------------------------------------------------------

    def gave_up(self, report: TroubleReport) -> bool:
        """
        Whether this customer has rung three times and stopped.

        They are writing in, not ringing, so telling them something does
        not start a wait that rings again: the rings they show, and the
        advise call's price, stay at none.
        """
        rings = self.patience_book()['rings']
        return rings.get(report.number, 0) >= MAX_RINGS

    def patience(self, report: TroubleReport) -> Tuple[int, int]:
        """
        Return the rings a customer has made in this wait and the minutes
        until the next.

        Their wait is the report's own elapsed time, which is the shift
        clock: it moves with what is typed and run, and the board ages while
        it does. The first tour is a grace, because the wire chief is still
        talking. It is the whole tour, not the stretch before the first
        report is closed (which is all ``first_tour`` covers). Read only.
        """
        window = PATIENCE[report.out_of_service]
        if self.career.shift == 1 or self.gave_up(report):
            return 0, window
        wait = max(0, report.minutes_spent
                   - self.patience_book()['told'].get(report.number, 0))
        return min(MAX_RINGS, wait // window), window - wait % window

    def patience_queue(self) -> List[Tuple[TroubleReport, int, int]]:
        """
        The customers holding, most rings first, then soonest to ring.

        Read only: looking at who is holding does not change who rang.
        """
        queue = []
        for report in self.desk.customers():
            rings, left = self.patience(report)
            queue.append((report, rings, left))
        return sorted(queue, key=lambda row: (-row[1], row[2]))

    def rings_total(self) -> int:
        """
        Rings customers have made this tour, whether or not anyone saw.

        A customer stops at the third, however many times they are advised
        and wait again: after that they are writing in, not ringing.
        """
        book = self.patience_book()
        counts = dict(book['rings'])
        for report in self.desk.customers():
            number = report.number
            rings, _ = self.patience(report)
            pending = max(0, rings - book['seen'].get(number, 0))
            counts[number] = min(MAX_RINGS, counts.get(number, 0) + pending)
        return sum(counts.values())

    def ring_sweep(self) -> List[Message]:
        """
        Notice the customers who have rung since the clock last moved.

        Counts each ring once, says so in the attendant's words, and charges
        the third to the index as a missed commitment. A customer who has
        given up has nothing more to say, so a report is rung on three times
        in the tour and no more, whatever it is told in between. A report is charged
        once whichever comes first, the customer giving up or the commitment
        passing: both set the report's ``missed_commitment`` flag, which the
        commitment's own count (and the close) look at before they charge.
        Only the repair desk has customers to ring, and the first tour is a
        grace, so anywhere else this does nothing.
        """
        if self.position.key != 'custserv' or self.career.shift == 1:
            return []
        book = self.patience_book()
        notices: List[Message] = []
        for report in self.desk.customers():
            number = report.number
            if self.gave_up(report):
                continue
            rings, _ = self.patience(report)
            seen = book['seen'].get(number, 0)
            if rings < seen:
                # They were told something and the wait began again.
                book['seen'][number] = rings
                continue
            if rings == seen:
                continue
            book['seen'][number] = rings
            given = book['rings'].get(number, 0)
            if given >= MAX_RINGS:
                continue
            total = min(MAX_RINGS, given + rings - seen)
            book['rings'][number] = total
            notice = self._ring_notice(report, total)
            if total >= MAX_RINGS and not report.missed_commitment:
                # The same cost a report that passes its commitment carries,
                # through the same path; the handoff prints it. The flag is
                # what keeps the commitment from charging it again.
                report.missed_commitment = True
                self.career.record_missed(1)
            self.switchroom.log.append(notice)
            notices.append(notice)
        return notices

    def _ring_notice(self, report: TroubleReport, rings: int) -> Message:
        """The attendant, on a customer who has just rung."""
        telephone = report.record.telephone_number
        if rings >= MAX_RINGS:
            lines = [
                f'{telephone} has rung {rings} times on {report.number} and',
                'will not ring again. They are writing in. That counts',
                'against the commitment.',
            ]
        else:
            lines = [
                f'{telephone} is on the line again about {report.number}.',
                f'That is ring {rings}. What do I tell them?',
            ]
        return Message(
            channel=CHANNEL_WRITE, sender='mreyes',
            received=self.clock.now(), lines=lines, kind='ring',
            subject=f'{report.number} customer rang', about=report.number)

    def _advance_shift(self) -> List[str]:
        """
        Charge the shift as it always has, then ring whoever has waited.

        Rendered the way a late commitment's notice is, so it is shown or
        left unseen by the ambience setting, and counted either way.
        """
        pieces = super()._advance_shift()
        return pieces + [render_message(message, self._stamp())
                         for message in self.ring_sweep()]

    # -- the call ----------------------------------------------------------

    @staticmethod
    def _has_reading(report: TroubleReport) -> bool:
        """
        Whether there is anything true to tell this customer.

        What the field has found, which is set only when the crew sent was
        the right force for the fault: a crew out on the right force has a
        finding already, and one sent to the wrong force has none. A test
        alone is not an answer (it says the line was measured, and the
        customer asked what is wrong with it), and nor is a wrong dispatch,
        which would be telling the customer something false.
        """
        return bool(report.field_finding)

    def advise(self, args: List[str]) -> str:
        """
        trouble advise [REPORT]: the repair desk's call back to a customer.

        With no argument, the customers holding. With a report, ring that
        customer and tell them where it stands. The call costs shift
        minutes, more for each time they have already rung, and more again
        when there is nothing yet to tell them - so the report is worth
        working before the customer is, and a customer on the third ring is
        worth reaching before one on the first.
        """
        refusal = desk_only(self.position, 'custserv', 'trouble advise')
        if refusal:
            return refusal
        if args:
            return self._advise_call(args[0])
        queue = self.patience_queue()
        lines = [f"CUSTOMERS HOLDING   {self.position.name}",
                 f"Shift time {self.shift_time()}", '=' * 66,
                 f"{'REPORT':<10}{'LINE':<14}{'RINGS':<7}{'NEXT RING':<11}"
                 f"{'CALL':<6}TOLD", '-' * 66]
        for report, rings, left in queue:
            known = self._has_reading(report)
            # Nobody rings after the third; there is no next ring to show.
            until = '-' if self.gave_up(report) else f"{left}m"
            lines.append(
                f"{report.number:<10}{report.record.telephone_number:<14}"
                f"{rings:<7}{until:<11}"
                f"{self._advise_cost(rings, known):>2}m   "
                f"{'status' if known else 'nothing yet'}")
        if not queue:
            lines.append("Nobody is holding.")
        lines += [
            '-' * 66,
            f"{len(queue)} customer(s) with a report open.",
            "",
            "  trouble advise <REPORT>   Ring them back and say where it",
            "                            stands (CALL minutes)",
            "  report next               What to work, so there is",
            "                            something to tell them",
            "",
            "A customer rings again after 20 shift minutes out of service,",
            "45 otherwise, counted from the last call, and the third ring",
            "counts as a missed commitment. A finding is something to",
            "tell them, which a crew out on the right force has; a test",
            "alone is not, nor a crew sent to the wrong force. These",
            "figures are the simulation's own.",
        ]
        return '\n'.join(lines)

    @staticmethod
    def _advise_cost(rings: int, known: bool) -> int:
        """Shift minutes an advise call costs."""
        return (ADVISE_CALL + ADVISE_RING * rings
                + (0 if known else ADVISE_EMPTY))

    def _advise_call(self, token: str) -> str:
        """Ring one customer back, and say what there is to say."""
        report = self.desk.find(token)
        if report is None or report not in self.desk.customers():
            return (f"trouble advise: no customer holding on '{token}'.\n"
                    f"'trouble advise' lists them.")
        rings, _ = self.patience(report)
        book = self.patience_book()
        known = self._has_reading(report)
        cost = self._advise_cost(rings, known)
        self._pass_time(cost)
        if known:
            book['told'][report.number] = report.minutes_spent
            if report.dispatched_to:
                said = (f"{report.crew or report.dispatched_to} is on it"
                        f" ({report.dispatched_to}).")
            else:
                said = f"it has been found: {report.field_finding}."
            if self.gave_up(report):
                tone = "They had given up ringing and written in."
            elif rings:
                tone = f"They had rung {rings} time(s) already."
            else:
                tone = "They had not rung yet."

            return '\n'.join([
                f"{report.number}: rang {report.record.telephone_number}. "
                f"{tone}",
                f"Told them: {said}",
                f"That was {cost} minutes of the shift; they will not ring "
                f"for {PATIENCE[report.out_of_service]} more.",
            ])
        # Nothing to tell: half the wait is forgiven, no more.
        wait = report.minutes_spent - book['told'].get(report.number, 0)
        book['told'][report.number] = report.minutes_spent - wait // 2
        return '\n'.join([
            f"{report.number}: rang {report.record.telephone_number} with "
            f"nothing to tell them.",
            f"That was {cost} minutes of the shift, and half of what they "
            f"had waited",
            "is still owed. A finding is an answer; 'report next' says "
            "what to",
            "work.",
        ])
