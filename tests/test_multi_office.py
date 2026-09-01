"""
Working an office you are not standing in.

The switching control centre sign-off said "remote administration of
offices from the control centre" and paid out in two commands that both
stay in your own building. This is that qualification cashed: eleven
buildings on one console, each with its own alarms, each belonging to an
operating company that goes somewhere specific in forty-eight days.
"""


import pytest

from bell_system.data.companies import (
    COMPANIES,
    COMPANIES_BY_STATE,
    NOT_WHOLLY_OWNED,
    RBOCS,
    for_state,
)
from bell_system.data.clli import STATE_CODES, is_valid


class TestTheOperatingCompanies:
    """Twenty-one companies going to seven regions."""

    def test_every_company_goes_to_a_real_region(self):
        for key, company in COMPANIES.items():
            assert company.rboc in RBOCS, (key, company.rboc)

    def test_every_region_gets_at_least_one_company(self):
        assigned = {company.rboc for company in COMPANIES.values()}
        assert assigned == set(RBOCS)

    def test_no_state_is_served_by_two_companies(self):
        seen = {}
        for company in COMPANIES.values():
            for state in company.states:
                assert state not in seen, (state, seen.get(state), company.key)
                seen[state] = company.key

    def test_the_verified_ones_are_the_ones_the_book_gives(self):
        """
        Engineering and Operations gives Pacific Telesis, Ameritech and
        Bell Atlantic in full. Everything else is externally sourced and
        must say so, so that a wrong one can be found.
        """
        for company in COMPANIES.values():
            if company.verified:
                assert company.rboc in ('PACIFIC TELESIS', 'AMERITECH',
                                        'BELL ATLANTIC'), company.key

    def test_the_minority_held_two_are_recorded_and_absent(self):
        """
        AT&T held only a minority stake in Southern New England Telephone
        and Cincinnati Bell, so neither divests and neither belongs in the
        table. Recording why beats leaving a hole.
        """
        assert 'CT' in NOT_WHOLLY_OWNED
        assert for_state('CT') is None
        assert 'Southern New England' in NOT_WHOLLY_OWNED['CT']

    def test_every_state_code_is_a_real_one(self):
        codes = set(STATE_CODES.values())
        for state in COMPANIES_BY_STATE:
            assert state in codes, state

    def test_new_jersey_goes_to_bell_atlantic(self):
        """The office this simulation is set in."""
        company = for_state('NJ')
        assert company.name == 'New Jersey Bell'
        assert company.rboc == 'BELL ATLANTIC'
        assert company.verified

    def test_every_company_has_something_to_say_about_itself(self):
        for key, company in COMPANIES.items():
            assert len(company.note) > 40, key
            assert company.note.endswith('.'), key


class TestTheConsole:
    """Eleven buildings, each of them distinguishable."""

    def test_it_watches_more_than_one_office(self, terminal):
        assert len(terminal.watched_offices()) > 1

    def test_every_office_on_it_is_distinct(self, terminal):
        """
        A CLLI names a building. A console listing one code twice is one
        you cannot connect from, because there is no way to say which you
        meant - and the office table does generate duplicates.
        """
        codes = [office['clli'] for office in terminal.watched_offices()]
        assert len(set(codes)) == len(codes)

    def test_every_code_on_it_is_a_valid_clli(self, terminal):
        for office in terminal.watched_offices():
            assert is_valid(office['clli']), office['clli']

    def test_the_listing_marks_where_you_are(self, terminal):
        assert '*' in terminal.execute_command('connect')

    def test_your_own_office_is_on_it(self, terminal):
        codes = {office['clli'] for office in terminal.watched_offices()}
        assert terminal.home_office['clli'] in codes


class TestConnecting:
    """Reaching another building, and coming back."""

    def other(self, terminal):
        """An office on the console that is not the home one."""
        return next(office for office in terminal.watched_offices()
                    if office['clli'] != terminal.home_office['clli'])

    def test_you_start_at_your_own_office(self, terminal):
        assert not terminal.office_is_remote()
        assert (terminal.current_office()['clli']
                == terminal.home_office['clli'])

    def test_connecting_by_code_works(self, terminal):
        target = self.other(terminal)
        result = terminal.execute_command(f"connect {target['clli']}")
        assert 'Connected to' in result
        assert terminal.office_is_remote()
        assert terminal.current_office()['clli'] == target['clli']

    def test_connecting_by_place_works(self, terminal):
        target = self.other(terminal)
        terminal.execute_command(f"connect {target['city'].split()[0]}")
        assert terminal.office_is_remote()

    def test_connecting_by_number_works(self, terminal):
        terminal.execute_command('connect 2')
        assert terminal.current_office()['clli'] == (
            terminal.watched_offices()[1]['clli'])

    def test_coming_home_works(self, terminal):
        terminal.execute_command(f"connect {self.other(terminal)['clli']}")
        result = terminal.execute_command('connect home')
        assert 'Disconnected' in result
        assert not terminal.office_is_remote()

    def test_coming_home_twice_says_so(self, terminal):
        assert 'already' in terminal.execute_command('connect home')

    def test_an_unknown_office_is_refused(self, terminal):
        assert 'no office of that name' in terminal.execute_command(
            'connect NOWHERE99XX0')

    def test_the_card_says_whose_office_it_is(self, terminal):
        result = terminal.execute_command(
            f"connect {self.other(terminal)['clli']}")
        assert 'OPERATING COMPANY' in result
        assert '1 January 1984' in result

    def test_a_remote_console_says_it_is_remote(self, terminal):
        assert terminal.remote_banner() == ''
        terminal.execute_command(f"connect {self.other(terminal)['clli']}")
        assert 'not this building' in terminal.remote_banner()


