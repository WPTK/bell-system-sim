"""
Tests for user-adjustable simulation settings.

Settings exist so historical accuracy and modern playability do not have to be
traded off globally. The defaults must therefore be the accurate ones, and a
value that departs from period behaviour must say so.
"""

import json

import pytest

from bell_system.settings import (
    DEFAULT_EPOCH,
    OPTIONS,
    OPTIONS_BY_KEY,
    Settings,
    settings_path,
)


def test_every_default_is_the_period_accurate_value():
    """
    Accuracy is the default everywhere it is defined.

    A player opts out of period behaviour deliberately; they never opt in.
    """
    for option in OPTIONS:
        if option.accurate is not None:
            assert option.default == option.accurate, option.key


def test_a_fresh_session_has_no_deviations():
    assert Settings().deviations() == []


def test_option_keys_are_unique():
    keys = [option.key for option in OPTIONS]
    assert len(keys) == len(set(keys))


def test_every_option_documents_itself():
    for option in OPTIONS:
        assert option.summary, option.key
        if option.choices is not None:
            assert option.default in option.choices, option.key


class TestValidation:
    def test_valid_value_is_accepted(self):
        settings = Settings()
        assert settings.set('date.format', 'iso') == 'iso'

    def test_value_is_case_insensitive(self):
        settings = Settings()
        assert settings.set('date.format', 'ISO') == 'iso'

    def test_invalid_value_is_rejected(self):
        settings = Settings()
        with pytest.raises(ValueError) as exc:
            settings.set('date.clock', '37')
        assert '24' in str(exc.value)

    def test_invalid_value_does_not_change_the_setting(self):
        settings = Settings()
        with pytest.raises(ValueError):
            settings.set('date.clock', '37')
        assert settings.get('date.clock') == '24'

    def test_unknown_key_is_rejected(self):
        with pytest.raises(KeyError):
            Settings().set('date.nonsense', 'x')

    def test_epoch_must_be_a_date(self):
        settings = Settings()
        with pytest.raises(ValueError):
            settings.set('date.epoch', 'yesterday')

    def test_epoch_accepts_an_iso_date(self):
        settings = Settings()
        assert settings.set('date.epoch', '1978-06-01') == '1978-06-01'


class TestDeviations:
    def test_changing_an_accurate_option_is_reported(self):
        settings = Settings()
        settings.set('display.charset', 'unicode')
        assert 'display.charset' in settings.deviations()

    def test_changing_a_neutral_option_is_not_a_deviation(self):
        """Seconds on or off is a readability choice, not an accuracy one."""
        settings = Settings()
        settings.set('date.seconds', 'off')
        assert 'date.seconds' not in settings.deviations()

    def test_reset_clears_deviations(self):
        settings = Settings()
        settings.set('display.charset', 'unicode')
        settings.set('date.source', 'real')
        settings.reset()
        assert settings.deviations() == []

    def test_reset_one_key_leaves_others(self):
        settings = Settings()
        settings.set('display.charset', 'unicode')
        settings.set('date.source', 'real')
        settings.reset('date.source')
        assert settings.get('date.source') == 'simulated'
        assert settings.get('display.charset') == 'unicode'


class TestPersistence:
    def test_settings_survive_a_new_instance(self, tmp_path):
        path = settings_path(str(tmp_path))
        first = Settings(path)
        first.set('date.format', 'iso')
        first.set('date.clock', '12')
        assert Settings(path).get('date.format') == 'iso'
        assert Settings(path).get('date.clock') == '12'

    def test_stored_file_is_readable_json(self, tmp_path):
        path = settings_path(str(tmp_path))
        Settings(path).set('date.format', 'us')
        stored = json.loads(open(path).read())
        assert stored['date.format'] == 'us'

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path):
        """A hand-edited file must never stop the simulation starting."""
        path = settings_path(str(tmp_path))
        open(path, 'w').write('{not json at all')
        assert Settings(path).get('date.format') == 'v7'

    def test_unknown_keys_in_file_are_ignored(self, tmp_path):
        path = settings_path(str(tmp_path))
        json.dump({'date.format': 'iso', 'not.a.setting': 'x'}, open(path, 'w'))
        settings = Settings(path)
        assert settings.get('date.format') == 'iso'
        assert 'not.a.setting' not in settings.as_dict()

    def test_invalid_stored_value_falls_back(self, tmp_path):
        path = settings_path(str(tmp_path))
        json.dump({'date.clock': '37'}, open(path, 'w'))
        assert Settings(path).get('date.clock') == '24'

    def test_settings_without_a_path_do_not_write(self):
        settings = Settings()
        settings.set('date.format', 'iso')
        assert settings.get('date.format') == 'iso'


def test_epoch_default_is_a_monday_in_the_simulated_era():
    """
    The default epoch anchors the shift and justifies the EST label.

    November 1983 is inside the depicted window and in standard time, so the
    timestamps the simulation prints are correct rather than merely plausible.
    """
    epoch = Settings().epoch()
    assert epoch.strftime('%A') == 'Monday'
    assert 1978 <= epoch.year <= 1983
    assert epoch.hour == 8
    assert Settings().get('date.epoch') == DEFAULT_EPOCH


def test_invalid_stored_epoch_does_not_crash_the_clock():
    settings = Settings()
    settings._values['date.epoch'] = 'not-a-date'
    assert settings.epoch().strftime('%Y-%m-%d') == DEFAULT_EPOCH


def test_options_by_key_covers_every_option():
    assert set(OPTIONS_BY_KEY) == {option.key for option in OPTIONS}
