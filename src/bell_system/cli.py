#!/usr/bin/env python3
"""
Bell System UNIX V7 Terminal Simulation - Command Line Interface
===============================================================

The single entry point for the simulation. Installed as the ``bell-system``
console script and also runnable as ``python -m bell_system``.
"""

import argparse
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog='bell-system',
        description='Bell System UNIX V7 Terminal Simulation (1978-1983)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bell-system                 Start the interactive simulation
  bell-system --role 1        Start as UNIX Systems Operator
  bell-system --simple        Use the simplified four-role interface
""",
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'Bell System UNIX V7 Terminal Simulation v{__version__}',
    )
    parser.add_argument(
        '--role',
        type=int,
        choices=range(1, 13),
        metavar='N',
        help='start with role N (1-12), skipping the selection menu',
    )
    parser.add_argument(
        '--simple',
        action='store_true',
        help='use the simplified four-role interface',
    )
    return parser


def main(argv=None) -> int:
    """
    Run the Bell System terminal simulation.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit status.
    """
    args = build_parser().parse_args(argv)

    try:
        if args.simple:
            from .simple_terminal import SimpleTerminal
            SimpleTerminal().run()
        else:
            from .terminal import BellSystemTerminal
            BellSystemTerminal().run(role=args.role)
    except KeyboardInterrupt:
        print("\nSimulation terminated by user.")
        return 0
    except EOFError:
        print("\nSession terminated.")
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
