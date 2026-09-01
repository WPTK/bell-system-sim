"""
The simulated Seventh Edition filesystem, and things worth reading in it.

The old filesystem was ten directories whose listings named files that did not
exist, and 724 bytes of content in total. You could not change directory, and
there was no way to read anything. That made the UNIX layer a backdrop rather
than a place, which is the wrong way round: sitting at a Bell System UNIX
machine in 1983 is the point, and the telephony is the work you happen to be
doing there.

So this is a real tree. Directories contain files, files contain text, and the
text is worth the trouble of finding. Some of it is the machine's own record -
the message of the day, the accounting logs, the password file. Some is the
work: line records, practices, shift logs. Some is the company, six weeks
before it stopped existing.

That last part is not invention. Engineering and Operations in the Bell System
records that "an agreement was reached between AT&T and the United States
Department of Justice to settle an antitrust suit by divesting the Bell
operating companies from AT&T", and that "the existence of the Bell System
ends with divestiture" on 1 January 1984. The simulated shift is 14 November
1983, forty-eight days before that. The memos below are this simulation's own
words for a thing that really was about to happen.
"""

from .clock import DIVESTITURE as _DIVESTITURE
from .data.homes import HOMES
from typing import Callable, Dict, List, NamedTuple, Optional, Union

# Divestiture took effect on 1 January 1984. The date itself lives in
# clock.py, with the function that counts down to it, so there is one of it.
DIVESTITURE = _DIVESTITURE.strftime('%Y-%m-%d')

Content = Union[str, Callable[..., str]]


class Node(NamedTuple):
    """One entry in the filesystem."""

    kind: str  # 'dir' or 'file'
    owner: str
    group: str
    mode: str
    content: Optional[Content] = None

    @property
    def is_dir(self) -> bool:
        """Return whether this entry is a directory."""
        return self.kind == 'dir'


def _dir(owner: str = 'root', group: str = 'other',
         mode: str = 'drwxr-xr-x') -> Node:
    """Build a directory node."""
    return Node('dir', owner, group, mode)


def _file(content: Content, owner: str = 'root', group: str = 'other',
          mode: str = '-rw-r--r--') -> Node:
    """Build a file node."""
    return Node('file', owner, group, mode, content)


MOTD = """UNIX Version 7
Bell Telephone Laboratories
Murray Hill, New Jersey

Copyright (c) 1979 Bell Telephone Laboratories, Incorporated.

*** NOTICE TO ALL CRAFT AND MANAGEMENT ***

Effective 1 January 1984 the Bell System is dissolved. This machine and
the offices it administers pass to the operating company on that date.
Records retention instructions are in /usr/doc/divestiture. Read them.

Your login, your qualifications and your service index travel with you.
Nothing else is guaranteed.

Trouble reports: mail(1), or the report(1) command.
Practices:       /usr/bsp
Stuck:           hint(1). Ask again if the first one was not enough.
Questions:       write ehalloran
Games:           /usr/games. Nights are long and the board is not always
                 full. Whoever keeps moo.scores, see net.games.
"""

# /etc/passwd. A Seventh Edition entry is name, password, uid, gid, gecos,
# home directory, shell. An empty second field means the account has no
# password and login(1) does not ask for one: most of these are like that,
# because the machine is in a locked building and the door is the security.
#
# root is not. The hash is not a real one and nothing checks it - what it
# does is make login(1) and su(1) ask, and refuse, which is what
# /usr/adm/sulog is already a record of somebody finding out.
PASSWD = """root:x8Zt4qKcNvBhE:0:1::/:/bin/sh
daemon::1:1::/:
bin::3:3::/bin:
sys::4:4::/usr/src:
adm::5:5::/usr/adm:
uucp::6:6::/usr/spool/uucp:/usr/lib/uucp/uucico
sysop::17:1::/usr/users/sysop:/bin/sh
switch::18:1::/usr/users/switch:/bin/sh
field::19:1::/usr/users/field:/bin/sh
noc::20:1::/usr/users/noc:/bin/sh
rjohnson::21:1::/usr/users/rjohnson:/bin/sh
mreyes::22:1::/usr/users/mreyes:/bin/sh
dpetrak::23:1::/usr/users/dpetrak:/bin/sh
lokafor::24:1::/usr/users/lokafor:/bin/sh
gvasquez::25:1::/usr/users/gvasquez:/bin/sh
ehalloran::26:1::/usr/users/ehalloran:/bin/sh
tnakamura::27:1::/usr/users/tnakamura:/bin/sh
wfinch::36:1::/usr/users/wfinch:/bin/sh
jsandoval::37:1::/usr/users/jsandoval:/bin/sh
abright::38:1::/usr/users/abright:/bin/sh
jhaverty::39:1::/usr/users/jhaverty:/bin/sh
tsps::28:1::/usr/users/tsps:/bin/sh
dba::29:1::/usr/users/dba:/bin/sh
netplan::30:1::/usr/users/netplan:/bin/sh
custserv::31:1::/usr/users/custserv:/bin/sh
radio::32:1::/usr/users/radio:/bin/sh
tnds::33:1::/usr/users/tnds:/bin/sh
sarts::34:1::/usr/users/sarts:/bin/sh
docprep::35:1::/usr/users/docprep:/bin/sh
"""

