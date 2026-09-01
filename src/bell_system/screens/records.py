"""
The records systems: what is on a line, and how you find out.

Four commands here were stubs and one was a stub that should have been the
most useful thing on the terminal. Between them they are the databases a
craftsperson actually queried during a tour - the line record, the service
order, the collect call - and a training index that says which of them you
are signed off for and what to do to be signed off for the rest.

Nothing here holds state of its own. The line records already live on the
report desk, the qualifications on the career record. These are views.
"""

from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from ..console import wrap
from ..data.regulars import REGULARS
from ..data.primer import CLOSING, OPENING, SECTIONS, TITLE
from ..progression import QUALIFICATIONS
from .session import SessionState

# The mechanised records systems a wire centre dealt with, and what each one
# was for. Every one of these is described elsewhere in this simulation; this
# table exists so dbquery can say which to reach for.
DATABASES: Dict[str, Tuple[str, str, str]] = {
    'lmos': (
        'Loop Maintenance Operations System',
        'Customer line records and trouble history',
        'lmos card <number>'),
    'cosmos': (
        'Computer System for Mainframe Operations',
        'Frame assignments, cable and pair, line equipment',
        'cosmos query <number>'),
    'tirks': (
        'Trunk Integrated Record Keeping System',
        'Special service circuits and their facilities end to end',
        'sarts circuit <id>'),
    'tnds': (
        'Total Network Data System',
        'Traffic measurement and network administration',
        'tnds status'),
}

# What a service order can ask for. These are the order types a wire centre
# saw; the codes are this simulation's own shorthand for them.
ORDER_TYPES: Dict[str, str] = {
    'new': 'New service, no working line at the address',
    'change': 'Change to a working line: class of service, features',
    'move': 'Move within the same wire centre',
    'out': 'Disconnect',
    'restore': 'Restore service after disconnect for non-payment',
}


