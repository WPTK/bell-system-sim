"""
The fourteen telephony commands that used to say they were unavailable.

Four of them - trace, capacity, coer, custdb - turned out to have real data
already in the simulation sitting behind them, and were unavailable only
because nobody had joined the two up. The tests below check the join as much
as the output: a trace must be the routing engine's answer, a capacity report
must be the trunk groups' real numbers, a line record must be the same card
LMOS holds.
"""

import pytest

from bell_system.constants import UNIMPLEMENTED_COMMANDS
from bell_system.screens.plant import EQUIPMENT

RETIRED = ['5ess', 'capacity', 'coer', 'collect', 'custdb', 'dbquery',
           'microwave', 'provision', 'satellite', 'trace', 'training',
           'western']


class TestNoStubsLeft:
    """The list is empty, and every command on the machine does something."""

    def test_the_list_is_empty(self):
        assert UNIMPLEMENTED_COMMANDS == frozenset()

    @pytest.mark.parametrize('command', RETIRED)
    def test_each_produces_real_output(self, terminal, command):
        result = terminal.execute_command(command)
        assert result.strip()
        assert 'not available in this release' not in result
        assert 'Command execution error' not in result
        assert 'command not found' not in result

    @pytest.mark.parametrize('command', ['analysis', 'netdata'])
    def test_the_two_with_no_referent_are_gone(self, terminal, command):
        """
        Neither was a real command name anywhere, and both duplicated a tnds
        subcommand that already worked. Removing beats implementing a name
        nothing ever had.
        """
        assert command not in terminal._command_handlers
        assert 'tnds' in terminal._command_handlers

    @pytest.mark.parametrize('subcommand', ['analysis', 'collect'])
    def test_what_they_duplicated_still_works(self, terminal, subcommand):
        result = terminal.execute_command(f'tnds {subcommand}')
        assert result.strip() and 'not found' not in result


class TestTrace:
    """trace(1) is the routing engine, printed one leg at a time."""

    def test_it_lists_the_offices_by_class(self, terminal):
        result = terminal.execute_command('trace')
        assert 'Class 5 - End Office' in result
        assert 'EO-NYC-01' in result

    def test_a_homing_chain_ends_at_a_regional_centre(self, terminal):
        result = terminal.execute_command('trace EO-NYC-01')
        assert 'EO-NYC-01' in result
        assert 'RC-EAST' in result
        assert result.index('EO-NYC-01') < result.index('RC-EAST')

    def test_a_call_takes_a_path_of_trunks(self, terminal):
        result = terminal.execute_command('trace EO-NYC-01 EO-CHI-01')
        assert 'PATH TAKEN' in result
        assert 'trunks in tandem' in result

    def test_the_path_it_prints_is_the_engine_s_answer(self, terminal):
        """
        trace must not invent a route. Every leg it prints has to be a leg
        the routing engine produced for the same pair of offices.
        """
        import random
        result = terminal.execute_command('trace EO-NYC-01 EO-CHI-01')
        engine = terminal.toll_network.route(
            'EO-NYC-01', 'EO-CHI-01', random.Random('EO-NYC-01EO-CHI-01'))
        for leg in engine.legs:
            assert leg.from_office in result
            assert leg.to_office in result
        assert f"{engine.trunk_count()} trunks in tandem" in result

    def test_an_office_not_in_the_table_is_reported(self, terminal):
        assert 'not in the routing table' in terminal.execute_command(
            'trace EO-NOWHERE')

    def test_a_call_to_itself_is_refused(self, terminal):
        assert 'same office' in terminal.execute_command(
            'trace EO-NYC-01 EO-NYC-01')

    def test_office_codes_are_case_insensitive(self, terminal):
        assert 'HOMING CHAIN' in terminal.execute_command('trace eo-nyc-01')


