"""
Thirteen tours on a real calendar, each with a beat, goals and an article.

The S1 and S2 audits found the same thing: the career was one tour thirteen
times. ``data/shift_events.py`` handed out the same three events with fixed
numbers on every shift, and put a Pentagon line and a microwave path out of
New York on a desk in New Jersey. ``data/tours.py`` replaces it.
"""

import re
from datetime import date, datetime

import pytest

from bell_system.data import tours
from bell_system.progression import QUALIFICATIONS
from bell_system.terminal import BellSystemTerminal

WEEKDAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday')

# Places the old boilerplate named, and a few more a careless draft might.
OTHER_PLACES = ('New York', 'NYC', 'Washington', 'WAS', 'Pentagon',
                'Chicago', 'Boston', 'Philadelphia', 'Detroit', 'Atlanta')


def go_to(terminal, tour):
    """Put a constructed terminal on a given tour of the career."""
    terminal.career.shift = tour
    terminal.clock.set_tour(tour)
    terminal.generate_shift_events()


def event_text(event):
    """Everything an event says, as one string."""
    return ' '.join(str(event[key]) for key in
                    ('id', 'title', 'description', 'details', 'source')
                    ) + ' ' + ' '.join(event['actions'])


def article_date(text):
    """The Date header of an article as a datetime."""
    stamp = re.search(r'^Date: (.*)$', text, re.M).group(1)
    return datetime.strptime(stamp, '%A, %d-%b-%y %H:%M:%S EST')


class TestTheCalendar:
    """Thirteen entries that agree with the clock."""

    def test_there_are_thirteen_with_unique_themes(self):
        assert [entry.number for entry in tours.TOURS] == list(range(1, 14))
        themes = [entry.theme for entry in tours.TOURS]
        assert len(set(themes)) == 13

    def test_dates_match_the_clock_and_the_last_is_new_years_eve(
            self, terminal):
        for entry in tours.TOURS:
            terminal.clock.set_tour(entry.number)
            assert terminal.clock.tour_day() == entry.day, entry.number
        assert tours.TOURS[0].day == date(1983, 11, 14)
        assert tours.TOURS[-1].day == date(1983, 12, 31)

    def test_thanksgiving_falls_between_tours_three_and_four(self):
        thanksgiving = date(1983, 11, 24)
        assert thanksgiving.weekday() == 3
        assert tours.TOURS[2].day < thanksgiving < tours.TOURS[3].day

    def test_the_shape_runs_build_crisis_relief_farewell(self):
        assert {entry.kind for entry in tours.TOURS} == set(tours.KINDS)
        assert tours.TOURS[-1].kind == 'farewell'

    def test_no_weekend_tour_is_written_up_as_a_monday(self):
        for entry in tours.TOURS:
            if entry.day.weekday() < 5:
                continue
            text = ' '.join(entry.briefing + tuple(
                beat.title + beat.details for beat in entry.beats))
            assert 'Monday' not in text, entry.number

    def test_a_weekday_named_in_a_tour_is_the_right_one(self):
        """Every 'Thursday 24 November' style date in the script is true."""
        spelled = re.compile(r'(' + '|'.join(WEEKDAYS) + r') (\d+) '
                             r'(November|December)')
        for entry in tours.TOURS:
            for beat in entry.beats:
                for name, day, month in spelled.findall(
                        beat.details + beat.description):
                    when = datetime.strptime(f'{day} {month} 1983',
                                             '%d %B %Y')
                    assert WEEKDAYS[when.weekday()] == name, entry.number

    def test_every_beat_says_whether_it_is_sourced_or_the_simulations_own(
            self):
        for entry in tours.TOURS:
            assert entry.beats, entry.number
            for beat in entry.beats:
                assert beat.origin in (tours.SOURCED, tours.OWN)
                assert beat.source, entry.number
                if beat.origin == tours.OWN:
                    assert 'own' in beat.source or 'own' in beat.details
            if entry.news:
                assert entry.news.origin in (tours.SOURCED, tours.OWN)

    def test_a_sourced_beat_points_at_something_that_exists(self, terminal):
        documents = ('/usr/doc/bulletin', '/usr/doc/divestiture')
        for entry in tours.TOURS:
            for beat in entry.beats:
                if beat.origin != tours.SOURCED:
                    continue
                assert (any(doc in beat.source for doc in documents)
                        or 'Engineering and Operations' in beat.source), \
                    entry.number
        for doc in documents:
            assert doc in terminal.filesystem

    def test_beats_come_due_inside_the_shift(self):
        for entry in tours.TOURS:
            for beat in entry.beats:
                hour, minute = (int(part) for part in beat.at.split(':'))
                assert 8 * 60 <= hour * 60 + minute < 16 * 60

    def test_the_script_is_for_its_own_calendar_only(self):
        assert tours.script(5, date(1983, 11, 30)).theme == 'Deferred work'
        assert tours.script(5, date(1985, 11, 30)) is None
        assert tours.script(14, date(1983, 12, 31)) is None