GROUP = """other::1:
daemon::1:daemon
bin::3:bin
sys::4:sys
adm::5:adm
uucp::6:uucp
craft::10:rjohnson,lokafor,gvasquez,mreyes,wfinch,jsandoval,abright
mgmt::11:ehalloran,dpetrak,tnakamura,jhaverty
"""



DIVESTITURE_MEMO = """                    BELL SYSTEM - CONFIDENTIAL
                 RECORDS RETENTION AND TRANSFER
                     Effective 1 January 1984

TO:      All craft and management, network operations
FROM:    Office of the Vice President - Operations
DATE:    1 November 1983

On 1 January 1984 the Bell System is dissolved under the consent decree
settling the Department of Justice antitrust suit. The operating
companies are divested from AT&T on that date.

WHAT THIS MEANS FOR THIS OFFICE

  This wire centre, its outside plant and its records pass to the
  operating company. Interexchange facilities and the toll network
  above class 4 remain with AT&T.

  Your employment continues. Your craft qualifications transfer.
  Service index history transfers.

WHAT YOU MUST DO BEFORE 31 DECEMBER

  1. Close every trouble report you can close honestly. Reports open
     at transfer are handed to the operating company with your name on
     them.

  2. Do not close reports you have not worked in order to clear the
     board. Disposition codes are audited after transfer.

  3. Line records, cable records and frame assignments stay with the
     wire centre. Do not remove copies.

  4. Anything in /usr/adm is retained for seven years.

A NOTE

  Some of you have spent thirty years here. The network you built is
  the largest machine anyone has ever made and it does not stop working
  on the first of January. It simply belongs to different companies.

  Work the board. That is the job on 31 December and it is the job on
  2 January.

                                                             - VP-OPS
"""

BULLETIN = """OPERATIONS BULLETIN 83-114                       14 November 1983

  1. MECHANISED LOOP TESTING is now the primary test method at this
     position. The line status verifier and automated line verification
     sets remain available but have limited capability beside it.

  2. REPEAT REPORTS are running above objective for the third month.
     A report closed as no trouble found on a line that is faulty
     returns as a repeat and counts twice. Measure before you close.

  3. THE ORDER WIRE is not a telephone. Keep it clear. The switching
     control centre is running trunk routines nightly and needs it.

  4. WEATHER. Wet cable reports rise with rainfall and stay up for
     several days after. Expect the board to be heavy this week.

  5. CAROT exceptions print to the maintenance teletype whether or not
     anybody is reading. Read them.
"""

HELLO_C = """#include <stdio.h>

main()
{
\tprintf("hello, world\\n");
}
"""

TESTLOG_C = """/*
 * testlog - append a line to the position test log
 * R. Alvarez, tour 2
 */
#include <stdio.h>

main(argc, argv)
int argc;
char **argv;
{
\tFILE *f;
\tint i;

\tif ((f = fopen("/usr/adm/testlog", "a")) == NULL) {
\t\tfprintf(stderr, "testlog: cannot open log\\n");
\t\texit(1);
\t}
\tfor (i = 1; i < argc; i++)
\t\tfprintf(f, "%s%c", argv[i], i < argc - 1 ? ' ' : '\\n');
\tfclose(f);
\texit(0);
}
"""

FORTUNES = """When in doubt, use brute force.
                -- Ken Thompson

UNIX is basically a simple operating system, but you have to be a
genius to understand the simplicity.
                -- Dennis Ritchie

One of the main causes of the fall of the Roman Empire was that,
lacking zero, they had no way to indicate successful termination of
their C programs.

The number of Unix installations has grown to 10, with more expected.
                -- The Unix Programmer's Manual, 2nd Edition, 1972

Everything should be built top-down, except the first time.

If you have a procedure with ten parameters, you probably missed some.

A cable is out of service until somebody proves otherwise.
                -- every splicer, everywhere
"""

SULOG = """SU 11/13 22:14 + tty02 rjohnson-root
SU 11/14 01:02 + tty03 dpetrak-root
SU 11/14 03:47 - tty07 mreyes-root
SU 11/14 06:15 + tty01 ehalloran-root
"""

MESSAGES = """Nov 13 22:01 mhuxco: uucico: call to pwba failed, retry 22:31
Nov 13 22:31 mhuxco: uucico: pwba ok, 12 files in 4 files out
Nov 14 00:00 mhuxco: accounting: daily runacct complete
Nov 14 02:14 mhuxco: rk0: soft error, block 44182, recovered
Nov 14 04:00 mhuxco: uucico: call to research ok, 3 files in
Nov 14 06:15 mhuxco: su: ehalloran on tty01
Nov 14 07:58 mhuxco: init: tour 1 logins enabled
"""

