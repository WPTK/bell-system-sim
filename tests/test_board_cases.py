"""
Phase 8: trouble that comes and goes, and a board that has causes in it.

Each test builds the report it needs. None depends on which reports a board
happens to be dealt, and the transient ones set the clock on the report they
build instead of hoping a draw produced one.
"""

import random
from datetime import datetime

import pytest

from bell_system.reports import (
    TRANSIENT_FAULTS,
    TRANSIENT_WINDOW,
    ReportDesk,
    transient_after,
)

SHIFT_START = datetime(1983, 11, 14, 8, 0)


@pytest.fixture
def desk():
    """A report desk with a fixed generator, so a test can reason about it."""
    return ReportDesk('201', '555', 'NWRKNJ02', random.Random(1983))


def _transient(terminal, fault='GROUND', after=30):
    """A report on a line whose trouble goes by itself, ``after`` minutes on."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    report.clears_after = after
    return report


class TestTransientTrouble:
    """A9: read faulty at the first test, clean an hour later."""

    def test_which_reports_are_transient_is_the_numbers_to_say(self):
        """Asked twice it answers the same, whoever else drew from the dice."""
        for index in range(200):
            number = f"TR-{index:05d}"
            assert transient_after(number, 'GROUND') == transient_after(
                number, 'GROUND')

    def test_only_the_faults_that_come_and_go_can_be_transient(self):
        for index in range(300):
            number = f"TR-{index:05d}"
            for fault in ('OPEN', 'SHORT', 'WET', 'FCG', 'CO_EQUIP', 'NONE'):
                assert transient_after(number, fault) is None

    def test_some_are_and_most_are_not(self):
        found = [transient_after(f"TR-{index:05d}", 'CROSS')
                 for index in range(400)]
        kinds = [value for value in found if value is not None]
        assert 40 < len(kinds) < 200
        low, high = TRANSIENT_WINDOW
        assert all(low <= value <= high for value in kinds)
        assert set(TRANSIENT_FAULTS) == {'GROUND', 'CROSS', 'FEMF'}

    def test_dealing_a_board_takes_nothing_from_the_dice(self):
        """The same seed deals the same board with or without the feature."""
        first = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        second = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        opened = [r.record.fault for r in first.open_shift(SHIFT_START)]
        again = [r.record.fault for r in second.open_shift(SHIFT_START)]
        assert opened == again

    def test_a_forced_condition_is_never_transient(self, desk):
        for fault in TRANSIENT_FAULTS:
            report = desk.receive(SHIFT_START, fault=fault)
            assert report.clears_after is None

    def test_the_clock_starts_at_the_first_test_and_not_before(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        report.clears_after = 30
        report.age(500)
        assert report.record.fault == 'GROUND'
        assert report.clears_at is None
        desk.record_test(report, 'mlt')
        assert report.clears_at == report.minutes_spent - 4 + 30

    def test_it_reads_faulty_at_first_and_clean_an_hour_later(self, terminal):
        report = _transient(terminal)
        first = terminal.execute_command(f'mlt {report.number}')
        assert 'Every reading was within limits' not in first
        terminal.execute_command('sleep 3600')
        again = terminal.execute_command(f'mlt {report.number}')
        assert 'Every reading was within limits' in again
        assert report.record.fault == 'NONE'

    def test_closing_it_no_trouble_after_the_retest_is_not_a_repeat(
            self, terminal):
        report = _transient(terminal)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command('sleep 3600')
        terminal.execute_command(f'mlt {report.number}')
        before = terminal.desk.repeat_count
        result = terminal.execute_command(f'report close {report.number} 8')
        assert 'matches what was on the line' in result
        assert terminal.desk.repeat_count == before
        assert report.correct

    def test_calling_it_trouble_found_after_it_cleared_is_wrong(
            self, terminal):
        report = _transient(terminal)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command('sleep 3600')
        result = terminal.execute_command(
            f'report close {report.number} 5 GROUND')
        assert report.correct is False
        assert 'Nothing was actually wrong' in result

    def test_a_crew_that_reached_it_while_it_was_there_cleared_it(
            self, terminal):
        report = _transient(terminal, after=20)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} outside')
        assert report.record.fault == 'GROUND'
        terminal.execute_command('sleep 3600')
        assert report.record.fault == 'GROUND'
        result = terminal.execute_command(
            f'report close {report.number} 5 GROUND')
        assert report.correct, result

    def test_a_closed_line_stops_changing(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        report.clears_after = 20
        desk.record_test(report, 'mlt')
        desk.close(report, 5, 'GROUND', SHIFT_START)
        report.age(600)
        assert report.record.fault == 'GROUND'

    def test_the_clock_survives_a_save(self, terminal):
        from bell_system.save import _report_in, _report_out
        report = _transient(terminal, after=45)
        terminal.desk.record_test(report, 'mlt')
        restored = _report_in(_report_out(report))
        assert (restored.clears_after, restored.clears_at) == (
            report.clears_after, report.clears_at)

    def test_a_report_saved_before_this_is_the_usual_kind(self, terminal):
        from bell_system.save import _report_in, _report_out
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        written = _report_out(report)
        del written['clears_after'], written['clears_at']
        restored = _report_in(written)
        assert restored.clears_after is None
        assert restored.clears_at is None

    def test_reading_the_board_does_not_start_the_clock(self, terminal):
        report = _transient(terminal)
        terminal.execute_command('report')
        terminal.execute_command(f'report show {report.number}')
        assert report.clears_at is None


def _wet(terminal):
    """A wet report, and the cable and binder group its pair is in."""
    from bell_system.cable import binder_of
    report = terminal.desk.receive(terminal.clock.now(), fault='WET')
    return report, f"{report.record.cable}/{binder_of(report.record.pair)}"


def _craft(terminal):
    terminal.execute_command('set assist.sections named')


class TestNamingTheSection:
    """C21: a splicer is told where, and a wrong group is a wrong trip."""

    def test_the_right_section_repairs(self, terminal):
        report, section = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {section}')
        assert 'resealed' in result
        assert report.field_finding == 'WET'

    def test_a_wrong_section_returns_the_crews_finding(self, terminal):
        report, section = _wet(terminal)
        cable, binder = section.split('/')
        wrong = f"{cable}/{(int(binder) % 24) + 1}"
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {wrong}')
        assert 'found it dry' in result
        assert 'resealed' not in result
        assert report.field_finding is None
        assert terminal.desk.plant.section_at(
            report.record.cable, report.record.pair) is not None

    def test_a_wrong_section_costs_the_wrong_trip(self, terminal):
        right, section = _wet(terminal)
        cable, binder = section.split('/')
        wrong = f"{cable}/{(int(binder) % 24) + 1}"
        before = right.minutes_spent
        terminal.execute_command(
            f'report dispatch {right.number} cable {wrong}')
        assert right.minutes_spent - before >= 45

    def test_the_old_form_still_works_in_fun(self, terminal):
        report, _ = _wet(terminal)
        terminal.execute_command('set assist.sections assumed')
        result = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'resealed' in result
        assert report.field_finding == 'WET'

    def test_craft_asks_where_and_charges_nothing(self, terminal):
        report, _ = _wet(terminal)
        _craft(terminal)
        before = report.desk_minutes
        result = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Which one?' in result
        assert report.desk_minutes == before
        assert report.dispatched_to is None

    def test_the_question_is_the_same_for_a_report_that_is_not_wet(
            self, terminal):
        wet, _ = _wet(terminal)
        dry = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        _craft(terminal)
        asked = [terminal.execute_command(
            f'report dispatch {report.number} cable') for report in (wet, dry)]
        assert asked[0] == asked[1]

    def test_another_force_is_not_asked_for_a_section(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        _craft(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} outside')
        assert 'Which one?' not in result

    def test_a_section_for_the_wrong_force_finds_the_same_dry_sheath(
            self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        cable = (report.record.cable % 80) + 1
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {cable}/3')
        assert 'found it dry' in result

    def test_a_group_with_other_water_is_cleared_for_its_own_reports(
            self, terminal):
        wet, section = _wet(terminal)
        other = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        result = terminal.execute_command(
            f'report dispatch {other.number} cable {section}')
        assert 'resealed' in result
        assert wet.sheath_repaired
        assert other.field_finding is None

    @pytest.mark.parametrize('token', ['81', '81/', '/8', '81/x', '81/8/2'])
    def test_something_that_is_not_a_section_is_refused(self, terminal, token):
        report, _ = _wet(terminal)
        if '/' not in token:
            return
        result = terminal.execute_command(
            f'report dispatch {report.number} cable {token}')
        assert 'not a cable and binder group' in result
        assert report.dispatched_to is None

    def test_there_is_no_binder_group_twenty_five(self, terminal):
        report, _ = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable 81/25')
        assert 'There is no group 25' in result

    def test_the_pair_form_is_not_a_section(self, terminal):
        """0081/0181 is the answer on the card; it is not accepted as one."""
        report, _ = _wet(terminal)
        result = terminal.execute_command(
            f'report dispatch {report.number} cable '
            f'{report.record.cable_pair()}')
        assert 'not a cable and binder group' in result \
            or 'There is no group' in result

    def test_the_setting_reads_off_the_profile_by_default(self, terminal):
        from bell_system.progression import DIFFICULTIES
        assert not DIFFICULTIES['fun'].section_required
        assert DIFFICULTIES['craft'].section_required


# -- A7: a cause behind several reports -----------------------------------

# What a case must never say about a report: the fault, the force that
# clears it, or how to close it. The crew's own finding is the one place
# that is allowed to, and it is tested where it is made.
FORBIDDEN = ('false cross', 'FCG', 'central office', 'outside plant',
             'code 5', 'code 8', 'trouble found', 'no trouble', 'ground',
             'cable repair')


def _tour(terminal, tour):
    """Move the session to a tour and let it decide what the tour holds."""
    terminal.career.shift = tour
    terminal._plant_case()
    return terminal.desk.cases[0] if terminal.desk.cases else None


def _run(terminal, tour=9):
    """Plant the tour's case and let every one of its reports arrive."""
    case = _tour(terminal, tour)
    terminal.desk.depth_limit = 40
    terminal.shift_minutes = 500
    notices = terminal._case_events()
    return case, [terminal.desk.reports[n] for n in case.members], notices