class RecordsCommands(SessionState):
    """
    Line records, service orders, collect calls and training.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`.
    """

    # -- custdb(1) --------------------------------------------------------

    def cmd_custdb(self, args: Optional[List[str]] = None) -> str:
        """
        Look a customer line record up.

        Given a telephone number or a report number, print what the records
        say about that line: who it serves, where it is, what cable and pair
        it comes in on, and how often it has been in trouble.

        This is the same line card LMOS holds. It is here under its own name
        because it is the lookup you do twenty times a tour and nobody wants
        to remember which system it lives in.
        """
        args = args or []
        if not args:
            return self._custdb_index()

        card = self.lmos_console.lmos.find_card(args[0])
        if card is None:
            return (f"custdb: {args[0]}: no record\n"
                    f"custdb with no argument lists the lines with records.")

        record = card.record
        rows = [f"CUSTOMER LINE RECORD  {record.telephone_number}",
                self.clock.timestamp(), '=' * 62, '',
                f"  Name            {record.name}",
                f"  Address         {record.address}",
                f"  Class of svc    {record.class_of_service}",
                f"  Wire centre     {record.clli}",
                '',
                "OUTSIDE PLANT",
                f"  Cable and pair  {record.cable}/{record.pair}",
                f"  Frame           H {record.horizontal}  V {record.vertical}",
                f"  Line equipment  {record.line_equipment}",
                '',
                "TROUBLE HISTORY",
                f"  Reports         {card.report_count}",
                f"  Repeats         {card.repeat_count}"]
        # One of the four the bureau knows by heart. The note is what the
        # last craftsperson wrote on the card, and it is the difference
        # between a number and somebody you have been out to.
        known = REGULARS.get(record.regular or '')
        if known is not None:
            rows.append(f"  Known since     {known.since}")
            rows.append('')
            rows.extend(f"  {line}" for line in wrap(known.note, 58))
        if card.is_chronic():
            rows.append("  CHRONIC - this line has reported often enough "
                        "that the")
            rows.append("            fix is probably not where the last one "
                        "was.")
        rows.append('')
        for report in card.history:
            state = 'closed' if report.closed_at else 'open'
            rows.append(f"  {report.number}  "
                        f"{report.received.strftime('%d %b %H:%M')}  "
                        f"{state:<7}{report.symptom}")
        return '\n'.join(rows)

    def _custdb_index(self) -> str:
        """List the lines that have a record on this position."""
        cards = self.lmos_console.lmos.line_cards()
        if not cards:
            return "custdb: no line records on this position yet"
        rows = ["CUSTOMER LINE RECORDS ON THIS POSITION", '',
                f"  {'NUMBER':<16}{'REPORTS':>8}  NAME"]
        for number, card in sorted(cards.items()):
            flag = ' CHRONIC' if card.is_chronic() else ''
            if card.record.regular:
                flag += ' (known)'
            rows.append(f"  {number:<16}{card.report_count:>8}  "
                        f"{card.record.name}{flag}")
        rows.extend(['', "custdb <number> for one of them."])
        return '\n'.join(rows)

    # -- dbquery(1) -------------------------------------------------------

    def cmd_dbquery(self, args: Optional[List[str]] = None) -> str:
        """
        Find which records system holds what you are after, and ask it.

        ``dbquery`` lists the systems. ``dbquery <system> <thing>`` puts the
        question to that system, which is the same as typing its own command
        and is here so you do not have to know which one that is.
        """
        args = args or []
        if not args:
            rows = ["MECHANISED RECORDS SYSTEMS", '']
            for key, (name, holds, how) in sorted(DATABASES.items()):
                rows.append(f"  {key:<8}{name}")
                rows.append(f"          {holds}")
                rows.append(f"          {how}")
                rows.append('')
            rows.append("dbquery <system> <thing> asks one of them.")
            rows.append("A telephone number is in lmos and cosmos; a circuit "
                        "id is in tirks.")
            return '\n'.join(rows)

        system = args[0].lower()
        if system not in DATABASES:
            # A bare number is a line lookup, which is what people mean.
            if any(character.isdigit() for character in system):
                return self.cmd_custdb([system])
            return (f"dbquery: {system}: no such system\n"
                    f"dbquery with no argument lists them.")
        if len(args) < 2:
            name, holds, how = DATABASES[system]
            return f"{name}\n{holds}\n\nAsk it with: {how}"

        rest = args[1:]
        if system == 'lmos':
            return self.cmd_custdb(rest)
        if system == 'cosmos':
            return self.execute_command(f"cosmos query {' '.join(rest)}")
        if system == 'tirks':
            return self.execute_command(f"sarts circuit {' '.join(rest)}")
        return self.execute_command(f"tnds {' '.join(rest)}")

    # -- provision(1) -----------------------------------------------------

    def cmd_provision(self, args: Optional[List[str]] = None) -> str:
        """
        Raise a service order against a line.

        A service order is what makes the outside plant change: it tells the
        frame what to cross-connect, the assignment records what to update,
        and an installer where to go. Nothing on a repair board moves without
        one.

        ``provision <type> <number>`` raises the order; ``provision`` lists
        the types.
        """
        args = args or []
        if not args:
            rows = ["SERVICE ORDER TYPES", '']
            for key, description in ORDER_TYPES.items():
                rows.append(f"  {key:<10}{description}")
            rows.extend(['', "provision <type> <number> raises one.",
                         "The due date is the next working day: the frame "
                         "works to a list,",
                         "and today's list was made up last night."])
            return '\n'.join(rows)

        order_type = args[0].lower()
        if order_type not in ORDER_TYPES:
            return (f"provision: {order_type}: not an order type\n"
                    f"provision with no argument lists them.")
        if len(args) < 2:
            return f"provision: usage: provision {order_type} <number>"

        card = self.lmos_console.lmos.find_card(args[1])
        if card is None and order_type != 'new':
            return (f"provision: {args[1]}: no working line\n"
                    f"A change, move, out or restore wants a line that is "
                    f"already there.")

        self._order_number += 1
        number = f"SO-{self.clock.now().strftime('%m%d')}-{self._order_number:03d}"
        # The next working day: the frame works to a list made up the night
        # before, so nothing raised now is done today, and nothing is done
        # at the weekend.
        due = self.clock.now().replace(hour=8, minute=0) + timedelta(days=1)
        while due.weekday() >= 5:
            due += timedelta(days=1)
        record = card.record if card else None
        rows = [f"SERVICE ORDER {number}", self.clock.timestamp(), '=' * 62, '',
                f"  Type            {order_type}",
                f"                  {ORDER_TYPES[order_type]}",
                f"  Telephone       {args[1]}",
                f"  Raised by       {self.username}",
                f"  Due             {due.strftime('%a %d %b')}, "
                f"the next working day"]
        if record is not None:
            rows.extend(['', "AGAINST",
                         f"  {record.name}, {record.address}",
                         f"  Cable {record.cable} pair {record.pair}, "
                         f"H {record.horizontal} V {record.vertical}"])
        rows.extend(['',
                     "The order is now on the frame's list. It is not done "
                     "until somebody",
                     "at the frame does it, and nothing you do at this "
                     "position hurries that."])
        self._service_orders.append({'number': number, 'type': order_type,
                                     'line': args[1],
                                     'at': self.clock.now()})
        return '\n'.join(rows)

    # -- collect(1) -------------------------------------------------------

    def cmd_collect(self, args: Optional[List[str]] = None) -> str:
        """
        Collect and third-number calls, and how they are handled.

        A collect call is one the called party agrees to pay for, and an
        operator has to get that agreement out loud before the call is cut
        through. That is why these calls need a person and why the traffic
        service position system exists at all.
        """
        args = args or []
        if args and args[0] == 'queue':
            return self.execute_command('tsps status')
        return f"""OPERATOR-HANDLED CALLS
{self.clock.timestamp()}
{'=' * 62}

WHAT NEEDS AN OPERATOR
{'=' * 62}
  Collect          The called party pays, and has to say so
  Third number     A third line pays, and has to be verified
  Person to person  Charged only if the named person answers
  Credit card      Calling card number verified against the record
  Coin             Overtime deposits on a station-paid call

WHY
{'=' * 62}
Every one of these is a promise to pay made by somebody who is not the
caller. Nothing in the switching equipment can take a promise. The
operator asks, hears the answer, and keys the acceptance, and only then
does the equipment cut the call through and start timing.

That is the whole reason there is a traffic service position system and
the whole reason it is a room full of people.

ON THIS POSITION
{'=' * 62}
This is a repair position and it does not take calls. What it does is
answer the operator when a call will not complete and somebody has to
find out why.

  collect queue     the operator position's own status
  tsps              the traffic service position system
  operator          reaching the operator from here
"""

    # -- training(1) ------------------------------------------------------

    def cmd_training(self, args: Optional[List[str]] = None) -> str:
        """
        What you are signed off for, and how to be signed off for the rest.

        Qualification in the Bell System followed the work: you were signed
        off for what you had done, on the say-so of somebody who had watched
        you do it. This prints where you are in that, and what the next step
        wants.
        """
        args = args or []
        held = set(self.career.qualifications)
        closed = len([report for report in self.desk.closed()
                      if report.correct])

        wanted = args[0].lower() if args else ''
        if wanted in ('unix', 'machine', 'shell'):
            return self._unix_primer()
        if wanted in {q.key for q in QUALIFICATIONS}:
            return self._training_course(wanted, held)

        rows = ["TRAINING AND QUALIFICATION", self.clock.timestamp(),
                '=' * 62, '',
                f"  Reports closed correctly this tour   {closed}",
                '']
        for qualification in QUALIFICATIONS:
            if qualification.key in held:
                state = 'signed off'
            elif closed >= qualification.requires_reports:
                state = 'ready - close one more and it is yours'
            else:
                short = qualification.requires_reports - closed
                state = f"wants {short} more report{'' if short == 1 else 's'}"
            rows.append(f"  {qualification.key:<8}{qualification.name:<28}"
                        f"{state}")
        rows.extend(['',
                     "training <name> for what one of them covers.",
                     "training unix for the annual refresher on the machine "
                     "itself.",
                     '',
                     "Nothing here is a course you sit. The reports on your "
                     "board are the",
                     "course, and closing them correctly is how it is "
                     "passed."])
        return '\n'.join(rows)

    def _unix_primer(self) -> str:
        """
        The annual refresher on the machine, rather than on the job.

        Every part of the Seventh Edition toolkit here works and hardly
        any of it is discoverable: /usr/doc/loop.pic is a diagram that
        prints as markup because it wants pic(1), and somebody who cats
        it reasonably concludes the file is broken. This is where that
        gets said, in the voice of a course nobody wanted to sit.
        """
        rows = [TITLE, '=' * 62, '']
        rows.extend(OPENING)
        for heading, body in SECTIONS:
            rows.extend(['', heading, '-' * 62])
            rows.extend(body)
        rows.append('')
        rows.extend(CLOSING)
        return '\n'.join(rows)

    def _training_course(self, key: str, held: set) -> str:
        """What one qualification covers, and what it opens."""
        qualification = next(q for q in QUALIFICATIONS if q.key == key)
        rows = [f"{qualification.name.upper()}", '=' * 62, '',
                qualification.description, '',
                f"  Wants        {qualification.requires_reports} report"
                f"{'' if qualification.requires_reports == 1 else 's'} "
                f"closed correctly",
                f"  Held         {'yes' if key in held else 'not yet'}",
                '',
                "OPENS"]
        for command in qualification.unlocks:
            page = self.man_pages.get(command, '')
            summary = ''
            for line in page.split('\n'):
                if ' - ' in line and not line.startswith(('NAME', 'SYNOPSIS')):
                    summary = line.split(' - ', 1)[1].strip()
                    break
            rows.append(f"  {command:<12}{summary}")
        rows.extend(['', f"man {qualification.unlocks[0]} has the detail."])
        return '\n'.join(rows)

    def _records_state(self) -> List[dict]:
        """Service orders raised this tour, for anything that wants them."""
        return list(self._service_orders)
