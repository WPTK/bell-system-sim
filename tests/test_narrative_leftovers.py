"""
The narrative inconsistencies of issue #60 that were left after phases 7a and 7b.

Each class is one item of the bible's section 8. The state directory is a
temporary one for every test (``isolated_state`` in conftest).
"""

import os
import re
from datetime import datetime

from bell_system import save
from bell_system.data.homes import HOMES
from bell_system.data.tours import TOURS
from bell_system.field import CREWS
from bell_system.filesystem import (
    DIVESTITURE_MEMO, FILESYSTEM, GROUP, NEWS_GENERAL_203, NEWS_MISC_88,
    PASSWD, TESTLOG_C,
)
from bell_system.npc import CRAFT, MACHINES, PLAYER_TTY, Switchroom
from bell_system.progression import QUALIFICATIONS
from bell_system.terminal import BellSystemTerminal


class TestTheItemsPhases7And7bFixedStayFixed:
    """I1, I4, I10 and I12 had no test of their own."""

    def test_i1_the_teletype_line_is_the_sulog_line(self):
        from bell_system import npc
        with open(npc.__file__, encoding='utf-8') as handle:
            source = handle.read()
        assert 'BADSU 11/14 03:47 - tty07 mreyes-root' in source
        assert '07:52' not in source
        assert 'SU 11/14 03:47 - tty07 mreyes-root' in FILESYSTEM[
            '/usr/adm/sulog'].content

    def test_i4_both_homes_name_the_sequence_relay(self):
        marker = FILESYSTEM['/usr/users/rjohnson/marker.notes'].content
        assert 'sequence relay' in marker
        assert 'sequence relay' in HOMES['switch']['aisle.notes']

    def test_i10_alvarez_signs_the_evening_tour(self):
        assert 'R. Alvarez, evening tour' in HOMES['sysop']['notes']
        assert 'R. Alvarez, evening tour' in TESTLOG_C
        assert 'tour 2' not in TESTLOG_C

    def test_i12_a_regular_has_a_street_and_no_city(self):
        from bell_system.data.regulars import REGULARS
        for regular in REGULARS.values():
            assert ',' not in regular.address, regular.address
            assert 'Jersey' not in regular.address


class TestI6TheFieldNotesNameOnlyRealCrews:
    """A crew a note speaks of is one the dispatcher can send."""

    def test_the_note_lists_the_crews_there_are(self):
        text = HOMES['field']['crews.notes']
        assert 'This wire centre has two cable splicers, a lineman, a station ' \
            'installer and a switching equipment technician' in text
        assert 'three splicing crews' not in text

    def test_the_note_offers_no_dispatch_tip_with_nothing_behind_it(self):
        assert 'fourth job' not in HOMES['field']['crews.notes']

    def test_no_note_speaks_of_a_crew_that_is_somebody_elses_trade(self):
        surnames = {crew.name.split(',')[0] for crew in CREWS}
        for files in HOMES.values():
            for text in files.values():
                for name in re.findall(r"(\w+)'s crew", text):
                    assert name in surnames, name


class TestI7OneTitlePerPerson:
    """A person has the title the roster gives them, wherever they appear."""

    def test_a_field_crew_is_its_roster_entry(self):
        by_name = {person.name: person for person in CRAFT.values()}
        for crew in CREWS:
            person = by_name[crew.name]
            assert crew.title == person.title, crew.name
            assert crew.key == person.login[1:], crew.name

    def test_the_central_office_crew_is_the_switching_technician(self):
        office = [crew for crew in CREWS if crew.force == 'Central office']
        assert [crew.name for crew in office] == ['Johnson, R.']
        assert office[0].title == 'Switching Equipment Technician'
        sender = Switchroom.FORCE_SENDERS['Central office']
        assert CRAFT[sender].name == office[0].name

    def test_the_transmission_engineer_is_not_a_crew(self):
        assert 'Nakamura, T.' not in {crew.name for crew in CREWS}

    def test_a_shift_saved_with_the_old_crew_key_still_dispatches(
            self, isolated_state):
        """The crew list used to hold Nakamura where Johnson now is."""
        def fresh():
            terminal = BellSystemTerminal()
            terminal.career.qualifications = [q.key for q in QUALIFICATIONS]
            terminal.career.shift = 2
            terminal.clock.set_tour(2)
            return terminal

        stored = save.capture(fresh())
        at = stored['force']['at']
        at['nakamura'] = at.pop('johnson')
        terminal = fresh()
        assert save.restore(terminal, stored)
        force = terminal.desk.force
        assert 'johnson' not in force.at
        crew, travel, came_from = force.send('Central office', 'TR-00001',
                                             30, 0)
        assert crew is not None and crew.name == 'Johnson, R.'
        assert came_from == 'upstairs'


