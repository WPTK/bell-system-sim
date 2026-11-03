"""
What one career leaves for the next.

A finished career used to be a dead end: the record sat there, and starting
again meant deleting a file by hand. ``career new`` closes a finished career
properly. Its three files are set aside in an archive directory and never
deleted, and a fourth, ``legacy.json``, carries two things forward:

* a handover note, generated from the career's totals and nothing else, and
* the files the player wrote under ``/usr/users/``.

The next career finds them under ``/usr/users/prior/``, as the files of an
earlier holder of the desk. They are undated and unsigned (the bible, W17).
They carry no fact about any report, so a second career has no key to a
board by reading the first one's files (pillar 1).

The rules the other save files follow apply here too: written by hand and
readable, written to a scratch name and moved into place, never raising on
a bad file, and capped. A legacy that does not read whole is left out and
the career starts without one, which is the worst that can happen.
"""

import json
import os
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from .filesystem import (
    Node, PLAYER_LIMIT, PLAYER_PREFIX, PRIOR, is_prior_path, normalise)
from .jsonfile import read_json, write_text_atomically

LEGACY_FILENAME = 'legacy.json'
LEGACY_VERSION = 1
ARCHIVE_DIRECTORY = 'archive'

# Where the earlier holder's files turn up (filesystem.PRIOR), and what is
# never saved from there: a legacy is handed down once, not stacked.
NOTE_NAME = 'HANDOVER'
NOTE_PATH = f'{PRIOR}/{NOTE_NAME}'

# The most that is carried, in bytes of file and in entries, the same sort
# of cap home.json has and for the same reason.
LEGACY_LIMIT = PLAYER_LIMIT
LEGACY_ENTRIES = 200

# The files a finished career owns. They are moved as a set or not at all.
CAREER_FILES = ('career.json', 'shift.json', 'home.json')


class Legacy(NamedTuple):
    """What a finished career hands on."""

    # The number of the career that wrote it: 1 for the first one finished.
    generation: int
    note: List[str]
    # Path under PRIOR to contents; a directory is None.
    files: Dict[str, Optional[str]]


def legacy_path(state_directory: str) -> str:
    """Return the legacy file path inside a state directory."""
    return os.path.join(state_directory, LEGACY_FILENAME)


def in_prior(path: str) -> bool:
    """Return whether a path is one of the earlier holder's."""
    return is_prior_path(path)


# -- what is written -------------------------------------------------------

def handover_note(career: Any, generation: int) -> List[str]:
    """
    The note an earlier holder leaves, from totals alone.

    It says how long the desk was held and how it ended, and nothing about
    any report, line or fault: the figures are the ones 'qual' prints.
    """
    verdict = (career.audit_verdict or 'not recorded').lower()
    return [
        "Left for whoever has this desk next.",
        "",
        f"Career             {generation}",
        f"Tours worked       {career.shift}",
        f"Reports closed     {career.reports_closed}",
        f"Audit              {verdict}",
        "",
        "What else I kept is in this directory. It is not much.",
    ]


def carried(changed: Dict[str, Node]) -> Dict[str, Optional[str]]:
    """
    Choose the player's files to hand on.

    Args:
        changed: What :func:`filesystem.player_changes` found

    Returns:
        Files under ``PRIOR`` keyed by path. Only what is under the users'
        home directories goes: the moo scoreboard stays with the career that
        earned it. Files are taken in path order until the cap is reached;
        one that would pass it is left behind and the rest still go.
    """
    found: Dict[str, Optional[str]] = {}
    for path, node in sorted(changed.items()):
        if not path.startswith(PLAYER_PREFIX) or in_prior(path):
            continue
        relative = path[len(PLAYER_PREFIX):].strip('/')
        if not relative:
            continue
        target = f'{PRIOR}/{relative}'
        # The note is the generated one; no file of the player's may shadow it.
        if target == NOTE_PATH:
            continue
        if node.is_dir:
            found[target] = None
        elif isinstance(node.content, str):
            found[target] = node.content
    return _within_cap(found)


def _size(files: Dict[str, Optional[str]]) -> int:
    """How big a legacy file is, as the text it is written as."""
    return len(_text(1, [], files).encode('utf-8'))


