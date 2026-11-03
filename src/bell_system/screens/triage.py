"""
The NOC's triage queue: open tickets, each with a response window that runs
on the shift clock.

Split out of tickets.py, which it would have taken past the size limit. The
verb is dispatched from ``trouble triage`` there; everything else is here.
"""

from typing import Any, Dict, List, Optional

from ..data.positions import POSITIONS
from ..types import TroubleTicket
from .session import SessionState

# The NOC's triage clock, in shift minutes. A ticket's window opens when the
# tour does (or when the ticket is entered) and the class sets how long it
# may wait for somebody to be on it. The 15, 30 and 60 are the response
# targets `trouble detail` already prints; a call out to the district costs
# the shift 6, 4 or 2 minutes. All of these figures are the simulation's own.
TRIAGE_WINDOW = {'CRITICAL': 15, 'MAJOR': 30, 'MINOR': 60}
TRIAGE_CALL = {'CRITICAL': 6, 'MAJOR': 4, 'MINOR': 2}


def _new_book(tour: int) -> Dict[str, Any]:
    """An empty triage book. ``earlier`` counts entries retired on resume."""
    return {'tour': tour, 'opened': {}, 'klass': {}, 'sig': {}, 'taken': {},
            'lapsed': {}, 'earlier': {'taken': 0, 'lapsed': 0}}


def _signature(ticket: TroubleTicket) -> str:
    """What says a ticket is the one a saved entry was made for."""
    return f"{ticket['title']}|{ticket['customer_impact']}"


def _whole_minutes(value: Any) -> Dict[str, int]:
    """A saved {ticket id: shift minute}, or nothing if it is not one."""
    if not isinstance(value, dict):
        return {}
    return {str(k): v for k, v in value.items()
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0}


