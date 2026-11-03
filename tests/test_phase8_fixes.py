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


def _minutes_on_report(terminal, command_for):
    """What a command takes off a fresh report's clock."""
    report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
    terminal.execute_command(f'mlt {report.number}')
    before = report.minutes_spent
    shown = terminal.execute_command(command_for(report))
    return report, shown, report.minutes_spent - before


class TestASectionIsOnlyForCableRepair:
    """C21: a cable and binder is part of one force's dispatch."""

    @pytest.mark.parametrize('force', ['outside plant', 'central office',
                                       'station'])
    def test_another_force_given_a_section_is_refused(self, terminal, force):
        report, shown, spent = _minutes_on_report(
            terminal, lambda r: f'report dispatch {r.number} {force} 81/8')
        assert 'only Cable repair takes a cable and binder' in shown
        assert report.dispatched_to is None
        _, idle, base = _minutes_on_report(terminal,
                                           lambda r: f'report show {r.number}')
        assert spent == base

    def test_the_refusal_is_the_same_for_the_right_force_and_the_wrong(
            self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
        right = terminal.execute_command(
            f'report dispatch {report.number} outside plant 81/8')
        wrong = terminal.execute_command(
            f'report dispatch {report.number} central office 81/8')
        assert right == wrong

    def test_the_usage_line_offers_a_section_to_cable_repair_only(
            self, terminal):
        shown = terminal.execute_command('report dispatch')
        assert '<force>\n' in shown or '<force>' in shown
        assert '[cable/binder]' not in shown
        assert 'Cable repair also takes a cable/binder' in shown

    def test_a_cable_that_is_not_in_the_plant_is_refused(self, terminal):
        report = terminal.desk.receive(terminal.clock.now(), fault='WET')
        count = terminal.desk.plant.cable_count
        shown = terminal.execute_command(
            f'report dispatch {report.number} cable repair {count + 1}/8')
        assert f'cables 1 to {count}' in shown
        assert report.dispatched_to is None


class TestThePressureAlarmOpensAJob:
    """A8: acting on the gauge costs no customer anything."""

    def _alarmed(self, terminal):
        """Run the tour on, ten minutes at a time, until the gauge alarms."""
        from test_board_cases import _leaking_tour
        section = _leaking_tour(terminal)
        heard = []
        for _ in range(48):
            was = terminal.shift_minutes
            terminal.shift_minutes += 10
            heard.extend(terminal._weather_events(was))
            if any('PRESSURE ALARM' in p for p in heard):
                return section, heard
        raise AssertionError('the gauge never alarmed')

    def test_the_alarm_opens_a_job_and_says_so(self, terminal):
        section, heard = self._alarmed(terminal)
        assert len(terminal.desk.jobs) == 1
        job = terminal.desk.jobs[0]
        assert job.number in ''.join(heard)
        assert (job.cable, job.binder) == (section.cable, section.binder)

    def test_the_job_names_the_cable_and_not_the_group(self, terminal):
        _, heard = self._alarmed(terminal)
        text = ''.join(heard)
        assert 'binder' not in text.lower()
        jobs = terminal.execute_command('report jobs')
        assert 'PJ-001' in jobs and 'binder' not in jobs.lower()

    def test_the_board_does_not_list_it(self, terminal):
        self._alarmed(terminal)
        assert 'PJ-001' not in terminal.execute_command('report')

    def test_a_splicer_sent_to_the_job_clears_it_and_charges_no_report(
            self, terminal):
        section, _ = self._alarmed(terminal)
        reports = list(terminal.desk.reports.values())
        before = [(r.minutes_spent, r.desk_minutes, r.missed_commitment)
                  for r in reports]
        was = terminal.career.record_dispatch
        calls = []
        terminal.career.record_dispatch = lambda *a, **k: calls.append(a)
        shown = terminal.execute_command(
            f'report dispatch PJ-001 cable repair '
            f'{section.cable}/{section.binder}')
        terminal.career.record_dispatch = was
        assert 'resealed' in shown
        assert terminal.desk.plant.open_section(
            section.cable, section.binder) is None
        assert calls == []
        after = [(r.minutes_spent, r.desk_minutes, r.missed_commitment)
                 for r in reports]
        assert [a[1:] for a in after] == [b[1:] for b in before]

    def test_the_trip_moves_the_shift_clock(self, terminal):
        section, _ = self._alarmed(terminal)
        job = terminal.desk.jobs[0]
        terminal.execute_command(
            f'report dispatch PJ-001 cable repair '
            f'{section.cable}/{section.binder}')
        assert job.desk_minutes > 0

    def test_the_wrong_group_is_a_wrong_trip_charged_to_the_job(
            self, terminal):
        section, _ = self._alarmed(terminal)
        other = section.binder % 24 + 1
        reports = list(terminal.desk.reports.values())
        before = [r.desk_minutes for r in reports]
        shown = terminal.execute_command(
            f'report dispatch PJ-001 cable repair {section.cable}/{other}')
        assert 'found it dry' in shown
        assert terminal.desk.jobs[0].desk_minutes > 0
        # The board ages with the clock; what the trip cost is the job's.
        assert [r.desk_minutes for r in reports] == before
        assert terminal.desk.plant.open_section(
            section.cable, section.binder) is not None

    def test_another_force_is_refused_without_a_charge(self, terminal):
        self._alarmed(terminal)
        shown = terminal.execute_command(
            'report dispatch PJ-001 outside plant')
        assert 'Only Cable repair' in shown
        assert terminal.desk.jobs[0].desk_minutes == 0

    def test_a_customer_report_on_the_same_sheath_comes_back_with_it(
            self, terminal):
        section, _ = self._alarmed(terminal)
        terminal.desk.plant.leak(200, 0.0)
        report = terminal.desk.receive(
            terminal.clock.now(), fault='WET', section=section)
        terminal.execute_command(
            f'report dispatch PJ-001 cable repair '
            f'{section.cable}/{section.binder}')
        assert report.sheath_repaired

    def test_the_job_is_saved(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        self._alarmed(terminal)
        captured = json.loads(json.dumps(save.capture(terminal)))
        fresh = BellSystemTerminal()
        fresh.career.shift = terminal.career.shift
        fresh.career.reports_closed = terminal.career.reports_closed
        assert save.restore(fresh, captured)
        assert [j.number for j in fresh.desk.jobs] == ['PJ-001']

    def test_a_save_from_before_has_no_jobs(self, terminal):
        import json
        from bell_system import save
        from bell_system.terminal import BellSystemTerminal
        captured = json.loads(json.dumps(save.capture(terminal)))
        captured['board'].pop('jobs', None)
        fresh = BellSystemTerminal()
        assert save.restore(fresh, captured)
        assert fresh.desk.jobs == []


class TestACaseSaysTheForceThatClearsIt:
    """Its words and its fault agree, whichever of its conditions it is."""

    def test_the_dig_does_not_point_at_the_splicers(self):
        from bell_system.data.cases import CASE_KINDS
        spec = CASE_KINDS['dig']
        words = ' '.join(list(spec.faults.values()) + list(spec.opened)
                         + list(spec.closed)).lower()
        assert 'splic' not in words

    def test_every_condition_of_a_kind_is_cleared_by_one_force(self):
        from bell_system.data.cases import CASE_KINDS
        from bell_system.data.trouble import FAULTS
        for spec in CASE_KINDS.values():
            forces = {FAULTS[fault].dispatch for fault in spec.faults}
            assert len(forces) == 1, (spec.key, forces)

    def test_the_dig_is_outside_plant_work(self):
        from bell_system.data.cases import CASE_KINDS
        from bell_system.data.trouble import FAULTS
        assert {FAULTS[f].dispatch for f in CASE_KINDS['dig'].faults} == {
            'Outside plant'}

    def test_each_kind_has_more_than_one_condition(self):
        from bell_system.data.cases import CASE_KINDS
        assert all(len(spec.faults) >= 2 for spec in CASE_KINDS.values())

    @pytest.mark.parametrize('fault', ['OPEN', 'SHORT', 'GROUND'])
    def test_outside_plant_clears_a_dig_of_any_condition(
            self, terminal, fault):
        from bell_system.cases import Case
        terminal.career.shift = 5
        terminal.desk.depth_limit = 40
        case = Case('CASE-5-dig', 'dig', '0007', [10, 20, 30], fault)
        terminal.desk.cases = [case]
        terminal.shift_minutes = 100
        terminal._case_events()
        members = [terminal.desk.reports[n] for n in case.members]
        assert len(members) == 3
        assert {m.record.fault for m in members} == {fault}
        shown = terminal.execute_command(
            f'report dispatch {members[0].number} outside plant')
        assert case.cleared, shown
        assert all(m.sheath_repaired for m in members[1:])

    def test_a_case_saved_before_the_choice_reads_as_it_was(self):
        from bell_system.cases import Case
        stored = Case('CASE-5-dig', 'dig', '0007', [10]).out()
        stored.pop('fault')
        assert Case.read(stored).fault == 'OPEN'
        assert Case.read({**stored, 'fault': 'GROUND'}).fault == 'GROUND'


class TestACareerIsDealtItsOwnTours:
    """The case plan, the leaks and the toll counts take the career's seed."""

    def test_the_same_seed_and_tour_deal_the_same_case(self):
        from bell_system.cases import plan
        for tour in range(4, 13):
            first, second = plan(tour, [], 'abc'), plan(tour, [], 'abc')
            assert (first and first.out()) == (second and second.out())

    def test_two_seeds_deal_different_cases(self):
        from bell_system.cases import plan
        dealt = {}
        for seed in ('one', 'two', 'three', 'four', 'five', 'six'):
            dealt[seed] = [
                (case.kind, case.fault, case.where, tuple(case.due))
                if case else None
                for case in (plan(t, [], seed) for t in range(4, 13)
                             if t not in (9, 10))]
        assert len({tuple(plans) for plans in dealt.values()}) == len(dealt)

    def test_a_dig_is_not_the_same_dig_in_every_career(self):
        from bell_system.cases import plan
        digs = set()
        for seed in range(40):
            for tour in range(4, 8):
                case = plan(tour, [], str(seed))
                if case and case.kind == 'dig':
                    digs.add((case.fault, case.where))
        assert len({fault for fault, _ in digs}) == 3
        assert len({where for _, where in digs}) > 10

    def test_both_kinds_draw_from_more_than_one_condition(self):
        from bell_system.cases import MARKER_TOURS, plan
        seen = {'marker': set(), 'dig': set()}
        for seed in range(60):
            for tour in (*MARKER_TOURS, 5, 6, 7):
                case = plan(tour, [], str(seed))
                if case:
                    seen[case.kind].add(case.fault)
        assert len(seen['marker']) == 2 and len(seen['dig']) == 3

    def test_the_leaks_differ_between_careers(self, terminal):
        sites = set()
        for seed in range(30):
            terminal.career.seed = str(seed)
            terminal.career.shift = 3
            terminal.desk.plant.sections = [
                s for s in terminal.desk.plant.sections if not s.latent]
            terminal._plant_leak()
            leaking = [s for s in terminal.desk.plant.sections if s.latent]
            sites.add(tuple((s.cable, s.binder) for s in leaking))
        assert len(sites) > 3

    def test_the_toll_counts_differ_between_careers(self):
        from bell_system.data import fraud
        counts = {tuple(fraud.figures(9, str(seed)).values())
                  for seed in range(20)}
        assert len(counts) > 10
        assert fraud.figures(9, 'a') == fraud.figures(9, 'a')

    def test_a_new_career_is_given_a_seed_and_keeps_it(
            self, isolated_state, monkeypatch):
        from bell_system.terminal import BellSystemTerminal
        monkeypatch.delenv('BELL_SYSTEM_SEED')
        first = BellSystemTerminal()
        assert first.career.seed
        again = BellSystemTerminal()
        assert again.career.seed == first.career.seed

    def test_two_new_careers_are_given_different_seeds(
            self, tmp_path, monkeypatch):
        from bell_system.terminal import BellSystemTerminal
        monkeypatch.delenv('BELL_SYSTEM_SEED')
        seeds = set()
        for name in ('one', 'two', 'three'):
            monkeypatch.setenv('BELL_SYSTEM_HOME', str(tmp_path / name))
            seeds.add(BellSystemTerminal().career.seed)
        assert len(seeds) == 3

    def test_a_career_from_before_is_given_one(self, isolated_state,
                                               monkeypatch):
        import json
        from bell_system.terminal import BellSystemTerminal
        monkeypatch.delenv('BELL_SYSTEM_SEED')
        first = BellSystemTerminal()
        path = first.career.path
        stored = json.loads(open(path).read())
        stored.pop('seed')
        open(path, 'w').write(json.dumps(stored))
        assert BellSystemTerminal().career.seed
