"""Manage a volatile in-memory filesystem.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import io
import os
import time
import typing
from collections import OrderedDict
from threading import RLock

import six

from . import errors
from .base import FS
from .enums import ResourceType, Seek
from .info import Info
from .mode import Mode
from .path import iteratepath
from .path import normpath
from .path import split
from ._typing import overload

if False:  # typing.TYPE_CHECKING
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Dict,
        Iterator,
        List,
        Optional,
        SupportsInt,
        Union,
        Text,
    )
    from .base import _OpendirFactory
    from .info import RawInfo
    from .permissions import Permissions
    from .subfs import SubFS

    _M = typing.TypeVar("_M", bound="MemoryFS")


@six.python_2_unicode_compatible
class _MemoryFile(io.RawIOBase):
    def __init__(self, path, memory_fs, mode, dir_entry):
        # type: (Text, MemoryFS, Text, _DirEntry) -> None
        super(_MemoryFile, self).__init__()
        self._path = path
        self._memory_fs = memory_fs
        self._mode = Mode(mode)
        self._dir_entry = dir_entry

        # We are opening a file - dir_entry.bytes_file is not None
        self._bytes_io = typing.cast(io.BytesIO, dir_entry.bytes_file)

        self.accessed_time = time.time()
        self.modified_time = time.time()
        self.pos = 0

        if self._mode.truncate:
            with self._dir_entry.lock:
                self._bytes_io.seek(0)
                self._bytes_io.truncate()
        elif self._mode.appending:
            with self._dir_entry.lock:
                self._bytes_io.seek(0, os.SEEK_END)
                self.pos = self._bytes_io.tell()

    def __str__(self):
        # type: () -> str
        _template = "<memoryfile '{path}' '{mode}'>"
        return _template.format(path=self._path, mode=self._mode)

    @contextlib.contextmanager
    def _seek_lock(self):
        # type: () -> Iterator[None]
        with self._dir_entry.lock:
            self._bytes_io.seek(self.pos)
            yield
            self.pos = self._bytes_io.tell()

    def on_modify(self):  # noqa: D401
        # type: () -> None
        """Called when file data is modified.
        """
        self._dir_entry.modified_time = self.modified_time = time.time()

    def on_access(self):  # noqa: D401
        # type: () -> None
        """Called when file is accessed.
        """
        self._dir_entry.accessed_time = self.accessed_time = time.time()

    def flush(self):
        # type: () -> None
        pass

    def __iter__(self):
        # type: () -> typing.Iterator[bytes]
        self._bytes_io.seek(self.pos)
        for line in self._bytes_io:
            yield line

    def next(self):
        # type: () -> bytes
        with self._seek_lock():
            return next(self._bytes_io)

    __next__ = next

    def readline(self, size=-1):
        # type: (int) -> bytes
        with self._seek_lock():
            self.on_access()
            return self._bytes_io.readline(size)

    def close(self):
        # type: () -> None
        if not self.closed:
            with self._dir_entry.lock:
                self._dir_entry.remove_open_file(self)
                super(_MemoryFile, self).close()

    def read(self, size=-1):
        # type: (Optional[int]) -> bytes
        if not self._mode.reading:
            raise IOError("File not open for reading")
        with self._seek_lock():
            self.on_access()
            return self._bytes_io.read(size)

    def readable(self):
        # type: () -> bool
        return self._mode.reading

    def readlines(self, hint=-1):
        # type: (int) -> List[bytes]
        with self._seek_lock():
            return self._bytes_io.readlines(hint)

    def seekable(self):
        # type: () -> bool
        return True

    def seek(self, pos, whence=Seek.set):
        # type: (int, SupportsInt) -> int
        # NOTE(@althonos): allows passing both Seek.set and os.SEEK_SET
        with self._seek_lock():
            self.on_access()
            return self._bytes_io.seek(pos, int(whence))

    def tell(self):
        # type: () -> int
        return self.pos

    def truncate(self, size=None):
        # type: (Optional[int]) -> int
        with self._seek_lock():
            self.on_modify()
            new_size = self._bytes_io.truncate(size)
            if size is not None and self._bytes_io.tell() < size:
                file_size = self._bytes_io.seek(0, os.SEEK_END)
                self._bytes_io.write(b"\0" * (size - file_size))
                self._bytes_io.seek(-size + file_size, os.SEEK_END)
            return size or new_size

    def writable(self):
        # type: () -> bool
        return self._mode.writing

    def write(self, data):
        # type: (bytes) -> int
        if not self._mode.writing:
            raise IOError("File not open for writing")
        with self._seek_lock():
            self.on_modify()
            return self._bytes_io.write(data)

    def writelines(self, sequence):  # type: ignore
        # type: (List[bytes]) -> None
        # FIXME(@althonos): For some reason the stub for IOBase.writelines
        #      is List[Any] ?! It should probably be Iterable[ByteString]
        with self._seek_lock():
            self.on_modify()
            self._bytes_io.writelines(sequence)


class _DirEntry(object):
    def __init__(self, resource_type, name):
        # type: (ResourceType, Text) -> None
        self.resource_type = resource_type
        self.name = name
        self._dir = OrderedDict()  # type: typing.MutableMapping[Text, _DirEntry]
        self._open_files = []  # type: typing.MutableSequence[_MemoryFile]
        self._bytes_file = None  # type: Optional[io.BytesIO]
        self.lock = RLock()

        current_time = time.time()
        self.created_time = current_time
        self.accessed_time = current_time
        self.modified_time = current_time

        if not self.is_dir:
            self._bytes_file = io.BytesIO()

    @property
    def bytes_file(self):
        # type: () -> Optional[io.BytesIO]
        return self._bytes_file

    @property
    def is_dir(self):
        # type: () -> bool
        return self.resource_type == ResourceType.directory

    @property
    def size(self):
        # type: () -> int
        with self.lock:
            if self.is_dir:
                return 0
            else:
                _bytes_file = typing.cast(io.BytesIO, self._bytes_file)
                _bytes_file.seek(0, os.SEEK_END)
                return _bytes_file.tell()

    @overload
    def get_entry(self, name, default):  # pragma: no cover
        # type: (Text, _DirEntry) -> _DirEntry
        pass

    @overload
    def get_entry(self, name):  # pragma: no cover
        # type: (Text) -> Optional[_DirEntry]
        pass

    @overload
    def get_entry(self, name, default):  # pragma: no cover
        # type: (Text, None) -> Optional[_DirEntry]
        pass

    def get_entry(self, name, default=None):
        # type: (Text, Optional[_DirEntry]) -> Optional[_DirEntry]
        assert self.is_dir, "must be a directory"
        return self._dir.get(name, default)

    def set_entry(self, name, dir_entry):
        # type: (Text, _DirEntry) -> None
        self._dir[name] = dir_entry

    def remove_entry(self, name):
        # type: (Text) -> None
        del self._dir[name]

    def __contains__(self, name):
        # type: (object) -> bool
        return name in self._dir

    def __len__(self):
        # type: () -> int
        return len(self._dir)

    def list(self):
        # type: () -> List[Text]
        return list(self._dir.keys())

    def add_open_file(self, memory_file):
        # type: (_MemoryFile) -> None
        self._open_files.append(memory_file)

    def remove_open_file(self, memory_file):
        # type: (_MemoryFile) -> None
        self._open_files.remove(memory_file)


@six.python_2_unicode_compatible
class MemoryFS(FS):
    """A filesystem that stored in memory.

    Memory filesystems are useful for caches, temporary data stores,
    unit testing, etc. Since all the data is in memory, they are very
    fast, but non-permanent. The `MemoryFS` constructor takes no
    arguments.

    Example:
        >>> mem_fs = MemoryFS()

    Or via an FS URL:
        >>> import fs
        >>> mem_fs = fs.open_fs('mem://')

    """

    _meta = {
        "case_insensitive": False,
        "invalid_path_chars": "\0",
        "network": False,
        "read_only": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
    }  # type: Dict[Text, Union[Text, int, bool, None]]

    def __init__(self):
        # type: () -> None
        """Create an in-memory filesystem.
        """
        self._meta = self._meta.copy()
        self.root = self._make_dir_entry(ResourceType.directory, "")
        super(MemoryFS, self).__init__()

    def __repr__(self):
        # type: () -> str
        return "MemoryFS()"

    def __str__(self):
        # type: () -> str
        return "<memfs>"

    def _make_dir_entry(self, resource_type, name):
        # type: (ResourceType, Text) -> _DirEntry
        return _DirEntry(resource_type, name)

    def _get_dir_entry(self, dir_path):
        # type: (Text) -> Optional[_DirEntry]
        """Get a directory entry, or `None` if one doesn't exist.
        """
        with self._lock:
            dir_path = normpath(dir_path)
            current_entry = self.root  # type: Optional[_DirEntry]
            for path_component in iteratepath(dir_path):
                if current_entry is None:
                    return None
                if not current_entry.is_dir:
                    return None
                current_entry = current_entry.get_entry(path_component)
            return current_entry

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        namespaces = namespaces or ()
        _path = self.validatepath(path)
        dir_entry = self._get_dir_entry(_path)
        if dir_entry is None:
            raise errors.ResourceNotFound(path)
        info = {"basic": {"name": dir_entry.name, "is_dir": dir_entry.is_dir}}
        if "details" in namespaces:
            info["details"] = {
                "_write": ["accessed", "modified"],
                "type": int(dir_entry.resource_type),
                "size": dir_entry.size,
                "accessed": dir_entry.accessed_time,
                "modified": dir_entry.modified_time,
                "created": dir_entry.created_time,
            }
        return Info(info)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        _path = self.validatepath(path)
        with self._lock:
            dir_entry = self._get_dir_entry(_path)
            if dir_entry is None:
                raise errors.ResourceNotFound(path)
            if not dir_entry.is_dir:
                raise errors.DirectoryExpected(path)
            return dir_entry.list()

    if False:  # typing.TYPE_CHECKING

        def opendir(self, path, factory=None):
            # type: (_M, Text, Optional[_OpendirFactory]) -> SubFS[_M]
            pass

    def makedir(
        self,  # type: _M
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_M]
        _path = self.validatepath(path)
        with self._lock:
            if _path == "/":
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)

            dir_path, dir_name = split(_path)

            parent_dir = self._get_dir_entry(dir_path)
            if parent_dir is None:
                raise errors.ResourceNotFound(path)

            dir_entry = parent_dir.get_entry(dir_name)
            if dir_entry is not None and not recreate:
                raise errors.DirectoryExists(path)

            if dir_entry is None:
                new_dir = self._make_dir_entry(ResourceType.directory, dir_name)
                parent_dir.set_entry(dir_name, new_dir)
            return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        _mode = Mode(mode)
        _mode.validate_bin()
        _path = self.validatepath(path)
        dir_path, file_name = split(_path)

        with self._lock:
            parent_dir_entry = self._get_dir_entry(dir_path)
            if parent_dir_entry is None or not parent_dir_entry.is_dir:
                raise errors.ResourceNotFound(path)

            if _mode.create:
                if file_name not in parent_dir_entry:
                    file_dir_entry = self._make_dir_entry(ResourceType.file, file_name)
                    parent_dir_entry.set_entry(file_name, file_dir_entry)
                else:
                    file_dir_entry = self._get_dir_entry(_path)  # type: ignore
                    if _mode.exclusive:
                        raise errors.FileExists(path)

                if file_dir_entry.is_dir:
                    raise errors.FileExpected(path)

                mem_file = _MemoryFile(
                    path=_path, memory_fs=self, mode=mode, dir_entry=file_dir_entry
                )

                file_dir_entry.add_open_file(mem_file)
                return mem_file  # type: ignore

            if file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            file_dir_entry = parent_dir_entry.get_entry(file_name)  # type: ignore
            if file_dir_entry.is_dir:
                raise errors.FileExpected(path)

            mem_file = _MemoryFile(
                path=_path, memory_fs=self, mode=mode, dir_entry=file_dir_entry
            )
            file_dir_entry.add_open_file(mem_file)
            return mem_file  # type: ignore

    def remove(self, path):
        # type: (Text) -> None
        _path = self.validatepath(path)

        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            file_dir_entry = typing.cast(_DirEntry, self._get_dir_entry(_path))
            if file_dir_entry.is_dir:
                raise errors.FileExpected(path)

            parent_dir_entry.remove_entry(file_name)

    def removedir(self, path):
        # type: (Text) -> None
        _path = self.validatepath(path)

        if _path == "/":
            raise errors.RemoveRootError()

        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            dir_dir_entry = typing.cast(_DirEntry, self._get_dir_entry(_path))
            if not dir_dir_entry.is_dir:
                raise errors.DirectoryExpected(path)

            if len(dir_dir_entry):
                raise errors.DirectoryNotEmpty(path)

            parent_dir_entry.remove_entry(file_name)

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        _path = self.validatepath(path)
        with self._lock:
            dir_path, file_name = split(_path)
            parent_dir_entry = self._get_dir_entry(dir_path)

            if parent_dir_entry is None or file_name not in parent_dir_entry:
                raise errors.ResourceNotFound(path)

            resource_entry = typing.cast(
                _DirEntry, parent_dir_entry.get_entry(file_name)
            )

            if "details" in info:
                details = info["details"]
                if "accessed" in details:
                    resource_entry.accessed_time = details["accessed"]  # type: ignore
                if "modified" in details:
                    resource_entry.modified_time = details["modified"]  # type: ignore
