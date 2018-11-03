"""Functions for copying resources *between* filesystem.
"""

from __future__ import print_function, unicode_literals

import typing

from .errors import FSError
from .opener import manage_fs
from .path import abspath, combine, frombase, normpath
from .tools import is_thread_safe
from .walk import Walker

if False:  # typing.TYPE_CHECKING
    from typing import Callable, Optional, Text, Union
    from .base import FS
    from .walk import Walker

    _OnCopy = Callable[[FS, Text, FS, Text], object]


def copy_fs(
    src_fs,  # type: Union[FS, Text]
    dst_fs,  # type: Union[FS, Text]
    walker=None,  # type: Optional[Walker]
    on_copy=None,  # type: Optional[_OnCopy]
    workers=0,  # type: int
):
    # type: (...) -> None
    """Copy the contents of one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (URL or instance).
        dst_fs (FS or str): Destination filesystem (URL or instance).
        walker (~fs.walk.Walker, optional): A walker object that will be
            used to scan for files in ``src_fs``. Set this if you only want
            to consider a sub-set of the resources in ``src_fs``.
        on_copy (callable):A function callback called after a single file copy
            is executed. Expected signature is ``(src_fs, src_path, dst_fs,
            dst_path)``.
        workers (int): Use `worker` threads to copy data, or ``0`` (default) for
            a single-threaded copy.

    """
    return copy_dir(
        src_fs, "/", dst_fs, "/", walker=walker, on_copy=on_copy, workers=workers
    )


def copy_fs_if_newer(
    src_fs,  # type: Union[FS, Text]
    dst_fs,  # type: Union[FS, Text]
    walker=None,  # type: Optional[Walker]
    on_copy=None,  # type: Optional[_OnCopy]
    workers=0,  # type: int
):
    # type: (...) -> None
    """Copy the contents of one filesystem to another, checking times.

    If both source and destination files exist, the copy is executed
    only if the source file is newer than the destination file. In case
    modification times of source or destination files are not available,
    copy file is always executed.

    Arguments:
        src_fs (FS or str): Source filesystem (URL or instance).
        dst_fs (FS or str): Destination filesystem (URL or instance).
        walker (~fs.walk.Walker, optional): A walker object that will be
            used to scan for files in ``src_fs``. Set this if you only want
            to consider a sub-set of the resources in ``src_fs``.
        on_copy (callable):A function callback called after a single file copy
            is executed. Expected signature is ``(src_fs, src_path, dst_fs,
            dst_path)``.
        workers (int): Use ``worker`` threads to copy data, or ``0`` (default) for
            a single-threaded copy.

    """
    return copy_dir_if_newer(
        src_fs, "/", dst_fs, "/", walker=walker, on_copy=on_copy, workers=workers
    )


def _source_is_newer(src_fs, src_path, dst_fs, dst_path):
    # type: (FS, Text, FS, Text) -> bool
    """Determine if source file is newer than destination file.

    Arguments:
        src_fs (FS): Source filesystem (instance or URL).
        src_path (str): Path to a file on the source filesystem.
        dst_fs (FS): Destination filesystem (instance or URL).
        dst_path (str): Path to a file on the destination filesystem.

    Returns:
        bool: `True` if the source file is newer than the destination
        file or file modification time cannot be determined, `False`
        otherwise.

    """
    try:
        if dst_fs.exists(dst_path):
            namespace = ("details", "modified")
            src_modified = src_fs.getinfo(src_path, namespace).modified
            if src_modified is not None:
                dst_modified = dst_fs.getinfo(dst_path, namespace).modified
                return dst_modified is None or src_modified > dst_modified
        return True
    except FSError:  # pragma: no cover
        # todo: should log something here
        return True


def copy_file(
    src_fs,  # type: Union[FS, Text]
    src_path,  # type: Text
    dst_fs,  # type: Union[FS, Text]
    dst_path,  # type: Text
):
    # type: (...) -> None
    """Copy a file from one filesystem to another.

    If the destination exists, and is a file, it will be first truncated.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a file on the source filesystem.
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a file on the destination filesystem.

    """
    with manage_fs(src_fs, writeable=False) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            if _src_fs is _dst_fs:
                # Same filesystem, so we can do a potentially optimized
                # copy
                _src_fs.copy(src_path, dst_path, overwrite=True)
            else:
                # Standard copy
                with _src_fs.lock(), _dst_fs.lock():
                    if _dst_fs.hassyspath(dst_path):
                        with _dst_fs.openbin(dst_path, "w") as write_file:
                            _src_fs.getfile(src_path, write_file)
                    else:
                        with _src_fs.openbin(src_path) as read_file:
                            _dst_fs.setbinfile(dst_path, read_file)


