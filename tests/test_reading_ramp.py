"""
The reading ramp: fun mode names a fault for its first sightings and then
leaves the reading to the player.

Plan rows R3, C8 and C9. The count is Career.fault_sightings, per fault type,
and Difficulty.annotation_sightings says how many are annotated.
"""

import pytest

from bell_system.data.trouble import (
    FAULTS,
    FIRST_REPORT_SYMPTOMS,
    REPORT_SYMPTOMS,
)
from bell_system.loop_testing import (
    STAGE_CREW,
    STAGE_NOTE,
    STAGE_NUMBERS,
    reading_stage,
)
from bell_system.cable import binder_of
from bell_system.progression import Career


class TestTheStageRule:
    def test_four_sightings_fade_to_numbers(self):
        stages = [reading_stage(n, 4) for n in range(1, 7)]
        assert stages == [STAGE_NOTE, STAGE_NOTE, STAGE_CREW, STAGE_CREW,
                          STAGE_NUMBERS, STAGE_NUMBERS]

    def test_no_annotation_is_numbers_from_the_start(self):
        assert reading_stage(1, 0) == STAGE_NUMBERS

    def test_an_odd_count_gives_the_extra_sighting_to_the_note(self):
        assert [reading_stage(n, 3) for n in (1, 2, 3, 4)] == [
            STAGE_NOTE, STAGE_NOTE, STAGE_CREW, STAGE_NUMBERS]