UUCPLOG = """uucico mhuxco (11/13-22:31) SUCCEEDED (call to pwba)
uucico mhuxco (11/13-22:33) OK (startup)
uucico pwba   (11/13-22:41) REQUEST (S bsp.660 /usr/bsp/ sysop)
uucico mhuxco (11/14-02:14) SUCCEEDED (call to mhuxt)
uucico mhuxt  (11/14-02:19) REQUEST (S news 14 files /usr/spool/news/ uucp)
uucico mhuxco (11/14-04:00) SUCCEEDED (call to research)
uucico mhuxco (11/14-04:02) OK (conversation complete)
uucico mhuxco (11/14-06:44) FAILED (call to ihnp4, no answer)
"""


# /usr/dict/words. The real one held about 25,000 entries and was what
# spell(1) checked against and look(1) searched. This one is short enough to
# ship and long enough to be useful: the common English words a memo on this
# machine would be built from, plus the vocabulary of the job, which the real
# /usr/dict/words did not have and which every Bell site added locally.
WORDS = """a
about
above
actually
administers
after
again
against
aisle
all
almost
along
already
also
always
am
an
and
another
answer
answering
antitrust
any
anybody
anyone
anything
appear
april
are
around
as
ask
asks
assignments
at
audited
august
automated
available
away
back
bad
be
because
been
before
being
belongs
below
beside
best
better
between
board
both
box
boxes
bridge
budget
build
building
built
bulletin
business
but
cable
call
called
came
can
cannot
capability
cares
carried
carrier
carries
carry
central
centre
change
characters
check
chief
circuit
class
clear
cleared
clearing
clears
close
closed
closing
code
codes
coffee
column
come
comes
command
commands
commitment
companies
company
complete
computer
condition
confidential
connect
consent
continues
control
copies
copy
copyright
could
count
counts
covers
craft
crew
crews
cross
crossbar
current
customer
cut
date
day
days
dead
december
decree
deep
department
depth
dial
did
different
digit
digits
dispatch
disposition
dissolved
distribution
divested
divestiture
do
does
done
door
down
drop
during
each
early
echo
editor
effective
either
else
employment
end
enough
enter
entry
equipment
error
errors
even
ever
every
everything
except
exceptions
exchange
expect
expected
facilities
failed
fall
faster
fault
faulty
february
feed
field
figure
file
files
fills
find
finding
finish
first
five
fix
fixed
fixes
following
for
found
four
frame
friday
from
gave
get
gets
getting
give
given
go
going
gone
good
got
great
ground
group
guaranteed
guess
had
half
hand
handed
handle
handled
happens
has
have
having
he
heavy
help
her
here
high
hill
him
his
history
hit
hold
holds
honestly
hour
house
how
however
hundred
i
if
in
incorporated
index
input
inside
instead
instructions
interexchange
is
it
its
january
jersey
job
july
june
just
justice
keep
keeps
kept
know
known
laboratories
largest
last
late
later
leave
leaves
left
less
let
letter
level
life
like
limited
line
lines
list
little
local
login
long
look
looks
loop
loops
loss
lower
machine
made
main
maintenance
make
makes
man
management
manual
many
march
mark
marker
matter
may
me
mean
means
measure
mechanised
meter
method
might
mile
mode
month
more
morning
most
moved
moves
moving
much
must
name
near
nearest
need
needs
network
never
new
newline
news
next
night
nightly
no
nobody
noise
not
note
notes
nothing
notice
november
now
number
objective
october
of
off
office
offices
often
ok
old
oldest
on
once
one
only
open
operating
operation
operations
optional
or
order
other
our
out
outside
over
own
pair
pairs
paper
part
pass
past
pay
pending
people
per
person
pick
picked
place
placed
plan
plant
point
poor
position
positions
possible
power
practice
practices
present
president
primary
print
printed
printing
prints
problem
programs
put
puts
qualifications
question
questions
quiet
rain
rainfall
range
reach
reached
read
reading
reads
ready
reason
receive
record
recorded
records
remain
remove
repair
repeat
reply
report
reports
request
research
result
retained
retention
returns
right
ring
rise
route
routines
routing
run
running
runs
said
same
saturday
saw
say
says
second
section
see
seem
seen
sends
sent
separate
september
service
set
sets
settling
seven
several
shall
she
sheet
shell
shift
short
should
show
shows
side
signal
simply
since
sites
sitting
size
sleep
slow
small
so
software
some
somebody
something
sound
south
spare
speak
special
spend
spent
splicer
spool
station
status
stay
stays
steps
still
stop
stops
street
subscriber
succeeded
such
suit
sunday
switch
switches
switching
system
take
taken
takes
taking
tape
telephone
teletype
tell
tells
ten
terminal
test
tested
testing
tests
than
that
the
their
them
then
there
these
they
thing
things
think
thinking
third
thirty
this
those
though
three
through
thursday
ticket
tickets
time
to
today
told
toll
tone
too
took
tour
toward
transfer
transfers
transmission
travel
trial
trip
trouble
trunk
trunks
try
tuesday
turn
turned
turns
twenty
twice
two
under
unix
until
up
upon
upstairs
us
use
used
uses
using
usual
value
verification
verifier
version
very
vice
voice
wait
waiting
walk
want
wanted
was
watching
water
way
we
weather
wednesday
week
well
went
were
wet
what
when
where
whether
which
while
who
whoever
whole
whose
why
will
wire
wires
with
within
without
word
work
worked
working
works
worse
worth
would
write
written
wrong
wrote
year
years
yesterday
yet
you
your
yours
"""


