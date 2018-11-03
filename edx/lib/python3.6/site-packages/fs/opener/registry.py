# coding: utf-8
"""`Registry` class mapping protocols and FS URLs to their `Opener`.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import typing

import six
import pkg_resources

from .base import Opener
from .errors import UnsupportedProtocol, EntryPointError
from .parse import parse_fs_url

if False:  # typing.TYPE_CHECKING
    from typing import Iterator, List, Text, Tuple, Union
    from ..base import FS


class Registry(object):
    """A registry for `Opener` instances.
    """

    def __init__(self, default_opener="osfs"):
        # type: (Text) -> None
        """Create a registry object.

        Arguments:
            default_opener (str, optional): The protocol to use, if one
                is not supplied. The default is to use 'osfs', so that the
                FS URL is treated as a system path if no protocol is given.

        """
        self.default_opener = default_opener
        self._protocols = None  # type: Union[None, List[Text]]

    def __repr__(self):
        # type: () -> Text
        return "<fs-registry {!r}>".format(self.protocols)

    @property
    def protocols(self):
        # type: () -> List[Text]
        """`list`: the list of supported protocols.
        """
        if self._protocols is None:
            self._protocols = [
                entry_point.name
                for entry_point in pkg_resources.iter_entry_points("fs.opener")
            ]
        return self._protocols

    def get_opener(self, protocol):
        # type: (Text) -> Opener
        """Get the opener class associated to a given protocol.

        Arguments:
            protocol (str): A filesystem protocol.

        Returns:
            Opener: an opener instance.

        Raises:
            ~fs.opener.errors.UnsupportedProtocol: If no opener
                could be found for the given protocol.
            EntryPointLoadingError: If the returned entry point
                is not an `Opener` subclass or could not be loaded
                successfully.

        """
        protocol = protocol or self.default_opener
        entry_point = next(pkg_resources.iter_entry_points("fs.opener", protocol), None)

        if entry_point is None:
            raise UnsupportedProtocol("protocol '{}' is not supported".format(protocol))

        try:
            opener = entry_point.load()
        except Exception as exception:
            six.raise_from(
                EntryPointError("could not load entry point; {}".format(exception)),
                exception,
            )
        else:
            if not issubclass(opener, Opener):
                raise EntryPointError("entry point did not return an opener")

        try:
            opener_instance = opener()
        except Exception as exception:
            six.raise_from(
                EntryPointError("could not instantiate opener; {}".format(exception)),
                exception,
            )

        return opener_instance

    def open(
        self,
        fs_url,  # type: Text
        writeable=True,  # type: bool
        create=False,  # type: bool
        cwd=".",  # type: Text
        default_protocol="osfs",  # type: Text
    ):
        # type: (...) -> Tuple[FS, Text]
        """Open a filesystem from a FS URL.

        Returns a tuple of a filesystem object and a path. If there is
        no path in the FS URL, the path value will be `None`.

        Arguments:
            fs_url (str): A filesystem URL.
            writeable (bool, optional): `True` if the filesystem must be
                writeable.
            create (bool, optional): `True` if the filesystem should be
                created if it does not exist.
            cwd (str): The current working directory.

        Returns:
            (FS, str): a tuple of ``(<filesystem>, <path from url>)``

        """
        if "://" not in fs_url:
            # URL may just be a path
            fs_url = "{}://{}".format(default_protocol, fs_url)

        parse_result = parse_fs_url(fs_url)
        protocol = parse_result.protocol
        open_path = parse_result.path

        opener = self.get_opener(protocol)

        open_fs = opener.open_fs(fs_url, parse_result, writeable, create, cwd)
        return open_fs, open_path

    def open_fs(
        self,
        fs_url,  # type: Text
        writeable=False,  # type: bool
        create=False,  # type: bool
        cwd=".",  # type: Text
        default_protocol="osfs",  # type: Text
    ):
        # type: (...) -> FS
        """Open a filesystem from a FS URL (ignoring the path component).

        Arguments:
            fs_url (str): A filesystem URL.
            writeable (bool, optional): `True` if the filesystem must
                be writeable.
            create (bool, optional): `True` if the filesystem should be
                created if it does not exist.
            cwd (str): The current working directory (generally only
                relevant for OS filesystems).
            default_protocol (str): The protocol to use if one is not
                supplied in the FS URL (defaults to ``"osfs"``).

        Returns:
            ~fs.base.FS: A filesystem instance.

        """
        from ..base import FS

        if isinstance(fs_url, FS):
            _fs = fs_url
        else:
            _fs, _path = self.open(
                fs_url,
                writeable=writeable,
                create=create,
                cwd=cwd,
                default_protocol=default_protocol,
            )
        return _fs

    @contextlib.contextmanager
    def manage_fs(
        self,
        fs_url,  # type: Union[FS, Text]
        create=False,  # type: bool
        writeable=False,  # type: bool
        cwd=".",  # type: Text
    ):
        # type: (...) -> Iterator[FS]
        """Get a context manager to open and close a filesystem.

        Arguments:
            fs_url (FS or str): A filesystem instance or a FS URL.
            create (bool, optional): If `True`, then create the filesystem if
                it doesn't already exist.
            writeable (bool, optional): If `True`, then the filesystem
                must be writeable.
            cwd (str): The current working directory, if opening a
                `~fs.osfs.OSFS`.

        Sometimes it is convenient to be able to pass either a FS object
        *or* an FS URL to a function. This context manager handles the
        required logic for that.

        Example:
            >>> def print_ls(list_fs):
            ...     '''List a directory.'''
            ...     with manage_fs(list_fs) as fs:
            ...         print(' '.join(fs.listdir()))

            This function may be used in two ways. You may either pass
            a ``str``, as follows::

                >>> print_list('zip://projects.zip')

            Or, an filesystem instance::

                >>> from fs.osfs import OSFS
                >>> projects_fs = OSFS('~/')
                >>> print_list(projects_fs)

        """
        from ..base import FS

        if isinstance(fs_url, FS):
            yield fs_url
        else:
            _fs = self.open_fs(fs_url, create=create, writeable=writeable, cwd=cwd)
            try:
                yield _fs
            except:
                raise
            finally:
                _fs.close()


registry = Registry()
