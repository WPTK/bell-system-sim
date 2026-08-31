"""Allow the simulation to be launched with ``python -m bell_system``."""

import sys

from .cli import main

if __name__ == '__main__':
    sys.exit(main())
