"""
The thirteen tours: a date, a reason and one thing that happens on each.

A career walks from 14 November 1983 to the last day of the Bell System in
thirteen tours, four days apart, the last pulled back onto 31 December
(``clock.py``). Until now they were the same tour thirteen times; this
gives each of them a shape - build, crisis, relief, farewell - and a
calendar to hang it on.

What is in an entry:

* a **theme** and a **kind**, and a short briefing printed with the shift;
* **beats**, the dated set pieces that go on the board and come due as the
  tour is worked. They replace the boilerplate that used to sit in
  ``shift_events.py``: fixed event numbers, the same three events every
  shift, and a Pentagon line and a microwave path out of New York for a
  desk in New Jersey;
* **goals**, two or three things to aim for, struck at handoff. They are
  not scored. The service index is the only score, and a goal that moved
  it would be a second one to keep honest;
* **news**, the one article the nightly feed brings in on that tour, so
  ``readnews`` is not the same list on 22 December as on 14 November.

Provenance follows ``SOURCES.md``. Every beat and every article says which
it is: ``SOURCED``, resting on a document in this repository or a row in
SOURCES.md, or ``OWN``, which the simulation made up. The briefings and
goals are the simulation's own throughout. The calendar is pinned in
docs/design/plan.md section 6:

* 14 November 1983 is the career epoch and the first tour (repo, clock.py).
* Thanksgiving was Thursday 24 November 1983 (SOURCES.md, derived).
* Christmas Day was Sunday 25 December 1983.
* The August strike ran 7-28 August 1983 (SOURCES.md, ``net.misc/88``).

Nothing is claimed about the weather on any of these days, and nothing
is put in the mouth of a real person: every poster in the news is made up.
Tours 4, 6, 11 and 13 fall on a weekend, so no copy here says "Monday".
A player who moves the epoch or reads the host clock is on a different
calendar, and ``script`` then returns nothing rather than describe 24
November on some other day.
"""

import random
from datetime import date, datetime
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple

Event = Dict[str, Any]

SOURCED = 'SOURCED'
OWN = 'OWN'

# The counts a goal can ask about. All of them are read off the tour that
# is being worked, or off the board as it stands, by the turnover screen.
METRICS = ('closed', 'correct', 'wrong', 'missed', 'repeats', 'carried',
           'late', 'unmeasured')

# What the briefing and a goal are written in, whatever else is going on.
KINDS = ('build', 'crisis', 'relief', 'farewell')

# The three watches of a day, and the hour of the clock each starts at.
WATCHES = ('day', 'evening', 'night')
WATCH_START_HOUR: Dict[str, int] = {'day': 8, 'evening': 16, 'night': 0}


class Beat(NamedTuple):
    """
    One dated set piece on a tour's board.

    Text may name ``{city}``, ``{clli}`` and ``{switch}``, which are the
    player's own office. Nothing else here may name a place.
    """

    at: str
    type: str
    priority: str
    status: str
    title: str
    description: str
    details: str
    actions: Tuple[str, ...]
    origin: str
    source: str


class Goal(NamedTuple):
    """A thing to aim for in a tour. Never scored."""

    text: str
    metric: str
    op: str
    target: int

    def met(self, counts: Mapping[str, int]) -> bool:
        """Whether the tour's counts satisfy this goal."""
        value = counts[self.metric]
        return value >= self.target if self.op == '>=' else value <= self.target


class NewsItem(NamedTuple):
    """One article the nightly feed brings in on a tour."""

    group: str
    number: int
    posting: str
    path: str
    sender: str
    subject: str
    message_id: str
    posted: datetime
    body: str
    origin: str
    source: str


class Tour(NamedTuple):
    """Everything that is particular to one tour of the career."""

    number: int
    day: date
    theme: str
    kind: str
    # Which watch of the day the tour is worked on (``WATCHES``): the
    # simulation's own, chosen to suit the theme. The clock starts every tour
    # at 08:00, so the hour on it cannot say who is in the building.
    watch: str
    briefing: Tuple[str, ...]
    beats: Tuple[Beat, ...]
    goals: Tuple[Goal, ...]
    news: Optional[NewsItem] = None


