"""
What to say to somebody who has asked for help, at three depths.

Infocom sold hint booklets printed in invisible ink: you revealed one hint
at a time with a marker, so what you got was the smallest nudge that
unstuck you rather than the answer to the puzzle. That worked because
asking was a deliberate act and because the first thing revealed was never
the solution. This table is the same shape.

Three levels to a situation, and each is a different person, because who
would tell you is part of what makes it land:

    1  Vasquez on write(1). She lives on the testboard and will tell you
       the reading before you ask for it, so hers is a nudge and no more.
    2  Something on this machine to go and read. Every reference here is
       a real file or a real command in this simulation - a Bell System
       Practice division that exists under /usr/bsp, a manual page that
       exists. None of it is an invented section number.
    3  Halloran, who signs your qualifications, saying it outright. He is
       short about it, because by this point you have asked three times.

The situation keys are the steps :func:`bell_system.screens.guidance.
GuidanceCommands.next_action` already returns, so the hint system and the
standing prompt cannot end up describing different situations.
"""

from typing import Dict, Sequence, Tuple

# One entry per level: the login of whoever says it, and their lines.
Hint = Tuple[str, Sequence[str]]

HINTS: Dict[str, Tuple[Hint, Hint, Hint]] = {
    # A first tour, before anything has been closed. The whole answer here
    # is that there is a loop at all.
    'first': (
        ('gvasquez', (
            'You have one report and about a day of commitment on it, so',
            'there is no hurry. Everything you need is on the board itself:',
            "type 'report' and read the line along the bottom.",
        )),
        ('ehalloran', (
            "Try 'help'. The top of it says what to do next, and it works",
            'it out from your own board rather than from a script.',
            "'man report' is the long version.",
        )),
        ('ehalloran', (
            'Four commands. report, then mlt, then report dispatch, then',
            'report close. That is the job. The rest of this machine is',
            'yours to explore once the board is clear.',
        )),
    ),
    # Something on the board has not been measured.
    'measure': (
        ('gvasquez', (
            'You are working a report nobody has put a meter on. Verify,',
            'locate, repair, verify - and you are still on the first one.',
            'Test it before you send anybody anywhere.',
        )),
        ('ehalloran', (
            "'man mlt' explains what mechanised loop testing measures and",
            'what each reading means. Division 660 under /usr/bsp is test',
            "centre operation, and 'report faults' lists every condition.",
        )),
        ('ehalloran', (
            "Type 'mlt' and the report number. Read the TEST RESULT block",
            'at the bottom. It names the fault and it names the crew. It',
            'is not a riddle.',
        )),
    ),
    # Measured, and now somebody has to go.
    'dispatch': (
        ('gvasquez', (
            'You have the reading. The bottom of it told you where the',
            'trouble is, and where it is decides who goes: the loop is not',
            'the office and the office is not the station.',
        )),
        ('ehalloran', (
            "'report forces' lists who we can send. Division 620 under",
            '/usr/bsp is outside plant, which is most of what goes wrong.',
            "'report show' will show you the reading again.",
        )),
        ('ehalloran', (
            "'report dispatch <number> <force>'. The force is the one the",
            'test named. Send anybody else and you have spent three',
            'quarters of an hour proving the meter right.',
        )),
    ),
    # The field has been and gone and nobody has closed it out.
    'close': (
        ('gvasquez', (
            'Somebody has been out to that one and called in. Until it is',
            'closed out it is still on your board and still running',
            'against the commitment.',
        )),
        ('ehalloran', (
            "'man report' has the disposition codes. Five is trouble found",
            'and you name the condition; eight is no trouble found. They',
            'are counted separately and they are counted.',
        )),
        ('ehalloran', (
            "'report close <number> 5 <fault>', with the fault the test",
            'gave you. Not the one the customer described - the one on the',
            'pair.',
        )),
    ),
    # With the field. There is genuinely nothing to do about that one.
    'wait': (
        ('gvasquez', (
            'That one is out with a crew and it will be a while. Nothing',
            'you type here brings them back any faster.',
        )),
        ('ehalloran', (
            "Look at the rest of the board with 'report', or your record",
            "with 'qual'. There is usually something else running.",
        )),
        ('ehalloran', (
            'Wait. Work something else, read something, or go and get a',
            'coffee. They will call in.',
        )),
    ),
    # Board clear. Not a failure state: it is the point of the job.
    'idle': (
        ('gvasquez', (
            'Clear board. Take it - they do not last. More will come in',
            'as the tour goes on.',
        )),
        ('ehalloran', (
            "'readnews' is the netnews spool and there is a fair amount on",
            "it. /usr/doc has what is going on with the company. 'qual'",
            'says how far off your next sign-off is.',
        )),
        ('ehalloran', (
            'There is nothing to do. That is allowed. Look around the',
            'machine - it is a UNIX system and most of it works.',
        )),
    ),
}

# What the last level says when it has already been said. Not a fourth
# hint: an admission that there is nothing further to give, which is more
# honest than repeating the third one and pretending it is new.
EXHAUSTED = (
    'That is everything I have on it.',
    "If it is still not moving, 'help' works out the next command from",
    'your own board, and it does it every time you ask.',
)
