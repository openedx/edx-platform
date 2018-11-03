"""Functions to compress the contents of a filesystem.

Currently zip and tar are supported, using the `zipfile` and
`tarfile` modules from the standard library.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time
import tarfile
import typing
import zipfile
from datetime import datetime

import six

from .enums import ResourceType
from .path import relpath
from .time import datetime_to_epoch
from .errors import NoSysPath, MissingInfoNamespace
from .walk import Walker

if False:  # typing.TYPE_CHECKING
    from typing import BinaryIO, Optional, Text, Tuple, Type, Union
    from .base import FS

    ZipTime = Tuple[int, int, int, int, int, int]


def write_zip(
    src_fs,  # type: FS
    file,  # type: Union[Text, BinaryIO]
    compression=zipfile.ZIP_DEFLATED,  # type: int
    encoding="utf-8",  # type: Text
    walker=None,  # type: Optional[Walker]
):
    # type: (...) -> None
    """Write the contents of a filesystem to a zip file.

    Arguments:
        src_fs (~fs.base.FS): The source filesystem to compress.
        file (str or io.IOBase): Destination file, may be a file name
            or an open file object.
        compression (int): Compression to use (one of the constants
            defined in the `zipfile` module in the stdlib). Defaults
            to `zipfile.ZIP_DEFLATED`.
        encoding (str):
             The encoding to use for filenames. The default is ``"utf-8"``,
             use ``"CP437"`` if compatibility with WinZip is desired.
        walker (~fs.walk.Walker, optional): A `Walker` instance, or `None`
            to use default walker. You can use this to specify which files
            you want to compress.

    """
    _zip = zipfile.ZipFile(file, mode="w", compression=compression, allowZip64=True)
    walker = walker or Walker()
    with _zip:
        gen_walk = walker.info(src_fs, namespaces=["details", "stat", "access"])
        for path, info in gen_walk:
            # Zip names must be relative, directory names must end
            # with a slash.
            zip_name = relpath(path + "/" if info.is_dir else path)
            if not six.PY3:
                # Python2 expects bytes filenames
                zip_name = zip_name.encode(encoding, "replace")

            if info.has_namespace("stat"):
                # If the file has a stat namespace, get the
                # zip time directory from the stat structure
                st_mtime = info.get("stat", "st_mtime", None)
                _mtime = time.localtime(st_mtime)
                zip_time = _mtime[0:6]  # type: ZipTime
            else:
                # Otherwise, use the modified time from details
                # namespace.
                mt = info.modified or datetime.utcnow()
                zip_time = (mt.year, mt.month, mt.day, mt.hour, mt.minute, mt.second)

            # NOTE(@althonos): typeshed's `zipfile.py` on declares
            #     ZipInfo.__init__ for Python < 3 ?!
            zip_info = zipfile.ZipInfo(zip_name, zip_time)  # type: ignore

            try:
                if info.permissions is not None:
                    zip_info.external_attr = info.permissions.mode << 16
            except MissingInfoNamespace:
                pass

            if info.is_dir:
                zip_info.external_attr |= 0x10
                # This is how to record directories with zipfile
                _zip.writestr(zip_info, b"")
            else:
                # Get a syspath if possible
                try:
                    sys_path = src_fs.getsyspath(path)
                except NoSysPath:
                    # Write from bytes
                    _zip.writestr(zip_info, src_fs.getbytes(path))
                else:
                    # Write from a file which is (presumably)
                    # more memory efficient
                    _zip.write(sys_path, zip_name)


def write_tar(
    src_fs,  # type: FS
    file,  # type: Union[Text, BinaryIO]
    compression=None,  # type: Optional[Text]
    encoding="utf-8",  # type: Text
    walker=None,  # type: Optional[Walker]
):
    # type: (...) -> None
    """Write the contents of a filesystem to a tar file.

    Arguments:
        file (str or io.IOBase): Destination file, may be a file
            name or an open file object.
        compression (str, optional): Compression to use, or `None`
            for a plain Tar archive without compression.
        encoding(str): The encoding to use for filenames. The
            default is ``"utf-8"``.
        walker (~fs.walk.Walker, optional): A `Walker` instance, or
            `None` to use default walker. You can use this to specify
            which files you want to compress.

    """
    type_map = {
        ResourceType.block_special_file: tarfile.BLKTYPE,
        ResourceType.character: tarfile.CHRTYPE,
        ResourceType.directory: tarfile.DIRTYPE,
        ResourceType.fifo: tarfile.FIFOTYPE,
        ResourceType.file: tarfile.REGTYPE,
        ResourceType.socket: tarfile.AREGTYPE,  # no type for socket
        ResourceType.symlink: tarfile.SYMTYPE,
        ResourceType.unknown: tarfile.AREGTYPE,  # no type for unknown
    }

    tar_attr = [("uid", "uid"), ("gid", "gid"), ("uname", "user"), ("gname", "group")]

    mode = "w:{}".format(compression or "")
    if isinstance(file, (six.text_type, six.binary_type)):
        _tar = tarfile.open(file, mode=mode)
    else:
        _tar = tarfile.open(fileobj=file, mode=mode)

    current_time = time.time()
    walker = walker or Walker()
    with _tar:
        gen_walk = walker.info(src_fs, namespaces=["details", "stat", "access"])
        for path, info in gen_walk:
            # Tar names must be relative
            tar_name = relpath(path)
            if not six.PY3:
                # Python2 expects bytes filenames
                tar_name = tar_name.encode(encoding, "replace")

            tar_info = tarfile.TarInfo(tar_name)

            if info.has_namespace("stat"):
                mtime = info.get("stat", "st_mtime", current_time)
            else:
                mtime = info.modified or current_time

            if isinstance(mtime, datetime):
                mtime = datetime_to_epoch(mtime)
            if isinstance(mtime, float):
                mtime = int(mtime)
            tar_info.mtime = mtime

            for tarattr, infoattr in tar_attr:
                if getattr(info, infoattr, None) is not None:
                    setattr(tar_info, tarattr, getattr(info, infoattr, None))

            if info.has_namespace("access"):
                tar_info.mode = getattr(info.permissions, "mode", 0o420)

            if info.is_dir:
                tar_info.type = tarfile.DIRTYPE
                _tar.addfile(tar_info)
            else:
                tar_info.type = type_map.get(info.type, tarfile.REGTYPE)
                tar_info.size = info.size
                with src_fs.openbin(path) as bin_file:
                    _tar.addfile(tar_info, bin_file)
