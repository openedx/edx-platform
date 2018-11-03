"""Function for *mirroring* a filesystem.

Mirroring will create a copy of a source filesystem on a destination
filesystem. If there are no files on the destination, then mirroring
is simply a straight copy. If there are any files or directories on the
destination they may be deleted or modified to match the source.

In order to avoid redundant copying of files, `mirror` can compare
timestamps, and only copy files with a newer modified date. This
timestamp comparison is only done if the file sizes are different.

This scheme will work if you have mirrored a directory previously, and
you would like to copy any changes. Otherwise you should set the
``copy_if_newer`` parameter to `False` to guarantee an exact copy, at
the expense of potentially copying extra files.

"""

from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager
import typing

from ._bulk import Copier
from .copy import copy_file_internal
from .errors import ResourceNotFound
from .opener import manage_fs
from .tools import is_thread_safe
from .walk import Walker

if False:  # typing.TYPE_CHECKING
    from typing import Callable, Optional, Text, Union
    from .base import FS
    from .info import Info


def _compare(info1, info2):
    # type: (Info, Info) -> bool
    """Compare two `Info` objects to see if they should be copied.

    Returns:
        bool: `True` if the `Info` are different in size or mtime.

    """
    # Check filesize has changed
    if info1.size != info2.size:
        return True
    # Check modified dates
    date1 = info1.modified
    date2 = info2.modified
    return date1 is None or date2 is None or date1 > date2


def mirror(
    src_fs,  # type: Union[FS, Text]
    dst_fs,  # type: Union[FS, Text]
    walker=None,  # type: Optional[Walker]
    copy_if_newer=True,  # type: bool
    workers=0,  # type: int
):
    # type: (...) -> None
    """Mirror files / directories from one filesystem to another.

    Mirroring a filesystem will create an exact copy of ``src_fs`` on
    ``dst_fs``, by removing any files / directories on the destination
    that aren't on the source, and copying files that aren't.

    Arguments:
        src_fs (FS or str): Source filesystem (URL or instance).
        dst_fs (FS or str): Destination filesystem (URL or instance).
        walker (~fs.walk.Walker, optional): An optional walker instance.
        copy_if_newer (bool): Only copy newer files (the default).
        workers (int): Number of worker threads used
            (0 for single threaded). Set to a relatively low number
            for network filesystems, 4 would be a good start.
    """

    def src():
        return manage_fs(src_fs, writeable=False)

    def dst():
        return manage_fs(dst_fs, create=True)

    with src() as _src_fs, dst() as _dst_fs:
        with _src_fs.lock(), _dst_fs.lock():
            _thread_safe = is_thread_safe(_src_fs, _dst_fs)
            with Copier(num_workers=workers if _thread_safe else 0) as copier:
                _mirror(
                    _src_fs,
                    _dst_fs,
                    walker=walker,
                    copy_if_newer=copy_if_newer,
                    copy_file=copier.copy,
                )


def _mirror(
    src_fs, dst_fs, walker=None, copy_if_newer=True, copy_file=copy_file_internal
):
    # type: (FS, FS, Optional[Walker], bool, Callable[[FS, str, FS, str], None]) -> None
    walker = walker or Walker()
    walk = walker.walk(src_fs, namespaces=["details"])
    for path, dirs, files in walk:
        try:
            dst = {
                info.name: info for info in dst_fs.scandir(path, namespaces=["details"])
            }
        except ResourceNotFound:
            dst_fs.makedir(path)
            dst = {}

        # Copy files
        for _file in files:
            _path = _file.make_path(path)
            dst_file = dst.pop(_file.name, None)
            if dst_file is not None:
                if dst_file.is_dir:
                    # Destination is a directory, remove it
                    dst_fs.removetree(_path)
                else:
                    # Compare file info
                    if copy_if_newer and not _compare(_file, dst_file):
                        continue
            copy_file(src_fs, _path, dst_fs, _path)

        # Make directories
        for _dir in dirs:
            _path = _dir.make_path(path)
            dst_dir = dst.pop(_dir.name, None)
            if dst_dir is not None:
                # Directory name exists on dst
                if not dst_dir.is_dir:
                    # Not a directory, so remove it
                    dst_fs.remove(_path)
            else:
                # Make the directory in dst
                dst_fs.makedir(_path, recreate=True)

        # Remove any remaining resources
        while dst:
            _, info = dst.popitem()
            _path = info.make_path(path)
            if info.is_dir:
                dst_fs.removetree(_path)
            else:
                dst_fs.remove(_path)
