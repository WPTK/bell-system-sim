"""
Things the machine holds that are worth finding, and who may read them.

Two rules govern this module, both from pillar 4 of ``docs/design/plan.md``.
Lore is found with ls, cat and grep, and nothing here is pushed at the player:
no briefing points at a file, and no file says what the player ought to do
about a report. And each sign-off opens the next layer, which is why the
groups below follow the ladder.

Everything in here is the simulation's own invention. The people are the
roster's (``npc.CRAFT``) except R. Alvarez, who held the sysop position
before the player and has no login; the dates are the fortnight before the
game starts and the tours after it; the log formats are the Seventh Edition's
where the Seventh Edition had them. ``narrative-bible.md`` T2 and T5 say what
is true behind the files, and the voices in section 4 are the standard the
text is held to. Alvarez is never given a pronoun.

A fragment is one file, with a title, that ``finds`` lists once it has been
read. Most are in the tree from the first tour. Some arrive on a later tour,
the way the netnews does, and live where nobody would browse: a dotfile in
a home directory, a dot directory in the uucp spool. Those are for ``grep``.
"""

from typing import Dict, FrozenSet, NamedTuple, Optional, Tuple

# filesystem.MOO_SCORES, which this module cannot import (the tree imports
# this module); a test holds the two together.
MOO_SCORES_PATH = '/usr/games/lib/moo.scores'


class Fragment(NamedTuple):
    """One file that is part of the machine's story."""

    key: str
    # What ``finds`` calls it. Plain nouns: a title names what the file is,
    # never what it means.
    title: str
    path: str
    # The first tour the file is on the machine.
    tour: int = 1
    # The text of a file that is new. None for a file that already ships,
    # which is only marked as a fragment.
    text: Optional[str] = None
    # For a new file, who owns it and what mode it has (root, other and
    # world-readable when left out). For one that ships already, only what
    # is given is changed.
    owner: Optional[str] = None
    group: Optional[str] = None
    mode: Optional[str] = None


# Which Unix group each sign-off puts the player in, by how many sign-offs
# are held. Halloran signs all of them; the third is the one he says he
# notices, and it is the adm group he mentions. The others are the groups
# the file in question would belong to on a real machine. The simulation's
# own: no source says a sign-off gated a file.
GROUP_FOR_SIGN_OFF: Dict[int, str] = {
    1: 'craft',
    2: 'uucp',
    3: 'adm',
    4: 'sys',
    5: 'mgmt',
}

# How many sign-offs the third group takes, which is when the wire chief
# says the su log is open to you.
ADM_GROUP_QUALIFICATIONS = 3


def groups_for(held: int) -> FrozenSet[str]:
    """Return the groups a craftsperson holding this many sign-offs is in."""
    return frozenset(group for number, group in GROUP_FOR_SIGN_OFF.items()
                     if number <= held)


# -- the last holder of the position ------------------------------------

SENT = """From sysop Fri Nov 11 23:02:40 1983
To: ehalloran
Subject: handover

Board is clear. Notes are in my home directory. Franklin Street
is done. Anything else is in the log.

R. Alvarez
"""

# The record journal. Reyes tries to reopen what the position closed and is
# refused; she tries su; Halloran su's at 06:15 and does it himself. The
# journal never says why he did.
LMOSLOG = """line record journal, mhuxco                     11/14
03:41  REOPEN  mreyes     refused: closed records are root's
03:44  REOPEN  mreyes     refused: closed records are root's
03:47  SU      mreyes     root: refused
03:52  REOPEN  mreyes     refused: closed records are root's
06:15  SU      ehalloran  root: ok
06:16  REOPEN  ehalloran  ok  records closed by sysop 11/07-11/11
                          that had been rung back on
06:21  CLOSE   ehalloran  journal
"""

# Halloran's own list. He is plain and says as little as he can; this is
# the one file where he says why.
REOPENED = """records reopened 11/14, under my name

The reports that rang back since 11/07 were reopened at 06:16.
Reyes tried at 03:47 and was refused.
The position has nobody in it.

                                                       E. Halloran
"""

# -- Alvarez's log, which testlog.c writes ------------------------------

TESTLOG = """10/31 closed 5 ntf 1 board 11
11/01 closed 6 ntf 2 board 9
11/02 closed 4 ntf 1 board 8
11/03 closed 6 ntf 2 board 8
11/04 closed 5 ntf 2 board 7
11/07 closed 6 ntf 3 board 9
11/08 closed 7 ntf 4 board 8
11/09 closed 8 ntf 5 board 5
11/10 closed 9 ntf 6 board 2
11/11 closed 7 ntf 6 board 0
"""