class TestTheBoardIsNotBoilerplate:
    """R4: no fixed numbers, no other city's equipment."""

    def test_no_event_carries_a_fixed_base_number(self, terminal):
        for tour in range(1, 14):
            go_to(terminal, tour)
            for event in terminal.shift_events:
                assert not event['id'].startswith('EV-80'), event['id']
                assert event['id'].startswith(f'EV-{tour:02d}')

    def test_tour_one_and_tour_seven_draw_different_events(self, terminal):
        go_to(terminal, 1)
        first = terminal.shift_events
        go_to(terminal, 7)
        seventh = terminal.shift_events
        assert not {e['id'] for e in first} & {e['id'] for e in seventh}
        # Routine recurs, as it does; what is particular to the tour does not.
        set_pieces = [{e['title'] for e in events if e['origin'] == tours.SOURCED
                       or e['type'] in ('BULLETIN', 'EQUIPMENT')}
                      for events in (first, seventh)]
        assert set_pieces[0] and set_pieces[1]
        assert not set_pieces[0] & set_pieces[1]
        assert [e['title'] for e in first] != [e['title'] for e in seventh]

    def test_no_event_names_a_city_but_the_players_office(self, terminal):
        office = terminal.home_office
        for tour in range(1, 14):
            go_to(terminal, tour)
            assert terminal.shift_events
            for event in terminal.shift_events:
                text = event_text(event)
                for place in OTHER_PLACES:
                    if place.lower() in office['city'].lower():
                        continue
                    assert place not in text, (tour, event['id'], place)

    def test_an_event_that_names_a_place_names_this_office(self, terminal):
        go_to(terminal, 7)
        mentions = [e for e in terminal.shift_events
                    if terminal.home_office['clli'] in event_text(e)]
        assert mentions

    def test_the_same_tour_is_the_same_board_every_time(self, terminal):
        """Rebuilt when a saved shift is picked up; fired ids must still fit."""
        go_to(terminal, 4)
        once = [dict(event) for event in terminal.shift_events]
        go_to(terminal, 4)
        assert terminal.shift_events == once

    def test_the_board_holds_at_most_eight_and_is_in_time_order(
            self, terminal):
        for tour in range(1, 14):
            go_to(terminal, tour)
            times = [event['time'] for event in terminal.shift_events]
            assert times == sorted(times)
            assert 1 <= len(times) <= 8

    def test_every_event_says_where_it_came_from(self, terminal):
        for tour in range(1, 14):
            go_to(terminal, tour)
            for event in terminal.shift_events:
                assert event['origin'] in (tours.SOURCED, tours.OWN)

    def test_a_moved_epoch_gets_routine_and_no_set_pieces(self, terminal):
        terminal.settings.set('date.epoch', '1984-06-01')
        go_to(terminal, 3)
        assert terminal.shift_events
        assert all(e['origin'] == tours.OWN for e in terminal.shift_events)
        assert terminal.tour_brief() == []
        assert 'Thanksgiving' not in ' '.join(
            event_text(e) for e in terminal.shift_events)

    def test_events_detail_names_its_origin(self, terminal):
        go_to(terminal, 9)
        beat = next(e for e in terminal.shift_events
                    if e['origin'] == tours.SOURCED)
        detail = terminal.execute_command(f"events detail {beat['id']}")
        assert 'Origin:' in detail and 'Sourced' in detail
        assert '/usr/doc/divestiture' in detail

    def test_the_old_catalogue_is_gone(self):
        with pytest.raises(ImportError):
            __import__('bell_system.data.shift_events')