class TestEachOfficeHasItsOwnState:
    """A console is only worth having if the offices differ."""

    def test_offices_are_in_different_states(self, terminal):
        counts = {len(terminal.office_alarms(office))
                  for office in terminal.watched_offices()}
        assert len(counts) > 1, 'every office on the console is identical'

    def test_the_same_office_gives_the_same_answer_twice(self, terminal):
        """
        Generated from the CLLI, so two looks agree. The mistake cosmos
        jumper had to be fixed for.
        """
        office = terminal.watched_offices()[3]
        first = [alarm['id'] for alarm in terminal.office_alarms(office)]
        second = [alarm['id'] for alarm in terminal.office_alarms(office)]
        assert first == second

    def test_no_two_offices_share_an_alarm_identifier(self, terminal):
        seen = set()
        for office in terminal.watched_offices():
            for alarm in terminal.office_alarms(office):
                assert alarm['id'] not in seen, alarm['id']
                seen.add(alarm['id'])

    def test_the_alarm_screen_reads_the_connected_office(self, terminal):
        target = next(office for office in terminal.watched_offices()
                      if office['clli'] != terminal.home_office['clli'])
        terminal.execute_command(f"connect {target['clli']}")
        assert target['clli'] in terminal.execute_command('alarm')

    def test_acknowledging_one_office_does_not_touch_another(self, terminal):
        offices = [o for o in terminal.watched_offices()
                   if terminal.office_alarms(o)]
        if len(offices) < 2:
            pytest.skip('this office table gave one alarmed building')
        first, second = offices[0], offices[1]
        target = terminal.office_alarms(first)[0]['id']
        terminal.execute_command(f"connect {first['clli']}")
        terminal.execute_command(f'alarm ack {target}')
        assert all(not alarm['acknowledged']
                   for alarm in terminal.office_alarms(second))

    def test_the_home_office_keeps_the_alarms_it_was_dealt(self, terminal):
        assert (terminal.office_alarms(terminal.home_office)
                is terminal.active_alarms)


class TestTheCompanyCommand:
    """Whose office, and where it goes."""

    def test_it_names_the_company_and_the_region(self, terminal):
        result = terminal.execute_command('company')
        assert 'New Jersey Bell' in result
        assert 'Bell Atlantic' in result

    def test_a_state_can_be_asked_about(self, terminal):
        assert 'Illinois Bell' in terminal.execute_command('company IL')
        assert 'Ameritech' in terminal.execute_command('company IL')

    def test_connecticut_says_why_it_is_not_in_the_table(self, terminal):
        result = terminal.execute_command('company CT')
        assert 'minority' in result
        assert 'not part of the divestiture' in result

    def test_the_whole_table_fits_a_screen(self, terminal):
        result = terminal.execute_command('company all')
        assert max(len(line) for line in result.split('\n')) <= 74
        for company in COMPANIES.values():
            assert company.name[:36] in result

    def test_externally_sourced_assignments_are_marked(self, terminal):
        result = terminal.execute_command('company all')
        assert '?' in result
        assert 'outside the bundled' in result

    def test_a_bad_state_code_is_refused(self, terminal):
        assert 'two-letter' in terminal.execute_command('company nonsense')


class TestTheSignOffPaysOutInWork:
    """The control centre hands you an office, which is the point."""

    def test_connect_is_what_the_scc_qualification_unlocks(self):
        from bell_system.progression import QUALIFICATIONS_BY_KEY
        assert 'connect' in QUALIFICATIONS_BY_KEY['scc'].unlocks

    def test_an_unqualified_position_cannot_connect(self, raw_terminal):
        assert 'not signed off' in raw_terminal.execute_command('connect')

    def test_the_control_centre_assigns_an_office(self, terminal):
        message = None
        for _ in range(30):
            terminal._scc_assigned = None
            message = terminal.scc_assignment()
            if message:
                break
        assert message is not None
        assert 'yours for the tour' in message
        assert 'connect' in message

    def test_it_never_assigns_the_office_you_are_sitting_in(self, terminal):
        for _ in range(20):
            terminal._scc_assigned = None
            message = terminal.scc_assignment()
            if message:
                assert terminal.home_office['clli'] not in message

    def test_it_only_assigns_once(self, terminal):
        first = None
        for _ in range(30):
            terminal._scc_assigned = None
            first = terminal.scc_assignment()
            if first:
                break
        if first is None:
            pytest.skip('nothing on this console was worth assigning')
        assert terminal.scc_assignment() is None

    def test_it_assigns_an_office_worth_looking_at(self, terminal):
        terminal._scc_assigned = None
        message = terminal.scc_assignment()
        if message is None:
            return
        clli = terminal._scc_assigned
        office = next(o for o in terminal.watched_offices()
                      if o['clli'] == clli)
        assert terminal.office_alarms(office)