# A makefile for the two programs under /usr/src/cmd, so make(1) has
# something real to build.
MAKEFILE = """# Two small programs. make(1) builds what is out of date,
# and nothing else. Run it twice and see.
all:	hello testlog

hello:	hello.c
\tcc -o hello hello.c

testlog:	testlog.c
\tcc -o testlog testlog.c
"""


# /usr/dict/papers, the bibliography refer(1) looks citations up in. The
# %-keyed record format is refer's own: %A author, %T title, %J journal,
# %V volume, %D date, %P pages.
#
# Every entry is a real paper and the citations are externally sourced and
# checked: Ritchie and Thompson in CACM 17(7), July 1974, 365-375; Thompson
# and Bourne in the July/August 1978 UNIX issue of the Bell System Technical
# Journal, 57(6) part 2, at 1931-1946 and 1971-1990; Feldman on make in
# Software: Practice and Experience 9(4), April 1979, 255-265; Kernighan on
# pic in the same journal, 12(1), January 1982, 1-21. A machine in a Bell
# building in 1983 would have had these to hand, most of them written down
# the corridor.
PAPERS = """%A D. M. Ritchie
%A K. Thompson
%T The UNIX Time-Sharing System
%J Communications of the ACM
%V 17(7)
%D July 1974
%P 365-375

%A K. Thompson
%T UNIX Implementation
%J Bell System Technical Journal
%V 57(6) part 2
%D July-August 1978
%P 1931-1946

%A S. R. Bourne
%T The UNIX Shell
%J Bell System Technical Journal
%V 57(6) part 2
%D July-August 1978
%P 1971-1990

%A S. I. Feldman
%T Make - A Program for Maintaining Computer Programs
%J Software: Practice and Experience
%V 9(4)
%D April 1979
%P 255-265

%A B. W. Kernighan
%T PIC - A Language for Typesetting Graphics
%J Software: Practice and Experience
%V 12(1)
%D January 1982
%P 1-21
"""


# A diagram in pic(1), left in /usr/doc for anybody who wants to see what
# the preprocessor does. A loop is a pair of wires from a subscriber's
# station to the frame in the central office and then to the switch.
LOOP_PIC = """.PS
box "station"
arrow
box "drop"
arrow
box "frame"
arrow
box "switch"
.PE
That is a loop. Everything in a trouble report is somewhere on it, and
the whole job is working out which box the fault is between.
"""


# A short piece with citations in it, so refer(1) has something to fill in
# and nroff(1) has something to format. The claims in it are the ones the
# papers it cites actually make.
WHY_UNIX = """.TL
Why there is a UNIX machine in a wire centre
.PP
Nobody bought this machine. The operating system on it was written at
Murray Hill for a PDP-7 that was going spare, and it spread through the
company the way a useful tool does: somebody carried a tape.
.PP
The system was described publicly in 1974
.[
ritchie thompson unix time-sharing
.]
and the whole of it was written up four years later in an issue of the
company journal given over to it, including the shell
.[
bourne shell
.]
and how the kernel is actually built
.[
thompson unix implementation
.]
.PP
That is why the manual for a program on a repair position cites a
research journal. There was no product to write a product manual for.
The 1956 decree kept the company out of the computer business, so what
it had instead was papers, and the papers are the documentation.
.PP
As of January that changes, and the system on this machine has a price.
"""


# Netnews. Usenet began in 1980 and by 1983 a Bell machine on the uucp network
# took a nightly feed. The header block follows RFC 850 (June 1983), the
# standard in force during the simulated period: Relay-Version first, then
# Posting-Version, Path, From, Newsgroups, Subject, Message-ID and Date, with
# the day of the week spelled out and the site suffixed .UUCP.
#
# The relay sites in the Path lines are real machines of the period - cbosgd,
# mhuxj, mhuxt and eagle appear in RFC 850's own worked example, and ihnp4,
# research and pwba are already carried in this machine's uucp log. mhuxco is
# this simulation's machine. The user names, and every article below, are this
# simulation's own: no real posting is reproduced and nothing here is put in
# the mouth of a real person.
_RELAY = 'Relay-Version: version B 2.10.1 6/24/83; site mhuxco.UUCP'


