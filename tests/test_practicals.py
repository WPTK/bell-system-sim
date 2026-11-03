"""
A count offers a sign-off, and a practical gives it.

Past the floor of correct closures Halloran stages one report on the live
board that needs what the sign-off is for. The sign-off is withheld until it
is worked, on fun as on craft; hint costs nothing while it is on the board;
a failed attempt says what was missed; a pass is saved on the career.
"""

import pytest

from bell_system import save
from bell_system.data.practicals import PRACTICALS
from bell_system.progression import QUALIFICATIONS, QUALIFICATIONS_BY_KEY

KEYS = list(PRACTICALS)

# What passes each one, as the player would type it.
SOLUTIONS = {
    'frame': ['cosmos fix {n}'],
    'office': ['switch clear {n}'],
    'scc': ['connect pool outside plant', 'report dispatch {n} outside'],
    'trunk': ['trunk trace {n}'],
    'toll': ['toll control reroute'],
}


def ready(terminal, key, difficulty=None):
    """Hold everything before ``key`` and the count for it, and nothing more."""
    if difficulty:
        terminal.career.set_difficulty(difficulty)
    held = ['loop']
    for qualification in QUALIFICATIONS[1:]:
        if qualification.key == key:
            break
        held.append(qualification.key)
    terminal.career.qualifications = held
    terminal.career.reports_correct = (
        QUALIFICATIONS_BY_KEY[key].requires_reports
        * terminal.career.difficulty.reports_per_qualification)
    return terminal


def staged(terminal):
    practical, report = terminal._practical_open()
    return practical, report


def work(terminal, key, number):
    for command in SOLUTIONS[key]:
        terminal.execute_command(command.format(n=number))


def test_every_sign_off_after_loop_has_a_practical():
    assert KEYS == [q.key for q in QUALIFICATIONS if q.verb]


@pytest.mark.parametrize('difficulty', ['fun', 'craft'])
def test_the_count_alone_does_not_sign_in_fun_or_craft(terminal, difficulty):
    ready(terminal, 'frame', difficulty)
    report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
    terminal.execute_command(f'mlt {report.number}')
    terminal.execute_command(f'report close {report.number} 5 OPEN')
    assert not terminal.career.is_qualified('frame')
    assert 'frame' not in terminal.career.practicals_passed


def test_the_offer_is_made_once_and_names_the_command(terminal):
    ready(terminal, 'frame')
    first = terminal._offer_qualifications()
    assert len(first) == 1 and 'qual take frame' in first[0]
    assert terminal._offer_qualifications() == []


def test_the_refusal_past_the_floor_points_at_the_practical(terminal):
    ready(terminal, 'frame')
    reply = terminal.execute_command('cosmos jumper TR-1')
    assert "'qual take frame'" in reply


def test_the_refusal_short_of_the_floor_still_counts_closures(terminal):
    ready(terminal, 'frame')
    terminal.career.reports_correct = 0
    reply = terminal.execute_command('cosmos jumper TR-1')
    assert 'Correct closures still needed' in reply


def test_qual_lists_a_ready_practical(terminal):
    ready(terminal, 'frame')
    shown = terminal.execute_command('qual')
    assert 'Count met. Practical: qual take frame' in shown
    assert "Next: Main Distributing Frame. 'qual take frame'." in shown


def test_take_before_the_floor_says_how_far_off(terminal):
    ready(terminal, 'frame')
    terminal.career.reports_correct -= 1
    reply = terminal.execute_command('qual take frame')
    assert 'not yet' in reply and '1 more correct closure.' in reply
    assert terminal._practical_open() is None


def test_take_with_no_key_lists_what_is_ready(terminal):
    ready(terminal, 'office')
    assert 'office' in terminal.execute_command('qual take')


def test_take_an_unknown_practical(terminal):
    assert 'no practical for' in terminal.execute_command('qual take warp')
    assert 'no practical for' in terminal.execute_command('qual take loop')


def test_take_one_already_held(terminal):
    reply = terminal.execute_command('qual take frame')
    assert 'already signed off' in reply


