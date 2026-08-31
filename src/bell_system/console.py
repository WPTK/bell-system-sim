"""
Terminal output primitives.

A single place for the display layer, kept apart from the simulation logic.
At present it only clears the screen, but writing the control sequence here
rather than shelling out to ``clear`` removes three subprocess launches, works
where the external binary is absent, and gives later terminal-fidelity work
(baud pacing, column discipline) somewhere obvious to live.
"""

import sys

# ANSI: erase the entire display, then home the cursor.
CLEAR_SCREEN = '\033[2J\033[H'


def clear_screen(stream=None) -> None:
    """
    Clear the terminal screen.

    Args:
        stream: Destination for the control sequence; defaults to stdout.
    """
    target = stream if stream is not None else sys.stdout
    target.write(CLEAR_SCREEN)
    target.flush()
