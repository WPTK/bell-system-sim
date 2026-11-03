"""
The generators the board's extras are drawn from.

A case, a leak and the toll counts are decided from the career and the tour,
each from a generator of its own so that deciding them takes nothing from
the one the board is dealt from. The career's seed is what makes one career's
tours differ from another's: with the tour alone, every career was dealt the
same dig on the same tour.
"""

import os
import random
import secrets
from typing import Optional

# Set in the environment to give every new career the same seed, for a test
# or a calibration run that needs the same tours twice.
ENVIRONMENT = 'BELL_SYSTEM_SEED'


def new_seed() -> str:
    """A seed for a career that has none: the environment's, else a draw."""
    fixed: Optional[str] = os.environ.get(ENVIRONMENT)
    return fixed if fixed is not None else secrets.token_hex(4)


def stream(seed: str, name: str, tour: int) -> random.Random:
    """
    The generator for one thing on one tour of one career.

    An empty seed is the old key, so a career that kept none is dealt what
    it always was.
    """
    return random.Random(f"{name}:{seed}:{tour}" if seed
                         else f"{name}:{tour}")
