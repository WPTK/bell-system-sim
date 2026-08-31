"""
LMOS, SARTS and the toll network, and the rule that keeps them honest.

Three qualifications used to pay out in placeholders: Main Distributing Frame
unlocked lmos, Switching Control Center unlocked sarts, and Toll Network -
which costs 108 correct closures on the hard difficulty - unlocked toll. All
three answered "subsystem not available in this release".

The guard at the bottom of this file is the one that matters. The rest test
that what replaced them is real.
"""

import random

import pytest

from bell_system.data.trouble import FAULTS
from bell_system.lmos import (
    LINE_RECORD_CAPACITY,
    OBJECTIVES,
    TEST_SYSTEMS,
    TREAT_REPORTS,
    Lmos,
)
from bell_system.progression import QUALIFICATIONS, QUALIFICATIONS_BY_KEY
from bell_system.special_services import (
    ACCESS_ARRANGEMENTS,
    CATEGORIES,
    STATUS_IN_SERVICE,
    STATUS_TROUBLE,
    SartsInventory,
)
from bell_system.terminal import UNIMPLEMENTED_COMMANDS


def work_a_report(terminal, fault=None):
    """Close one report so the bureau has history to show."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    terminal.execute_command(f'mlt {report.number}')
    terminal.execute_command(
        f'report dispatch {report.number} '
        f'{FAULTS[report.record.fault].dispatch}')
    terminal.execute_command(
        f'report close {report.number} 5 {report.record.fault}')
    return report


class TestProgressionPaysOut:
    """The R2 rule, and the reason this file exists."""

    def test_no_qualification_unlocks_a_stub(self):
        """
        A sign-off must never hand back "subsystem not available".

        This is the test that would have caught it: frame paid out lmos, scc
        paid out sarts, and toll - the longest grind in the game - paid out
        toll.
        """
        offenders = [
            (qualification.name, command)
            for qualification in QUALIFICATIONS
            for command in qualification.unlocks
            if command in UNIMPLEMENTED_COMMANDS
        ]
        assert not offenders, f'qualifications paying out in stubs: {offenders}'

    @pytest.mark.parametrize('command', ['lmos', 'sarts', 'toll'])
    def test_the_three_are_no_longer_stubs(self, command):
        assert command not in UNIMPLEMENTED_COMMANDS

    @pytest.mark.parametrize('command', ['lmos', 'sarts', 'toll'])
    def test_they_produce_real_output(self, terminal, command):
        result = terminal.execute_command(command)
        assert 'subsystem not available' not in result
        assert 'Command execution error' not in result
        assert len(result.splitlines()) > 8

    @pytest.mark.parametrize('key,command', [
        ('frame', 'lmos'), ('scc', 'sarts'), ('toll', 'toll'),
    ])
    def test_each_is_still_reached_by_its_qualification(self, key, command):
        assert command in QUALIFICATIONS_BY_KEY[key].unlocks


class TestLmos:
    """The bureau's view onto its own line records."""

    def test_the_status_screen_states_the_system_capacity(self, terminal):
        result = terminal.execute_command('lmos')
        assert f'{LINE_RECORD_CAPACITY:,}' in result

    def test_it_names_the_three_test_systems(self, terminal):
        result = terminal.execute_command('lmos')
        for code in TEST_SYSTEMS:
            assert code in result

    def test_it_states_the_bureau_objectives(self, terminal):
        result = terminal.execute_command('lmos')
        for objective in OBJECTIVES:
            assert objective in result

    def test_line_cards_come_from_the_report_desk(self, terminal):
        report = work_a_report(terminal)
        cards = Lmos(terminal.desk).line_cards()
        assert report.record.telephone_number in cards

    def test_a_line_card_shows_the_trouble_history(self, terminal):
        report = work_a_report(terminal)
        result = terminal.execute_command(
            f'lmos line {report.record.telephone_number}')
        assert report.record.name in result
        assert report.record.cable_pair() in result
        assert report.number in result

    def test_a_line_card_answers_to_a_report_number(self, terminal):
        report = work_a_report(terminal)
        assert Lmos(terminal.desk).find_card(report.number) is not None

    def test_an_unknown_line_is_reported(self, terminal):
        assert 'no line card record' in terminal.execute_command(
            'lmos line 999-999-9999')

    def test_a_line_becomes_chronic_at_three_reports(self, terminal):
        record = None
        for _ in range(3):
            report = terminal.desk.receive(
                terminal.clock.now(), fault='GROUND', record=record)
            record = report.record
        chronic = Lmos(terminal.desk).chronic_lines()
        assert chronic
        assert chronic[0].report_count >= 3
        assert 'CHRONIC' in terminal.execute_command(
            f'lmos line {record.telephone_number}')

    def test_treat_lists_its_analyses(self, terminal):
        result = terminal.execute_command('lmos treat')
        for report in TREAT_REPORTS:
            assert report in result

    def test_treat_counts_what_was_actually_closed(self, terminal):
        work_a_report(terminal, fault='GROUND')
        result = terminal.execute_command('lmos treat')
        assert 'Trouble found' in result
        assert 'Ground' in result

    def test_treat_coin_reports_on_coin_lines(self, terminal):
        assert 'Coin' in terminal.execute_command('lmos treat coin')

    def test_treat_force_reports_dispatches(self, terminal):
        work_a_report(terminal)
        result = terminal.execute_command('lmos treat force')
        assert 'Repair Force Administration' in result

    def test_utilisation_counts_the_work_done(self, terminal):
        work_a_report(terminal)
        result = terminal.execute_command('lmos utilisation')
        assert 'Measurements taken' in result
        assert 'Dispatches made' in result

    def test_report_processing_lists_the_board(self, terminal):
        # Capture the board first: running any command advances the shift, and
        # new work arrives whether or not ambience is on.
        expected = [report.number for report in terminal.desk.pending()]
        result = terminal.execute_command('lmos reports')
        for number in expected:
            assert number in result

    def test_an_unknown_option_is_reported(self, terminal):
        assert 'unknown option' in terminal.execute_command('lmos frobnicate')