class TriageCommands(SessionState):
    """
    The queue, its book and its clock.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- the NOC's triage queue ---------------------------------------------

    _triage_book: Optional[Dict[str, Any]] = None

    def triage_book(self) -> Dict[str, Any]:
        """
        The queue's own record for this tour.

        When each ticket was entered and what class it was then, which have
        been taken and when, and which ran past their window. Kept per tour
        because the shift clock starts again at zero with each one; an open
        ticket carries over, and its window starts again with the tour.

        A new book stamps every ticket there is at minute 0, which is when
        the tour opened. take_position() makes it at the start of the tour
        so that nothing is stamped later than that; a ticket that turns up
        after is stamped when it is first seen (see triage_stamp).
        """
        book = self._triage_book
        if book is None or book['tour'] != self.career.shift:
            book = _new_book(self.career.shift)
            self._triage_book = book
            for ticket in self.active_tickets:
                self.triage_stamp(ticket, 0)
        return book

    def triage_stamp(self, ticket: TroubleTicket,
                     at: Optional[int] = None) -> None:
        """
        Fix when a ticket's window opened and which class it runs on.

        Once only. The class is the one the ticket had when it was first
        stamped, so `trouble escalate` raising its priority does not hand
        it a shorter window after the fact. A ticket stamped late is
        stamped from now.
        """
        book = self.triage_book()
        book['opened'].setdefault(
            ticket['id'], self.shift_minutes if at is None else at)
        book['klass'].setdefault(ticket['id'], ticket['priority'])
        book['sig'].setdefault(ticket['id'], _signature(ticket))

    def triage_state(self) -> Dict[str, Any]:
        """The book as the save file keeps it."""
        book = self.triage_book()
        state: Dict[str, Any] = {'tour': book['tour'],
                                 'earlier': dict(book['earlier'])}
        for key in ('opened', 'klass', 'sig', 'taken', 'lapsed'):
            state[key] = dict(book[key])
        return state

    def restore_triage(self, stored: Any) -> None:
        """
        Put a saved book back, and stamp what the resumed pool brought.

        The ticket pool is dealt again when a shift resumes, and its
        tickets reuse the numbers of the ones it replaces. So a saved
        entry only describes the ticket now holding that number if the
        ticket is the same one (its signature matches); otherwise the
        entry is retired into the tour's running counts and the new ticket
        opens its window from now, not from minute 0, which would make
        everything late. A save from before the book existed brings none,
        and every ticket opens from now.
        """
        book = _new_book(self.career.shift)
        if isinstance(stored, dict) and stored.get('tour') == book['tour']:
            for key in ('opened', 'taken', 'lapsed'):
                book[key] = _whole_minutes(stored.get(key))
            for key in ('klass', 'sig'):
                value = stored.get(key)
                book[key] = ({str(k): str(v) for k, v in value.items()}
                             if isinstance(value, dict) else {})
            book['klass'] = {k: v for k, v in book['klass'].items()
                             if v in TRIAGE_WINDOW}
            earlier = stored.get('earlier')
            if isinstance(earlier, dict):
                for key in ('taken', 'lapsed'):
                    value = earlier.get(key)
                    if isinstance(value, int) and value >= 0:
                        book['earlier'][key] = value
        for ticket in self.active_tickets:
            ticket_id = ticket['id']
            if book['sig'].get(ticket_id) != _signature(ticket):
                for key in ('taken', 'lapsed'):
                    if book[key].pop(ticket_id, None) is not None:
                        book['earlier'][key] += 1
                for key in ('opened', 'klass', 'sig'):
                    book[key].pop(ticket_id, None)
        self._triage_book = book
        for ticket in self.active_tickets:
            self.triage_stamp(ticket)

    def triage_grace(self) -> bool:
        """The whole of the first tour is a grace, not only until a close."""
        return self.career.shift == 1

    def triage_due(self, ticket: TroubleTicket) -> int:
        """The shift minute by which somebody has to be on this ticket."""
        self.triage_stamp(ticket)
        book = self.triage_book()
        return (book['opened'][ticket['id']]
                + TRIAGE_WINDOW[book['klass'][ticket['id']]])

    def triage_queue(self) -> List[TroubleTicket]:
        """
        Open tickets nobody is on, soonest window first.

        Only a ticket that is OPEN and that nobody has been given is
        waiting: one the control centre handed to a position, one that
        `trouble assign` named a team for, one taken here, and anything
        resolved or closed is not. Pure: it changes nothing. A window that
        has passed is noticed by triage_sweep.
        """
        book = self.triage_book()
        queue = [t for t in self.active_tickets
                 if t['status'] == 'OPEN'
                 and t['id'] not in self._assigned_tickets
                 and t['id'] not in book['taken']]
        queue.sort(key=lambda t: (self.triage_due(t), -t['customer_impact'],
                                  t['id']))
        return queue

    def triage_overdue(self) -> List[TroubleTicket]:
        """
        Tickets waiting past their window right now. Changes nothing.

        Computed from the shift clock and nothing else, so the same minute
        always reads the same. The first tour is a grace.
        """
        if self.triage_grace():
            return []
        now = self.shift_minutes
        return [t for t in self.triage_queue() if now > self.triage_due(t)]

    def triage_lapsed(self) -> int:
        """Tickets whose window closed with nobody on them, noticed or not."""
        book = self.triage_book()
        ids = set(book['lapsed'])
        ids.update(t['id'] for t in self.triage_overdue())
        return len(ids) + book['earlier']['lapsed']

    def triage_sweep(self) -> None:
        """
        Notice the windows that have passed: up one level, once, on record.

        Called where the queue is shown and where a ticket is taken, and
        nowhere else, so that the tally can count without changing a thing.
        """
        book = self.triage_book()
        for ticket in self.triage_overdue():
            if ticket['id'] in book['lapsed']:
                continue
            book['lapsed'][ticket['id']] = self.shift_minutes
            ticket['escalation_level'] = min(
                ticket['escalation_level'] + 1, 4)
            ticket['resolution_steps'].append(
                f"[{self.shift_time()}] Response window passed with "
                f"nobody on it; escalation level "
                f"{ticket['escalation_level']}")

    def _triage(self, args: List[str]) -> str:
        """trouble triage [ID]: show the queue, or take a ticket from it."""
        if args:
            return self._triage_take(args[0].upper())
        self.triage_sweep()
        queue = self.triage_queue()
        book = self.triage_book()
        now = self.shift_minutes
        lines = [f"NOC TRIAGE QUEUE   {POSITIONS['noc'].name}",
                 f"Shift time {self.shift_time()}", '=' * 66,
                 f"{'ID':<9}{'CLASS':<9}{'WINDOW':<11}{'CALL':<6}"
                 f"{'CUSTOMERS':>10}  OFFICE", '-' * 66]
        for ticket in queue:
            left = self.triage_due(ticket) - now
            window = f"{left}m left" if left >= 0 else f"LATE {-left}m"
            lines.append(
                f"{ticket['id']:<9}{ticket['priority']:<9}{window:<11}"
                f"{TRIAGE_CALL[ticket['priority']]:>2}m   "
                f"{ticket['customer_impact']:>10,}  "
                f"{self._office_label(ticket['affected_office'])[:24]}")
        if not queue:
            lines.append("Nothing waiting. Every open ticket has somebody "
                         "on it.")
        lines.append('-' * 66)
        lines += [
            f"{len(queue)} waiting, "
            f"{len(book['taken']) + book['earlier']['taken']} taken this "
            f"tour, {self.triage_lapsed()} past their window.",
            "",
            "  trouble triage <ID>   Take one; the call costs the CALL "
            "minutes",
            "  trouble detail <ID>   Read it first (that costs a minute)",
            "",
            "Windows run on the shift clock from the start of the tour:",
            "CRITICAL 15, MAJOR 30, MINOR 60. A ticket nobody is on when "
            "its",
            "window closes goes up a level, and counts as a missed "
            "commitment",
            "on your index whether or not you look. The figures are the "
            "simulation's own.",
        ]
        return '\n'.join(lines)

    def _triage_take(self, ticket_id: str) -> str:
        """Put this position on a ticket, and say whether it was in time."""
        self.triage_sweep()
        queue = self.triage_queue()
        ticket = next((t for t in queue if t['id'] == ticket_id), None)
        book = self.triage_book()
        if ticket is None:
            if ticket_id in book['taken']:
                return f"trouble triage: {ticket_id} is already on you."
            return (f"trouble triage: {ticket_id} is not in the queue.\n"
                    f"'trouble triage' lists what is waiting.")
        now = self.shift_minutes
        due = self.triage_due(ticket)
        cost = TRIAGE_CALL[ticket['priority']]
        book['taken'][ticket_id] = now
        if ticket['status'] == 'OPEN':
            ticket['status'] = 'IN_PROGRESS'
        ticket['assigned_team'] = f"{self.username} (this position)"
        self._assigned_tickets.add(ticket_id)
        late = now > due and not self.triage_grace()
        if late:
            verdict = f"{now - due} minutes after the window closed"
        elif now <= due:
            verdict = f"in time, with {due - now} minutes of the window left"
        else:
            verdict = "on a first tour, which is a grace"
        if late:
            # The same cost a report that passes its commitment carries,
            # through the same path: the handoff prints it.
            self.career.record_missed(1)
        ticket['resolution_steps'].append(
            f"[{self.shift_time()}] Taken by {self.username}, {verdict}")
        self._pass_time(cost)
        return (f"{ticket_id} {ticket['priority']} taken {verdict}.\n"
                f"The call out to the district took {cost} minutes of the "
                f"shift.\n"
                f"'trouble resolve {ticket_id}' closes it when it is done.")