class TestBriefingAndGoals:
    """C15: two or three goals on the briefing, struck at handoff."""

    def test_every_tour_has_two_or_three_goals_that_can_be_read(self):
        for entry in tours.TOURS:
            assert 2 <= len(entry.goals) <= 3, entry.number
            for goal in entry.goals:
                assert goal.metric in tours.METRICS
                assert goal.op in ('>=', '<=')

    def test_shift_on_tour_five_shows_tour_fives_briefing(self, terminal):
        go_to(terminal, 5)
        shown = terminal.execute_command('shift')
        entry = tours.TOURS[4]
        assert 'Tour 5 of 13' in shown
        assert entry.theme in shown
        assert entry.briefing[0].strip() in shown
        for goal in entry.goals:
            assert goal.text in shown
        assert 'Tour 6 of 13' not in shown

    def test_shift_on_two_tours_does_not_read_the_same(self, terminal):
        go_to(terminal, 3)
        three = terminal.execute_command('shift')
        go_to(terminal, 9)
        nine = terminal.execute_command('shift')
        assert tours.TOURS[2].theme in three
        assert tours.TOURS[8].theme in nine
        assert tours.TOURS[2].theme not in nine

    def test_the_briefing_the_shift_opens_with_lists_the_goals(
            self, terminal, capsys):
        go_to(terminal, 8)
        terminal.role = 'sysop'
        terminal.show_shift_briefing()
        shown = capsys.readouterr().out
        assert 'Inventory for transfer' in shown
        for goal in tours.TOURS[7].goals:
            assert goal.text in shown

    def test_handoff_strikes_each_goal_as_met_or_missed(self, terminal):
        go_to(terminal, 2)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'TOUR GOALS' in out
        for goal in tours.TOURS[1].goals:
            row = next(line for line in out.split('\n') if goal.text in line)
            assert row.rstrip().endswith(('met', 'missed')), row

    def test_a_goal_is_met_when_the_tour_meets_it(self, terminal):
        go_to(terminal, 2)
        goal = tours.Goal('x', 'closed', '>=', 3)
        assert goal.met({'closed': 3}) and not goal.met({'closed': 2})
        goal = tours.Goal('x', 'late', '<=', 1)
        assert goal.met({'late': 1}) and not goal.met({'late': 2})

    def test_goal_progress_follows_the_tour(self, terminal):
        go_to(terminal, 2)
        before = terminal.goal_counts()
        assert before['closed'] == 0
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report close {report.number} 8')
        assert terminal.goal_counts()['closed'] == 1
        assert terminal.goal_counts()['wrong'] in (0, 1)

    def test_goals_never_change_the_index(self, terminal):
        go_to(terminal, 2)
        report = terminal.desk.pending()[0]
        terminal.execute_command(f'mlt {report.number}')
        terminal.execute_command(f'report close {report.number} 8')
        index = terminal.career.service_index()
        missed = terminal.career.missed_commitments
        terminal.goal_counts()
        terminal.goal_lines(final=True)
        terminal.execute_command('handoff')
        assert terminal.career.service_index() == index
        assert terminal.career.missed_commitments == missed

    def test_the_last_tour_prints_its_goals_in_the_account_of_the_career(
            self, terminal):
        terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
        go_to(terminal, 13)
        terminal.execute_command('report')
        out = terminal.execute_command('handoff relieve')
        assert 'TOUR GOALS' in out and 'THE CAREER' in out
        assert out.index('TOUR GOALS') < out.index('THE CAREER')