def _article(posting: str, path: str, sender: str, group: str, subject: str,
             message_id: str, date: str, body: str, **extra: str) -> str:
    """
    Assemble one article in RFC 850 order.

    Building them rather than writing out fourteen header blocks by hand keeps
    the order right everywhere and makes a missing header impossible.
    """
    lines = [_RELAY,
             f'Posting-Version: version B 2.10.1 6/24/83; site {posting}.UUCP',
             f'Path: {path}',
             f'From: {sender}',
             f'Newsgroups: {group}',
             f'Subject: {subject}',
             f'Message-ID: {message_id}',
             f'Date: {date}']
    lines.extend(f'{name.replace("_", "-")}: {value}'
                 for name, value in extra.items())
    return '\n'.join(lines) + '\n\n' + body


NEWS_WIZARDS_114 = _article(
    'eagle', 'mhuxco!mhuxt!mhuxj!eagle!dkellner',
    'dkellner@eagle.uucp (D Kellner)',
    'net.unix-wizards',
    'Re: how many files is too many in one directory?',
    '<3114@eagle.UUCP>', 'Friday, 11-Nov-83 03:12:44 EST',
    """> We have a spool directory with about 900 files in it and ls has
> started taking a noticeable amount of time.

Nine hundred is nothing. The problem is not the count, it is that you
are calling ls and then reading the whole thing. Pipe it. If you want
one file, ask for one file.

The other half of your problem is that ls sorts. If you do not need
them in order, you are paying for a sort you are going to throw away.
""")

NEWS_WIZARDS_121 = _article(
    'cbosgd', 'mhuxco!ihnp4!cbosgd!pmarchetti',
    'pmarchetti@cbosgd.uucp (P Marchetti)',
    'net.unix-wizards',
    'Re: System V, and what happens to the commands we know',
    '<1121@cbosgd.UUCP>', 'Saturday, 12-Nov-83 19:40:11 EST',
    """> Now that the company is selling it, are we going to be told which
> version we are allowed to run?

Somebody in this thread has the order of events backwards. The company
could not sell it before. The 1956 decree kept AT&T out of the computer
business, so the system went out to universities on a tape and a
handshake and that is the whole reason any of us learned it. The 1982
decree is what let them into the business, and System V is what that
looks like when it arrives in a carton with a price on it.

I am not going to tell you that is bad news. I will tell you it is a
different kind of news than the tape was. The tape came with source.

Practical answer for your machine: nothing you type today stops
working. ed is ed. The differences you will actually hit are in the
shell and in what the manual calls things.
""")

NEWS_WIZARDS_126 = _article(
    'mhuxj', 'mhuxco!mhuxt!mhuxj!bcorrigan',
    'bcorrigan@mhuxj.uucp (B Corrigan)',
    'net.unix-wizards',
    'Re: ed(1) prints ? and I would like to know why',
    '<807@mhuxj.UUCP>', 'Sunday, 13-Nov-83 21:02:57 EST',
    """> It will not tell me what I did wrong. It prints a question mark and
> waits. I am supposed to guess.

Yes.

This is not an oversight and it is not the editor being unfriendly at
you. It was written for a teletype at 110 baud on a machine that had to
hold the whole thing in core, and a message you already know the meaning
of is thirty characters you have to sit and watch print. The question
mark is the shortest thing that means "no."

Once you have used it for a week you will find you know which ? it is
before you have finished reading it. It is nearly always one of three
things: you gave an address that does not exist, you are in input mode
and thought you were in command mode, or you are in command mode and
thought you were in input mode.
""")

NEWS_GENERAL_203 = _article(
    'ihnp4', 'mhuxco!ihnp4!rteixeira',
    'rteixeira@ihnp4.uucp (R Teixeira)',
    'net.general',
    'What actually happens to us on January 1?',
    '<2203@ihnp4.UUCP>', 'Sunday, 6-Nov-83 22:41:09 EST',
    """Nobody in my building can give a straight answer, so let me try here.

The operating company gets the wire centres, the loops and the local
switching. AT&T keeps long lines and everything above class 4. Fine.
Understood. What I cannot get anybody to tell me is which one of those
this computer belongs to, and I have twelve years of trouble history on
it.

I am told the answer is "the records stay with the wire centre." The
records are on a disc. The disc is in a machine. Nobody has told the
machine.
""")

NEWS_GENERAL_211 = _article(
    'research', 'mhuxco!research!aweatherly',
    'aweatherly@research.uucp (A Weatherly)',
    'net.general',
    'Re: What actually happens to us on January 1?',
    '<914@research.UUCP>', 'Thursday, 10-Nov-83 12:18:33 EST',
    """> Nobody has told the machine.

The machine is the easy part. Somebody will come and put a new label on
it and it will keep answering to the old name for years, because the
scripts that call it were written in 1974 and nobody is going to find
all of them.

What I would think about is the parts of the job that were never
written down because they did not need to be. When you want a pair
carried past the wire centre today you ring a man and he does it. In
January that man works for a different company and there is a form.

Nobody is going to hand you a list of those. You find them one at a
time, and you find them at 3am.
""",
    References='<2203@ihnp4.UUCP>', Followup_To='net.general')

