"""
The other craft on the system, and the channels they reach you on.

A wire centre in 1983 was not a quiet place to sit. The switching control
centre had you on the order wire, the repair service bureau put reports on
your board, the maintenance teletype printed whether you were reading it or
not, and anyone logged into the same machine could interrupt your terminal
with write(1). This module is those people.

Four channels, each period-correct:

  write(1)    Terminal to terminal on the same UNIX system. Interrupts you
              where you sit; the Seventh Edition manual's own format.
  mail(1)     Reaches you whether you are at the terminal or not.
  order wire  The maintenance circuit between offices and the control centre.
              Voice in reality; rendered here as the words that came over it.
  teletype    The switching machine's maintenance TTY, printing on its own
              schedule. Nobody sends these; the office does.

The people are invented. The jobs, the places and the things they say about
the plant are drawn from the operations the bundled documents describe.
"""

import random
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Sequence

CHANNEL_WRITE = 'write'
CHANNEL_MAIL = 'mail'
CHANNEL_ORDERWIRE = 'orderwire'
CHANNEL_TELETYPE = 'teletype'

CHANNEL_NAMES: Dict[str, str] = {
    CHANNEL_WRITE: 'write(1)',
    CHANNEL_MAIL: 'mail(1)',
    CHANNEL_ORDERWIRE: 'order wire',
    CHANNEL_TELETYPE: 'maintenance TTY',
}


class Craft(NamedTuple):
    """One of the other people working the network tonight."""

    login: str
    name: str
    title: str
    location: str
    tty: str
    # How this person tends to come at you.
    manner: str


CRAFT: Dict[str, Craft] = {
    'rjohnson': Craft(
        'rjohnson', 'Johnson, R.', 'Switching Equipment Technician',
        'CENTRAL_OFF', '02',
        'Twenty-two years on step and crossbar. Tells you what he did, not '
        'what the manual says.'),
    'mreyes': Craft(
        'mreyes', 'Reyes, M.', 'Repair Service Attendant',
        'RSB_NEWARK', '07',
        'Takes the customer calls. Everything she sends you has a commitment '
        'attached to it.'),
    'dpetrak': Craft(
        'dpetrak', 'Petrak, D.', 'SCC Maintenance Administrator',
        'SCC_BEDMINSTER', '03',
        'Watches eleven offices from one console. Polite, and never asks '
        'twice.'),
    'lokafor': Craft(
        'lokafor', 'Okafor, L.', 'Cable Splicer',
        'FIELD_SUP', '04',
        'Out in it. Calls in from a terminal box on a butt-in set and does '
        'not have all day.'),
    'gvasquez': Craft(
        'gvasquez', 'Vasquez, G.', 'Testboard Technician',
        'TEST_CENTER', '09',
        'Lives on the board. Will tell you the reading before you ask for '
        'it.'),
    'ehalloran': Craft(
        'ehalloran', 'Halloran, E.', 'Wire Chief',
        'CENTRAL_OFF', '01',
        'Signs your qualifications. Reads the service index every morning.'),
    'tnakamura': Craft(
        'tnakamura', 'Nakamura, T.', 'Transmission Engineer',
        'TRANS_CTR', '05',
        'Carrier and toll. Talks in dB and will correct you if you do not.'),
    'carot': Craft(
        'carot', 'CAROT', 'Centralized Automatic Reporting On Trunks',
        'CAROT_CENTER', '11',
        'Not a person. Tests trunks all night and prints what it finds.'),
}

# Who reaches you on which channel.
CHANNEL_SENDERS: Dict[str, Sequence[str]] = {
    CHANNEL_WRITE: ('rjohnson', 'gvasquez', 'mreyes', 'ehalloran'),
    CHANNEL_MAIL: ('ehalloran', 'dpetrak', 'tnakamura', 'mreyes'),
    CHANNEL_ORDERWIRE: ('dpetrak', 'lokafor', 'rjohnson', 'tnakamura'),
    CHANNEL_TELETYPE: ('carot',),
}


class Message(NamedTuple):
    """Something one of them sent you."""

    channel: str
    sender: str
    received: datetime
    lines: List[str]
    kind: str
    subject: str
    # A report number the message concerns, when it concerns one.
    about: Optional[str]


