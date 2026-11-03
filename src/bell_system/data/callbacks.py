"""
What a customer says when you ring them back.

A callback used to be one call with one answer. The customer, though, is
asked different questions by different attendants and says different things,
and a repair service attendant who had the right question to hand learned
more from three words than from a paragraph. Here a callback asks one
question: ``report callback <number> <topic>``. Each question costs the same
call, and each answer is true of the line and says only what a customer
would say.

An answer narrows what the trouble can be and never names it. Several
conditions give the same words, and the same words are said whichever of
them it is, so the answer cannot tell the two apart; the measurement and the
field have to. How far a question narrows it is the test in
tests/test_board_cases.py: no answer is given by every condition, and none
by only one that the others could not also be said of, except where the
customer has in fact seen nothing else (a clean line).

Nor do two questions together settle which force to send. For every pair of
them there is a condition whose two answers fit conditions that different
forces clear: a cross and a wet sheath both creep up on a house and are
both shared with a neighbour. That is tests/test_phase8_fixes.py, over the
pairs and not over any one answer.

The simulation's own. The conditions are the documented ones (data.trouble);
what a customer says of each is the simulation's own, as REPORT_SYMPTOMS is.
No source gives a script for these calls.
"""

from typing import Dict, NamedTuple, Optional, Tuple


class Topic(NamedTuple):
    """One question a callback can ask."""

    key: str
    # The question, as the attendant puts it.
    asks: str
    # What the customer says, by the condition the line is really in.
    heard: Dict[str, str]


# The old callback, one account and no question. Still what a bare
# ``report callback`` gets.
GENERAL: Dict[str, str] = {
    'OPEN': "It went dead all at once. There was work in the street last "
            "week.",
    'SHORT': "Nothing at all when I pick it up, and my daughter says she "
             "gets a busy signal every time.",
    'GROUND': "There is a hum, worse when it rains, and sometimes it rings "
              "once by itself.",
    'CROSS': "I can hear two other people talking. They can hear me as "
             "well.",
    'WET': "It has been getting worse all week, since the storm. The "
           "neighbours have it too.",
    'FCG': "I get nothing when I dial. The dial tone is there and then it "
           "just sits.",
    'FEMF': "There is a loud buzz, and I felt something off the set once. "
            "The power line runs right past.",
    'ROH': "No, I have not had any trouble calling out. People say they "
           "cannot reach me.",
    'CO_EQUIP': "It never rings. I have tried a different telephone and it "
                "does the same thing.",
    'NONE': "It happened twice on Tuesday and it has been fine since. "
            "Perhaps it fixed itself.",
}

# What a customer says they hear when a call will not go through, for the
# conditions where the answer is in the cadence and not in the words.
# Busy is 60 interruptions a minute and reorder is 120; they are the same
# 480 and 620 Hz, so the description says how fast and never says which.
# tone(1) writes both, which is the one question on this board that has to
# be answered by ear.
CADENCE_HEARD: Dict[str, str] = {
    'CO_EQUIP': "I dial and I get the busy signal, but it is going about "
                "twice as fast as a busy usually goes. It does it on every "
                "number I try, including my sister's, and she is not on "
                "the telephone.",
    'NONE': "I get the busy signal. The ordinary one, the slow one. It is "
            "just that I get it rather a lot lately, and I did wonder.",
    # Not a cadence at all, which is the point of having a third: the
    # office took the call and then did nothing with it, so there is
    # nothing to hear. Somebody comparing two tones has to notice that
    # neither of them is what this customer is describing.
    'FCG': "I dial the whole number and then there is nothing. Not a busy, "
           "not a ringing. It goes quiet and it stays quiet until I hang "
           "up.",
}

_ALL_AT_ONCE = ("All at once. It was fine and then it was not, and it has "
                "not changed since.")
_CREEPING = ("It crept up on us. A little worse every day, and a good deal "
             "worse after it rains.")
