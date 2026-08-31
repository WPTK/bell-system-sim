"""
The operational screens, one module per subsystem.

``terminal.py`` grew to eleven thousand lines and two hundred and thirty
methods because every subsystem's screens were written into it. These modules
hold those screens, grouped by the part of the plant they belong to, and are
mixed into :class:`~bell_system.terminal.BellSystemTerminal`.

Mixins rather than composition, deliberately and for now. The screens read
session state - the clock, the settings, the trunk groups, the report desk -
that the terminal owns, and a mixin preserves that access unchanged while the
files are split, which keeps a large mechanical refactor verifiable against
the existing test suite rather than rewritten and hoped for.

Newer subsystems do it properly: :mod:`bell_system.lmos` and
:mod:`bell_system.special_services` own their state and take the terminal as
a collaborator. That is the shape these should reach one subsystem at a time,
and new work should follow those two rather than these.
"""
