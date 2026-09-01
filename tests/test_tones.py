"""
The signalling, rendered to audio.

Every frequency, level and cadence has been in data/signaling.py since it
was written, described in words and never heard. These check that what
comes out is what the tables say - especially the relative levels, which
are the part it would be easy to quietly get wrong.
"""

import math
import os
import wave

import pytest

from bell_system import tones
from bell_system.data.signaling import (
    DTMF_KEYS,
    MF_SIGNALS,
    PROGRESS_TONES,
    SF_FREQUENCY_HZ,
)


def peak(samples):
    """Loudest point of a rendering."""
    return max((abs(value) for value in samples), default=0.0)


def dominant_hz(samples, rate=tones.SAMPLE_RATE):
    """
    The strongest frequency in a rendering, by a coarse search.

    A full transform would be better and needs numpy, which this project
    does not depend on. Correlating against candidate frequencies is enough
    to tell 480 Hz from 620 Hz.
    """
    best, best_power = 0, -1.0
    for hz in range(100, 2800, 2):
        real = sum(value * math.cos(2 * math.pi * hz * i / rate)
                   for i, value in enumerate(samples))
        imaginary = sum(value * math.sin(2 * math.pi * hz * i / rate)
                        for i, value in enumerate(samples))
        power = real * real + imaginary * imaginary
        if power > best_power:
            best, best_power = hz, power
    return best


class TestTheLevelsAreTheTables:
    """The part that would be easy to get quietly wrong."""

    def test_zero_dbm_is_the_reference(self):
        assert tones.amplitude_for(0.0) == tones.REFERENCE_AMPLITUDE

    def test_six_db_down_is_half_the_amplitude(self):
        assert tones.amplitude_for(-6.0) == pytest.approx(
            tones.REFERENCE_AMPLITUDE / 2, rel=0.01)

    def test_busy_renders_below_dial_by_what_the_table_says(self):
        """
        Dial tone is -13 dBm and busy is -24. Eleven dB apart in the table
        means eleven dB apart in the file.
        """
        table = (PROGRESS_TONES['dial'].level_dbm
                 - PROGRESS_TONES['busy'].level_dbm)
        rendered = 20 * math.log10(peak(tones.render('dial', seconds=1.0))
                                   / peak(tones.render('busy', seconds=1.0)))
        assert rendered == pytest.approx(table, abs=0.2)

    def test_the_loudest_tone_does_not_clip(self):
        """
        The howler is 0 dBm with four components, which is the worst case
        the tables contain, and the reference is set so it just fits.
        """
        assert peak(tones.render('howler', seconds=1.0)) <= 1.0

    def test_normalising_changes_the_file_and_not_the_table(self, tmp_path):
        quiet = tones.render('busy', seconds=1.0)
        assert peak(quiet) < 0.1
        path = str(tmp_path / 'busy.wav')
        tones.write(path, quiet, normalise=True)
        assert os.path.getsize(path) > 1000
        # The renderer itself is unchanged.
        assert peak(tones.render('busy', seconds=1.0)) == peak(quiet)


class TestTheFrequenciesAreTheTables:
    """Nothing here invents a frequency."""

    @pytest.mark.parametrize('name', ['dial', 'busy', 'ringback'])
    def test_a_progress_tone_contains_its_own_frequencies(self, name):
        tone = PROGRESS_TONES[name]
        # Sample the on-portion only, so a cadence gap does not dominate.
        samples = tones.render(name, seconds=0.2)[:1600]
        found = dominant_hz(samples)
        assert min(abs(found - hz) for hz in tone.frequencies) <= 6, (
            name, found, tone.frequencies)

    def test_sf_is_twenty_six_hundred(self):
        samples = tones.sf_supervision(seizure=False, seconds=0.2)
        assert abs(dominant_hz(samples) - SF_FREQUENCY_HZ) <= 6

    def test_every_progress_tone_renders(self):
        for name in PROGRESS_TONES:
            assert tones.render(name, seconds=0.5)

    def test_an_unknown_name_is_refused(self):
        with pytest.raises(KeyError):
            tones.render('nonsense')