NEWS_MISC_88 = _article(
    'mhuxt', 'mhuxco!mhuxt!jsandoval',
    'jsandoval@mhuxt.uucp (J Sandoval)',
    'net.misc',
    'Re: what the August walkout actually settled',
    '<556@mhuxt.UUCP>', 'Monday, 7-Nov-83 18:26:40 EST',
    """> Three weeks out and I still cannot tell you what we got.

Twenty-two days, and what came back was five and a half in the first
year and one and a half in each of the next two. You can decide for
yourself what that is against what the groceries did.

The part nobody put on a leaflet is the part that should worry you.
Service did not fall over while we were out. It used to be that a
walkout of that size meant the dial tone went with it, and this time
the switches mostly just ran. That is not because anyone crossed. It is
because there is less and less of this job that needs a person standing
in front of it, and the company now knows that, and so do we.

Whatever the number turns out to have been worth, employment security
was the thing on the table that was actually about the next ten years.
""")

NEWS_NEWS_45 = _article(
    'mhuxj', 'mhuxco!mhuxt!mhuxj!lstrand',
    'lstrand@mhuxj.uucp (L Strand)',
    'net.news',
    'expire is set to 14 days here and I am still full',
    '<791@mhuxj.UUCP>', 'Monday, 7-Nov-83 09:33:15 EST',
    """Two weeks of net.all is now more than this spool will hold, which is
not something I expected to be typing this year.

Before anybody tells me to buy a disc: the growth is not in the number
of articles, it is in how many groups the feed carries. We subscribed
to a feed, not to net.all, and the difference has quietly stopped
being small.

If you are running a site and you have not looked at what you are
taking lately, go and look. sys(5) will let you say what you want
instead of taking everything and expiring it in a fortnight.
""",
    Expires='Monday, 21-Nov-83 00:00:00')

NEWS_NEWS_51 = _article(
    'cbosgd', 'mhuxco!ihnp4!cbosgd!hgillam',
    'hgillam@cbosgd.uucp (H Gillam)',
    'net.news',
    'Reply paths stay in reply format until January 1',
    '<1140@cbosgd.UUCP>', 'Tuesday, 8-Nov-83 14:07:52 EST',
    """The Path line is not documentation. Until the first of January it has
to be something you could hand to uux and have arrive, which means
host!host!host!user with no gaps and no editorialising in the middle.

After the first of January it is a trace and you may stop caring
whether it would route. Not before. There are sites out there whose
only way of answering you is to run what is in that line.

Two things change for me on the first of January and this is the one I
expect to go smoothly.
""",
    Followup_To='net.news')

NEWS_JOKES_88 = _article(
    'mhuxco', 'mhuxco!dpetrak',
    'dpetrak@mhuxco.uucp (D Petrak)',
    'net.jokes',
    'overheard at the frame',
    '<41@mhuxco.UUCP>', 'Wednesday, 9-Nov-83 11:55:02 EST',
    """New man asks the wire chief how you tell if a pair is good.

Chief says: you put a tone on it and you go and listen for the tone.

New man asks what if you do not hear the tone.

Chief says: then it is either a bad pair or you are in the wrong
building, and after twenty years I can tell you which one it usually
is.
""")

NEWS_JOKES_93 = _article(
    'eagle', 'mhuxco!mhuxt!mhuxj!eagle!fokonkwo',
    'fokonkwo@eagle.uucp (F Okonkwo)',
    'net.jokes',
    'Re: overheard at the frame',
    '<3129@eagle.UUCP>', 'Saturday, 12-Nov-83 08:14:26 EST',
    """Ours is shorter.

Q. How many craft does it take to clear a trouble that is not there?

A. Two. One to not find it and one to write "NTF" so convincingly that
it comes back in April as somebody else's.
""",
    References='<41@mhuxco.UUCP>')

NEWS_LANG_C_62 = _article(
    'mhuxt', 'mhuxco!mhuxt!ggreenhalgh',
    'ggreenhalgh@mhuxt.uucp (G Greenhalgh)',
    'net.lang.c',
    'Re: printf does not put the newline there for you',
    '<563@mhuxt.UUCP>', 'Tuesday, 8-Nov-83 23:51:08 EST',
    """> Everything comes out on one line and then the prompt lands on the
> end of it.

That is because you did not ask for a newline and it did not invent
one. printf prints what you told it to print and nothing else, which is
the whole reason you can use it to print half a line.

	printf("hello, world");        no newline
	printf("hello, world\\n");      newline

The second one is what is in the book. Put the \\n in.

The related surprise, since you will hit it next: the shell's echo does
add one, so a program you wrote and a shell line that looks the same
behave differently, and you will spend an afternoon on that at least
once.
""")

