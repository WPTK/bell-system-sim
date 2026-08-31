"""
User-adjustable simulation settings.

The simulation aims at historical accuracy first, but some accurate behaviours
are less playable on a modern terminal than on a Teletype. Rather than pick one
and impose it, those choices live here as settings with period-accurate
defaults, so a player can trade fidelity for comfort deliberately.

Options are declared in ``OPTIONS`` as data. The settings screen, validation,
persistence and the manual page all read that one declaration, so adding an
option means adding a single entry here.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

SETTINGS_FILENAME = 'settings.json'

# The simulated shift begins Monday 14 November 1983 at 08:00. The date is
# inside the 1978-1983 window the simulation depicts, falls on a Monday, and
# sits in standard time - which is why timestamps throughout the simulation
# can legitimately read EST.
DEFAULT_EPOCH = '1983-11-14'
EPOCH_HOUR = 8
EPOCH_MINUTE = 0


class Option:
    """One user-adjustable setting."""

    def __init__(self, key: str, default: str, choices: Optional[List[str]],
                 summary: str, detail: str = '', accurate: Optional[str] = None):
        self.key = key
        self.default = default
        self.choices = choices
        self.summary = summary
        self.detail = detail
        # The value matching period behaviour, when one of the choices does.
        self.accurate = accurate

    def validate(self, value: str) -> str:
        """
        Check a proposed value and return it normalised.

        Raises:
            ValueError: if the value is not permitted for this option
        """
        if self.choices is None:
            return self._validate_free(value)
        lowered = value.lower()
        for choice in self.choices:
            if choice.lower() == lowered:
                return choice
        raise ValueError(
            f"'{value}' is not valid for {self.key}. "
            f"Choose one of: {', '.join(self.choices)}"
        )

    def _validate_free(self, value: str) -> str:
        """Validate an option with no fixed choice list."""
        if self.key == 'date.epoch':
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise ValueError(
                    f"'{value}' is not a date. Use YYYY-MM-DD, for example {DEFAULT_EPOCH}."
                )
            return value
        return value


OPTIONS: List[Option] = [
    Option(
        'date.source', 'simulated', ['simulated', 'real'],
        'Where the clock reads from',
        'simulated runs the 1983 shift clock; real shows your own system time.',
        accurate='simulated',
    ),
    Option(
        'date.epoch', DEFAULT_EPOCH, None,
        'Date the simulated shift begins',
        'YYYY-MM-DD. The shift starts at 08:00 and runs forward in real time.',
    ),
    Option(
        'date.format', 'v7', ['v7', 'iso', 'us'],
        'Date layout',
        'v7 is UNIX date(1) order (Mon Nov 14 1983); iso is YYYY-MM-DD; '
        'us is MM-DD-YYYY.',
        accurate='v7',
    ),
    Option(
        'date.clock', '24', ['24', '12'],
        'Clock convention',
        '24-hour was standard in Bell System operational records.',
        accurate='24',
    ),
    Option(
        'date.seconds', 'on', ['on', 'off'],
        'Show seconds in timestamps',
        'off shortens every timestamp to hours and minutes.',
    ),
    Option(
        'display.charset', 'ascii', ['ascii', 'unicode'],
        'Character set for output',
        'ascii restricts output to 7-bit ASCII as period terminals required; '
        'unicode permits block and box-drawing glyphs on a modern terminal.',
        accurate='ascii',
    ),
    Option(
        'display.prompt', 'v7', ['v7', 'verbose'],
        'Shell prompt style',
        'v7 is the bare Bourne shell prompt ($, or # for root); '
        'verbose adds user, host and directory.',
        accurate='v7',
    ),
    Option(
        'game.difficulty', 'fun', ['fun', 'craft'],
        'How hard the work is',
        "fun is Fun Simulation: reports can be closed without measuring, "
        "qualification comes quickly and a wrong call costs little. craft is "
        "I Hate Myself: measure before you close, repeat reports come back on "
        "your index, commitments are counted, and qualification is slow. "
        "craft is the closer depiction of the job; it carries no accuracy "
        "marking here because difficulty governs how forgiving the "
        "simulation is, not how it renders 1983.",
    ),
    Option(
        'game.ambience', 'on', ['on', 'off'],
        'Traffic from the other craft on the system',
        'on lets the switching control centre, the repair service bureau and '
        'the rest of the craft interrupt you on write(1), mail(1), the order '
        'wire and the maintenance teletype, at the rate the difficulty sets. '
        'off leaves the terminal to you.',
    ),
    Option(
        'display.pacing', '300', ['off', '110', '300', '1200'],
        'Print output at a terminal speed',
        'A teleprinter printed one character at a time and you watched it '
        'happen. A Teletype Model 33 ran at 110 baud, ten characters a '
        'second; the Model 43 this position has is switchable to 110 or 300, '
        'ten or thirty characters a second, and 300 is what it is strapped '
        'for. 1200 is a later CRT. off prints instantly, which no terminal '
        'of the period did. Ctrl-C stops a listing, as it did then. Pacing '
        'applies to a terminal and not to a pipe, because a program that '
        'slowed down output nobody was watching would be a strange program.',
        accurate='300',
    ),
    Option(
        'display.log_console', 'off', ['off', 'on'],
        'Print diagnostic log records to the terminal',
        'on interleaves Python logging output with simulation output; '
        'useful when debugging, but nothing a 1983 terminal would emit.',
        accurate='off',
    ),
]

OPTIONS_BY_KEY: Dict[str, Option] = {option.key: option for option in OPTIONS}


class Settings:
    """
    The active settings for a session, persisted between runs.

    Values are stored as strings so that what is written to disk is exactly
    what the settings screen displays and what a player types.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._values: Dict[str, str] = {
            option.key: option.default for option in OPTIONS
        }
        if path:
            self.load()

    # -- access ---------------------------------------------------------

    def get(self, key: str) -> str:
        """Return the current value of an option."""
        if key not in OPTIONS_BY_KEY:
            raise KeyError(key)
        return self._values[key]

    def is_on(self, key: str) -> bool:
        """Return True when an on/off option is on."""
        return self.get(key) == 'on'

    def set(self, key: str, value: str) -> str:
        """
        Change an option after validating the value.

        Returns:
            The normalised value that was stored

        Raises:
            KeyError: if the option does not exist
            ValueError: if the value is not permitted
        """
        if key not in OPTIONS_BY_KEY:
            raise KeyError(key)
        normalised = OPTIONS_BY_KEY[key].validate(value)
        self._values[key] = normalised
        self.save()
        return normalised

    def reset(self, key: Optional[str] = None) -> None:
        """Restore one option, or all of them, to the period-accurate default."""
        if key is None:
            self._values = {option.key: option.default for option in OPTIONS}
        else:
            if key not in OPTIONS_BY_KEY:
                raise KeyError(key)
            self._values[key] = OPTIONS_BY_KEY[key].default
        self.save()

    def as_dict(self) -> Dict[str, str]:
        """Return a copy of every current value."""
        return dict(self._values)

    def deviations(self) -> List[str]:
        """Return the keys whose value departs from period-accurate behaviour."""
        return [
            option.key for option in OPTIONS
            if option.accurate is not None and self._values[option.key] != option.accurate
        ]

    # -- persistence ----------------------------------------------------

    def load(self) -> None:
        """
        Read stored settings, ignoring anything unreadable or unrecognised.

        A corrupt or hand-edited file must never stop the simulation starting,
        so unknown keys and invalid values fall back to their defaults.
        """
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r') as handle:
                stored = json.load(handle)
        except (OSError, ValueError):
            return
        if not isinstance(stored, dict):
            return
        for key, value in stored.items():
            option = OPTIONS_BY_KEY.get(key)
            if option is None or not isinstance(value, str):
                continue
            try:
                self._values[key] = option.validate(value)
            except ValueError:
                continue

    def save(self) -> None:
        """Write the current settings, ignoring a read-only filesystem."""
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as handle:
                json.dump(self._values, handle, indent=2, sort_keys=True)
                handle.write('\n')
        except OSError:
            return

    # -- derived values -------------------------------------------------

    def epoch(self) -> datetime:
        """Return the datetime at which the simulated shift begins."""
        try:
            base = datetime.strptime(self.get('date.epoch'), '%Y-%m-%d')
        except ValueError:
            base = datetime.strptime(DEFAULT_EPOCH, '%Y-%m-%d')
        return base.replace(hour=EPOCH_HOUR, minute=EPOCH_MINUTE)


def state_dir() -> str:
    """
    Return the per-user directory for logs and command history.

    Honours ``BELL_SYSTEM_HOME`` when set, otherwise follows the XDG state
    convention. Writing here rather than the current working directory keeps
    an installed ``bell-system`` from littering whatever directory it is run
    from. The directory is created if it does not exist.
    """
    override = os.environ.get('BELL_SYSTEM_HOME')
    if override:
        path = override
    else:
        base = os.environ.get('XDG_STATE_HOME') or os.path.join(
            os.path.expanduser('~'), '.local', 'state'
        )
        path = os.path.join(base, 'bell-system')
    os.makedirs(path, exist_ok=True)
    return path


def settings_path(state_directory: str) -> str:
    """Return the settings file path inside a state directory."""
    return os.path.join(state_directory, SETTINGS_FILENAME)


def describe(value: Any) -> str:
    """Render a value for display in the settings screen."""
    return str(value)
