"""
What happens to a person when the board does what it does.

A missed commitment, a close that was wrong, a close that was right: each
of them lands on somebody, and this is what that somebody says. The index
already counts all three. These are the same events with a person on the
other end, which is pillar 2 of docs/design/plan.md.

The speaker is nearly always Reyes, the repair service attendant, because
she is the one who takes the call (narrative-bible.md section 4). So every
line here is hers, and she keeps to her profile: she gives the report, the
number to ring and a time, she asks the question she has to answer, and she
never blames a person and never guesses a cause out loud. A line that
names a fault, a cable or a part is the player's to work out, not hers to
say, and the tests hold every line here to that.

The customers' words come through her, one line each, by class of service.
The classes are the six the reports carry (``reports.CLASSES_OF_SERVICE``).
A customer on ordinary reports has no voice of their own (bible section 4,
"Others without a voice yet"), so these are about a kind of line and not
about a person.

Everything below is the simulation's own. No customer, company or call
record was consulted, and none should be inferred.
"""

from typing import Dict, NamedTuple


class Late(NamedTuple):
    """A report past its commitment, as the people on the telephone know it."""

    number: str
    telephone: str
    class_of_service: str
    out_of_service: bool
    committed: str


# What a customer with no telephone says to the attendant, by class. One
# line, read after her own.
OVERDUE: Dict[str, str] = {
    '1FR': "They are ringing from a neighbour's. There is no telephone in "
           "the house.",
    '1MR': "They are ringing from work. There is nobody at home to let "
           "anybody in.",
    '1FB': "It is a shop. They have said they are losing the afternoon, "
           "and they have said it twice.",
    'PBX': "It is a switchboard. Nobody outside can reach any extension "
           "behind it.",
    'COIN': "It is the only pay telephone on that block.",
    'PVT': "It is a private line. The other end is ringing me as well, "
           "and they want one answer.",
}

# The customer's second call, after a close that was wrong and a report that
# has come back. One line each, and each ends on the question she has to
# answer.
SECOND_CALL: Dict[str, str] = {
    '1FR': "They say it is doing what it did before. What time can I give "
           "them to be home for it?",
    '1MR': "They took the morning for it once already. What time can I "
           "give them that they can plan around?",
    '1FB': "They run a business off it, and a second call is one they have "
           "to explain. When can I say?",
    'PBX': "The attendant at the switchboard says every extension is doing "
           "the same. What time do I give them?",
    'COIN': "The pay station is taking coins and giving nothing again. "
            "Somebody will ask me where the coins go. What do I say?",
    'PVT': "Private line again. Both ends say the trouble is at the other "
           "end. What do I tell them?",
}

# A call after a close that was right. Sometimes the customer rings to say
# so, which is rarer than ringing to say the opposite and is why it is worth
# the line. One line each, each a question she has to answer.
CALL_BACK: Dict[str, str] = {
    '1FR': "They rang to say it is working. Do I tell them it is closed?",
    '1MR': "They rang to say it is clear; they were home when it came "
           "back. Is it closed on your side?",
    '1FB': "The shop rang to say the line is back and they are taking "
           "calls again. May I tell them it is closed?",
    'PBX': "The switchboard rang to say every extension is back. They "
           "asked who to thank. What do I say?",
    'COIN': "The owner of the pay station rang to say it is taking coins "
            "and giving dial tone. Do they need to do anything more?",
    'PVT': "Both ends of the private line rang separately to say it is "
           "up. Do I tell them it is closed?",
}

# How often a customer rings back after a close that was right. The
# simulation's own figure, set so that it is a surprise and not a habit.
CALL_BACK_CHANCE = 0.25

# The class a line falls back to when the report names one the tables do
# not, which only a hand-edited save could produce.
DEFAULT_CLASS = '1FR'


def second_call(class_of_service: str) -> str:
    """The customer's words on the second call, for this class of service."""
    return SECOND_CALL.get(class_of_service, SECOND_CALL[DEFAULT_CLASS])


def call_back(class_of_service: str) -> str:
    """The customer's words after a close that was right."""
    return CALL_BACK.get(class_of_service, CALL_BACK[DEFAULT_CLASS])


def overdue(class_of_service: str) -> str:
    """What a customer with no telephone says, past the commitment."""
    return OVERDUE.get(class_of_service, OVERDUE[DEFAULT_CLASS])
