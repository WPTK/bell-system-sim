"""
The narrative inconsistencies of issue #60 that were left after phases 7a and 7b.

Each class is one item of the bible's section 8. The state directory is a
temporary one for every test (``isolated_state`` in conftest).
"""

import re

from bell_system.data.homes import HOMES
from bell_system.field import CREWS


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
