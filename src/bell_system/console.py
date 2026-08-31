"""
Terminal output primitives.

A single place for the display layer, kept apart from the simulation logic.
Writing control sequences here rather than shelling out to ``clear`` removes
three subprocess launches and works where the external binary is absent.

This module also enforces the character set. Bell System terminals of the
period were 7-bit ASCII: a Teletype Model 43 or DATASPEED 40 could not print a
block glyph, a box-drawing rule or an emoji. Output therefore passes through a
transliteration table by default, which substitutes period-plausible ASCII.
A player who prefers the modern rendering can set ``display.charset`` to
``unicode`` and see the glyphs as written.
"""

import sys
from typing import Optional

# ANSI: erase the entire display, then home the cursor.
CLEAR_SCREEN = '\033[2J\033[H'

# Every non-ASCII character the simulation emits, mapped to a 7-bit
# equivalent. Bars and rules keep their visual weight; status marks become the
# words an operator would have read on paper.
ASCII_SUBSTITUTIONS = {
    '█': '#',      # FULL BLOCK, progress bars
    '░': '.',      # LIGHT SHADE, unfilled bar
    '═': '=',      # BOX DRAWINGS DOUBLE HORIZONTAL
    '║': '|',      # BOX DRAWINGS DOUBLE VERTICAL
    '╔': '+',      # BOX DRAWINGS DOUBLE DOWN AND RIGHT
    '╗': '+',      # BOX DRAWINGS DOUBLE DOWN AND LEFT
    '╚': '+',      # BOX DRAWINGS DOUBLE UP AND RIGHT
    '╝': '+',      # BOX DRAWINGS DOUBLE UP AND LEFT
    '•': '-',      # BULLET
    '±': '+/-',    # PLUS-MINUS SIGN
    '°': ' deg',   # DEGREE SIGN
    '×': 'x',      # MULTIPLICATION SIGN
    'μ': 'u',      # GREEK SMALL LETTER MU, as in microseconds
    '→': '->',     # RIGHTWARDS ARROW
    '↑': '^',      # UPWARDS ARROW
    '↓': 'v',      # DOWNWARDS ARROW
    '✓': 'OK',     # CHECK MARK
    '✅': '[OK]',   # WHITE HEAVY CHECK MARK
    '❌': '[XX]',   # CROSS MARK
    '⚠': '[!]',    # WARNING SIGN
    '⚡': '[!]',    # HIGH VOLTAGE SIGN
    'ℹ': '[i]',    # INFORMATION SOURCE
    '\U0001f527': '',   # WRENCH
    '\U0001f3af': '',   # DIRECT HIT
    '\U0001f4a1': '',   # ELECTRIC LIGHT BULB
    '\U0001f4cb': '',   # CLIPBOARD
    '\U0001f389': '',   # PARTY POPPER
}

_TRANSLATION = str.maketrans({
    ord(character): replacement
    for character, replacement in ASCII_SUBSTITUTIONS.items()
})


def to_ascii(text: str) -> str:
    """
    Render text as printable 7-bit ASCII.

    Known characters are substituted from the table; anything else outside
    printable ASCII is dropped rather than passed through, so output can be
    guaranteed printable on a period terminal.

    Args:
        text: The text to transliterate

    Returns:
        Text containing only printable ASCII, tab and newline
    """
    substituted = text.translate(_TRANSLATION)
    return ''.join(
        character for character in substituted
        if character in '\t\n\r' or 0x20 <= ord(character) <= 0x7E
    )


def render(text: str, charset: str = 'ascii') -> str:
    """
    Prepare text for display under the active character-set setting.

    Args:
        text: The text to render
        charset: ``ascii`` to transliterate, ``unicode`` to pass through

    Returns:
        The text as it should be written to the terminal
    """
    return text if charset == 'unicode' else to_ascii(text)


def clear_screen(stream=None) -> None:
    """
    Clear the terminal screen.

    Args:
        stream: Destination for the control sequence; defaults to stdout.
    """
    target = stream if stream is not None else sys.stdout
    target.write(CLEAR_SCREEN)
    target.flush()


def emit(text: str, charset: str = 'ascii', stream=None,
         end: str = '\n') -> None:
    """
    Write simulation output to the terminal under the active character set.

    Args:
        text: The text to display
        charset: ``ascii`` to transliterate, ``unicode`` to pass through
        stream: Destination; defaults to stdout
        end: Trailing string, as for ``print``
    """
    target = stream if stream is not None else sys.stdout
    target.write(render(text, charset) + end)


def non_ascii_characters(text: str) -> Optional[str]:
    """
    Return the distinct non-ASCII characters in text, or None if there are none.

    Used by the test suite to hold rendered output to the period character set.
    """
    found = sorted({character for character in text if ord(character) > 0x7E})
    return ''.join(found) if found else None