def _within_cap(files: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """Keep what fits, shallowest and first in path order."""
    kept: Dict[str, Optional[str]] = {}
    for path in sorted(files, key=lambda held: (held.count('/'), held)):
        if len(kept) >= LEGACY_ENTRIES:
            break
        trial = dict(kept)
        trial[path] = files[path]
        if _size(trial) <= LEGACY_LIMIT - 4096:
            kept = trial
    return kept


def _text(generation: int, note: List[str],
          files: Dict[str, Optional[str]]) -> str:
    """The text of a legacy file."""
    return json.dumps({
        'version': LEGACY_VERSION,
        'generation': generation,
        'note': note,
        'files': {path: {'kind': 'dir' if content is None else 'file',
                         'content': content}
                  for path, content in sorted(files.items())},
    }, indent=1, sort_keys=True) + '\n'


def write(path: str, handed: Legacy) -> None:
    """
    Write a legacy.

    Raises:
        OSError: If it cannot be written
    """
    text = _text(handed.generation, handed.note, handed.files)
    write_text_atomically(path, text)


# -- what is read ----------------------------------------------------------

def _clean_path(path: Any) -> Optional[str]:
    """A saved path, forced under PRIOR, or nothing if it will not go."""
    if not isinstance(path, str) or '\x00' in path:
        return None
    if (normalise(path, '/') != path or not in_prior(path) or path == PRIOR
            or path == NOTE_PATH):
        return None
    return path


def load(path: str) -> Optional[Legacy]:
    """
    Read a legacy from disk, or nothing if there is not one to apply.

    Entry by entry, the way home.json is read: a damaged entry is left out
    and the rest kept, and a path outside ``/usr/users/prior/`` is refused
    however it got into the file, so a hand-edited legacy.json is not a way
    to write anywhere else. A file over the cap, of another version, or not
    shaped like a legacy is ignored whole.
    """
    try:
        if not path or not os.path.exists(path) or \
                os.path.getsize(path) > LEGACY_LIMIT:
            return None
    except OSError:
        return None
    stored = read_json(path)
    if (not isinstance(stored, dict)
            or stored.get('version') != LEGACY_VERSION
            or not isinstance(stored.get('files'), dict)):
        return None
    generation = stored.get('generation')
    if not isinstance(generation, int) or isinstance(generation, bool) \
            or generation < 1:
        return None
    note = stored.get('note')
    lines = [line for line in note if isinstance(line, str)] \
        if isinstance(note, list) else []
    files: Dict[str, Optional[str]] = {}
    for held, entry in stored['files'].items():
        clean = _clean_path(held)
        if clean is None or not isinstance(entry, dict):
            continue
        if entry.get('kind') == 'dir':
            files[clean] = None
        elif entry.get('kind') == 'file' and isinstance(
                entry.get('content'), str):
            files[clean] = entry['content']
        if len(files) >= LEGACY_ENTRIES:
            break
    return Legacy(generation, lines[:40], files)


def seed(filesystem: Dict[str, Node], handed: Optional[Legacy]) -> None:
    """
    Put an earlier holder's files into a session's filesystem.

    Read-only to everybody, because they are somebody else's, and with every
    directory above them made, so a file is never out of reach. The files are
    not the player's, so :func:`filesystem.player_changes` leaves them out
    of home.json; they come back from legacy.json each session.
    """
    if handed is None:
        return
    filesystem[PRIOR] = Node('dir', 'root', 'other', 'dr-xr-xr-x')
    filesystem[NOTE_PATH] = Node(
        'file', 'root', 'other', '-r--r--r--',
        '\n'.join(handed.note) + '\n')
    for path in sorted(handed.files, key=lambda held: held.count('/')):
        content = handed.files[path]
        if not _make_parents(filesystem, path):
            continue
        if content is None:
            filesystem[path] = Node('dir', 'root', 'other', 'dr-xr-xr-x')
        else:
            filesystem[path] = Node('file', 'root', 'other', '-r--r--r--',
                                    content)


def _make_parents(filesystem: Dict[str, Node], path: str) -> bool:
    """
    Make the directories above a path, or say they cannot be.

    A parent that is a file stops the entry, as it does in
    :func:`save.restore_home`, so a file is never put under a file.
    """
    if not in_prior(path) or path == PRIOR:
        return False
    parent = path
    missing = []
    while True:
        parent = parent.rsplit('/', 1)[0]
        if parent == PRIOR:
            break
        held = filesystem.get(parent)
        if held is None:
            missing.append(parent)
        elif not held.is_dir:
            return False
    for folder in missing:
        filesystem[folder] = Node('dir', 'root', 'other', 'dr-xr-xr-x')
    return True


# -- closing a career ------------------------------------------------------

def next_archive(state_directory: str) -> Tuple[str, int]:
    """The first archive directory name not yet taken, and its number."""
    number = 1
    while os.path.exists(os.path.join(
            state_directory, ARCHIVE_DIRECTORY, f'career-{number}')):
        number += 1
    return (os.path.join(state_directory, ARCHIVE_DIRECTORY,
                         f'career-{number}'), number)


def generation_of(state_directory: str) -> int:
    """The number the career being finished is: one past the last legacy's."""
    previous = load(legacy_path(state_directory))
    return previous.generation + 1 if previous else 1


def set_aside(state_directory: str, where: str, moved: List[str]) -> None:
    """
    Move a finished career's files into an archive directory.

    Nothing is deleted. Each file is moved, not copied, and its name is added
    to ``moved`` as it goes, so that whatever stops this part way (the caller
    puts those back with :func:`put_back`) leaves nothing unaccounted for.
    The previous legacy file goes in too, since the new one replaces it.

    Args:
        state_directory: Where the career's files are
        where: The archive directory to make, from :func:`next_archive`
        moved: Filled with the names moved so far

    Raises:
        OSError: If a file could not be moved
    """
    os.makedirs(where)
    for name in (*CAREER_FILES, LEGACY_FILENAME):
        source = os.path.join(state_directory, name)
        if os.path.exists(source):
            os.replace(source, os.path.join(where, name))
            moved.append(name)


def put_back(state_directory: str, where: str, moved: List[str]) -> List[str]:
    """
    Undo :func:`set_aside`: move files back and remove the empty folder.

    Returns:
        The names that could not be moved back, which are still in ``where``
    """
    stuck = []
    for name in moved:
        try:
            os.replace(os.path.join(where, name),
                       os.path.join(state_directory, name))
        except OSError:
            stuck.append(name)
    # Only folders this made, and only while they are empty.
    for folder in (where, os.path.dirname(where)):
        try:
            os.rmdir(folder)
        except OSError:
            break
    return stuck
