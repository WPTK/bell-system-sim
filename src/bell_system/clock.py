"""
The simulation clock.

Every timestamp the simulation emits comes from here rather than from
``datetime.now()`` directly. In its default configuration the clock reports the
1983 shift the simulation depicts; real elapsed time advances it, so a session
that runs for twenty minutes sees twenty minutes pass on the shift.

Formatting also lives here, because how a timestamp reads is a user setting:
period-accurate UNIX ``date(1)`` order by default, with ISO and US layouts and
a 12-hour clock available for readability.
"""

from datetime import datetime, timedelta
from typing import Optional

from .settings import Settings

# Timestamps carry EST because the default epoch sits in November, inside
# standard time. A user who moves the epoch into summer is choosing that.
TIMEZONE_LABEL = 'EST'


class SimClock:
    """
    Reports the current simulated time and formats it for display.

    Args:
        settings: The settings that decide the source, epoch and layout
        started_at: Real time the session began; defaults to now
    """

    def __init__(self, settings: Settings, started_at: Optional[datetime] = None):
        self._settings = settings
        self._session_start = started_at or datetime.now()

    # -- the time itself ------------------------------------------------

    def now(self) -> datetime:
        """
        Return the current simulated time.

        With ``date.source`` set to ``real`` this is the host clock. Otherwise
        it is the configured epoch advanced by however long the session has
        been running.
        """
        if self._settings.get('date.source') == 'real':
            return datetime.now()
        elapsed = datetime.now() - self._session_start
        return self._settings.epoch() + elapsed

    def elapsed(self) -> timedelta:
        """Return how long the session has been running."""
        return datetime.now() - self._session_start

    def reset_session(self) -> None:
        """Restart the shift from the epoch, used when the epoch changes."""
        self._session_start = datetime.now()

    # -- formatting -----------------------------------------------------

    def _time_format(self) -> str:
        """Build the strftime fragment for the time of day."""
        twelve_hour = self._settings.get('date.clock') == '12'
        seconds = self._settings.is_on('date.seconds')
        if twelve_hour:
            base = '%I:%M:%S' if seconds else '%I:%M'
            return base + ' %p'
        return '%H:%M:%S' if seconds else '%H:%M'

    def time(self, moment: Optional[datetime] = None) -> str:
        """Return the time of day, without a date."""
        moment = moment or self.now()
        rendered = moment.strftime(self._time_format())
        if self._settings.get('date.clock') == '12':
            # strftime pads the hour to two digits; 8:05 AM reads better.
            rendered = rendered.lstrip('0')
        return rendered

    def date(self, moment: Optional[datetime] = None) -> str:
        """Return the date, without a time of day."""
        moment = moment or self.now()
        layout = self._settings.get('date.format')
        if layout == 'iso':
            return moment.strftime('%Y-%m-%d')
        if layout == 'us':
            return moment.strftime('%m-%d-%Y')
        return moment.strftime('%B %d, %Y')

    def timestamp(self, moment: Optional[datetime] = None) -> str:
        """Return a full date and time, the usual form for report headers."""
        moment = moment or self.now()
        return f'{self.date(moment)} {self.time(moment)} {TIMEZONE_LABEL}'

    def date_command(self, moment: Optional[datetime] = None) -> str:
        """
        Render the output of the ``date`` command.

        In the default layout this is UNIX ``date(1)`` order, which is what a
        V7 system printed: ``Mon Nov 14 08:00:00 EST 1983``.
        """
        moment = moment or self.now()
        layout = self._settings.get('date.format')
        clock = self.time(moment)
        if layout == 'iso':
            return f'{moment.strftime("%Y-%m-%d")} {clock} {TIMEZONE_LABEL}'
        if layout == 'us':
            return f'{moment.strftime("%m-%d-%Y")} {clock} {TIMEZONE_LABEL}'
        return (
            f'{moment.strftime("%a %b %d")} {clock} '
            f'{TIMEZONE_LABEL} {moment.strftime("%Y")}'
        )

    def log_stamp(self, moment: Optional[datetime] = None) -> str:
        """Return a compact timestamp for ticket and event records."""
        moment = moment or self.now()
        return f'{self.time(moment)} {TIMEZONE_LABEL}'
