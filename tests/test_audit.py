"""
The audit the divestiture memo promises, at the end of the last tour.

The memo of 1 November says open reports go to the operating company "with
your name on them" and that disposition codes "are audited after transfer".
Nothing ever audited anything: the ending was a ceremony. The audit gives a
verdict and changes what the wire chief says. It does not end the career
early. The thirteenth tour closes it on 31 December whatever the audit says.
"""

import re
from datetime import datetime

import pytest

from bell_system.clock import TOURS_TO_DIVESTITURE
from bell_system.npc import (
    AUDIT_EXCEPTIONS,
    AUDIT_FAILED,
    AUDIT_PASSED,
    Switchroom,
)
from bell_system.screens.turnover import audit

LABELS = ('Dispositions on record', 'matched the line', 'did not match',
          'Came back as repeats', 'Handed over open', 'Verdict')


def go_to_last_tour(terminal):
    """Put a constructed terminal on 31 December."""
    terminal.career.shift = TOURS_TO_DIVESTITURE
    terminal.career.save()
    terminal.clock.set_tour(terminal.career.shift)
    terminal.generate_shift_events()


def close_some(terminal, count):
    """Work and close real reports, so every counter has a history."""
    for report in terminal.desk.pending()[:count]:
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report close {report.number} 8')


def audit_block(text):
    """The audit's rows as a dict of label to value."""
    start = text.index('THE AUDIT')
    block = text[start:].split('\n\n')[0]
    found = {}
    for line in block.split('\n'):
        match = re.match(r'\s+(' + '|'.join(LABELS) + r')\s+(.*)$', line)
        if match:
            found[match.group(1)] = match.group(2).strip()
    return found


class TestTheVerdict:
    """Counts in, a verdict out."""

    def test_a_clean_record_passes(self):
        found = audit(40, 40, 0, [], 0)
        assert found.verdict == AUDIT_PASSED
        assert found.wrong == 0

    def test_a_few_misses_pass_with_no_finding(self):
        assert audit(40, 38, 1, [], 0).verdict == AUDIT_PASSED

    def test_more_than_a_tenth_wrong_is_a_finding(self):
        assert audit(40, 34, 2, [], 0).verdict == AUDIT_EXCEPTIONS

    def test_more_than_a_quarter_wrong_fails(self):
        found = audit(40, 28, 5, [], 0)
        assert found.verdict == AUDIT_FAILED
        assert '12 of 40' in ' '.join(found.reasons)

    def test_nothing_closed_fails(self):
        found = audit(0, 0, 0, ['R-0001', 'R-0002'], 0)
        assert found.verdict == AUDIT_FAILED
        assert 'Nothing was closed' in found.reasons[0]

    def test_open_reports_past_commitment_are_a_finding(self):
        found = audit(40, 40, 0, ['R-1', 'R-2', 'R-3'], 2)
        assert found.verdict == AUDIT_EXCEPTIONS
        assert '2 went over' in ' '.join(found.reasons)

    def test_handing_over_more_late_than_you_closed_fails(self):
        assert audit(3, 3, 0, ['a'] * 9, 9).verdict == AUDIT_FAILED

    def test_open_reports_alone_are_not_a_failure(self):
        """The memo asks for an honest handoff, not an empty board."""
        assert audit(30, 30, 0, ['a'] * 8, 0).verdict == AUDIT_PASSED


