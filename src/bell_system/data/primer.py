"""
The annual refresher on the machine itself.

Every implemented part of the Seventh Edition toolkit works and almost
none of it is discoverable. /usr/doc/loop.pic is a diagram and prints as
nine lines of markup, because it is pic(1) source and wants running
through pic(1). /usr/doc/why.unix is a document and wants nroff(1). A
player who cats them sees dot commands and concludes the files are
broken, which is a fair conclusion and the wrong one.

So this is the course. It is written as the refresher a craftsperson was
made to sit once a year and mostly did not need, which is why it is short
and slightly weary about itself: the fiction has to carry the teaching,
because a tutorial box would not survive contact with the rest of this
simulation.

Nothing in here is a Bell System document. The commands and their
behaviour are Seventh Edition, which the bundled UNIX documentation
covers; the course around them, the wire chief's remarks and the framing
as an annual requirement are the simulation's own.
"""

from typing import Sequence, Tuple

# One section to a heading. Kept as data rather than one long string so
# the course reads as a course and the terminal can rule between parts.
Section = Tuple[str, Sequence[str]]

TITLE = 'BSP 000-100-000 - ANNUAL REFRESHER, MACHINE OPERATION'

OPENING: Sequence[str] = (
    "Everybody at a craft position sits this once a year. Most of you do",
    "not need it. It is here because the machine on your desk is a general",
    "purpose computer that happens to have a repair bureau on it, and the",
    "half of it that is not the bureau is worth ten minutes of your time.",
    '',
    "The short version: this is a UNIX system. Everything on it is a file,",
    "including your board, your mail and the practices.",
)

SECTIONS: Sequence[Section] = (
    ('LOOKING AROUND', (
        "ls                 what is in this directory",
        "ls -l              the same, with owner, size and date",
        "cd /usr/doc        go somewhere",
        "cd                 go back to your own directory",
        "pwd                where am I",
        '',
        "Directories worth the walk: /usr/doc, /usr/bsp, /usr/lmos,",
        "/usr/games, /usr/spool/news, and /usr/users, which has the notes",
        "whoever held your position last left behind.",
    )),
    ('READING THINGS', (
        "cat <file>         print a file",
        "more <file>        print it a screen at a time",
        "head, tail         the first or last few lines",
        "grep <word> <file> the lines with a word in them",
        "wc -l <file>       how many lines",
        '',
        "man <command>      the manual page for anything on this machine",
        '',
        "man(1) is the one to remember. Every command here has a page and",
        "the pages were written by the people who wrote the commands.",
    )),
    ('DOCUMENTS ARE NOT FILES YOU READ DIRECTLY', (
        "A document on this machine is kept as its source, with formatting",
        "instructions in it, and is run through a formatter to be read.",
        "This surprises people every year, so:",
        '',
        "nroff <file>       format a document for a terminal",
        "pic <file>         draw the diagrams in it",
        "refer <file>       resolve the citations in it",
        '',
        "Which is why cat(1) on /usr/doc/why.unix gives you dot commands",
        "and a mess. Try instead:",
        '',
        "     nroff /usr/doc/why.unix",
        "     pic /usr/doc/loop.pic",
        '',
        "The second one is a picture of a subscriber loop, and it is worth",
        "four minutes if you have never had one drawn for you.",
    )),
    ('JOINING COMMANDS TOGETHER', (
        "The output of one command becomes the input of the next if you put",
        "a vertical bar between them. This is the whole idea of the system",
        "and it is why there are so many small commands rather than a few",
        "large ones.",
        '',
        "     who | wc -l                    how many people are on",
        "     grep PEND /usr/lmos/board      the reports still open",
        "     ls /usr/lmos | wc -l           how big the board is",
        '',
        "You can send output to a file with a greater-than sign, and run",
        "two commands on one line by putting a semicolon between them.",
    )),
    ('YOUR BOARD IS A DIRECTORY', (
        "/usr/lmos holds one file for every report on your board, with the",
        "whole record in it, plus three that are always there:",
        '',
        "     board          the pending list, one line to a report",
        "     closed         what you have closed, and how it was judged",
        "     cable          where the water is, and what it has taken",
        '',
        "So there are two ways to work and neither is the proper one:",
        '',
        "     report                         the board, as a screen",
        "     cat /usr/lmos/board            the board, as a file",
        "     grep WRONG /usr/lmos/closed    what you got wrong today",
        '',
        "Your mail is a file as well, under /usr/spool/mail.",
    )),
    ('THE REST OF IT', (
        "There is more on here than the job. Some of it is useful, some of",
        "it was written by somebody at Murray Hill on a Friday, and part of",
        "the point of a machine like this is that you cannot always tell",
        "which is which until you have looked.",
        '',
        "     readnews       the netnews feed. It comes in overnight",
        "     /usr/games     it is a long night shift",
        "     fortune        exactly what it sounds like",
        '',
        "Go and poke at it. Nothing on this machine will break from being",
        "read, and the parts that would break are not yours to write to.",
    )),
)

CLOSING: Sequence[str] = (
    "That is the refresher. Sign the sheet on the way out.",
    '',
    "hint(1) if you are stuck on the job rather than on the machine.",
    "'training' on its own is the qualification record.",
)
