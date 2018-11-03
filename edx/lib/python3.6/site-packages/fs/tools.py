"""Miscellaneous tools for operating on filesystems.
"""

from __future__ import print_function
from __future__ import unicode_literals

import io
import typing

from . import errors
from .errors import DirectoryNotEmpty
from .errors import ResourceNotFound
from .path import abspath
from .path import dirname
from .path import normpath
from .path import recursepath

if False:  # typing.TYPE_CHECKING
    from typing import IO, List, Optional, Text
    from .base import FS


def remove_empty(fs, path):
    # type: (FS, Text) -> None
    """Remove all empty parents.

    Arguments:
        fs (FS): A filesystem instance.
        path (str): Path to a directory on the filesystem.

    """
    path = abspath(normpath(path))
    try:
        while path not in ("", "/"):
            fs.removedir(path)
            path = dirname(path)
    except DirectoryNotEmpty:
        pass


def copy_file_data(src_file, dst_file, chunk_size=None):
    # type: (IO, IO, Optional[int]) -> None
    """Copy data from one file object to another.

    Arguments:
        src_file (io.IOBase): File open for reading.
        dst_file (io.IOBase): File open for writing.
        chunk_size (int): Number of bytes to copy at
            a time (or `None` to use sensible default).

    """
    _chunk_size = chunk_size or io.DEFAULT_BUFFER_SIZE
    read = src_file.read
    write = dst_file.write
    # The 'or None' is so that it works with binary and text files
    for chunk in iter(lambda: read(_chunk_size) or None, None):
        write(chunk)


def get_intermediate_dirs(fs, dir_path):
    # type: (FS, Text) -> List[Text]
    """Get a list of non-existing intermediate directories.

    Arguments:
        fs (FS): A filesystem instance.
        dir_path (str): A path to a new directory on the filesystem.

    Returns:
        list: A list of non-existing paths.

    Raises:
        `fs.errors.DirectoryExpected`: If a path component
            references a file and not a directory.

    """
    intermediates = []
    with fs.lock():
        for path in recursepath(abspath(dir_path), reverse=True):
            try:
                resource = fs.getinfo(path)
            except ResourceNotFound:
                intermediates.append(abspath(path))
            else:
                if resource.is_dir:
                    break
                raise errors.DirectoryExpected(dir_path)
    return intermediates[::-1][:-1]


def is_thread_safe(*filesystems):
    # type: (FS) -> bool
    """Check if all filesystems are thread-safe.

    Arguments:
        filesystems (FS): Filesystems instances to check.

    Returns:
        bool: if all filesystems are thread safe.

    """
    return all(fs.getmeta().get("thread_safe", False) for fs in filesystems)