def _news(group: str, number: int, posting: str, sender: str, name: str,
          subject: str, serial: int, posted: datetime, body: str,
          origin: str = OWN, source: str = "the simulation's own"
          ) -> NewsItem:
    """Build an article, with a Path that ends in its poster."""
    relay = '' if posting == 'mhuxco' else f'{posting}!'
    return NewsItem(
        group, number, posting, f'mhuxco!{relay}{sender}',
        f'{sender}@{posting}.uucp ({name})', subject,
        f'<{serial}@{posting}.UUCP>', posted, body, origin, source)


TOURS: Tuple[Tour, ...] = (
    Tour(
        1, date(1983, 11, 14), 'A new board', 'build',
        'day',
        ("Your first tour. One report on the board and the wire chief on",
         "the order wire. Operations Bulletin 83-114 came out this morning."),
        (Beat(
            '08:20', 'BULLETIN', 'MEDIUM', 'PENDING',
            'Operations Bulletin 83-114 posted',
            'Operations Bulletin 83-114, dated 14 November',
            'Mechanised loop testing is the primary test method at this '
            'position. Repeat reports are running above objective. Measure '
            'before you close.',
            ('Read /usr/doc/bulletin', 'Measure before you close'),
            SOURCED, '/usr/doc/bulletin'),),
        (Goal('Close the report on your board.', 'closed', '>=', 1),
         Goal('Close it on what the line says.', 'correct', '>=', 1)),
    ),
    Tour(
        2, date(1983, 11, 18), 'Records stay', 'build',
        'day',
        ("The memo of 1 November is in force: line, cable and frame",
         "records stay with this wire centre. Work the board."),
        (Beat(
            '09:10', 'BULLETIN', 'MEDIUM', 'PENDING',
            'Records retention: copies stay in the building',
            'Retention reminder from the Vice President - Operations',
            'Line records, cable records and frame assignments stay with '
            'the wire centre at {city}. Do not remove copies. Anything in '
            '/usr/adm is retained for seven years.',
            ('Read /usr/doc/divestiture', 'Leave the records where they are'),
            SOURCED, '/usr/doc/divestiture, rules 3 and 4'),),
        (Goal('Close three reports.', 'closed', '>=', 3),
         Goal('No more than one wrong close.', 'wrong', '<=', 1)),
        _news('net.unix-wizards', 129, 'eagle', 'rvance', 'R Vance',
              'fsck after a power dip, and what lost+found is for', 3141,
              datetime(1983, 11, 17, 21, 14, 9),
              """Power dipped for under a second here Tuesday night and the machine
came up with eleven files in lost+found. All of them were temporary
files from a compile that was running at the time.

If you find files there with numbers for names, look at the first few
lines before you throw them out. Nine times in ten it is a temp file.
The tenth time it is somebody's afternoon.
"""),
    ),
    Tour(
        3, date(1983, 11, 22), 'Before the holiday', 'build',
        'evening',
        ("Thanksgiving is Thursday, after this tour. The building runs",
         "thin from tomorrow night. Leave the board in a state somebody",
         "who has never seen it could pick up."),
        (Beat(
            '10:30', 'MAINTENANCE', 'MEDIUM', 'SCHEDULED',
            'Holiday coverage: reduced staffing from Wednesday night',
            'Thanksgiving week coverage at {clli}',
            'Staffing at {city} drops to one craftsperson a tour from '
            'Wednesday night until the holiday weekend is over. Thanksgiving '
            'is Thursday 24 November. The roster is the simulation\'s own.',
            ('Hand over a board with every commitment stated',
             'Note anything that will not keep until Saturday'),
            OWN, "the simulation's own; the date is in SOURCES.md"),),
        (Goal('Close four reports before the holiday.', 'closed', '>=', 4),
         Goal('Leave no more than two past commitment.', 'late', '<=', 2)),
        _news('net.general', 215, 'ihnp4', 'mtorres', 'M Torres',
              'uucp over the holiday', 3215,
              datetime(1983, 11, 21, 17, 40, 22),
              """Nobody will be in on Thursday and the nightly poll still runs. If
your site's phone line is shared with a person, set the poll for
after two in the morning and leave the line to them until then.

Machines that call out and find no answer will retry on the next
cycle. Nothing is lost, it is only late.
"""),
    ),
    Tour(
        4, date(1983, 11, 26), 'After the holiday', 'crisis',
        'night',
        ("First tour since Thanksgiving. Reports taken over the long",
         "weekend are on the board with their commitments running.",
         "A lot of it will be the same few faults."),
        (Beat(
            '09:05', 'CUSTOMER', 'HIGH', 'ACTIVE',
            'Holiday backlog at the repair bureau',
            'Reports taken since Wednesday are on the board',
            'The repair service bureau took reports through the holiday '
            'with nobody at {clli} to work them. Commitments run from the '
            'time they were taken, not from the time you came in. How big '
            'the backlog is, in this simulation, is the simulation\'s own.',
            ('Take the oldest first', 'Measure each before dispatching'),
            OWN, "the simulation's own"),),
        (Goal('Close four reports.', 'closed', '>=', 4),
         Goal('Leave no more than two past commitment.', 'late', '<=', 2)),
        _news('net.jokes', 97, 'mhuxj', 'lbrandt', 'L Brandt',
              'cold turkey and the network layer', 3297,
              datetime(1983, 11, 25, 22, 3, 51),
              """Leftover turkey is a store-and-forward protocol. Each sandwich is a
packet, the refrigerator is the spool, and the sender never learns
which hop dropped it.

Retries are handled by the one person who is still awake at midnight.
"""),
    ),
    Tour(
        5, date(1983, 11, 30), 'Deferred work', 'build',
        'day',
        ("Maintenance that waited out the August strike is back on the",
         "schedule this week. It runs into the board."),
        (Beat(
            '11:00', 'MAINTENANCE', 'MEDIUM', 'SCHEDULED',
            'Deferred routine maintenance back on the sheet',
            'Work put off during the summer walkout is scheduled again',
            'The August strike ran from 7 to 28 August. What the simulation '
            'does with it is its own: the routining that slipped is back on '
            'the schedule at {clli}, and some of it will show up as '
            'reports before it is done.',
            ('Expect some of it to reach the board',
             'Check the sheet before you call a pair clean'),
            OWN, "the simulation's own; strike dates are in SOURCES.md"),),
        (Goal('Close five reports.', 'closed', '>=', 5),
         Goal('No more than three missed commitments.', 'missed', '<=', 3)),
        _news('net.misc', 91, 'mhuxt', 'jsandoval', 'J Sandoval',
              'three months on from the walkout', 3191,
              datetime(1983, 11, 29, 19, 12, 7),
              """The routine work we skipped in August is back on the sheet. Three
months is a long time for a frame, and it shows.

I am not going to say what that means for anyone's pay or anyone's
job. I will say the cables do not know there was a strike, and the
ones nobody looked at for a season are the ones that call in first.
"""),
    ),
    Tour(
        6, date(1983, 12, 4), 'Weekend coverage', 'relief',
        'night',
        ("A Sunday tour and a lighter one. The routine work is done",
         "and the building is quiet. Use it to measure everything that",
         "has not been measured."),
        (Beat(
            '13:00', 'SYSTEM', 'LOW', 'MONITORING',
            'Weekend routines run on schedule',
            'Trunk routines and exception reports, light load',
            'The nightly trunk routines and the exception printing ran '
            'without incident at {clli}. The maintenance teletype is quiet. '
            'The simulation\'s own weekend, no source behind it.',
            ('Read the exception printing', 'Work the board'),
            OWN, "the simulation's own"),),
        (Goal('Close three reports.', 'closed', '>=', 3),
         Goal('Measure all but two of what is on the board.',
              'unmeasured', '<=', 2),
         Goal('No more than one wrong close.', 'wrong', '<=', 1)),
        _news('net.sources', 47, 'cbosgd', 'kmaddox', 'K Maddox',
              'spool.sh: how much is waiting, by group', 3347,
              datetime(1983, 12, 3, 10, 30, 14),
              """: spool.sh - how many articles are waiting in each group
for d in /usr/spool/news/*
do
	echo `ls $d | wc -l` $d
done

That is the whole thing. Pipe it through sort -n if you want the busy
ones last.
"""),
    ),
    Tour(
        7, date(1983, 12, 8), 'Pressure watch', 'crisis',
        'evening',
        ("Pressure readings on the cable routes out of this office are",
         "due. Water gets in where pressure has been lost, and the",
         "board follows it by a day or two."),
        (Beat(
            '08:40', 'EQUIPMENT', 'HIGH', 'PENDING',
            'Cable pressure readings due on the {city} routes',
            'Readings on the pressurised sheaths out of {clli}',
            'Dry air keeps water out of the sheath, and pressure falls '
            'before water enters. The routes are read on a schedule; this '
            'one is the simulation\'s own, and no reading in it is real.',
            ('Take the readings', 'Write up any route that has fallen'),
            OWN, "the simulation's own; the principle is in SOURCES.md"),),
        (Goal('Close five reports.', 'closed', '>=', 5),
         Goal('Nothing comes back: no repeats.', 'repeats', '<=', 0)),
        _news('net.lang.c', 66, 'research', 'dwhitlock', 'D Whitlock',
              'is 0 the same as NULL?', 3366,
              datetime(1983, 12, 7, 14, 45, 38),
              """I have been writing 0 where I mean the null pointer and lint does
not complain. Is that safe everywhere, or only on the machines I have
tried it on?

(It works here. It also worked on the one machine where it did not.)
"""),
    ),
    Tour(
        8, date(1983, 12, 12), 'Inventory for transfer', 'build',
        'day',
        ("The office, its plant and its records pass to the operating",
         "company on 1 January. The inventory list is due, and the",
         "board is the part of it you can still change."),
        (Beat(
            '10:00', 'BULLETIN', 'MEDIUM', 'SCHEDULED',
            'Transfer inventory: plant and records list due',
            'The wire centre at {city} is listed for transfer',
            'This wire centre, its outside plant and its records pass to '
            'the operating company on 1 January 1984. Reports open at '
            'transfer go with them. The list itself is the simulation\'s '
            'own invention.',
            ('Read /usr/doc/divestiture', 'Close what you can close honestly'),
            SOURCED, '/usr/doc/divestiture'),),
        (Goal('Close five reports.', 'closed', '>=', 5),
         Goal('No more than one wrong close.', 'wrong', '<=', 1),
         Goal('Measure all but two of what is on the board.',
              'unmeasured', '<=', 2)),
        _news('net.unix-wizards', 133, 'cbosgd', 'pmarchetti', 'P Marchetti',
              'how long is /usr/adm kept?', 3433,
              datetime(1983, 12, 11, 20, 28, 3),
              """Our memo says anything in /usr/adm is retained for seven years. It
does not say who is going to read it in seven years.

Whoever it is will find sulog, the accounting files and the login
records, and they will be able to tell exactly who was here when. I
would write the shell scripts accordingly.
""", SOURCED, '/usr/doc/divestiture, rule 4'),
    ),
    Tour(
        9, date(1983, 12, 16), 'Close honestly', 'build',
        'evening',
        ("Rule 2 of the memo: do not close reports you have not worked",
         "to clear the board. Disposition codes are audited after",
         "transfer. The wire chief is reading them already."),
        (Beat(
            '08:45', 'MEETING', 'HIGH', 'SCHEDULED',
            'Wire chief: dispositions will be audited',
            'Reminder of rule 2 of the retention memo',
            'Do not close reports you have not worked in order to clear '
            'the board. Disposition codes are audited after transfer. What '
            'a sample looks like is the simulation\'s own.',
            ('Read /usr/doc/divestiture', 'Measure before you close'),
            SOURCED, '/usr/doc/divestiture, rule 2'),),
        (Goal('Close four reports.', 'closed', '>=', 4),
         Goal('No wrong closes.', 'wrong', '<=', 0)),
        _news('net.games', 19, 'mhuxco', 'wfinch', 'W Finch',
              'moo: what I do with the first guess', 3519,
              datetime(1983, 12, 15, 13, 5, 40),
              """After a few of these the first guess matters less than the second.
Pick four different digits, take the cows and bulls, and do not
repeat a digit until the information makes you.

My average is nine. Okafor says hers is better. I have asked to see
the scoreboard.
"""),
    ),
    Tour(
        10, date(1983, 12, 20), 'The new owners', 'relief',
        'day',
        ("Someone from the operating company walks the office this week.",
         "Nothing about the work changes. Keep the board as it is."),
        (Beat(
            '09:30', 'MEETING', 'MEDIUM', 'SCHEDULED',
            'Visit from the operating company',
            'Walk-through of the {city} wire centre',
            'A representative of the operating company walks through '
            '{clli} to see the frames and the board. Who it is, and what '
            'they ask, is the simulation\'s own.',
            ('Keep the board current', 'Answer what you are asked'),
            OWN, "the simulation's own"),),
        (Goal('Close five reports.', 'closed', '>=', 5),
         Goal('Leave no more than two past commitment.', 'late', '<=', 2)),
        _news('net.general', 219, 'ihnp4', 'sellis', 'S Ellis',
              'login names after the first', 3219,
              datetime(1983, 12, 19, 16, 52, 11),
              """If your login is going to change on the first of the year, tell
your mail correspondents now, not on the second. Mail to a name that
no longer exists goes to the postmaster, and the postmaster is
already busy.

An alias for a month is cheaper than a lost letter.
"""),
    ),
    Tour(
        11, date(1983, 12, 24), 'Christmas Eve', 'crisis',
        'evening',
        ("Christmas Day is tomorrow. On a peak day the long-haul",
         "interstate traffic runs past what the network was built for",
         "while local calling is light. Network management is getting",
         "ready, and the board still has to be worked."),
        (Beat(
            '15:00', 'TRAFFIC', 'HIGH', 'SCHEDULED',
            'Network management: controls ready for tomorrow',
            'Preparation for the Christmas Day peak',
            'Engineering and Operations describes Christmas Day as a peak-'
            'day overload: local and intrastate calling is light and long-'
            'haul interstate traffic far exceeds engineered capacity, '
            'handled with controls such as cancelling alternate routing '
            'and rerouting across time zones. What {clli} is asked to do '
            'about it is the simulation\'s own.',
            ('Keep the order wire clear', 'Do not raise anything on the '
             'trunk groups unless it is yours'),
            SOURCED, 'Engineering and Operations in the Bell System, '
                     '2nd ed. 1984, section 5.6 and Table 5-1'),),
        (Goal('Close five reports.', 'closed', '>=', 5),
         Goal('No more than three missed commitments.', 'missed', '<=', 3)),
        _news('net.jokes', 101, 'eagle', 'cnorvell', 'C Norvell',
              'the twelve days of uucp', 3601,
              datetime(1983, 12, 23, 23, 40, 2),
              """On the first day of uucp my true site sent to me: a file that
would not parse.

On the second day of uucp my true site sent to me: two retries, and a
file that would not parse.

I will spare you the rest. By the twelfth day somebody has pulled the
phone line.
"""),
    ),
    Tour(
        12, date(1983, 12, 28), 'The controls come off', 'relief',
        'night',
        ("Christmas Day is past. Anything put on for it has to be taken",
         "off, and the week between holidays is the quietest on the",
         "board. Four days left."),
        (Beat(
            '09:00', 'TRAFFIC', 'MEDIUM', 'PENDING',
            'Review controls set for the holiday',
            'After Christmas Day',
            'Whatever was set at {clli} for Christmas Day is reviewed and '
            'cleared. The simulation\'s own routine: no source fixes the '
            'procedure.',
            ('Confirm each control is off', 'Report what was cleared'),
            OWN, "the simulation's own"),),
        (Goal('Close three reports.', 'closed', '>=', 3),
         Goal('Nothing comes back: no repeats.', 'repeats', '<=', 0),
         Goal('Leave no more than one past commitment.', 'late', '<=', 1)),
        _news('net.news', 54, 'mhuxj', 'hpalmer', 'H Palmer',
              'reminder: reply-format Path lines until the first', 3654,
              datetime(1983, 12, 27, 11, 20, 45),
              """A reminder from the man who maintains the Path lines on this site:
RFC 850 requires Path lines in the reply format, something uux can
route to, until 1 January 1984.

If your site's lines do not end in the poster's name, fix them this
week.
""", SOURCED, 'RFC 850 (June 1983); SOURCES.md'),
    ),
    Tour(
        13, date(1983, 12, 31), 'The last day', 'farewell',
        'day',
        ("The last working day of the Bell System. The memo is the",
         "last thing anyone will ask you to read. Hand the board over",
         "the way you would want to be handed one."),
        (Beat(
            '12:00', 'BULLETIN', 'HIGH', 'SCHEDULED',
            'Records transfer effective tomorrow',
            'Retention and transfer, effective 1 January 1984',
            'On 1 January 1984 the office, its plant and its records pass '
            'to the operating company. Reports open at transfer are handed '
            'over with the name of whoever had them on them.',
            ('Close every report you can close honestly',
             'Hand over what you cannot'),
            SOURCED, '/usr/doc/divestiture'),),
        (Goal('Close four reports.', 'closed', '>=', 4),
         Goal('No wrong closes.', 'wrong', '<=', 0),
         Goal('Leave no more than one past commitment.', 'late', '<=', 1)),
        _news('net.misc', 94, 'mhuxco', 'rvance', 'R Vance',
              'last post of the year', 3794,
              datetime(1983, 12, 30, 18, 15, 30),
              """This is the last one I will send from the old name. The machine
does not care what company it belongs to and neither does the spool.

Whoever has the board tomorrow: it is a good office. Leave the lights
on.
"""),
    ),
)