def _dig(terminal):
    """A cut cable with three reports already on the board."""
    from bell_system.cases import Case
    terminal.career.shift = 5
    terminal.desk.depth_limit = 40
    terminal.desk.cases = [Case('CASE-5-dig', 'dig', '0042', [30, 40, 50])]
    terminal.shift_minutes = 100
    terminal._case_events()
    case = terminal.desk.cases[0]
    return case, [terminal.desk.reports[n] for n in case.members]


class TestAPlan:
    """The plan is the tour's alone, and says how many and when."""

    def test_tour_nine_is_marker_two(self):
        from bell_system.cases import plan
        case = plan(9, [])
        assert case.kind == 'marker'
        assert 3 <= len(case.due) <= 5
        assert all(25 <= minute <= 170 for minute in case.due)

    def test_it_is_the_same_plan_every_time(self):
        from bell_system.cases import plan
        assert plan(9, []).out() == plan(9, []).out()

    def test_marker_two_fires_on_nine_or_ten_and_once(self):
        from bell_system.cases import MARKER_LEDGER, plan
        ledger = []
        fired = []
        for tour in range(1, 14):
            case = plan(tour, ledger)
            if case and case.kind == 'marker':
                fired.append(tour)
                ledger.append(MARKER_LEDGER)
        assert fired == [9]

    def test_tour_ten_has_it_if_nine_never_did(self):
        from bell_system.cases import plan
        assert plan(10, []).kind == 'marker'

    def test_the_early_tours_have_none(self):
        from bell_system.cases import plan
        assert all(plan(tour, []) is None for tour in (1, 2, 3))

    def test_a_planted_cause_is_written_in_the_ledger(self, terminal):
        from bell_system.cases import MARKER_LEDGER
        _tour(terminal, 9)
        assert MARKER_LEDGER in terminal.career.beats_seen
        later = _tour(terminal, 10)
        assert later is None or later.kind != 'marker'

    def test_planting_does_not_deal_a_report(self, terminal):
        before = len(terminal.desk.reports)
        _tour(terminal, 9)
        assert len(terminal.desk.reports) == before


