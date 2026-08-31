"""
COMMON LANGUAGE Location Identification codes.

Every Bell System location carried a CLLI code, and every record that referred
to a place - trunk designations, circuit layout records, trouble reports, test
requests - referred to it by that code. The simulation previously identified
offices with ad-hoc strings like NYC-CO-14 and 1ESS-NYC-001, which is the one
thing a craftsperson of the period would never have written.

Structure, from the message-trunk designation format in Telecommunications
Transmission Engineering Volume 3 (1977), where the location identification
field is eleven characters, the first six strictly alphabetic:

    1-4   Geographical    place, town or locality      alphabetic
    5-6   Geopolitical    state, province or country   alphabetic
    7-8   Network site    building within that place   alphanumeric
    9-11  Network entity  equipment or work centre     alphanumeric

The first eight characters identify a building; all eleven identify a
particular machine or entity inside it. Records needing only the building
carry the eight-character form.

A caution recorded rather than hidden: Engineering and Operations in the Bell
System (1984) twice describes CLLI as a ten-character code. The 1977 field
layout, and every later description, give eleven. Eleven is used here.

In this period COMMON LANGUAGE was administered by AT&T and published in the
Bell System Practices, Division 795 - specifically BSP 795-100-100 Issue 5,
October 1982. Administration passed to Bellcore only at divestiture in
January 1984, so neither Bellcore nor the later BR 751 practices belong in a
simulation set before then.

The abbreviation rule that turns a place name into its four-character code
lives in that practice, which was not available. Generated place codes here
are therefore plausible rather than authoritative, and the module says so
rather than implying otherwise.
"""

import re
from typing import Dict, NamedTuple, Optional

CLLI_LENGTH = 11
BUILDING_LENGTH = 8

# Positions 1-6 are alphabetic; 7-11 may be alphanumeric.
CLLI_PATTERN = re.compile(r'^[A-Z]{6}[A-Z0-9]{5}$')
BUILDING_PATTERN = re.compile(r'^[A-Z]{6}[A-Z0-9]{2}$')


class Clli(NamedTuple):
    """A parsed COMMON LANGUAGE location identifier."""

    place: str
    state: str
    building: str
    entity: str

    def __str__(self) -> str:
        return f'{self.place}{self.state}{self.building}{self.entity}'

    def building_code(self) -> str:
        """Return the eight-character form identifying the building alone."""
        return f'{self.place}{self.state}{self.building}'


class EntityType(NamedTuple):
    """A network entity code and the equipment it denotes."""

    prefix: str
    description: str
    switch_types: tuple


# Switching entity codes. The two letters name the control or technology and
# the final character distinguishes machines in the same building.
SWITCHING_ENTITIES: Dict[str, EntityType] = {
    'MG': EntityType('MG', 'Marker group', ('XB1', 'XB5', 'XB4', 'XB4A')),
    'SG': EntityType('SG', 'Step group', ('SXS',)),
    'CG': EntityType('CG', 'Control group', ('1ESS', '1AESS', '2ESS', '2BESS', '3ESS')),
    'DS': EntityType('DS', 'Digital switch', ('5ESS',)),
}

# Final characters reserved for particular kinds of entity.
RESERVED_FINAL: Dict[str, str] = {
    'T': 'Toll or tandem switching entity',
    'B': 'Board - operator and switchboard positions, including 0 and 411',
    'D': 'Miscellaneous termination entity',
}

# Letters not used in entity codes, being too easily confused when written or
# read over an order wire.
UNUSED_LETTERS = frozenset('IOUWY')

# Real codes, each verifiable against published switching rosters. These are
# recorded rather than generated, and are the only codes here asserted to have
# denoted an actual office.
ATTESTED_CLLI: Dict[str, str] = {
    'CHCGILCL57T': 'Chicago 7, Illinois - the first No. 4 ESS, cut January 1976',
    'DLLSTXTA02T': 'Dallas Taylor, Texas - No. 4A Crossbar used as a local area tandem',
    'SNFCCA2143T': 'San Francisco, California - Pacific Bell toll tandem',
}


# The office data carries full state names; CLLI wants the two-character
# geopolitical code.
STATE_CODES: Dict[str, str] = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT',
    'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL',
    'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL',
    'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY',
    'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
    'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
    'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
    'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY',
}