# Ambient chatter. Nothing here needs an answer; it is the sound of the
# building. Each entry is a channel, a sender and the words.
_CHATTER: Sequence[tuple] = (
    (CHANNEL_WRITE, 'rjohnson',
     ['Frame is warm again in aisle four. If you get a batch of reports off',
      'one cable tonight, look at the horizontals before you send anybody',
      'out.']),
    (CHANNEL_WRITE, 'gvasquez',
     ['Board is quiet. If you want a pair measured before you commit to it,',
      'send it over and I will run it.']),
    (CHANNEL_WRITE, 'rjohnson',
     ['Marker on the number five is taking longer than it likes on the third',
      'trial. Not calling it yet. Watch your dial tone speed.']),
    (CHANNEL_ORDERWIRE, 'lokafor',
     ['Splicer to test desk. I am in the 400 pair at Franklin and Third.',
      'It is wet in here. Whatever you have out of that cable, it is mine.']),
    (CHANNEL_ORDERWIRE, 'dpetrak',
     ['SCC to office. Routine. No action, just logging that we have you on',
      'the wire.']),
    (CHANNEL_ORDERWIRE, 'tnakamura',
     ['Transmission to office. We are running routines on the toll groups',
      'tonight. If a trunk goes quiet on you, it is us, not the plant.']),
    (CHANNEL_TELETYPE, 'carot',
     ['CAROT ROUTINE TEST COMPLETE',
      'GROUP TESTED 24 CIRCUITS  NO EXCEPTIONS']),
    (CHANNEL_TELETYPE, 'carot',
     ['CAROT EXCEPTION REPORT',
      'TRUNK 0117  LOSS 5.4 DB  ABOVE OBJECTIVE',
      'CIRCUIT LEFT IN SERVICE  RETEST NEXT ROUTINE']),
    (CHANNEL_TELETYPE, 'carot',
     ['SUPERVISION IRREGULARITY',
      'SF TONE PRESENT DURING CONNECTION  TRUNK 0342',
      'CIRCUIT REMOVED FROM SERVICE']),
    (CHANNEL_WRITE, 'mreyes',
     ['Board is filling up out here. If you can clear anything short, do it',
      'now, because the afternoon batch has not landed yet.']),
    (CHANNEL_MAIL, 'ehalloran',
     ['Reminder to all craft: a report closed as no trouble found is still a',
      'report. The index does not care how quickly the board cleared.']),
    (CHANNEL_MAIL, 'tnakamura',
     ['Loss objectives are stated at 1004 Hz. If you are reading at any other',
      'frequency you are not measuring what the objective is written against.']),
    (CHANNEL_MAIL, 'dpetrak',
     ['The processor controlled interrogator will work the remote office test',
      'line from here without CAROT. Ask before you seize a trunk we are',
      'already routining.']),
)

# Advice offered when a report is sitting untested. Written as the older
# craft would put it: what to do, not what it is called.
_HINTS: Sequence[tuple] = (
    ('gvasquez',
     ['Before you send anybody anywhere, measure it. Tip to ring, both to',
      'ground, and the capacitance. The capacitance is the distance.']),
    ('rjohnson',
     ['If tip to ring reads infinite and there is no station termination,',
      'you have an open, and the capacitance tells you how far out it is.',
      'Local cable is 0.083 microfarads to the mile.']),
    ('rjohnson',
     ['One conductor low to ground and tip to ring normal is a ground.',
      'That is outside plant. Do not send it to the office.']),
    ('gvasquez',
     ['Volts on the pair with no battery applied is foreign EMF. That is a',
      'power problem, not a telephone problem, and it is dangerous.']),
    ('ehalloran',
     ['If the loop measures clean all the way to the frame and the customer',
      'still cannot be called, the trouble is toward the switch. That is',
      'ours, not the plant force.']),
    ('gvasquez',
     ['Several pairs low in the same cable at once is water. One splicer',
      'trip fixes all of them. Send it to cable, not to plant.']),
    ('rjohnson',
     ['Loop closed, station termination there, current flowing, nothing out',
      'of limits: the receiver is off the hook. Nobody needs to drive out',
      'for that one.']),
)


