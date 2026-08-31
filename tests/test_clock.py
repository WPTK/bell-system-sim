"""
Tests for the simulation clock.

The simulation previously printed the real wall-clock date in a setting dated
1978-1983 — the first command a player typed broke the period. Every timestamp
now comes from here.
"""

from datetime import datetime, timedelta

import pytest

from bell_system.clock import SimClock
from bell_system.settings import Settings


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def clock(settings):
    """A clock pinned to the session start, so tests are deterministic."""
    return SimClock(settings, started_at=datetime.now())


def test_simulated_time_is_in_the_period(clock):
    """The default clock reports 1983, not the host's year."""
    assert clock.now().year == 1983
    assert clock.now().year != datetime.now().year


def test_simulated_shift_starts_at_the_epoch(clock):
    now = clock.now()
    assert now.month == 11 and now.day == 14
    assert now.hour == 8


def test_shift_advances_with_real_time(settings):
    """Twenty minutes of play is twenty minutes of the shift."""
    started = datetime.now() - timedelta(minutes=20)
    clock = SimClock(settings, started_at=started)
    elapsed = clock.now() - settings.epoch()
    assert timedelta(minutes=19) < elapsed < timedelta(minutes=21)


def test_real_source_reports_the_host_clock(settings):
    settings.set('date.source', 'real')
    clock = SimClock(settings)
    assert clock.now().year == datetime.now().year


def test_changing_the_epoch_moves_the_shift(settings):
    settings.set('date.epoch', '1978-06-01')
    clock = SimClock(settings)
    assert clock.now().year == 1978
    assert clock.now().month == 6


class TestFormats:
    """The layouts a player can choose between."""

    def test_v7_layout_matches_unix_date(self, clock):
        """Seventh Edition date(1) printed: Mon Nov 14 08:00:00 EST 1983."""
        assert clock.date_command() == 'Mon Nov 14 08:00:00 EST 1983'

    def test_iso_layout(self, settings, clock):
        settings.set('date.format', 'iso')
        assert clock.date_command().startswith('1983-11-14 08:00:00')

    def test_us_layout(self, settings, clock):
        settings.set('date.format', 'us')
        assert clock.date_command().startswith('11-14-1983 08:00:00')

    def test_twelve_hour_clock(self, settings, clock):
        settings.set('date.clock', '12')
        rendered = clock.date_command()
        assert '8:00:00 AM' in rendered
        assert '08:00:00' not in rendered

    def test_twenty_four_hour_clock(self, settings, clock):
        settings.set('date.clock', '24')
        rendered = clock.date_command()
        assert '08:00:00' in rendered
        assert 'AM' not in rendered

    def test_seconds_can_be_suppressed(self, settings, clock):
        settings.set('date.seconds', 'off')
        rendered = clock.date_command()
        assert '08:00' in rendered
        assert '08:00:00' not in rendered

    def test_seconds_and_twelve_hour_combine(self, settings, clock):
        settings.set('date.clock', '12')
        settings.set('date.seconds', 'off')
        assert '8:00 AM' in clock.date_command()

    @pytest.mark.parametrize('layout', ['v7', 'iso', 'us'])
    @pytest.mark.parametrize('hours', ['12', '24'])
    @pytest.mark.parametrize('seconds', ['on', 'off'])
    def test_every_combination_renders(self, settings, clock, layout, hours, seconds):
        """No combination of the format settings may produce empty output."""
        settings.set('date.format', layout)
        settings.set('date.clock', hours)
        settings.set('date.seconds', seconds)
        for rendered in (clock.date_command(), clock.timestamp(),
                         clock.date(), clock.time(), clock.log_stamp()):
            assert rendered.strip()
            assert all(ord(character) <= 0x7E for character in rendered)

    def test_timestamps_are_dated_in_the_period(self, clock):
        assert '1983' in clock.timestamp()

    def test_est_is_correct_for_the_default_epoch(self, clock):
        """
        November is standard time, so the EST label the simulation prints
        throughout is accurate rather than merely conventional.
        """
        assert 'EST' in clock.date_command()
        assert clock.now().month == 11
