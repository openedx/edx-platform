"""Tools for managing OS errors.
"""

from __future__ import print_function
from __future__ import unicode_literals

import collections
import errno
import platform
import sys
import typing
from contextlib import contextmanager

from six import reraise

from . import errors

if False:  # typing.TYPE_CHECKING
    from types import TracebackType
    from typing import Iterator, Optional, Mapping, Text, Type, Union


_WINDOWS_PLATFORM = platform.system() == "Windows"


class _ConvertOSErrors(object):
    """Context manager to convert OSErrors in to FS Errors.
    """

    FILE_ERRORS = {
        64: errors.RemoteConnectionError,  # ENONET
        errno.EACCES: errors.PermissionDenied,
        errno.ENOENT: errors.ResourceNotFound,
        errno.EFAULT: errors.ResourceNotFound,
        errno.ESRCH: errors.ResourceNotFound,
        errno.ENOTEMPTY: errors.DirectoryNotEmpty,
        errno.EEXIST: errors.FileExists,
        183: errors.DirectoryExists,
        # errno.ENOTDIR: errors.DirectoryExpected,
        errno.ENOTDIR: errors.ResourceNotFound,
        errno.EISDIR: errors.FileExpected,
        errno.EINVAL: errors.FileExpected,
        errno.ENOSPC: errors.InsufficientStorage,
        errno.EPERM: errors.PermissionDenied,
        errno.ENETDOWN: errors.RemoteConnectionError,
        errno.ECONNRESET: errors.RemoteConnectionError,
        errno.ENAMETOOLONG: errors.PathError,
        errno.EOPNOTSUPP: errors.Unsupported,
        errno.ENOSYS: errors.Unsupported,
    }

    DIR_ERRORS = FILE_ERRORS.copy()
    DIR_ERRORS[errno.ENOTDIR] = errors.DirectoryExpected
    DIR_ERRORS[errno.EEXIST] = errors.DirectoryExists
    DIR_ERRORS[errno.EINVAL] = errors.DirectoryExpected

    if _WINDOWS_PLATFORM:  # pragma: no cover
        DIR_ERRORS[13] = errors.DirectoryExpected
        DIR_ERRORS[267] = errors.DirectoryExpected
        FILE_ERRORS[13] = errors.FileExpected

    def __init__(self, opname, path, directory=False):
        # type: (Text, Text, bool) -> None
        self._opname = opname
        self._path = path
        self._directory = directory

    def __enter__(self):
        # type: () -> _ConvertOSErrors
        return self

    def __exit__(
        self,
        exc_type,  # type: Optional[Type[BaseException]]
        exc_value,  # type: Optional[BaseException]
        traceback,  # type: Optional[TracebackType]
    ):
        # type: (...) -> None
        os_errors = self.DIR_ERRORS if self._directory else self.FILE_ERRORS
        if exc_type and isinstance(exc_value, EnvironmentError):
            _errno = exc_value.errno
            fserror = os_errors.get(_errno, errors.OperationFailed)
            if _errno == errno.EACCES and sys.platform == "win32":
                if getattr(exc_value, "args", None) == 32:  # pragma: no cover
                    fserror = errors.ResourceLocked
            reraise(fserror, fserror(self._path, exc=exc_value), traceback)


# Stops linter complaining about invalid class name
convert_os_errors = _ConvertOSErrors


@contextmanager
def unwrap_errors(path_replace):
    # type: (Union[Text, Mapping[Text, Text]]) -> Iterator[None]
    """Get a context to map OS errors to their `fs.errors` counterpart.

    The context will re-write the paths in resource exceptions to be
    in the same context as the wrapped filesystem.

    The only parameter may be the path from the parent, if only one path
    is to be unwrapped. Or it may be a dictionary that maps wrapped
    paths on to unwrapped paths.

    """
    try:
        yield
    except errors.ResourceError as e:
        if hasattr(e, "path"):
            if isinstance(path_replace, collections.Mapping):
                e.path = path_replace.get(e.path, e.path)
            else:
                e.path = path_replace
        reraise(type(e), e)