# -- windows -----------------------------------------------------------

# Stretches of the career, as the first and last tour of each, for anything
# said by the building that fits only part of the countdown. The names are
# the simulation's own and follow the dates above: tours 1-4 are the four
# days of 14-26 November, 5-8 run 30 November to 12 December, 9-12 are
# 16-28 December and 13 is 31 December.
Window = Tuple[int, int]

EARLY: Window = (1, 4)
MIDDLE: Window = (5, 8)
LATE: Window = (9, 12)
LAST: Window = (13, 13)
ANY: Window = (1, len(TOURS))


def heard_on(window: Window, tour: int) -> bool:
    """Whether a line tagged for a window may be said on this tour."""
    return window[0] <= tour <= window[1]


# -- filler ------------------------------------------------------------

# What a wire centre had on its sheet on any shift. These are the simulation's
# own and the figures in them are invented; what is grounded is only the
# shape, a briefing of scheduled work, tests and known conditions. They name
# the player's own office and nowhere else.
_FILLER: Tuple[Tuple[Any, ...], ...] = (
    ('08:30', 'SYSTEM', 'LOW', 'MONITORING',
     'Trunk group monitoring at {clli}',
     'Daily trunk group performance cycle',
     'Trunk groups out of {clli} are within objective. Nothing is blocking.',
     ('Review the hourly figures',)),
    ('08:45', 'TEST', 'MEDIUM', 'COMPLETE',
     'Emergency service routing verified at {clli}',
     'Daily test of 911 routing from {city}',
     'Routing tested from the {switch} at {city}. Setup time inside '
     'specification.',
     ('Document the result',)),
    ('09:30', 'MAINTENANCE', 'MEDIUM', 'SCHEDULED',
     'Preventive maintenance on the {switch} at {clli}',
     'Scheduled routine, {switch}',
     'Routine maintenance on the {switch} at {city} is on the sheet. '
     'Allow for the maintenance teletype printing during it.',
     ('Read the exception printing', 'Note anything that stays open')),
    ('10:15', 'EQUIPMENT', 'MEDIUM', 'MONITORING',
     'Frame cross-connect inspection, {clli}',
     'Main distributing frame walk-through',
     'A walk of the main frame at {city} for loose jumpers and open '
     'protectors. Findings become reports.',
     ('Log what is found', 'Raise a report for anything open')),
    ('11:20', 'TRAFFIC', 'LOW', 'MONITORING',
     'Peak-hour usage study at {clli}',
     'Usage study, {switch}',
     'Usage counts are being taken on the {switch} at {city} for the '
     'engineers. They are not yours to act on.',
     ('Leave the counts alone',)),
    ('13:10', 'SYSTEM', 'LOW', 'COMPLETE',
     'Backup of the line records at {clli}',
     'Line record save',
     'The line records for {city} were saved to tape. A restore is not '
     'scheduled.',
     ('Confirm the tape is shelved',)),
    ('14:05', 'TRAINING', 'LOW', 'SCHEDULED',
     'Craft refresher at {clli}',
     'Refresher on the test desk',
     'A refresher for craft at {city} on the test desk. Attendance is '
     'taken.',
     ('Sign the attendance sheet',)),
    ('15:00', 'TEST', 'MEDIUM', 'SCHEDULED',
     'Dial tone speed test, {clli}',
     'Dial tone delay test, {switch}',
     'The dial tone speed test runs on the {switch} at {city} this '
     'shift.',
     ('Read the result when it prints',)),
)


def watch_of(tour: int) -> str:
    """
    The watch a tour is worked on.

    Not tied to the calendar the way ``script`` is: which watch it is has
    nothing to say about 24 November, so a player who has moved the epoch
    still has a day tour and a night one.
    """
    if not 1 <= tour <= len(TOURS):
        return 'day'
    return TOURS[tour - 1].watch


def start_hour(tour: int) -> int:
    """The hour of the clock a tour opens on: its watch's, not always 08:00."""
    return WATCH_START_HOUR[watch_of(tour)]


def script(tour: int, today: date) -> Optional[Tour]:
    """
    Return the entry for a tour, if the calendar is the one it was written for.

    A player who has moved the epoch is on a different calendar. A beat
    about Thanksgiving on some other 24 November would be a lie, so they
    get the filler and no script.
    """
    if not 1 <= tour <= len(TOURS):
        return None
    entry = TOURS[tour - 1]
    return entry if entry.day == today else None


def _event(event_id: str, beat: Beat, office: Mapping[str, str],
           offset: int = 0) -> Event:
    """
    Turn a beat into an event record, naming the player's own office.

    Beats are written against the day watch; ``offset`` is the hours the
    tour's watch starts from 08:00, so an evening tour's 09:15 reads 17:15.
    """
    fill = {'city': office['city'], 'clli': office['clli'],
            'switch': office['switch_type']}
    return {
        'id': event_id,
        'time': f'{(int(beat.at[:2]) + offset) % 24:02d}{beat.at[2:]}',
        'type': beat.type,
        'title': beat.title.format(**fill),
        'priority': beat.priority,
        'status': beat.status,
        'description': beat.description.format(**fill),
        'details': beat.details.format(**fill),
        'actions': list(beat.actions),
        'origin': beat.origin,
        'source': beat.source,
    }


