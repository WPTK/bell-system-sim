"""
The geographic dataset, and the guard that was missing when it broke.

The simulation used to read its geographic data from a path relative to the
working directory. From the source tree that loaded eighty numbering plan
areas; from anywhere else it caught FileNotFoundError and fell back to six
offices without a word. Every test ran from the repository root, so nothing
saw it.

These tests run from somewhere else on purpose.
"""

import gzip
import io
import os
import re

import pytest

from bell_system.data import geography


@pytest.fixture
def elsewhere(tmp_path, monkeypatch):
    """Run the test from a directory with no source tree in sight."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestPackagedDataset:
    """The data ships with the code."""

    def test_it_loads(self):
        assert geography.load()

    def test_it_carries_real_breadth(self):
        data = geography.load()
        assert len(data) >= 100, 'lost numbering plan areas'
        assert geography.office_count(data) >= 4000, 'lost central offices'

    def test_every_place_has_what_the_simulation_reads(self):
        for exchanges in geography.load().values():
            for places in exchanges.values():
                for place in places:
                    assert place['city']
                    assert place['state']
                    assert place['latitude']
                    assert place['longitude']

    def test_the_limit_argument_narrows_it(self):
        assert len(geography.load(limit_npas=5)) == 5


class TestPeriodAccuracy:
    """Only area codes that could have existed in 1978-1983."""

    def test_every_npa_uses_the_period_format(self):
        """
        Engineering and Operations (2nd ed., 1984) describes "the basic set of
        152 area codes possible using the N0/1X format". A middle digit other
        than 0 or 1 means the code was created in 1995 or later.
        """
        offenders = [npa for npa in geography.load()
                     if not re.match(r'^[2-9][01][0-9]$', npa)]
        assert not offenders, f'anachronistic area codes: {offenders}'

    def test_known_period_area_codes_are_present(self):
        data = geography.load()
        # Original 1947 numbering plan areas, all still in service in 1983.
        for npa in ('212', '213', '312', '415', '617', '202'):
            assert npa in data, f'{npa} missing'

    def test_a_post_1995_area_code_is_absent(self):
        data = geography.load()
        # 646 (New York, 1999) and 480 (Phoenix, 1999) postdate the period.
        assert '646' not in data
        assert '480' not in data

    def test_codes_created_after_the_period_are_absent(self):
        """
        The format rule alone lets these through; they are excluded by name.

        718 is the one the existing suite already guarded: it split from 212
        in September 1984, after the simulated shift.
        """
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from tools.build_nanpa import POST_PERIOD_NPAS

        data = geography.load()
        present = sorted(npa for npa in POST_PERIOD_NPAS if npa in data)
        assert not present, f'post-period area codes present: {present}'
        assert '718' in POST_PERIOD_NPAS

    def test_every_excluded_code_records_why(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from tools.build_nanpa import POST_PERIOD_NPAS

        for npa, note in POST_PERIOD_NPAS.items():
            assert re.match(r'^(198|199)\d, ', note), \
                f'{npa} must record the year it was created: {note!r}'


class TestLoadsFromAnywhere:
    """The regression guard. This is the test that did not exist."""

    def test_the_dataset_loads_from_another_directory(self, elsewhere):
        data = geography.load()
        assert len(data) >= 100
        assert geography.office_count(data) >= 4000

    def test_a_terminal_built_elsewhere_has_the_whole_network(self, elsewhere):
        from bell_system.terminal import BellSystemTerminal
        BellSystemTerminal._NANPA_CACHE = None
        BellSystemTerminal._NANPA_DEGRADED = False
        try:
            terminal = BellSystemTerminal()
            assert len(terminal.nanpa_data) >= 100
            assert len(terminal.central_offices) >= 4000
            assert not terminal.geography_degraded
        finally:
            BellSystemTerminal._NANPA_CACHE = None
            BellSystemTerminal._NANPA_DEGRADED = False

    def test_geographic_commands_work_from_another_directory(self, elsewhere):
        from bell_system.terminal import BellSystemTerminal
        BellSystemTerminal._NANPA_CACHE = None
        try:
            terminal = BellSystemTerminal()
            terminal.settings.set('game.ambience', 'off')
            result = terminal.execute_command('trouble geographic')
            assert 'Command execution error' not in result
            assert result.strip()
        finally:
            BellSystemTerminal._NANPA_CACHE = None
            BellSystemTerminal._NANPA_DEGRADED = False

    def test_the_working_directory_does_not_change_the_answer(self, tmp_path,
                                                              monkeypatch):
        from_here = geography.office_count(geography.load())
        monkeypatch.chdir(tmp_path)
        from_there = geography.office_count(geography.load())
        assert from_here == from_there


class TestFailsLoudly:
    """Missing data is announced, never silently substituted."""

    def test_an_unreadable_dataset_raises(self, monkeypatch):
        def broken(_package):
            raise FileNotFoundError('gone')
        monkeypatch.setattr(geography, '_resource_files', broken)
        with pytest.raises(geography.GeographyUnavailable) as caught:
            geography.load()
        assert geography.DATASET in str(caught.value)

    def test_an_empty_dataset_raises(self, monkeypatch):
        empty = io.TextIOWrapper(
            gzip.GzipFile(fileobj=io.BytesIO(
                gzip.compress(b'npa,nxx,city,state,latitude,longitude\n'))),
            encoding='utf-8')
        monkeypatch.setattr(geography, '_open_dataset', lambda: empty)
        with pytest.raises(geography.GeographyUnavailable):
            geography.load()

    def test_the_terminal_marks_itself_degraded_and_logs_it(self, monkeypatch,
                                                            caplog):
        from bell_system.terminal import BellSystemTerminal

        def unavailable(*_args, **_kwargs):
            raise geography.GeographyUnavailable('test')
        monkeypatch.setattr(geography, 'load', unavailable)
        BellSystemTerminal._NANPA_CACHE = None
        BellSystemTerminal._NANPA_DEGRADED = False
        try:
            terminal = BellSystemTerminal()
            assert terminal.geography_degraded
            assert terminal.nanpa_data
            assert any('Geographic data unavailable' in record.message
                       for record in caplog.records)
        finally:
            BellSystemTerminal._NANPA_CACHE = None
            BellSystemTerminal._NANPA_DEGRADED = False


class TestBuildScript:
    """The dataset must be reproducible from its source."""

    def test_the_build_script_documents_the_period_filter(self):
        path = os.path.join(os.path.dirname(__file__), '..',
                            'tools', 'build_nanpa.py')
        source = open(path).read()
        assert 'N0/1X' in source, 'the period filter must cite its source'
        assert 'Engineering and Operations' in source
