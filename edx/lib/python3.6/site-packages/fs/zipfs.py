"""Manage the filesystem in a Zip archive.
"""

from __future__ import print_function
from __future__ import unicode_literals

import typing
import zipfile
from datetime import datetime

import six

from . import errors
from .base import FS
from .compress import write_zip
from .enums import ResourceType, Seek
from .info import Info
from .iotools import RawWrapper
from .permissions import Permissions
from .memoryfs import MemoryFS
from .opener import open_fs
from .path import dirname, forcedir, normpath, relpath
from .time import datetime_to_epoch
from .wrapfs import WrapFS

if False:  # typing.TYPE_CHECKING
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Dict,
        List,
        Optional,
        SupportsInt,
        Text,
        Tuple,
        Union,
    )
    from .info import RawInfo
    from .subfs import SubFS

    R = typing.TypeVar("R", bound="ReadZipFS")


class _ZipExtFile(RawWrapper):
    def __init__(self, fs, name):
        # type: (ReadZipFS, Text) -> None
        self._zip = _zip = fs._zip
        self._end = _zip.getinfo(name).file_size
        self._pos = 0
        super(_ZipExtFile, self).__init__(_zip.open(name), "r", name)

    def read(self, size=-1):
        # type: (int) -> bytes
        buf = self._f.read(-1 if size is None else size)
        self._pos += len(buf)
        return buf

    def read1(self, size=-1):
        # type: (int) -> bytes
        buf = self._f.read1(-1 if size is None else size)  # type: ignore
        self._pos += len(buf)
        return buf

    def seek(self, offset, whence=Seek.set):
        # type: (int, SupportsInt) -> int
        """Change stream position.

        Change the stream position to the given byte offset. The
        offset is interpreted relative to the position indicated by
        ``whence``.

        Arguments:
            offset (int): the offset to the new position, in bytes.
            whence (int): the position reference. Possible values are:
                * `Seek.set`: start of stream (the default).
                * `Seek.current`: current position; offset may be negative.
                * `Seek.end`: end of stream; offset must be negative.

        Returns:
            int: the new absolute position.

        Raises:
            ValueError: when ``whence`` is not known, or ``offset``
                is invalid.

        Note:
            Zip compression does not support seeking, so the seeking
            is emulated. Seeking somewhere else than the current position
            will need to either:
                * reopen the file and restart decompression
                * read and discard data to advance in the file

        """
        _whence = int(whence)
        if _whence == Seek.current:
            offset += self._pos
        if _whence == Seek.current or _whence == Seek.set:
            if offset < 0:
                raise ValueError("Negative seek position {}".format(offset))
        elif _whence == Seek.end:
            if offset > 0:
                raise ValueError("Positive seek position {}".format(offset))
            offset += self._end
        else:
            raise ValueError(
                "Invalid whence ({}, should be {}, {} or {})".format(
                    _whence, Seek.set, Seek.current, Seek.end
                )
            )

        if offset < self._pos:
            self._f = self._zip.open(self.name)  # type: ignore
            self._pos = 0
        self.read(offset - self._pos)
        return self._pos

    def tell(self):
        # type: () -> int
        return self._pos


