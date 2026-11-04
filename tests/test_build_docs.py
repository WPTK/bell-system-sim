"""The documentation site is generated from the in-game man pages."""

import importlib.util
import sys
from pathlib import Path

import pytest

from bell_system.data.man_pages import DESK_SECTIONS, MAN_PAGES

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope='module')
def build_docs():
    spec = importlib.util.spec_from_file_location(
        'build_docs_under_test', ROOT / 'tools' / 'build_docs.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def site(build_docs, tmp_path_factory):
    out = tmp_path_factory.mktemp('docs-build')
    count, files = build_docs.build(out)
    return out, count, files


class TestTheGeneratedSite:
    def test_one_page_per_man_page(self, site):
        out, count, _ = site
        pages = [p for p in (out / 'command-reference').rglob('*.md')
                 if p.name != 'index.md']
        assert count == len(MAN_PAGES) == len(pages)
        assert {p.stem for p in pages} == set(MAN_PAGES)

    def test_each_page_holds_the_man_text_unchanged(self, site):
        out, _, _ = site
        for page in (out / 'command-reference').rglob('*.md'):
            if page.name == 'index.md':
                continue
            assert MAN_PAGES[page.stem].rstrip() in page.read_text(
                encoding='utf-8')

    def test_the_home_page_and_the_index_exist(self, site):
        out, _, files = site
        assert (out / 'index.md').read_text(encoding='utf-8').startswith(
            '# Getting started')
        assert files == len(MAN_PAGES) + 2

    def test_the_index_links_every_page(self, site):
        out, _, _ = site
        index = (out / 'command-reference' / 'index.md').read_text(encoding='utf-8')
        for name in MAN_PAGES:
            assert f"`{name}`](" in index

    def test_a_desk_only_section_is_shown_on_its_page(self, site):
        out, _, _ = site
        for name, by_position in DESK_SECTIONS.items():
            page = next((out / 'command-reference').rglob(f'{name}.md'))
            text = page.read_text(encoding='utf-8')
            for extra in by_position.values():
                assert extra.rstrip() in text

    def test_every_page_is_in_exactly_one_section(self, build_docs):
        for name in MAN_PAGES:
            assert build_docs.section_of(name) in {
                slug for slug, _, _ in build_docs.SECTIONS}

    def test_the_fence_survives_backticks_in_the_text(self, build_docs):
        block = build_docs.fence("one ``` two\n")
        assert block.startswith('````text\n')
        assert block.rstrip().endswith('````')


class TestTheGeneratorWillNotDeleteTheRepository:
    def test_it_refuses_the_repository_root(self, build_docs):
        with pytest.raises(ValueError):
            build_docs.build(ROOT)

    def test_it_refuses_a_directory_holding_tracked_files(self, build_docs):
        for name in ('docs', 'src', 'tools'):
            with pytest.raises(ValueError):
                build_docs.build(ROOT / name)
        assert (ROOT / 'tools' / 'build_docs.py').exists()
        assert (ROOT / 'docs' / 'site' / 'index.md').exists()

    def test_it_refuses_a_parent_of_the_repository(self, build_docs):
        with pytest.raises(ValueError):
            build_docs.build(ROOT.parent)

    def test_main_reports_a_refusal_and_exits_nonzero(self, build_docs,
                                                      capsys):
        assert build_docs.main(['build_docs.py', str(ROOT / 'docs')]) == 2
        assert 'refusing' in capsys.readouterr().err


class TestTheGeneratorOnlyReplacesItsOwnOutput:
    def test_it_refuses_a_directory_with_files_it_did_not_write(
            self, build_docs, tmp_path):
        mine = tmp_path / 'notes'
        mine.mkdir()
        (mine / 'keep.txt').write_text('local only', encoding='utf-8')
        with pytest.raises(ValueError):
            build_docs.build(mine)
        assert (mine / 'keep.txt').read_text(encoding='utf-8') == 'local only'

    def test_it_refuses_an_untracked_directory_inside_the_repository(
            self, build_docs):
        out = ROOT / 'untracked-local-notes'
        out.mkdir()
        try:
            (out / 'keep.txt').write_text('local only', encoding='utf-8')
            with pytest.raises(ValueError):
                build_docs.build(out)
            assert (out / 'keep.txt').exists()
        finally:
            (out / 'keep.txt').unlink()
            out.rmdir()

    def test_it_replaces_its_own_earlier_output(self, build_docs, tmp_path):
        out = tmp_path / 'site-source'
        build_docs.build(out)
        (out / 'stale.md').write_text('old', encoding='utf-8')
        build_docs.build(out)
        assert not (out / 'stale.md').exists()
        assert (out / build_docs.MARKER).exists()

    def test_it_accepts_an_empty_or_new_directory(self, build_docs, tmp_path):
        empty = tmp_path / 'empty'
        empty.mkdir()
        build_docs.build(empty)
        build_docs.build(tmp_path / 'new')