class TestWestern:
    """The equipment reference, and what it will not claim."""

    def test_it_lists_by_kind(self, terminal):
        result = terminal.execute_command('western')
        assert 'STATION' in result and 'SWITCHING' in result
        assert 'TRANSMISSION' in result

    def test_an_entry_has_a_date_and_a_reason_to_exist(self, terminal):
        result = terminal.execute_command('western 500')
        assert '1949' in result
        assert 'rotary' in result.lower()

    def test_a_partial_name_finds_one_entry(self, terminal):
        assert '1982' in terminal.execute_command('western 5ess')

    def test_an_unknown_name_is_reported(self, terminal):
        assert 'no entry' in terminal.execute_command('western nonsense')

    def test_every_entry_carries_a_year_and_a_kind(self, terminal):
        """
        An entry without a date is a claim with nothing behind it, which is
        what this table exists not to make.
        """
        for key, item in EQUIPMENT.items():
            assert item.introduced.isdigit(), key
            assert 1930 < int(item.introduced) <= 1983, key
            assert item.kind in ('station', 'switching', 'transmission'), key
            assert item.note.endswith('.'), key

    def test_nothing_in_the_table_postdates_the_shift(self, terminal):
        """The shift is November 1983; nothing later can be in the plant."""
        for key, item in EQUIPMENT.items():
            assert int(item.introduced) <= 1983, key


class TestCapacityAndCoer:
    """Reports built from state that was already there."""

    def test_capacity_reports_the_real_trunk_groups(self, terminal):
        result = terminal.execute_command('capacity')
        for name, group in terminal.trunk_groups.items():
            assert name in result
            assert str(group['capacity']) in result

    def test_capacity_names_a_group_over_its_objective(self, terminal):
        name = next(iter(terminal.trunk_groups))
        terminal.trunk_groups[name]['utilization'] = 97
        result = terminal.execute_command('capacity')
        assert 'OVER' in result
        assert 'Over objective' in result and name in result

    def test_coer_counts_the_offices_that_exist(self, terminal):
        result = terminal.execute_command('coer')
        assert 'End Office' in result
        end_offices = sum(1 for office in terminal.toll_network.offices.values()
                          if office.switch_class == 5)
        assert str(end_offices) in result

    def test_coer_on_one_office_prints_its_chain(self, terminal):
        result = terminal.execute_command('coer TC-NYC')
        assert 'RC-EAST' in result
        assert 'PC-NYC' in result

    def test_coer_reports_the_board(self, terminal):
        result = terminal.execute_command('coer')
        assert str(len(terminal.desk.pending())) in result


class TestRadioReality:
    """microwave(1) and satellite(1) say true things about the plant."""

    def test_microwave_names_the_system_and_the_band(self, terminal):
        result = terminal.execute_command('microwave')
        assert 'TH-3' in result and 'GHz' in result

    def test_microwave_explains_a_fade(self, terminal):
        assert 'fade' in terminal.execute_command('microwave').lower()

    def test_satellite_says_there_are_none_and_why(self, terminal):
        result = terminal.execute_command('satellite')
        assert '22,300' in result
        assert 'echo suppressor' in result

    def test_5ess_says_there_is_not_one_here(self, terminal):
        result = terminal.execute_command('5ess')
        assert 'NOT IN THIS OFFICE' in result
        assert '1982' in result


class TestCustomerRecords:
    """custdb(1) and the systems dbquery(1) points at."""

    def a_number(self, terminal):
        """A telephone number that has a record on this position."""
        return sorted(terminal.lmos_console.lmos.line_cards())[0]

    def test_it_lists_the_lines_with_records(self, terminal):
        result = terminal.execute_command('custdb')
        assert self.a_number(terminal) in result

    def test_a_record_carries_the_outside_plant(self, terminal):
        result = terminal.execute_command(f'custdb {self.a_number(terminal)}')
        assert 'Cable and pair' in result
        assert 'Line equipment' in result

    def test_the_record_is_the_card_lmos_holds(self, terminal):
        """
        custdb must not build its own view of a line. It prints the card the
        report desk already carries, and these two drifting apart would be
        the same bug this project has spent its life removing.
        """
        number = self.a_number(terminal)
        card = terminal.lmos_console.lmos.find_card(number)
        result = terminal.execute_command(f'custdb {number}')
        assert card.record.name in result
        assert card.record.address in result
        assert str(card.record.cable) in result
        assert card.record.clli in result

    def test_the_trouble_history_is_the_reports(self, terminal):
        number = self.a_number(terminal)
        card = terminal.lmos_console.lmos.find_card(number)
        result = terminal.execute_command(f'custdb {number}')
        for report in card.history:
            assert report.number in result

    def test_an_unknown_number_is_reported(self, terminal):
        assert 'no record' in terminal.execute_command('custdb 555-0000')

    def test_dbquery_lists_the_systems(self, terminal):
        result = terminal.execute_command('dbquery')
        assert 'lmos' in result and 'cosmos' in result and 'tirks' in result

    def test_dbquery_puts_a_number_to_lmos(self, terminal):
        number = self.a_number(terminal)
        assert (terminal.execute_command(f'dbquery lmos {number}')
                == terminal.execute_command(f'custdb {number}'))

    def test_a_bare_number_is_taken_as_a_line(self, terminal):
        number = self.a_number(terminal)
        assert 'CUSTOMER LINE RECORD' in terminal.execute_command(
            f'dbquery {number}')

    def test_an_unknown_system_is_reported(self, terminal):
        assert 'no such system' in terminal.execute_command('dbquery nonsense')


