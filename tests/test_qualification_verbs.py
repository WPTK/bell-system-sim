"""
Each sign-off after Loop and Station adds a verb that changes the board.

For each of the five there is a command that changes the report desk, that
the wire chief refuses until the sign-off is held, and that `qual` lists.
Before this a sign-off opened screens and nothing else, and a craftsperson
who held all six had the same four ways to work a report as one who held one.
"""

import random
from datetime import datetime

import pytest

from bell_system import save
from bell_system.field import POOL_CREW, Assignment, FieldForce
from bell_system.progression import QUALIFICATIONS, QUALIFICATIONS_BY_KEY
from bell_system.reports import (
    COST_FRAME_FIX,
    COST_FRAME_LOOKUP,
    COST_OFFICE_CLEAR,
    COST_TRUNK_TRACE,
    CONTROLS,
    STATUS_DISPATCHED,
    ReportDesk,
)

# Sign-off, a fault the verb is for, and the command that works it.
VERBS = [
    ('frame', 'CO_EQUIP', 'cosmos fix {}'),
    ('office', 'FCG', 'switch clear {}'),
    ('scc', 'OPEN', 'connect pool Outside plant'),
    ('trunk', 'NONE', 'trunk trace {}'),
    ('toll', 'NONE', 'toll control block'),
]


def new_report(terminal, fault, symptom=None):
    report = terminal.desk.receive(terminal.clock.now(), fault=fault)
    if symptom:
        report.symptom = symptom
    return report


def signed_off(terminal, key):
    held = ['loop']
    for qualification in QUALIFICATIONS:
        held.append(qualification.key)
        if qualification.key == key:
            break
    terminal.career.qualifications = held


@pytest.mark.parametrize('key,fault,command', VERBS)
def test_the_wire_chief_refuses_the_verb_before_the_sign_off(
        raw_terminal, key, fault, command):
    report = new_report(raw_terminal, fault, 'Calls do not complete')
    before = (raw_terminal.desk.control, raw_terminal.desk.force.loaned,
              report.status, report.minutes_spent, report.field_finding)
    reply = raw_terminal.execute_command(command.format(report.number))
    assert 'not signed off' in reply
    assert QUALIFICATIONS_BY_KEY[key].name in reply
    assert before == (raw_terminal.desk.control,
                      raw_terminal.desk.force.loaned,
                      report.status, report.minutes_spent,
                      report.field_finding)


@pytest.mark.parametrize('key,fault,command', VERBS)
def test_every_verb_is_listed_in_qual_and_in_the_man_page(
        raw_terminal, key, fault, command):
    qualification = QUALIFICATIONS_BY_KEY[key]
    assert qualification.verb
    assert qualification.verb_effect
    listing = raw_terminal.execute_command('qual')
    assert f'Adds:  {qualification.verb}' in listing
    page = raw_terminal.man_pages[qualification.unlocks[0]
                                  if key != 'scc' else 'connect']
    assert qualification.verb.split(' <')[0] in page


def test_only_the_five_signoffs_after_loop_carry_a_verb():
    assert [q.key for q in QUALIFICATIONS if q.verb] == [
        'frame', 'office', 'scc', 'trunk', 'toll']


# -- frame ---------------------------------------------------------------


def test_cosmos_fix_clears_a_frame_defect_without_a_truck(terminal):
    report = new_report(terminal, 'CO_EQUIP')
    assert report.record.frame_defect
    reply = terminal.execute_command(f'cosmos fix {report.number}')
    assert report.field_finding == 'CO_EQUIP'
    assert report.status == STATUS_DISPATCHED
    assert report.tested
    assert report.dispatched_to is None
    assert report.record.frame_defect is None
    assert f'{COST_FRAME_FIX} minutes charged' in reply
    # The record agrees with the plant now, so a second look says so.
    again = terminal.execute_command(f'cosmos jumper {report.record.telephone_number}')
    assert 'The record is in order' in again


def test_cosmos_fix_on_a_line_with_nothing_wrong_changes_nothing(terminal):
    report = new_report(terminal, 'OPEN')
    reply = terminal.execute_command(f'cosmos fix {report.number}')
    assert 'nothing to fix' in reply.lower()
    assert report.field_finding is None
    assert report.status != STATUS_DISPATCHED
    assert report.desk_minutes == COST_FRAME_LOOKUP


