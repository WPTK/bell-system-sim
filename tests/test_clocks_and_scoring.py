"""
One clock, and a score that cannot be had by leaving the board alone.

The S2 playtest found that time had no teeth. A report's commitment was only
ever charged by spend(), on the report being worked, so a board nobody
touched stayed exactly as old as it began; crews came back on the wall clock
while everything else ran on the shift clock; and thirteen sign-offs typed in
a row, with forty-seven reports pending, ended a career at 100.0 EXCELLENT.
"""

import json
import random
from datetime import datetime, timedelta

import pytest

from bell_system import save
from bell_system.field import FieldForce
from bell_system.progression import Career
from bell_system.reports import ReportDesk
from bell_system.terminal import BellSystemTerminal

RELIEVE = 'handoff relieve'


@pytest.fixture
def terminal(terminal):
    """The usual quiet terminal, with a working board of five."""
    while len(terminal.desk.pending()) < 5:
        terminal.desk.receive(terminal.clock.now())
    return terminal


def elapsed(terminal):
    """Every open report's elapsed minutes, by number."""
    return {report.number: report.minutes_spent
            for report in terminal.desk.pending()}


def escalations(terminal, number):
    """How many times the attendant has chased one report."""
    return sum(1 for message in terminal.switchroom.log
               if message.kind == 'escalation' and message.about == number)


class TestACommitmentIsElapsedTime:
    """It runs whether or not anybody is working the report."""

    def test_waiting_ages_every_report_on_the_board(self, terminal):
        before = elapsed(terminal)
        terminal.execute_command('sleep 7200')
        after = elapsed(terminal)
        assert before and set(after) >= set(before)
        for number, was in before.items():
            assert after[number] >= was + 120, number

    def test_desk_time_on_one_report_ages_the_others_by_the_same(
            self, terminal):
        worked, other = terminal.desk.pending()[:2]
        was = {worked.number: worked.minutes_spent,
               other.number: other.minutes_spent}
        terminal.execute_command(f'mlt {worked.number}')
        spent = worked.minutes_spent - was[worked.number]
        aged = other.minutes_spent - was[other.number]
        # The report that was measured was charged the measurement itself
        # and is not then aged for the same minutes a second time.
        assert spent == aged

    def test_a_crew_out_on_a_report_is_not_charged_twice(self, terminal):
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} '
                                 f'{report.record.fault and "outside"}')
        if report.crew is None:
            pytest.skip('this draw needed a different force')
        covered = report.minutes_spent
        terminal.execute_command('sleep 600')
        assert report.minutes_spent == covered

    def test_it_ages_on_the_handoff_too(self, terminal):
        terminal.execute_command('report')
        before = elapsed(terminal)
        terminal.execute_command(RELIEVE)
        for report in terminal.desk.pending():
            if report.number in before:
                assert report.minutes_spent > before[report.number]


class TestPassingACommitment:
    """Counted when it passes, said once, whoever was working it."""

    def make_late(self, terminal):
        """Put the nearest report half an hour from its commitment."""
        report = terminal.desk.pending()[0]
        report.commitment = (report.received
                             + timedelta(minutes=report.minutes_spent + 30))
        return report

    def test_a_report_nobody_touched_is_counted_when_it_goes(self, terminal):
        report = self.make_late(terminal)
        assert not report.overdue()
        before = terminal.career.missed_commitments
        terminal.execute_command('sleep 3600')
        assert report.overdue()
        assert terminal.career.missed_commitments >= before + 1

    def test_it_is_counted_once(self, terminal):
        report = self.make_late(terminal)
        terminal.execute_command('sleep 3600')
        assert report.missed_commitment
        assert escalations(terminal, report.number) == 1
        terminal.execute_command('sleep 3600')
        assert escalations(terminal, report.number) == 1

    def test_the_attendant_says_so_once(self, terminal):
        report = self.make_late(terminal)
        terminal.settings.set('game.ambience', 'on')
        terminal.execute_command('sleep 3600')
        terminal.execute_command('pwd')
        assert escalations(terminal, report.number) == 1
        message = next(m for m in terminal.switchroom.log
                       if m.kind == 'escalation'
                       and m.about == report.number)
        assert message.sender == 'mreyes'

    def test_closing_it_late_does_not_count_it_twice(self, terminal):
        report = self.make_late(terminal)
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command('sleep 3600')
        counted = terminal.career.missed_commitments
        terminal.execute_command(f'report close {report.number} 8')
        assert terminal.career.missed_commitments == counted


