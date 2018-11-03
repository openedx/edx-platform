"""Container for filesystem resource informations.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing
from typing import cast
from copy import deepcopy

import six

from .path import join
from .enums import ResourceType
from .errors import MissingInfoNamespace
from .permissions import Permissions
from .time import epoch_to_datetime
from ._typing import overload, Text

if False:  # typing.TYPE_CHECKING
    from datetime import datetime
    from typing import Any, Callable, List, Mapping, Optional, Union

    RawInfo = Mapping[Text, Mapping[Text, object]]
    ToDatetime = Callable[[int], datetime]
    T = typing.TypeVar("T")


@six.python_2_unicode_compatible
class Info(object):
    """Container for :ref:`info`.

    Resource informations are returned by the following methods:

         * `~fs.base.FS.getinfo`
         * `~fs.base.FS.scandir`
         * `~fs.base.FS.filterfir`

    Arguments:
        raw_info (dict): A dict containing resource info.
        to_datetime (callable): A callable that converts an
            epoch time to a datetime object. The default uses
            :func:`~fs.time.epoch_to_datetime`.

    """

    def __init__(self, raw_info, to_datetime=epoch_to_datetime):
        # type: (RawInfo, ToDatetime) -> None
        """Create a resource info object from a raw info dict.
        """
        self.raw = raw_info
        self._to_datetime = to_datetime
        self.namespaces = frozenset(self.raw.keys())

    def __str__(self):
        # type: () -> str
        if self.is_dir:
            return "<dir '{}'>".format(self.name)
        else:
            return "<file '{}'>".format(self.name)

    __repr__ = __str__

    def __eq__(self, other):
        # type: (object) -> bool
        return self.raw == getattr(other, "raw", None)

    @overload
    def _make_datetime(self, t):  # pragma: no cover
        # type: (None) -> None
        pass

    @overload
    def _make_datetime(self, t):  # pragma: no cover
        # type: (int) -> datetime
        pass

    def _make_datetime(self, t):
        # type: (Optional[int]) -> Optional[datetime]
        if t is not None:
            return self._to_datetime(t)
        else:
            return None

    @overload
    def get(self, namespace, key):  # pragma: no cover
        # type: (Text, Text) -> Any
        pass

    @overload
    def get(self, namespace, key, default):  # pragma: no cover
        # type: (Text, Text, T) -> Union[Any, T]
        pass

    def get(self, namespace, key, default=None):
        # type: (Text, Text, Optional[Any]) -> Optional[Any]
        """Get a raw info value.

        Arguments:
            namespace (str): A namespace identifier.
            key (str): A key within the namespace.
            default (object, optional): A default value to return
                if either the namespace or the key within the namespace
                is not found.

        Example:
            >>> info.get('access', 'permissions')
            ['u_r', 'u_w', '_wx']

        """
        try:
            return self.raw[namespace].get(key, default)  # type: ignore
        except KeyError:
            return default

    def _require_namespace(self, namespace):
        # type: (Text) -> None
        """Check if the given namespace is present in the info.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the given namespace is not
                present in the info.

        """
        if namespace not in self.raw:
            raise MissingInfoNamespace(namespace)

    def is_writeable(self, namespace, key):
        # type: (Text, Text) -> bool
        """Check if a given key in a namespace is writable.

        Uses `~fs.base.FS.setinfo`.

        Arguments:
            namespace (str): A namespace identifier.
            key (str): A key within the namespace.

        Returns:
            bool: `True` if the key can be modified, `False` otherwise.

        """
        _writeable = self.get(namespace, "_write", ())
        return key in _writeable

    def has_namespace(self, namespace):
        # type: (Text) -> bool
        """Check if the resource info contains a given namespace.

        Arguments:
            namespace (str): A namespace identifier.

        Returns:
            bool: `True` if the namespace was found, `False` otherwise.

        """
        return namespace in self.raw

    def copy(self, to_datetime=None):
        # type: (Optional[ToDatetime]) -> Info
        """Create a copy of this resource info object.
        """
        return Info(deepcopy(self.raw), to_datetime=to_datetime or self._to_datetime)

    def make_path(self, dir_path):
        # type: (Text) -> Text
        """Make a path by joining ``dir_path`` with the resource name.

        Arguments:
            dir_path (str): A path to a directory.

        Returns:
            str: A path to the resource.

        """
        return join(dir_path, self.name)

    @property
    def name(self):
        # type: () -> Text
        """`str`: the resource name.
        """
        return cast(Text, self.get("basic", "name"))

    @property
    def suffix(self):
        # type: () -> Text
        """`str`: the last component of the name (including dot), or an
        empty string if there is no suffix.

        Example:
            >>> info
            <info 'foo.py'>
            >>> info.suffix
            '.py'
        """
        name = self.get("basic", "name")
        if name.startswith(".") and name.count(".") == 1:
            return ""
        basename, dot, ext = name.rpartition(".")
        return "." + ext if dot else ""

    @property
    def suffixes(self):
        # type: () -> List[Text]
        """`List`: a list of any suffixes in the name.

        Example:
            >>> info
            <info 'foo.tar.gz'>
            >>> info.suffixes
            ['.tar', '.gz']
        """
        name = self.get("basic", "name")
        if name.startswith(".") and name.count(".") == 1:
            return []
        return ["." + suffix for suffix in name.split(".")[1:]]

    @property
    def stem(self):
        # type: () -> Text
        """`str`: the name minus any suffixes.

        Example:
            >>> info
            <info 'foo.tar.gz'>
            >>> info.stem
            'foo'

        """
        name = self.get("basic", "name")
        if name.startswith("."):
            return name
        return name.split(".")[0]

    @property
    def is_dir(self):
        # type: () -> bool
        """`bool`: `True` if the resource references a directory.
        """
        return cast(bool, self.get("basic", "is_dir"))

    @property
    def is_file(self):
        # type: () -> bool
        """`bool`: `True` if the resource references a file.
        """
        return not cast(bool, self.get("basic", "is_dir"))

    @property
    def is_link(self):
        # type: () -> bool
        """`bool`: `True` if the resource is a symlink.
        """
        self._require_namespace("link")
        return self.get("link", "target", None) is not None

    @property
    def type(self):
        # type: () -> ResourceType
        """`~fs.ResourceType`: the type of the resource.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the 'details'
                namespace is not in the Info.

        """
        self._require_namespace("details")
        return ResourceType(self.get("details", "type", 0))

    @property
    def accessed(self):
        # type: () -> Optional[datetime]
        """`~datetime.datetime`: the resource last access time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace("details")
        _time = self._make_datetime(self.get("details", "accessed"))
        return _time

    @property
    def modified(self):
        # type: () -> Optional[datetime]
        """`~datetime.datetime`: the resource last modification time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace("details")
        _time = self._make_datetime(self.get("details", "modified"))
        return _time

    @property
    def created(self):
        # type: () -> Optional[datetime]
        """`~datetime.datetime`: the resource creation time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace("details")
        _time = self._make_datetime(self.get("details", "created"))
        return _time

    @property
    def metadata_changed(self):
        # type: () -> Optional[datetime]
        """`~datetime.datetime`: the resource metadata change time, or `None`.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace("details")
        _time = self._make_datetime(self.get("details", "metadata_changed"))
        return _time

    @property
    def permissions(self):
        # type: () -> Optional[Permissions]
        """`Permissions`: the permissions of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace("access")
        _perm_names = self.get("access", "permissions")
        if _perm_names is None:
            return None
        permissions = Permissions(_perm_names)
        return permissions

    @property
    def size(self):
        # type: () -> int
        """`int`: the size of the resource, in bytes.

        Requires the ``"details"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"details"``
                namespace is not in the Info.

        """
        self._require_namespace("details")
        return cast(int, self.get("details", "size"))

    @property
    def user(self):
        # type: () -> Optional[Text]
        """`str`: the owner of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace("access")
        return self.get("access", "user")

    @property
    def uid(self):
        # type: () -> Optional[int]
        """`int`: the user id of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace("access")
        return self.get("access", "uid")

    @property
    def group(self):
        # type: () -> Optional[Text]
        """`str`: the group of the resource owner, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace("access")
        return self.get("access", "group")

    @property
    def gid(self):
        # type: () -> Optional[int]
        """`int`: the group id of the resource, or `None`.

        Requires the ``"access"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"access"``
                namespace is not in the Info.

        """
        self._require_namespace("access")
        return self.get("access", "gid")

    @property
    def target(self):  # noqa: D402
        # type: () -> Optional[Text]
        """`str`: the link target (if resource is a symlink), or `None`.

        Requires the ``"link"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"link"``
                namespace is not in the Info.

        """
        self._require_namespace("link")
        return self.get("link", "target")