def test_cosmos_fix_names_the_report_it_cannot_find(terminal):
    assert 'no report matching' in terminal.execute_command('cosmos fix TR-0')


def test_cosmos_fix_leaves_a_closed_report_alone(terminal):
    report = new_report(terminal, 'CO_EQUIP')
    terminal.execute_command(f'mlt {report.number}')
    terminal.execute_command(f'report close {report.number} 5 CO_EQUIP')
    assert 'already closed' in terminal.execute_command(
        f'cosmos fix {report.number}')


# -- office --------------------------------------------------------------


def test_switch_clear_moves_a_false_cross_or_ground_off_the_line(terminal):
    report = new_report(terminal, 'FCG')
    reply = terminal.execute_command(f'switch clear {report.number}')
    assert report.field_finding == 'FCG'
    assert report.status == STATUS_DISPATCHED
    assert report.tested
    assert f'{COST_OFFICE_CLEAR} minutes charged' in reply


@pytest.mark.parametrize('fault', ['CO_EQUIP', 'OPEN', 'NONE'])
def test_switch_clear_finds_nothing_to_clear_on_any_other_fault(
        terminal, fault):
    report = new_report(terminal, fault)
    reply = terminal.execute_command(f'switch clear {report.number}')
    assert 'diagnostic clean' in reply
    assert report.field_finding is None
    assert not report.tested
    assert report.desk_minutes == COST_FRAME_LOOKUP


def test_switch_clear_works_only_on_the_office_you_are_in(terminal):
    report = new_report(terminal, 'FCG')
    other = next(office for office in terminal.watched_offices()
                 if office['clli'] != terminal.home_office['clli'])
    terminal.execute_command(f"connect {other['clli']}")
    assert 'sitting in' in terminal.execute_command(
        f'switch clear {report.number}')
    assert report.field_finding is None


# -- scc -----------------------------------------------------------------


def test_connect_pool_lends_one_crew_for_one_category(terminal):
    force = terminal.desk.force
    assert POOL_CREW not in force.crews_for('Outside plant')
    reply = terminal.execute_command('connect pool outside plant')
    assert force.loaned == 'Outside plant'
    assert POOL_CREW in force.crews_for('Outside plant')
    assert POOL_CREW not in force.crews_for('Station')
    assert 'yours for outside plant' in reply
    # The pool has one crew.
    again = terminal.execute_command('connect pool station')
    assert 'already spoken for' in again
    assert force.loaned == 'Outside plant'


def test_connect_pool_needs_a_force_it_knows(terminal):
    assert 'usage' in terminal.execute_command('connect pool')
    assert 'usage' in terminal.execute_command('connect pool nobody')
    assert terminal.desk.force.loaned is None


def test_the_pool_crew_goes_when_the_wire_centres_own_are_out(terminal):
    desk = terminal.desk
    for crew in desk.force.crews_for('Outside plant'):
        desk.force.out[crew.key] = Assignment(crew, 'TR-1', 30, 60, 0)
    report = new_report(terminal, 'OPEN')
    assert 'Nobody free' in desk.dispatch(report, 'Outside plant', 0)
    terminal.execute_command('connect pool Outside plant')
    desk.dispatch(report, 'Outside plant', 0)
    assert report.crew == POOL_CREW.name
    # It starts at the far end of the district.
    assert report.travel_minutes >= 35


def test_the_pool_crew_is_on_the_roster_only_while_it_is_loaned():
    force = FieldForce(random.Random(1))
    assert POOL_CREW not in force.roster()
    assert force.borrow('Station')
    assert POOL_CREW in force.roster()
    force.new_tour(0)
    assert force.loaned is None
    assert POOL_CREW not in force.roster()


def test_a_crew_still_out_from_the_last_tour_cannot_be_borrowed_again():
    force = FieldForce(random.Random(1))
    force.borrow('Station')
    force.out[POOL_CREW.key] = Assignment(POOL_CREW, 'TR-1', 40, 100, 0)
    force.new_tour(10)
    assert force.loaned is None
    assert not force.borrow('Station')


def test_the_loan_survives_a_saved_shift(terminal):
    terminal.execute_command('connect pool Cable repair')
    stored = save.capture(terminal)
    terminal.desk.force.loaned = None
    save._force_in(terminal.desk, stored['force'])
    assert terminal.desk.force.loaned == 'Cable repair'


