"""
What the last night says, and what it answers to.

The ending used to be one message from the wire chief that read three
numbers. It now reads the career: how the audit went, whether the player
found the files that explain the building, whether the people on the board
did them a good turn, what was earned. Everything here is a function of
those, so the same career always ends the same way and a resumed one says
nothing different.

Rules the text keeps:

* Nothing here names a fault, a disposition or a cause for any
  report. It reads what the career amounted to, never what was true of a
  line, so a second career has no key to a board by reading the first one's
  ending.
* Nothing is pushed that the machine keeps for the player to find.
  A line may say that something was read; it never says what is in it. Reyes
  speaks of the log only when the player has read the log.
* No cutscene. Each piece is a message on a channel the
  building already has, in its speaker's voice, two lines
  and no more, each well inside 120 characters.
* The audit changes the words, not the length of the career.

The wording is the simulation's own. The one period fact, that the operating
companies passed to the regional holding companies on 1 January 1984, is the
date ``clock.py`` quotes from Engineering and Operations; a holding company
is named only where ``data/companies.py`` marks the assignment verified.
"""

from typing import FrozenSet, List, NamedTuple, Optional, Tuple

from ..npc import AUDIT_EXCEPTIONS, AUDIT_FAILED

# Channel names, repeated here because this module is read by npc.py's
# tests as plain data; they are the ones in npc.py.
WRITE = 'write'
ORDERWIRE = 'orderwire'
TELETYPE = 'teletype'


class Ring(NamedTuple):
    """The one report Reyes speaks of: a number to ring and a time."""

    number: str
    telephone: str
    time: str
    # 'open' for one that goes over on the board, 'closed' for the last one
    # closed when the board is clear.
    state: str


class Shape(NamedTuple):
    """Everything about a career that the ending reads, and nothing else."""

    verdict: str
    closed: int
    # Whether the sheath side has work that is not done: a report sent to the
    # cable force and still open, or the Franklin sheath Sandoval spoke of.
    sheath_open: bool
    # Whether the hour Reyes got on a report was kept, by that report being
    # closed inside the commitment as extended.
    hour_kept: bool
    # The company the player's own office belongs to. Empty where the office
    # is in a state with no wholly-owned company (Connecticut).
    company: str
    # The regional holding company, only where the assignment is verified.
    holding: str
    # What to say instead of a company where there is none.
    outside: str
    heard: FrozenSet[str]
    favours: FrozenSet[str]
    finds: FrozenSet[str]
    commendations: FrozenSet[str]
    ring: Optional[Ring]


def _transfer(shape: Shape) -> List[str]:
    """The maintenance teletype: where the office goes. A machine, so no 'you'."""
    if shape.company:
        first = f"mhuxco: position closed. records to {shape.company}."
        second = (f"holding company {shape.holding}. effective 1/1/84."
                  if shape.holding else "effective 1/1/84.")
    else:
        first = "mhuxco: position closed."
        second = (f"{shape.outside}: minority-held, outside the divestiture."
                  if shape.outside else "effective 1/1/84.")
    return [first, second]


def _reyes(shape: Shape) -> List[str]:
    """The bureau, once: a report, a number to ring, a time, a question."""
    ring = shape.ring
    if ring is None:
        first = "My sheet is clear."
    elif ring.state == 'open':
        first = (f"{ring.number} on {ring.telephone}, due {ring.time}, "
                 f"goes over open.")
    else:
        first = (f"{ring.number} on {ring.telephone}, closed {ring.time}, "
                 f"has not rung back.")
    # The record journal is the fourth sign-off's, and the chief's own list
    # the fifth's (data/finds.py). She says no more than she knows: that the
    # machine refused her, and that the reports it refused her are open now.
    # The chief did not tell her he reopened them, so she asks who did.
    if 'lmoslog' in shape.finds and 'reopened' in shape.finds:
        second = ("The ones I could not reopen are open again. "
                  "I did not open them. Who did?")
    elif 'lmoslog' in shape.finds:
        second = ("I tried to reopen one at 03:41 and it said no. "
                  "Does it still say no?")
    elif ring is None:
        # Nobody to ring, so nothing to tell anybody.
        second = _no_ring(shape)
    elif 'mreyes' in shape.favours and shape.hour_kept:
        second = ("The hour I asked for was kept. "
                  "What do I tell them on the second?")
    elif shape.verdict == AUDIT_FAILED:
        second = "The audit has it with your name. What do I tell them?"
    elif shape.verdict == AUDIT_EXCEPTIONS:
        second = "The audit noted it. What do I tell them?"
    else:
        second = "They will ring on the second. What do I tell them?"
    return [first, second]


def _no_ring(shape: Shape) -> str:
    """Reyes with no report to speak of: nobody has rung, so nobody is asked."""
    if shape.verdict == AUDIT_FAILED:
        return "The audit has it with your name. Nobody has rung yet."
    if shape.verdict == AUDIT_EXCEPTIONS:
        return "The audit noted it. Nobody has rung yet."
    return "Nobody has rung. If they do on the second, I will know what to say."


def _sandoval(shape: Shape) -> List[str]:
    """The field, once: the order-wire form and little else."""
    first = "Field to test desk."
    if 'sandoval.2' in shape.heard and shape.company:
        return [f"{first} The memo means {shape.company}.",
                "I read the line again. I will be here on the second."]
    if 'jsandoval' in shape.favours:
        return [f"{first} You sent me the jobs that fit.",
                "That is not nothing. Thank you."]
    if shape.sheath_open:
        return [f"{first} The sheath side is not finished.",
                "It will be there when the next one comes on."]
    return [f"{first} Nothing open on the sheath side.",
            "That is all I have."]


def halloran_note(shape: Shape) -> List[str]:
    """
    What the wire chief adds, in front of 'Go home.', for what he saw.

    He reads the index every morning and does not praise it; he says one
    plain thing about the record and stops. Nothing when there is nothing.
    """
    if 'first_clean_tour' in shape.commendations:
        return ["There was a tour you handed over clean.",
                "I did not say so then. It is on the record."]
    if 'retain' in shape.finds:
        return ["You read what is kept. All of it is kept seven years.",
                "Your record will be in it."]
    return []


def pieces(shape: Shape) -> List[Tuple[str, str, List[str]]]:
    """
    The epilogue as (channel, sender, lines), in the order it is said.

    The teletype first, since a machine is what outlasts a shift; then the
    two people whose arcs end on the last tour. The wire chief's own word
    follows these in ``npc.Switchroom.last_word``, which is always last.
    """
    return [
        (TELETYPE, 'adm', _transfer(shape)),
        (WRITE, 'mreyes', _reyes(shape)),
        (ORDERWIRE, 'jsandoval', _sandoval(shape)),
    ]
