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
    'wfinch': Craft(
        'wfinch', 'Finch, W.', 'Station Installer',
        'FIELD_SUP', '06',
        'Drop, protector and set: everything the customer can see. Rings in '
        'from the kitchen phone as often as from a terminal box.'),
    'jsandoval': Craft(
        'jsandoval', 'Sandoval, J.', 'Cable Splicer',
        'FIELD_SUP', '11',
        'Second splicer. Newer than Okafor and says less, which the wire '
        'chief has noticed and has not decided about.'),
    'abright': Craft(
        'abright', 'Bright, A.', 'Lineman',
        'FIELD_SUP', '12',
        'Aerial and buried plant between the office and the drop. Calls in '
        'from wherever the ladder is.'),
    'jhaverty': Craft(
        'jhaverty', 'Haverty, J.', 'Chief Operator',
        'TSPS_NEWARK', '10',
        'Runs a room of operator positions. Everything she brings you is a '
        'call somebody is still holding.'),
    'adm': Craft(
        'adm', 'ADM', 'System accounting',
        'CENTRAL_OFF', '08',
        'Not a person. The machine writing its own record, in the register '
        'a machine writes in.'),
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


# What each desk hears on top of the whole building.
#
# Added to the shared pool rather than replacing it: a document preparation
# desk still hears CAROT printing trunk exceptions at three in the morning,
# because it is in the same building and the teletype does not care who is
# sitting there. It just also hears Petrak about an addendum.
#
# This is where the character of a position actually lives. The work mix
# tells you what kind of tour it is; these tell you whose building it is.
_POSITION_CHATTER: Dict[str, Sequence[tuple]] = {

    'sysop': (
        (CHANNEL_TELETYPE, 'adm',
         ['/usr/spool is at 84 percent. uucp has 47 files queued for pwba',
          'and pwba has not answered since 06:44.']),
        (CHANNEL_WRITE, 'tnakamura',
         ['Somebody left a job running on the 11/70 over the weekend and it',
          'is still running. It is not mine. I have looked.']),
        (CHANNEL_WRITE, 'ehalloran',
         ['When the operating company takes this machine in January they',
          'take the accounts on it. Anything in /tmp is yours until then',
          "and nobody else's ever."]),
        (CHANNEL_TELETYPE, 'adm',
         ['su: BADSU 11/14 07:52 - tty03 mreyes-root']),
    ),

    'switch': (
        (CHANNEL_WRITE, 'rjohnson',
         ['Marker 2 took eleven seconds on a third trial this morning. Peg',
          'count is up and nothing is out of limits, which is the whole',
          'problem with a marker.']),
        (CHANNEL_ORDERWIRE, 'dpetrak',
         ['SCC to office. Your dial tone speed is on the wrong side of the',
          'objective for the second morning. Nothing is alarming. Somebody',
          'is going to ask.']),
        (CHANNEL_WRITE, 'ehalloran',
         ['If it is a false cross or ground the loop will measure clean to',
          'the frame every time. Do not send anybody out on one.']),
        (CHANNEL_TELETYPE, 'carot',
         ['*** OFFICE 24 HOUR SUMMARY - MACHINE ACCESS WITHIN OBJECTIVE',
          '*** MACHINE SWITCHING - 3 EXCEPTIONS - SEE COER']),
    ),

    'field': (
        (CHANNEL_ORDERWIRE, 'lokafor',
         ['Field to test desk. I am in a manhole at Franklin and it has six',
          'inches of water in it. Whatever else you were going to give me',
          'today, give it to Sandoval.']),
        (CHANNEL_ORDERWIRE, 'wfinch',
         ['Station to test desk. Customer met me at the door and told me it',
          'has been doing it for three weeks. Three weeks and one report.',
          'They always wait.']),
        (CHANNEL_WRITE, 'mreyes',
         ['Two off Elm Street in twenty minutes. Before you send anybody,',
          'look at what cable they are on.']),
        (CHANNEL_ORDERWIRE, 'abright',
         ['Lineman to test desk. That pole at Grand has been leaning since',
          "the storm and it is going to be somebody's problem in January."]),
    ),

    'noc': (
        (CHANNEL_TELETYPE, 'carot',
         ['*** REGIONAL SUMMARY 08:00 - 4 GROUPS OVER OBJECTIVE',
          '*** ALL WITHIN P.01 - NO ACTION INDICATED']),
        (CHANNEL_ORDERWIRE, 'dpetrak',
         ['SCC to national. Bedminster is showing the same three groups you',
          'are. Nobody below us can see it: every office underneath reports',
          'a normal day.']),
        (CHANNEL_WRITE, 'ehalloran',
         ['One group over objective is a group. Three homing on the same',
          'sectional centre is something else, and it will not show up',
          'anywhere but here.']),
        (CHANNEL_TELETYPE, 'carot',
         ['*** MASS CALLING DETECTED NPA 212 NXX 555',
          '*** CODE BLOCK RECOMMENDED']),
    ),

    'tsps': (
        (CHANNEL_ORDERWIRE, 'jhaverty',
         ['Chief operator. Position 14 has a collect the called party will',
          'not accept and will not hang up on either. She has been on it',
          'four minutes.']),
        (CHANNEL_WRITE, 'jhaverty',
         ['If it rings and nobody answers it is a line. If it rings and',
          'somebody answers and cannot hear, it is not, and I would rather',
          'know which before I tell the caller anything.']),
        (CHANNEL_ORDERWIRE, 'jhaverty',
         ['We have had six calls off one exchange saying the line is busy',
          'when it is not. Six is not six people being wrong.']),
        (CHANNEL_WRITE, 'mreyes',
         ['A permanent signal and a receiver off the hook are the same',
          'thing to the equipment. They are not the same thing to the',
          'customer, who is asleep.']),
    ),

    'dba': (
        (CHANNEL_WRITE, 'lokafor',
         ['The pair COSMOS says is spare has a working line on it. I am',
          'standing at the terminal box looking at it. Fix the record',
          'before somebody gets assigned it.']),
        (CHANNEL_WRITE, 'ehalloran',
         ['Every record on this machine goes to the operating company on',
          'the first of January. Anything wrong in it on the thirty-first',
          'is wrong in it forever.']),
        (CHANNEL_TELETYPE, 'adm',
         ['cosmos: 3 pending frame orders unworked at 08:00',
          'cosmos: load balance index 0.940 - within objective']),
        (CHANNEL_WRITE, 'rjohnson',
         ['If the cross-connect record and the frame disagree, the frame is',
          'right. It is always the frame. The frame is the thing that is',
          'actually there.']),
    ),

    'netplan': (
        (CHANNEL_WRITE, 'ehalloran',
         ['They want the eighteen month forecast by Friday and the only',
          'thing you have to build it out of is last month.']),
        (CHANNEL_WRITE, 'tnakamura',
         ['The growth is not in telephones. It is in what people put on the',
          'line once they have one, and the special services group is going',
          'to run out of facilities before anybody notices.']),
        (CHANNEL_ORDERWIRE, 'dpetrak',
         ['SCC to planning. Who does the arithmetic in January for a circuit',
          'with one end in each company? Nobody here knows and I have asked',
          'three people.']),
        (CHANNEL_TELETYPE, 'carot',
         ['*** TRUNK FORECAST EXCEPTION - TG-089-CHI',
          '*** MEASURED BUSY HOUR HAS MOVED 2 HOURS SINCE LAST QUARTER']),
    ),

    'custserv': (
        (CHANNEL_WRITE, 'mreyes',
         ['She has taken the morning off work twice for this. If we miss it',
          'again I would rather ring her than have her ring us.']),
        (CHANNEL_WRITE, 'mreyes',
         ['The line tests fine from here about a third of the time and the',
          'trouble is real about a third of the time. They are not the',
          'same third.']),
        (CHANNEL_ORDERWIRE, 'jhaverty',
         ['Chief operator. The caller you had at ten rang the operator',
          'instead. She is not angry, she is just out of ways to try.']),
        (CHANNEL_WRITE, 'wfinch',
         ['Station to desk. Nothing wrong with the set. Nothing wrong with',
          'the drop. I have told them somebody will call and I would rather',
          'somebody did.']),
    ),

    'radio': (
        (CHANNEL_ORDERWIRE, 'tnakamura',
         ['Transmission to radio. Fade margin on the Chester hop is down',
          'four dB and it is raining on it. That is weather, not a fault,',
          'and there is nothing on the ground to go and look at.']),
        (CHANNEL_WRITE, 'gvasquez',
         ['A path that fades on a clear morning is a dish that has moved.',
          'Winter does it. Nobody notices until spring.']),
        (CHANNEL_TELETYPE, 'carot',
         ['*** TH-3 ROUTE 4 - DIVERSITY SWITCH TO PROTECTION 07:41',
          '*** RESTORED 07:58 - NO ACTION INDICATED']),
        (CHANNEL_ORDERWIRE, 'tnakamura',
         ['Transmission to radio. Somebody is going to ask you why we do',
          'not put it on satellite. Half a second, is why.']),
    ),

    'tnds': (
        (CHANNEL_TELETYPE, 'carot',
         ['*** OVERNIGHT COLLECTION COMPLETE - 41 OFFICES REPORTING',
          '*** 2 OFFICES NO DATA - JCITNJ02 NWRKNJ07']),
        (CHANNEL_WRITE, 'tnakamura',
         ['Before you report a difference between two offices, find out',
          'whether it is a difference in the traffic or a difference in the',
          'counting. It is the counting more often than anybody admits.']),
        (CHANNEL_ORDERWIRE, 'dpetrak',
         ['SCC to data. That office has been engineered to a busy hour that',
          'stopped being the busy hour in 1980.']),
        (CHANNEL_TELETYPE, 'adm',
         ['tnds: collection window 0100-0400 - 3h 12m elapsed',
          'tnds: 1 retransmission requested']),
    ),

    'sarts': (
        (CHANNEL_ORDERWIRE, 'gvasquez',
         ['Test centre to specials. Both ends measure in limits and the',
          'circuit is still down. That is the whole job, that sentence.']),
        (CHANNEL_WRITE, 'rjohnson',
         ['Get the layout record before you ring anybody. Half of what',
          'comes to that desk is somebody testing a section that was',
          'rearranged in 1979 and is not in the circuit any more.']),
        (CHANNEL_ORDERWIRE, 'tnakamura',
         ['Transmission to specials. The customer on that private line runs',
          'a data set on it and they will know before we do.']),
        (CHANNEL_TELETYPE, 'carot',
         ['*** ROTL SEIZURE FAILED - CKT 27-DATA-0088',
          '*** RETRY SCHEDULED 0300']),
    ),

    'docprep': (
        (CHANNEL_WRITE, 'dpetrak',
         ['The addendum supplements the practice, it does not replace it.',
          'Both go out. I know. I have said this before.']),
        (CHANNEL_WRITE, 'ehalloran',
         ['Every practice with the words Bell System on the cover needs',
          'looking at before January and there are four hundred of them.']),
        (CHANNEL_TELETYPE, 'adm',
         ['lpd: 2 jobs queued, 31 pages',
          'lpd: /dev/lp paper low']),
        (CHANNEL_WRITE, 'tnakamura',
         ['If it is coming out mangled it is nf and fi in the wrong place.',
          'It is always nf and fi in the wrong place.']),
    ),
}

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
        # (kind, first line) of what has been said lately, so that
        # chatter and advice do not crowd each other out.
        self._recent: List[tuple] = []

    # -- construction ----------------------------------------------------

    def _pick(self, pool: Sequence[tuple], kind: str) -> Optional[tuple]:
        """
        Choose something from a pool that has not been said lately.

        This used to draw one at random, ask whether it had been said
        recently, and return nothing if it had - so the interruption was
        silently dropped rather than replaced. With a window of eight and
        an advice pool of seven, that meant 99.7 per cent of advice was
        thrown away: after the first few hints the older hands never spoke
        again. Ambient chatter fared better and still lost 63 per cent.

        The building noise is most of what this simulation is for, so
        losing two thirds of it to a dedup was expensive. Drawing from what
        has NOT been said costs the same and loses nothing: only a pool
        entirely used up inside its own window comes back empty, and then
        the caller is right to say nothing.
        """
        if not pool:
            return None
        fresh = [item for item in pool
                 if (kind, item[-1][0]) not in self._recent]
        if not fresh:
            return None
        chosen = self.rng.choice(fresh)
        self._recent.append((kind, chosen[-1][0]))
        # Half the smaller pool, so a pool of seven repeats no sooner than
        # every fourth time and a pool of thirteen no sooner than every
        # seventh, rather than one window fitting every pool badly.
        window = max(2, min(len(pool) // 2, 12))
        while len(self._recent) > window:
            self._recent.pop(0)
        return chosen

    def _deliver(self, message: Message) -> Message:
        """File a message where it belongs and return it."""
        self.log.append(message)
        if message.channel == CHANNEL_MAIL:
            self.mailbox.append(message)
        return message

    # -- traffic ---------------------------------------------------------

    def chatter(self, now: datetime,
                position: Optional[str] = None) -> Optional[Message]:
        """
        Return an ambient message, or None if the pool is used up.

        A position hears its own people on top of the whole building, not
        instead of it: a document preparation desk still gets CAROT
        printing trunk exceptions, because the teletype does not care who
        is sitting there.
        """
        pool = tuple(_CHATTER) + tuple(_POSITION_CHATTER.get(position or '', ()))
        picked = self._pick(pool, 'chatter')
        if picked is None:
            return None
        channel, sender, lines = picked
        return self._deliver(Message(
            channel=channel, sender=sender, received=now, lines=list(lines),
            kind='chatter', subject=lines[0][:40], about=None,
        ))

    def hint(self, now: datetime) -> Optional[Message]:
        """Return advice from one of the older hands."""
        picked = self._pick(_HINTS, 'hint')
        if picked is None:
            return None
        sender, lines = picked
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

    def weather(self, now: datetime, change: str) -> Message:
        """
        Somebody looking out of the window, which is a maintenance report.

        Rain is the documented reason wet cable gets worse, so a change in
        the weather is operational news on a repair position and not
        scenery. It comes from the frame because the frame is where the
        window is.
        """
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='rjohnson', received=now,
            lines=[change,
                   'Anything you have on a wet sheath is about to get '
                   'busier.'] if 'started raining' in change else [change],
            kind='weather', subject='Weather', about=None,
        ))

    def office_assignment(self, now: datetime, clli: str, city: str,
                          trouble: str, standing: int) -> Message:
        """
        The control centre putting an office on you for the tour.

        This is what the switching control centre sign-off is for: one
        maintenance administrator watching a group of buildings and handing
        one out when it wants looking at.
        """
        return self._deliver(Message(
            channel=CHANNEL_ORDERWIRE, sender='dpetrak', received=now,
            lines=[
                'SCC to office.',
                f'{clli} at {city} is yours for the tour. {standing} '
                f'alarm{"" if standing == 1 else "s"} standing,',
                f'the one that matters is {trouble}.',
                f"'connect {clli}' when you have a gap.",
            ],
            kind='office', subject=f'{clli} assigned', about=clli,
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
        'Station': 'wfinch',
    }

    def field_call(self, now: datetime, report_number: str,
                   finding: str, force: str = 'Outside plant',
                   crew: Optional[str] = None) -> Message:
        """
        The dispatched force calling in from the field.

        Names the crew that actually went where one is known. The report
        has recorded who it was since named field forces were built; this
        call was still coming in as the cable splicer whoever went.
        """
        sender = self.FORCE_SENDERS.get(force, 'lokafor')
        if crew:
            for login, person in CRAFT.items():
                if person.name == crew:
                    sender = login
                    break
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
