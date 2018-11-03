"""Manage filesystems in temporary locations.

A temporary filesytem is stored in a location defined by your OS
(``/tmp`` on linux). The contents are deleted when the filesystem
is closed.

A `TempFS` is a good way of preparing a directory structure in advance,
that you can later copy. It can also be used as a temporary data store.

"""

from __future__ import print_function
from __future__ import unicode_literals

import shutil
import tempfile
import typing

import six

from . import errors
from .osfs import OSFS

if False:  # typing.TYPE_CHECKING
    from typing import Optional, Text


@six.python_2_unicode_compatible
class TempFS(OSFS):
    """A temporary filesystem on the OS.

    Arguments:
        identifier (str): A string to distinguish the directory within
            the OS temp location, used as part of the directory name.
        temp_dir (str, optional): An OS path to your temp directory
            (leave as `None` to auto-detect)
        auto_clean (bool): If `True` (the default), the directory
            contents will be wiped on close.
        ignore_clean_errors (bool): If `True` (the default), any errors
            in the clean process will be suppressed. If `False`, they
            will be raised.

    """

    def __init__(
        self,
        identifier="__tempfs__",  # type: Text
        temp_dir=None,  # type: Optional[Text]
        auto_clean=True,  # type: bool
        ignore_clean_errors=True,  # type: bool
    ):
        # type: (...) -> None
        self.identifier = identifier
        self._auto_clean = auto_clean
        self._ignore_clean_errors = ignore_clean_errors
        self._cleaned = False

        self.identifier = identifier.replace("/", "-")

        self._temp_dir = tempfile.mkdtemp(identifier or "fsTempFS", dir=temp_dir)
        super(TempFS, self).__init__(self._temp_dir)

    def __repr__(self):
        # type: () -> Text
        return "TempFS()"

    def __str__(self):
        # type: () -> Text
        return "<tempfs '{}'>".format(self._temp_dir)

    def close(self):
        # type: () -> None
        if self._auto_clean:
            self.clean()
        super(TempFS, self).close()

    def clean(self):
        # type: () -> None
        """Clean (delete) temporary files created by this filesystem.
        """
        if self._cleaned:
            return

        try:
            shutil.rmtree(self._temp_dir)
        except Exception as error:
            if not self._ignore_clean_errors:
                raise errors.OperationFailed(
                    msg="failed to remove temporary directory", exc=error
                )
        self._cleaned = True