class ZipFS(WrapFS):
    """Read and write zip files.

    There are two ways to open a ZipFS for the use cases of reading
    a zip file, and creating a new one.

    If you open the ZipFS with  ``write`` set to `False` (the default)
    then the filesystem will be a read only filesystem which maps to
    the files and directories within the zip file. Files are
    decompressed on the fly when you open them.

    Here's how you might extract and print a readme from a zip file::

        with ZipFS('foo.zip') as zip_fs:
            readme = zip_fs.gettext('readme.txt')

    If you open the ZipFS with ``write`` set to `True`, then the ZipFS
    will be a empty temporary filesystem. Any files / directories you
    create in the ZipFS will be written in to a zip file when the ZipFS
    is closed.

    Here's how you might write a new zip file containing a readme.txt
    file::

        with ZipFS('foo.zip', write=True) as new_zip:
            new_zip.settext(
                'readme.txt',
                'This zip file was written by PyFilesystem'
            )


    Arguments:
        file (str or io.IOBase): An OS filename, or an open file object.
        write (bool): Set to `True` to write a new zip file, or `False`
            (default) to read an existing zip file.
        compression (int): Compression to use (one of the constants
            defined in the `zipfile` module in the stdlib).
        temp_fs (str): An FS URL for the temporary filesystem used to
            store data prior to zipping.

    """

    def __new__(
        cls,
        file,  # type: Union[Text, BinaryIO]
        write=False,  # type: bool
        compression=zipfile.ZIP_DEFLATED,  # type: int
        encoding="utf-8",  # type: Text
        temp_fs="temp://__ziptemp__",  # type: Text
    ):
        # type: (...) -> FS
        # This magic returns a different class instance based on the
        # value of the ``write`` parameter.
        if write:
            return WriteZipFS(
                file, compression=compression, encoding=encoding, temp_fs=temp_fs
            )
        else:
            return ReadZipFS(file, encoding=encoding)

    if False:  # typing.TYPE_CHECKING

        def __init__(
            self,
            file,  # type: Union[Text, BinaryIO]
            write=False,  # type: bool
            compression=zipfile.ZIP_DEFLATED,  # type: int
            encoding="utf-8",  # type: Text
            temp_fs="temp://__ziptemp__",  # type: Text
        ):
            # type: (...) -> None
            pass


@six.python_2_unicode_compatible
class WriteZipFS(WrapFS):
    """A writable zip file.
    """

    def __init__(
        self,
        file,  # type: Union[Text, BinaryIO]
        compression=zipfile.ZIP_DEFLATED,  # type: int
        encoding="utf-8",  # type: Text
        temp_fs="temp://__ziptemp__",  # type: Text
    ):
        # type: (...) -> None
        self._file = file
        self.compression = compression
        self.encoding = encoding
        self._temp_fs_url = temp_fs
        self._temp_fs = open_fs(temp_fs)
        self._meta = dict(self._temp_fs.getmeta())  # type: ignore
        super(WriteZipFS, self).__init__(self._temp_fs)

    def __repr__(self):
        # type: () -> Text
        t = "WriteZipFS({!r}, compression={!r}, encoding={!r}, temp_fs={!r})"
        return t.format(self._file, self.compression, self.encoding, self._temp_fs_url)

    def __str__(self):
        # type: () -> Text
        return "<zipfs-write '{}'>".format(self._file)

    def delegate_path(self, path):
        # type: (Text) -> Tuple[FS, Text]
        return self._temp_fs, path

    def delegate_fs(self):
        # type: () -> FS
        return self._temp_fs

    def close(self):
        # type: () -> None
        if not self.isclosed():
            try:
                self.write_zip()
            finally:
                self._temp_fs.close()
        super(WriteZipFS, self).close()

    def write_zip(
        self,
        file=None,  # type: Union[Text, BinaryIO, None]
        compression=None,  # type: Optional[int]
        encoding=None,  # type: Optional[Text]
    ):
        # type: (...) -> None
        """Write zip to a file.

        Arguments:
            file (str or io.IOBase, optional): Destination file, may be
                a file name or an open file handle.
            compression (int, optional): Compression to use (one of the
                constants defined in the `zipfile` module in the stdlib).
            encoding (str, optional): The character encoding to use
                (default uses the encoding defined in
                `~WriteZipFS.__init__`).

        Note:
            This is called automatically when the ZipFS is closed.

        """
        if not self.isclosed():
            write_zip(
                self._temp_fs,
                file or self._file,
                compression=compression or self.compression,
                encoding=encoding or self.encoding,
            )


