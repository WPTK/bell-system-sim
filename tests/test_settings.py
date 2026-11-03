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


class TestAssists:
    """
    Difficulty is a profile, and an assist is one field of it set by name.

    The setting is the authority and the profile is what applies while it
    reads ``profile``.
    """

    @staticmethod
    def career_with(settings, profile):
        from bell_system.progression import Career
        career = Career(difficulty=profile)
        career.set_assists(settings.assist_overrides())
        return career

    def test_every_assist_starts_on_the_profile(self):
        settings = Settings()
        assert settings.assist_departures() == []
        assert settings.assist_overrides() == {}

    @pytest.mark.parametrize('profile', ['fun', 'craft'])
    def test_each_assist_overrides_its_profile_value(self, profile):
        from bell_system.progression import ASSISTS
        for assist in ASSISTS:
            for choice, value in assist.choices.items():
                settings = Settings()
                settings.set(assist.key, choice)
                career = self.career_with(settings, profile)
                assert getattr(career.difficulty, assist.field) == value, \
                    (assist.key, choice)
                assert career.difficulty.key == profile

    def test_the_profile_table_is_never_written_to(self):
        from bell_system.progression import DIFFICULTIES
        before = dict(DIFFICULTIES)
        settings = Settings()
        settings.set('assist.commitments_count', 'full')
        self.career_with(settings, 'fun')
        assert DIFFICULTIES == before

    def test_back_to_profile_gives_the_profile_back(self):
        from bell_system.progression import DIFFICULTIES
        settings = Settings()
        settings.set('assist.pace', 'slow')
        settings.set('assist.pace', 'profile')
        career = self.career_with(settings, 'fun')
        assert career.difficulty == DIFFICULTIES['fun']

    def test_an_assist_survives_a_restart(self, tmp_path):
        path = settings_path(str(tmp_path))
        Settings(path).set('assist.annotate', 'on')
        assert Settings(path).assist_departures() == ['assist.annotate']

    def test_an_assist_value_nobody_offers_falls_back_to_profile(self, tmp_path):
        path = settings_path(str(tmp_path))
        with open(path, 'w') as handle:
            json.dump({'assist.pace': 'ludicrous'}, handle)
        assert Settings(path).get('assist.pace') == 'profile'

    def test_assists_are_not_period_deviations(self):
        """They bend the difficulty, which the option text says is not 1983."""
        settings = Settings()
        settings.set('assist.test_first', 'off')
        assert settings.deviations() == []

    @pytest.mark.parametrize('profile,choice,loses_less', [
        ('fun', 'full', False),
        ('craft', 'off', True),
    ])
    def test_commitments_count_overrides_in_both_directions(
            self, profile, choice, loses_less):
        """Fun can be made to count them in full, craft to stop counting."""
        from bell_system.progression import score_index
        settings = Settings()
        plain = self.career_with(settings, profile).difficulty
        settings.set('assist.commitments_count', choice)
        assisted = self.career_with(settings, profile).difficulty
        before = score_index(10, 0, 0, 5, 0, plain)
        after = score_index(10, 0, 0, 5, 0, assisted)
        assert (after > before) if loses_less else (after < before)

    def test_a_missed_commitment_costs_nothing_when_not_counted(self):
        from bell_system.progression import score_index
        settings = Settings()
        settings.set('assist.commitments_count', 'off')
        difficulty = self.career_with(settings, 'craft').difficulty
        assert score_index(10, 0, 0, 10, 0, difficulty) == 100.0

    def test_annotation_defaults_are_per_profile(self):
        from bell_system.progression import ANNOTATE_ALWAYS, DIFFICULTIES
        assert DIFFICULTIES['fun'].annotation_sightings == 4
        assert DIFFICULTIES['craft'].annotation_sightings == 0
        settings = Settings()
        settings.set('assist.annotate', 'on')
        career = self.career_with(settings, 'craft')
        assert career.difficulty.annotation_sightings == ANNOTATE_ALWAYS


class TestAssistsAtTheTerminal:
    def test_set_lists_the_departures(self, raw_terminal):
        raw_terminal.execute_command('set assist.pace slow')
        screen = raw_terminal.execute_command('set')
        assert '1 assist(s) override' in screen
        assert 'assist.pace' in screen.split('override')[1]

    def test_set_with_nothing_changed_lists_none(self, raw_terminal):
        assert 'override' not in raw_terminal.execute_command('set')

    def test_the_session_takes_the_assist_at_once(self, raw_terminal):
        raw_terminal.execute_command('set assist.test_first on')
        assert raw_terminal.career.difficulty.require_test_before_close
        raw_terminal.execute_command('set assist.test_first off')
        assert not raw_terminal.career.difficulty.require_test_before_close

    def test_reset_puts_them_all_back(self, raw_terminal):
        raw_terminal.execute_command('set assist.pace slow')
        raw_terminal.execute_command('set reset')
        assert raw_terminal.settings.assist_departures() == []
        assert raw_terminal.career.difficulty.reports_per_qualification == 3

    def test_a_new_session_starts_with_the_saved_assist(self, raw_terminal):
        from bell_system.terminal import BellSystemTerminal
        raw_terminal.execute_command('set assist.pace slow')
        again = BellSystemTerminal()
        assert again.career.difficulty.reports_per_qualification == 12

    def test_qual_names_the_assists_in_force(self, raw_terminal):
        raw_terminal.execute_command('set assist.commitments_count off')
        record = raw_terminal.execute_command('qual')
        assert 'Assists' in record
        assert 'assist.commitments_count' in record
        assert '(not counted)' in record

    def test_a_craft_session_with_the_test_requirement_off_may_close(
            self, raw_terminal):
        raw_terminal.execute_command('set game.difficulty craft')
        raw_terminal.execute_command('set assist.test_first off')
        said = raw_terminal.execute_command('set game.difficulty craft')
        assert 'cannot be closed until' not in said