class TestI8OneTerminalEach:
    """The roster, /etc/ttys and /dev agree, and no two people share a line."""

    def test_no_two_of_the_roster_share_a_terminal(self):
        ttys = [person.tty for person in CRAFT.values()]
        assert len(ttys) == len(set(ttys)), ttys

    def test_the_player_has_a_terminal_of_their_own(self):
        assert PLAYER_TTY not in [person.tty for person in CRAFT.values()]

    def test_etc_ttys_lists_the_roster_and_the_players_terminal(self, terminal):
        listed = terminal.execute_command('cat /etc/ttys').split()
        assert listed[0] == '14console'
        assert sorted(line[2:] for line in listed[1:]) == sorted(
            [f'tty{person.tty}' for person in CRAFT.values()]
            + [f'tty{PLAYER_TTY}'])

    def test_a_machines_line_is_disabled_and_a_persons_is_not(self, terminal):
        flags = {line[2:]: line[0] for line in
                 terminal.execute_command('cat /etc/ttys').split()[1:]}
        for person in CRAFT.values():
            expected = '0' if person.login in MACHINES else '1'
            assert flags[f'tty{person.tty}'] == expected, person.login
        assert flags[f'tty{PLAYER_TTY}'] == '1'

    def test_every_terminal_is_a_device(self, terminal):
        listing = terminal.execute_command('ls /dev').split()
        for number in [p.tty for p in CRAFT.values()] + [PLAYER_TTY]:
            assert f'tty{number}' in listing, number

    def test_the_banner_tty_wall_and_the_sulog_use_the_players_terminal(
            self, terminal):
        assert terminal.execute_command('tty').strip() == (
            f'/dev/tty{PLAYER_TTY}')
        said = terminal.execute_command('wall hello')
        assert f'from {terminal.username} tty{PLAYER_TTY}' in said
        sender = re.search(r'^Message from (\w+) tty(\d+)', said, re.M)
        assert sender and CRAFT[sender.group(1)].tty == sender.group(2)
        terminal.execute_command('su root')
        sulog = terminal.filesystem['/usr/adm/sulog'].content
        assert f'- tty{PLAYER_TTY} {terminal.username or "sysop"}-root' in sulog
        assert 'tty01 sysop' not in sulog


class TestI11MessageIdsRunInDateOrder:
    """A site numbers its articles as it posts them."""

    def test_each_sites_ids_rise_with_the_dates(self):
        posted = []
        for path, node in FILESYSTEM.items():
            if path.startswith('/usr/spool/news/') and not node.is_dir:
                text = node.content
                ident = re.search(r'^Message-ID: <(\d+)@(\w+)\.UUCP>$', text,
                                  re.M)
                date = re.search(r'^Date: (.+) EST$', text, re.M)
                assert ident and date, path
                stamp = datetime.strptime(date.group(1), '%A, %d-%b-%y %H:%M:%S')
                posted.append((ident.group(2), int(ident.group(1)), stamp))
        for tour in TOURS:
            if tour.news is not None:
                item = tour.news
                serial = int(item.message_id[1:].split('@')[0])
                posted.append((item.posting, serial, item.posted))
        assert len(posted) > 15
        for site in {site for site, _, _ in posted}:
            ordered = sorted((serial, stamp) for s, serial, stamp in posted
                             if s == site)
            stamps = [stamp for _, stamp in ordered]
            assert stamps == sorted(stamps), (site, ordered)

    def test_the_references_point_at_an_earlier_id(self):
        text = FILESYSTEM['/usr/spool/news/net.sources/44'].content
        assert 'References: <44@mhuxco.UUCP>' in text
        assert 'Message-ID: <45@mhuxco.UUCP>' in text


class TestI13I14PeriodClaimsAreSourcedOrGone:
    """A figure that no document here gives is not in the game's text."""

    def test_the_unsourced_figures_are_not_in_the_notes_or_the_memo(self):
        noc = HOMES['noc']['watch.notes']
        tsps = HOMES['tsps']['position.notes']
        assert 'forty years' not in noc and 'busiest' not in noc
        assert 'heaviest' not in noc
        assert 'thirty seconds' not in tsps and 'hundred' not in tsps
        assert 'class 4' not in DIVESTITURE_MEMO
        assert 'class 4' not in NEWS_GENERAL_203

    def test_each_claim_that_stayed_has_a_row_in_sources(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'SOURCES.md'), encoding='utf-8') as handle:
            sources = handle.read()
        for needle in ("Long-haul calling jams the intertoll trunks on Mother's Day",
                       'about 250 milliseconds one way',
                       'service between LATAs is offered by AT&T and other interexchange carriers',
                       'UNIX Version 7'):
            assert needle in sources, needle


class TestI9SandovalsOldAccount:
    """
    Sandoval has a login here and posts from mhuxt. Both are meant (T3):
    the news account did not move with him.
    """

    def test_he_has_a_login_and_the_craft_group_here(self):
        assert 'jsandoval:' in PASSWD
        members = GROUP.split('craft::10:')[1].split('\n')[0].split(',')
        assert 'jsandoval' in members

    def test_everything_he_posts_is_from_the_old_site(self):
        assert 'site mhuxt.UUCP' in NEWS_MISC_88
        posts = [tour.news for tour in TOURS
                 if tour.news is not None
                 and tour.news.sender.startswith('jsandoval@')]
        assert posts and {item.posting for item in posts} == {'mhuxt'}
