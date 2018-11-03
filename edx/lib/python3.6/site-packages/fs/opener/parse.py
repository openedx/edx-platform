"""Function to parse FS URLs in to their constituent parts.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re
import typing

import six
from six.moves.urllib.parse import parse_qs, unquote

from .errors import ParseError

if False:  # typing.TYPE_CHECKING
    from typing import Optional, Text


_ParseResult = collections.namedtuple(
    "ParseResult", ["protocol", "username", "password", "resource", "params", "path"]
)


class ParseResult(_ParseResult):
    """A named tuple containing fields of a parsed FS URL.

    Attributes:
        protocol (str): The protocol part of the url, e.g. ``osfs``
            or ``ftp``.
        username (str, optional): A username, or `None`.
        password (str, optional): A password, or `None`.
        resource (str): A *resource*, typically a domain and path, e.g.
            ``ftp.example.org/dir``.
        params (dict): A dictionary of parameters extracted from the
            query string.
        path (str, optional): A path within the filesystem, or `None`.

    """


_RE_FS_URL = re.compile(
    r"""
^
(.*?)
:\/\/

(?:
(?:(.*?)@(.*?))
|(.*?)
)

(?:
!(.*?)$
)*$
""",
    re.VERBOSE,
)


def parse_fs_url(fs_url):
    # type: (Text) -> ParseResult
    """Parse a Filesystem URL and return a `ParseResult`.

    Arguments:
        fs_url (str): A filesystem URL.

    Returns:
        ~fs.opener.parse.ParseResult: a parse result instance.

    Raises:
        ~fs.errors.ParseError: if the FS URL is not valid.

    """
    match = _RE_FS_URL.match(fs_url)
    if match is None:
        raise ParseError("{!r} is not a fs2 url".format(fs_url))

    fs_name, credentials, url1, url2, path = match.groups()
    if not credentials:
        username = None  # type: Optional[Text]
        password = None  # type: Optional[Text]
        url = url2
    else:
        username, _, password = credentials.partition(":")
        username = unquote(username)
        password = unquote(password)
        url = url1
    url, has_qs, qs = url.partition("?")
    resource = unquote(url)
    if has_qs:
        _params = parse_qs(qs, keep_blank_values=True)
        params = {k: unquote(v[0]) for k, v in six.iteritems(_params)}
    else:
        params = {}
    return ParseResult(fs_name, username, password, resource, params, path)