def _measure(terminal, fault='SHORT'):
    """Receive a new report with a fault and mlt it; return the output."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    return report, terminal.execute_command(f'mlt {report.number}')


class TestFunFadesPerFaultType:
    def test_sightings_one_and_two_name_the_fault_and_say_why(self, terminal):
        for _ in range(2):
            _, result = _measure(terminal)
            assert 'System reads this as: Short' in result
            assert 'Dispatch to: Outside plant' in result
            assert 'Note: ' in result

    def test_sightings_three_and_four_give_the_crew_class_only(
            self, terminal):
        for _ in range(2):
            _measure(terminal)
        for _ in range(2):
            _, result = _measure(terminal)
            assert 'Dispatch to: Outside plant' in result
            assert 'System reads this as' not in result
            assert 'Note: ' not in result

    def test_from_the_fifth_it_is_numbers_only(self, terminal):
        for _ in range(4):
            _measure(terminal)
        _, result = _measure(terminal)
        assert 'System reads this as' not in result
        assert 'Dispatch to' not in result
        assert 'Note: ' not in result
        assert 'INSULATION RESISTANCE' in result

    def test_the_count_is_for_each_fault_type(self, terminal):
        for _ in range(5):
            _measure(terminal, 'SHORT')
        _, result = _measure(terminal, 'OPEN')
        assert 'System reads this as: Open' in result
        assert terminal.career.fault_sightings == {'SHORT': 5, 'OPEN': 1}

    def test_measuring_a_report_again_is_not_another_sighting(
            self, terminal):
        report, first = _measure(terminal)
        again = terminal.execute_command(f'mlt {report.number}')
        assert terminal.career.fault_sightings == {'SHORT': 1}
        assert 'System reads this as' in first and 'System reads' in again

    def test_the_count_survives_a_restart(self, terminal):
        for _ in range(5):
            _measure(terminal)
        assert Career(terminal.career.path).fault_sightings == {'SHORT': 5}

    def test_the_sighting_of_a_report_survives_a_save(self, terminal):
        from bell_system.save import _report_in, _report_out
        report, _ = _measure(terminal)
        assert _report_in(_report_out(report)).sighting == 1

    def test_a_report_saved_before_sightings_loads(self, terminal):
        from bell_system.save import _report_in, _report_out
        report, _ = _measure(terminal)
        stored = _report_out(report)
        del stored['sighting']
        assert _report_in(stored).sighting is None


class TestAssists:
    def test_annotate_on_keeps_the_notes(self, terminal):
        terminal.execute_command('set assist.annotate on')
        for _ in range(6):
            _, result = _measure(terminal)
            assert 'System reads this as: Short' in result
            assert 'Note: ' in result

    def test_annotate_off_is_numbers_from_the_first(self, terminal):
        terminal.execute_command('set assist.annotate off')
        _, result = _measure(terminal)
        assert 'System reads this as' not in result
        assert 'Dispatch to' not in result

    def test_craft_shows_no_note(self, terminal):
        terminal.execute_command('set game.difficulty craft')
        _, result = _measure(terminal)
        assert 'System reads this as' not in result
        assert 'Dispatch to' not in result
        assert 'Note: ' not in result

    def test_craft_with_annotate_on_shows_the_notes(self, terminal):
        terminal.execute_command('set game.difficulty craft')
        terminal.execute_command('set assist.annotate fade')
        _, result = _measure(terminal)
        assert 'System reads this as: Short' in result

    def test_craft_sightings_count_towards_a_later_fun_career(
            self, terminal):
        terminal.execute_command('set game.difficulty craft')
        for _ in range(4):
            _measure(terminal)
        terminal.execute_command('set game.difficulty fun')
        _, result = _measure(terminal)
        assert 'Dispatch to' not in result


class TestACorrectDispatchStopsNamingTheFault:
    def _dispatch(self, terminal, report):
        terminal.shift_minutes += 900
        force = FAULTS[report.record.fault].dispatch.lower()
        return terminal.execute_command(
            f'report dispatch {report.number} {force}')

    @pytest.mark.parametrize('code', ['OPEN', 'SHORT', 'GROUND', 'CROSS',
                                      'FEMF', 'FCG', 'CO_EQUIP', 'WET'])
    def test_the_fifth_dispatch_does_not_say_what_was_cleared(
            self, terminal, code):
        terminal.career.fault_sightings[code] = 4
        report = terminal.desk.receive(terminal.clock.now(), fault=code)
        result = self._dispatch(terminal, report).lower()
        assert report.field_finding == code
        assert FAULTS[code].name.lower() not in result
        assert 'cleared' in result or 'resealed' in result
        assert 'water' not in result

    @pytest.mark.parametrize('code', ['OPEN', 'GROUND', 'WET'])
    def test_the_first_dispatch_names_it(self, terminal, code):
        report = terminal.desk.receive(terminal.clock.now(), fault=code)
        result = self._dispatch(terminal, report).lower()
        assert FAULTS[code].name.lower() in result or 'water' in result

    def test_a_dispatch_that_found_nothing_is_not_a_sighting(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        terminal.shift_minutes += 900
        terminal.execute_command(f'report dispatch {report.number} station')
        assert report.field_finding is None
        assert terminal.career.fault_sightings == {}

    def test_measuring_then_dispatching_is_one_sighting(self, terminal):
        report, _ = _measure(terminal, 'OPEN')
        self._dispatch(terminal, report)
        assert terminal.career.fault_sightings == {'OPEN': 1}

    def test_the_crew_call_in_follows_the_count_too(self, terminal):
        terminal.career.fault_sightings['GROUND'] = 4
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        self._dispatch(terminal, report)
        queued = ' '.join(str(m) for m in terminal._queued_messages).lower()
        assert 'ground' not in queued


class TestTheFirstReportTeaches:
    def test_each_first_report_symptom_belongs_to_a_different_fault(self):
        for fault, symptom in FIRST_REPORT_SYMPTOMS.items():
            assert symptom not in REPORT_SYMPTOMS[fault], fault

    def test_a_new_career_opens_on_a_report_that_disagrees_with_its_pair(
            self, raw_terminal):
        [report] = raw_terminal.desk.pending()
        assert report.symptom == FIRST_REPORT_SYMPTOMS[report.record.fault]
        assert report.symptom not in REPORT_SYMPTOMS[report.record.fault]

    def test_a_working_shift_deals_ordinary_reports(self, terminal):
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=8)
        for report in terminal.desk.pending():
            assert report.symptom in REPORT_SYMPTOMS[report.record.fault]

    def test_the_customer_says_the_rest_on_a_callback(self, raw_terminal):
        raw_terminal.settings.set('game.ambience', 'off')
        [report] = raw_terminal.desk.pending()
        result = raw_terminal.execute_command('report callback 1')
        assert report.record.name in result


class TestHallorenSendsThemToTheCustomerFirst:
    def _first_tour(self, terminal):
        terminal.settings.set('game.ambience', 'off')
        assert terminal.first_tour()
        return terminal

    def test_the_board_nudge_names_report_callback(self, raw_terminal):
        terminal = self._first_tour(raw_terminal)
        result = terminal.execute_command('report')
        assert 'Message from ehalloran' in result
        assert "report callback 1" in result
        assert 'mlt 1' not in result

    def test_the_callback_nudge_names_mlt(self, raw_terminal):
        terminal = self._first_tour(raw_terminal)
        terminal.execute_command('report')
        result = terminal.execute_command('report callback 1')
        assert 'Message from ehalloran' in result
        assert "mlt 1" in result

    def test_a_callback_before_the_board_does_not_repeat_the_board_nudge(
            self, raw_terminal):
        terminal = self._first_tour(raw_terminal)
        result = terminal.execute_command('report callback 1')
        assert result.count('Message from ehalloran') == 1
        assert 'That is the board' not in result

    def test_help_points_at_the_callback_until_it_is_made(self, raw_terminal):
        terminal = self._first_tour(raw_terminal)
        assert terminal.next_action().command == 'report callback 1' or \
            terminal.next_action().command.startswith('report callback')
        terminal.execute_command('report callback 1')
        assert terminal.next_action().command.startswith('mlt')

    def test_a_player_who_measures_first_is_not_sent_back(self, raw_terminal):
        terminal = self._first_tour(raw_terminal)
        terminal.execute_command('mlt 1')
        assert terminal.next_action().step != 'callback'


def _alone(terminal, report):
    """Drop whatever else the building has sent, so the board is this one."""
    terminal.desk.reports = {report.number: report}
    terminal.desk.order[:] = [report.number]


def _dispatched(terminal, code, sightings):
    """A report for a fault seen ``sightings`` times already, cleared."""
    terminal.career.fault_sightings[code] = sightings
    report = terminal.desk.receive(terminal.clock.now(), fault=code)
    terminal.shift_minutes += 900
    force = FAULTS[code].dispatch.lower()
    terminal.execute_command(f'report dispatch {report.number} {force}')
    _alone(terminal, report)
    return report


class TestNothingElseGivesTheFaultAway:
    """Once mlt stops naming a fault, neither does the rest of the desk."""

    def test_next_does_not_type_the_code_to_close_with(self, terminal):
        report = _dispatched(terminal, 'GROUND', 4)
        action = terminal.next_action()
        assert action.step == 'close'
        assert action.command == f'report close {report.number} 5 <fault>'

    def test_next_types_the_code_while_the_fault_is_still_named(
            self, terminal):
        report = _dispatched(terminal, 'GROUND', 0)
        assert terminal.next_action().command == (
            f'report close {report.number} 5 GROUND')

    def test_the_report_file_does_not_print_the_code(self, terminal):
        report = _dispatched(terminal, 'GROUND', 4)
        shown = terminal.execute_command(f'cat /usr/lmos/{report.number}')
        assert 'field found' in shown
        assert 'GROUND' not in shown

    def test_the_report_file_prints_it_while_the_fault_is_named(
            self, terminal):
        report = _dispatched(terminal, 'GROUND', 0)
        shown = terminal.execute_command(f'cat /usr/lmos/{report.number}')
        assert 'field found GROUND' in shown

    def _measured(self, terminal, sightings):
        terminal.career.fault_sightings['GROUND'] = sightings
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        terminal.execute_command(f'mlt {report.number}')
        _alone(terminal, report)
        return report

    def test_next_does_not_pick_the_crew_at_the_numbers_stage(self, terminal):
        report = self._measured(terminal, 4)
        action = terminal.next_action()
        assert action.step == 'dispatch'
        assert action.command == f'report show {report.number}'

    def test_next_still_picks_the_crew_while_mlt_names_it(self, terminal):
        report = self._measured(terminal, 0)
        assert terminal.next_action().command == (
            f'report dispatch {report.number} outside plant')


class TestOneSpliceIsOneSighting:
    def test_pairs_repaired_by_another_reports_trip_are_not_sightings(
            self, terminal):
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        made = [terminal.desk.receive(terminal.clock.now(), fault='WET')
                for _ in range(12)]
        first = made[0]
        group = [r for r in made
                 if r.record.cable == first.record.cable
                 and binder_of(r.record.pair) == binder_of(first.record.pair)]
        assert len(group) >= 3
        terminal.shift_minutes += 900
        terminal.execute_command(
            f'report dispatch {group[0].number} cable repair')
        assert [r.sheath_repaired for r in group[1:]] == [True] * (
            len(group) - 1)
        # Sending a crew to a pair that is already dry sends nobody.
        for other in group[1:]:
            terminal.execute_command(
                f'report dispatch {other.number} cable repair')
        assert terminal.career.fault_sightings == {'WET': 1}


class TestTheDifficultySentence:
    def test_craft_says_mlt_stops_naming_the_fault(self, terminal):
        result = terminal.execute_command('set game.difficulty craft')
        assert 'no longer name the fault' in result

    def test_craft_with_annotate_on_does_not_say_it(self, terminal):
        terminal.execute_command('set assist.annotate on')
        result = terminal.execute_command('set game.difficulty craft')
        assert 'no longer name the fault' not in result
        assert 'cannot be closed until the loop has been measured' in result