class TestMissesAreSoftOnFunAndFullOnCraft:
    """The same miss, weighed by the difficulty."""

    def career(self, key, missed=5, closed=10):
        career = Career(difficulty=key)
        career.reports_closed = closed
        career.reports_correct = closed
        career.missed_commitments = missed
        return career

    def test_fun_counts_them_but_not_much(self):
        fun = self.career('fun')
        assert 90 < fun.service_index() < 100

    def test_craft_counts_them_in_full(self):
        craft = self.career('craft')
        assert craft.service_index() == pytest.approx(90.0)

    def test_craft_loses_more_than_fun_for_the_same_misses(self):
        assert (self.career('craft').service_index()
                < self.career('fun').service_index())

    def test_no_misses_costs_nothing_on_either(self):
        for key in ('fun', 'craft'):
            assert self.career(key, missed=0).service_index() == 100.0


class TestABoardLeftToAgeIsNotPerfect:
    """Zero reports closed is not a reason to score 100."""

    @pytest.mark.parametrize('key', ['fun', 'craft'])
    def test_unworked_overdue_reports_cost_the_index(self, key):
        career = Career(difficulty=key)
        career.open_overdue = lambda: 20
        career.missed_commitments = 20
        assert career.index_band() != 'EXCELLENT'
        assert career.service_index() < 80

    def test_nothing_overdue_and_nothing_closed_is_still_100(self):
        assert Career().service_index() == 100.0

    def test_closing_the_overdue_reports_gives_it_back(self):
        career = Career(difficulty='craft')
        late = [3]
        career.open_overdue = lambda: late[0]
        open_score = career.service_index()
        late[0] = 0
        assert career.service_index() > open_score


class TestHandoffNeedsSomethingToHandOver:
    """A sign-off with nothing behind it is refused, and says how to proceed."""

    def test_a_bare_sign_off_is_refused(self, terminal):
        before = terminal.career.shift
        result = terminal.execute_command(RELIEVE)
        assert result.startswith('Nothing to hand over')
        assert "'report'" in result
        assert terminal.career.shift == before

    def test_reading_the_board_is_enough(self, terminal):
        terminal.execute_command('report')
        before = terminal.career.shift
        terminal.execute_command(RELIEVE)
        assert terminal.career.shift == before + 1

    def test_so_is_working_a_report(self, terminal):
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'mlt {report.number}')
        before = terminal.career.shift
        terminal.execute_command(RELIEVE)
        assert terminal.career.shift == before + 1

    def test_the_next_tour_asks_again(self, terminal):
        terminal.execute_command('report')
        terminal.execute_command(RELIEVE)
        assert terminal.execute_command(RELIEVE).startswith(
            'Nothing to hand over')

    def test_the_first_tour_still_ends_on_the_one_report(self, raw_terminal):
        terminal = raw_terminal
        terminal.settings.set('game.ambience', 'off')
        assert terminal.first_tour()
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report dispatch {report.number} '
                                 f'{report.record.fault and "outside"}')
        terminal.execute_command(f'report close {report.number} 8')
        before = terminal.career.shift
        terminal.execute_command(RELIEVE)
        assert terminal.career.shift == before + 1

    @pytest.mark.parametrize('key', ['fun', 'craft'])
    def test_thirteen_tours_of_looking_and_nothing_else(self, terminal, key):
        """The S2 bot: look at the board, sign off, thirteen times."""
        terminal.career.set_difficulty(key)
        terminal.career.shift = 1
        terminal.clock.set_tour(1)
        for _ in range(13):
            terminal.execute_command('report')
            terminal.execute_command(RELIEVE)
        career = terminal.career
        assert career.finished
        assert career.reports_closed == 0
        assert career.missed_commitments > 0
        assert career.service_index() < 95
        assert career.index_band() != 'EXCELLENT'


class TestOneClockForTheCrews:
    """Crews are back on shift minutes, which is when the board ages."""

    def test_a_crew_is_out_until_the_shift_reaches_its_return(self):
        force = FieldForce(random.Random(1))
        crew, travel, _ = force.send('Cable repair', 'TR-00001', 60, 0)
        job = force.out[crew.key]
        assert job.back_at() == travel + 60
        assert crew not in force.free('Cable repair', job.back_at() - 1)
        assert crew in force.free('Cable repair', job.back_at())

    def test_a_handoff_rebases_the_crews_still_out(self):
        force = FieldForce(random.Random(1))
        crew, travel, _ = force.send('Cable repair', 'TR-00001', 700, 400)
        was = force.out[crew.key].back_at()
        force.new_tour(480)
        assert force.out[crew.key].back_at() == was - 480

    def test_a_crew_home_before_the_handoff_is_not_carried(self):
        force = FieldForce(random.Random(1))
        crew, _, _ = force.send('Cable repair', 'TR-00001', 30, 0)
        force.new_tour(480)
        assert crew.key not in force.out

    def test_nobody_free_says_when_in_shift_terms(self):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        for number in ('TR-00001', 'TR-00002'):
            desk.force.send('Cable repair', number, 600, 0)
        report = desk.receive(datetime(1983, 11, 14), fault='WET')
        said = desk.dispatch(report, 'Cable repair', 10)
        assert report.dispatched_to is None
        assert said.startswith('Nobody free on cable repair')
        assert ' back in ' in said and 'into the tour' in said
        assert 'AM' not in said and 'EST' not in said

    def test_and_the_terminal_suggests_the_next_thing(self, terminal):
        terminal.settings.set('game.prompts', 'on')
        for number in ('TR-00001', 'TR-00002'):
            terminal.desk.force.send('Cable repair', number, 600,
                                     terminal.shift_minutes)
        report = terminal.desk.pending()[0]
        report.record.fault = 'WET'
        said = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Nobody free' in said
        assert 'Next:' in said

    def test_and_says_nothing_of_the_kind_unless_asked(self, terminal):
        """Prompts are off unless asked for, and so is a hint on a refusal."""
        for number in ('TR-00001', 'TR-00002'):
            terminal.desk.force.send('Cable repair', number, 600,
                                     terminal.shift_minutes)
        report = terminal.desk.pending()[0]
        report.record.fault = 'WET'
        said = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Nobody free' in said
        assert 'stays on the board' in said
        assert 'Next:' not in said


