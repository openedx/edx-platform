# coding: utf-8
"""`MemoryFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing

from .base import Opener

if False:  # typing.TYPE_CHECKING
    from typing import Text
    from .parse import ParseResult
    from ..memoryfs import MemoryFS


class MemOpener(Opener):
    """`MemoryFS` opener.
    """

    protocols = ["mem"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> MemoryFS
        from ..memoryfs import MemoryFS

        mem_fs = MemoryFS()
        return mem_fs
