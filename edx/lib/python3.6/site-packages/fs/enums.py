"""Enums used by PyFilesystem.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import os
from enum import IntEnum, unique


@unique
class ResourceType(IntEnum):
    """Resource Types.

    Positive values are reserved, negative values are implementation
    dependent.

    Most filesystems will support only directory(1) and file(2). Other
    types exist to identify more exotic resource types supported
    by Linux filesystems.

    """

    #: Unknown resource type, used if the filesystem is unable to
    #: tell what the resource is.
    unknown = 0
    #: A directory.
    directory = 1
    #: A simple file.
    file = 2
    #: A character file.
    character = 3
    #: A block special file.
    block_special_file = 4
    #: A first in first out file.
    fifo = 5
    #: A socket.
    socket = 6
    #: A symlink.
    symlink = 7


@unique
class Seek(IntEnum):
    """Constants used by `io.IOBase.seek`.

    These match `os.SEEK_CUR`, `os.SEEK_END`, and `os.SEEK_SET`
    from the standard library.

    """

    #: Seek from the current file position.
    current = os.SEEK_CUR
    #: Seek from the end of the file.
    end = os.SEEK_END
    #: Seek from the start of the file.
    set = os.SEEK_SET