class TestSarts:
    """Special services circuits, and reaching them remotely."""

    def test_an_inventory_is_generated_for_the_office(self, terminal):
        assert terminal.special_services.circuits

    def test_every_circuit_belongs_to_a_known_category(self, terminal):
        for circuit in terminal.special_services.circuits.values():
            assert circuit.category in CATEGORIES

    def test_every_circuit_has_a_known_access_arrangement(self, terminal):
        for circuit in terminal.special_services.circuits.values():
            assert circuit.access in ACCESS_ARRANGEMENTS

    def test_the_attested_categories_are_marked_as_such(self):
        attested = [c for c in CATEGORIES.values() if c.attested]
        assert len(attested) >= 7
        for code in ('FX', 'WATS', 'PBX', 'CTX', 'PL', 'PN'):
            assert CATEGORIES[code].attested

    def test_status_reports_what_is_reachable(self, terminal):
        result = terminal.execute_command('sarts')
        assert 'Reachable without a visit' in result
        assert str(terminal.special_services.remotely_testable()) in result

    def test_the_listing_shows_every_circuit(self, terminal):
        result = terminal.execute_command('sarts list')
        assert f'{len(terminal.special_services.circuits)} circuit(s)' in result

    def test_a_circuit_record_renders(self, terminal):
        circuit = terminal.special_services.listing()[0]
        result = terminal.execute_command(f'sarts circuit {circuit.circuit_id}')
        assert circuit.customer in result
        assert circuit.service.name in result

    def test_a_four_wire_circuit_gets_the_full_responder(self, terminal):
        circuit = next(c for c in terminal.special_services.circuits.values()
                       if c.wires == 4 and c.reachable())
        result = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert '105-type' in result
        assert 'Gain slope' in result

    def test_a_two_wire_circuit_gets_loss_and_noise(self, terminal):
        circuit = next(c for c in terminal.special_services.circuits.values()
                       if c.wires == 2 and c.reachable())
        result = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert '100-type' in result
        assert 'Noise' in result
        assert 'Gain slope' not in result

    def test_a_jack_circuit_cannot_be_reached_and_says_why(self, terminal):
        circuit = next((c for c in terminal.special_services.circuits.values()
                        if c.access == 'JACK'), None)
        if circuit is None:
            pytest.skip('no jack-access circuit in this inventory')
        result = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert 'manual jack access' in result
        assert 'Switched Maintenance Access System' in result

    def test_a_clean_circuit_returns_to_service(self, terminal):
        inventory = terminal.special_services
        circuit = next(c for c in inventory.circuits.values() if c.reachable())
        circuit.impaired = False
        circuit.status = STATUS_TROUBLE
        result = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert 'Returned to service' in result
        assert circuit.status == STATUS_IN_SERVICE

    def test_an_impaired_circuit_is_held(self, terminal):
        inventory = terminal.special_services
        circuit = next(c for c in inventory.circuits.values() if c.reachable())
        circuit.impaired = True
        circuit.status = STATUS_IN_SERVICE
        result = terminal.execute_command(f'sarts test {circuit.circuit_id}')
        assert 'FAIL' in result
        assert circuit.status == STATUS_TROUBLE

    def test_an_unknown_circuit_is_reported(self, terminal):
        assert 'no circuit matching' in terminal.execute_command(
            'sarts test ZZZZ-NOPE')

    def test_the_inventory_is_reproducible_from_a_seed(self):
        first = SartsInventory('NWRKNJ02', random.Random(11))
        second = SartsInventory('NWRKNJ02', random.Random(11))
        assert list(first.circuits) == list(second.circuits)


class TestToll:
    """The class 4 and higher offices."""

    def test_it_states_where_the_boundary_is(self, terminal):
        result = terminal.execute_command('toll')
        assert 'class 4 and higher' in result

    def test_it_counts_offices_by_class(self, terminal):
        result = terminal.execute_command('toll')
        assert 'Regional Center' in result
        assert 'Toll Center' in result

    def test_the_hierarchy_shows_what_homes_on_what(self, terminal):
        result = terminal.execute_command('toll hierarchy')
        assert 'homes on' in result
        for office in terminal.toll_network.offices.values():
            if office.switch_class <= 4:
                assert office.code in result

    def test_end_offices_are_not_in_the_hierarchy(self, terminal):
        result = terminal.execute_command('toll hierarchy')
        for office in terminal.toll_network.offices.values():
            if office.switch_class == 5:
                assert office.code not in result

    def test_load_shows_trunk_group_occupancy(self, terminal):
        result = terminal.execute_command('toll load')
        for name in terminal.trunk_groups:
            assert name in result

    def test_it_states_the_grade_of_service(self, terminal):
        assert 'P.01' in terminal.execute_command('toll load')