def parse(code: str) -> Optional[Clli]:
    """
    Parse an eleven-character CLLI code.

    Args:
        code: The code to parse, in any case

    Returns:
        The parsed code, or None if it is not well formed
    """
    candidate = code.strip().upper()
    if not CLLI_PATTERN.match(candidate):
        return None
    return Clli(candidate[0:4], candidate[4:6], candidate[6:8], candidate[8:11])


def is_valid(code: str) -> bool:
    """Return whether a string is a well-formed CLLI code."""
    return parse(code) is not None


def is_valid_building(code: str) -> bool:
    """Return whether a string is a well-formed eight-character building code."""
    return bool(BUILDING_PATTERN.match(code.strip().upper()))


def entity_for_switch(switch_type: str, is_toll: bool = False,
                      ordinal: int = 0) -> str:
    """
    Return the network entity code for a switching machine.

    Toll and tandem entities take a numeric pair and a final T. Local machines
    take the two letters naming their control technology and a digit
    distinguishing machines in the same building.

    Args:
        switch_type: Switching system code, such as 1ESS or XB5
        is_toll: Whether the machine serves toll or tandem traffic
        ordinal: Distinguishes several machines in one building

    Returns:
        A three-character entity code
    """
    if is_toll:
        return f'{ordinal % 100:02d}T'
    for entity in SWITCHING_ENTITIES.values():
        if switch_type in entity.switch_types:
            return f'{entity.prefix}{ordinal % 10}'
    # No attested entity prefix was found for machines outside the table -
    # panel among them - so fall back to the miscellaneous termination code
    # rather than claiming a technology prefix that may be wrong.
    return f'{ordinal % 10}0D'


def describe_entity(entity: str) -> str:
    """Describe what an entity code denotes."""
    entity = entity.upper()
    if len(entity) == 3 and entity[2] in RESERVED_FINAL and entity[:2].isdigit():
        return RESERVED_FINAL[entity[2]]
    known = SWITCHING_ENTITIES.get(entity[:2])
    if known is not None:
        return f'{known.description} {entity[2]}'
    if entity[-1] in RESERVED_FINAL:
        return RESERVED_FINAL[entity[-1]]
    return 'Entity code'


# Place codes attested in published switching rosters and Common Language
# descriptions. Large cities carried several, one per borough or section, so
# these are the codes for the principal downtown wire centres. Anything not
# listed here falls through to the derivation below and is plausible only.
KNOWN_PLACE_CODES: Dict[str, str] = {
    'NEW YORK': 'NYCM',
    'MANHATTAN': 'NYCM',
    'BROOKLYN': 'BRKL',
    'CHICAGO': 'CHCG',
    'NEWARK': 'NWRK',
    'SAN FRANCISCO': 'SNFC',
    'DALLAS': 'DLLS',
    'WASHINGTON': 'WASH',
}


def place_code(city: str) -> str:
    """
    Derive a four-character place code from a city name.

    Places with an attested code use it. For anything else the real
    abbreviation rule is published in BSP 795-100-100, which was not
    available, so this reproduces only the conventions observable in
    attested codes: letters only, upper case, vowels dropped from the interior
    of a single-word name, and short names padded by repeating the final
    letter. A code produced here is plausible, not authoritative.

    Args:
        city: The place name

    Returns:
        A four-character alphabetic place code
    """
    letters = re.sub(r'[^A-Za-z ]', '', city).upper().strip()
    if not letters:
        return 'XXXX'

    attested = KNOWN_PLACE_CODES.get(letters)
    if attested is not None:
        return attested

    words = letters.split()
    if len(words) > 1:
        # Multi-word names take leading letters from each word.
        code = ''.join(word[0] for word in words)
        if len(code) < 4:
            code += words[-1][1:]
    else:
        word = words[0]
        # Keep the first letter, then drop interior vowels, as CHCG from
        # Chicago and NWRK from Newark do.
        code = word[0] + re.sub(r'[AEIOU]', '', word[1:])
        if len(code) < 4:
            code = word

    code = code[:4]
    while len(code) < 4:
        code += code[-1]
    return code


def build(city: str, state: str, building: str = 'CO',
          entity: str = 'MG0') -> Optional[Clli]:
    """
    Build a CLLI code for a place.

    Args:
        city: Place name, abbreviated to four characters
        state: Two-character geopolitical code
        building: Two-character network site code
        entity: Three-character network entity code

    Returns:
        The code, or None if the parts do not form a valid one
    """
    candidate = (
        f'{place_code(city)}'
        f'{state.upper()[:2]:X<2}'
        f'{building.upper()[:2]:0<2}'
        f'{entity.upper()[:3]:0<3}'
    )
    return parse(candidate)