class TestTheRunOfReports:
    """A7: three to five reports, one cause, and the board says so."""

    def test_three_to_five_reports_arrive(self, terminal):
        case, members, notices = _run(terminal)
        assert 3 <= len(members) <= 5
        assert case.due == []

    def test_none_arrive_before_their_minute(self, terminal):
        case = _tour(terminal, 9)
        terminal.shift_minutes = min(case.due) - 1
        assert terminal._case_events() == []
        assert case.members == []

    def test_the_lines_share_a_frame(self, terminal):
        case, members, _ = _run(terminal)
        frames = {r.record.line_equipment.rsplit('-', 2)[0] for r in members}
        assert frames == {case.where}

    def test_a_dig_shares_a_cable_and_no_pair(self, terminal):
        _, members = _dig(terminal)
        assert {r.record.cable for r in members} == {42}
        assert len({r.record.pair for r in members}) == len(members)

    def test_each_comes_in_as_an_assignment(self, terminal):
        _, members, notices = _run(terminal)
        assigned = [m for m in notices if m.kind == 'assignment']
        assert len(assigned) == len(members)

    def test_whoever_is_nearest_says_so_once_at_the_third(self, terminal):
        _, _, notices = _run(terminal)
        notes = [m for m in notices if m.kind == 'case']
        assert len(notes) == 1 and notes[0].sender == 'rjohnson'
        assert terminal._case_events() == []

    def test_a_full_board_holds_the_rest_back(self, terminal):
        case = _tour(terminal, 9)
        terminal.desk.depth_limit = len(terminal.desk.pending())
        terminal.shift_minutes = 500
        terminal._case_events()
        assert case.members == [] and case.due
        terminal.desk.depth_limit += 40
        terminal._case_events()
        assert case.due == []

    def test_report_show_says_see_also(self, terminal):
        _, members, _ = _run(terminal)
        shown = terminal.execute_command(f'report show {members[0].number}')
        assert 'See also' in shown
        for other in members[1:]:
            assert other.number in shown
        assert 'line link frame' in shown

    def test_a_report_with_no_company_says_nothing(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        assert 'See also' not in terminal.execute_command(
            f'report show {report.number}')

    def test_reading_it_changes_nothing(self, terminal):
        from bell_system import save
        _, members, _ = _run(terminal)
        before = save.capture(terminal)['board']['cases']
        for report in members:
            terminal.execute_command(f'report show {report.number}')
        assert save.capture(terminal)['board']['cases'] == before

    def test_nothing_it_says_names_a_fault_a_force_or_a_code(self, terminal):
        case, members, notices = _run(terminal)
        said = '\n'.join(' '.join(m.lines) for m in notices
                         if m.kind in ('assignment', 'case'))
        for report in members:
            shown = terminal.execute_command(f'report show {report.number}')
            said += shown.split('See also')[-1].split('MEASUREMENTS')[0]
        for word in FORBIDDEN:
            assert word.lower() not in said.lower(), word


class TestOneActionClearsThem:
    """A7: the crew that clears the cause has cleared every report in it."""

    def _clear(self, terminal):
        case, members, _ = _run(terminal)
        result = terminal.execute_command(
            f'report dispatch {members[0].number} central office')
        return case, members, result

    def test_the_rest_are_repaired_and_need_only_a_close(self, terminal):
        case, members, _ = self._clear(terminal)
        assert case.cleared
        for other in members[1:]:
            assert other.sheath_repaired
            assert other.field_finding == 'FCG'
            assert other.dispatched_to is None

    def test_a_second_crew_is_not_sent(self, terminal):
        _, members, _ = self._clear(terminal)
        result = terminal.execute_command(
            f'report dispatch {members[1].number} central office')
        assert 'Nobody needs to go' in result
        assert members[1].dispatched_to is None

    def test_the_crew_says_what_it_found(self, terminal):
        _, _, result = self._clear(terminal)
        assert 'can be closed without a further dispatch' in result

    def test_a_crew_that_names_nothing_names_nothing(self, terminal):
        _, members, _ = _run(terminal)
        found, _ = terminal.desk.send_crew(
            members[0], 'Central office', 0, name_fault=False)
        assert 'Marker' not in found
        assert 'can be closed without a further dispatch' in found

    def test_a_crew_that_names_it_names_the_marker(self, terminal):
        _, members, _ = _run(terminal)
        found, _ = terminal.desk.send_crew(
            members[0], 'Central office', 0, name_fault=True)
        assert 'Marker 2' in found

    def test_the_rest_close_as_found_and_are_right(self, terminal):
        _, members, _ = self._clear(terminal)
        for report in members:
            assert terminal.desk.close(
                report, 5, 'FCG', terminal.clock.now())
            assert report.correct

    def test_the_wrong_force_clears_nothing(self, terminal):
        case, members, _ = _run(terminal)
        terminal.execute_command(
            f'report dispatch {members[0].number} outside plant')
        assert not case.cleared
        assert not any(r.sheath_repaired for r in members)

    def test_reports_yet_to_come_do_not(self, terminal):
        case = _tour(terminal, 9)
        terminal.desk.depth_limit = 40
        terminal.shift_minutes = min(case.due)
        terminal._case_events()
        first = terminal.desk.reports[case.members[0]]
        terminal.execute_command(
            f'report dispatch {first.number} central office')
        assert case.cleared and case.due == []
        terminal.shift_minutes = 500
        # The tour's other thread, the toll counts, is not this case's.
        assert [m for m in terminal._case_events()
                if m.kind != 'fraud'] == []

    def test_the_cause_is_said_cleared_once(self, terminal):
        _, members, _ = self._clear(terminal)
        said = [m for _, m in terminal._queued_messages if m.kind == 'case']
        assert len(said) == 1 and said[0].sender == 'rjohnson'
        terminal.execute_command(
            f'report dispatch {members[1].number} central office')
        assert len([m for _, m in terminal._queued_messages
                    if m.kind == 'case']) == 1

    def test_a_dig_is_cleared_by_outside_plant(self, terminal):
        _, members = _dig(terminal)
        terminal.execute_command(
            f'report dispatch {members[0].number} outside plant')
        assert all(r.sheath_repaired for r in members[1:])


class TestACaseIsSaved:
    """A7: the run survives a quit, and a save from before has none."""

    def _fresh(self, terminal):
        from bell_system.terminal import BellSystemTerminal
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        return fresh

    def _written(self, terminal):
        import json
        from bell_system import save
        return json.loads(json.dumps(save.capture(terminal)))

    def test_it_round_trips(self, terminal):
        from bell_system import save
        case, members, _ = _run(terminal)
        fresh = self._fresh(terminal)
        assert save.restore(fresh, self._written(terminal))
        assert [c.out() for c in fresh.desk.cases] == [case.out()]
        assert fresh.desk.reports[members[0].number].case == case.ident

    def test_an_unarrived_report_is_still_to_come(self, terminal):
        from bell_system import save
        case = _tour(terminal, 9)
        fresh = self._fresh(terminal)
        assert save.restore(fresh, self._written(terminal))
        assert fresh.desk.cases[0].due == case.due

    def test_a_save_from_before_loads_with_none(self, terminal):
        from bell_system import save
        _run(terminal)
        captured = self._written(terminal)
        del captured['board']['cases']
        for entry in captured['board']['reports']:
            del entry['case']
        fresh = self._fresh(terminal)
        assert save.restore(fresh, captured)
        assert fresh.desk.cases == []
        assert all(r.case is None for r in fresh.desk.reports.values())

    def test_a_damaged_case_is_not_half_loaded(self, terminal):
        from bell_system import save
        _run(terminal)
        captured = self._written(terminal)
        captured['board']['cases'][0]['kind'] = 'nonsense'
        fresh = self._fresh(terminal)
        assert not save.restore(fresh, captured)


# -- A8: water that goes on leaking ----------------------------------------

def _plant_with_a_pair(seed=2):
    """A plant with one wet section that has reported once."""
    from bell_system.cable import CablePlant
    plant = CablePlant(random.Random(seed))
    cable, pair = plant.wet_pair(SHIFT_START)
    plant.attach(cable, pair, 'TR-00001')
    plant.sections[0].capacity = 25
    return plant


def _leaking_tour(terminal, tour=3):
    """Start a tour that opens with a sheath leaking and nobody told."""
    terminal.career.shift = tour
    terminal.career.reports_closed = 5
    terminal._plant_case()
    terminal.desk.depth_limit = 40
    return terminal.desk.plant.sections[0]


def _run_the_clock(terminal, until=480, step=10):
    """Move the tour on, and return what was said and when."""
    heard = []
    for _ in range(0, until, step):
        was = terminal.shift_minutes
        terminal.shift_minutes += step
        for piece in terminal._weather_events(was):
            heard.append((terminal.shift_minutes, piece))
    return heard


class TestTheSheathLeaks:
    """A8: unrepaired water takes a pair an hour, and the gauge knows first."""

    def test_an_unrepaired_sheath_takes_a_pair_an_hour(self):
        plant = _plant_with_a_pair()
        assert len(plant.leak(59, 0.0)) == 0
        assert len(plant.leak(1, 0.0)) == 1
        assert len(plant.leak(180, 0.0)) == 3

    def test_rain_makes_it_faster(self):
        dry = _plant_with_a_pair()
        wet = _plant_with_a_pair()
        assert len(wet.leak(60, 1.0)) == 4
        assert len(wet.leak(60, 1.0)) > len(dry.leak(60, 0.0))

    def test_how_much_it_takes_does_not_depend_on_chance(self):
        first = _plant_with_a_pair(seed=1)
        second = _plant_with_a_pair(seed=99)
        assert ([len(first.leak(7, 0.4)) for _ in range(60)]
                == [len(second.leak(7, 0.4)) for _ in range(60)])

    def test_it_stops_at_what_the_group_was_going_to_take(self):
        plant = _plant_with_a_pair()
        plant.sections[0].capacity = 3
        assert len(plant.leak(600, 1.0)) == 2

    def test_a_splicer_stops_it(self):
        plant = _plant_with_a_pair()
        plant.leak(30, 0.0)
        plant.repair(plant.sections[0], SHIFT_START)
        assert plant.leak(600, 1.0) == []

    def test_the_pressure_falls_with_time_as_well_as_with_pairs(self):
        plant = _plant_with_a_pair()
        before = plant.sections[0].psi
        plant.leak(60, 0.0)
        assert plant.sections[0].psi == pytest.approx(before - 1.5)


class TestThePressureAlarm:
    """A8: the contactor alarms before the first customer rings."""

    def test_a_leak_is_planted_without_a_report(self, terminal):
        section = _leaking_tour(terminal)
        assert section.latent and not section.pairs
        assert not [r for r in terminal.desk.reports.values()
                    if r.record.fault == 'WET']

    def test_it_alarms_before_the_first_report(self, terminal):
        _leaking_tour(terminal)
        heard = _run_the_clock(terminal)
        alarms = [at for at, text in heard if 'PRESSURE ALARM' in text]
        reports = [at for at, text in heard if 'on your board' in text]
        assert alarms and reports and alarms[0] < reports[0]

    def test_it_alarms_once(self, terminal):
        _leaking_tour(terminal)
        heard = _run_the_clock(terminal)
        assert len([1 for _, text in heard if 'PRESSURE ALARM' in text]) == 1

    def test_the_alarm_names_the_cable_and_not_the_group(self, terminal):
        section = _leaking_tour(terminal)
        heard = _run_the_clock(terminal)
        text = next(text for _, text in heard if 'PRESSURE ALARM' in text)
        assert f"CABLE {section.cable:04d}" in text
        assert 'binder' not in text.lower() and 'water' not in text.lower()

    def test_weather_shows_the_alarming_sheath_before_any_report(
            self, terminal):
        section = _leaking_tour(terminal)
        terminal.desk.plant.leak(110, 0.0)
        shown = terminal.execute_command('weather')
        assert 'pressure contactor alarming' in shown
        assert f"cable {section.cable} binder {section.binder}" in shown

    def test_the_water_is_in_the_group_the_alarm_was_for(self, terminal):
        section = _leaking_tour(terminal)
        heard = _run_the_clock(terminal)
        from bell_system.cable import binder_of
        landed = {(r.record.cable, binder_of(r.record.pair))
                  for r in terminal.desk.reports.values()
                  if r.record.fault == 'WET'}
        assert heard
        assert landed == {(section.cable, section.binder)}

    def test_a_splicer_sent_early_finds_it_and_nothing_follows(self, terminal):
        section = _leaking_tour(terminal)
        terminal.desk.plant.leak(110, 0.0)
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        result = terminal.execute_command(
            f'report dispatch {report.number} cable '
            f'{section.cable}/{section.binder}')
        assert 'resealed' in result
        heard = _run_the_clock(terminal)
        assert not [1 for _, text in heard if 'on your board' in text
                    and 'weak' in text]
        assert not [r for r in terminal.desk.reports.values()
                    if r.record.fault == 'WET']

    def test_the_board_does_not_draw_a_pair_from_an_unnoticed_leak(
            self, terminal):
        section = _leaking_tour(terminal)
        for _ in range(30):
            cable, pair = terminal.desk.plant.wet_pair(terminal.clock.now())
            assert not section.contains(cable, pair)

    def test_planting_one_deals_nothing_differently(self, terminal):
        terminal.career.shift = 3
        terminal.career.reports_closed = 5
        before = terminal.desk.rng.getstate()
        terminal._plant_case()
        assert terminal.desk.rng.getstate() == before

    def test_a_leak_and_its_clock_are_saved(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        section = _leaking_tour(terminal)
        terminal.desk.plant.leak(110, 0.0)
        section.alarmed = True
        captured = json.loads(json.dumps(save.capture(terminal)))
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        again = fresh.desk.plant.sections[0]
        assert (again.wet_minutes, again.credit, again.alarmed,
                again.psi) == (section.wet_minutes, section.credit, True,
                               section.psi)

    def test_a_save_from_before_loads(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        _leaking_tour(terminal)
        captured = json.loads(json.dumps(save.capture(terminal)))
        for entry in captured['plant']:
            for key in ('wet_minutes', 'credit', 'alarmed'):
                del entry[key]
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        assert fresh.desk.plant.sections[0].wet_minutes == 0


# -- C22: a callback with questions -----------------------------------------

def _called(terminal, fault, *topic, symptom=None):
    """Ring back a report on a line in ``fault`` and return what came back."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault,
                                   symptom=symptom)
    said = terminal.execute_command(
        'report callback ' + ' '.join([report.number, *topic]))
    return report, said


def _minutes_on(terminal, command):
    """What a command takes off a fresh report's clock, whatever its own."""
    report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
    before = report.minutes_spent
    terminal.execute_command(command.format(n=report.number))
    return report.minutes_spent - before


class TestCallbackQuestions:
    """C22: one question a call, each costing a callback, none naming it."""

    def test_each_question_costs_a_callback(self, terminal):
        from bell_system.reports import COST_CALLBACK
        idle = _minutes_on(terminal, 'report show {n}')
        for topic in ('start', 'others', 'hear'):
            cost = _minutes_on(terminal, 'report callback {n} ' + topic)
            assert cost - idle == COST_CALLBACK, topic
        assert _minutes_on(terminal, 'report callback {n}') - idle ==             COST_CALLBACK

    def test_an_answer_is_marked_with_the_question_asked(self, terminal):
        _, said = _called(terminal, 'WET', 'others')
        assert 'Asked: others' in said

    def test_the_bare_call_is_what_it_was(self, terminal):
        from bell_system.data.callbacks import GENERAL
        _, said = _called(terminal, 'GROUND')
        assert 'Asked' not in said
        assert GENERAL['GROUND'] in ' '.join(said.replace('"', '').split())

    def test_the_bare_call_says_what_else_can_be_asked(self, terminal):
        _, said = _called(terminal, 'OPEN')
        assert 'You could also ask: start, others, hear' in said

    def test_a_question_that_is_not_one_costs_nothing(self, terminal):
        idle = _minutes_on(terminal, 'report show {n}')
        assert _minutes_on(terminal, 'report callback {n} weather') == idle
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        said = terminal.execute_command(
            f'report callback {report.number} weather')
        assert 'no such question' in said and 'start, others, hear' in said

    def test_asking_a_closed_report_costs_nothing(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        report.status = 'CLOSED'
        said = terminal.execute_command(
            f'report callback {report.number} start')
        assert 'already closed' in said

    def test_no_answer_is_given_by_every_condition(self):
        from bell_system.data.callbacks import TOPICS
        for topic in TOPICS.values():
            assert len(set(topic.heard.values())) > 1, topic.key

    def test_every_condition_has_an_answer_to_every_question(self):
        from bell_system.data.callbacks import GENERAL, TOPICS
        for topic in TOPICS.values():
            assert set(topic.heard) == set(GENERAL), topic.key

    def test_the_true_condition_is_always_among_those_an_answer_fits(self):
        from bell_system.data.callbacks import GENERAL, TOPICS, asked, narrowed
        for key in TOPICS:
            for fault in GENERAL:
                said = asked(key, fault, 'Cannot call out')
                assert fault in narrowed(key, said), (key, fault)

    def test_a_question_narrows_the_set(self):
        from bell_system.data.callbacks import GENERAL, TOPICS, asked, narrowed
        for key in TOPICS:
            for fault in GENERAL:
                said = asked(key, fault, 'Cannot call out')
                assert len(narrowed(key, said)) < len(GENERAL), (key, fault)

    def test_two_questions_tell_more_than_one(self):
        """The set after two answers is smaller than after either alone."""
        from bell_system.data.callbacks import asked, narrowed
        fault = 'WET'
        one = set(narrowed('start', asked('start', fault, '')))
        two = one & set(narrowed('hear', asked('hear', fault, '')))
        assert fault in two and len(two) < len(one)

    def test_no_answer_names_a_fault_a_force_or_a_close_code(self):
        from bell_system.data.callbacks import CADENCE_HEARD, TOPICS
        from bell_system.data.trouble import FAULTS
        said = [text for topic in TOPICS.values()
                for text in topic.heard.values()]
        said += list(CADENCE_HEARD.values())
        names = {fault.name.lower() for fault in FAULTS.values()}
        names |= {fault.dispatch.lower() for fault in FAULTS.values()}
        for text in said:
            low = text.lower()
            assert not any(name in low for name in names), text
            assert 'close' not in low and 'code' not in low, text

    def test_a_call_about_calls_that_do_not_complete_is_heard_in_the_cadence(
            self, terminal):
        _, said = _called(terminal, 'CO_EQUIP', 'hear',
                          symptom='Calls do not complete')
        assert 'twice as fast' in ' '.join(said.split())
        _, said = _called(terminal, 'NONE', 'hear',
                          symptom='Calls do not complete')
        assert 'the slow one' in ' '.join(said.split())

    def test_the_same_words_are_said_on_any_report_of_the_same_kind(
            self, terminal):
        _, first = _called(terminal, 'WET', 'start')
        _, second = _called(terminal, 'WET', 'start')
        assert first.split('"')[1:-1] == second.split('"')[1:-1]
