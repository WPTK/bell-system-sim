"""
The Practices binder: tables a craftsperson applies, kept in /usr/bsp.

A Bell System Practice was a numbered sheet in a binder at the desk, and the
work was looking up what a reading meant and doing what the sheet said. These
are that, for the loop, and they are written to be applied rather than read:
every sheet is a table.

The sheet numbers are the simulation's own. Divisions 620 (Outside Plant -
General) and 660 (Test Center Operation) are real BSP divisions (see
BSP_CATEGORIES in :mod:`bell_system.constants`), but no Practice from either
was reachable, and the section and sheet numbers here are not Bell System
numbers. Every sheet says so in its header, and says which of its figures
come from a document in the repository (SOURCES.md) and which are the
simulation's own.

The tables are built from the same data the simulation runs on
(:data:`bell_system.data.trouble.FAULTS` and the constants in
:mod:`bell_system.loop_testing`), so a sheet cannot disagree with the
machine it describes.
"""

from typing import Callable, Dict, List, NamedTuple, Sequence

from ..loop_testing import (
    CABLE_UF_PER_MILE,
    COIN_STATION_CURRENT_MA,
    LOADED_DESIGN_LIMIT_OHMS,
    RESISTANCE_DESIGN_LIMIT_OHMS,
    distance_to_open,
)
from .trouble import FAULTS, REAL_FAULTS, REPORT_SYMPTOMS

RULE = '-' * 72

# Said at the head of every sheet, whatever else it says.
NUMBER_NOTICE = (
    "The number of this sheet is the simulation's own. Divisions 620 and 660 "
    "are Bell System divisions; the section and sheet numbers are not Bell "
    "System numbers, and no Practice was consulted.")

SOURCED = 'From a document in the repository'
OWN = "The simulation's own"


class Sheet(NamedTuple):
    """One Practice sheet."""

    number: str
    title: str
    # Each figure the sheet uses and where it comes from, as (what, source).
    basis: Sequence[tuple]
    # Builds the table and the lines under it.
    body: Callable[[], List[str]]


def _range(low_high: tuple) -> str:
    """Render an ohms range for a table cell."""
    low, high = low_high
    if low == 0:
        return f"under {high:,}"
    return f"{low:,} - {high:,}"


def _readings() -> List[str]:
    rows = [f"{'CONDITION':<22}{'TIP-RING OHMS':<22}{'TO GROUND OHMS':<22}",
            RULE]
    for code in REAL_FAULTS + ['ROH']:
        fault = FAULTS[code]
        rows.append(f"{code:<22}{_range(fault.tip_ring_ohms):<22}"
                    f"{_range(fault.to_ground_ohms):<22}")
        rows.append(f"    {fault.mlt_signature}")
    rows.extend([
        RULE,
        "",
        "HOW TO APPLY",
        "  1. Read tip-ring, tip-ground and ring-ground separately. Which one",
        "     is low says which table row to start from.",
        "  2. Foreign voltage with no battery on the pair is foreign EMF or a",
        "     cross; then the resistances pick between them.",
        "  3. A loop that reads clean everywhere is not a loop fault: sheet",
        "     660-003.",
        "  4. Capacitance gives the distance to an open: sheet 660-002.",
        "",
        f"A loop of 18 kft or less is designed to {RESISTANCE_DESIGN_LIMIT_OHMS}"
        " ohms, nonloaded;",
        f"18 to 24 kft to {LOADED_DESIGN_LIMIT_OHMS} ohms with H88 loading. A "
        f"coin station needs",
        f"{COIN_STATION_CURRENT_MA} mA.",
    ])
    return rows


def _distance() -> List[str]:
    rows = [f"{'CAPACITANCE':<16}{'MILES':<12}{'KILOFEET':<12}", RULE]
    for microfarads in (0.05, 0.10, 0.20, 0.30):
        miles = distance_to_open(microfarads)
        rows.append(f"{microfarads:<16.2f}{miles:<12.2f}"
                    f"{round(miles * 5.28, 1):<12}")
    rows.extend([
        RULE,
        "",
        f"Local exchange cable is {CABLE_UF_PER_MILE} microfarads to the "
        "mile, so",
        "  miles = capacitance / " + str(CABLE_UF_PER_MILE),
        "",
        "HOW TO APPLY",
        "  Only on a pair that reads open. An open reads short: the reading",
        "  stops at the break, so the distance is to the fault and not to the",
        "  station. Send the crew to that distance from the office.",
    ])
    return rows


