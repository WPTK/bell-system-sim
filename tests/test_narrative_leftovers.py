"""
The narrative inconsistencies of issue #60 that were left after phases 7a and 7b.

Each class is one item of the bible's section 8. The state directory is a
temporary one for every test (``isolated_state`` in conftest).
"""

import re

from bell_system import save
from bell_system.data.homes import HOMES
from bell_system.field import CREWS
from bell_system.npc import CRAFT, Switchroom
from bell_system.progression import QUALIFICATIONS
from bell_system.terminal import BellSystemTerminal


class TestI6TheFieldNotesNameOnlyRealCrews:
    """A crew a note speaks of is one the dispatcher can send."""

    def test_the_crew_that_takes_the_fourth_job_is_on_the_crew_list(self):
        surnames = {crew.name.split(',')[0] for crew in CREWS}
        text = HOMES['field']['crews.notes']
        who = re.findall(r'(\w+) will take a fourth job', text)
        assert who and set(who) <= surnames, who

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

    def test_etc_ttys_lists_every_terminal_in_the_roster(self, terminal):
        listed = terminal.execute_command('cat /etc/ttys').split()
        assert listed[0] == '14console'
        assert sorted(line[2:] for line in listed[1:]) == sorted(
            f'tty{person.tty}' for person in CRAFT.values())

    def test_every_terminal_in_the_roster_is_a_device(self, terminal):
        listing = terminal.execute_command('ls /dev').split()
        for person in CRAFT.values():
            assert f'tty{person.tty}' in listing, person.login