def copy_file_internal(
    src_fs,  # type: FS
    src_path,  # type: Text
    dst_fs,  # type: FS
    dst_path,  # type: Text
):
    # type: (...) -> None
    """Low level copy, that doesn't call manage_fs or lock.

    If the destination exists, and is a file, it will be first truncated.

    This method exists to optimize copying in loops. In general you
    should prefer `copy_file`.

    Arguments:
        src_fs (FS): Source filesystem.
        src_path (str): Path to a file on the source filesystem.
        dst_fs (FS: Destination filesystem.
        dst_path (str): Path to a file on the destination filesystem.

    """
    if src_fs is dst_fs:
        # Same filesystem, so we can do a potentially optimized
        # copy
        src_fs.copy(src_path, dst_path, overwrite=True)
    elif dst_fs.hassyspath(dst_path):
        with dst_fs.openbin(dst_path, "w") as write_file:
            src_fs.getfile(src_path, write_file)
    else:
        with src_fs.openbin(src_path) as read_file:
            dst_fs.setbinfile(dst_path, read_file)


def copy_file_if_newer(
    src_fs,  # type: Union[FS, Text]
    src_path,  # type: Text
    dst_fs,  # type: Union[FS, Text]
    dst_path,  # type: Text
):
    # type: (...) -> bool
    """Copy a file from one filesystem to another, checking times.

    If the destination exists, and is a file, it will be first truncated.
    If both source and destination files exist, the copy is executed only
    if the source file is newer than the destination file. In case
    modification times of source or destination files are not available,
    copy is always executed.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a file on the source filesystem.
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a file on the destination filesystem.

    Returns:
        bool: `True` if the file copy was executed, `False` otherwise.

    """
    with manage_fs(src_fs, writeable=False) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            if _src_fs is _dst_fs:
                # Same filesystem, so we can do a potentially optimized
                # copy
                if _source_is_newer(_src_fs, src_path, _dst_fs, dst_path):
                    _src_fs.copy(src_path, dst_path, overwrite=True)
                    return True
                else:
                    return False
            else:
                # Standard copy
                with _src_fs.lock(), _dst_fs.lock():
                    if _source_is_newer(_src_fs, src_path, _dst_fs, dst_path):
                        copy_file_internal(_src_fs, src_path, _dst_fs, dst_path)
                        return True
                    else:
                        return False


def copy_structure(
    src_fs,  # type: Union[FS, Text]
    dst_fs,  # type: Union[FS, Text]
    walker=None,  # type: Optional[Walker]
):
    # type: (...) -> None
    """Copy directories (but not files) from ``src_fs`` to ``dst_fs``.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        dst_fs (FS or str): Destination filesystem (instance or URL).
        walker (~fs.walk.Walker, optional): A walker object that will be
            used to scan for files in ``src_fs``. Set this if you only
            want to consider a sub-set of the resources in ``src_fs``.

    """
    walker = walker or Walker()
    with manage_fs(src_fs) as _src_fs:
        with manage_fs(dst_fs, create=True) as _dst_fs:
            with _src_fs.lock(), _dst_fs.lock():
                for dir_path in walker.dirs(_src_fs):
                    _dst_fs.makedir(dir_path, recreate=True)


