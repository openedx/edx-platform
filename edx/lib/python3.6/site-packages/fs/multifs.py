"""Manage several filesystems through a single view.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import typing
from collections import namedtuple, OrderedDict
from operator import itemgetter

from six import text_type

from . import errors
from .base import FS
from .mode import check_writable
from .opener import open_fs
from .path import abspath, normpath

if False:  # typing.TYPE_CHECKING
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Iterator,
        IO,
        MutableMapping,
        List,
        MutableSet,
        Optional,
        Text,
        Tuple,
    )
    from .enums import ResourceType
    from .info import Info, RawInfo
    from .permissions import Permissions
    from .subfs import SubFS

    M = typing.TypeVar("M", bound="MultiFS")


_PrioritizedFS = namedtuple("_PrioritizedFS", ["priority", "fs"])


class MultiFS(FS):
    """A filesystem that delegates to a sequence of other filesystems.

    Operations on the MultiFS will try each 'child' filesystem in order,
    until it succeeds. In effect, creating a filesystem that combines
    the files and dirs of its children.

    """

    _meta = {"virtual": True, "read_only": False, "case_insensitive": False}

    def __init__(self, auto_close=True):
        # type: (bool) -> None
        super(MultiFS, self).__init__()

        self._auto_close = auto_close
        self.write_fs = None  # type: Optional[FS]
        self._write_fs_name = None  # type: Optional[Text]
        self._sort_index = 0
        self._filesystems = {}  # type: MutableMapping[Text, _PrioritizedFS]
        self._fs_sequence = None  # type: Optional[List[Tuple[Text, FS]]]
        self._closed = False

    def __repr__(self):
        # type: () -> Text
        if self._auto_close:
            return "MultiFS()"
        else:
            return "MultiFS(auto_close=False)"

    def __str__(self):
        # type: () -> Text
        return "<multifs>"

    def add_fs(self, name, fs, write=False, priority=0):
        # type: (Text, FS, bool, int) -> None
        """Add a filesystem to the MultiFS.

        Arguments:
            name (str): A unique name to refer to the filesystem being
                added.
            fs (FS or str): The filesystem (instance or URL) to add.
            write (bool): If this value is True, then the ``fs`` will
                be used as the writeable FS (defaults to False).
            priority (int): An integer that denotes the priority of the
                filesystem being added. Filesystems will be searched in
                descending priority order and then by the reverse order
                they were added. So by default, the most recently added
                filesystem will be looked at first.

        """
        if isinstance(fs, text_type):
            fs = open_fs(fs)

        if not isinstance(fs, FS):
            raise TypeError("fs argument should be an FS object or FS URL")

        self._filesystems[name] = _PrioritizedFS(
            priority=(priority, self._sort_index), fs=fs
        )
        self._sort_index += 1
        self._resort()

        if write:
            self.write_fs = fs
            self._write_fs_name = name

    def get_fs(self, name):
        # type: (Text) -> FS
        """Get a filesystem from its name.

        Arguments:
            name (str): The name of a filesystem previously added.

        Returns:
            FS: the filesystem added as ``name`` previously.

        Raises:
            KeyError: If no filesystem with given ``name`` could be found.

        """
        return self._filesystems[name].fs

    def _resort(self):
        # type: () -> None
        """Force `iterate_fs` to re-sort on next reference.
        """
        self._fs_sequence = None

    def iterate_fs(self):
        # type: () -> Iterator[Tuple[Text, FS]]
        """Get iterator that returns (name, fs) in priority order.
        """
        if self._fs_sequence is None:
            self._fs_sequence = [
                (name, fs)
                for name, (_order, fs) in sorted(
                    self._filesystems.items(), key=itemgetter(1), reverse=True
                )
            ]
        return iter(self._fs_sequence)

    def _delegate(self, path):
        # type: (Text) -> Optional[FS]
        """Get a filesystem which has a given path.
        """
        for _name, fs in self.iterate_fs():
            if fs.exists(path):
                return fs
        return None

    def _delegate_required(self, path):
        # type: (Text) -> FS
        """Check that there is a filesystem with the given ``path``.
        """
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        return fs

    def _writable_required(self, path):
        # type: (Text) -> FS
        """Check that ``path`` is writeable.
        """
        if self.write_fs is None:
            raise errors.ResourceReadOnly(path)
        return self.write_fs

    def which(self, path, mode="r"):
        # type: (Text, Text) -> Tuple[Optional[Text], Optional[FS]]
        """Get a tuple of (name, fs) that the given path would map to.

        Arguments:
            path (str): A path on the filesystem.
            mode (str): An `io.open` mode.

        """
        if check_writable(mode):
            return self._write_fs_name, self.write_fs
        for name, fs in self.iterate_fs():
            if fs.exists(path):
                return name, fs
        return None, None

    def close(self):
        # type: () -> None
        self._closed = True
        if self._auto_close:
            try:
                for _order, fs in self._filesystems.values():
                    fs.close()
            finally:
                self._filesystems.clear()
                self._resort()

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        self.check()
        namespaces = namespaces or ()
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        _path = abspath(normpath(path))
        info = fs.getinfo(_path, namespaces=namespaces)
        return info

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        directory = []
        exists = False
        for _name, _fs in self.iterate_fs():
            try:
                directory.extend(_fs.listdir(path))
            except errors.ResourceNotFound:
                pass
            else:
                exists = True
        if not exists:
            raise errors.ResourceNotFound(path)
        directory = list(OrderedDict.fromkeys(directory))
        return directory

    def makedir(
        self,  # type: M
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        self.check()
        write_fs = self._writable_required(path)
        return write_fs.makedir(path, permissions=permissions, recreate=recreate)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        self.check()
        if check_writable(mode):
            _fs = self._writable_required(path)
        else:
            _fs = self._delegate_required(path)
        return _fs.openbin(path, mode=mode, buffering=buffering, **options)

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        fs = self._delegate_required(path)
        return fs.remove(path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        fs = self._delegate_required(path)
        return fs.removedir(path)

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        self.check()
        seen = set()  # type: MutableSet[Text]
        exists = False
        for _name, fs in self.iterate_fs():
            try:
                for info in fs.scandir(path, namespaces=namespaces, page=page):
                    if info.name not in seen:
                        yield info
                        seen.add(info.name)
                exists = True
            except errors.ResourceNotFound:
                pass

        if not exists:
            raise errors.ResourceNotFound(path)

    def getbytes(self, path):
        # type: (Text) -> bytes
        self.check()
        fs = self._delegate(path)
        if fs is None:
            raise errors.ResourceNotFound(path)
        return fs.getbytes(path)

    def getfile(self, path, file, chunk_size=None, **options):
        # type: (Text, BinaryIO, Optional[int], **Any) -> None
        fs = self._delegate_required(path)
        return fs.getfile(path, file, chunk_size=chunk_size, **options)

    def gettext(self, path, encoding=None, errors=None, newline=""):
        # type: (Text, Optional[Text], Optional[Text], Text) -> Text
        self.check()
        fs = self._delegate_required(path)
        return fs.gettext(path, encoding=encoding, errors=errors, newline=newline)

    def getsize(self, path):
        # type: (Text) -> int
        self.check()
        fs = self._delegate_required(path)
        return fs.getsize(path)

    def getsyspath(self, path):
        # type: (Text) -> Text
        self.check()
        fs = self._delegate_required(path)
        return fs.getsyspath(path)

    def gettype(self, path):
        # type: (Text) -> ResourceType
        self.check()
        fs = self._delegate_required(path)
        return fs.gettype(path)

    def geturl(self, path, purpose="download"):
        # type: (Text, Text) -> Text
        self.check()
        fs = self._delegate_required(path)
        return fs.geturl(path, purpose=purpose)

    def hassyspath(self, path):
        # type: (Text) -> bool
        self.check()
        fs = self._delegate(path)
        return fs is not None and fs.hassyspath(path)

    def hasurl(self, path, purpose="download"):
        # type: (Text, Text) -> bool
        self.check()
        fs = self._delegate(path)
        return fs is not None and fs.hasurl(path, purpose=purpose)

    def isdir(self, path):
        # type: (Text) -> bool
        self.check()
        fs = self._delegate(path)
        return fs is not None and fs.isdir(path)

    def isfile(self, path):
        # type: (Text) -> bool
        self.check()
        fs = self._delegate(path)
        return fs is not None and fs.isfile(path)

    def setinfo(self, path, info):
        # type:(Text, RawInfo) -> None
        self.check()
        write_fs = self._writable_required(path)
        return write_fs.setinfo(path, info)

    def validatepath(self, path):
        # type: (Text) -> Text
        self.check()
        if self.write_fs is not None:
            self.write_fs.validatepath(path)
        else:
            super(MultiFS, self).validatepath(path)
        path = abspath(normpath(path))
        return path

    def makedirs(
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        self.check()
        write_fs = self._writable_required(path)
        return write_fs.makedirs(path, permissions=permissions, recreate=recreate)

    def open(
        self,
        path,  # type: Text
        mode="r",  # type: Text
        buffering=-1,  # type: int
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
        **kwargs  # type: Any
    ):
        # type: (...) -> IO
        self.check()
        if check_writable(mode):
            _fs = self._writable_required(path)
        else:
            _fs = self._delegate_required(path)
        return _fs.open(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            **kwargs
        )

    def setbinfile(self, path, file):
        # type: (Text, BinaryIO) -> None
        self._writable_required(path).setbinfile(path, file)

    def setbytes(self, path, contents):
        # type: (Text, bytes) -> None
        self._writable_required(path).setbytes(path, contents)

    def settext(
        self,
        path,  # type: Text
        contents,  # type: Text
        encoding="utf-8",  # type: Text
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        write_fs = self._writable_required(path)
        return write_fs.settext(
            path, contents, encoding=encoding, errors=errors, newline=newline
        )