def test_the_force_screen_shows_the_pool_crew_only_when_it_is_here(terminal):
    assert POOL_CREW.name not in terminal.execute_command('force')
    terminal.execute_command('connect pool Station')
    assert POOL_CREW.name in terminal.execute_command('force')


# -- trunk ---------------------------------------------------------------


def test_trunk_trace_finds_the_bad_trunk_behind_a_call_that_will_not_complete(
        terminal):
    report = new_report(terminal, 'NONE', 'Calls do not complete')
    worst = min(terminal.trunk_groups,
                key=lambda name: terminal.trunk_groups[name]['quality'])
    terminal.trunk_groups[worst]['status'] = 'ACTIVE'
    terminal.trunk_groups[worst]['quality'] = 0.981
    reply = terminal.execute_command(f'trunk trace {report.number}')
    assert worst in reply
    assert report.field_finding == 'NONE'
    assert report.status == STATUS_DISPATCHED
    assert report.tested
    assert terminal.trunk_groups[worst]['quality'] > 0.981
    assert f'{COST_TRUNK_TRACE} minutes charged' in reply


@pytest.mark.parametrize('fault,symptom', [
    ('NONE', 'Noise on the line'),
    ('FCG', 'Calls do not complete'),
    ('CO_EQUIP', 'Calls do not complete'),
    ('OPEN', 'No dial tone'),
])
def test_trunk_trace_finds_the_trunks_good_on_every_other_report(
        terminal, fault, symptom):
    report = new_report(terminal, fault, symptom)
    reply = terminal.execute_command(f'trunk trace {report.number}')
    assert 'tests good' in reply
    assert report.field_finding is None
    assert not report.tested
    assert report.desk_minutes == COST_FRAME_LOOKUP


def test_trunk_trace_needs_a_report(terminal):
    assert 'usage' in terminal.execute_command('trunk trace')


# -- toll ----------------------------------------------------------------


def test_toll_control_stays_on_until_it_is_taken_off(terminal):
    assert terminal.desk.control is None
    reply = terminal.execute_command('toll control block')
    assert terminal.desk.control == 'block'
    assert 'until you take it off' in reply
    # Other work does not take it off.
    terminal.execute_command('mlt')
    terminal.execute_command('toll load')
    assert terminal.desk.control == 'block'
    assert 'block is on' in terminal.execute_command('toll control')
    assert 'already on' in terminal.execute_command('toll control block')
    terminal.execute_command('toll control reroute')
    assert terminal.desk.control == 'reroute'
    terminal.execute_command('toll control off')
    assert terminal.desk.control is None
    assert 'none is on' in terminal.execute_command('toll control off')


def test_toll_control_asks_for_a_control_it_knows(terminal):
    assert 'none is on' in terminal.execute_command('toll control')
    assert 'put one on' in terminal.execute_command('toll control jam')
    assert terminal.desk.control is None


@pytest.mark.parametrize('name', sorted(CONTROLS))
def test_a_control_thins_no_trouble_reports_and_shortens_new_commitments(
        name):
    relief, minutes = CONTROLS[name]

    def draw(control):
        desk = ReportDesk('201', '555', 'NWRKNJ02', random.Random(7))
        desk.control = control
        now = datetime(1983, 11, 14, 9)
        faults = [desk._choose_fault() for _ in range(4000)]
        return faults.count('NONE') / len(faults), desk._commitment(
            'OPEN', now, 0) - now

    share_off, wait_off = draw(None)
    share_on, wait_on = draw(name)
    assert share_on < share_off * (relief + 0.12)
    assert share_on < share_off
    assert (wait_off - wait_on).total_seconds() == minutes * 60


def test_the_control_survives_a_saved_shift(terminal):
    terminal.execute_command('toll control reroute')
    stored = save.capture(terminal)
    assert stored['board']['control'] == 'reroute'
    terminal.desk.control = None
    assert save.restore(terminal, stored)
    assert terminal.desk.control == 'reroute'


def test_a_saved_shift_from_before_controls_loads_with_none(terminal):
    stored = save.capture(terminal)
    del stored['board']['control']
    terminal.desk.control = 'block'
    assert save.restore(terminal, stored)
    assert terminal.desk.control is None


def test_a_control_the_desk_does_not_know_is_no_control(terminal):
    stored = save.capture(terminal)
    stored['board']['control'] = 'sdoc'
    assert save.restore(terminal, stored)
    assert terminal.desk.control is None
