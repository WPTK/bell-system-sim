"""
The ending reads the career (C23).

Careers are built here by setting the saved fields the ending reads, on a
career that has reached the last tour, not by playing whatever an unseeded
board deals. The words are tested as a table; one run through the real
terminal proves they reach the screen.
"""

import re


from bell_system.clock import TOURS_TO_DIVESTITURE
from bell_system.data.companies import for_state
from bell_system.data.epilogue import Ring, Shape, halloran_note, pieces
from bell_system.data.finds import FRAGMENTS_BY_KEY
from bell_system.data.trouble import FAULTS
from bell_system.npc import AUDIT_EXCEPTIONS, AUDIT_FAILED, AUDIT_PASSED
from bell_system import ending

RING = Ring('TR-04001', '201-200-1234', '14:30', 'open')


def shape(**changes):
    """A shape with nothing in it, changed by what a test is about."""
    base = dict(
        verdict=AUDIT_PASSED, closed=40, open_count=3,
        company='New Jersey Bell Telephone Company', holding='Bell Atlantic',
        outside='', heard=frozenset(), favours=frozenset(),
        finds=frozenset(), commendations=frozenset(), ring=RING)
    base.update(changes)
    return Shape(**base)


def said(subject):
    """Everything the epilogue says for a shape, as one string."""
    chief = halloran_note(subject)
    return '\n'.join([line for _, _, lines in pieces(subject)
                      for line in lines] + chief)


SHAPES = {
    'plain': shape(),
    'failed': shape(verdict=AUDIT_FAILED, closed=0, ring=None),
    'reader': shape(finds=frozenset({'lmoslog', 'reopened', 'retain'}),
                    heard=frozenset({'sandoval.2'})),
    'liked': shape(favours=frozenset({'mreyes', 'jsandoval'}),
                   commendations=frozenset({'first_clean_tour'})),
}


class TestFourCareers:
    def test_four_shapes_four_epilogues(self):
        texts = {name: said(held) for name, held in SHAPES.items()}
        assert len(set(texts.values())) == len(SHAPES)

    def test_each_names_the_players_own_company(self):
        for name, held in SHAPES.items():
            if held.company:
                assert held.company in said(held), name

    def test_every_piece_is_two_short_lines(self):
        for name, held in SHAPES.items():
            for _channel, _sender, lines in pieces(held):
                assert len(lines) == 2, name
                assert all(len(line) <= 100 for line in lines), (name, lines)

    def test_a_failed_audit_changes_the_words_and_not_the_length(self):
        passed = shape(verdict=AUDIT_PASSED)
        for verdict in (AUDIT_EXCEPTIONS, AUDIT_FAILED):
            changed = shape(verdict=verdict)
            assert said(changed) != said(passed)
            assert ([len(lines) for *_, lines in pieces(changed)]
                    == [len(lines) for *_, lines in pieces(passed)])

    def test_reyes_says_no_more_than_the_player_has_read(self):
        nothing = said(shape())
        assert '03:47' not in nothing and 'reopened' not in nothing
        assert '03:47' in said(shape(finds=frozenset({'lmoslog'})))
        both = said(shape(finds=frozenset({'lmoslog', 'reopened'})))
        assert 'reopened' in both and '06:15' in both

    def test_sandoval_names_the_company_only_after_the_memo_beat(self):
        assert 'The memo means' not in said(shape())
        heard = said(shape(heard=frozenset({'sandoval.2'})))
        assert 'The memo means New Jersey Bell' in heard

    def test_a_state_with_no_company_is_said_as_it_is(self):
        held = shape(company='', holding='',
                     outside='Southern New England Telephone Company')
        assert 'minority-held' in said(held)

    def test_a_holding_company_only_where_the_assignment_is_verified(self):
        assert 'Bell Atlantic' in said(shape())
        assert 'holding company' not in said(shape(holding=''))

    def test_it_never_names_a_fault_or_a_disposition(self):
        """Pillar 1: no answer key to a later board."""
        # 'open' is left out: a report goes over open, which is the board.
        names = [fault.name.lower() for fault in FAULTS.values()
                 if ' ' in fault.name] + ['short', 'ground', 'cross']
        codes = [re.compile(rf'\b{code}\b') for code in FAULTS]
        for name, held in SHAPES.items():
            text = said(held)
            assert not any(re.search(rf'{word}', text.lower())
                           for word in names), name
            assert not any(code.search(text) for code in codes), name
            assert 'code 5' not in text and 'code 8' not in text

    def test_the_machine_does_not_say_you(self):
        for held in SHAPES.values():
            teletype = pieces(held)[0]
            assert not re.search(r'\byou\b', ' '.join(teletype[2]).lower())

    def test_the_finds_it_listens_for_exist(self):
        for key in ('lmoslog', 'reopened', 'retain'):
            assert key in FRAGMENTS_BY_KEY


class TestReadingTheCareer:
    def test_shape_is_read_from_the_saved_fields(self, terminal):
        career = terminal.career
        career.office = {**career.office, 'state': 'NJ'}
        career.finds = ['lmoslog']
        career.beats_seen = ['sandoval.2', 'favour:mreyes', 'settled:x']
        career.commendations = ['first_clean_tour']
        held = ending.shape_of(career, terminal.desk, AUDIT_PASSED)
        assert held.finds == {'lmoslog'}
        assert held.heard == {'sandoval.2'}
        assert held.favours == {'mreyes'}
        assert held.commendations == {'first_clean_tour'}
        assert held.company == for_state('NJ').name

    def test_a_state_with_no_company_gets_the_minority_held_one(
            self, terminal):
        terminal.career.office = {**terminal.career.office, 'state': 'CT'}
        held = ending.shape_of(terminal.career, terminal.desk, AUDIT_PASSED)
        assert held.company == ''
        assert 'Southern New England' in held.outside


class TestOnTheLastDay:
    def last_tour(self, terminal, state='NJ'):
        terminal.career.shift = TOURS_TO_DIVESTITURE
        terminal.career.office = {**terminal.career.office, 'state': state}
        terminal.career.save()
        terminal.clock.set_tour(terminal.career.shift)
        terminal.desk.reports.clear()
        terminal.desk.order.clear()
        terminal.desk.open_shift(terminal.clock.now(), 0, count=6)
        terminal.execute_command('report')

    def test_the_screen_carries_the_epilogue_in_order(self, terminal):
        self.last_tour(terminal)
        out = terminal.execute_command('handoff relieve')
        company = for_state('NJ').name
        assert company in out
        order = [out.index(text) for text in
                 ('THE AUDIT', 'MAINTENANCE TTY', 'Message from mreyes',
                  'ORDER WIRE', 'Message from ehalloran')]
        assert order == sorted(order)

    def test_the_company_is_kept_as_the_assignment(self, terminal):
        self.last_tour(terminal)
        terminal.execute_command('handoff relieve')
        assert terminal.career.assignment == for_state('NJ').name

    def test_a_failed_audit_still_ends_on_the_chief(self, terminal):
        self.last_tour(terminal)
        out = terminal.execute_command('handoff relieve')
        assert 'FAILED' in out
        assert out.index('Go home.') > out.index('Message from mreyes')
        assert terminal.career.finished

    def test_connecticut_ends_without_a_company(self, terminal):
        self.last_tour(terminal, state='CT')
        out = terminal.execute_command('handoff relieve')
        assert 'minority-held' in out