NEWS_SOURCES_41 = _article(
    'mhuxco', 'mhuxco!lokafor',
    'lokafor@mhuxco.uucp (L Okafor)',
    'net.sources',
    'one-liner: how deep is the board',
    '<44@mhuxco.UUCP>', 'Monday, 14-Nov-83 07:22:18 EST',
    """For those of you sitting at a repair position wondering whether it is
worth getting a coffee:

	grep -c PEND /usr/lmos/board

If that number is under five, go. If it is over eight, you are not
getting one.

Somebody will tell me report(1) already prints this. It does. This one
fits in a .profile.
""")

NEWS_SOURCES_44 = _article(
    'mhuxco', 'mhuxco!rjohnson',
    'rjohnson@mhuxco.uucp (R Johnson)',
    'net.sources',
    'Re: one-liner: how deep is the board',
    '<45@mhuxco.UUCP>', 'Monday, 14-Nov-83 07:48:03 EST',
    """The other half of that, for when you are waiting on a load to come off
and you would rather be told than keep looking:

	until [ `grep -c PEND /usr/lmos/board` -lt 5 ]
	do
		sleep 300
	done
	echo board is down to size

Set it going in one window if you have one and forget about it. Do not
make the sleep smaller than five minutes. The board does not change
faster than that and neither does the machine.
""",
    References='<44@mhuxco.UUCP>')

NEWS_GAMES_17 = _article(
    'mhuxco', 'mhuxco!lokafor',
    'lokafor@mhuxco.uucp (L Okafor)',
    'net.games',
    'Re: moo strategy, and a scoreboard that lies',
    '<46@mhuxco.UUCP>', 'Wednesday, 9-Nov-83 23:37:41 EST',
    """> Is there a way to do it in five every time?

No, but there is a way to stop doing it in eleven.

Your first two guesses are not for guessing. Spend them. 1234 and then
5678 tells you how many of your four digits live in each half and which
of them are placed, and you have not tried to be clever yet. Everything
after that is bookkeeping.

The one that gets people is bulls versus cows. A bull is the right
digit in the right column. A cow is a digit you have got, in a column
you have not. Two cows and no bulls is good news. It means you are one
rearrangement away and most people throw the guess out and start again.

While I am here: whoever is keeping /usr/games/lib/moo.scores, mine is
not an eleven. The terminal was dropping characters that night and I
have witnesses.
""")


