# coding: utf-8
"""`OSFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing

from .base import Opener

if False:  # typing.TYPE_CHECKING
    from typing import Text
    from .parse import ParseResult
    from ..osfs import OSFS


class OSFSOpener(Opener):
    """`OSFS` opener.
    """

    protocols = ["file", "osfs"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> OSFS
        from ..osfs import OSFS
        from os.path import abspath, expanduser, normpath, join

        _path = abspath(join(cwd, expanduser(parse_result.resource)))
        path = normpath(_path)
        osfs = OSFS(path, create=create)
        return osfs
