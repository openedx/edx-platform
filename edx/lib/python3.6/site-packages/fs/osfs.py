"""Manage the filesystem provided by your OS.

In essence, an `OSFS` is a thin layer over the `io` and `os` modules
of the Python standard library.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import io
import itertools
import logging
import os
import platform
import shutil
import stat
import sys
import typing

import six

try:
    from os import scandir
except ImportError:
    try:
        from scandir import scandir  # type: ignore
    except ImportError:  # pragma: no cover
        scandir = None

try:
    from os import sendfile
except ImportError:
    try:
        from sendfile import sendfile
    except ImportError:
        sendfile = None

from . import errors
from .errors import FileExists
from .base import FS
from .enums import ResourceType
from ._fscompat import fsencode, fsdecode, fspath
from .info import Info
from .path import basename, dirname
from .permissions import Permissions
from .error_tools import convert_os_errors
from .mode import Mode, validate_open_mode
from .errors import NoURL

if False:  # typing.TYPE_CHECKING
    from typing import (
        Any,
        BinaryIO,
        Callable,
        Collection,
        Dict,
        Iterator,
        IO,
        List,
        Optional,
        SupportsInt,
        Text,
        Tuple,
    )
    from .base import _OpendirFactory
    from .info import RawInfo
    from .subfs import SubFS

    _O = typing.TypeVar("_O", bound="OSFS")


log = logging.getLogger("fs.osfs")


_WINDOWS_PLATFORM = platform.system() == "Windows"


@six.python_2_unicode_compatible
class OSFS(FS):
    """Create an OSFS.

    Arguments:
        root_path (str or ~os.PathLike): An OS path or path-like object to
            the location on your HD you wish to manage.
        create (bool): Set to `True` to create the root directory if it
            does not already exist, otherwise the directory should exist
            prior to creating the ``OSFS`` instance (defaults to `False`).
        create_mode (int): The permissions that will be used to create
            the directory if ``create`` is `True` and the path doesn't
            exist, defaults to ``0o777``.

    Raises:
        `fs.errors.CreateFailed`: If ``root_path`` does not
            exist, or could not be created.

    Examples:
        >>> current_directory_fs = OSFS('.')
        >>> home_fs = OSFS('~/')
        >>> windows_system32_fs = OSFS('c://system32')

    """

    def __init__(
        self,
        root_path,  # type: Text
        create=False,  # type: bool
        create_mode=0o777,  # type: SupportsInt
    ):
        # type: (...) -> None
        """Create an OSFS instance.
        """
        super(OSFS, self).__init__()
        if isinstance(root_path, bytes):
            root_path = fsdecode(root_path)
        self.root_path = root_path
        _drive, _root_path = os.path.splitdrive(fsdecode(fspath(root_path)))
        _root_path = _drive + (_root_path or '/') if _drive else _root_path
        _root_path = os.path.expanduser(os.path.expandvars(_root_path))
        _root_path = os.path.normpath(os.path.abspath(_root_path))
        self._root_path = _root_path

        if create:
            try:
                if not os.path.isdir(_root_path):
                    os.makedirs(_root_path, mode=int(create_mode))
            except OSError as error:
                raise errors.CreateFailed(
                    "unable to create {} ({})".format(root_path, error), error
                )
        else:
            if not os.path.isdir(_root_path):
                raise errors.CreateFailed("root path does not exist")

        _meta = self._meta = {
            "case_insensitive": os.path.normcase("Aa") != "aa",
            "network": False,
            "read_only": False,
            "supports_rename": True,
            "thread_safe": True,
            "unicode_paths": os.path.supports_unicode_filenames,
            "virtual": False,
        }

        if _WINDOWS_PLATFORM:  # pragma: no cover
            _meta["invalid_path_chars"] = (
                "".join(six.unichr(n) for n in range(31)) + '\\:*?"<>|'
            )
        else:
            _meta["invalid_path_chars"] = "\0"

            if "PC_PATH_MAX" in os.pathconf_names:
                _meta["max_sys_path_length"] = os.pathconf(
                    fsencode(_root_path), os.pathconf_names["PC_PATH_MAX"]
                )

    def __repr__(self):
        # type: () -> str
        _fmt = "{}({!r})"
        _class_name = self.__class__.__name__
        return _fmt.format(_class_name, self.root_path)

    def __str__(self):
        # type: () -> str
        fmt = "<{} '{}'>"
        _class_name = self.__class__.__name__
        return fmt.format(_class_name.lower(), self.root_path)

    def _to_sys_path(self, path):
        # type: (Text) -> Text
        """Convert a FS path to a path on the OS.
        """
        sys_path = fsencode(
            os.path.join(self._root_path, path.lstrip("/").replace("/", os.sep))
        )
        return sys_path

    @classmethod
    def _make_details_from_stat(cls, stat_result):
        # type: (os.stat_result) -> Dict[Text, object]
        """Make a *details* info dict from an `os.stat_result` object.
        """
        details = {
            "_write": ["accessed", "modified"],
            "accessed": stat_result.st_atime,
            "modified": stat_result.st_mtime,
            "size": stat_result.st_size,
            "type": int(cls._get_type_from_stat(stat_result)),
        }
        # On other Unix systems (such as FreeBSD), the following
        # attributes may be available (but may be only filled out if
        # root tries to use them):
        details["created"] = getattr(stat_result, "st_birthtime", None)
        ctime_key = "created" if _WINDOWS_PLATFORM else "metadata_changed"
        details[ctime_key] = stat_result.st_ctime
        return details

    @classmethod
    def _make_access_from_stat(cls, stat_result):
        # type: (os.stat_result) -> Dict[Text, object]
        """Make an *access* info dict from an `os.stat_result` object.
        """
        access = {}  # type: Dict[Text, object]
        access["permissions"] = Permissions(mode=stat_result.st_mode).dump()
        access["gid"] = gid = stat_result.st_gid
        access["uid"] = uid = stat_result.st_uid
        if not _WINDOWS_PLATFORM:
            import grp
            import pwd

            try:
                access["group"] = grp.getgrgid(gid).gr_name
            except KeyError:  # pragma: no cover
                pass

            try:
                access["user"] = pwd.getpwuid(uid).pw_name
            except KeyError:  # pragma: no cover
                pass
        return access

    STAT_TO_RESOURCE_TYPE = {
        stat.S_IFDIR: ResourceType.directory,
        stat.S_IFCHR: ResourceType.character,
        stat.S_IFBLK: ResourceType.block_special_file,
        stat.S_IFREG: ResourceType.file,
        stat.S_IFIFO: ResourceType.fifo,
        stat.S_IFLNK: ResourceType.symlink,
        stat.S_IFSOCK: ResourceType.socket,
    }

    @classmethod
    def _get_type_from_stat(cls, _stat):
        # type: (os.stat_result) -> ResourceType
        """Get the resource type from an `os.stat_result` object.
        """
        st_mode = _stat.st_mode
        st_type = stat.S_IFMT(st_mode)
        return cls.STAT_TO_RESOURCE_TYPE.get(st_type, ResourceType.unknown)

    # --------------------------------------------------------
    # Required Methods
    # --------------------------------------------------------

    def _gettarget(self, sys_path):
        # type: (Text) -> Optional[Text]
        try:
            target = os.readlink(fsencode(sys_path))
        except OSError:
            return None
        else:
            return target

    def _make_link_info(self, sys_path):
        # type: (Text) -> Dict[Text, object]
        _target = self._gettarget(sys_path)
        return {"target": _target}

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        self.check()
        namespaces = namespaces or ()
        _path = self.validatepath(path)
        sys_path = self.getsyspath(_path)
        _lstat = None
        with convert_os_errors("getinfo", path):
            _stat = os.stat(fsencode(sys_path))
            if "lstat" in namespaces:
                _lstat = os.lstat(fsencode(sys_path))

        info = {
            "basic": {"name": basename(_path), "is_dir": stat.S_ISDIR(_stat.st_mode)}
        }
        if "details" in namespaces:
            info["details"] = self._make_details_from_stat(_stat)
        if "stat" in namespaces:
            info["stat"] = {
                k: getattr(_stat, k) for k in dir(_stat) if k.startswith("st_")
            }
        if "lstat" in namespaces:
            info["lstat"] = {
                k: getattr(_lstat, k) for k in dir(_lstat) if k.startswith("st_")
            }
        if "link" in namespaces:
            info["link"] = self._make_link_info(sys_path)
        if "access" in namespaces:
            info["access"] = self._make_access_from_stat(_stat)

        return Info(info)

    def listdir(self, path):
        # type: (Text) -> List[Text]
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors("listdir", path, directory=True):
            names = os.listdir(fsencode(sys_path))
        return [fsdecode(name) for name in names]
        # return names

    def makedir(
        self,  # type: _O
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_O]
        self.check()
        mode = Permissions.get_mode(permissions)
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors("makedir", path, directory=True):
            try:
                os.mkdir(sys_path, mode)
            except OSError as error:
                if error.errno == errno.ENOENT:
                    raise errors.ResourceNotFound(path)
                elif error.errno == errno.EEXIST and recreate:
                    pass
                else:
                    raise
            return self.opendir(_path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors("openbin", path):
            if six.PY2 and _mode.exclusive:
                sys_path = os.open(sys_path, os.O_RDWR | os.O_CREAT | os.O_EXCL)
            binary_file = io.open(
                sys_path, mode=_mode.to_platform_bin(), buffering=buffering, **options
            )
        return binary_file  # type: ignore

    def remove(self, path):
        # type: (Text) -> None
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors("remove", path):
            try:
                os.remove(sys_path)
            except OSError as error:
                if error.errno == errno.EACCES and sys.platform == "win32":
                    # sometimes windows says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: no cover
                        raise errors.FileExpected(path)
                if error.errno == errno.EPERM and sys.platform == "darwin":
                    # sometimes OSX says this for attempts to remove a dir
                    if os.path.isdir(sys_path):  # pragma: no cover
                        raise errors.FileExpected(path)
                raise

    def removedir(self, path):
        # type: (Text) -> None
        self.check()
        _path = self.validatepath(path)
        if _path == "/":
            raise errors.RemoveRootError()
        sys_path = self._to_sys_path(path)
        with convert_os_errors("removedir", path, directory=True):
            os.rmdir(sys_path)

    # --------------------------------------------------------
    # Optional Methods
    # --------------------------------------------------------

    # --- Type hint for opendir ------------------------------

    if False:  # typing.TYPE_CHECKING

        def opendir(self, path, factory=None):
            # type: (_O, Text, Optional[_OpendirFactory]) -> SubFS[_O]
            pass


    # --- Backport of os.sendfile for Python < 3.8 -----------

    def _check_copy(self, src_path, dst_path, overwrite=False):
        # validate individual paths
        _src_path = self.validatepath(src_path)
        _dst_path = self.validatepath(dst_path)
        # check src_path exists and is a file
        if self.gettype(src_path) is not ResourceType.file:
            raise errors.FileExpected(src_path)
        # check dst_path does not exist if we are not overwriting
        if not overwrite and self.exists(_dst_path):
            raise errors.DestinationExists(dst_path)
        # check parent dir of _dst_path exists and is a directory
        if self.gettype(dirname(dst_path)) is not ResourceType.directory:
            raise errors.DirectoryExpected(dirname(dst_path))
        return _src_path, _dst_path


    if sys.version_info[:2] < (3, 8) and sendfile is not None:

        _sendfile_error_codes = frozenset({
            errno.EIO,
            errno.EINVAL,
            errno.ENOSYS,
            errno.ENOTSUP,
            errno.EBADF,
            errno.ENOTSOCK,
            errno.EOPNOTSUPP,
        })

        def copy(self, src_path, dst_path, overwrite=False):
            # type: (Text, Text, bool) -> None
            with self._lock:
                # validate and canonicalise paths
                _src_path, _dst_path = self._check_copy(src_path, dst_path, overwrite)
                _src_sys, _dst_sys = self.getsyspath(_src_path), self.getsyspath(_dst_path)
                # attempt using sendfile
                try:
                    # initialise variables to pass to sendfile
                    # open files to obtain a file descriptor
                    with io.open(_src_sys, 'r') as src:
                        with io.open(_dst_sys, 'w') as dst:
                            fd_src, fd_dst = src.fileno(), dst.fileno()
                            sent = maxsize = os.fstat(fd_src).st_size
                            offset = 0
                            while sent > 0:
                                sent = sendfile(fd_dst, fd_src, offset, maxsize)
                                offset += sent
                except OSError as e:
                    # the error is not a simple "sendfile not supported" error
                    if e.errno not in self._sendfile_error_codes:
                        raise
                    # fallback using the shutil implementation
                    shutil.copy2(_src_sys, _dst_sys)

    else:

        def copy(self, src_path, dst_path, overwrite=False):
            # type: (Text, Text, bool) -> None
            with self._lock:
                _src_path, _dst_path = self._check_copy(src_path, dst_path, overwrite)
                shutil.copy2(self.getsyspath(_src_path), self.getsyspath(_dst_path))

    # --- Backport of os.scandir for Python < 3.5 ------------

    if scandir:

        def _scandir(self, path, namespaces=None):
            # type: (Text, Optional[Collection[Text]]) -> Iterator[Info]
            self.check()
            namespaces = namespaces or ()
            _path = self.validatepath(path)
            sys_path = self._to_sys_path(_path)
            with convert_os_errors("scandir", path, directory=True):
                for dir_entry in scandir(sys_path):
                    info = {
                        "basic": {
                            "name": fsdecode(dir_entry.name),
                            "is_dir": dir_entry.is_dir(),
                        }
                    }
                    if "details" in namespaces:
                        stat_result = dir_entry.stat()
                        info["details"] = self._make_details_from_stat(stat_result)
                    if "stat" in namespaces:
                        stat_result = dir_entry.stat()
                        info["stat"] = {
                            k: getattr(stat_result, k)
                            for k in dir(stat_result)
                            if k.startswith("st_")
                        }
                    if "lstat" in namespaces:
                        lstat_result = dir_entry.stat(follow_symlinks=False)
                        info["lstat"] = {
                            k: getattr(lstat_result, k)
                            for k in dir(lstat_result)
                            if k.startswith("st_")
                        }
                    if "link" in namespaces:
                        info["link"] = self._make_link_info(
                            os.path.join(sys_path, dir_entry.name)
                        )
                    if "access" in namespaces:
                        stat_result = dir_entry.stat()
                        info["access"] = self._make_access_from_stat(stat_result)

                    yield Info(info)

    else:

        def _scandir(self, path, namespaces=None):
            # type: (Text, Optional[Collection[Text]]) -> Iterator[Info]
            self.check()
            namespaces = namespaces or ()
            _path = self.validatepath(path)
            sys_path = self.getsyspath(_path)
            _sys_path = fsencode(sys_path)
            with convert_os_errors("scandir", path, directory=True):
                for entry_name in os.listdir(sys_path):
                    _entry_name = fsdecode(entry_name)
                    entry_path = os.path.join(sys_path, _entry_name)
                    stat_result = os.stat(fsencode(entry_path))
                    info = {
                        "basic": {
                            "name": _entry_name,
                            "is_dir": stat.S_ISDIR(stat_result.st_mode),
                        }
                    }  # type: Dict[Text, Dict[Text, Any]]
                    if "details" in namespaces:
                        info["details"] = self._make_details_from_stat(stat_result)
                    if "stat" in namespaces:
                        info["stat"] = {
                            k: getattr(stat_result, k)
                            for k in dir(stat_result)
                            if k.startswith("st_")
                        }
                    if "lstat" in namespaces:
                        lstat_result = os.lstat(entry_path)
                        info["lstat"] = {
                            k: getattr(lstat_result, k)
                            for k in dir(lstat_result)
                            if k.startswith("st_")
                        }
                    if "link" in namespaces:
                        info["link"] = self._make_link_info(
                            os.path.join(sys_path, entry_name)
                        )
                    if "access" in namespaces:
                        info["access"] = self._make_access_from_stat(stat_result)

                    yield Info(info)

    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    # --- Miscellaneous --------------------------------------

    def getsyspath(self, path):
        # type: (Text) -> Text
        sys_path = os.path.join(self._root_path, path.lstrip("/").replace("/", os.sep))
        return sys_path

    def geturl(self, path, purpose="download"):
        # type: (Text, Text) -> Text
        if purpose != "download":
            raise NoURL(path, purpose)
        return "file://" + self.getsyspath(path)

    def gettype(self, path):
        # type: (Text) -> ResourceType
        self.check()
        sys_path = self._to_sys_path(path)
        with convert_os_errors("gettype", path):
            stat = os.stat(sys_path)
        resource_type = self._get_type_from_stat(stat)
        return resource_type

    def islink(self, path):
        # type: (Text) -> bool
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        with convert_os_errors("islink", path):
            return os.path.islink(sys_path)

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
        _mode = Mode(mode)
        validate_open_mode(mode)
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        with convert_os_errors("open", path):
            if six.PY2 and _mode.exclusive:
                sys_path = os.open(sys_path, os.O_RDWR | os.O_CREAT | os.O_EXCL)
            _encoding = encoding or "utf-8"
            return io.open(
                sys_path,
                mode=_mode.to_platform(),
                buffering=buffering,
                encoding=None if _mode.binary else _encoding,
                errors=errors,
                newline=None if _mode.binary else newline,
                **options
            )

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        self.check()
        _path = self.validatepath(path)
        sys_path = self._to_sys_path(_path)
        if not os.path.exists(sys_path):
            raise errors.ResourceNotFound(path)
        if "details" in info:
            details = info["details"]
            if "accessed" in details or "modified" in details:
                _accessed = typing.cast(int, details.get("accessed"))
                _modified = typing.cast(int, details.get("modified", _accessed))
                accessed = int(_modified if _accessed is None else _accessed)
                modified = int(_modified)
                if accessed is not None or modified is not None:
                    with convert_os_errors("setinfo", path):
                        os.utime(sys_path, (accessed, modified))