# Everything the tree holds. Paths are absolute and directories carry no
# listing of their own: children are found by walking the keys, so a listing
# can never name a file that is not there - which is what the old structure
# did throughout.
FILESYSTEM: Dict[str, Node] = {
    '/': _dir(),
    '/bin': _dir(),
    '/dev': _dir(),
    '/etc': _dir(),
    '/lib': _dir(),
    '/tmp': _dir(mode='drwxrwxrwx'),
    '/usr': _dir(),

    '/etc/motd': _file(MOTD),
    '/etc/passwd': _file(PASSWD),
    '/etc/group': _file(GROUP),
    '/etc/rc': _file("/etc/update &\n/usr/lib/lpd\n/etc/cron\nrm -f /tmp/*\n",
                     mode='-rwxr--r--'),
    '/etc/ttys': _file("14console\n12tty01\n12tty02\n12tty03\n02tty04\n"),

    '/dev/console': _file('', mode='crw--w--w-'),
    '/dev/tty01': _file('', mode='crw--w--w-'),
    '/dev/null': _file('', mode='crw-rw-rw-'),
    '/dev/rk0': _file('', mode='brw-------'),

    '/usr/adm': _dir(owner='adm', group='adm'),
    '/usr/adm/messages': _file(MESSAGES, owner='adm', group='adm'),
    '/usr/adm/sulog': _file(SULOG, owner='adm', group='adm', mode='-rw-------'),
    '/usr/adm/uucplog': _file(UUCPLOG, owner='uucp', group='uucp'),

    '/usr/bin': _dir(),
    '/usr/lib': _dir(),
    '/usr/spool': _dir(mode='drwxrwxrwx'),
    '/usr/spool/uucp': _dir(owner='uucp', group='uucp'),
    '/usr/spool/mail': _dir(mode='drwxrwxrwx'),
    '/usr/spool/at': _dir(mode='drwxrwxrwx'),

    '/usr/doc': _dir(),
    '/usr/doc/divestiture': _file(DIVESTITURE_MEMO),
    '/usr/doc/bulletin': _file(BULLETIN),
    '/usr/doc/loop.pic': _file(LOOP_PIC),
    '/usr/doc/why.unix': _file(WHY_UNIX),

    '/usr/src': _dir(owner='sys', group='sys'),
    '/usr/src/cmd': _dir(owner='sys', group='sys'),
    '/usr/src/cmd/hello.c': _file(HELLO_C, owner='sys', group='sys'),
    '/usr/src/cmd/testlog.c': _file(TESTLOG_C, owner='sys', group='sys'),
    '/usr/src/cmd/makefile': _file(MAKEFILE, owner='sys', group='sys'),

    '/usr/dict': _dir(),
    '/usr/dict/words': _file(WORDS),
    '/usr/dict/papers': _file(PAPERS),

    '/usr/games': _dir(),
    '/usr/games/lib': _dir(),
    '/usr/games/fortunes': _file(FORTUNES),

    '/usr/spool/news': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.games': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.games/17': _file(NEWS_GAMES_17, owner='uucp'),
    '/usr/spool/news/net.general': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.general/203': _file(NEWS_GENERAL_203, owner='uucp'),
    '/usr/spool/news/net.general/211': _file(NEWS_GENERAL_211, owner='uucp'),
    '/usr/spool/news/net.jokes': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.jokes/88': _file(NEWS_JOKES_88, owner='uucp'),
    '/usr/spool/news/net.jokes/93': _file(NEWS_JOKES_93, owner='uucp'),
    '/usr/spool/news/net.lang.c': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.lang.c/62': _file(NEWS_LANG_C_62, owner='uucp'),
    '/usr/spool/news/net.misc': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.misc/88': _file(NEWS_MISC_88, owner='uucp'),
    '/usr/spool/news/net.news': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.news/45': _file(NEWS_NEWS_45, owner='uucp'),
    '/usr/spool/news/net.news/51': _file(NEWS_NEWS_51, owner='uucp'),
    '/usr/spool/news/net.sources': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.sources/41': _file(NEWS_SOURCES_41, owner='uucp'),
    '/usr/spool/news/net.sources/44': _file(NEWS_SOURCES_44, owner='uucp'),
    '/usr/spool/news/net.unix-wizards': _dir(owner='uucp', group='uucp'),
    '/usr/spool/news/net.unix-wizards/114': _file(NEWS_WIZARDS_114, owner='uucp'),
    '/usr/spool/news/net.unix-wizards/121': _file(NEWS_WIZARDS_121, owner='uucp'),
    '/usr/spool/news/net.unix-wizards/126': _file(NEWS_WIZARDS_126, owner='uucp'),

    '/usr/bsp': _dir(),
    '/usr/lmos': _dir(owner='sysop', group='craft'),

    '/usr/users': _dir(),
    '/usr/users/rjohnson/marker.notes': _file(
        "aisle 4 no. 5 crossbar, marker 2\n"
        "third trial slow since 81. measured it again 11/2, still slow,\n"
        "still inside limits. do not raise a ticket, they will only close\n"
        "it no trouble found and it will come back to me.\n"
        "if it ever fails outright the trouble is in the sequence relay,\n"
        "not the marker. i have been saying this for two years.\n",
        owner='rjohnson', group='craft'),
    '/usr/games/lib/moo.scores': _file(
        "gvasquez  4\nrjohnson  5\nsysop     -\nmreyes    7\n"
        "lokafor  11  (says the terminal was slow)\n"),
}

# Home directories for the other craft, so /usr/users is not a lie.
for _login in ('rjohnson', 'mreyes', 'dpetrak', 'lokafor', 'gvasquez',
               'ehalloran', 'tnakamura'):
    FILESYSTEM[f'/usr/users/{_login}'] = _dir(
        owner=_login, group='craft', mode='drwxr-x---')


# One home directory for each position somebody can be put at. Selecting a
# role puts you in /usr/users/<role>, and for eleven of the twelve that was
# a directory that did not exist: pwd(1) named it and ls(1) said it was not
# there. What is in them lives in data/homes.py.
for _role, _files in HOMES.items():
    FILESYSTEM[f'/usr/users/{_role}'] = _dir(
        owner=_role, group='craft', mode='drwxr-x---')
    for _name, _text in _files.items():
        FILESYSTEM[f'/usr/users/{_role}/{_name}'] = _file(
            _text, owner=_role, group='craft')


def normalise(path: str, cwd: str) -> str:
    """
    Resolve a path against a working directory, the way the shell does.

    Handles absolute and relative paths, ``.`` and ``..``, and a bare ``~``
    for the home directory of the current position.
    """
    if not path:
        return cwd
    if path.startswith('~'):
        path = '/usr/users/sysop' + path[1:]
    if not path.startswith('/'):
        path = f"{cwd.rstrip('/')}/{path}"

    parts: List[str] = []
    for piece in path.split('/'):
        if piece in ('', '.'):
            continue
        if piece == '..':
            if parts:
                parts.pop()
            continue
        parts.append(piece)
    return '/' + '/'.join(parts)


def children(path: str, tree: Dict[str, Node]) -> List[str]:
    """Return the immediate entry names inside a directory."""
    prefix = '/' if path == '/' else path + '/'
    found = set()
    for candidate in tree:
        if candidate == path or not candidate.startswith(prefix):
            continue
        rest = candidate[len(prefix):]
        found.add(rest.split('/', 1)[0])
    return sorted(found)