class TestProvisioning:
    """provision(1), which is what makes the plant change."""

    def a_number(self, terminal):
        return sorted(terminal.lmos_console.lmos.line_cards())[0]

    def test_it_lists_the_order_types(self, terminal):
        result = terminal.execute_command('provision')
        assert 'new' in result and 'restore' in result

    def test_an_order_gets_a_number_and_a_due_date(self, terminal):
        result = terminal.execute_command(
            f'provision change {self.a_number(terminal)}')
        assert 'SERVICE ORDER SO-' in result
        assert 'next working day' in result

    def test_the_due_date_is_never_a_weekend(self, terminal):
        result = terminal.execute_command(
            f'provision change {self.a_number(terminal)}')
        due = [line for line in result.split('\n') if 'Due ' in line][0]
        assert 'Sat' not in due and 'Sun' not in due

    def test_an_order_against_a_working_line_shows_the_plant(self, terminal):
        result = terminal.execute_command(
            f'provision move {self.a_number(terminal)}')
        assert 'Cable' in result

    def test_a_change_wants_a_line_that_is_there(self, terminal):
        assert 'no working line' in terminal.execute_command(
            'provision change 555-0000')

    def test_new_service_does_not(self, terminal):
        assert 'SERVICE ORDER' in terminal.execute_command(
            'provision new 555-0000')

    def test_an_unknown_type_is_reported(self, terminal):
        assert 'not an order type' in terminal.execute_command(
            'provision nonsense 555-0000')

    def test_orders_are_numbered_in_sequence(self, terminal):
        number = self.a_number(terminal)
        first = terminal.execute_command(f'provision change {number}')
        second = terminal.execute_command(f'provision change {number}')
        assert '-001' in first and '-002' in second


class TestTraining:
    """training(1), which reads the career record rather than inventing one."""

    def test_it_reports_every_qualification(self, terminal):
        from bell_system.progression import QUALIFICATIONS
        result = terminal.execute_command('training')
        for qualification in QUALIFICATIONS:
            assert qualification.key in result

    def test_a_fully_qualified_operator_is_signed_off_for_all(self, terminal):
        result = terminal.execute_command('training')
        assert 'signed off' in result
        assert 'wants' not in result

    def test_a_new_operator_is_told_what_is_short(self, raw_terminal):
        result = raw_terminal.execute_command('training')
        assert 'wants' in result or 'ready' in result

    def test_a_named_qualification_lists_what_it_opens(self, terminal):
        from bell_system.progression import QUALIFICATIONS_BY_KEY
        result = terminal.execute_command('training trunk')
        for command in QUALIFICATIONS_BY_KEY['trunk'].unlocks:
            assert command in result

    def test_what_it_says_a_qualification_opens_is_what_it_opens(self, terminal):
        """
        training reads the qualification records. If it ever starts keeping
        its own list, this is what notices.
        """
        from bell_system.progression import QUALIFICATIONS
        for qualification in QUALIFICATIONS:
            result = terminal.execute_command(f'training {qualification.key}')
            assert qualification.description.split('.')[0] in result
            for command in qualification.unlocks:
                assert command in result


class TestCollect:
    """collect(1), which explains why a room full of people existed."""

    def test_it_names_the_call_types_that_need_a_person(self, terminal):
        result = terminal.execute_command('collect')
        assert 'Collect' in result and 'Third number' in result

    def test_it_gives_the_reason(self, terminal):
        assert 'promise to pay' in terminal.execute_command('collect')

    def test_the_queue_reaches_the_operator_position(self, terminal):
        assert terminal.execute_command('collect queue').strip()
