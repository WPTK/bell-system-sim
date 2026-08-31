"""
Bell System UNIX V7 Terminal Simulation
=======================================

A recreation of AT&T Bell System internal operations workstations from the
period 1978-1983.

This package provides a terminal-based simulation of Bell System operations,
featuring 12 operational roles, period-accurate commands, and Bell System
operational workflows.
"""

__version__ = "2.1.0"
__author__ = "Bell System Operations Simulation Project"
__license__ = "MIT"

from .simple_terminal import SimpleTerminal
from .terminal import BellSystemTerminal
from .tutorial import BellSystemTutorial

__all__ = [
    'BellSystemTerminal',
    'SimpleTerminal',
    'BellSystemTutorial',
]
