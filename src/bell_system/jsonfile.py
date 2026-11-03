"""
Reading and writing the small JSON files the simulation keeps.

Every file here is a person's progress, and every one can be damaged: hand
edited, cut short by a crash, or written by a later version. Reading one
therefore never raises, and writing one never leaves half a file behind.
"""

import json
import os
import tempfile
from typing import Any, Optional


def read_json(path: Optional[str]) -> Optional[Any]:
    """
    Read a JSON file, or nothing at all if it will not read.

    A file that is not text, not JSON, or nested so deeply that the parser
    gives up (RecursionError) is a bad file like any other, not a crash.
    """
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError, RecursionError):
        return None


def write_text_atomically(path: str, text: str) -> None:
    """
    Replace a file with this text, all of it or none of it.

    Written beside the file and moved over it, so a crash part way through
    leaves the old file, not a short one.

    Raises:
        OSError: If the directory or file cannot be written
    """
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    descriptor, scratch = tempfile.mkstemp(
        dir=directory, prefix='.' + os.path.basename(path), suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            handle.write(text)
        os.replace(scratch, path)
    except BaseException:
        try:
            os.remove(scratch)
        except OSError:
            pass
        raise