class TestNoFakeOutcomes:
    """Resolving a ticket reports the ticket, not an invented audience."""

    def test_no_customers_restored_and_no_dollars_recovered(self, terminal):
        ticket = terminal.active_tickets[0]
        result = terminal.execute_command(f"trouble resolve {ticket['id']}")
        assert ticket['id'] in result
        assert 'Resolved' in result
        for invented in ('customers restored', 'Revenue Recovered',
                         'EXCEEDED TARGET', '$'):
            assert invented not in result

    def test_it_says_whether_it_made_its_target(self, terminal):
        ticket = terminal.active_tickets[0]
        result = terminal.execute_command(f"trouble resolve {ticket['id']}")
        assert ('Within target' in result) or ('Past target by' in result)


class TestSavesFromBefore:
    """A shift written before reports aged on the shift clock still loads."""

    def old_save(self, terminal):
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'report dispatch {report.number} outside')
        captured = json.loads(json.dumps(save.capture(terminal)))
        for entry in captured['board']['reports']:
            del entry['desk_booked']
        del captured['tour']['tour_desk_start']
        del captured['tour']['board_reviewed']
        for job in captured['force']['out'].values():
            job['left'] = '1983-11-14T08:00:00'
        return captured

    def test_the_missing_fields_are_forgiven(self, terminal):
        captured = self.old_save(terminal)
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        for report in fresh.desk.reports.values():
            assert report.desk_booked == report.desk_minutes
        assert fresh._board_reviewed
        # A signed-off sign-off is not trapped behind the new gate.
        assert fresh._tour_has_work()

    def test_a_wall_clock_crew_is_taken_to_be_back(self, terminal):
        captured = self.old_save(terminal)
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        assert fresh.desk.force.out == {}

    def test_a_new_save_round_trips_the_crews(self, terminal):
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'report dispatch {report.number} outside')
        captured = json.loads(json.dumps(save.capture(terminal)))
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        assert ({key: job.back_at()
                 for key, job in fresh.desk.force.out.items()}
                == {key: job.back_at()
                    for key, job in terminal.desk.force.out.items()})

    def test_an_old_career_file_loads(self, tmp_path):
        path = tmp_path / 'career.json'
        path.write_text(json.dumps({
            'difficulty': 'fun', 'shift': 3, 'reports_closed': 4,
            'reports_correct': 3, 'reports_wrong': 1, 'repeat_reports': 0,
            'missed_commitments': 0, 'qualifications': ['loop'],
            'index_history': [100.0], 'office': {}, 'finished': False,
        }))
        career = Career(str(path))
        assert career.shift == 3
        assert 0 < career.service_index() <= 100


class TestNoDecisionsIsNoScore:
    """A tour with nothing closed and nothing late has no index to bank."""

    def test_a_career_with_no_record_is_unscored(self):
        assert not Career().scored()

    def test_closing_or_lateness_scores_it(self):
        closed = Career()
        closed.reports_closed = 1
        late = Career()
        late.open_overdue = lambda: 1
        assert closed.scored() and late.scored()

    def test_an_unscored_shift_adds_nothing_to_the_history(self):
        career = Career()
        career.end_shift()
        assert career.index_history == []
        assert career.shift == 2

    def test_a_scored_shift_does(self):
        career = Career()
        career.reports_closed = 3
        career.reports_correct = 3
        career.end_shift()
        assert career.index_history == [100.0]

    def test_a_first_tour_of_looking_banks_nothing(self, terminal):
        for report in terminal.desk.pending():
            report.commitment += timedelta(days=3)
        before = terminal.career.shift
        terminal.execute_command('report')
        said = terminal.execute_command(RELIEVE)
        assert terminal.career.shift == before + 1
        assert terminal.career.index_history == []
        assert 'none yet' in said
        assert '100.0' not in said

    def test_a_tour_that_left_the_board_to_rot_banks_the_real_score(
            self, terminal):
        for report in terminal.desk.pending():
            report.minutes_spent += 10000
        terminal.execute_command('report')
        terminal.execute_command(RELIEVE)
        assert len(terminal.career.index_history) == 1
        assert terminal.career.index_history[0] < 95


