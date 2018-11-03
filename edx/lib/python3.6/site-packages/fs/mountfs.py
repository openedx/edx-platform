"""Manage other filesystems as a folder hierarchy.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing

from six import text_type

from . import errors
from .base import FS
from .memoryfs import MemoryFS
from .path import abspath
from .path import forcedir
from .path import normpath
from .mode import validate_open_mode
from .mode import validate_openbin_mode

if False:  # typing.TYPE_CHECKING
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Iterator,
        IO,
        List,
        MutableSequence,
        Optional,
        Text,
        Tuple,
        Union,
    )
    from .enums import ResourceType
    from .info import Info, RawInfo
    from .permissions import Permissions
    from .subfs import SubFS

    M = typing.TypeVar("M", bound="MountFS")


class MountError(Exception):
    """Thrown when mounts conflict.
    """


class MountFS(FS):
    """A virtual filesystem that maps directories on to other file-systems.

    Arguments:
        auto_close (bool): If `True` (the default), the child
            filesystems will be closed when `MountFS` is closed.

    """

    _meta = {
        "virtual": True,
        "read_only": False,
        "unicode_paths": True,
        "case_insensitive": False,
        "invalid_path_chars": "\0",
    }

    def __init__(self, auto_close=True):
        # type: (bool) -> None
        super(MountFS, self).__init__()
        self.auto_close = auto_close
        self.default_fs = MemoryFS()  # type: FS
        self.mounts = []  # type: MutableSequence[Tuple[Text, FS]]

    def __repr__(self):
        # type: () -> str
        return "MountFS(auto_close={!r})".format(self.auto_close)

    def __str__(self):
        # type: () -> str
        return "<mountfs>"

    def _delegate(self, path):
        # type: (Text) -> Tuple[FS, Text]
        """Get the delegate FS for a given path.

        Arguments:
            path (str): A path.

        Returns:
            (FS, str): a tuple of ``(<fs>, <path>)`` for a mounted filesystem,
            or ``(None, None)`` if no filesystem is mounted on the
            given ``path``.

        """
        _path = forcedir(abspath(normpath(path)))
        is_mounted = _path.startswith

        for mount_path, fs in self.mounts:
            if is_mounted(mount_path):
                return fs, _path[len(mount_path) :].rstrip("/")

        return self.default_fs, path

    def mount(self, path, fs):
        # type: (Text, Union[FS, Text]) -> None
        """Mounts a host FS object on a given path.

        Arguments:
            path (str): A path within the MountFS.
            fs (FS or str): A filesystem (instance or URL) to mount.

        """
        if isinstance(fs, text_type):
            from .opener import open_fs

            fs = open_fs(fs)

        if not isinstance(fs, FS):
            raise TypeError("fs argument must be an FS object or a FS URL")

        if fs is self:
            raise ValueError("Unable to mount self")
        _path = forcedir(abspath(normpath(path)))

        for mount_path, _ in self.mounts:
            if _path.startswith(mount_path):
                raise MountError("mount point overlaps existing mount")

        self.mounts.append((_path, fs))
        self.default_fs.makedirs(_path, recreate=True)

    def close(self):
        # type: () -> None
        # Explicitly closes children if requested
        if self.auto_close:
            for _path, fs in self.mounts:
                fs.close()
            del self.mounts[:]
        self.default_fs.close()
        super(MountFS, self).close()

    def desc(self, path):
        # type: (Text) -> Text
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        fs, delegate_path = self._delegate(path)
        if fs is self.default_fs:
            fs = self
        return "{path} on {fs}".format(fs=fs, path=delegate_path)

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        self.check()
        fs, _path = self._delegate(path)
        return fs.getinfo(_path, namespaces=namespaces)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        fs, _path = self._delegate(path)
        return fs.listdir(_path)

    def makedir(self, path, permissions=None, recreate=False):
        # type: (Text, Optional[Permissions], bool) -> SubFS[FS]
        self.check()
        fs, _path = self._delegate(path)
        return fs.makedir(_path, permissions=permissions, recreate=recreate)

    def openbin(self, path, mode="r", buffering=-1, **kwargs):
        # type: (Text, Text, int, **Any) -> BinaryIO
        validate_openbin_mode(mode)
        self.check()
        fs, _path = self._delegate(path)
        return fs.openbin(_path, mode=mode, buffering=-1, **kwargs)

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        fs, _path = self._delegate(path)
        return fs.remove(_path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        path = normpath(path)
        if path in ("", "/"):
            raise errors.RemoveRootError(path)
        fs, _path = self._delegate(path)
        return fs.removedir(_path)

    def getbytes(self, path):
        # type: (Text) -> bytes
        self.check()
        fs, _path = self._delegate(path)
        return fs.getbytes(_path)

    def getfile(self, path, file, chunk_size=None, **options):
        # type: (Text, BinaryIO, Optional[int], **Any) -> None
        fs, _path = self._delegate(path)
        return fs.getfile(_path, file, chunk_size=chunk_size, **options)

    def gettext(
        self,
        path,  # type: Text
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> Text
        self.check()
        fs, _path = self._delegate(path)
        return fs.gettext(_path, encoding=encoding, errors=errors, newline=newline)

    def getsize(self, path):
        # type: (Text) -> int
        self.check()
        fs, _path = self._delegate(path)
        return fs.getsize(_path)

    def getsyspath(self, path):
        # type: (Text) -> Text
        self.check()
        fs, _path = self._delegate(path)
        return fs.getsyspath(_path)

    def gettype(self, path):
        # type: (Text) -> ResourceType
        self.check()
        fs, _path = self._delegate(path)
        return fs.gettype(_path)

    def geturl(self, path, purpose="download"):
        # type: (Text, Text) -> Text
        self.check()
        fs, _path = self._delegate(path)
        return fs.geturl(_path, purpose=purpose)

    def hasurl(self, path, purpose="download"):
        # type: (Text, Text) -> bool
        self.check()
        fs, _path = self._delegate(path)
        return fs.hasurl(_path, purpose=purpose)

    def isdir(self, path):
        # type: (Text) -> bool
        self.check()
        fs, _path = self._delegate(path)
        return fs.isdir(_path)

    def isfile(self, path):
        # type: (Text) -> bool
        self.check()
        fs, _path = self._delegate(path)
        return fs.isfile(_path)

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        self.check()
        fs, _path = self._delegate(path)
        return fs.scandir(_path, namespaces=namespaces, page=page)

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        fs, _path = self._delegate(path)
        return fs.setinfo(_path, info)

    def validatepath(self, path):
        # type: (Text) -> Text
        self.check()
        fs, _path = self._delegate(path)
        fs.validatepath(_path)
        path = abspath(normpath(path))
        return path

    def open(
        self,
        path,  # type: Text
        mode="r",  # type: Text
        buffering=-1,  # type: int
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
        **options  # type: Any
    ):
        # type: (...) -> IO
        validate_open_mode(mode)
        self.check()
        fs, _path = self._delegate(path)
        return fs.open(
            _path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            **options
        )

    def setbinfile(self, path, file):
        # type: (Text, BinaryIO) -> None
        self.check()
        fs, _path = self._delegate(path)
        return fs.setbinfile(_path, file)

    def setbytes(self, path, contents):
        # type: (Text, bytes) -> None
        self.check()
        fs, _path = self._delegate(path)
        return fs.setbytes(_path, contents)

    def settext(
        self,
        path,  # type: Text
        contents,  # type: Text
        encoding="utf-8",  # type: Text
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        fs, _path = self._delegate(path)
        return fs.settext(
            _path, contents, encoding=encoding, errors=errors, newline=newline
        )