def _clean() -> List[str]:
    rows = [f"{'CONDITION':<12}{'WHAT SEPARATES IT'}", RULE]
    rows.extend([
        f"{'CO_EQUIP':<12}Line equipment, line link or a jumper on the frame.",
        f"{'':<12}The cross-connect record shows what is wrong.",
        f"{'FCG':<12}The office test fails and the loop is clean to the frame.",
        f"{'':<12}The cross-connect record is in order.",
        f"{'NONE':<12}Nothing out of limits, and nothing on the record.",
        f"{'':<12}It may have cleared itself, or it may be hiding.",
        RULE,
        "",
        "HOW TO APPLY",
        "  mlt cannot tell these three apart: every reading is inside limits.",
        "  Look the line up on the frame before measuring it again:",
        "",
        "      cosmos jumper <telephone number>",
        "",
        "  A record that does not agree with the plant is CO_EQUIP, and the",
        "  remedy is on the frame and not in the street. A record in order",
        "  leaves FCG or no trouble. You need the frame sign-off for cosmos",
        "  (qual).",
    ])
    return rows


def _who() -> List[str]:
    rows = [f"{'CONDITION':<14}{'SEND':<26}{'TYPICAL REPAIR MINUTES'}", RULE]
    for code in REAL_FAULTS + ['ROH', 'NONE']:
        fault = FAULTS[code]
        low, high = fault.typical_minutes
        rows.append(f"{code:<14}{fault.dispatch:<26}{low} - {high}")
    rows.extend([
        RULE,
        "",
        "HOW TO APPLY",
        "  The condition says where the trouble is, and where it is says who",
        "  goes: the loop is not the office, and the office is not the",
        "  station. 'report forces' lists the crews. A crew sent to the wrong",
        "  place finds nothing and the trip is charged against the",
        "  commitment.",
        "  A receiver off hook is the customer's to put back. Nobody is",
        "  sent: call them.",
    ])
    return rows


def _customer_says() -> List[str]:
    heard: Dict[str, List[str]] = {}
    for code, symptoms in REPORT_SYMPTOMS.items():
        for symptom in symptoms:
            heard.setdefault(symptom, []).append(code)
    rows = [f"{'THE CUSTOMER SAYS':<34}{'IT MAY BE'}", RULE]
    for symptom in sorted(heard):
        rows.append(f"{symptom:<34}{', '.join(sorted(heard[symptom]))}")
    rows.extend([
        RULE,
        "",
        "HOW TO APPLY",
        "  The wording on a card is not always a row in this table. A",
        "  customer says what they noticed, and one complaint fits several",
        "  conditions. Narrow it with 'report callback', which costs a few",
        "  minutes of the commitment, then measure. The pair has the last",
        "  word: close out the condition you found and not the one that was",
        "  described.",
        "  Calls that do not complete are the one the words cannot settle:",
        "  busy and reorder are the same two tones at different cadences.",
    ])
    return rows


def _closing() -> List[str]:
    rows = [f"{'CODE':<8}{'MEANING':<24}{'USE WHEN'}", RULE,
            f"{'5':<8}{'Trouble found':<24}You found a condition and cleared it.",
            f"{'':<8}{'':<24}Name the condition: report close <n> 5 <CODE>.",
            f"{'8':<8}{'No trouble found':<24}Nothing was there to clear.",
            RULE,
            "",
            "CONDITION CODES",
            ]
    for code in REAL_FAULTS + ['ROH']:
        rows.append(f"  {code:<10}{FAULTS[code].name}")
    rows.extend([
        "  No trouble found is code 8, not a condition code.",
        "",
        "HOW TO APPLY",
        "  A faulty line closed 8 may call back: that repeat is what the",
        "  simulation counts against you. Close 8 only when the loop reads",
        "  clean and the frame record is in order.",
    ])
    return rows