# -- the places nobody browses ------------------------------------------

SCRATCH = """franklin st, october. for the log, so i do not do it twice.

  10/04  crew 1   nothing at the pole                 ntf
  10/05  crew 2   nothing at the pole                 ntf
  10/06  crew 3   spliced
  10/07  crew 4   spliced, same place
"""

TRIAL = """marker 2, aisle 4, third trial, seconds. my watch and the timing
jack, same bench, same hand. limit is 12.

  81   jan  6.8    jun  7.1    nov  7.4
  82   mar  7.9    jul  8.3    nov  8.8
  83   feb  9.4    may  9.9    aug 10.5
       11/2 11.2   11/29 11.6

still inside limits.
"""

RETAIN = """/usr/adm retained through 31 December 1990, per the memo.
reviewed by E.H., 12/12.

  messages    keep
  shiftlog    keep
  uucplog     keep
  testlog     keep
  sulog       keep
"""

TRANSFER = """accounts on mhuxco, for the operating company. from the wire chief.

  root daemon bin sys adm uucp   system. they take these as they stand.
  sysop switch field noc tsps    positions. whoever has one on 1/1
  dba netplan custserv radio     has it.
  tnds sarts docprep
  rjohnson mreyes dpetrak        people. the list goes over as written.
  lokafor gvasquez ehalloran
  tnakamura wfinch jsandoval
  abright jhaverty
  alvarez                        no login. the files are under sysop.
                                 leave them.
"""


# The order here is the number ``finds`` prints beside each title, so new
# fragments go on the end.
FRAGMENTS: Tuple[Fragment, ...] = (
    # The thread of the last holder, one layer to a sign-off.
    # dead.letter ships with the sysop home (data/homes.py).
    Fragment('letter', 'Mail to the chief, not sent',
             '/usr/users/sysop/dead.letter', mode='-rw-r-----'),
    Fragment('sent', 'Mail to the chief, sent',
             '/usr/spool/mail/ehalloran', text=SENT,
             owner='ehalloran', group='uucp', mode='-rw-r-----'),
    Fragment('sulog', 'Who became whom', '/usr/adm/sulog'),
    Fragment('lmoslog', 'The record journal', '/usr/adm/lmoslog',
             text=LMOSLOG, owner='sys', group='sys', mode='-rw-r-----'),
    Fragment('reopened', "The chief's own list",
             '/usr/users/ehalloran/reopened', text=REOPENED,
             owner='ehalloran', group='mgmt', mode='-rw-r-----'),
    # What was on the machine already.
    Fragment('notes', 'Notes for whoever has the position',
             '/usr/users/sysop/notes'),
    Fragment('testlog', 'The position test log', '/usr/adm/testlog',
             text=TESTLOG, owner='sysop', group='craft'),
    Fragment('testlogc', 'testlog.c', '/usr/src/cmd/testlog.c'),
    Fragment('scratch', 'A file in /tmp', '/tmp/.f', tour=2,
             text=SCRATCH, owner='sysop', group='craft'),
    Fragment('marker', 'Marker 2, as Johnson found it',
             '/usr/users/rjohnson/marker.notes'),
    Fragment('trial', 'Third trial times',
             '/usr/users/rjohnson/.trial', tour=5, text=TRIAL,
             owner='rjohnson', group='craft'),
    Fragment('memo', 'The January memo', '/usr/doc/divestiture'),
    Fragment('retain', 'What is kept seven years', '/usr/adm/.retain',
             tour=8, text=RETAIN, owner='ehalloran', group='adm'),
    Fragment('transfer', 'Accounts for transfer', '/usr/lib/.xfer',
             tour=10, text=TRANSFER, owner='ehalloran', group='mgmt'),
    Fragment('strike', 'A post on the August strike',
             '/usr/spool/news/net.misc/88'),
    Fragment('moo', 'The scoreboard', MOO_SCORES_PATH),
    Fragment('uucplog', 'Calls that were not answered',
             '/usr/adm/uucplog'),
)

FRAGMENTS_BY_PATH: Dict[str, Fragment] = {
    fragment.path: fragment for fragment in FRAGMENTS}
FRAGMENTS_BY_KEY: Dict[str, Fragment] = {
    fragment.key: fragment for fragment in FRAGMENTS}
