"""
Home directories, one for each position somebody can be put at.

Selecting a role puts you in /usr/users/<role>, which for eleven of the
twelve was a directory that did not exist: pwd(1) named it and ls(1) said
it was not there. This is what is in each of them.

A position is not really different from another one because the help text
differs. It is different because the person who had it before you left
different things lying around. So each home carries a .profile that sets
the terminal up the way that desk wants it, and a file left by whoever sat
there last - which is where a good deal of what you need to know about the
job actually lives.

The people named are this simulation's own. Everything they describe about
the plant is grounded where the rest of the simulation grounds it.
"""

from typing import Dict

# What every .profile on this machine starts with. The real ones were this
# short: a path, a terminal, and the erase and kill characters, because a
# terminal that could not backspace was the first thing you fixed.
_COMMON = """PATH=:/bin:/usr/bin
export PATH
SHELL=/bin/sh
export SHELL
TERM=43
export TERM
stty erase '^h' kill '^u'
"""


def _profile(role: str, tail: str) -> str:
    """Assemble one .profile: the common part, then what this desk adds."""
    return (f"# Profile for the {role} position\n"
            f"{_COMMON}HOME=/usr/users/{role}\nexport HOME\n{tail}")


HOMES: Dict[str, Dict[str, str]] = {

    'sysop': {
        '.profile': _profile(
            'operations',
            'echo "Board:"; report\n'),
        '.mailrc': "set nosave\nalias chief ehalloran\nalias board mreyes\n",
        'notes': """Notes left for whoever has this position next.

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
""",
    },

    'switch': {
        '.profile': _profile(
            'switching',
            'echo "Office:"; alarm\n'),
        'aisle.notes': """The No. 5 crossbar, aisle by aisle, as I found it.

AISLE 1-2   Line link frames. Nothing here goes wrong that is not a
            relay, and a relay that has gone wrong has usually been
            gone wrong for a while.

AISLE 3     Originating registers. If dial tone is slow at nine in the
            morning it is because there are not enough of these free,
            not because anything is broken. Traffic engineering knows.

AISLE 4     Markers. Number 2 is slow on the third trial. It has been
            slow on the third trial since 1981. Two people have looked
            at it and both wrote NTF, and they were both right: the
            trouble is in the timing chain and the timing chain is
            within limits. Leave it.

AISLE 5-6   Trunk link frames and the outgoing senders.

The rule with a common control office is that the control is common.
One marker serves every call that wants one, so a marker that is
marginal does not break one call, it makes thousands of calls slightly
worse and none of them badly enough to report. That is why you find it
in the peg count and not in a trouble ticket.

                                             - T. Nakamura
""",
    },

    'field': {
        '.profile': _profile(
            'field liaison',
            'echo "Dispatched:"; trouble list\n'),
        'crews.notes': """Who is out, and what they are good for.

There are three splicing crews and one installation crew on this wire
centre, and the difference between a good tour and a bad one is whether
you sent the right one.

A splicer fixes the cable. An installer fixes the station and the drop.
If you are not sure which side of the protector the trouble is on, do
not guess - run a loop test first. An installer sent to a wet cable
comes back having done nothing and the customer has had a morning off
work for nothing.

Vasquez's crew will take a fourth job at four o'clock and finish it.
Nobody else will. Do not spend that on something that could wait.

The commitment is a promise the company made to a person, not a target
somebody set for you. When it is going to be missed, the useful thing
is to say so early, not to be right about why.

                                             - M. Reyes
""",
    },

    'noc': {
        '.profile': _profile(
            'network operations',
            'echo "Network:"; capacity\n'),
        'watch.notes': """What this position is actually watching for.

Not faults. Faults have their own people and their own board. What you
are watching for is the shape of the traffic changing, because that is
the thing nobody else in the network is positioned to see.

A single trunk group over its objective is a trunk group problem. Three
groups over their objective all homing on the same sectional centre is
something else, and it will not show up as anything at all in the
offices underneath it. Each one of them will report a normal day.

Learn what a normal hour looks like on this network before you try to
spot an abnormal one. Run capacity at the same time every morning for a
fortnight. The numbers are boring and then one day they are not, and
you will only know which day that is because you know what boring
looks like.

Mother's Day is the busiest calling day of the year and everybody has
known that for forty years. It is not a surprise and it is not an
outage. Do not raise anything.

                                             - E. Halloran
""",
    },

    'tsps': {
        '.profile': _profile(
            'traffic service position',
            'echo "Position:"; tsps status\n'),
        'position.notes': """The job in one line: you are the part of the network that can
hear.

Everything else here is equipment. Equipment can complete a call, time
it and bill it, and equipment cannot ask a person whether they will
accept the charges and understand the answer. That is why this room
exists and that is the whole of what it is for.

Practical things nobody writes down:

A collect call is not accepted until you have heard someone say so. Not
a noise, not a click. If you are not sure, ask again.

The caller can hear you the entire time. Every word.

Coin overtime comes up before the money does, so you have a few seconds
where you know the call is about to be cut off and they do not. Use
them.

The average call at this position is under thirty seconds and there are
several hundred of them in a tour. It is not hard work. It is the same
work, at speed, all day, and the mistake people make is treating the
four hundredth one differently from the first.

                                             - D. Petrak
""",
    },

    'dba': {
        '.profile': _profile(
            'records',
            'echo "Systems:"; dbquery\n'),
        'records.notes': """The records are not the plant. Say that to yourself every
morning.

COSMOS says the pair is spare. The pair has a working line on it. One
of those is a fact and the other is a record, and the wire does not
care what the record says.

Most of what this position does is find the places where the two have
drifted apart and put them back together. They drift for ordinary
reasons: a service order that was worked and never closed out, a
temporary cross-connect somebody put up at two in the morning, a
disconnect where the physical work happened three weeks after the
paperwork.

The dangerous drift is the other direction. A pair the records think is
working and is actually spare costs nothing. A pair the records think
is spare and is actually working gets assigned to somebody new, and
then two customers are on one pair and both of them report trouble
and neither report makes any sense.

When you find one, fix the record and then go and find out how it got
that way. There is almost never only one.

                                             - L. Okafor
""",
    },

    'netplan': {
        # capacity(1) rather than tnds(1): planning is signed off for
        # interoffice trunks, not for the toll network, and a profile that
        # opens on a command the desk cannot run is no use to anybody.
        '.profile': _profile(
            'network planning',
            'echo "Groups:"; capacity\n'),
        'planning.notes': """You are being asked what the network needs eighteen months
from now, and everything you have to answer with is a measurement of
what it needed last month.

That is the whole difficulty and no amount of arithmetic removes it.

Two things are worth knowing.

The first is that trunks are ordered, built and turned up on a schedule
measured in quarters, so a group that is over its objective today has
been over it for a while and will be over it for a while longer. By the
time you are looking at it the decision that mattered was made a year
ago by somebody who is not you.

The second is that the growth in this network is not in the number of
telephones. It is in what people put on the line once they have it:
data sets, private lines, foreign exchange. A forecast built on
telephone counts will be wrong in a direction nobody notices until the
special services group runs out of facilities.

After January this is somebody else's forecast anyway. The lines cross
a boundary that will exist by then, and nobody has told me who does the
arithmetic for a circuit with one end in each company.

                                             - E. Halloran
""",
    },

    'custserv': {
        '.profile': _profile(
            'customer service',
            'echo "Board:"; report\n'),
        'contact.notes': """What the person on the other end of the line actually wants.

They want their telephone to work. They do not want an explanation of
why it does not, they do not want the name of the system that will fix
it, and they very much do not want to hear the word "facility".

Three things, in order:

Believe them. The most common opening in this job is a customer being
carefully talked out of a trouble that turns out to be real. The line
tests fine from here about a third of the time and the trouble is real
about a third of the time, and those are not the same third.

Give a time and keep it. A commitment kept badly beats a commitment
missed politely. The index measures the same thing.

Say what will happen next in words they can repeat to somebody else,
because they will have to.

The one thing you are not allowed to do is guess out loud. "It's
probably the cable" gets repeated back to you in three days as
something the telephone company said.

                                             - M. Reyes
""",
    },

    'radio': {
        '.profile': _profile(
            'radio',
            'echo "Routes:"; microwave\n'),
        'paths.notes': """Radio is not like the rest of the plant and the difference
catches people out.

Everything else here you can go and touch. A pair is a pair, a relay is
a relay, and if it is broken there is a place you can stand where the
broken thing is in front of you. A radio path is twenty-six miles of
air and there is nowhere to stand.

So the questions are different. Not "what is broken" but "what is the
margin, and what is eating it".

Rain is the honest answer most of the time at six gigahertz. Heavy rain
on a long hop takes the fade margin and there is nothing to do and
nothing to fix; diversity switches over and you watch it until the
weather goes past. That is not a trouble and writing it up as one just
means somebody drives out to a tower to confirm that it was raining.

The dishonest answers are the interesting ones. A path that fades on a
clear morning is not weather. Look at the tower first: a dish that has
moved a fraction of a degree over a winter will do exactly that, and it
will do it worse every month until somebody realigns it.

The other one is a path that is fine except at the same time every day.
That is the sun, or it is somebody else's transmitter, and either way
it is a pattern and patterns are findable.

                                             - G. Vasquez
""",
    },

    'tnds': {
        '.profile': _profile(
            'network data',
            'echo "Collection:"; tnds status\n'),
        'data.notes': """What the measurements are and what they are not.

Every office in this network counts things: calls offered, calls
completed, how long the registers were held, how many times a group
went all-trunks-busy. Those counts come up here, and this position
turns them into the numbers that decide where the money goes next year.

The temptation is to believe the numbers because they came off a
machine. Resist it. A peg count counts what the counter is wired to
count, and the counter was wired by a person, sometimes twenty years
ago, sometimes to a slightly different definition than the office next
door uses.

So before you report a difference between two offices, find out whether
it is a difference in the traffic or a difference in the counting. It
is the counting more often than anybody wants to admit.

The other thing: a busy hour is a measurement, not an opinion. It is
the highest hour, found by measuring, and it moves. An office
engineered to a busy hour that stopped being the busy hour three years
ago is engineered to nothing at all.

                                             - T. Nakamura
""",
    },

    'sarts': {
        '.profile': _profile(
            'special services',
            'echo "Circuits:"; sarts\n'),
        'circuits.notes': """A special service circuit is one that does not go through the
switch, and everything difficult about this position follows from that.

An ordinary line has one customer, one pair and one office, and when it
breaks you know within about three questions which of those to look at.
A private line has two ends, a number of offices in between, and
equipment at every one of them that somebody had to install to a
specification that was written for that one circuit.

So when it breaks, nobody owns it. Each office looks at their piece,
finds their piece within limits, and says so, truthfully, and the
circuit is still down.

That is what this position is for. You are the only person who can see
the whole circuit at once, which means you are the only one who can
find the section that is in limits at both ends and still wrong in the
middle.

Get the layout record before you get on the phone to anybody. Half the
troubles on this desk are somebody testing a section that is not in
the circuit any more because it was rearranged in 1979.

                                             - R. Johnson
""",
    },

    'docprep': {
        '.profile': _profile(
            'document preparation',
            'echo "Papers in /usr/dict/papers, documents in /usr/doc."\n'),
        'formatting.notes': """How the tools fit together, since nobody explains it.

They are a pipeline and each one only does its own job:

    tbl  handles tables
    eqn  handles mathematics
    pic  handles diagrams
    refer  fills in citations
    nroff  fills and sets the text
    troff  the same, for a typesetter

The preprocessors go first, in that order, and each one reads what came
before it. So a document with a table and a diagram in it is

    pic file | tbl | nroff

and if you get the order wrong the second one sees the first one's
output as text and sets it as text, which looks exactly like your
document being mangled for no reason.

The other thing worth knowing: nroff fills. It takes your lines apart
and reassembles them to the measure, which is what you want for prose
and is a disaster for anything laid out in columns. .nf stops it and
.fi starts it again, and every mysterious formatting problem anybody
has ever brought to this desk was one of those two in the wrong place.

/usr/doc/why.unix has citations in it if you want something to practise
refer on.

                                             - D. Petrak
""",
    },
}
