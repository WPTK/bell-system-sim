"""
The audit the divestiture memo promises, at the end of the last tour.

The memo of 1 November says open reports go to the operating company "with
your name on them" and that disposition codes "are audited after transfer".
Nothing ever audited anything: the ending was a ceremony. The audit gives a
verdict and changes what the wire chief says. It does not end the career
early. The thirteenth tour closes it on 31 December whatever the audit says.
"""

import json
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
from bell_system.progression import Career
from bell_system.screens.turnover import audit

LABELS = ('Dispositions on record', 'matched the line', 'did not match',
          'Came back as repeats', 'Handed over open', 'Verdict')


BOARD = 6


def go_to_last_tour(terminal):
    """
    Put a constructed terminal on 31 December, with a board it is sure of.

    The fixture's board was dealt on tour one, which is a single report, so
    closing three of them left nothing to hand over unless a report happened
    to arrive in time. Six are dealt here: closing three always leaves
    reports open, and nothing the tests do can take the board below that.
    """
    terminal.career.shift = TOURS_TO_DIVESTITURE
    terminal.career.save()
    terminal.clock.set_tour(terminal.career.shift)
    terminal.generate_shift_events()
    terminal.desk.reports.clear()
    terminal.desk.order.clear()
    terminal.desk.open_shift(terminal.clock.now(), 0, count=BOARD)


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
        found = audit(40, 0, 0, [], 0)
        assert found.verdict == AUDIT_PASSED
        assert found.wrong == 0

    def test_a_few_misses_pass_with_no_finding(self):
        assert audit(40, 2, 1, [], 0).verdict == AUDIT_PASSED

    def test_more_than_a_tenth_wrong_is_a_finding(self):
        assert audit(40, 6, 2, [], 0).verdict == AUDIT_EXCEPTIONS

    def test_more_than_a_quarter_wrong_fails(self):
        found = audit(40, 12, 5, [], 0)
        assert found.verdict == AUDIT_FAILED
        assert '12 of 40' in ' '.join(found.reasons)

    def test_nothing_closed_fails(self):
        found = audit(0, 0, 0, ['R-0001', 'R-0002'], 0)
        assert found.verdict == AUDIT_FAILED
        assert 'Nothing was closed' in found.reasons[0]

    def test_open_reports_past_commitment_are_a_finding(self):
        found = audit(40, 0, 0, ['R-1', 'R-2', 'R-3'], 2)
        assert found.verdict == AUDIT_EXCEPTIONS
        assert '2 went over' in ' '.join(found.reasons)

    def test_handing_over_more_late_than_you_closed_fails(self):
        assert audit(3, 0, 0, ['a'] * 9, 9).verdict == AUDIT_FAILED

    def test_open_reports_alone_are_not_a_failure(self):
        """The memo asks for an honest handoff, not an empty board."""
        assert audit(30, 0, 0, ['a'] * 8, 0).verdict == AUDIT_PASSED


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

    def test_a_second_visit_reads_the_same_audit_and_banks_nothing(
            self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        first = terminal.execute_command('handoff relieve')
        banked = len(terminal.career.index_history)
        again = terminal.execute_command('handoff relieve')
        assert 'relieve you twice' in again
        assert audit_block(again)['Verdict'] == audit_block(first)['Verdict']
        assert len(terminal.career.index_history) == banked

    def test_the_look_ahead_holds_the_verdict_until_sign_off(self, terminal):
        """Sign-off ages the board first, so a verdict now could be undone."""
        go_to_last_tour(terminal)
        close_some(terminal, 3)
        record = terminal.execute_command('handoff')
        found = audit_block(record)
        assert found['Verdict'] == 'struck at sign-off'
        for verdict in (AUDIT_PASSED, AUDIT_EXCEPTIONS, AUDIT_FAILED):
            assert verdict not in record
        assert 'Unworked time will still age the board' in record

    def test_the_counts_the_look_ahead_shows_are_the_ones_signed_off(
            self, terminal):
        go_to_last_tour(terminal)
        close_some(terminal, 3)
        ahead = audit_block(terminal.execute_command('handoff'))
        signed = audit_block(terminal.execute_command('handoff relieve'))
        for label in ('Dispositions on record', 'matched the line',
                      'did not match', 'Came back as repeats'):
            assert ahead[label] == signed[label]
        assert signed['Verdict'] in (AUDIT_PASSED, AUDIT_EXCEPTIONS,
                                     AUDIT_FAILED)

    def test_the_preview_is_not_worked_out_on_sign_off(self, terminal,
                                                       monkeypatch):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        calls = []
        real = terminal.career_audit
        monkeypatch.setattr(terminal, 'career_audit',
                            lambda: calls.append(1) or real())
        terminal.execute_command('handoff relieve')
        assert len(calls) == 1


class TestADamagedRecordCannotMakeNegativeFigures:
    """The audit reads the career's own count of wrong dispositions."""

    def test_wrong_is_held_between_none_and_all(self):
        too_many = audit(5, 9, 0, [], 0)
        assert (too_many.wrong, too_many.correct) == (5, 0)
        too_few = audit(5, -3, 0, [], 0)
        assert (too_few.wrong, too_few.correct) == (0, 5)

    def test_a_career_with_more_correct_than_closed_does_not_go_negative(
            self, terminal):
        terminal.career.reports_closed = 10
        terminal.career.reports_correct = 99
        terminal.career.reports_wrong = 0
        found = terminal.career_audit()
        assert (found.wrong, found.correct) == (0, 10)

    def test_the_audit_reads_the_careers_wrong_count(self, terminal):
        terminal.career.reports_closed = 10
        terminal.career.reports_correct = 10
        terminal.career.reports_wrong = 4
        assert terminal.career_audit().wrong == 4


class TestTheAuditIsKept:
    """Once the career is finished the audit is still there to read."""

    def finish(self, terminal):
        go_to_last_tour(terminal)
        close_some(terminal, 3)
        return terminal.execute_command('handoff relieve')

    def test_the_verdict_and_the_open_reports_are_stored(self, terminal):
        out = self.finish(terminal)
        career = terminal.career
        assert career.audit_verdict == audit_block(out)['Verdict']
        assert len(career.audit_open) >= BOARD - 3
        assert career.audit_late >= 0

    def test_they_survive_a_restart(self, terminal):
        out = self.finish(terminal)
        again = Career(terminal.career.path)
        again.load()
        assert again.finished
        assert again.audit_verdict == audit_block(out)['Verdict']
        assert again.audit_open == terminal.career.audit_open

    def test_handoff_shows_the_audit_after_the_career_is_over(
            self, terminal):
        out = self.finish(terminal)
        later = terminal.execute_command('handoff')
        assert 'THE AUDIT' in later
        assert 'AS THINGS STAND' not in later
        assert audit_block(later)['Verdict'] == audit_block(out)['Verdict']
        assert audit_block(later)['Handed over open'] == audit_block(out)[
            'Handed over open']

    def test_a_file_from_before_the_audit_still_loads(self, terminal):
        """No audit keys: the old file loads and handoff just stays quiet."""
        path = terminal.career.path
        with open(path) as handle:
            record = json.load(handle)
        record.update(finished=True, shift=TOURS_TO_DIVESTITURE)
        for key in ('audit_verdict', 'audit_open', 'audit_late'):
            record.pop(key, None)
        with open(path, 'w') as handle:
            json.dump(record, handle)
        old = Career(path)
        old.load()
        assert old.finished and old.audit_verdict == ''
        terminal.career = old
        assert 'THE AUDIT' not in terminal.execute_command('handoff')

    def test_a_later_versions_keys_are_still_held(self, terminal):
        path = terminal.career.path
        self.finish(terminal)
        with open(path) as handle:
            record = json.load(handle)
        record['from_the_future'] = {'kept': True}
        with open(path, 'w') as handle:
            json.dump(record, handle)
        again = Career(path)
        again.load()
        again.save()
        with open(path) as handle:
            assert json.load(handle)['from_the_future'] == {'kept': True}
        assert again.audit_verdict


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

    def test_the_praise_comes_before_the_audit(self):
        """He does not lead with the bad news and then say what he thought."""
        for verdict in (AUDIT_EXCEPTIONS, AUDIT_FAILED):
            text = ' '.join(self.words(verdict))
            assert text.index('better at it than most') < text.index(
                'The audit')

    def test_an_audit_with_findings_does_not_promise_nobody_will_argue(
            self):
        for verdict in (AUDIT_EXCEPTIONS, AUDIT_FAILED):
            assert 'argue' not in ' '.join(self.words(verdict))
        assert 'argue' in ' '.join(self.words(AUDIT_PASSED))

    def test_a_clean_audit_does_not_make_a_speech(self):
        assert not any('audit' in line for line in self.words(AUDIT_PASSED))

    def test_the_chief_speaks_the_verdict_on_the_last_day(self, terminal):
        go_to_last_tour(terminal)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'The audit did not go your way' in out
