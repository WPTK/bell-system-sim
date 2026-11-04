"""
The trouble report loop, loop measurement, test lines and the other craft.

These test the work itself: that a report carries a hidden electrical truth,
that measuring it tells you what that truth is, that dispatching to the wrong
place costs you, and that closing it dishonestly brings it back.
"""

import random
from datetime import datetime, timedelta

import pytest

from bell_system.data.consequences import Late
from bell_system.data.testlines import LIMITS, TEST_LINES, TEST_LINE_ORDER
from bell_system.data.trouble import (
    DISPATCH_FORCES,
    DISPOSITIONS,
    FAULTS,
    NSPMP_WEIGHTS,
    REAL_FAULTS,
    REPORT_SYMPTOMS,
)
from bell_system.loop_testing import (
    CABLE_UF_PER_MILE,
    LOOP_OHMS_PER_MILE,
    RESISTANCE_DESIGN_LIMIT_OHMS,
    access_test_line,
    design_note,
    distance_to_open,
    measure_loop,
)
from bell_system.npc import CHANNEL_NAMES, CRAFT, Switchroom, render
from bell_system.reports import ReportDesk, valid_force

SHIFT_START = datetime(1983, 11, 14, 8, 0)


@pytest.fixture
def desk():
    """A report desk with a fixed generator, so a test can reason about it."""
    return ReportDesk('201', '555', 'NWRKNJ02', random.Random(1983))


class TestFaultData:
    """The electrical vocabulary a close out is written against."""

    def test_every_real_fault_has_a_signature_and_a_force(self):
        for code in REAL_FAULTS:
            fault = FAULTS[code]
            assert fault.mlt_signature
            assert fault.dispatch

    def test_every_fault_has_a_customer_symptom(self):
        for code in FAULTS:
            assert REPORT_SYMPTOMS[code]

    def test_no_trouble_found_is_not_a_real_fault(self):
        assert 'NONE' not in REAL_FAULTS

    def test_the_published_dispositions_are_five_and_eight(self):
        assert sorted(DISPOSITIONS) == [5, 8]

    def test_the_measurement_weights_sum_to_one_hundred(self):
        assert sum(NSPMP_WEIGHTS.values()) == 100

    def test_every_dispatch_a_fault_names_is_a_real_force(self):
        for fault in FAULTS.values():
            if fault.dispatch in ('None', 'None - customer contact'):
                continue
            assert fault.dispatch in DISPATCH_FORCES


class TestReportDesk:
    """The pending list and the rules for working it."""

    def test_a_shift_opens_with_a_backlog(self, desk):
        opened = desk.open_shift(SHIFT_START)
        assert opened
        assert len(desk.pending()) == len(opened)

    def test_the_board_is_ordered_by_commitment(self, desk):
        desk.open_shift(SHIFT_START)
        for _ in range(4):
            desk.receive(SHIFT_START)
        due = [report.due_in() for report in desk.pending()]
        assert due == sorted(due)

    def test_out_of_service_gets_the_shorter_commitment(self, desk):
        dead = desk.receive(SHIFT_START, fault='OPEN')
        noisy = desk.receive(SHIFT_START, fault='GROUND')
        assert dead.commitment < noisy.commitment

    def test_a_backlog_pushes_new_commitments_out(self, desk):
        first = desk.receive(SHIFT_START, fault='GROUND')
        for _ in range(5):
            desk.receive(SHIFT_START, fault='GROUND')
        last = desk.receive(SHIFT_START, fault='GROUND')
        assert last.commitment > first.commitment

    def test_slack_only_ever_extends_a_commitment(self, desk):
        tight = desk.receive(SHIFT_START, slack_minutes=0, fault='OPEN')
        loose = desk.receive(SHIFT_START, slack_minutes=90, fault='OPEN')
        assert loose.commitment > tight.commitment

    @pytest.mark.parametrize('token_of', [
        lambda report: report.number,
        lambda report: report.number.replace('TR-', ''),
        lambda report: report.record.telephone_number,
        lambda report: '1',
    ])
    def test_a_report_answers_to_every_way_of_naming_it(self, desk, token_of):
        report = desk.receive(SHIFT_START)
        assert desk.find(token_of(report)) is report

    def test_an_unknown_token_finds_nothing(self, desk):
        desk.receive(SHIFT_START)
        assert desk.find('TR-99999') is None