SHEETS: Dict[str, Sheet] = {sheet.number: sheet for sheet in (
    Sheet('620-001', 'Who to send for a condition',
          [('Which crew clears which condition', OWN),
           ('Typical repair minutes', OWN)],
          _who),
    Sheet('660-001', 'Reading a mechanised loop test (mlt)',
          [('Resistance ranges for each condition', OWN),
           ('Foreign voltage with no battery on the pair read as foreign EMF '
            'or a cross', OWN),
           ('1300 and 1500 ohm design limits and their length bands',
            SOURCED + ': Engineering and Operations in the Bell System'),
           ('Coin station current', SOURCED
            + ': Engineering and Operations in the Bell System')],
          _readings),
    Sheet('660-002', 'Distance to an open from capacitance',
          [('Cable capacitance per mile', SOURCED
            + ': Telecommunications Transmission Engineering, Vol. 2'),
           ('That an open reads short, the reading stopping at the break',
            OWN + ' model of the capacitance measurement')],
          _distance),
    Sheet('660-003', 'A loop that reads clean',
          [('Which conditions read clean', OWN),
           ('That a frame trouble shows on the cross-connect record', OWN)],
          _clean),
    Sheet('660-004', 'What the customer says, and what it may be',
          [('The complaint wording', OWN),
           ('The pairing of wording and condition', OWN),
           ('Busy and reorder as the same two tones at different cadences',
            OWN + ': 480 and 620 Hz, as docs/changelog.md has it; no '
            'source was consulted')],
          _customer_says),
    Sheet('660-005', 'Closing out a report',
          [('Codes 5 and 8', SOURCED
            + ': Engineering and Operations in the Bell System, 16.4'),
           ('Judging a close against the line\'s real condition', OWN),
           ('A repeat report counting against the closer', OWN)],
          _closing),
)}


def render(number: str) -> str:
    """
    Render one sheet as the text of its file.

    Args:
        number: A key of SHEETS

    Returns:
        The sheet: a header that says the number is the simulation's own and
        where each figure comes from, then the table
    """
    sheet = SHEETS[number]
    lines = [
        f"BELL SYSTEM PRACTICE (simulation)            SHEET {sheet.number}",
        sheet.title.upper(),
        '=' * 72,
        "NUMBER",
    ]
    lines.extend(f"  {line}" for line in _wrap(NUMBER_NOTICE))
    lines.extend(['', "FIGURES ON THIS SHEET"])
    for what, source in sheet.basis:
        lines.append(f"  {what}")
        lines.extend(f"      {line}" for line in _wrap(source + '.', 64))
    lines.extend(['', '=' * 72])
    lines.extend(sheet.body())
    return '\n'.join(line.rstrip() for line in lines) + '\n'


def search(topic: str) -> List[Sheet]:
    """
    Find the sheets that are about a topic.

    Args:
        topic: Words to look for; a sheet matches when every one of them is
            in its number, its title or its text

    Returns:
        The matching sheets, in binder order
    """
    words = topic.lower().split()
    found = []
    for number in sorted(SHEETS):
        sheet = SHEETS[number]
        text = f"{number} {sheet.title} {render(number)}".lower()
        if all(word in text for word in words):
            found.append(sheet)
    return found


def index() -> str:
    """Render the binder's contents, which is the file called index."""
    lines = ["PRACTICES BINDER", '=' * 72,
             *(f"  {line}" for line in _wrap(NUMBER_NOTICE)), '']
    for number in sorted(SHEETS):
        lines.append(f"  {number}  {SHEETS[number].title}")
    lines.extend(['', "Read a sheet with cat. They are tables: find the row "
                      "your reading is in."])
    return '\n'.join(lines) + '\n'


def _wrap(text: str, width: int = 68) -> List[str]:
    """Break a paragraph to a measure."""
    words, lines, current = text.split(), [], ''
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines
