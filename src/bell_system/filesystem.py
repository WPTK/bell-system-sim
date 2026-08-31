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

from typing import Callable, Dict, List, NamedTuple, Optional, Union

# Divestiture took effect on 1 January 1984.
DIVESTITURE = '1984-01-01'

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
Questions:       write ehalloran
"""

PASSWD = """root::0:1::/:/bin/sh
daemon::1:1::/:
bin::3:3::/bin:
sys::4:4::/usr/src:
adm::5:5::/usr/adm:
uucp::6:6::/usr/spool/uucp:/usr/lib/uucp/uucico
sysop::17:1::/usr/users/sysop:/bin/sh
rjohnson::21:1::/usr/users/rjohnson:/bin/sh
mreyes::22:1::/usr/users/mreyes:/bin/sh
dpetrak::23:1::/usr/users/dpetrak:/bin/sh
lokafor::24:1::/usr/users/lokafor:/bin/sh
gvasquez::25:1::/usr/users/gvasquez:/bin/sh
ehalloran::26:1::/usr/users/ehalloran:/bin/sh
tnakamura::27:1::/usr/users/tnakamura:/bin/sh
"""

GROUP = """other::1:
daemon::1:daemon
bin::3:bin
sys::4:sys
adm::5:adm
uucp::6:uucp
craft::10:rjohnson,lokafor,gvasquez,mreyes
mgmt::11:ehalloran,dpetrak,tnakamura
"""

PROFILE = """# Profile for the operations position
PATH=:/bin:/usr/bin
export PATH
HOME=/usr/users/sysop
export HOME
SHELL=/bin/sh
export SHELL
TERM=43
export TERM
stty erase '^h' kill '^u'
echo "Board:"; report
"""

NOTES = """Notes left for whoever has this position next.

Read /usr/doc/divestiture before you do anything else. It is not
optional and it is not long.

The board fills faster than it clears between about ten and two. Work
the nearest commitment first, not the oldest report - they are not the
same thing and the index only cares about the commitment.

If you get three or four reports off one cable in the same morning,
stop and look at the cable and pair before you dispatch anybody. It is
almost always water and one splicer trip fixes all of them. I sent four
separate crews to Franklin Street last month. Do not be me.

Halloran reads the index every morning. He will not say anything if it
is good.

The 5 crossbar in aisle four has a marker that takes its time on the
third trial. It has been like that for two years. It is not yours to
fix and it is not worth a ticket.

                                             - R. Alvarez, tour 2
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
uucico mhuxco (11/14-04:00) SUCCEEDED (call to research)
uucico mhuxco (11/14-04:02) OK (conversation complete)
uucico mhuxco (11/14-06:44) FAILED (call to ihnp4, no answer)
"""

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

    '/usr/doc': _dir(),
    '/usr/doc/divestiture': _file(DIVESTITURE_MEMO),
    '/usr/doc/bulletin': _file(BULLETIN),

    '/usr/src': _dir(owner='sys', group='sys'),
    '/usr/src/cmd': _dir(owner='sys', group='sys'),
    '/usr/src/cmd/hello.c': _file(HELLO_C, owner='sys', group='sys'),
    '/usr/src/cmd/testlog.c': _file(TESTLOG_C, owner='sys', group='sys'),

    '/usr/games': _dir(),
    '/usr/games/fortunes': _file(FORTUNES),

    '/usr/bsp': _dir(),
    '/usr/lmos': _dir(owner='sysop', group='craft'),

    '/usr/users': _dir(),
    '/usr/users/sysop': _dir(owner='sysop', group='craft', mode='drwxr-x---'),
    '/usr/users/sysop/.profile': _file(PROFILE, owner='sysop', group='craft'),
    '/usr/users/sysop/notes': _file(NOTES, owner='sysop', group='craft'),
}

# Home directories for the other craft, so /usr/users is not a lie.
for _login in ('rjohnson', 'mreyes', 'dpetrak', 'lokafor', 'gvasquez',
               'ehalloran', 'tnakamura'):
    FILESYSTEM[f'/usr/users/{_login}'] = _dir(
        owner=_login, group='craft', mode='drwxr-x---')


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