class TestOldSavesDoNotBurstOnLoad:
    """Reports already late in an old save are known, not newly missed."""

    def test_already_overdue_reports_are_flagged_quietly(self, terminal):
        captured = json.loads(json.dumps(save.capture(terminal)))
        open_numbers = {report.number for report in terminal.desk.pending()}
        for entry in captured['board']['reports']:
            del entry['desk_booked']
            if entry['number'] in open_numbers:
                entry['minutes_spent'] = 99999
                entry['missed_commitment'] = False
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        late = [report for report in fresh.desk.pending() if report.overdue()]
        assert len(late) == len(open_numbers)
        assert all(report.missed_commitment for report in late)
        before = fresh.career.missed_commitments
        assert fresh.desk.age(30, fresh.shift_minutes) == []
        fresh.execute_command('report')
        assert fresh.career.missed_commitments == before
        assert not any(message.kind == 'escalation'
                       for message in fresh.switchroom.log)

    def test_a_current_save_keeps_its_own_flags(self, terminal):
        report = terminal.desk.pending()[0]
        report.minutes_spent += 99999
        assert not report.missed_commitment
        captured = json.loads(json.dumps(save.capture(terminal)))
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        assert not fresh.desk.find(report.number).missed_commitment


class TestTheSuggestedWaitIsTheRealOne:
    """'Next:' is worked out against the clock as the command will leave it."""

    def block_cable_crews(self, terminal, minutes=600):
        terminal.settings.set('game.prompts', 'on')
        for number in ('TR-90001', 'TR-90002'):
            terminal.desk.force.send('Cable repair', number, minutes,
                                     terminal.shift_minutes)

    def test_sleeping_the_suggested_time_brings_a_crew_in(self, terminal):
        self.block_cable_crews(terminal)
        report = terminal.desk.pending()[0]
        report.record.fault = 'WET'
        for other in terminal.desk.pending()[1:]:
            other.tested = True
        said = terminal.execute_command(
            f'report dispatch {report.number} cable')
        seconds = int(said.split("'sleep ")[1].split("'")[0])
        returns = min(job.back_at()
                      for job in terminal.desk.force.out.values()
                      if job.crew.force == 'Cable repair')
        terminal.execute_command(f'sleep {seconds}')
        assert terminal.shift_minutes >= returns
        # Not a dispatch's twelve minutes more than it had to be.
        assert terminal.shift_minutes - returns <= 2

    def test_a_crew_back_before_the_command_ends_is_not_waited_for(
            self, terminal):
        self.block_cable_crews(terminal, minutes=1)
        for key, job in terminal.desk.force.out.items():
            terminal.desk.force.out[key] = job._replace(travel=0, work=1)
        report = terminal.desk.pending()[0]
        report.record.fault = 'WET'
        said = terminal.execute_command(
            f'report dispatch {report.number} cable')
        assert 'Nobody free' not in said or "'sleep 0'" not in said


class TestOnlyWorkedReportsCanBeClosed:
    """A crew sent to the wrong place found nothing, so there is nothing to close."""

    def setup_two(self, terminal, wrong):
        terminal.settings.set('game.prompts', 'on')
        first, second = terminal.desk.pending()[:2]
        first.record.fault = 'WET'
        second.record.fault = 'WET'
        terminal.execute_command(
            f"report dispatch {first.number} "
            f"{'central office' if wrong else 'cable'}")
        for key, job in list(terminal.desk.force.out.items()):
            if job.report == first.number:
                del terminal.desk.force.out[key]
        for number in ('TR-90001', 'TR-90002'):
            terminal.desk.force.send('Cable repair', number, 600,
                                     terminal.shift_minutes)
        return first, second

    def test_a_wrong_force_dispatch_is_not_suggested_for_closing(
            self, terminal):
        first, second = self.setup_two(terminal, wrong=True)
        assert first.status == 'DISP' and not first.field_finding
        said = terminal.execute_command(
            f'report dispatch {second.number} cable')
        assert 'can be closed' not in said

    def test_a_right_one_still_is(self, terminal):
        first, second = self.setup_two(terminal, wrong=False)
        assert first.status == 'DISP' and first.field_finding
        said = terminal.execute_command(
            f'report dispatch {second.number} cable')
        assert f'{first.number} has been worked and can be closed' in said
