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
from typing import (
    Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple,
)

from .data import consequences
from .data.consequences import Late
from .data.tours import (
    EARLY, LAST, LATE, MIDDLE, WATCHES, Window, heard_on,
)

# How the audit at the end of the last tour came out (screens/turnover.py).
AUDIT_PASSED = 'PASSED'
AUDIT_EXCEPTIONS = 'PASSED WITH EXCEPTIONS'
AUDIT_FAILED = 'FAILED'

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


# The three watches of a day (``data/tours.py`` says which a tour is worked
# on), with the bands the shift briefing prints.
WATCH_LABELS: Dict[str, str] = {
    'day': 'Day Shift (08:00-16:00)',
    'evening': 'Evening Shift (16:00-24:00)',
    'night': 'Night Shift (24:00-08:00)',
}


def watch_at(when: datetime) -> str:
    """
    Which watch of the day an hour on the clock falls in.

    Only for a clock that is the real one (``date.source`` set to ``real``).
    A simulated tour starts at 08:00 whichever watch it is worked on, so
    there the tour says (``tours.watch_of``).
    """
    if 8 <= when.hour < 16:
        return 'day'
    if 16 <= when.hour < 24:
        return 'evening'
    return 'night'


class Craft(NamedTuple):
    """One of the other people working the network tonight."""

    login: str
    name: str
    title: str
    location: str
    tty: str
    # How this person tends to come at you.
    manner: str
    # The watches they are on. Most of the building is staffed round the
    # clock; a few are a day job. The simulation's own, set from what each
    # job was (narrative-bible.md section 4); nothing says otherwise.
    # Dispatch ignores it: a crew is called out, not asked in.
    watches: Tuple[str, ...] = WATCHES


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
        'from the kitchen phone as often as from a terminal box.',
        watches=('day', 'evening')),
    'jsandoval': Craft(
        'jsandoval', 'Sandoval, J.', 'Cable Splicer',
        'FIELD_SUP', '11',
        'Second splicer. Newer than Okafor and says less, which the wire '
        'chief has noticed and has not decided about.'),
    'abright': Craft(
        'abright', 'Bright, A.', 'Lineman',
        'FIELD_SUP', '12',
        'Aerial and buried plant between the office and the drop. Calls in '
        'from wherever the ladder is.',
        watches=('day',)),
    'jhaverty': Craft(
        'jhaverty', 'Haverty, J.', 'Chief Operator',
        'TSPS_NEWARK', '10',
        'Runs a room of operator positions. Everything she brings you is a '
        'call somebody is still holding.',
        watches=('day', 'evening')),
    'adm': Craft(
        'adm', 'ADM', 'System accounting',
        'CENTRAL_OFF', '08',
        'Not a person. The machine writing its own record, in the register '
        'a machine writes in.'),
    'tnakamura': Craft(
        'tnakamura', 'Nakamura, T.', 'Transmission Engineer',
        'TRANS_CTR', '05',
        'Carrier and toll. Talks in dB and will correct you if you do not.',
        watches=('day',)),
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
    # The key of the arc beat this is, when it is one. The caller files it
    # in the career so that a beat is said once.
    beat: str = ''


class ArcBeat(NamedTuple):
    """
    One thing a person says once, on the tours it fits.

    The simulation's own. A beat is the story arriving on a channel the
    building already has: one or two lines, never a scene, and nothing the
    player has to answer (plan.md anti-pillar 1).

    The sender has to be on the watch the tour is worked on or the beat waits
    for a tour they are, so a beat from a day-only person in a window of
    night tours would never be said. Every sender here is on every watch.
    """

    key: str
    channel: str
    sender: str
    window: Window
    lines: Tuple[str, ...]


