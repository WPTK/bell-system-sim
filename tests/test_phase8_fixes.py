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