def test_take_stages_one_report_with_the_brief(terminal):
    ready(terminal, 'frame')
    reply = terminal.execute_command('qual take frame')
    practical, report = staged(terminal)
    assert practical.key == 'frame' and report.practical == 'frame'
    assert report.number in reply and "'qual submit'" in reply
    assert report.record.fault == 'CO_EQUIP'
    assert report.record.frame_defect is not None
    assert not report.overdue()


def test_take_again_shows_the_brief_and_stages_nothing_new(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    before = len(terminal.desk.pending())
    reply = terminal.execute_command('qual take frame')
    assert reply.startswith('Still on your board')
    assert len(terminal.desk.pending()) == before


def test_one_practical_at_a_time(terminal):
    ready(terminal, 'frame')
    terminal.career.reports_correct = 999
    terminal.execute_command('qual take frame')
    reply = terminal.execute_command('qual take office')
    assert 'qual submit' in reply
    assert staged(terminal)[0].key == 'frame'


def test_the_sign_offs_tools_work_while_the_practical_is_on(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    assert 'not signed off' not in terminal.execute_command(
        f'cosmos jumper {report.number}')
    assert not terminal.career.is_qualified('frame')


def test_the_tools_go_again_when_it_is_handed_in(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    terminal.execute_command('qual submit')
    assert 'not signed off' in terminal.execute_command('cosmos jumper TR-1')


def test_a_practical_cannot_be_closed_as_a_report(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    reply = terminal.execute_command(f'report close {report.number} 5 CO_EQUIP')
    assert 'is a practical' in reply
    assert terminal.career.reports_closed == 0


@pytest.mark.parametrize('key', KEYS)
def test_working_it_gets_the_sign_off(terminal, key):
    ready(terminal, key)
    terminal.execute_command(f'qual take {key}')
    _, report = staged(terminal)
    work(terminal, key, report.number)
    reply = terminal.execute_command('qual submit')
    assert 'passed' in reply and 'You are signed off on' in reply
    assert terminal.career.is_qualified(key)
    assert key in terminal.career.practicals_passed
    assert terminal._practical_open() is None
    assert report.number not in terminal.desk.reports


@pytest.mark.parametrize('key', KEYS)
def test_handing_in_nothing_says_what_was_missed(terminal, key):
    ready(terminal, key)
    terminal.execute_command(f'qual take {key}')
    reply = terminal.execute_command('qual submit')
    assert 'not signed' in reply
    assert not terminal.career.is_qualified(key)
    assert key not in terminal.career.practicals_passed
    assert terminal._practical_open() is None
    assert 'You are signed off on' not in reply
    assert f"'qual take {key}'" in reply


@pytest.mark.parametrize('key', KEYS)
def test_a_failed_practical_can_be_taken_again(terminal, key):
    ready(terminal, key)
    terminal.execute_command(f'qual take {key}')
    terminal.execute_command('qual submit')
    terminal.execute_command(f'qual take {key}')
    _, report = staged(terminal)
    work(terminal, key, report.number)
    assert terminal.career.is_qualified(key) is False
    terminal.execute_command('qual submit')
    assert terminal.career.is_qualified(key)


def test_a_staged_report_leaves_the_career_counts_alone(terminal):
    ready(terminal, 'frame')
    closed = terminal.career.reports_closed
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    work(terminal, 'frame', report.number)
    terminal.execute_command('qual submit')
    assert terminal.career.reports_closed == closed
    assert terminal.desk.closed_count == 0


def test_submit_with_nothing_on_the_board(terminal):
    assert 'no practical on your board' in terminal.execute_command(
        'qual submit')


def test_the_sign_off_remark_follows_the_count_held(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    work(terminal, 'frame', report.number)
    reply = terminal.execute_command('qual submit')
    assert 'That opens: cosmos' in reply


# -- hint ------------------------------------------------------------------


def test_hint_is_free_while_a_practical_is_on_the_board(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    minutes = terminal.shift_minutes
    reply = terminal.execute_command('hint')
    # The command itself costs the shift its one minute and the hint no more.
    assert terminal.shift_minutes - minutes <= 1
    assert 'frame' in reply.lower()


def test_hint_walks_down_the_practical_and_ends_on_the_command(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    replies = [terminal.execute_command('hint') for _ in range(3)]
    assert f'cosmos fix {report.number}' in replies[2]


def test_hint_costs_what_it_did_with_no_practical(terminal):
    before = terminal.shift_minutes
    terminal.execute_command('hint')
    assert terminal.shift_minutes - before >= 2


# -- the staging -------------------------------------------------------------


def test_the_scc_practical_leaves_the_local_crews_out(terminal):
    ready(terminal, 'scc')
    terminal.execute_command('qual take scc')
    force = terminal.desk.force
    free = force.free('Outside plant', terminal.shift_minutes)
    assert free == []


def test_the_scc_practical_gives_the_loan_back_if_it_was_spent(terminal):
    ready(terminal, 'scc')
    terminal.execute_command('connect pool Station')
    ready(terminal, 'scc')
    terminal.execute_command('qual take scc')
    assert terminal.desk.force.loaned is None


def test_the_scc_practical_wants_the_right_force(terminal):
    ready(terminal, 'scc')
    terminal.execute_command('qual take scc')
    _, report = staged(terminal)
    terminal.execute_command('connect pool station')
    terminal.execute_command(f'report dispatch {report.number} outside')
    reply = terminal.execute_command('qual submit')
    assert 'not signed' in reply and 'station' in reply


def test_the_toll_practical_wants_reroute_not_block(terminal):
    ready(terminal, 'toll')
    terminal.execute_command('qual take toll')
    terminal.execute_command('toll control block')
    reply = terminal.execute_command('qual submit')
    assert 'blocked the route' in reply
    assert not terminal.career.is_qualified('toll')


def test_the_toll_practical_takes_its_control_off(terminal):
    ready(terminal, 'toll')
    terminal.execute_command('qual take toll')
    terminal.execute_command('toll control reroute')
    terminal.execute_command('qual submit')
    assert terminal.desk.control is None


def test_the_trunk_practical_puts_the_group_right_afterwards(terminal):
    ready(terminal, 'trunk')
    terminal.execute_command('qual take trunk')
    groups = terminal.trunk_groups
    worst = min(groups, key=lambda name: groups[name]['quality'])
    assert groups[worst]['quality'] < 0.9
    terminal.execute_command('qual submit')
    assert min(group['quality'] for group in groups.values()
               if group['status'] == 'ACTIVE') > 0.9


def test_a_wrong_truck_is_named_as_such(terminal):
    ready(terminal, 'office')
    terminal.execute_command('qual take office')
    _, report = staged(terminal)
    terminal.execute_command(f'report dispatch {report.number} outside')
    reply = terminal.execute_command('qual submit')
    assert 'You sent a truck' in reply


# -- the shift --------------------------------------------------------------


def test_a_handoff_ends_a_practical_nobody_handed_in(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    terminal._abandon_practical()
    assert terminal._practical_open() is None
    assert report.number not in terminal.desk.reports


def test_a_practical_survives_a_saved_shift(terminal):
    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    stored = save.capture(terminal)
    terminal.desk.reports[report.number].practical = None
    assert terminal._practical_open() is None
    assert save.restore(terminal, stored)
    assert terminal._practical_open()[1].number == report.number


def test_a_report_saved_before_practicals_is_an_ordinary_one(terminal):
    report = terminal.desk.receive(terminal.clock.now(), fault='OPEN')
    stored = save.capture(terminal)
    for entry in stored['board']['reports']:
        entry.pop('practical', None)
    assert save.restore(terminal, stored)
    assert terminal.desk.reports[report.number].practical is None


def test_a_practical_passed_is_saved_on_the_career(terminal, tmp_path):
    from bell_system.progression import Career

    ready(terminal, 'frame')
    terminal.execute_command('qual take frame')
    _, report = staged(terminal)
    work(terminal, 'frame', report.number)
    terminal.execute_command('qual submit')
    again = Career(terminal.career.path)
    assert again.practicals_passed == ['frame']
    assert 'frame' in again.qualifications


def test_the_qual_man_page_describes_the_practical(terminal):
    page = terminal.execute_command('man qual')
    assert 'qual take' in page and 'qual submit' in page
