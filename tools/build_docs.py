#!/usr/bin/env python3
"""
Build the Markdown for the documentation site from the in-game manual pages.

The manual lives in src/bell_system/data/man_pages.py, because `man` reads it
at run time. This script turns the same dictionary into one Markdown page per
command, so the hosted manual cannot disagree with the game. The pages go to
docs-build/ (untracked), together with a copy of the hand-written home page
from docs/site/. MkDocs then builds docs-build/ into the site.

A page belongs to exactly one section, worked out from the code that already
groups commands for `help`:

    Trouble desk       the commands every position has (BUREAU_COMMANDS)
    People             who, write, mail, orderwire and handoff (PEOPLE_COMMANDS)
    Position commands  what only some positions have (POSITION_COMMANDS)
    System             every other page, which is the Unix utilities, the
                       system commands and the telephony reference pages

Run from the repository root:

    python tools/build_docs.py [output-directory]
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from bell_system.data.man_pages import DESK_SECTIONS, MAN_PAGES  # noqa: E402
from bell_system.data.positions import (  # noqa: E402
    POSITION_COMMANDS, POSITIONS)
from bell_system.screens.guidance import GuidanceCommands  # noqa: E402

DEFAULT_OUT = ROOT / 'docs-build'
# Written into every output directory so a later run knows the directory is
# generated output and not somebody's files.
MARKER = '.build_docs'
HOME_PAGE = ROOT / 'docs' / 'site' / 'index.md'

# slug, title, one line for the index page. The index page shows them in this
# order. The site's sidebar sorts the slugs, because MkDocs titles a section
# from its directory name.
SECTIONS = (
    ('trouble-desk', 'Trouble desk',
     'Every position works these.'),
    ('people', 'People',
     'Who is on the system, writing to them, and handing the tour over.'),
    ('position-commands', 'Position commands',
     'Commands only some positions have. Each page names the positions.'),
    ('system', 'System',
     'Unix utilities, system commands and telephony reference pages.'),
)

_NAME_LINE = re.compile(r'^NAME\s*\n\s+(\S+)\s+-\s+(.+)$', re.MULTILINE)


def section_of(name: str) -> str:
    """Return the slug of the section the page for `name` belongs to."""
    if name in {n for n, _ in GuidanceCommands.BUREAU_COMMANDS}:
        return 'trouble-desk'
    if name in {n for n, _ in GuidanceCommands.PEOPLE_COMMANDS}:
        return 'people'
    if any(name in commands for commands in POSITION_COMMANDS.values()):
        return 'position-commands'
    return 'system'


def positions_with(name: str) -> List[str]:
    """Return the position keys that have `name`, in login-menu order."""
    return [key for key in POSITIONS
            if name in POSITION_COMMANDS.get(key, ())]


def summary_of(text: str) -> str:
    """Return the one line after the dash in the page's NAME section."""
    match = _NAME_LINE.search(text)
    return match.group(2).strip() if match else ''


def fence(text: str) -> str:
    """Wrap `text` so Markdown shows it as written, whatever it contains."""
    longest = max((len(run) for run in re.findall(r'`+', text)), default=0)
    ticks = '`' * max(3, longest + 1)
    return f"{ticks}text\n{text.rstrip()}\n{ticks}\n"


def render_page(name: str) -> str:
    """Return the Markdown for one command's page."""
    parts = [f"# {name}\n"]
    keys = positions_with(name)
    if keys:
        who = ', '.join(f"`{k}` ({POSITIONS[k].name})" for k in keys)
        parts.append(f"Positions with this command: {who}.\n")
    parts.append(fence(MAN_PAGES[name]))
    for key, extra in DESK_SECTIONS.get(name, {}).items():
        parts.append(f"## At the {POSITIONS[key].name} desk\n")
        parts.append(f"The game adds this only for `{key}`.\n")
        parts.append(fence(extra))
    return '\n'.join(parts)


def render_index(groups: Dict[str, List[str]]) -> str:
    """Return the Markdown for the command index page."""
    parts = [
        "# Command reference\n",
        f"{len(MAN_PAGES)} manual pages, the same text `man <command>` "
        "prints in the game. Use the search box to find a command or a "
        "word in a page.\n",
    ]
    for slug, title, blurb in SECTIONS:
        names = groups[slug]
        parts.append(f"## {title}\n")
        parts.append(f"{blurb}\n")
        for name in names:
            line = summary_of(MAN_PAGES[name])
            tail = f" - {line}" if line else ''
            parts.append(f"- [`{name}`]({slug}/{name}.md){tail}")
        parts.append('')
    return '\n'.join(parts)


def write(path: Path, text: str) -> None:
    """Write `text` with Unix line endings. Path.write_text has no newline
    argument before Python 3.10."""
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def refuse_unsafe(out: Path) -> None:
    """
    Raise ValueError if replacing `out` could destroy tracked files.

    build() deletes the directory it is given, so it refuses the repository
    root, any directory that contains it, any directory holding a tracked
    file (docs/, src/, tools/) and any other directory that has files in it
    but not the marker an earlier run wrote.
    """
    out = out.resolve()
    if out == ROOT or out in ROOT.parents:
        raise ValueError(f"{out} is or contains the repository root")
    if out.exists() and any(out.iterdir()) and not (out / MARKER).exists():
        raise ValueError(f"{out} has files that {MARKER} did not write; "
                         "name an empty or new directory")
    if ROOT not in out.parents:
        return
    try:
        tracked = subprocess.run(
            ['git', 'ls-files', '--', str(out)], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        tracked = [] if out == DEFAULT_OUT.resolve() else ['(git unavailable)']
    if tracked:
        raise ValueError(f"{out} holds tracked files, such as {tracked[0]}")


def build(out: Path = DEFAULT_OUT) -> Tuple[int, int]:
    """
    Write the site's Markdown to `out`, replacing what is there.

    Returns the number of man pages written and the number of files.
    """
    refuse_unsafe(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text('generated by tools/build_docs.py\n',
                              encoding='utf-8')
    commands = out / 'command-reference'
    groups: Dict[str, List[str]] = {slug: [] for slug, _, _ in SECTIONS}
    for name in sorted(MAN_PAGES):
        if not re.fullmatch(r'[a-z0-9]+', name):
            raise ValueError(f"man page name {name!r} is not a safe filename")
        groups[section_of(name)].append(name)
        page = commands / section_of(name) / f"{name}.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        write(page, render_page(name))
    write(commands / 'index.md', render_index(groups))
    shutil.copyfile(HOME_PAGE, out / 'index.md')
    count = sum(len(names) for names in groups.values())
    files = sum(1 for p in out.rglob('*')
                if p.is_file() and p.name != MARKER)
    return count, files


def main(argv: List[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUT
    try:
        count, files = build(out)
    except ValueError as err:
        print(f"build_docs: refusing to write: {err}", file=sys.stderr)
        return 2
    print(f"{count} man pages, {files} files written to {out}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