class TestWorkingAReport:
    """Measuring, dispatching and closing."""

    def test_measuring_marks_the_report_and_costs_time(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        before = report.minutes_spent
        desk.record_test(report, 'measured')
        assert report.tested
        assert report.minutes_spent > before

    def test_the_right_force_finds_and_clears_it(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        result = desk.dispatch(report, FAULTS['GROUND'].dispatch)
        assert 'located and cleared' in result
        assert report.field_finding == 'GROUND'

    def test_the_wrong_force_finds_nothing_and_costs_time(self, desk):
        """
        A named person drives out to the wrong place, which is the point of
        the penalty: it is somebody's morning, not an abstraction.
        """
        report = desk.receive(SHIFT_START, fault='GROUND')
        before = report.minutes_spent
        result = desk.dispatch(report, 'Central office', 0)
        assert 'found nothing at their end' in result
        assert report.field_finding is None
        assert report.crew is not None
        assert report.minutes_spent > before

    def test_the_wrong_force_charges_the_drive_as_well(self, desk):
        report = desk.receive(SHIFT_START, fault='GROUND')
        before = report.minutes_spent
        desk.dispatch(report, 'Central office', 0)
        assert report.minutes_spent - before > report.travel_minutes

    def test_naming_the_right_fault_on_code_five_is_correct(self, desk):
        report = desk.receive(SHIFT_START, fault='SHORT')
        assert desk.close(report, 5, 'SHORT', SHIFT_START)

    def test_naming_the_wrong_fault_on_code_five_is_not(self, desk):
        report = desk.receive(SHIFT_START, fault='SHORT')
        assert not desk.close(report, 5, 'OPEN', SHIFT_START)

    def test_code_eight_on_a_clean_line_is_correct(self, desk):
        report = desk.receive(SHIFT_START, fault='NONE')
        assert desk.close(report, 8, None, SHIFT_START)

    def test_code_eight_on_a_faulty_line_is_not(self, desk):
        report = desk.receive(SHIFT_START, fault='WET')
        assert not desk.close(report, 8, None, SHIFT_START)

    def test_a_closed_report_leaves_the_pending_list(self, desk):
        report = desk.receive(SHIFT_START, fault='NONE')
        desk.close(report, 8, None, SHIFT_START)
        assert report not in desk.pending()
        assert report in desk.closed()

    def test_a_wrongly_closed_faulty_line_can_come_back(self, desk):
        report = desk.receive(SHIFT_START, fault='WET')
        desk.close(report, 8, None, SHIFT_START)
        assert desk.should_repeat(report, chance=1.0)
        repeat = desk.repeat(report, SHIFT_START)
        assert repeat.repeat_of == report.number
        assert repeat.record is report.record

    def test_a_correctly_closed_report_never_comes_back(self, desk):
        report = desk.receive(SHIFT_START, fault='WET')
        desk.close(report, 5, 'WET', SHIFT_START)
        assert not desk.should_repeat(report, chance=1.0)

    def test_a_wrong_call_on_a_clean_line_does_not_come_back(self, desk):
        report = desk.receive(SHIFT_START, fault='NONE')
        desk.close(report, 5, 'OPEN', SHIFT_START)
        assert not desk.should_repeat(report, chance=1.0)

    def test_a_commitment_passed_by_the_close_itself_is_missed(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        report.spend(100_000)
        desk.close(report, 8, None, SHIFT_START)
        assert report.missed_commitment

    def test_a_commitment_kept_is_not_missed(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        desk.close(report, 8, None, SHIFT_START)
        assert not report.missed_commitment

    def test_ageing_flags_a_report_once(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        assert desk.age(100_000, 0) == [report]
        assert desk.age(100, 0) == []

    @pytest.mark.parametrize('word,expected', [
        ('osp', 'Outside plant'),
        ('central', 'Central office'),
        ('cable', 'Cable repair'),
        ('co', 'Central office'),
    ])
    def test_a_force_answers_to_a_craftspersons_shorthand(self, word, expected):
        assert valid_force(word) == expected

    def test_a_word_that_is_not_a_force_resolves_to_nothing(self):
        assert valid_force('the fire brigade') is None


class TestLoopMeasurement:
    """What mechanised loop testing reports, and whether it can be trusted."""

    def test_one_line_always_measures_the_same_way(self):
        first = measure_loop('201-555-0100', 'GROUND')
        second = measure_loop('201-555-0100', 'GROUND')
        assert first == second

    def test_an_open_shows_no_station_termination(self):
        measurement = measure_loop('201-555-0100', 'OPEN')
        assert not measurement.station_termination
        assert measurement.loop_resistance_ohms is None

    def test_a_short_reads_near_zero_across_the_pair(self):
        measurement = measure_loop('201-555-0100', 'SHORT')
        assert measurement.tip_ring_ohms <= 90

    def test_a_ground_pulls_one_conductor_down_only(self):
        measurement = measure_loop('201-555-0100', 'GROUND')
        low = min(measurement.tip_ground_ohms, measurement.ring_ground_ohms)
        high = max(measurement.tip_ground_ohms, measurement.ring_ground_ohms)
        assert low < 5_000
        assert high > 100_000

    def test_foreign_emf_shows_voltage_with_no_battery_applied(self):
        measurement = measure_loop('201-555-0100', 'FEMF')
        assert measurement.dc_volts > 0 or measurement.ac_volts > 0

    def test_a_clean_line_reads_high_insulation_everywhere(self):
        measurement = measure_loop('201-555-0100', 'NONE')
        assert measurement.tip_ring_ohms > 100_000
        assert measurement.tip_ground_ohms > 100_000
        assert measurement.ring_ground_ohms > 100_000

    def test_a_receiver_off_hook_shows_a_closed_loop_drawing_current(self):
        measurement = measure_loop('201-555-0100', 'ROH')
        assert measurement.station_termination
        assert measurement.loop_current_ma > 20

    def test_capacitance_converts_to_distance_at_the_documented_rate(self):
        assert distance_to_open(CABLE_UF_PER_MILE) == pytest.approx(1.0)
        assert distance_to_open(2 * CABLE_UF_PER_MILE) == pytest.approx(2.0)

    def test_loop_resistance_follows_the_documented_rate(self):
        measurement = measure_loop('201-555-0100', 'NONE')
        expected = round(measurement.distance_miles * LOOP_OHMS_PER_MILE)
        assert measurement.loop_resistance_ohms == expected

    def test_the_rate_puts_the_design_limit_near_three_miles(self):
        miles = RESISTANCE_DESIGN_LIMIT_OHMS / LOOP_OHMS_PER_MILE
        assert 2.8 < miles < 3.2

    def test_the_system_withholds_the_fault_when_asked_to(self):
        named = measure_loop('201-555-0100', 'CROSS', name_fault=True)
        silent = measure_loop('201-555-0100', 'CROSS', name_fault=False)
        assert named.suspected == 'CROSS'
        assert silent.suspected is None

    def test_the_design_note_names_the_right_rule_for_the_length(self):
        assert '1300 ohms' in design_note(900, 12.0)
        assert 'H88' in design_note(1400, 22.0)
        assert 'digital loop carrier' in design_note(1400, 30.0)

    def test_an_open_pair_has_no_loop_resistance_to_judge(self):
        assert 'cannot be read' in design_note(None, 12.0)


class TestTestLines:
    """The far-end test line series and what it returns."""

    def test_the_attested_series_is_present(self):
        for code in ('100', '102', '105'):
            assert TEST_LINES[code].attested

    def test_every_ordered_code_exists(self):
        for code in TEST_LINE_ORDER:
            assert code in TEST_LINES

    def test_the_102_returns_loss_only(self):
        result = access_test_line('102', 'TG-001')
        assert result.loss_db is not None
        assert result.noise_dbrnc is None
        assert result.slope_db is None

    def test_the_100_adds_noise(self):
        result = access_test_line('100', 'TG-001')
        assert result.loss_db is not None
        assert result.noise_dbrnc is not None

    def test_the_105_returns_the_full_picture(self):
        result = access_test_line('105', 'TG-001')
        assert result.loss_db is not None
        assert result.noise_dbrnc is not None
        assert result.noise_with_tone_dbrnc is not None
        assert result.slope_db is not None

    def test_a_healthy_circuit_passes(self):
        result = access_test_line('105', 'TG-001', degraded=False)
        assert result.passed
        assert result.loss_db <= LIMITS.loss_high_db

    def test_a_degraded_circuit_fails_and_says_why(self):
        result = access_test_line('105', 'TG-001', degraded=True)
        assert not result.passed
        assert result.notes

    def test_the_balance_test_line_reports_return_loss(self):
        result = access_test_line('BAL', 'TG-001')
        assert any('return loss' in note.lower() for note in result.notes)

    def test_an_unknown_code_returns_nothing(self):
        assert access_test_line('999', 'TG-001') is None


class TestSwitchroom:
    """The other craft, and the channels they reach you on."""

    def test_every_channel_has_senders_who_exist(self):
        from bell_system.npc import CHANNEL_SENDERS
        for channel, senders in CHANNEL_SENDERS.items():
            assert channel in CHANNEL_NAMES
            for login in senders:
                assert login in CRAFT

    def test_mail_accumulates_and_reading_empties_it(self):
        room = Switchroom(random.Random(4))
        room.qualification_notice(SHIFT_START, 'Loop and Station', ('mlt',))
        assert len(room.unread()) == 1
        assert len(room.take_mail()) == 1
        assert room.unread() == []

    def test_write_renders_in_the_seventh_edition_form(self):
        room = Switchroom(random.Random(4))
        message = room.assignment(
            SHIFT_START, 'TR-00001', '201-555-0100', 'No dial tone', '16:00')
        rendered = render(message, 'stamp')
        assert rendered.startswith('\nMessage from mreyes tty')
        assert rendered.rstrip().endswith('EOT')

    def test_the_order_wire_names_where_it_came_from(self):
        room = Switchroom(random.Random(4))
        message = room.field_call(SHIFT_START, 'TR-00001', 'cleared')
        assert 'ORDER WIRE' in render(message, 'stamp')

    def test_the_teletype_prints_without_a_sender_banner(self):
        room = Switchroom(random.Random(4))
        for _ in range(60):
            message = room.chatter(SHIFT_START)
            if message and message.channel == 'teletype':
                assert 'MAINTENANCE TTY' in render(message, 'stamp')
                return
        pytest.skip('no teletype traffic drawn in this run')

    def test_the_frame_answers_for_office_dispatches(self):
        room = Switchroom(random.Random(4))
        message = room.field_call(
            SHIFT_START, 'TR-00001', 'cleared', force='Central office')
        assert message.sender == 'rjohnson'

    def test_a_repeated_line_is_held_back(self):
        room = Switchroom(random.Random(4))
        first = room.chatter(SHIFT_START)
        assert first is not None
        # The same line must not come round again immediately.
        for _ in range(20):
            again = room.chatter(SHIFT_START)
            if again is not None:
                assert again.lines != first.lines
                return


class TestReportCommands:
    """The loop as a player works it at the terminal."""

    def test_the_board_renders_with_pending_work(self, terminal):
        result = terminal.execute_command('report')
        assert 'Repair Service Bureau' in result
        assert 'Service index' in result

    def test_a_report_shows_its_line_record(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'report show {report.number}')
        assert report.record.telephone_number in result
        assert report.record.cable_pair() in result
        assert 'Commitment' in result

    def test_measuring_records_against_the_report(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'mlt {report.number}')
        assert 'MECHANISED LOOP TEST' in result
        assert 'INSULATION RESISTANCE' in result
        assert report.tested

    def test_the_measurement_matches_what_is_on_the_line(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='SHORT')
        result = terminal.execute_command(f'mlt {report.number}')
        assert 'Near zero resistance tip to ring' in result

    def test_dispatching_reports_back_from_the_field(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='GROUND')
        result = terminal.execute_command(
            f'report dispatch {report.number} outside')
        assert 'Outside plant' in result

    def test_closing_correctly_moves_the_career(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='CROSS')
        before = terminal.career.reports_correct
        result = terminal.execute_command(
            f'report close {report.number} 5 CROSS')
        assert 'matches what was on the line' in result
        assert terminal.career.reports_correct == before + 1

    def test_closing_wrongly_says_what_was_actually_there(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        result = terminal.execute_command(f'report close {report.number} 8')
        assert 'wet cable' in result.lower()
        assert terminal.career.reports_wrong == 1

    def test_code_five_without_a_fault_is_refused(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'report close {report.number} 5')
        assert 'Name what you found' in result
        assert report.status != 'CLOSED'

    def test_an_invented_fault_code_is_refused(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(
            f'report close {report.number} 5 GREMLINS')
        assert 'not a trouble condition' in result

    def test_an_unpublished_disposition_is_refused(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'report close {report.number} 3')
        assert 'not a disposition' in result

    def test_craft_refuses_a_close_on_an_unmeasured_line(self, terminal):
        terminal.execute_command('set game.difficulty craft')
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'report close {report.number} 8')
        assert 'has not been measured' in result
        assert report.status != 'CLOSED'

    def test_craft_accepts_the_close_once_it_is_measured(self, terminal):
        terminal.execute_command('set game.difficulty craft')
        report = terminal.desk.receive(terminal.clock.now(), fault='NONE')
        terminal.execute_command(f'mlt {report.number}')
        result = terminal.execute_command(f'report close {report.number} 8')
        assert 'closed, code 8' in result

    def test_craft_will_not_name_the_fault_for_you(self, terminal):
        terminal.execute_command('set game.difficulty craft')
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        result = terminal.execute_command(f'mlt {report.number}')
        assert 'will not name a condition' in result
        assert 'System reads this as' not in result
        assert 'Dispatch to:' not in result

    def test_the_fault_reference_lists_every_condition(self, terminal):
        result = terminal.execute_command('report faults')
        for fault in FAULTS.values():
            assert fault.code in result

    def test_a_call_back_gets_more_from_the_customer(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='CROSS')
        before = report.minutes_spent
        result = terminal.execute_command(f'report callback {report.number}')
        assert 'hear two other people' in result
        assert report.minutes_spent > before

    def test_closed_work_is_listed_with_the_truth(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='NONE')
        terminal.execute_command(f'report close {report.number} 8')
        result = terminal.execute_command('report closed')
        assert report.number in result
        assert 'correct' in result

    def test_an_unknown_option_is_reported(self, terminal):
        assert 'unknown option' in terminal.execute_command('report frobnicate')


class TestBoardCommands:
    """The test board, test lines and supervision."""

    def test_the_board_shows_what_is_on_it(self, terminal):
        result = terminal.execute_command('testboard')
        assert 'Test Board' in result
        assert '1004 Hz' in result

    def test_the_board_measures_a_loop(self, terminal):
        report = terminal.desk.pending()[0]
        result = terminal.execute_command(f'testboard loop {report.number}')
        assert 'MECHANISED LOOP TEST' in result

    def test_supervision_reads_the_sf_tone(self, terminal):
        group = next(iter(terminal.trunk_groups))
        result = terminal.execute_command(f'testboard supervision {group}')
        assert '2600 Hz' in result
        assert 'Trunk state' in result

    def test_supervision_on_an_unknown_group_is_reported(self, terminal):
        result = terminal.execute_command('testboard supervision TG-NOPE')
        assert 'no trunk group' in result

    def test_the_test_line_series_lists_the_attested_types(self, terminal):
        result = terminal.execute_command('testline')
        assert '100-type' in result
        assert '105-type' in result
        assert 'Remote office test line' in result

    def test_a_test_line_measures_a_circuit(self, terminal):
        group = next(iter(terminal.trunk_groups))
        result = terminal.execute_command(f'testline 105 {group}')
        assert 'Loss at 1004 Hz' in result
        assert 'Gain slope' in result

    def test_an_unknown_test_line_is_reported(self, terminal):
        assert 'no 999 test line' in terminal.execute_command('testline 999 X')


class TestMessagingCommands:
    """write, mail and the order wire at the terminal."""

    def test_write_lists_who_can_be_reached(self, terminal):
        result = terminal.execute_command('write')
        for login in ('rjohnson', 'mreyes', 'gvasquez'):
            assert login in result

    def test_write_gets_an_answer(self, terminal):
        result = terminal.execute_command('write gvasquez what do you read')
        assert 'Message from gvasquez' in result
        assert 'EOT' in result

    def test_writing_to_a_stranger_is_reported(self, terminal):
        assert 'not logged on' in terminal.execute_command('write nobody hello')

    def test_carot_does_not_take_messages(self, terminal):
        assert 'test system' in terminal.execute_command('write carot hello')

    def test_who_lists_the_same_people_write_reaches(self, terminal):
        listing = terminal.execute_command('who')
        for login in CRAFT:
            assert login in listing

    def test_mail_is_empty_until_something_arrives(self, terminal):
        assert terminal.execute_command('mail') == 'No mail.'

    def test_mail_delivers_a_qualification_sign_off(self, terminal):
        terminal.switchroom.qualification_notice(
            terminal.clock.now(), 'Main Distributing Frame', ('cosmos',))
        result = terminal.execute_command('mail')
        assert 'Main Distributing Frame' in result
        assert terminal.execute_command('mail') == 'No mail.'

    def test_the_order_wire_can_be_listened_to(self, terminal):
        result = terminal.execute_command('orderwire')
        assert 'Order wire' in result

    def test_the_order_wire_raises_the_control_centre(self, terminal):
        result = terminal.execute_command('orderwire scc')
        assert 'SCC' in result

    def test_calling_something_in_is_logged(self, terminal):
        result = terminal.execute_command('orderwire report cable wet at third')
        assert 'cable wet at third' in result
        assert 'SCC copies' in result


class TestAmbience:
    """Traffic from the rest of the building, and turning it off."""

    def test_ambience_off_leaves_output_alone(self, terminal):
        terminal.settings.set('game.ambience', 'off')
        for _ in range(40):
            assert terminal.execute_command('pwd').strip() == \
                terminal.current_directory

    def test_ambience_off_files_nothing_in_the_mailbox(self, terminal,
                                                       monkeypatch):
        # The roll that would have made somebody speak, forced, and the
        # one who speaks forced onto the mail channel, so this is not a
        # matter of luck: the craft are not asked at all.
        monkeypatch.setattr(random, 'random', lambda: 0.0)
        monkeypatch.setattr(
            terminal, '_craft_interruption',
            lambda difficulty: terminal.switchroom.qualification_notice(
                terminal.clock.now(), 'Chatter', ('pwd',)))
        for _ in range(10):
            terminal.execute_command('pwd')
        assert terminal.execute_command('mail') == 'No mail.'

    def test_ambience_on_eventually_says_something(self, raw_terminal):
        raw_terminal.settings.set('game.difficulty', 'craft')
        raw_terminal.career.set_difficulty('craft')
        for _ in range(200):
            if len(raw_terminal.execute_command('pwd').splitlines()) > 1:
                return
        pytest.fail('the other craft never said anything in 200 commands')

    def test_a_held_message_lands_a_few_commands_later(self, terminal):
        terminal.settings.set('game.ambience', 'on')
        message = terminal.switchroom.chase(
            terminal.clock.now(),
            Late('TR-00001', '201-555-0100', '1FR', False, '08:30'))
        terminal._queue_message(message, after=2)
        first = terminal.execute_command('pwd')
        assert 'TR-00001' not in first
        second = terminal.execute_command('pwd')
        assert 'TR-00001' in second


class TestShiftHandoff:
    """Signing off, and what carries to the next shift."""

    def test_the_handoff_reports_the_board(self, terminal):
        result = terminal.execute_command('handoff')
        assert 'REPAIR SERVICE BUREAU' in result
        assert 'Service Index' in result

    def test_relieving_banks_the_index_and_advances_the_shift(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='NONE')
        terminal.execute_command(f'report close {report.number} 8')
        before = terminal.career.shift
        result = terminal.execute_command('handoff relieve')
        assert 'Relieved' in result
        assert terminal.career.shift == before + 1
        assert terminal.career.index_history

    def test_pending_work_carries_forward(self, terminal):
        carried = {report.number for report in terminal.desk.pending()}
        terminal.execute_command('handoff relieve')
        still = {report.number for report in terminal.desk.pending()}
        assert carried <= still


class TestTimeAccounting:
    """Working time charged against a commitment."""

    def test_a_fresh_report_has_time_remaining(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        assert report.due_in() > timedelta(0)
        assert not report.overdue()

    def test_spending_past_the_commitment_makes_it_overdue(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        report.spend(100_000)
        assert report.overdue()
        assert report.age_label().startswith('-')

    def test_the_label_reads_as_hours_and_minutes(self, desk):
        report = desk.receive(SHIFT_START, fault='OPEN')
        assert ':' in report.age_label()


class TestTestCalls:
    """Placing a call through the network and reading every stage of it."""

    def test_the_usage_screen_lists_the_offices(self, terminal):
        result = terminal.execute_command('testcall')
        assert 'Test Call' in result
        for code in list(terminal.toll_network.offices)[:3]:
            assert code in result

    def test_a_call_shows_seizure_address_and_route(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        assert 'SF tone removed' in result
        assert 'KP' in result and 'ST' in result
        assert 'ROUTE ADVANCE' in result
        assert 'Trunks in tandem' in result

    def test_the_address_outpulsed_is_only_mf_digits(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        line = next(row for row in result.splitlines()
                    if 'Address outpulsed' in row)
        symbols = line.split('Address outpulsed')[1].split()
        assert symbols[0] == 'KP'
        assert symbols[-1] == 'ST'
        assert all(symbol.isdigit() for symbol in symbols[1:-1])

    def test_a_start_signal_is_always_named(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        assert any(word in result
                   for word in ('wink start', 'delay dial', 'immediate start'))

    def test_the_same_office_answers_the_same_way_every_time(self, terminal):
        first = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        second = terminal.execute_command('testcall EO-NYC-01 EO-CHI-01')
        start = 'Start signal'
        assert next(r for r in first.splitlines() if start in r) == \
            next(r for r in second.splitlines() if start in r)

    def test_terminating_on_a_test_line_measures_the_connection(
            self, terminal, monkeypatch):
        """Final groups block one call in a hundred, so take the roll away."""
        monkeypatch.setattr('bell_system.routing.FINAL_GROUP_BLOCKING', 0.0)
        monkeypatch.setattr('bell_system.routing.HIGH_USAGE_BLOCKING', 0.0)
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01 105')
        assert 'MEASUREMENT' in result
        assert 'Loss at 1004 Hz' in result
        assert 'Gain slope' in result

    def test_a_completed_call_releases_the_trunk(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        if 'COMPLETED' in result:
            assert 'SF tone restored' in result

    def test_an_unknown_office_is_reported(self, terminal):
        assert 'no office' in terminal.execute_command('testcall XX YY')

    def test_a_call_to_itself_is_refused(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-NYC-01')
        assert 'two different offices' in result

    def test_an_unknown_test_line_is_reported(self, terminal):
        result = terminal.execute_command('testcall EO-NYC-01 EO-BOS-01 999')
        assert 'no 999 test line' in result

    def test_a_test_call_needs_the_trunk_sign_off(self, raw_terminal):
        result = raw_terminal.execute_command('testcall EO-NYC-01 EO-BOS-01')
        assert 'not signed off' in result
        assert 'Interoffice Trunks' in result


class TestTicketAssignment:
    """The switching control centre putting a ticket on you by name."""

    def test_an_assignment_names_the_ticket_and_the_office(self, terminal):
        ticket = terminal.active_tickets[0]
        label = terminal._office_label(ticket['affected_office'])
        message = terminal.switchroom.ticket_assignment(
            terminal.clock.now(), ticket['id'], ticket['title'],
            ticket['priority'], label)
        rendered = render(message, 'stamp')
        assert ticket['id'] in rendered
        assert label in rendered
        assert 'trouble detail' in rendered

    def test_a_critical_ticket_says_everything_else_waits(self, terminal):
        message = terminal.switchroom.ticket_assignment(
            terminal.clock.now(), 'SW-0001', 'Marker failure',
            'CRITICAL', 'NWRKNJ02')
        assert 'Everything else waits' in render(message, 'stamp')

    def test_an_assignment_reaches_the_position_it_was_given_to(self, terminal):
        terminal.settings.set('game.ambience', 'on')
        terminal.career.set_difficulty('craft')
        for _ in range(400):
            terminal.execute_command('pwd')
            assigned = [ticket for ticket in terminal.active_tickets
                        if 'this position' in ticket.get('assigned_team', '')]
            if assigned:
                assert assigned[0]['id'] in terminal._assigned_tickets
                return
        pytest.skip('no ticket was assigned in this run')

    def test_a_ticket_is_never_assigned_twice(self, terminal):
        terminal.settings.set('game.ambience', 'on')
        terminal.career.set_difficulty('craft')
        for _ in range(200):
            terminal.execute_command('pwd')
        assert len(terminal._assigned_tickets) == len(
            set(terminal._assigned_tickets))


class TestShiftClock:
    """The working shift, and the events that come due on it."""

    def test_a_shift_starts_at_zero(self, terminal):
        assert terminal.shift_minutes == 0
        assert terminal.shift_time() == '0:00'

    def test_every_command_costs_a_minute_of_the_shift(self, terminal):
        before = terminal.shift_minutes
        for _ in range(10):
            terminal.execute_command('pwd')
        assert terminal.shift_minutes == before + 10

    def test_desk_work_is_charged_to_the_shift(self, terminal):
        report = terminal.desk.pending()[0]
        before = terminal.shift_minutes
        terminal.execute_command(f'mlt {report.number}')
        assert terminal.shift_minutes > before + 1

    def test_the_field_forces_repair_is_not_your_time(self, terminal):
        """
        A test desk works the next report while the field works this one.

        Charging the repair interval to the working shift burned a whole
        shift in three dispatches.
        """
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        wanted = FAULTS['WET'].dispatch
        before = terminal.shift_minutes
        terminal.execute_command(f'report dispatch {report.number} {wanted}')
        assert report.minutes_spent > 100
        assert terminal.shift_minutes - before < 40

    def test_desk_time_never_exceeds_elapsed_time(self, terminal):
        for report in terminal.desk.pending():
            terminal.execute_command(f'mlt {report.number}')
        for report in terminal.desk.reports.values():
            assert report.desk_minutes <= report.minutes_spent

    def test_events_come_due_as_the_shift_is_worked(self, terminal):
        assert terminal._fired_events == set()
        terminal.shift_minutes = 400
        terminal._fire_due_events()
        assert terminal._fired_events

    def test_an_event_only_fires_once(self, terminal):
        terminal.shift_minutes = 400
        terminal._fire_due_events()
        fired = set(terminal._fired_events)
        terminal._fire_due_events()
        assert terminal._fired_events == fired

    def test_a_pending_event_becomes_active_when_it_fires(self, terminal):
        pending = [event for event in terminal.shift_events
                   if event.get('status') == 'PENDING']
        terminal.shift_minutes = 24 * 60
        terminal._fire_due_events()
        for event in pending:
            assert event['status'] == 'ACTIVE'

    def test_a_refused_dispatch_leaves_a_measured_report_tested(
            self, terminal):
        """#61 finding 2: the board dropped TESTED back to PEND."""
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=8)
        outside = [held for held in terminal.desk.pending()
                   if held.record.fault in ('OPEN', 'SHORT', 'GROUND',
                                            'CROSS', 'FEMF')]
        first, second = outside[0], outside[1]
        terminal.execute_command(f'mlt {first.number}')
        terminal.execute_command(f'mlt {second.number}')
        terminal.execute_command(f'report dispatch {first.number} outside')
        refused = terminal.execute_command(
            f'report dispatch {second.number} outside')
        assert 'Nobody free' in refused
        board = terminal.execute_command('report')
        row = next(line for line in board.splitlines()
                   if second.number in line)
        assert 'TESTED' in row and 'PEND' not in row

    def test_the_tour_ends_at_eight_hours_and_relief_takes_it(self, terminal):
        tour = terminal.career.shift
        terminal.shift_minutes = 479
        out = terminal.execute_command('report')
        assert 'That is eight hours' in out and 'Relieved.' in out
        assert terminal.career.shift == tour + 1
        assert terminal.shift_minutes < 10

    def test_it_ends_with_ambience_off_too(self, terminal):
        # The fixture's terminal is quiet. Time being up is not ambience.
        terminal.shift_minutes = 479
        assert 'Relieved.' in terminal.execute_command('report')

    def test_a_sleep_past_the_end_ends_the_tour_after_the_sleep(
            self, terminal):
        tour = terminal.career.shift
        out = terminal.execute_command('sleep 36000')
        assert 'That is eight hours' in out and 'Relieved.' in out
        assert terminal.career.shift == tour + 1

    def test_a_long_command_is_finished_before_the_handoff(self, terminal):
        """The command that crosses 8:00 is not cut short; then relief."""
        tour = terminal.career.shift
        terminal.shift_minutes = 450
        held = terminal.desk.customers()[0]
        held.spend(120, desk=120)
        out = terminal.execute_command(f'report {held.number}')
        assert held.number in out
        assert out.index(held.number) < out.index('That is eight hours')
        assert terminal.career.shift == tour + 1

    def test_the_handoff_is_not_repeated(self, terminal):
        terminal.shift_minutes = 479
        terminal.execute_command('report')
        tour = terminal.career.shift
        for command in ('report', 'shift', 'sleep 30'):
            assert 'eight hours' not in terminal.execute_command(command)
        assert terminal.career.shift == tour

    def test_the_shift_screen_never_runs_past_the_end(self, terminal):
        terminal.shift_minutes = 480 + 75
        terminal.execute_command('report')
        assert 'Past the end' not in terminal.execute_command('shift')
        terminal.shift_minutes = 100
        assert 'Past the end' not in terminal.execute_command('shift')

    def test_a_save_made_past_the_end_hands_off_once_on_resume(
            self, terminal):
        from bell_system.terminal import BellSystemTerminal
        terminal.execute_command('report')
        tour = terminal.career.shift
        terminal.shift_minutes = 500
        terminal.save_shift()
        fresh = BellSystemTerminal()
        fresh.career.qualifications = list(terminal.career.qualifications)
        assert fresh.resumed and fresh.career.shift == tour
        assert 'Relieved.' in fresh.execute_command('report')
        assert fresh.career.shift == tour + 1
        assert 'eight hours' not in fresh.execute_command('report')
        assert fresh.career.shift == tour + 1

    def test_on_the_last_tour_the_end_is_the_career_and_only_once(
            self, terminal):
        from bell_system.clock import TOURS_TO_DIVESTITURE
        terminal.career.shift = TOURS_TO_DIVESTITURE
        terminal.career.save()
        terminal.clock.set_tour(terminal.career.shift)
        terminal.execute_command('report')
        terminal.shift_minutes = 479
        out = terminal.execute_command('report')
        assert 'That is eight hours' in out and terminal.career.finished
        assert 'eight hours' not in terminal.execute_command('report')

    def _last_tour(self, terminal):
        from bell_system.clock import TOURS_TO_DIVESTITURE
        terminal.career.shift = TOURS_TO_DIVESTITURE
        terminal.career.save()
        terminal.clock.set_tour(terminal.career.shift)
        terminal.execute_command('report')
        terminal.shift_minutes = 479

    def test_the_last_tour_time_up_is_one_coherent_scene(self, terminal):
        """
        No relief comes on the last day, and the screen never says it does.

        The wire chief says the eight hours are up and that nobody relieves
        the position, on the day watch, with no evening word and no
        'relieved' anywhere in it.
        """
        self._last_tour(terminal)
        out = terminal.execute_command('report')
        assert 'That is eight hours' in out
        assert 'no relief on the last day' in out
        for word in ('Relief is on the floor', 'Relieved', 'relieved',
                     'tonight', 'this evening', 'this morning',
                     'handing the position over'):
            assert word not in out, word

    def test_a_redirect_does_not_swallow_the_end_of_the_last_tour(
            self, terminal):
        self._last_tour(terminal)
        out = terminal.execute_command('report > board.txt')
        assert 'That is eight hours' in out and terminal.career.finished
        filed = terminal.execute_command('cat board.txt')
        assert 'That is eight hours' not in filed
        assert 'THE CAREER' not in filed

    def test_a_redirect_does_not_swallow_the_end_of_a_tour(self, terminal):
        tour = terminal.career.shift
        terminal.shift_minutes = 479
        out = terminal.execute_command('report > board.txt')
        assert 'That is eight hours' in out
        assert terminal.career.shift == tour + 1
        filed = terminal.execute_command('cat board.txt')
        assert 'That is eight hours' not in filed
        assert 'Relieved.' not in filed

    def test_a_pipe_or_tee_does_not_swallow_the_end_of_a_tour(self, terminal):
        for line in ('report | cat', 'report | tee board.txt'):
            tour = terminal.career.shift
            terminal.shift_minutes = 479
            out = terminal.execute_command(line)
            assert 'That is eight hours' in out, line
            assert terminal.career.shift == tour + 1, line
        assert 'That is eight hours' not in terminal.execute_command(
            'cat board.txt')

    def test_relieving_resets_the_shift_clock_and_schedule(self, terminal):
        terminal.shift_minutes = 400
        terminal._fire_due_events()
        assert terminal._fired_events
        terminal.execute_command('report')
        terminal.execute_command('handoff relieve')
        # The handoff command itself costs a minute of the new shift.
        assert terminal.shift_minutes < 5
        assert terminal._fired_events == set()

    def test_events_advance_even_with_ambience_off(self, terminal):
        terminal.settings.set('game.ambience', 'off')
        before = terminal.shift_minutes
        terminal.execute_command('pwd')
        assert terminal.shift_minutes > before

    def test_new_work_arrives_even_with_ambience_off(self, terminal):
        """
        Ambience governs whether anybody tells you, not whether it happens.

        An early return here once meant a quiet terminal never got another
        report as long as it ran.
        """
        terminal.settings.set('game.ambience', 'off')
        before = len(terminal.desk.reports)
        for _ in range(60):
            terminal.execute_command('pwd')
        assert len(terminal.desk.reports) > before

    def test_the_board_never_runs_away(self, terminal):
        from bell_system.reports import MAX_PENDING
        terminal.settings.set('game.ambience', 'off')
        for _ in range(300):
            terminal.execute_command('pwd')
        assert len(terminal.desk.pending()) <= MAX_PENDING
