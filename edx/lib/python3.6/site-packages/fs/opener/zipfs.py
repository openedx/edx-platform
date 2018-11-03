# coding: utf-8
"""`ZipFS` opener definition.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import typing

from .base import Opener
from .errors import NotWriteable

if False:  # typing.TYPE_CHECKING
    from typing import Text
    from .parse import ParseResult
    from ..zipfs import ZipFS


class ZipOpener(Opener):
    """`ZipFS` opener.
    """

    protocols = ["zip"]

    def open_fs(
        self,
        fs_url,  # type: Text
        parse_result,  # type: ParseResult
        writeable,  # type: bool
        create,  # type: bool
        cwd,  # type: Text
    ):
        # type: (...) -> ZipFS
        from ..zipfs import ZipFS

        if not create and writeable:
            raise NotWriteable("Unable to open existing ZIP file for writing")
        zip_fs = ZipFS(parse_result.resource, write=create)
        return zip_fs