_PASSED = ("It was bad twice and then it stopped. It is fine as I talk to "
           "you, if that is any help.")

_EVERY_TELEPHONE = ("Every telephone in the house. I took the extensions "
                    "off and it was no different.")
_NEIGHBOURS = ("The house two doors down says theirs has been bad all week. "
               "Mine is the same on every telephone I plug in.")
_ONE_SET = "It is the one telephone. I tried another one and that was fine."

_NOTHING = "Nothing. It is dead, not even a hiss."
_DIAL_TONE = ("Dial tone, quite normal. It is when I start to dial that it "
              "goes wrong.")
_HUM = "A steady hum, and a buzz on top of it when somebody is on the line."
_VOICES = "Crackling, and now and then somebody else's voice far off."
_NORMAL = "Nothing wrong at this end. It sounds the way it always did."

TOPICS: Dict[str, Topic] = {
    'start': Topic('start', 'When did it start?', {
        'OPEN': _ALL_AT_ONCE, 'SHORT': _ALL_AT_ONCE, 'FCG': _ALL_AT_ONCE,
        'CO_EQUIP': _ALL_AT_ONCE, 'ROH': _ALL_AT_ONCE,
        'WET': _CREEPING, 'GROUND': _CREEPING,
        'CROSS': _CREEPING, 'FEMF': _CREEPING,
        'NONE': _PASSED,
    }),
    'others': Topic(
        'others', 'Is it the same on other telephones, or next door?', {
            'OPEN': _EVERY_TELEPHONE, 'SHORT': _EVERY_TELEPHONE,
            'GROUND': _EVERY_TELEPHONE,
            'FCG': _EVERY_TELEPHONE, 'FEMF': _EVERY_TELEPHONE,
            'CO_EQUIP': _EVERY_TELEPHONE,
            # A cross has a second pair in it, and that is a neighbour's.
            'WET': _NEIGHBOURS, 'CROSS': _NEIGHBOURS,
            'ROH': _ONE_SET, 'NONE': _ONE_SET,
        }),
    'hear': Topic('hear', 'What do you hear when you pick it up?', {
        'OPEN': _NOTHING, 'SHORT': _NOTHING,
        'FCG': _DIAL_TONE, 'CO_EQUIP': _DIAL_TONE,
        'GROUND': _HUM, 'FEMF': _HUM,
        'CROSS': _VOICES, 'WET': _VOICES,
        'ROH': _NORMAL, 'NONE': _NORMAL,
    }),
}


def topics() -> str:
    """The questions a callback can ask, as a line to print."""
    return ', '.join(TOPICS)


def asked(topic: str, fault: str, symptom: str) -> Optional[str]:
    """
    What the customer says to one question, or None if it is not one.

    Where a report is about calls not completing, the customer asked what
    they hear describes a rhythm and not the trouble (see CADENCE_HEARD),
    which replaces the ordinary answer rather than joining it.
    """
    found = TOPICS.get(topic.lower())
    if found is None:
        return None
    if (found.key == 'hear' and fault in CADENCE_HEARD
            and 'complete' in symptom.lower()):
        return CADENCE_HEARD[fault]
    return found.heard.get(fault, GENERAL.get(fault, ''))


def general(fault: str, symptom: str, described: str) -> Tuple[str, bool]:
    """
    What the customer says to the bare callback, and whether by ear.

    Args:
        fault: The condition the line is really in
        symptom: What the report says
        described: The condition's own description, for one the table
            does not have

    Returns:
        The words, and whether they are a cadence for tone(1) to settle
    """
    heard = CADENCE_HEARD.get(fault)
    by_ear = heard is not None and 'complete' in symptom.lower()
    if by_ear and heard:
        return heard, True
    return GENERAL.get(fault, described), False


def narrowed(topic: str, said: str) -> Tuple[str, ...]:
    """The conditions that give a customer exactly these words."""
    found = TOPICS[topic]
    return tuple(fault for fault, words in found.heard.items()
                 if words == said)
