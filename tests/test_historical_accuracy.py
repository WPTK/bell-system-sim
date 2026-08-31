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
        motd = terminal.filesystem['/etc/motd'].content
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


class TestClli:
    """
    COMMON LANGUAGE location identification.

    The simulation previously identified offices with ad-hoc strings like
    NYC-CO-14, which is the one thing a craftsperson of the period would
    never have written.
    """

    def test_code_is_eleven_characters(self):
        from bell_system.data.clli import CLLI_LENGTH
        assert CLLI_LENGTH == 11

    @pytest.mark.parametrize('code', [
        'CHCGILCL57T', 'DLLSTXTA02T', 'SNFCCA2143T',
    ])
    def test_attested_codes_parse(self, code):
        from bell_system.data.clli import ATTESTED_CLLI, parse
        parsed = parse(code)
        assert parsed is not None
        assert str(parsed) == code
        assert code in ATTESTED_CLLI

    def test_first_six_characters_must_be_alphabetic(self):
        """The 1977 field layout gives the first six positions as alphabetic."""
        from bell_system.data.clli import is_valid
        assert is_valid('CHCGILCL57T')
        assert not is_valid('CH1GILCL57T')
        assert not is_valid('CHCG1LCL57T')

    def test_length_is_enforced(self):
        from bell_system.data.clli import is_valid
        assert not is_valid('CHCGILCL57')
        assert not is_valid('CHCGILCL57TT')

    def test_building_form_is_the_first_eight(self):
        from bell_system.data.clli import parse
        assert parse('CHCGILCL57T').building_code() == 'CHCGILCL'

    def test_segments_decode(self):
        from bell_system.data.clli import parse
        parsed = parse('CHCGILCL57T')
        assert parsed.place == 'CHCG'
        assert parsed.state == 'IL'
        assert parsed.building == 'CL'
        assert parsed.entity == '57T'

    @pytest.mark.parametrize('city,code', [
        ('New York', 'NYCM'),
        ('Chicago', 'CHCG'),
        ('Newark', 'NWRK'),
        ('San Francisco', 'SNFC'),
        ('Dallas', 'DLLS'),
    ])
    def test_attested_place_codes(self, city, code):
        from bell_system.data.clli import place_code
        assert place_code(city) == code

    def test_place_code_is_always_four_alphabetic_characters(self):
        from bell_system.data.clli import place_code
        for city in ('Ely', 'X', 'Saint Paul', "Coeur d'Alene", ''):
            code = place_code(city)
            assert len(code) == 4, city
            assert code.isalpha(), city

    def test_entity_code_matches_the_machine(self):
        """
        The two letters name the control technology, so a crossbar office
        cannot carry a step group code.
        """
        from bell_system.data.clli import entity_for_switch
        assert entity_for_switch('XB5').startswith('MG')
        assert entity_for_switch('SXS').startswith('SG')
        assert entity_for_switch('1ESS').startswith('CG')
        assert entity_for_switch('4ESS', is_toll=True).endswith('T')

    def test_every_generated_office_has_a_valid_code(self, terminal):
        from bell_system.data.clli import is_valid
        malformed = [
            office['clli'] for office in terminal.central_offices.values()
            if not is_valid(office['clli'])
        ]
        assert not malformed, malformed[:5]

    def test_office_entity_matches_its_switch(self, terminal):
        """
        The two letters of an entity code name the control technology, so a
        crossbar office cannot carry a step group code and vice versa.
        """
        from bell_system.data.clli import SWITCHING_ENTITIES
        for office in terminal.central_offices.values():
            entity = office['clli'][8:]
            known = SWITCHING_ENTITIES.get(entity[:2])
            if known is not None:
                assert office['switch_type'] in known.switch_types, office['clli']

    def test_panel_is_not_generated(self, terminal):
        """
        Panel is real history and stays in the reference table, but by this
        period it was down to a handful of Newark offices; generating them
        nationwide would itself be inaccurate.
        """
        panel = [o['clli'] for o in terminal.central_offices.values()
                 if o['switch_type'] == 'PANEL']
        assert not panel, panel[:3]

    def test_decode_command_explains_a_code(self, terminal):
        result = terminal.execute_command('clli decode CHCGILCL57T')
        assert 'CHCG' in result and 'Toll or tandem' in result

    def test_decode_rejects_a_malformed_code(self, terminal):
        assert 'not a well formed' in terminal.execute_command('clli decode NOPE')

    def test_no_bellcore_in_administration_text(self, terminal):
        """
        COMMON LANGUAGE passed to Bellcore only at divestiture, so a
        simulation set before 1984 cites AT&T and BSP 795-100-100.
        """
        result = terminal.execute_command('clli')
        assert 'BELLCORE' not in result.upper()
        assert '795-100-100' in result


class TestCosmos:
    """COSMOS administers the main distributing frame, not a computer."""

    def test_status_explains_what_main_frame_means(self, terminal):
        result = terminal.execute_command('cosmos')
        assert 'main distributing frame' in result
        assert 'not a mainframe computer' in result

    def test_frame_has_both_sides(self, terminal):
        result = terminal.execute_command('cosmos')
        assert 'Vertical appearances' in result
        assert 'Horizontal appearances' in result

    def test_assignment_produces_a_frame_work_order(self, terminal):
        result = terminal.execute_command('cosmos assign 555-1212')
        assert 'frame work order' in result.lower()
        assert 'jumper' in result.lower()

    def test_balance_reports_line_link_groups(self, terminal):
        result = terminal.execute_command('cosmos balance')
        assert 'ORIGINATING CCS' in result

    def test_syntax_is_declared_as_the_simulation_own(self, terminal):
        """
        No source available reproduces real COSMOS transaction syntax, so
        the command says its own syntax is invented rather than implying
        historical fidelity it cannot claim.
        """
        assert "simulation's own" in terminal.execute_command('cosmos')


class TestBellSystemPractices:
    """
    BSP division numbers, corrected against published practice indexes.

    The previous table was invented and assigned division 600 to "UNIX and
    Computing Systems"; 600-699 is outside plant and test centre operation,
    and no division covered computing systems at all.
    """

    def test_real_divisions_are_used(self):
        from bell_system.constants import BSP_CATEGORIES
        assert BSP_CATEGORIES['795'] == 'Common Language'
        assert BSP_CATEGORIES['660'] == 'Test Center Operation'
        assert BSP_CATEGORIES['800'] == 'Equipment Design Requirements'

    def test_no_computing_division_is_claimed(self):
        from bell_system.constants import BSP_CATEGORIES
        for subject in BSP_CATEGORIES.values():
            assert 'UNIX' not in subject
            assert 'Computing' not in subject

    def test_clli_practice_is_cited(self):
        from bell_system.constants import BSP_PRACTICES
        assert '795-100-100' in BSP_PRACTICES


def test_sarts_expansion_is_correct():
    """
    SARTS is the Switched Access Remote Test System. It tests special
    services, but that is not what the acronym stands for.
    """
    from bell_system.terminal import BELL_SYSTEM_ROLES
    assert 'Switched Access Remote Test' in BELL_SYSTEM_ROLES[11][1]
    assert 'Special Service Testing' not in BELL_SYSTEM_ROLES[11][1]