# Ambient chatter. Nothing here needs an answer; it is the sound of the
# building. Each entry is a channel, a sender and the words.
_CHATTER: Sequence[tuple] = (
    (CHANNEL_WRITE, 'rjohnson',
     ['Frame is warm again in aisle four. If you get a batch of reports off',
      'one cable this shift, look at the horizontals before you send anybody',
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
      'this shift. If a trunk goes quiet on you, it is us, not the plant.']),
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
    # Said on part of the countdown only (data/tours.py windows). The
    # simulation's own; each is a person looking at the same calendar.
    (CHANNEL_MAIL, 'ehalloran',
     ['Work the report nearest its commitment first, unless the plant gives',
      'you a reason not to.'], EARLY),
    (CHANNEL_MAIL, 'ehalloran',
     ['Anything still open at handoff goes over as it stands.',
      'Close what you can.'], MIDDLE),
    (CHANNEL_ORDERWIRE, 'dpetrak',
     ['SCC to office. Routine. No action, and I expect to say the same',
      'thing to you in January under another name.'], LATE),
    (CHANNEL_WRITE, 'rjohnson',
     ['Wired up the last of the spare shelves today. Whoever has the frame',
      'next will find them where I left them.'], LATE),
    (CHANNEL_ORDERWIRE, 'dpetrak',
     ['SCC to office. Routine. No action, logged the same as the others.'],
     LAST),
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

# What the wire chief adds, by how many sign-offs you now hold. He signs
# every one of them, so a fixed line would make him a form letter. Anything
# past the fifth falls back to the first, which is where he started and
# where he stays: he is not effusive.
_SIGN_OFF_REMARKS: Dict[int, Tuple[str, ...]] = {
    1: ('Do not work anything you are not signed off on.',),
    2: ('Second one. You are past the part where everybody helps you.',),
    3: ('Third. I have signed three for you now and I do not sign three',
        'for everybody. Whatever happens in January, that is a fact about',
        'you and not about the company.',
        'You are in the adm group as of this morning. That opens the',
        'accounting records, /usr/adm/sulog included, which you will find',
        'has your name in it.'),
    4: ('Fourth. You are quicker on the board than I was at this point,',
        'which I am telling you once and will not repeat.'),
    5: ('Fifth. There is not much left that I can sign.',),
}


# Which login a person is, by the name the field force knows them by.
CRAFT_BY_NAME: Dict[str, str] = {
    person.name: login for login, person in CRAFT.items()}

# People away for whole tours, by login: Okafor is out on tours 12 and 13
# (narrative-bible T3, which has Sandoval take the sheath nobody else will).
# The simulation's own.
AWAY: Dict[str, Window] = {'lokafor': (12, 13)}


def is_away(login: str, tour: int) -> bool:
    """Whether this person is out for the whole of this tour."""
    return login in AWAY and heard_on(AWAY[login], tour)


def on_shift(login: str, watch: str, tour: Optional[int] = None) -> bool:
    """
    Whether this person is in on this watch of this tour.

    Anyone who is not a person on the roster (a machine, a name from an
    older save) is always on: nothing here has the standing to say they are
    not. With no tour given, nobody is away.
    """
    person = CRAFT.get(login)
    if person is None:
        return True
    if tour is not None and is_away(login, tour):
        return False
    return watch in person.watches


def _by_the_clock(login: str, when: datetime) -> bool:
    """Who is in, for a room nobody has told which tour it is."""
    return on_shift(login, watch_at(when))


# The story, said once each, in the order they are due. The simulation's own;
# the people and what is known of them are narrative-bible.md sections 4 and
# 5, and each beat keeps to its speaker's profile there. Two lines at most,
# nothing the player must answer, and no beat explains what the machine
# keeps for the player to find (T2 and T3 stay open).
ARC_BEATS: Tuple[ArcBeat, ...] = (
    # Alvarez has no login and no terminal, so is spoken of, not heard.
    ArcBeat('alvarez.1', CHANNEL_MAIL, 'ehalloran', (2, 4), (
        'The position had somebody on it before you. R. Alvarez.',
        'testlog.c in /usr/src/cmd is theirs. The log it writes is yours now.',
    )),
    ArcBeat('sandoval.1', CHANNEL_ORDERWIRE, 'jsandoval', (4, 7), (
        'Field to test desk. Small-count aerial on Grand is spliced and tested.',
        'If you have more of that size, send them to me.',
    )),
    ArcBeat('reyes.1', CHANNEL_WRITE, 'mreyes', (5, 8), (
        '{number} on {tel}, closed {time}. They want it opened again.',
        'I can only give them a new number. Is there another way?',
    )),
    ArcBeat('sandoval.2', CHANNEL_ORDERWIRE, 'jsandoval', (8, 10), (
        'Field to test desk. The memo says my employment continues.',
        'I have read it twice. I looked for which company it means.',
    )),
    ArcBeat('reyes.2', CHANNEL_WRITE, 'mreyes', (9, 11), (
        '{number} on {tel}, closed {time}. They ask who has it in February.',
        'I said the trouble card for the line carries on. Is that right?',
    )),
    ArcBeat('alvarez.2', CHANNEL_WRITE, 'ehalloran', (10, 12), (
        'Alvarez rang this morning to ask how the position was going.',
        'I said it was being worked. That was the whole call.',
    )),
    ArcBeat('sandoval.3', CHANNEL_ORDERWIRE, 'jsandoval', (12, 13), (
        'Field to test desk. Okafor is not on this shift. I have the Franklin '
        'sheath.',
        'It is a big count and I will be slow on it. I will do it.',
    )),
)


# -- rapport -----------------------------------------------------------------
#
# Goodwill with the people who work for you, 0 to 5, kept in the career by
# login. The simulation's own. A report closed right earns the person who
# worked it a point; closed wrong, they lose one; either happens once per
# person per tour. Nothing is spent and nothing is shown: at the threshold
# one of them does you one good turn, once, and that is the whole of it.

RAPPORT_MAX = 5
FAVOUR_AT = 3

# What each of them says when the favour comes. {number} is the report whose
# commitment moves, {until} its new time. All of them are an hour.
FAVOURS: Dict[str, Tuple[str, ...]] = {
    'mreyes': ('I rang them and asked for another hour. They gave it.',
               '{number} is due {until}.'),
    'lokafor': ('Rang the customer from the box. They will wait an hour.',
                '{number}, due {until}. It is mine.'),
    'jsandoval': ('I told the customer an hour more.',
                  '{number}, due {until}.'),
    'wfinch': ('I was at the door. They said an hour more is all right.',
               '{number} is due {until}.'),
    'abright': ('Told the customer from the pole. An hour.',
                '{number}, due {until}.'),
    'tnakamura': ('Sixty minutes added against {number}. It is now due '
                  '{until}.',),
}

FAVOUR_MINUTES = 60


def rapport_with(crew: Optional[str]) -> str:
    """Who a report's close is owed to: the crew that went, else the bureau."""
    for login, person in CRAFT.items():
        if crew and person.name == crew and login in FAVOURS:
            return login
    return 'mreyes'


def adjust_rapport(rapport: Dict[str, int], ledger: List[str], login: str,
                   tour: int, step: int) -> bool:
    """
    Move one person's rapport by a step, if they have not moved this tour.

    Clamped 0 to RAPPORT_MAX. A gain and a loss are each allowed once per
    person per tour, and the ledger (the career's ``beats_seen``) is what
    remembers it across a save. Returns whether anything was recorded.
    """
    key = f'rapport{"+" if step > 0 else "-"}:{login}:{tour}'
    if key in ledger:
        return False
    ledger.append(key)
    rapport[login] = max(0, min(RAPPORT_MAX, rapport.get(login, 0) + step))
    return True


def favour_due(rapport: Dict[str, int], ledger: List[str],
               is_in: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """
    The first person at the threshold who has not yet done their favour.

    Given who is in, only somebody who is: a favour waits for the person to
    be there.
    """
    for login in FAVOURS:
        if (rapport.get(login, 0) >= FAVOUR_AT
                and f'favour:{login}' not in ledger
                and (is_in is None or is_in(login))):
            return login
    return None


class Switchroom:
    """
    Generates the traffic the other craft put on your terminal.

    The terminal asks this for an interruption after a command and gets one
    at the difficulty's rate, or nothing. Mail accumulates whether it is read
    or not, as mail does.
    """

    def __init__(self, rng: Optional[random.Random] = None,
                 arcs: Optional[Sequence[ArcBeat]] = None,
                 present: Optional[Callable[[str, datetime], bool]] = None):
        self.rng = rng or random.Random()
        # Whether a person is in at a given moment. The terminal supplies
        # this from the tour being worked (the board and the clock do not
        # agree on the hour); a room with none goes by the clock.
        self.present: Callable[[str, datetime], bool] = present or _by_the_clock
        self.mailbox: List[Message] = []
        self.log: List[Message] = []
        # The story beats there are to say. Handed in by tests; otherwise
        # the table at the foot of this module.
        self.arcs: Sequence[ArcBeat] = ARC_BEATS if arcs is None else arcs
        # (kind, first line) of what has been said lately, so that
        # chatter does not crowd itself out.
        self._recent: List[tuple] = []
        # Reports the board has already been chased over, once each.
        self._chased: set = set()

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
                 if (kind, item[2][0]) not in self._recent]
        if not fresh:
            return None
        chosen = self.rng.choice(fresh)
        self._recent.append((kind, chosen[2][0]))
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

    def chatter(self, now: datetime, position: Optional[str] = None,
                tour: Optional[int] = None) -> Optional[Message]:
        """
        Return an ambient message, or None if the pool is used up.

        A position hears its own people on top of the whole building, not
        instead of it: a document preparation desk still gets CAROT
        printing trunk exceptions, because the teletype does not care who
        is sitting there. A line tagged for part of the countdown is
        offered only on those tours; with no tour given, all of them are.
        """
        pool = tuple(_CHATTER) + tuple(_POSITION_CHATTER.get(position or '', ()))
        if tour is not None:
            pool = tuple(item for item in pool
                         if len(item) < 4 or heard_on(item[3], tour))
        # Only whoever is on the watch it is can say anything: the order
        # wire, the mail and the write(1) traffic all come from somebody.
        pool = tuple(item for item in pool if self.present(item[1], now))
        picked = self._pick(pool, 'chatter')
        if picked is None:
            return None
        channel, sender, lines = picked[:3]
        return self._deliver(Message(
            channel=channel, sender=sender, received=now, lines=list(lines),
            kind='chatter', subject=lines[0][:40], about=None,
        ))

    def next_message(self, now: datetime, tour: int,
                     position: Optional[str] = None,
                     overdue: Sequence[Late] = (),
                     seen: Sequence[str] = (),
                     recall: Optional[Late] = None) -> Optional[Message]:
        """
        Whatever one of the other craft would say next, in a fixed order.

        The story first: an arc beat whose tours these are and which has
        not been said. Then the board: somebody asking after a report that
        has passed its commitment. Then the building, which is random and
        is the only part that is. A random line never gets in front of
        something that was about to happen.

        Args:
            now: When it is said
            tour: Which tour of the career, 1-13
            position: The desk, for the chatter only that desk hears
            overdue: The reports past their commitment
            seen: Keys of beats already said, from the career
            recall: A report to speak of, for the beats that are about one;
                its ``committed`` is the time to give. Without one those
                beats wait, since Reyes does not speak without a report.
        """
        beat = self._arc_beat(now, tour, seen, recall)
        if beat is not None:
            return beat
        board = self._board_driven(now, overdue, seen)
        if board is not None:
            return board
        return self.chatter(now, position=position, tour=tour)

    def _arc_beat(self, now: datetime, tour: int, seen: Sequence[str],
                  recall: Optional[Late] = None) -> Optional[Message]:
        """The first arc beat that fits this tour and has not been said."""
        for beat in self.arcs:
            if beat.key in seen or not heard_on(beat.window, tour):
                continue
            if not self.present(beat.sender, now):
                continue
            about = '{number}' in ''.join(beat.lines)
            if about and recall is None:
                continue
            lines = [line.format(
                number=recall.number if recall else '',
                tel=recall.telephone if recall else '',
                time=recall.committed if recall else '') for line in beat.lines]
            return self._deliver(Message(
                channel=beat.channel, sender=beat.sender, received=now,
                lines=lines, kind='beat', subject=lines[0][:40],
                about=recall.number if about and recall else None,
                beat=beat.key,
            ))
        return None

    def _board_driven(self, now: datetime, overdue: Sequence[Late],
                      seen: Sequence[str] = ()) -> Optional[Message]:
        """
        Someone asking after a late report nobody has yet spoken of.

        Said at most once per report, the career's ``chased:`` entries
        making that true across a save, and never for one the attendant
        already raised when its commitment passed (``overdue_notice``).
        """
        for late in overdue:
            if (late.number not in self._chased
                    and f'chased:{late.number}' not in seen):
                self._chased.add(late.number)
                return self.chase(now, late)
        return None

    def advice(self, now: datetime, sender: str, lines: List[str],
               level: int) -> Message:
        """
        A hint somebody asked for, from whoever would give it.

        It only ever arrives because the operator typed hint(1), which is
        the whole reason it can afford to be direct. Nobody offers advice
        on their own: the readings already say what they mean, and the
        older hands are not going to say it a fourth time.
        """
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender=sender, received=now,
            lines=list(lines), kind='advice',
            subject=f'Hint {level}', about=None,
        ))

    def moo_beaten(self, now: datetime,
                   guesses: int) -> Optional[Message]:
        """
        Okafor, on somebody taking her eleven off the board.

        Her position on that eleven is a matter of record - she maintains
        the terminal was dropping characters and that she has witnesses -
        so the scoreboard was never going to change quietly. Unless she is
        not there to say so: nobody else has her line, so while she is away
        (``AWAY``) the scoreboard changes quietly after all.
        """
        if not self.present('lokafor', now):
            return None
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='lokafor', received=now,
            lines=[
                f'Somebody just did it in {guesses}.',
                'I want it on the record that mine was not an eleven. That',
                'terminal was dropping characters and there were people in',
                'the room.',
                'Good number though.',
            ],
            kind='chatter', subject='moo', about=None,
        ))

    def last_word(self, now: datetime, tours: int, closed: int,
                  qualifications: int,
                  verdict: str = AUDIT_PASSED) -> Message:
        """
        What the wire chief says at the end of the last tour.

        He has been reading the service index every morning for however
        long this took, and he signed every qualification on the record.
        He does not make a speech about it, because he would not.

        The audit changes what he says and not how long the career was: it
        had its say on the same page, and he does not pretend it did not.
        """
        lines = [
            'That is the tour, and that is the company.',
            f'{tours} tours and {closed} reports off the board. I signed '
            f'{qualifications} of your',
            'qualifications and I stand behind every one of them.',
        ]
        if qualifications >= 5:
            lines.append('You were better at it than most of the people '
                         'who trained you.')
        # The qualifications are still signed and still his. What the audit
        # takes back is the claim that nobody there will argue, and it says
        # so after the praise rather than in front of it.
        if verdict == AUDIT_EXCEPTIONS:
            lines.extend(['The audit found some things. They are on the '
                          'record with your name,', 'and so is the rest of '
                          'it.'])
            closing = ['morning, the record says what you can work.']
        elif verdict == AUDIT_FAILED:
            lines.append('The audit did not go your way and I am not going '
                         'to tell you it did.')
            closing = ['morning, the record says what you can work. The '
                       'audit says how you did it.', 'Read both.']
        else:
            closing = ['morning, the record says what you can work and '
                       'nobody there', 'is going to argue with it.']
        lines.extend([
            '',
            'They go with you. Whichever of the seven you end up at in the',
            *closing,
            'Go home.',
        ])
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='ehalloran', received=now,
            lines=lines, kind='nudge', subject='Last tour', about=None,
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

    def chief_nudge(self, now: datetime, lines: List[str]) -> Message:
        """
        The wire chief walking a new craftsperson through one report.

        This is the whole of the tutorial. It arrives on write(1) from the
        man who signs your qualifications, because that is who would do it
        and because the channel already exists.
        """
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='ehalloran', received=now,
            lines=list(lines), kind='nudge', subject='First tour',
            about=None,
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

    def chase(self, now: datetime, late: Late) -> Message:
        """
        Ask, once, about a report that has passed its commitment.

        A customer with no telephone reaches the attendant, and she says
        what they said. A customer who still has service reaches nobody:
        the question is the wire chief's, and it is about the index.
        """
        if late.out_of_service:
            sender = 'mreyes'
            lines = self._gone_lines(late)
        else:
            sender = 'ehalloran'
            lines = [
                f'{late.number} is past commitment.',
                'I would like it cleared or dispatched before the index run.',
            ]
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender=sender, received=now, lines=lines,
            kind='chase', subject=f'{late.number} past commitment',
            about=late.number,
        ))

    @staticmethod
    def _gone_lines(late: Late) -> List[str]:
        """Reyes on a line out of service past its time: theirs, then hers."""
        return [
            f'{late.number} on {late.telephone} was due {late.committed} '
            f'and has gone. What do I tell them?',
            consequences.overdue(late.class_of_service),
        ]

    def overdue_notice(self, now: datetime, report_number: str,
                       telephone_number: str,
                       late: Optional[Late] = None) -> Message:
        """
        The attendant, once, on a report that has just passed its commitment.

        Not random and not repeated: it is said when the commitment passes,
        whoever was or was not working the report, and then not again. Given
        the report's class of service and whether the line is out, she says
        what that customer said; the board-driven ``chase`` then leaves the
        report alone, since she has already raised it.
        """
        self._chased.add(report_number)
        if late is not None and late.out_of_service:
            lines = self._gone_lines(late)
        else:
            lines = [
                f'{report_number} is past its commitment.',
                f'{telephone_number} is on the line asking when. I told',
                'them a time and it has gone. What do I tell them now?',
            ]
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='mreyes', received=now,
            lines=lines,
            kind='escalation', subject=f'{report_number} past commitment',
            about=report_number,
        ))

    @staticmethod
    def _repeat_lines(report_number: str, original: str,
                      telephone_number: str, class_of_service: str,
                      committed: str) -> List[str]:
        """The customer's second call: the report, then their words."""
        due = f' Due {committed}.' if committed else ''
        return [
            f'{report_number} is back on {telephone_number}, a repeat of '
            f'your {original} close.{due}',
            consequences.second_call(class_of_service),
        ]

    def repeat_notice(self, now: datetime, report_number: str,
                      original: str, telephone_number: str,
                      class_of_service: str = '',
                      committed: str = '') -> Message:
        """Tell you a report you closed has come back, and who rang."""
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='mreyes', received=now,
            lines=self._repeat_lines(report_number, original,
                                     telephone_number, class_of_service,
                                     committed),
            kind='repeat', subject=f'{report_number} repeat report',
            about=report_number,
        ))

    def with_class(self, message: Message, original: str,
                   telephone_number: str, class_of_service: str,
                   committed: str) -> Message:
        """
        Say a repeat again with what the caller of it did not have to hand.

        The bureau files the notice when the report comes back and knows the
        number and the code; the class of service and the new commitment are
        on the report. This is a workaround: the fix is to pass them where
        the notice is made (``bureau.py`` ``_close_report``), which is not
        this phase's file. The earlier log entry is replaced, not added to.
        """
        assert message.about is not None
        again = message._replace(lines=self._repeat_lines(
            message.about, original, telephone_number, class_of_service,
            committed))
        if message in self.log:
            self.log[self.log.index(message)] = again
        return again

    def call_back(self, now: datetime, report_number: str,
                  telephone_number: str, class_of_service: str,
                  closed: str) -> Message:
        """A customer ringing the bureau to say a close held."""
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender='mreyes', received=now,
            lines=[
                f'{report_number} on {telephone_number}, closed {closed}.',
                consequences.call_back(class_of_service),
            ],
            kind='callback', subject=f'{report_number} call-back',
            about=report_number,
        ))

    def rings_back(self, report_number: str, ledger: List[str]) -> bool:
        """
        Whether this clean close draws a call.

        Decided once per report. The ledger is the career's ``beats_seen``,
        which is what makes once true after a save and a resume.
        """
        key = f'rang:{report_number}'
        if key in ledger:
            return False
        ledger.append(key)
        return self.rng.random() < consequences.CALL_BACK_CHANCE

    def favour(self, now: datetime, login: str, report_number: str,
               until: str) -> Message:
        """Somebody who owes you nothing doing you a good turn, once."""
        lines = [line.format(number=report_number, until=until)
                 for line in FAVOURS[login]]
        return self._deliver(Message(
            channel=CHANNEL_WRITE, sender=login, received=now, lines=lines,
            kind='favour', subject=f'{report_number} favour',
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
        if not self.present(sender, now):
            # Dispatch does not care who is on the watch: a crew is called
            # out (``field_call`` is made for a crew that was sent, and its
            # name wins below). Only the voice does, so with no crew named
            # it is a splicer who rings in, out in it at any hour.
            sender = 'lokafor' if self.present('lokafor', now) else 'jsandoval'
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

    def practical_offer(self, now: datetime, name: str,
                        key: str) -> Message:
        """
        The wire chief saying a sign-off is there to be taken.

        The count of correct closures is the floor. He will not sign on a
        count, and says so once, with the one command that moves it along.
        """
        return self._deliver(Message(
            channel=CHANNEL_MAIL, sender='ehalloran', received=now,
            lines=[
                f'You have the closures for {name}.',
                'I do not sign on a count. I will set you up a line to work',
                f"that wants what {name} is for. 'qual take {key}'.",
            ],
            kind='qualification', subject=f'Practical: {name}',
            about=None,
        ))

    def qualification_notice(self, now: datetime, name: str,
                             commands: Sequence[str],
                             held: int = 1, days_left: int = 48) -> Message:
        """
        The wire chief signing off a qualification.

        He signs all of them, so what he says has to change or he is a
        form letter. The first is business. By the third he has been
        watching long enough to say something about the person rather than
        about the sign-off, and with the company weeks from ending, what
        that sign-off is worth is a question he cannot honestly duck.
        """
        lines = [
            f'You are signed off on {name}.',
            'That opens: ' + ', '.join(commands) + '.',
        ]
        lines.extend(_SIGN_OFF_REMARKS.get(
            held, ('Do not work anything you are not signed off on.',)))
        if held >= 3 and days_left <= 14:
            lines.append(f'For whatever it is worth with {days_left} days '
                         f'left of the company.')
        return self._deliver(Message(
            channel=CHANNEL_MAIL, sender='ehalloran', received=now,
            lines=lines,
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
