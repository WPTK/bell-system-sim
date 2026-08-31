"""
Tests that hold period claims to their sources.

Each check here corresponds to a specific factual error the audit found, and
several assert values taken from Bell System documents bundled with this
repository - so a future edit cannot quietly reintroduce the error.
"""

import pytest

from bell_system.data.carrier import (
    L_CARRIER_SYSTEMS,
    MULTIPLEX_HIERARCHY,
)
from bell_system.data.signaling import (
    MF_FREQUENCIES,
    MF_SIGNALS,
    PROGRESS_TONES,
    SF_ADDRESS_LEVEL_DBM,
    SF_FREQUENCY_HZ,
    SF_IDLE_LEVEL_DBM,
)
from bell_system.data.switching import SWITCHING_SYSTEMS


class TestPostEraReferences:
    """Entities and codes that did not exist during 1978-1983."""

    def test_bellcore_is_not_referenced(self, terminal):
        """
        Bell Communications Research was created on 1 January 1984 by the
        divestiture decree - after the period, and fatal to the simulation's
        pre-divestiture framing.
        """
        for command in ('who', 'status', 'help'):
            assert 'BELLCORE' not in terminal.execute_command(command).upper()

    def test_motd_names_a_period_entity(self, terminal):
        motd = terminal.filesystem['/etc/motd']['content']
        assert 'BELLCORE' not in motd.upper()

    def test_npa_718_is_absent(self, terminal):
        """718 split from 212 on 1 September 1984, after the period."""
        npas = {office['npa'] for office in terminal.central_offices.values()}
        assert '718' not in npas

    def test_washington_dc_is_npa_202(self, terminal):
        """
        NPA 301 has been Maryland since the 1947 assignment; the District of
        Columbia is 202. Both tables said 301 while supplying DC's own
        coordinates.
        """
        dc = [o for o in terminal.central_offices.values()
              if o['city'] == 'Washington' and o['state'] in ('DC', 'District of Columbia')]
        for office in dc:
            assert office['npa'] == '202'


class TestSwitchingMachines:
    """Machines Western Electric actually built, as they were built."""

    def test_first_service_years(self):
        """Cutover years for the machines the simulation places."""
        expected = {
            'SXS': 1919, 'PANEL': 1921, 'XB1': 1938, 'XB5': 1948,
            '1ESS': 1965, '2ESS': 1970, '4ESS': 1976, '3ESS': 1976,
            '1AESS': 1976, '5ESS': 1982,
        }
        for code, year in expected.items():
            assert SWITCHING_SYSTEMS[code].first_service == year, code

    def test_no_ess_predates_stored_program_control(self):
        for code, system in SWITCHING_SYSTEMS.items():
            if 'ESS' in code:
                assert system.first_service >= 1965, code

    def test_third_ess_is_a_rural_machine(self):
        """
        The No. 3 ESS was the smallest ESS Western Electric built, for rural
        community dial offices. The simulation had one in Boston carrying
        roughly seven times the traffic the machine could handle.
        """
        third = SWITCHING_SYSTEMS['3ESS']
        assert third.max_lines <= 5000
        assert 'ural' in third.market

    def test_toll_machines_are_marked_as_such(self):
        for code in ('XB4', 'XB4A', '4ESS'):
            assert SWITCHING_SYSTEMS[code].is_toll, code

    def test_5ess_barely_existed_in_the_period(self):
        """Only a handful were in service before 1984."""
        assert SWITCHING_SYSTEMS['5ESS'].first_service == 1982


class TestLCarrier:
    """
    Line spectra verified against the transmission volumes in this repository.

    The old table gave every system the wrong band and mislabelled all three
    with multiplex-level names: 564-3084 kHz is the basic mastergroup, an
    assembly band, not the L4 line spectrum.
    """

    @pytest.mark.parametrize('code,low,high', [
        ('L1', 60, 2788),
        ('L3', 312, 8284),
        ('L4', 564, 17548),
        ('L5', 3124, 60556),
        ('L5E', 3252, 64844),
    ])
    def test_line_bands(self, code, low, high):
        system = L_CARRIER_SYSTEMS[code]
        assert system.line_low_khz == low
        assert system.line_high_khz == high

    @pytest.mark.parametrize('code,channels', [
        ('L1', 600), ('L3', 1860), ('L4', 3600), ('L5', 10800), ('L5E', 13200),
    ])
    def test_channel_capacity(self, code, channels):
        assert L_CARRIER_SYSTEMS[code].channels == channels

    @pytest.mark.parametrize('code,miles', [
        ('L1', 8), ('L3', 4), ('L4', 2), ('L5', 1),
    ])
    def test_repeater_spacing_halves_each_generation(self, code, miles):
        assert L_CARRIER_SYSTEMS[code].repeater_spacing_miles == miles

    def test_bandwidth_is_consistent_with_the_stated_figures(self):
        """
        E&O Table 9-4 states bandwidths independently of the band limits.
        They must agree, which is what makes these values trustworthy.
        """
        expected = {'L1': 2.7, 'L3': 8.0, 'L4': 17.0, 'L5': 57.5, 'L5E': 61.5}
        for code, mhz in expected.items():
            assert abs(L_CARRIER_SYSTEMS[code].bandwidth_mhz() - mhz) < 0.15, code

    @pytest.mark.parametrize('name,low,high', [
        ('Basic group', 60, 108),
        ('Basic supergroup', 312, 552),
        ('Basic mastergroup (U600)', 564, 3084),
        ('Basic jumbogroup', 564, 17548),
    ])
    def test_multiplex_hierarchy(self, name, low, high):
        level = next(x for x in MULTIPLEX_HIERARCHY if x.name == name)
        assert (level.low_khz, level.high_khz) == (low, high)

    def test_line_band_is_not_a_multiplex_band(self):
        """The specific conflation the old table made."""
        assert L_CARRIER_SYSTEMS['L4'].line_high_khz != 3084