class Switchroom:
    """
    Generates the traffic the other craft put on your terminal.

    The terminal asks this for an interruption after a command and gets one
    at the difficulty's rate, or nothing. Mail accumulates whether it is read
    or not, as mail does.
    """

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.mailbox: List[Message] = []
        self.log: List[Message] = []
        self._recent: List[str] = []

    # -- construction ----------------------------------------------------

    def _remember(self, key: str) -> bool:
        """Return whether this line has been used recently."""
        if key in self._recent:
            return True
        self._recent.append(key)
        if len(self._recent) > 8:
            self._recent.pop(0)
        return False

    def _deliver(self, message: Message) -> Message:
        """File a message where it belongs and return it."""
        self.log.append(message)
        if message.channel == CHANNEL_MAIL:
            self.mailbox.append(message)
        return message

    # -- traffic ---------------------------------------------------------

    def chatter(self, now: datetime) -> Optional[Message]:
        """Return an ambient message, or None if it repeats a recent one."""
        channel, sender, lines = self.rng.choice(_CHATTER)
        key = lines[0]
        if self._remember(key):
            return None
        return self._deliver(Message(
            channel=channel, sender=sender, received=now, lines=list(lines),
            kind='chatter', subject=lines[0][:40], about=None,
        ))

    def hint(self, now: datetime) -> Optional[Message]:
        """Return advice from one of the older hands."""
        sender, lines = self.rng.choice(_HINTS)
        if self._remember(lines[0]):
            return None
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender=sender, received=now,
            lines=list(lines), kind='hint', subject='Advice', about=None,
        ))

    def assignment(self, now: datetime, report_number: str,
                   telephone_number: str, symptom: str,
                   commitment: str) -> Message:
        """Hand a new trouble report over from the repair service bureau."""
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='mreyes', received=now,
            lines=[
                f'Report {report_number} on your board.',
                f'{telephone_number} - {symptom.lower()}.',
                f'Committed {commitment}.',
            ],
            kind='assignment', subject=f'{report_number} assigned',
            about=report_number,
        ))

    def ticket_assignment(self, now: datetime, ticket_id: str, title: str,
                          priority: str, office: str) -> Message:
        """The switching control centre putting a trouble ticket on you."""
        urgency = ('This one is critical. Everything else waits.'
                   if priority == 'CRITICAL'
                   else 'When you have a gap.')
        return self._deliver(Message(
            channel=CHANNEL_ORDERWIRE, sender='dpetrak', received=now,
            lines=[
                'SCC to office.',
                f'{ticket_id} is yours: {title}',
                f'{office}, {priority.lower()}. {urgency}',
                f"'trouble detail {ticket_id}' has the rest of it.",
            ],
            kind='ticket', subject=f'{ticket_id} assigned',
            about=ticket_id,
        ))

    # Which channel an event of each type would have come over.
    EVENT_CHANNELS: Dict[str, str] = {
        'SYSTEM': CHANNEL_TELETYPE,
        'TEST': CHANNEL_TELETYPE,
        'MAINTENANCE': CHANNEL_ORDERWIRE,
        'TRAFFIC': CHANNEL_ORDERWIRE,
        'CUSTOMER': CHANNEL_WRITE,
        'EQUIPMENT': CHANNEL_WRITE,
    }

    EVENT_SENDERS: Dict[str, str] = {
        CHANNEL_TELETYPE: 'carot',
        CHANNEL_ORDERWIRE: 'dpetrak',
        CHANNEL_WRITE: 'rjohnson',
    }

    def shift_event(self, now: datetime, event_id: str, event_type: str,
                    title: str, priority: str, at: str) -> Message:
        """
        Announce a shift event as it comes due.

        Events reach a craftsperson over whichever channel would have carried
        them: the machine's own traffic prints to the maintenance teletype,
        maintenance coordination comes over the order wire, and anything a
        person noticed comes from that person.
        """
        channel = self.EVENT_CHANNELS.get(event_type, CHANNEL_WRITE)
        sender = self.EVENT_SENDERS[channel]

        if channel == CHANNEL_TELETYPE:
            lines = [
                f'{at}  {event_type}  {event_id}',
                title.upper(),
                f'PRIORITY {priority}',
            ]
        elif channel == CHANNEL_ORDERWIRE:
            lines = [
                'SCC to office.',
                f'{event_id} is due: {title}',
                f'{priority.lower()} priority, scheduled {at}.',
            ]
        else:
            lines = [
                f'{event_id} just came up.',
                title + '.',
                f"'events detail {event_id}' if you want the rest.",
            ]

        return self._deliver(Message(
            channel=channel, sender=sender, received=now, lines=lines,
            kind='event', subject=f'{event_id} {title[:30]}', about=event_id,
        ))

    def chase(self, now: datetime, report_number: str,
              telephone_number: str) -> Message:
        """Ask, once, about a report that has passed its commitment."""
        sender = self.rng.choice(('mreyes', 'ehalloran'))
        if sender == 'ehalloran':
            lines = [
                f'{report_number} is past commitment.',
                'I would like it either cleared or dispatched before the',
                'index run tonight.',
            ]
        else:
            lines = [
                f'Customer on {telephone_number} called back.',
                f'That is {report_number}. What do I tell them?',
            ]
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender=sender, received=now, lines=lines,
            kind='chase', subject=f'{report_number} past commitment',
            about=report_number,
        ))

    def repeat_notice(self, now: datetime, report_number: str,
                      original: str, telephone_number: str) -> Message:
        """Tell you a report you closed has come back."""
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='mreyes', received=now,
            lines=[
                f'{telephone_number} is back.',
                f'You closed it as {original}. It is {report_number} now, and',
                'it counts as a repeat.',
            ],
            kind='repeat', subject=f'{report_number} repeat report',
            about=report_number,
        ))

    # Which of them answers for which repair force.
    FORCE_SENDERS: Dict[str, str] = {
        'Central office': 'rjohnson',
        'Outside plant': 'lokafor',
        'Cable repair': 'lokafor',
        'Station': 'lokafor',
    }

    def field_call(self, now: datetime, report_number: str,
                   finding: str, force: str = 'Outside plant') -> Message:
        """The dispatched force calling in from the field."""
        sender = self.FORCE_SENDERS.get(force, 'lokafor')
        opening = ('Frame to test desk.' if sender == 'rjohnson'
                   else 'Field to test desk.')
        return self._deliver(Message(
            channel=CHANNEL_ORDERWIRE, sender=sender, received=now,
            lines=[
                opening,
                f'On {report_number}: {finding}.',
            ],
            kind='field', subject=f'{report_number} field report',
            about=report_number,
        ))

    def qualification_notice(self, now: datetime, name: str,
                             commands: Sequence[str]) -> Message:
        """The wire chief signing off a qualification."""
        return self._deliver(Message(
            channel=CHANNEL_MAIL, sender='ehalloran', received=now,
            lines=[
                f'You are signed off on {name}.',
                'That opens: ' + ', '.join(commands) + '.',
                'Do not work anything you are not signed off on.',
            ],
            kind='qualification', subject=f'Qualification: {name}',
            about=None,
        ))

    # -- reading ---------------------------------------------------------

    def unread(self) -> List[Message]:
        """Return mail that has not been read."""
        return list(self.mailbox)

    def take_mail(self) -> List[Message]:
        """Return and clear the mailbox, as reading mail does."""
        waiting = list(self.mailbox)
        self.mailbox.clear()
        return waiting


def render(message: Message, stamp: str) -> str:
    """
    Render a message the way its channel presented it.

    Args:
        message: The message to render
        stamp: A formatted timestamp for the channels that carried one

    Returns:
        The message as it appeared on the terminal or the printer
    """
    person = CRAFT.get(message.sender)
    body = '\n'.join(message.lines)

    if message.channel == CHANNEL_WRITE:
        tty = person.tty if person else '00'
        return (f"\nMessage from {message.sender} tty{tty} [{stamp}]...\n"
                f"{body}\nEOT\n")

    if message.channel == CHANNEL_MAIL:
        name = person.name if person else message.sender
        return (f"From {message.sender}  {stamp}\n"
                f"Subject: {message.subject}\n\n"
                f"{body}\n\n-- {name}\n")

    if message.channel == CHANNEL_ORDERWIRE:
        where = person.location if person else 'UNKNOWN'
        return f"\n[ORDER WIRE {where} {stamp}]\n{body}\n"

    return f"\n{stamp}  MAINTENANCE TTY\n{body}\n"
