"""
Phase 8 review fixes: what a line cleared by itself, a case across a
turnover, and the rest, each tested on a report or case the test builds.
"""

import pytest


def _alone(terminal, fault='GROUND', after=30):
    """The only report on the board, on a line that will clear by itself."""
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    report.clears_after = after
    terminal.desk.reports = {report.number: report}
    terminal.desk.order = [report.number]
    return report


class TestThePromptReadsWhatWasMeasured:
    """The standing prompt knows what the player saw, not what the line is."""

    def test_it_is_unchanged_when_the_line_clears(self, terminal):
        report = _alone(terminal)
        terminal.execute_command(f'mlt {report.number}')
        before = terminal.next_action()
        report.age(report.clears_at - report.minutes_spent + 5)
        assert report.record.fault == 'NONE'
        assert terminal.next_action() == before

    def test_it_changes_when_the_player_measures_again(self, terminal):
        report = _alone(terminal)
        terminal.execute_command(f'mlt {report.number}')
        before = terminal.next_action()
        report.age(report.clears_at - report.minutes_spent + 5)
        terminal.execute_command(f'mlt {report.number}')
        assert report.read_fault() == 'NONE'
        assert terminal.next_action() != before or report.read_fault() == 'NONE'

    def test_what_was_last_read_is_saved(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        report = _alone(terminal)
        terminal.execute_command(f'mlt {report.number}')
        report.age(report.clears_at - report.minutes_spent + 5)
        captured = json.loads(json.dumps(save.capture(terminal)))
        fresh = BellSystemTerminal()
        assert save.restore(fresh, captured)
        again = fresh.desk.reports[report.number]
        assert (again.last_read, again.cleared_alone) == ('GROUND', True)

    def test_a_save_from_before_loads(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        report = _alone(terminal)
        terminal.execute_command(f'mlt {report.number}')
        captured = json.loads(json.dumps(save.capture(terminal)))
        for entry in captured['board']['reports']:
            entry.pop('last_read', None)
            entry.pop('cleared_alone', None)
        fresh = BellSystemTerminal()
        assert save.restore(fresh, captured)
        assert fresh.desk.reports[report.number].last_read is None


def _marker_run(terminal):
    """Tour 9's marker case with every one of its reports on the board."""
    from bell_system.cases import MARKER_LEDGER  # noqa: F401
    terminal.career.shift = 9
    terminal._plant_case()
    terminal.desk.depth_limit = 40
    terminal.shift_minutes = 500
    terminal._case_events()
    case = terminal.desk.cases[0]
    return case, [terminal.desk.reports[n] for n in case.members]


class TestACaseAcrossATurnover:
    """A cause outlives the tour it began on while any of it is open."""

    def test_the_case_is_kept_while_a_report_of_it_is_open(self, terminal):
        case, members = _marker_run(terminal)
        terminal.career.shift = 10
        terminal._plant_case()
        assert case in terminal.desk.cases
        assert case.due == []

    def test_one_right_trip_still_clears_the_run_on_the_next_tour(
            self, terminal):
        case, members = _marker_run(terminal)
        terminal.career.shift = 10
        terminal._plant_case()
        terminal.execute_command(
            f'report dispatch {members[0].number} central office')
        assert case.cleared
        assert all(m.sheath_repaired for m in members[1:])

    def test_it_is_dropped_when_all_of_it_is_closed(self, terminal):
        case, members = _marker_run(terminal)
        for member in members:
            member.status = 'CLOSED'
        terminal.career.shift = 10
        terminal._plant_case()
        assert case not in terminal.desk.cases

    def test_a_save_from_before_cases_resumed_mid_tour_keeps_the_marker(
            self, terminal):
        import json
        from bell_system import save
        from bell_system.cases import MARKER_LEDGER
        from bell_system.terminal import BellSystemTerminal
        terminal.career.shift = 9
        captured = json.loads(json.dumps(save.capture(terminal)))
        captured['board'].pop('cases', None)
        fresh = BellSystemTerminal()
        fresh.career.shift = 9
        fresh._plant_case()
        assert save.restore(fresh, captured)
        assert MARKER_LEDGER not in fresh.career.beats_seen
        fresh.career.shift = 10
        fresh._plant_case()
        assert fresh.desk.cases and fresh.desk.cases[0].kind == 'marker'
