"""Abstract permissions container.
"""

from __future__ import print_function
from __future__ import unicode_literals

import typing
from typing import Container, Iterable

import six

from ._typing import Text


if False:  # typing.TYPE_CHECKING
    from typing import Iterator, List, Optional, Tuple, Type, Union


def make_mode(init):
    # type: (Union[int, Iterable[Text], None]) -> int
    """Make a mode integer from an initial value.
    """
    return Permissions.get_mode(init)


class _PermProperty(object):
    """Creates simple properties to get/set permissions.
    """

    def __init__(self, name):
        # type: (Text) -> None
        self._name = name
        self.__doc__ = "Boolean for '{}' permission.".format(name)

    def __get__(self, obj, obj_type=None):
        # type: (Permissions, Optional[Type[Permissions]]) -> bool
        return self._name in obj

    def __set__(self, obj, value):
        # type: (Permissions, bool) -> None
        if value:
            obj.add(self._name)
        else:
            obj.remove(self._name)


@six.python_2_unicode_compatible
class Permissions(object):
    """An abstraction for file system permissions.

    Permissions objects store information regarding the permissions
    on a resource. It supports Linux permissions, but is generic enough
    to manage permission information from almost any filesystem.

    Arguments:
        names (list, optional): A list of permissions.
        mode (int, optional): A mode integer.
        user (str, optional): A triplet of *user* permissions, e.g.
            ``"rwx"`` or ``"r--"``
        group (str, optional): A triplet of *group* permissions, e.g.
            ``"rwx"`` or ``"r--"``
        other (str, optional): A triplet of *other* permissions, e.g.
            ``"rwx"`` or ``"r--"``
        sticky (bool, optional): A boolean for the *sticky* bit.
        setuid (bool, optional): A boolean for the *setuid* bit.
        setguid (bool, optional): A boolean for the *setguid* bit.

    Example:
        >>> from fs.permissions import Permissions
        >>> p = Permissions(user='rwx', group='rw-', other='r--')
        >>> print(p)
        rwxrw-r--
        >>> p.mode
        500
        >>> oct(p.mode)
        '0764'

    """

    _LINUX_PERMS = [
        ("setuid", 2048),
        ("setguid", 1024),
        ("sticky", 512),
        ("u_r", 256),
        ("u_w", 128),
        ("u_x", 64),
        ("g_r", 32),
        ("g_w", 16),
        ("g_x", 8),
        ("o_r", 4),
        ("o_w", 2),
        ("o_x", 1),
    ]  # type: List[Tuple[Text, int]]
    _LINUX_PERMS_NAMES = [_name for _name, _mask in _LINUX_PERMS]  # type: List[Text]

    def __init__(
        self,
        names=None,  # type: Optional[Iterable[Text]]
        mode=None,  # type: Optional[int]
        user=None,  # type: Optional[Text]
        group=None,  # type: Optional[Text]
        other=None,  # type: Optional[Text]
        sticky=None,  # type: Optional[bool]
        setuid=None,  # type: Optional[bool]
        setguid=None,  # type: Optional[bool]
    ):
        # type: (...) -> None
        if names is not None:
            self._perms = set(names)
        elif mode is not None:
            self._perms = {name for name, mask in self._LINUX_PERMS if mode & mask}
        else:
            perms = self._perms = set()
            perms.update("u_" + p for p in user or "" if p != "-")
            perms.update("g_" + p for p in group or "" if p != "-")
            perms.update("o_" + p for p in other or "" if p != "-")

        if sticky:
            self._perms.add("sticky")
        if setuid:
            self._perms.add("setuid")
        if setguid:
            self._perms.add("setguid")

    def __repr__(self):
        # type: () -> Text
        if not self._perms.issubset(self._LINUX_PERMS_NAMES):
            _perms_str = ", ".join("'{}'".format(p) for p in sorted(self._perms))
            return "Permissions(names=[{}])".format(_perms_str)

        def _check(perm, name):
            # type: (Text, Text) -> Text
            return name if perm in self._perms else ""

        user = "".join((_check("u_r", "r"), _check("u_w", "w"), _check("u_x", "x")))
        group = "".join((_check("g_r", "r"), _check("g_w", "w"), _check("g_x", "x")))
        other = "".join((_check("o_r", "r"), _check("o_w", "w"), _check("o_x", "x")))
        args = []
        _fmt = "user='{}', group='{}', other='{}'"
        basic = _fmt.format(user, group, other)
        args.append(basic)
        if self.sticky:
            args.append("sticky=True")
        if self.setuid:
            args.append("setuid=True")
        if self.setuid:
            args.append("setguid=True")
        return "Permissions({})".format(", ".join(args))

    def __str__(self):
        # type: () -> Text
        return self.as_str()

    def __iter__(self):
        # type: () -> Iterator[Text]
        return iter(self._perms)

    def __contains__(self, permission):
        # type: (object) -> bool
        return permission in self._perms

    def __eq__(self, other):
        # type: (object) -> bool
        if isinstance(other, Permissions):
            names = other.dump()  # type: object
        else:
            names = other
        return self.dump() == names

    def __ne__(self, other):
        # type: (object) -> bool
        return not self.__eq__(other)

    @classmethod
    def parse(cls, ls):
        # type: (Text) -> Permissions
        """Parse permissions in Linux notation.
        """
        user = ls[:3]
        group = ls[3:6]
        other = ls[6:9]
        return cls(user=user, group=group, other=other)

    @classmethod
    def load(cls, permissions):
        # type: (List[Text]) -> Permissions
        """Load a serialized permissions object.
        """
        return cls(names=permissions)

    @classmethod
    def create(cls, init=None):
        # type: (Union[int, Iterable[Text], None]) -> Permissions
        """Create a permissions object from an initial value.

        Arguments:
            init (int or list, optional): May be None to use `0o777`
                permissions, a mode integer, or a list of permission names.

        Returns:
            int: mode integer that may be used for instance by `os.makedir`.

        Example:
            >>> Permissions.create(None)
            Permissions(user='rwx', group='rwx', other='rwx')
            >>> Permissions.create(0o700)
            Permissions(user='rwx', group='', other='')
            >>> Permissions.create(['u_r', 'u_w', 'u_x'])
            Permissions(user='rwx', group='', other='')

        """
        if init is None:
            return cls(mode=0o777)
        if isinstance(init, cls):
            return init
        if isinstance(init, int):
            return cls(mode=init)
        if isinstance(init, list):
            return cls(names=init)
        raise ValueError("permissions is invalid")

    @classmethod
    def get_mode(cls, init):
        # type: (Union[int, Iterable[Text], None]) -> int
        """Convert an initial value to a mode integer.
        """
        return cls.create(init).mode

    def copy(self):
        # type: () -> Permissions
        """Make a copy of this permissions object.
        """
        return Permissions(names=list(self._perms))

    def dump(self):
        # type: () -> List[Text]
        """Get a list suitable for serialization.
        """
        return sorted(self._perms)

    def as_str(self):
        # type: () -> Text
        """Get a Linux-style string representation of permissions.
        """
        perms = [
            c if name in self._perms else "-"
            for name, c in zip(self._LINUX_PERMS_NAMES[-9:], "rwxrwxrwx")
        ]
        if "setuid" in self._perms:
            perms[2] = "s" if "u_x" in self._perms else "S"
        if "setguid" in self._perms:
            perms[5] = "s" if "g_x" in self._perms else "S"
        if "sticky" in self._perms:
            perms[8] = "t" if "o_x" in self._perms else "T"

        perm_str = "".join(perms)
        return perm_str

    @property
    def mode(self):
        # type: () -> int
        """`int`: mode integer.
        """
        mode = 0
        for name, mask in self._LINUX_PERMS:
            if name in self._perms:
                mode |= mask
        return mode

    @mode.setter
    def mode(self, mode):
        # type: (int) -> None
        self._perms = {name for name, mask in self._LINUX_PERMS if mode & mask}

    u_r = _PermProperty("u_r")
    u_w = _PermProperty("u_w")
    u_x = _PermProperty("u_x")

    g_r = _PermProperty("g_r")
    g_w = _PermProperty("g_w")
    g_x = _PermProperty("g_x")

    o_r = _PermProperty("o_r")
    o_w = _PermProperty("o_w")
    o_x = _PermProperty("o_x")

    sticky = _PermProperty("sticky")
    setuid = _PermProperty("setuid")
    setguid = _PermProperty("setguid")

    def add(self, *permissions):
        # type: (*Text) -> None
        """Add permission(s).

        Arguments:
            *permissions (str): Permission name(s), such as ``'u_w'``
                or ``'u_x'``.

        """
        self._perms.update(permissions)

    def remove(self, *permissions):
        # type: (*Text) -> None
        """Remove permission(s).

        Arguments:
            *permissions (str): Permission name(s), such as ``'u_w'``
                or ``'u_x'``.s

        """
        self._perms.difference_update(permissions)

    def check(self, *permissions):
        # type: (*Text) -> bool
        """Check if one or more permissions are enabled.

        Arguments:
            *permissions (str): Permission name(s), such as ``'u_w'``
                or ``'u_x'``.

        Returns:
            bool: `True` if all given permissions are set.

        """
        return self._perms.issuperset(permissions)