class TestNetnews:
    """C19: one item a tour, and nothing dated after the day."""

    def test_the_first_tour_has_the_original_spool(self, terminal):
        go_to(terminal, 1)
        assert terminal.execute_command('readnews').startswith(
            '14 articles waiting')

    def test_tour_one_and_tour_nine_list_different_items(self, terminal):
        go_to(terminal, 1)
        one = terminal.execute_command('readnews')
        go_to(terminal, 9)
        nine = terminal.execute_command('readnews')
        assert one != nine
        assert '22 articles waiting' in nine

    def test_the_feed_brings_one_article_each_tour_after_the_first(
            self, terminal):
        for tour in range(1, 14):
            go_to(terminal, tour)
            assert len(terminal._news_articles()) == 14 + tour - 1, tour

    def test_no_article_is_dated_after_the_tour(self, terminal):
        for tour in range(1, 14):
            go_to(terminal, tour)
            today = tours.TOURS[tour - 1].day
            for path in terminal._news_articles():
                text = terminal.filesystem[path].content
                assert article_date(text).date() <= today, (tour, path)

    def test_an_article_arrives_after_the_previous_tour_began(self):
        for entry in tours.TOURS:
            if entry.news is None:
                continue
            assert entry.news.posted.date() > tours.TOURS[
                entry.number - 2].day or entry.number == 1
            assert entry.news.posted.date() <= entry.day

    def test_a_new_article_is_a_file_cat_can_read(self, terminal):
        go_to(terminal, 12)
        path = '/usr/spool/news/net.news/54'
        assert path in terminal.filesystem
        assert 'RFC 850' in terminal.execute_command(f'cat {path}')
        listing = terminal.execute_command('ls /usr/spool/news/net.news')
        assert '54' in listing

    def test_delivery_is_idempotent(self, terminal):
        go_to(terminal, 6)
        once = dict(terminal.filesystem)
        terminal.deliver_news()
        terminal.deliver_news()
        assert terminal.filesystem == once

    def test_the_shared_tree_is_not_touched(self, terminal):
        from bell_system.filesystem import FILESYSTEM
        before = len(FILESYSTEM)
        go_to(terminal, 13)
        assert len(FILESYSTEM) == before

    def test_new_articles_keep_to_rfc_850(self, terminal):
        """The same checks the original spool is held to."""
        go_to(terminal, 13)
        required = ['Relay-Version', 'Posting-Version', 'Path', 'From',
                    'Newsgroups', 'Subject', 'Message-ID', 'Date']
        ids = []
        for path in terminal._news_articles():
            body = str(terminal.filesystem[path].content)
            headers = [line.split(':')[0]
                       for line in body.split('\n\n')[0].split('\n')]
            assert headers[:len(required)] == required, path
            route = next(line[6:] for line in body.split('\n')
                         if line.startswith('Path: '))
            sender = next(line[6:].split('@')[0] for line in body.split('\n')
                          if line.startswith('From: '))
            assert route.startswith('mhuxco!') and ' ' not in route, path
            assert route.split('!')[-1] == sender, path
            ids.append(next(line for line in body.split('\n')
                            if line.startswith('Message-ID: ')))
        assert len(ids) == len(set(ids))

    def test_the_date_header_names_the_right_weekday(self, terminal):
        go_to(terminal, 13)
        for path in terminal._news_articles():
            text = terminal.filesystem[path].content
            stamp = re.search(r'^Date: (\w+),', text, re.M).group(1)
            assert stamp == article_date(text).strftime('%A'), path

    def test_a_moved_epoch_does_not_get_this_calendars_news(self, terminal):
        terminal.settings.set('date.epoch', '1984-06-01')
        go_to(terminal, 13)
        assert len(terminal._news_articles()) == 14


