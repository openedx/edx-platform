"""Collection of useful `~fs.wrapfs.WrapFS` subclasses.

Here's an example that opens a filesystem then makes it *read only*::

    >>> from fs import open_fs
    >>> from fs.wrap import read_only
    >>> projects_fs = open_fs('~/projects')
    >>> read_only_projects_fs = read_only(projects_fs)
    >>> read_only_projects_fs.remove('__init__.py')
    Traceback (most recent call last):
      ...
    fs.errors.ResourceReadOnly: resource '__init__.py' is read only

"""

from __future__ import print_function
from __future__ import unicode_literals

import typing

from .wrapfs import WrapFS
from .path import abspath, normpath, split
from .errors import ResourceReadOnly, ResourceNotFound
from .info import Info
from .mode import check_writable

if False:  # typing.TYPE_CHECKING
    from datetime import datetime
    from typing import (
        Any,
        BinaryIO,
        Collection,
        Dict,
        Iterator,
        IO,
        Optional,
        Text,
        Tuple,
    )
    from .base import FS
    from .info import Info, RawInfo
    from .subfs import SubFS
    from .permissions import Permissions


_W = typing.TypeVar("_W", bound="WrapFS")
_T = typing.TypeVar("_T", bound="FS")
_F = typing.TypeVar("_F", bound="FS", covariant=True)


def read_only(fs):
    # type: (_T) -> WrapReadOnly[_T]
    """Make a read-only filesystem.

    Arguments:
        fs (FS): A filesystem instance.

    Returns:
        FS: A read only version of ``fs``

    """
    return WrapReadOnly(fs)


def cache_directory(fs):
    # type: (_T) -> WrapCachedDir[_T]
    """Make a filesystem that caches directory information.

    Arguments:
        fs (FS): A filesystem instance.

    Returns:
        FS: A filesystem that caches results of `~FS.scandir`, `~FS.isdir`
        and other methods which read directory information.

    """
    return WrapCachedDir(fs)


class WrapCachedDir(WrapFS[_F], typing.Generic[_F]):
    """Caches filesystem directory information.

    This filesystem caches directory information retrieved from a
    scandir call. This *may* speed up code that calls `~FS.isdir`,
    `~FS.isfile`, or `~FS.gettype` too frequently.

    Note:
        Using this wrap will prevent changes to directory information
        being visible to the filesystem object. Consequently it is best
        used only in a fairly limited scope where you don't expected
        anything on the filesystem to change.

    """

    wrap_name = "cached-dir"

    def __init__(self, wrap_fs):
        # type: (_F) -> None
        super(WrapCachedDir, self).__init__(wrap_fs)
        self._cache = {}  # type: Dict[Tuple[Text, frozenset], Dict[Text, Info]]

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        _path = abspath(normpath(path))
        cache_key = (_path, frozenset(namespaces or ()))
        if cache_key not in self._cache:
            _scan_result = self._wrap_fs.scandir(path, namespaces=namespaces, page=page)
            _dir = {info.name: info for info in _scan_result}
            self._cache[cache_key] = _dir
        gen_scandir = iter(self._cache[cache_key].values())
        return gen_scandir

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        _path = abspath(normpath(path))
        if _path == "/":
            return Info({"basic": {"name": "", "is_dir": True}})
        dir_path, resource_name = split(_path)
        cache_key = (dir_path, frozenset(namespaces or ()))

        if cache_key not in self._cache:
            self.scandir(dir_path, namespaces=namespaces)

        _dir = self._cache[cache_key]
        try:
            info = _dir[resource_name]
        except KeyError:
            raise ResourceNotFound(path)
        return info

    def isdir(self, path):
        # type: (Text) -> bool
        # FIXME(@althonos): this raises an error on non-existing file !
        return self.getinfo(path).is_dir

    def isfile(self, path):
        # type: (Text) -> bool
        # FIXME(@althonos): this raises an error on non-existing file !
        return not self.getinfo(path).is_dir


class WrapReadOnly(WrapFS[_F], typing.Generic[_F]):
    """Makes a Filesystem read-only.

    Any call that would would write data or modify the filesystem in any way
    will raise a `~fs.errors.ResourceReadOnly` exception.

    """

    wrap_name = "read-only"

    def appendbytes(self, path, data):
        # type: (Text, bytes) -> None
        self.check()
        raise ResourceReadOnly(path)

    def appendtext(
        self,
        path,  # type: Text
        text,  # type: Text
        encoding="utf-8",  # type: Text
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        self.check()
        raise ResourceReadOnly(path)

    def makedir(
        self,  # type: _W
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_W]
        self.check()
        raise ResourceReadOnly(path)

    def move(self, src_path, dst_path, overwrite=False):
        # type: (Text, Text, bool) -> None
        self.check()
        raise ResourceReadOnly(dst_path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        self.check()
        if check_writable(mode):
            raise ResourceReadOnly(path)
        return self._wrap_fs.openbin(path, mode=mode, buffering=-1, **options)

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        raise ResourceReadOnly(path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        raise ResourceReadOnly(path)

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        raise ResourceReadOnly(path)

    def settext(
        self,
        path,  # type: Text
        contents,  # type: Text
        encoding="utf-8",  # type: Text
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        self.check()
        raise ResourceReadOnly(path)

    def settimes(self, path, accessed=None, modified=None):
        # type: (Text, Optional[datetime], Optional[datetime]) -> None
        self.check()
        raise ResourceReadOnly(path)

    def copy(self, src_path, dst_path, overwrite=False):
        # type: (Text, Text, bool) -> None
        self.check()
        raise ResourceReadOnly(dst_path)

    def create(self, path, wipe=False):
        # type: (Text, bool) -> bool
        self.check()
        raise ResourceReadOnly(path)

    def makedirs(
        self,  # type: _W
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_W]
        self.check()
        raise ResourceReadOnly(path)

    def open(
        self,
        path,  # type: Text
        mode="r",  # type: Text
        buffering=-1,  # type: int
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
        line_buffering=False,  # type: bool
        **options  # type: Any
    ):
        # type: (...) -> IO
        self.check()
        if check_writable(mode):
            raise ResourceReadOnly(path)
        return self._wrap_fs.open(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            line_buffering=line_buffering,
            **options
        )

    def setbytes(self, path, contents):
        # type: (Text, bytes) -> None
        self.check()
        raise ResourceReadOnly(path)

    def setbinfile(self, path, file):
        # type: (Text, BinaryIO) -> None
        self.check()
        raise ResourceReadOnly(path)

    def setfile(
        self,
        path,  # type: Text
        file,  # type: IO
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        self.check()
        raise ResourceReadOnly(path)

    def touch(self, path):
        # type: (Text) -> None
        self.check()
        raise ResourceReadOnly(path)
