"""Base class for filesystem wrappers.
"""

from __future__ import unicode_literals

import copy
import typing

import six

from . import errors
from .base import FS
from .copy import copy_file
from .info import Info
from .move import move_file
from .path import abspath, normpath
from .error_tools import unwrap_errors

if False:  # typing.TYPE_CHECKING
    from datetime import datetime
    from threading import RLock
    from typing import (
        Any,
        AnyStr,
        BinaryIO,
        Callable,
        Collection,
        Dict,
        Iterator,
        Iterable,
        IO,
        List,
        Mapping,
        Optional,
        Text,
        TextIO,
        Tuple,
        Union,
    )
    from .enums import ResourceType
    from .info import RawInfo
    from .permissions import Permissions
    from .subfs import SubFS
    from .walk import BoundWalker

    _T = typing.TypeVar("_T", bound="FS")
    _OpendirFactory = Callable[[_T, Text], SubFS[_T]]


_F = typing.TypeVar("_F", bound="FS", covariant=True)
_W = typing.TypeVar("_W", bound="WrapFS[FS]")


@six.python_2_unicode_compatible
class WrapFS(FS, typing.Generic[_F]):
    """A proxy for a filesystem object.

    This class exposes an filesystem interface, where the data is
    stored on another filesystem(s), and is the basis for
    `~fs.subfs.SubFS` and other *virtual* filesystems.

    """

    wrap_name = None  # type: Optional[Text]

    def __init__(self, wrap_fs):
        # type: (_F) -> None
        self._wrap_fs = wrap_fs
        super(WrapFS, self).__init__()

    def __repr__(self):
        # type: () -> Text
        return "{}({!r})".format(self.__class__.__name__, self._wrap_fs)

    def __str__(self):
        # type: () -> Text
        wraps = []
        _fs = self  # type: Union[FS, WrapFS[FS]]
        while hasattr(_fs, "_wrap_fs"):
            wrap_name = getattr(_fs, "wrap_name", None)
            if wrap_name is not None:
                wraps.append(wrap_name)
            _fs = _fs._wrap_fs  # type: ignore
        if wraps:
            _str = "{}({})".format(_fs, ", ".join(wraps[::-1]))
        else:
            _str = "{}".format(_fs)
        return _str

    def delegate_path(self, path):
        # type: (Text) -> Tuple[_F, Text]
        """Encode a path for proxied filesystem.

        Arguments:
            path (str): A path on the filesystem.

        Returns:
            (FS, str): a tuple of ``(<filesystem>, <new_path>)``

        """
        return self._wrap_fs, path

    def delegate_fs(self):
        # type: () -> _F
        """Get the proxied filesystem.

        This method should return a filesystem for methods not
        associated with a path, e.g. `~fs.base.FS.getmeta`.

        """
        return self._wrap_fs

    def appendbytes(self, path, data):
        # type: (Text, bytes) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.appendbytes(_path, data)

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
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.appendtext(
                _path, text, encoding=encoding, errors=errors, newline=newline
            )

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            raw_info = _fs.getinfo(_path, namespaces=namespaces).raw
        if abspath(normpath(path)) == "/":
            raw_info = dict(raw_info)
            raw_info["basic"]["name"] = ""  # type: ignore
        return Info(raw_info)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            dir_list = _fs.listdir(_path)
        return dir_list

    def lock(self):
        # type: () -> RLock
        self.check()
        _fs = self.delegate_fs()
        return _fs.lock()

    def makedir(
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.makedir(_path, permissions=permissions, recreate=recreate)

    def move(self, src_path, dst_path, overwrite=False):
        # type: (Text, Text, bool) -> None
        # A custom move permits a potentially optimized code path
        src_fs, _src_path = self.delegate_path(src_path)
        dst_fs, _dst_path = self.delegate_path(dst_path)
        with unwrap_errors({_src_path: src_path, _dst_path: dst_path}):
            if not overwrite and dst_fs.exists(_dst_path):
                raise errors.DestinationExists(_dst_path)
            move_file(src_fs, _src_path, dst_fs, _dst_path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            bin_file = _fs.openbin(_path, mode=mode, buffering=-1, **options)
        return bin_file

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.remove(_path)

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        _path = abspath(normpath(path))
        if _path == "/":
            raise errors.RemoveRootError()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.removedir(_path)

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            for info in _fs.scandir(_path, namespaces=namespaces, page=page):
                yield info

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        return _fs.setinfo(_path, info)

    def settimes(self, path, accessed=None, modified=None):
        # type: (Text, Optional[datetime], Optional[datetime]) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.settimes(_path, accessed=accessed, modified=modified)

    def touch(self, path):
        # type: (Text) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.touch(_path)

    def copy(self, src_path, dst_path, overwrite=False):
        # type: (Text, Text, bool) -> None
        src_fs, _src_path = self.delegate_path(src_path)
        dst_fs, _dst_path = self.delegate_path(dst_path)
        with unwrap_errors({_src_path: src_path, _dst_path: dst_path}):
            if not overwrite and dst_fs.exists(_dst_path):
                raise errors.DestinationExists(_dst_path)
            copy_file(src_fs, _src_path, dst_fs, _dst_path)

    def create(self, path, wipe=False):
        # type: (Text, bool) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.create(_path, wipe=wipe)

    def desc(self, path):
        # type: (Text) -> Text
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            desc = _fs.desc(_path)
        return desc

    def exists(self, path):
        # type: (Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            exists = _fs.exists(_path)
        return exists

    def filterdir(
        self,
        path,  # type: Text
        files=None,  # type: Optional[Iterable[Text]]
        dirs=None,  # type: Optional[Iterable[Text]]
        exclude_dirs=None,  # type: Optional[Iterable[Text]]
        exclude_files=None,  # type: Optional[Iterable[Text]]
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        self.check()
        _fs, _path = self.delegate_path(path)
        iter_files = iter(
            _fs.filterdir(
                _path,
                exclude_dirs=exclude_dirs,
                exclude_files=exclude_files,
                files=files,
                dirs=dirs,
                namespaces=namespaces,
                page=page,
            )
        )
        with unwrap_errors(path):
            for info in iter_files:
                yield info

    def getbytes(self, path):
        # type: (Text) -> bytes
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _bytes = _fs.getbytes(_path)
        return _bytes

    def gettext(
        self,
        path,  # type: Text
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> Text
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _text = _fs.gettext(
                _path, encoding=encoding, errors=errors, newline=newline
            )
        return _text

    def getmeta(self, namespace="standard"):
        # type: (Text) -> Mapping[Text, object]
        self.check()
        meta = self.delegate_fs().getmeta(namespace=namespace)
        return meta

    def getsize(self, path):
        # type: (Text) -> int
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            size = _fs.getsize(_path)
        return size

    def getsyspath(self, path):
        # type: (Text) -> Text
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            sys_path = _fs.getsyspath(_path)
        return sys_path

    def gettype(self, path):
        # type: (Text) -> ResourceType
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _type = _fs.gettype(_path)
        return _type

    def geturl(self, path, purpose="download"):
        # type: (Text, Text) -> Text
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            return _fs.geturl(_path, purpose=purpose)

    def hassyspath(self, path):
        # type: (Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            has_sys_path = _fs.hassyspath(_path)
        return has_sys_path

    def hasurl(self, path, purpose="download"):
        # type: (Text, Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            has_url = _fs.hasurl(_path, purpose=purpose)
        return has_url

    def isdir(self, path):
        # type: (Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _isdir = _fs.isdir(_path)
        return _isdir

    def isfile(self, path):
        # type: (Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _isfile = _fs.isfile(_path)
        return _isfile

    def islink(self, path):
        # type: (Text) -> bool
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _islink = _fs.islink(_path)
        return _islink

    def makedirs(
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        self.check()
        _fs, _path = self.delegate_path(path)
        return _fs.makedirs(_path, permissions=permissions, recreate=recreate)

    # FIXME(@althonos): line_buffering is not a FS.open declared argument
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
        # type: (...) -> IO[AnyStr]
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            open_file = _fs.open(
                _path,
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
                line_buffering=line_buffering,
                **options
            )
        return open_file

    def opendir(
        self,  # type: _W
        path,  # type: Text
        factory=None,  # type: Optional[_OpendirFactory]
    ):
        # type: (...) -> SubFS[_W]
        from .subfs import SubFS

        factory = factory or SubFS
        if not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(path=path)
        with unwrap_errors(path):
            return factory(self, path)

    def setbytes(self, path, contents):
        # type: (Text, bytes) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setbytes(_path, contents)

    def setbinfile(self, path, file):
        # type: (Text, BinaryIO) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setbinfile(_path, file)

    def setfile(
        self,
        path,  # type: Text
        file,  # type: IO[AnyStr]
        encoding=None,  # type: Optional[Text]
        errors=None,  # type: Optional[Text]
        newline="",  # type: Text
    ):
        # type: (...) -> None
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.setfile(_path, file, encoding=encoding, errors=errors, newline=newline)

    def validatepath(self, path):
        # type: (Text) -> Text
        self.check()
        _fs, _path = self.delegate_path(path)
        with unwrap_errors(path):
            _fs.validatepath(_path)
        path = abspath(normpath(path))
        return path

    @property
    def walk(self):
        # type: () -> BoundWalker
        return self._wrap_fs.walker_class.bind(self)