class TestTsps:
    """
    TSPS served toll and assistance calls, not directory assistance.

    The screen made directory assistance 40-50 percent of TSPS traffic and
    added conference setup, while omitting coin and calling card - the two
    functions TSPS existed to mechanise.
    """

    @staticmethod
    def _tsps_state(terminal):
        """TSPS state initialises on first use, so exercise the command."""
        terminal.execute_command('tsps')
        return terminal.tsps_data

    def test_directory_assistance_is_not_a_position_function(self, terminal):
        assert 'directory_assist' not in self._tsps_state(terminal)

    def test_conference_is_not_a_position_function(self, terminal):
        assert 'conference' not in self._tsps_state(terminal)

    @pytest.mark.parametrize('function', [
        'coin', 'calling_card', 'collect_calls', 'third_number',
        'person_to_person', 'assistance', 'oni',
    ])
    def test_documented_functions_are_present(self, terminal, function):
        assert function in self._tsps_state(terminal)

    def test_screen_explains_the_directory_assistance_absence(self, terminal):
        result = terminal.execute_command('tsps')
        assert '411' in result

    def test_anachronistic_metrics_are_gone(self, terminal):
        """
        First Call Resolution and a five-point customer satisfaction score
        are call-centre constructs of the late 1980s and 1990s.
        """
        result = terminal.execute_command('tsps')
        assert 'First Call Resolution' not in result
        assert 'Customer Satisfaction' not in result

    def test_period_measurements_are_present(self, terminal):
        """Speed of answer and average work time are what Bell measured."""
        result = terminal.execute_command('tsps')
        assert 'Speed of answer' in result
        assert 'objective 2 to 6' in result
        assert 'Average work time' in result
        assert 'Erlang C' in result


class TestSignalingValues:
    """Signaling values, with the repo-verified ones asserted exactly."""

    def test_sf_supervision_levels(self):
        """
        Verified in Telecommunications Transmission Engineering Vol 1: the
        idle tone is -20 dBm0, raised 12 dB when pulsing address digits.
        """
        assert SF_FREQUENCY_HZ == 2600
        assert SF_IDLE_LEVEL_DBM == -20.0
        assert SF_ADDRESS_LEVEL_DBM == -8.0
        assert SF_ADDRESS_LEVEL_DBM - SF_IDLE_LEVEL_DBM == 12.0

    def test_mf_uses_two_of_six_frequencies(self):
        """
        Ten digits and five auxiliary signals is exactly the number of pairs
        available from six frequencies, so the table has no spare combination.
        """
        assert len(MF_FREQUENCIES) == 6
        assert len(MF_SIGNALS) == 15
        pairs = {(s.low, s.high) for s in MF_SIGNALS.values()}
        assert len(pairs) == 15

    def test_receiver_off_hook_tone(self):
        """Repo-verified: four frequencies interrupted five times a second."""
        roh = PROGRESS_TONES['howler']
        assert roh.frequencies == (1400, 2060, 2450, 2600)
        assert roh.cadence == (0.1, 0.1)

    def test_ringback_cadence_matches_the_ringing_cycle(self):
        """
        The standard central office ringing cycle was two seconds of ringing
        followed by four seconds of silence; audible ringing tracks it.
        """
        assert PROGRESS_TONES['ringback'].cadence == (2.0, 4.0)

    def test_no_unsourced_tone_plan_date_is_claimed(self):
        """
        No source consulted, including the repository's own 1977 transmission
        volumes, gives an adoption year for the Precise Tone Plan.
        """
        import bell_system.data.signaling as signaling
        assert '1976' not in (signaling.__doc__ or '')


class TestSwitchingHierarchy:
    """Office counts from E&O Table 4-1, distribution of offices in 1982."""

    def test_hierarchy_reports_documented_counts(self, terminal):
        result = terminal.execute_command('tnds hierarchy')
        for count in ('10', '52', '148', '508', '9,803'):
            assert count in result

    def test_connection_limits_are_stated(self, terminal):
        result = terminal.execute_command('tnds hierarchy')
        assert 'Maximum trunks in one connection:     9' in result