class TestCadence:
    """Busy and reorder are the same tone at different rates."""

    def test_they_share_their_frequencies(self):
        assert (PROGRESS_TONES['busy'].frequencies
                == PROGRESS_TONES['reorder'].frequencies)

    def test_reorder_is_interrupted_twice_as_often(self):
        busy = PROGRESS_TONES['busy'].cadence[0]
        reorder = PROGRESS_TONES['reorder'].cadence[0]
        assert busy == pytest.approx(reorder * 2)

    def test_a_cadenced_tone_has_silence_in_it(self):
        samples = tones.render('busy', seconds=2.0)
        quiet = sum(1 for value in samples if abs(value) < 0.001)
        assert quiet > len(samples) * 0.3

    def test_a_continuous_tone_does_not(self):
        samples = tones.render('dial', seconds=1.0)
        quiet = sum(1 for value in samples if abs(value) < 0.001)
        assert quiet < len(samples) * 0.1

    def test_a_rendering_is_the_length_asked_for(self):
        for name in ('dial', 'busy', 'ringback'):
            samples = tones.render(name, seconds=1.5)
            assert len(samples) == int(tones.SAMPLE_RATE * 1.5)


class TestAddressSignalling:
    """MF and Touch-Tone."""

    def test_kp_and_st_are_read_as_one_symbol_each(self):
        """A plain character walk would look for a signal called K."""
        assert tones._split_symbols('KP212ST') == [
            'KP', '2', '1', '2', 'ST']

    def test_a_pulse_train_renders(self):
        assert tones.mf_digits('KP212ST')

    def test_kp_is_held_longer_than_a_digit(self):
        """The far end has to recognise a train before it starts counting."""
        from bell_system.data.signaling import MF_DIGIT_MS, MF_KP_MS
        assert MF_KP_MS > MF_DIGIT_MS
        assert len(tones.mf_digits('KP')) > len(tones.mf_digits('1'))

    def test_every_mf_signal_can_be_pulsed(self):
        for symbol in MF_SIGNALS:
            assert tones.mf_digits(symbol)

    def test_an_unknown_mf_symbol_is_refused(self):
        with pytest.raises(KeyError):
            tones.mf_digits('Z')

    def test_every_touch_tone_key_renders(self):
        for key in DTMF_KEYS:
            assert tones.dtmf(key)

    def test_the_two_dtmf_groups_are_at_different_levels(self):
        """
        The high group is sent louder because the network's response falls
        off across the band and the far end has to hear both.
        """
        from bell_system.data.signaling import (
            DTMF_HIGH_GROUP_LEVEL_DBM,
            DTMF_LOW_GROUP_LEVEL_DBM,
        )
        assert DTMF_HIGH_GROUP_LEVEL_DBM > DTMF_LOW_GROUP_LEVEL_DBM

    def test_sf_seizure_has_a_gap_in_it(self):
        """2600 present is idle; absent is seized. That is the signalling."""
        samples = tones.sf_supervision(seizure=True, seconds=3.0)
        middle = samples[len(samples) // 3: 2 * len(samples) // 3]
        assert peak(middle) < 0.001


class TestTheFile:
    """What gets written."""

    def test_it_is_a_playable_wave_file(self, tmp_path):
        path = str(tmp_path / 'dial.wav')
        tones.write(path, tones.render('dial', seconds=0.5))
        with wave.open(path) as handle:
            assert handle.getframerate() == tones.SAMPLE_RATE
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 2
            assert handle.getnframes() == int(tones.SAMPLE_RATE * 0.5)

    def test_the_rate_is_the_networks_own(self):
        """A voice channel was sampled at 8 kHz for T-carrier."""
        assert tones.SAMPLE_RATE == 8000

    def test_it_clips_rather_than_wrapping(self, tmp_path):
        """Wrapping sounds like a fault in the equipment."""
        path = str(tmp_path / 'loud.wav')
        tones.write(path, [2.0, -2.0, 0.0])
        with wave.open(path) as handle:
            frames = handle.readframes(3)
        import struct
        values = struct.unpack('<3h', frames)
        assert values[0] == 32767
        assert values[1] == -32767


class TestTheCommand:
    """tone(1)."""

    def test_the_listing_names_everything_renderable(self, terminal):
        listing = terminal.execute_command('tone')
        for name in PROGRESS_TONES:
            assert name in listing
        for name in ('mf', 'dtmf', 'sf'):
            assert name in listing

    def test_it_writes_a_file_and_says_where(self, terminal):
        result = terminal.execute_command('tone busy')
        assert 'wrote' in result
        path = result.split('wrote ')[1].split('\n')[0]
        assert os.path.exists(path)

    def test_it_says_what_the_tone_means(self, terminal):
        assert PROGRESS_TONES['busy'].meaning in terminal.execute_command(
            'tone busy')

    def test_it_says_the_file_is_outside_the_simulation(self, terminal):
        """A 1983 machine could not have made a wave file."""
        assert 'outside the simulation' in terminal.execute_command('tone dial')

    def test_an_unknown_tone_is_refused(self, terminal):
        assert 'nothing of that name' in terminal.execute_command(
            'tone nonsense')

    def test_mf_takes_an_address(self, terminal):
        assert 'wrote' in terminal.execute_command('tone mf KP212ST')

    def test_it_does_not_write_into_the_simulated_tree(self, terminal):
        terminal.execute_command('tone dial')
        assert not any(path.endswith('.wav') for path in terminal.filesystem)


class TestTheEra:
    """
    The plant follows the date, and says where it does not.

    A second era turned out to be substantially already built: the office
    generator reads each switching system's first-service year, so moving
    the epoch moves the network. What does not move is the writing, and the
    screen has to say so rather than letting a player find a 1984
    divestiture notice on a 1955 machine.
    """

    def build(self, epoch, tmp_path, monkeypatch):
        """A terminal with the epoch set, from a clean state directory."""
        monkeypatch.setenv('BELL_SYSTEM_HOME', str(tmp_path / epoch))
        from bell_system.terminal import BellSystemTerminal
        first = BellSystemTerminal()
        first.settings.set('date.epoch', epoch)
        instance = BellSystemTerminal()
        instance.settings.set('game.ambience', 'off')
        return instance

    def kinds(self, terminal):
        """The switch types present in the network."""
        return {office['switch_type']
                for office in terminal.central_offices.values()}

    def test_nineteen_fifty_five_has_no_electronic_switching(
            self, tmp_path, monkeypatch):
        present = self.kinds(self.build('1955-06-14', tmp_path, monkeypatch))
        assert 'SXS' in present
        assert not any(code.endswith('ESS') for code in present), present

    def test_nineteen_seventy_one_has_the_first_two(
            self, tmp_path, monkeypatch):
        present = self.kinds(self.build('1971-06-14', tmp_path, monkeypatch))
        assert '1ESS' in present
        assert '5ESS' not in present
        assert '4ESS' not in present

    def test_the_shift_date_has_the_whole_table(self, tmp_path, monkeypatch):
        present = self.kinds(self.build('1983-11-14', tmp_path, monkeypatch))
        assert '5ESS' in present
        assert 'SXS' in present

    def test_no_office_predates_its_own_switching_system(
            self, tmp_path, monkeypatch):
        """
        The bug the switching data was written to stop: a No. 5 Crossbar
        cut over in 1901, or a 5ESS seventeen years early.
        """
        from bell_system.data.switching import SWITCHING_SYSTEMS
        for epoch in ('1955-06-14', '1971-06-14', '1983-11-14'):
            terminal = self.build(epoch, tmp_path, monkeypatch)
            for office in terminal.central_offices.values():
                system = SWITCHING_SYSTEMS[office['switch_type']]
                assert int(office['installation_date']) >= system.first_service
                assert int(office['installation_date']) <= int(epoch[:4])

    def test_the_screen_lists_what_is_not_built_yet(
            self, tmp_path, monkeypatch):
        terminal = self.build('1955-06-14', tmp_path, monkeypatch)
        result = terminal.execute_command('era')
        assert 'NOT YET BUILT' in result
        assert '5ESS' in result

    def test_it_admits_the_writing_did_not_move(self, tmp_path, monkeypatch):
        terminal = self.build('1955-06-14', tmp_path, monkeypatch)
        result = terminal.execute_command('era')
        assert 'WHAT HAS NOT MOVED' in result
        assert 'November 1983' in result

    def test_it_says_nothing_of_the_kind_on_the_shift_date(
            self, tmp_path, monkeypatch):
        terminal = self.build('1983-11-14', tmp_path, monkeypatch)
        result = terminal.execute_command('era')
        assert 'WHAT HAS NOT MOVED' not in result
        assert 'NOT YET BUILT' not in result
