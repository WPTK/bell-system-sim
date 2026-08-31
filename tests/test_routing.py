"""
Tests for hierarchical alternate routing.

The rules asserted here come from Engineering and Operations in the Bell
System: complete at the lowest level of the hierarchy, overflow from
high-usage to final groups, block with reorder when a final group is full,
and never exceed nine trunks in tandem.
"""

import random

import pytest

from bell_system.routing import (
    FINAL_GROUP_BLOCKING,
    HIGH_USAGE_BLOCKING,
    MAX_TRUNKS_IN_CONNECTION,
    build_default_network,
)


@pytest.fixture
def network():
    return build_default_network()


@pytest.fixture
def end_offices(network):
    return [code for code, office in network.offices.items()
            if office.switch_class == 5]


def test_documented_limits():
    """No connection could use more than nine trunks in tandem."""
    assert MAX_TRUNKS_IN_CONNECTION == 9


def test_grade_of_service_objectives():
    """Final groups meet P.01; high-usage groups are meant to overflow."""
    assert FINAL_GROUP_BLOCKING == 0.01
    assert HIGH_USAGE_BLOCKING == 0.10
    assert HIGH_USAGE_BLOCKING > FINAL_GROUP_BLOCKING


class TestHomingChains:
    def test_every_office_reaches_a_regional_centre(self, network):
        """A homing chain terminates at a class 1 office."""
        for code, office in network.offices.items():
            chain = network.homing_chain(code)
            top = network.offices[chain[-1]]
            assert top.switch_class == 1, f'{code} homes on {top.code}'

    def test_chain_climbs_the_hierarchy(self, network):
        """Each step up a homing chain reaches an office of lower class number."""
        for code in network.offices:
            chain = [network.offices[c] for c in network.homing_chain(code)]
            classes = [office.switch_class for office in chain]
            assert classes == sorted(classes, reverse=True), code

    def test_chain_terminates(self, network):
        """A chain never loops, however the table is arranged."""
        for code in network.offices:
            chain = network.homing_chain(code)
            assert len(chain) == len(set(chain)), code

    def test_common_point_within_a_region(self, network):
        """Two offices under one regional centre meet on their chains."""
        assert network.common_point('EO-BOS-01', 'EO-NYC-01') is not None

    def test_offices_in_different_regions_have_no_shared_chain_point(self, network):
        """
        Boston and Chicago home to different regional centres, so their
        chains never meet; the call crosses at the regional level instead.
        """
        assert network.common_point('EO-BOS-01', 'EO-CHI-01') is None
        assert network.regional_centre('EO-BOS-01') == 'RC-EAST'
        assert network.regional_centre('EO-CHI-01') == 'RC-CENT'

    def test_interregional_calls_still_complete(self, network):
        """Every regional centre had a final group to every other."""
        rng = random.Random(9)
        completed = sum(
            1 for _ in range(200)
            if network.route('EO-BOS-01', 'EO-CHI-01', rng).completed
        )
        assert completed > 150, f'only {completed} of 200 interregional calls completed'


class TestRouting:
    def test_a_completed_call_has_a_path(self, network):
        result = network.route('EO-BOS-01', 'EO-CHI-01', random.Random(1))
        if result.completed:
            assert result.legs
            assert result.trunk_count() >= 1

    def test_no_connection_exceeds_the_maximum(self, network, end_offices):
        rng = random.Random(4)
        for _ in range(2000):
            origin, destination = rng.sample(end_offices, 2)
            result = network.route(origin, destination, rng)
            assert result.trunk_count() <= MAX_TRUNKS_IN_CONNECTION

    def test_average_connection_is_slightly_over_three_trunks(self, network, end_offices):
        """
        The documented average for a toll connection, including the toll
        connecting trunks at each end.
        """
        rng = random.Random(11)
        lengths = []
        for _ in range(4000):
            origin, destination = rng.sample(end_offices, 2)
            result = network.route(origin, destination, rng)
            if result.completed:
                lengths.append(result.trunk_count())
        average = sum(lengths) / len(lengths)
        assert 2.7 <= average <= 3.6, f'average was {average:.2f}'

    def test_a_toll_call_uses_at_least_three_trunks_via_the_toll_centre(self, network):
        """
        Up a toll connecting trunk, across the intertoll network, and back
        down - unless an end office toll trunk bypasses the toll centre.
        """
        rng = random.Random(2)
        seen_three = False
        for _ in range(200):
            result = network.route('EO-BOS-01', 'EO-CHI-01', rng)
            if result.completed and result.trunk_count() >= 3:
                seen_three = True
                types = [leg.group_type for leg in result.legs]
                assert types[0] == 'Toll connecting'
                assert types[-1] == 'Toll connecting'
                break
        assert seen_three

    def test_blocked_call_names_the_full_group(self, network, end_offices):
        rng = random.Random(3)
        for _ in range(4000):
            origin, destination = rng.sample(end_offices, 2)
            result = network.route(origin, destination, rng)
            if not result.completed and result.legs:
                assert 'reorder' in result.reason
                assert any(leg.blocked for leg in result.legs)
                return
        pytest.skip('no blocked call in this sample')

    def test_unknown_office_is_reported(self, network):
        result = network.route('EO-BOS-01', 'NOWHERE')
        assert not result.completed
        assert 'not in routing table' in result.reason

    def test_same_office_is_rejected(self, network):
        result = network.route('EO-BOS-01', 'EO-BOS-01')
        assert not result.completed


class TestRoutingCommand:
    def test_status_lists_the_routing_table(self, terminal):
        result = terminal.execute_command('routing')
        assert 'HIERARCHICAL' in result.upper()
        assert 'EO-BOS-01' in result

    def test_trace_follows_a_call(self, terminal):
        result = terminal.execute_command('routing trace EO-BOS-01 EO-CHI-01')
        assert 'ROUTE ADVANCE' in result
        assert 'COMPLETED' in result or 'BLOCKED' in result

    def test_chain_shows_the_hierarchy(self, terminal):
        result = terminal.execute_command('routing chain EO-CHI-01')
        assert 'Regional Center' in result
        assert 'Toll Center' in result

    def test_unknown_office_is_reported(self, terminal):
        assert 'no office' in terminal.execute_command('routing chain NOWHERE')

    def test_unknown_option_is_reported(self, terminal):
        assert 'Unknown option' in terminal.execute_command('routing nonsense')