@six.python_2_unicode_compatible
class ReadZipFS(FS):
    """A readable zip file.
    """

    _meta = {
        "case_insensitive": True,
        "network": False,
        "read_only": True,
        "supports_rename": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
    }

    @errors.CreateFailed.catch_all
    def __init__(self, file, encoding="utf-8"):
        # type: (Union[BinaryIO, Text], Text) -> None
        super(ReadZipFS, self).__init__()
        self._file = file
        self.encoding = encoding
        self._zip = zipfile.ZipFile(file, "r")
        self._directory_fs = None  # type: Optional[MemoryFS]

    def __repr__(self):
        # type: () -> Text
        return "ReadZipFS({!r})".format(self._file)

    def __str__(self):
        # type: () -> Text
        return "<zipfs '{}'>".format(self._file)

    def _path_to_zip_name(self, path):
        # type: (Text) -> str
        """Convert a path to a zip file name.
        """
        path = relpath(normpath(path))
        if self._directory.isdir(path):
            path = forcedir(path)
        if six.PY2:
            return path.encode(self.encoding)
        return path

    @property
    def _directory(self):
        # type: () -> MemoryFS
        """`MemoryFS`: a filesystem with the same folder hierarchy as the zip.
        """
        self.check()
        with self._lock:
            if self._directory_fs is None:
                self._directory_fs = _fs = MemoryFS()
                for zip_name in self._zip.namelist():
                    resource_name = zip_name
                    if six.PY2:
                        resource_name = resource_name.decode(self.encoding, "replace")
                    if resource_name.endswith("/"):
                        _fs.makedirs(resource_name, recreate=True)
                    else:
                        _fs.makedirs(dirname(resource_name), recreate=True)
                        _fs.create(resource_name)
            return self._directory_fs

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        _path = self.validatepath(path)
        namespaces = namespaces or ()
        raw_info = {}  # type: Dict[Text, Dict[Text, object]]

        if _path == "/":
            raw_info["basic"] = {"name": "", "is_dir": True}
            if "details" in namespaces:
                raw_info["details"] = {"type": int(ResourceType.directory)}

        else:
            basic_info = self._directory.getinfo(_path)
            raw_info["basic"] = {"name": basic_info.name, "is_dir": basic_info.is_dir}

            if not {"details", "access", "zip"}.isdisjoint(namespaces):
                zip_name = self._path_to_zip_name(path)
                try:
                    zip_info = self._zip.getinfo(zip_name)
                except KeyError:
                    # Can occur if there is an implied directory in the zip
                    pass
                else:
                    if "details" in namespaces:
                        raw_info["details"] = {
                            "size": zip_info.file_size,
                            "type": int(
                                ResourceType.directory
                                if basic_info.is_dir
                                else ResourceType.file
                            ),
                            "modified": datetime_to_epoch(
                                datetime(*zip_info.date_time)
                            ),
                        }
                    if "zip" in namespaces:
                        raw_info["zip"] = {
                            k: getattr(zip_info, k)
                            for k in zip_info.__slots__  # type: ignore
                            if not k.startswith("_")
                        }
                    if "access" in namespaces:
                        # check the zip was created on UNIX to get permissions
                        if zip_info.external_attr and zip_info.create_system == 3:
                            raw_info["access"] = {
                                "permissions": Permissions(
                                    mode=zip_info.external_attr >> 16 & 0xFFF
                                ).dump()
                            }

        return Info(raw_info)

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        return self._directory.listdir(path)

    def makedir(
        self,  # type: R
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[R]
        self.check()
        raise errors.ResourceReadOnly(path)

    def openbin(self, path, mode="r", buffering=-1, **kwargs):
        # type: (Text, Text, int, **Any) -> BinaryIO
        self.check()
        if "w" in mode or "+" in mode or "a" in mode:
            raise errors.ResourceReadOnly(path)

        if not self._directory.exists(path):
            raise errors.ResourceNotFound(path)
        elif self._directory.isdir(path):
            raise errors.FileExpected(path)

        zip_name = self._path_to_zip_name(path)
        return _ZipExtFile(self, zip_name)  # type: ignore

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        raise errors.ResourceReadOnly(path)

    def close(self):
        # type: () -> None
        super(ReadZipFS, self).close()
        self._zip.close()

    def getbytes(self, path):
        # type: (Text) -> bytes
        self.check()
        if not self._directory.isfile(path):
            raise errors.ResourceNotFound(path)
        zip_name = self._path_to_zip_name(path)
        zip_bytes = self._zip.read(zip_name)
        return zip_bytes