class TestReviewOfTheFirstPass:
    """Things the review of the first pass found."""

    def test_no_tour_is_met_by_working_nothing(self):
        """A goal list of upper bounds alone is met by a desk nobody sat at."""
        idle = {metric: 0 for metric in tours.METRICS}
        for entry in tours.TOURS:
            assert not all(goal.met(idle) for goal in entry.goals),                 entry.number

    def test_a_preview_ticks_nothing_whatever_the_board_looks_like(
            self, terminal):
        """Unworked time ages the board before the tour is struck."""
        go_to(terminal, 12)
        assert terminal.goal_lines(final=False)
        for row in terminal.goal_lines(final=False):
            assert '[x]' not in row

    def test_the_preview_says_unworked_time_will_age_the_board(
            self, terminal):
        go_to(terminal, 12)
        assert 'Unworked time' in terminal.execute_command('handoff')
        assert 'Unworked time' in terminal.execute_command('shift')

    def test_the_final_strike_still_ticks_what_was_met(self, terminal):
        go_to(terminal, 2)
        assert any('[x]' in row for row in terminal.goal_lines(final=True))

    def test_the_shift_screen_has_no_stray_blank_line_without_a_brief(
            self, terminal):
        go_to(terminal, 2)
        terminal.settings.set('date.source', 'real')
        terminal.generate_shift_events()
        assert terminal.tour_brief(terminal.goal_counts()) == []
        shown = terminal.execute_command('shift')
        assert '=' * 62 + '\n\n' not in shown

    def test_an_own_beat_prints_only_its_source(self, terminal):
        go_to(terminal, 3)
        beat = next(e for e in terminal.shift_events
                    if e['origin'] == tours.OWN)
        detail = terminal.execute_command(f"events detail {beat['id']}")
        assert f"Origin:      {beat['source']}" in detail
        assert 'Own -' not in detail


class TestAnOldSaveMeetsTheNewIds:
    """A mid-tour save from before the tour script keeps the old numbers."""

    def old_save(self, terminal, minutes):
        go_to(terminal, 2)
        terminal.settings.set('game.prompts', 'off')
        terminal.execute_command('report')
        terminal.shift_minutes = minutes
        terminal._fired_events = {'EV-8001', 'EV-8002', 'EV-8003'}
        terminal.save_shift()
        fresh = BellSystemTerminal()
        fresh.career.qualifications = list(terminal.career.qualifications)
        return fresh

    def test_the_old_numbers_are_dropped(self, terminal):
        fresh = self.old_save(terminal, 200)
        assert fresh.resumed
        on_board = {e['id'] for e in fresh.shift_events}
        assert fresh._fired_events <= on_board

    def test_what_was_already_due_does_not_fire_as_a_burst(self, terminal):
        fresh = self.old_save(terminal, 200)
        assert fresh._fire_due_events() == []

    def test_what_is_not_yet_due_still_fires_in_its_time(self, terminal):
        fresh = self.old_save(terminal, 30)
        later = [e for e in fresh.shift_events
                 if e['id'] not in fresh._fired_events]
        assert later
        fresh.shift_minutes = 479
        assert fresh._fire_due_events()

    def test_a_current_save_is_left_exactly_as_it_was(self, terminal):
        go_to(terminal, 2)
        terminal.settings.set('game.prompts', 'off')
        terminal.execute_command('report')
        terminal.shift_minutes = 200
        terminal._fire_due_events()
        before = set(terminal._fired_events)
        terminal.save_shift()
        fresh = BellSystemTerminal()
        fresh.career.qualifications = list(terminal.career.qualifications)
        assert fresh.resumed
        assert fresh._fired_events == before
