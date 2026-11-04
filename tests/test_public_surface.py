"""What the public repository says about itself matches what it contains."""

import re
from pathlib import Path

import pytest

from bell_system.progression import DIFFICULTIES
from bell_system.settings import OPTIONS

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_TEXT = (
    sorted((ROOT / 'src' / 'bell_system').rglob('*.py'))
    + sorted((ROOT / 'tools').glob('*.py'))
    + sorted((ROOT / 'tests').glob('*.py'))
    + [ROOT / 'README.md', ROOT / 'SOURCES.md',
       ROOT / 'docs' / 'site' / 'index.md']
)
THIS_FILE = Path(__file__).resolve()


def read(path):
    return path.read_text(encoding='utf-8')


def flat(path):
    return ' '.join(read(path).split())


# The period documents are kept by the maintainer and are not in the
# repository. Nothing public may say they are.
PERIOD_DOCUMENTS_ARE_NOT_HERE = [
    r'\bbundled\b',
    r'document here',
    r'document in (the|this) repository',
    r'repo-verified',
    r'\.txt files above',
]

# The design notes and the narrative bible are local-only.
LOCAL_ONLY_NAMES = [
    r'docs/design',
    r'narrative-bible',
    r'\bplan\.md',
    r'attached_assets',
]


def hits(patterns):
    found = []
    for path in PUBLIC_TEXT:
        if path.resolve() == THIS_FILE:
            continue
        text = read(path)
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                found.append(f"{path.relative_to(ROOT)}: {match.group(0)}")
    return found


class TestNothingClaimsTheDocumentsShip:
    def test_no_text_says_the_period_documents_are_in_the_repository(self):
        assert hits(PERIOD_DOCUMENTS_ARE_NOT_HERE) == []

    def test_a_practice_sheet_calls_its_source_a_period_document(self):
        from bell_system.data.practices import SOURCED
        assert 'repository' not in SOURCED
        assert 'period document' in SOURCED


class TestNothingNamesLocalOnlyFiles:
    def test_no_public_text_names_the_design_notes_by_path(self):
        assert hits(LOCAL_ONLY_NAMES) == []

    def test_the_nanpa_builder_takes_its_dump_as_an_argument(self):
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'build_nanpa.py')],
            capture_output=True, text=True, cwd=ROOT)
        assert result.returncode != 0
        assert '--source' in result.stderr


class TestTheReadmeMatchesTheSettings:
    def test_it_lists_every_setting_that_is_not_an_assist(self):
        readme = read(ROOT / 'README.md')
        missing = [option.key for option in OPTIONS
                   if not option.key.startswith('assist.')
                   and f"`{option.key}`" not in readme]
        assert missing == []

    def test_it_names_every_assist(self):
        readme = read(ROOT / 'README.md')
        missing = [option.key for option in OPTIONS
                   if option.key.startswith('assist.')
                   and f"`{option.key}`" not in readme]
        assert missing == []

    def test_the_repeat_chance_it_gives_is_the_one_the_code_uses(self):
        readme = flat(ROOT / 'README.md')
        fun = DIFFICULTIES['fun'].repeat_report_chance
        craft = DIFFICULTIES['craft'].repeat_report_chance
        assert fun == pytest.approx(0.25)
        assert 'one time in four in `fun`' in readme
        assert f"{round(craft * 100)} times in 100 in `craft`" in readme


class TestTheSitePageMatchesTheDifficultyProfiles:
    def test_fun_still_counts_a_missed_commitment(self):
        fun = DIFFICULTIES['fun']
        assert fun.missed_commitment_scale == pytest.approx(0.25)
        page = flat(ROOT / 'docs' / 'site' / 'index.md')
        assert 'commitments are not counted' not in page
        assert 'a quarter of what it costs in `craft`' in page

    def test_the_site_repeat_chances_are_the_codes(self):
        page = flat(ROOT / 'docs' / 'site' / 'index.md')
        craft = DIFFICULTIES['craft'].repeat_report_chance
        assert 'one in four in `fun`' in page
        assert f"{round(craft * 100)} in 100 in `craft`" in page

    def test_every_setting_it_says_the_readme_lists_is_listed(self):
        page = flat(ROOT / 'docs' / 'site' / 'index.md')
        assert 'The README lists every setting' in page
        readme = read(ROOT / 'README.md')
        assert all(f"`{o.key}`" in readme for o in OPTIONS
                   if not o.key.startswith('assist.'))