def copy_dir(
    src_fs,  # type: Union[FS, Text]
    src_path,  # type: Text
    dst_fs,  # type: Union[FS, Text]
    dst_path,  # type: Text
    walker=None,  # type: Optional[Walker]
    on_copy=None,  # type: Optional[_OnCopy]
    workers=0,  # type: int
):
    # type: (...) -> None
    """Copy a directory from one filesystem to another.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a directory on the source filesystem.
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a directory on the destination filesystem.
        walker (~fs.walk.Walker, optional): A walker object that will be
            used to scan for files in ``src_fs``. Set this if you only
            want to consider a sub-set of the resources in ``src_fs``.
        on_copy (callable, optional):  A function callback called after
            a single file copy is executed. Expected signature is
            ``(src_fs, src_path, dst_fs, dst_path)``.
        workers (int): Use ``worker`` threads to copy data, or ``0`` (default) for
            a single-threaded copy.

    """
    on_copy = on_copy or (lambda *args: None)
    walker = walker or Walker()
    _src_path = abspath(normpath(src_path))
    _dst_path = abspath(normpath(dst_path))

    def src():
        return manage_fs(src_fs, writeable=False)

    def dst():
        return manage_fs(dst_fs, create=True)

    from ._bulk import Copier

    with src() as _src_fs, dst() as _dst_fs:
        with _src_fs.lock(), _dst_fs.lock():
            _thread_safe = is_thread_safe(_src_fs, _dst_fs)
            with Copier(num_workers=workers if _thread_safe else 0) as copier:
                _dst_fs.makedir(_dst_path, recreate=True)
                for dir_path, dirs, files in walker.walk(_src_fs, _src_path):
                    copy_path = combine(_dst_path, frombase(_src_path, dir_path))
                    for info in dirs:
                        _dst_fs.makedir(info.make_path(copy_path), recreate=True)
                    for info in files:
                        src_path = info.make_path(dir_path)
                        dst_path = info.make_path(copy_path)
                        copier.copy(_src_fs, src_path, _dst_fs, dst_path)
                        on_copy(_src_fs, src_path, _dst_fs, dst_path)


def copy_dir_if_newer(
    src_fs,  # type: Union[FS, Text]
    src_path,  # type: Text
    dst_fs,  # type: Union[FS, Text]
    dst_path,  # type: Text
    walker=None,  # type: Optional[Walker]
    on_copy=None,  # type: Optional[_OnCopy]
    workers=0,  # type: int
):
    # type: (...) -> None
    """Copy a directory from one filesystem to another, checking times.

    If both source and destination files exist, the copy is executed only
    if the source file is newer than the destination file. In case
    modification times of source or destination files are not available,
    copy is always executed.

    Arguments:
        src_fs (FS or str): Source filesystem (instance or URL).
        src_path (str): Path to a directory on the source filesystem.
        dst_fs (FS or str): Destination filesystem (instance or URL).
        dst_path (str): Path to a directory on the destination filesystem.
        walker (~fs.walk.Walker, optional): A walker object that will be
            used to scan for files in ``src_fs``. Set this if you only
            want to consider a sub-set of the resources in ``src_fs``.
        on_copy (callable, optional):  A function callback called after
            a single file copy is executed. Expected signature is
            ``(src_fs, src_path, dst_fs, dst_path)``.
        workers (int): Use ``worker`` threads to copy data, or ``0`` (default) for
            a single-threaded copy.

    """
    on_copy = on_copy or (lambda *args: None)
    walker = walker or Walker()
    _src_path = abspath(normpath(src_path))
    _dst_path = abspath(normpath(dst_path))

    def src():
        return manage_fs(src_fs, writeable=False)

    def dst():
        return manage_fs(dst_fs, create=True)

    from ._bulk import Copier

    with src() as _src_fs, dst() as _dst_fs:
        with _src_fs.lock(), _dst_fs.lock():
            _thread_safe = is_thread_safe(_src_fs, _dst_fs)
            with Copier(num_workers=workers if _thread_safe else 0) as copier:
                _dst_fs.makedir(_dst_path, recreate=True)
                namespace = ("details", "modified")
                dst_state = {
                    path: info
                    for path, info in walker.info(_dst_fs, _dst_path, namespace)
                    if info.is_file
                }
                src_state = [
                    (path, info)
                    for path, info in walker.info(_src_fs, _src_path, namespace)
                ]
                for dir_path, copy_info in src_state:
                    copy_path = combine(_dst_path, frombase(_src_path, dir_path))
                    if copy_info.is_dir:
                        _dst_fs.makedir(copy_path, recreate=True)
                    elif copy_info.is_file:
                        # dst file is present, try to figure out if copy
                        # is necessary
                        try:
                            src_modified = copy_info.modified
                            dst_modified = dst_state[dir_path].modified
                        except KeyError:
                            do_copy = True
                        else:
                            do_copy = (
                                src_modified is None
                                or dst_modified is None
                                or src_modified > dst_modified
                            )

                        if do_copy:
                            copier.copy(_src_fs, dir_path, _dst_fs, copy_path)
                            on_copy(_src_fs, dir_path, _dst_fs, copy_path)
