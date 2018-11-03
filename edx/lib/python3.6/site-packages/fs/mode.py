"""Abstract I/O mode container.

Mode strings are used in in `~fs.base.FS.open` and
`~fs.base.FS.openbin`.

"""

from __future__ import print_function
from __future__ import unicode_literals

import typing

import six

from ._typing import Text


if False:  # typing.TYPE_CHECKING
    from typing import Container, FrozenSet, Set, Union


__all__ = ["Mode", "check_readable", "check_writable", "validate_openbin_mode"]


# https://docs.python.org/3/library/functions.html#open
@six.python_2_unicode_compatible
class Mode(typing.Container[Text]):
    """An abstraction for I/O modes.

    A mode object provides properties that can be used to interrogate the
    `mode strings <https://docs.python.org/3/library/functions.html#open>`_
    used when opening files.

    Arguments:
        mode (str): A *mode* string, as used by `io.open`.

    Raises:
        ValueError: If the mode string is invalid.

    Example:
        >>> mode = Mode('rb')
        >>> mode.reading
        True
        >>> mode.writing
        False
        >>> mode.binary
        True
        >>> mode.text
        False

    """

    def __init__(self, mode):
        # type: (Text) -> None
        self._mode = mode
        self.validate()

    def __repr__(self):
        # type: () -> Text
        return "Mode({!r})".format(self._mode)

    def __str__(self):
        # type: () -> Text
        return self._mode

    def __contains__(self, character):
        # type: (object) -> bool
        """Check if a mode contains a given character.
        """
        return character in self._mode

    def to_platform(self):
        # type: () -> Text
        """Get a mode string for the current platform.

        Currently, this just removes the 'x' on PY2 because PY2 doesn't
        support exclusive mode.

        """
        return self._mode.replace("x", "w") if six.PY2 else self._mode

    def to_platform_bin(self):
        # type: () -> Text
        """Get a *binary* mode string for the current platform.

        Currently, this just removes the 'x' on PY2 because PY2 doesn't
        support exclusive mode.

        """
        _mode = self.to_platform().replace("t", "")
        return _mode if "b" in _mode else _mode + "b"

    def validate(self, _valid_chars=frozenset("rwxtab+")):
        # type: (Union[Set[Text], FrozenSet[Text]]) -> None
        """Validate the mode string.

        Raises:
            ValueError: if the mode contains invalid chars.

        """
        mode = self._mode
        if not mode:
            raise ValueError("mode must not be empty")
        if not _valid_chars.issuperset(mode):
            raise ValueError("mode '{}' contains invalid characters".format(mode))
        if mode[0] not in "rwxa":
            raise ValueError("mode must start with 'r', 'w', 'x', or 'a'")
        if "t" in mode and "b" in mode:
            raise ValueError("mode can't be binary ('b') and text ('t')")

    def validate_bin(self):
        # type: () -> None
        """Validate a mode for opening a binary file.

        Raises:
            ValueError: if the mode contains invalid chars.

        """
        self.validate()
        if "t" in self:
            raise ValueError("mode must be binary")

    @property
    def create(self):
        # type: () -> bool
        """`bool`: `True` if the mode would create a file.
        """
        return "a" in self or "w" in self or "x" in self

    @property
    def reading(self):
        # type: () -> bool
        """`bool`: `True` if the mode permits reading.
        """
        return "r" in self or "+" in self

    @property
    def writing(self):
        # type: () -> bool
        """`bool`: `True` if the mode permits writing.
        """
        return "w" in self or "a" in self or "+" in self or "x" in self

    @property
    def appending(self):
        # type: () -> bool
        """`bool`: `True` if the mode permits appending.
        """
        return "a" in self

    @property
    def updating(self):
        # type: () -> bool
        """`bool`: `True` if the mode permits both reading and writing.
        """
        return "+" in self

    @property
    def truncate(self):
        # type: () -> bool
        """`bool`: `True` if the mode would truncate an existing file.
        """
        return "w" in self or "x" in self

    @property
    def exclusive(self):
        # type: () -> bool
        """`bool`: `True` if the mode require exclusive creation.
        """
        return "x" in self

    @property
    def binary(self):
        # type: () -> bool
        """`bool`: `True` if a mode specifies binary.
        """
        return "b" in self

    @property
    def text(self):
        # type: () -> bool
        """`bool`: `True` if a mode specifies text.
        """
        return "t" in self or "b" not in self


def check_readable(mode):
    # type: (Text) -> bool
    """Check a mode string allows reading.

    Arguments:
        mode (str): A mode string, e.g. ``"rt"``

    Returns:
        bool: `True` if the mode allows reading.

    """
    return Mode(mode).reading


def check_writable(mode):
    # type: (Text) -> bool
    """Check a mode string allows writing.

    Arguments:
        mode (str): A mode string, e.g. ``"wt"``

    Returns:
        bool: `True` if the mode allows writing.

    """
    return Mode(mode).writing


def validate_open_mode(mode):
    # type: (Text) -> None
    """Check ``mode`` parameter of `~fs.base.FS.open` is valid.

    Arguments:
        mode (str): Mode parameter.

    Raises:
        `ValueError` if mode is not valid.

    """
    Mode(mode)


def validate_openbin_mode(mode, _valid_chars=frozenset("rwxab+")):
    # type: (Text, Union[Set[Text], FrozenSet[Text]]) -> None
    """Check ``mode`` parameter of `~fs.base.FS.openbin` is valid.

    Arguments:
        mode (str): Mode parameter.

    Raises:
        `ValueError` if mode is not valid.

    """
    if "t" in mode:
        raise ValueError("text mode not valid in openbin")
    if not mode:
        raise ValueError("mode must not be empty")
    if mode[0] not in "rwxa":
        raise ValueError("mode must start with 'r', 'w', 'a' or 'x'")
    if not _valid_chars.issuperset(mode):
        raise ValueError("mode '{}' contains invalid characters".format(mode))