def build(tour: int, office: Mapping[str, str],
          today: date) -> List[Event]:
    """
    Return the events on the board for a tour.

    The tour's own beats, if the calendar is right for them, and three
    pieces of routine drawn from the filler. The draw is seeded by the tour
    and the office, so the same tour at the same office is the same board
    every time: events are rebuilt when a saved shift is picked up, and the
    ones that already fired are remembered by number.

    Args:
        tour: Which tour of the career, 1-13
        office: The player's own office: ``city``, ``clli``, ``switch_type``
        today: The calendar day the tour falls on

    Returns:
        The events in time order, numbered by the tour and the order
    """
    entry = script(tour, today)
    beats = list(entry.beats) if entry else []
    rng = random.Random(f'{tour}-{office["clli"]}')
    drawn = rng.sample(_FILLER, 3 if beats else 4)
    pieces = [Beat(at, kind, priority, status, title, description, details,
                   actions, OWN, "the simulation's own")
              for (at, kind, priority, status, title, description, details,
                   actions) in drawn]
    ordered = sorted(beats + pieces, key=lambda beat: beat.at)
    offset = start_hour(tour) - WATCH_START_HOUR['day']
    return [_event(f'EV-{tour:02d}{number:02d}', beat, office, offset)
            for number, beat in enumerate(ordered, 1)]


def news_through(tour: int, today: date) -> List[NewsItem]:
    """
    Return the articles that have arrived by a tour, one for each tour after
    the first.

    Only on the calendar they were written for, and never one dated after the
    day: the spool does not hold tomorrow's news.
    """
    if script(tour, today) is None:
        return []
    return [entry.news for entry in TOURS[:tour]
            if entry.news is not None and entry.news.posted.date() <= today]
