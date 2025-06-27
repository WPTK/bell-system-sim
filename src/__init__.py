"""
Bell System UNIX V7 Terminal Simulation
=======================================

A historically accurate recreation of AT&T Bell System internal operations
workstations from the transformative period of 1978-1983.

This package provides an authentic terminal-based experience of Bell System
operations, featuring 12 operational roles, 50+ period-accurate commands,
and comprehensive Bell System workflows.
"""

__version__ = "2.0.0"
__author__ = "Bell System Operations Simulation Project"
__license__ = "MIT"

from .bell import BellSystemTerminal
from .unix_terminal import BellSystemTerminal as SimpleBellSystemTerminal
from .bell_system_tutorial import BellSystemTutorial

__all__ = [
    'BellSystemTerminal',
    'SimpleBellSystemTerminal', 
    'BellSystemTutorial'
]