class TestTheAuditOnTheLastDay:
    """Tour 13 prints the audit, from the same counts as the rest."""

    def test_the_counts_match_report_closed_and_the_open_board(
            self, terminal):
        go_to_last_tour(terminal)
        close_some(terminal, 4)
        listing = terminal.execute_command('report closed')
        closed, correct, repeats = (int(n) for n in re.search(
            r'Closed (\d+), correct (\d+), repeats (\d+)', listing).groups())
        open_now = len(terminal.desk.pending())
        found = audit_block(terminal.execute_command('handoff relieve'))
        assert found['Dispositions on record'] == str(closed)
        assert found['matched the line'] == str(correct)
        assert found['did not match'] == str(closed - correct)
        assert found['Came back as repeats'] == str(repeats)
        assert found['Handed over open'].split(',')[0] == str(open_now)

    def test_a_zero_work_career_fails_it(self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert audit_block(out)['Verdict'] == AUDIT_FAILED
        assert 'Nothing was closed' in out

    def test_open_reports_go_over_with_the_name_on_them(self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        open_numbers = [r.number for r in terminal.desk.pending()]
        out = terminal.execute_command('handoff relieve')
        assert 'your name is on them' in out
        assert open_numbers[0] in out

    def test_a_failed_audit_never_ends_the_career_early(self, terminal):
        """The career ends on 31 December. It is neither shorter nor longer."""
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert audit_block(out)['Verdict'] == AUDIT_FAILED
        assert terminal.career.finished
        assert terminal.career.shift == TOURS_TO_DIVESTITURE
        assert 'THE CAREER' in out
        assert 'begins' not in out

    def test_no_audit_before_the_last_day(self, terminal):
        terminal.career.shift = TOURS_TO_DIVESTITURE - 1
        terminal.clock.set_tour(terminal.career.shift)
        terminal.execute_command('report')
        assert 'THE AUDIT' not in terminal.execute_command('handoff')
        out = terminal.execute_command('handoff relieve')
        assert 'THE AUDIT' not in out
        assert not terminal.career.finished

    def test_an_earlier_failing_record_ends_nothing_either(self, terminal):
        terminal.career.shift = 6
        terminal.career.reports_closed = 20
        terminal.career.reports_correct = 4
        terminal.clock.set_tour(6)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert not terminal.career.finished
        assert terminal.career.shift == 7
        assert 'THE AUDIT' not in out

    def test_the_handoff_looks_ahead_on_the_last_day(self, terminal):
        go_to_last_tour(terminal)
        record = terminal.execute_command('handoff')
        assert 'THE AUDIT, AS THINGS STAND' in record
        assert not terminal.career.finished

    def test_working_the_board_changes_the_look_ahead(self, terminal):
        go_to_last_tour(terminal)
        before = audit_block(terminal.execute_command('handoff'))
        close_some(terminal, 3)
        after = audit_block(terminal.execute_command('handoff'))
        assert before['Dispositions on record'] != after[
            'Dispositions on record']

    def test_the_audit_comes_between_the_career_and_the_wire_chief(
            self, terminal):
        go_to_last_tour(terminal)
        close_some(terminal, 2)
        out = terminal.execute_command('handoff relieve')
        assert (out.index('THE CAREER') < out.index('THE AUDIT')
                < out.index('ehalloran'))

    def test_a_second_visit_does_not_audit_again(self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        terminal.execute_command('handoff relieve')
        again = terminal.execute_command('handoff relieve')
        assert 'THE AUDIT' not in again
        assert 'relieve you twice' in again


class TestTheEpilogueReadsTheVerdict:
    """The audit changes the words, not the length of the career."""

    def words(self, verdict):
        message = Switchroom().last_word(
            datetime(1983, 12, 31, 16, 0), TOURS_TO_DIVESTITURE, 40, 6,
            verdict)
        return message.lines

    def test_each_verdict_reads_differently(self):
        said = {v: tuple(self.words(v)) for v in
                (AUDIT_PASSED, AUDIT_EXCEPTIONS, AUDIT_FAILED)}
        assert len(set(said.values())) == 3

    @pytest.mark.parametrize('verdict', [AUDIT_PASSED, AUDIT_EXCEPTIONS,
                                         AUDIT_FAILED])
    def test_the_seven_line_stays_whatever_the_verdict(self, verdict):
        text = ' '.join(self.words(verdict))
        assert 'Whichever of the seven you end up at in the' in text
        assert 'Go home.' in text

    def test_a_failed_audit_is_named_in_the_chiefs_words(self):
        assert any('audit' in line for line in self.words(AUDIT_FAILED))

    def test_a_clean_audit_does_not_make_a_speech(self):
        assert not any('audit' in line for line in self.words(AUDIT_PASSED))

    def test_the_chief_speaks_the_verdict_on_the_last_day(self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'The audit did not go your way' in out
