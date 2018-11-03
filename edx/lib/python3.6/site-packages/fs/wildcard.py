"""Match wildcard filenames.
"""
# Adapted from https://hg.python.org/cpython/file/2.7/Lib/fnmatch.py

from __future__ import unicode_literals, print_function

import re
import typing
from functools import partial

from .lrucache import LRUCache
from . import path

if False:  # typing.TYPE_CHECKING
    from typing import Callable, Iterable, MutableMapping, Text, Tuple, Pattern


_PATTERN_CACHE = LRUCache(1000)  # type: LRUCache[Tuple[Text, bool], Pattern]


def match(pattern, name):
    # type: (Text, Text) -> bool
    """Test whether a name matches a wildcard pattern.

    Arguments:
        pattern (str): A wildcard pattern, e.g. ``"*.py"``.
        name (str): A filename.

    Returns:
        bool: `True` if the filename matches the pattern.

    """
    try:
        re_pat = _PATTERN_CACHE[(pattern, True)]
    except KeyError:
        res = "(?ms)" + _translate(pattern) + r'\Z'
        _PATTERN_CACHE[(pattern, True)] = re_pat = re.compile(res)
    return re_pat.match(name) is not None


def imatch(pattern, name):
    # type: (Text, Text) -> bool
    """Test whether a name matches a wildcard pattern (case insensitive).

    Arguments:
        pattern (str): A wildcard pattern, e.g. ``"*.py"``.
        name (bool): A filename.

    Returns:
        bool: `True` if the filename matches the pattern.

    """
    try:
        re_pat = _PATTERN_CACHE[(pattern, False)]
    except KeyError:
        res = "(?ms)" + _translate(pattern, case_sensitive=False) + r'\Z'
        _PATTERN_CACHE[(pattern, False)] = re_pat = re.compile(res, re.IGNORECASE)
    return re_pat.match(name) is not None


def match_any(patterns, name):
    # type: (Iterable[Text], Text) -> bool
    """Test if a name matches any of a list of patterns.

    Will return `True` if ``patterns`` is an empty list.

    Arguments:
        patterns (list): A list of wildcard pattern, e.g ``["*.py",
            "*.pyc"]``
        name (str): A filename.

    Returns:
        bool: `True` if the name matches at least one of the patterns.

    """
    if not patterns:
        return True
    return any(match(pattern, name) for pattern in patterns)


def imatch_any(patterns, name):
    # type: (Iterable[Text], Text) -> bool
    """Test if a name matches any of a list of patterns (case insensitive).

    Will return `True` if ``patterns`` is an empty list.

    Arguments:
        patterns (list): A list of wildcard pattern, e.g ``["*.py",
            "*.pyc"]``
        name (str): A filename.

    Returns:
        bool: `True` if the name matches at least one of the patterns.

    """
    if not patterns:
        return True
    return any(imatch(pattern, name) for pattern in patterns)


def get_matcher(patterns, case_sensitive):
    # type: (Iterable[Text], bool) -> Callable[[Text], bool]
    """Get a callable that matches names against the given patterns.

    Arguments:
        patterns (list): A list of wildcard pattern. e.g. ``["*.py",
            "*.pyc"]``
        case_sensitive (bool): If ``True``, then the callable will be case
            sensitive, otherwise it will be case insensitive.

    Returns:
        callable: a matcher that will return `True` if the name given as
        an argument matches any of the given patterns.

    Example:
        >>> from fs import wildcard
        >>> is_python = wildcard.get_matcher(['*.py'], True)
        >>> is_python('__init__.py')
        True
        >>> is_python('foo.txt')
        False

    """
    if not patterns:
        return lambda name: True
    if case_sensitive:
        return partial(match_any, patterns)
    else:
        return partial(imatch_any, patterns)


def _translate(pattern, case_sensitive=True):
    # type: (Text, bool) -> Text
    """Translate a wildcard pattern to a regular expression.

    There is no way to quote meta-characters.

    Arguments:
        pattern (str): A wildcard pattern.
        case_sensitive (bool): Set to `False` to use a case
            insensitive regex (default `True`).

    Returns:
        str: A regex equivalent to the given pattern.

    """
    if not case_sensitive:
        pattern = pattern.lower()
    i, n = 0, len(pattern)
    res = ""
    while i < n:
        c = pattern[i]
        i = i + 1
        if c == "*":
            res = res + "[^/]*"
        elif c == "?":
            res = res + "."
        elif c == "[":
            j = i
            if j < n and pattern[j] == "!":
                j = j + 1
            if j < n and pattern[j] == "]":
                j = j + 1
            while j < n and pattern[j] != "]":
                j = j + 1
            if j >= n:
                res = res + "\\["
            else:
                stuff = pattern[i:j].replace("\\", "\\\\")
                i = j + 1
                if stuff[0] == "!":
                    stuff = "^" + stuff[1:]
                elif stuff[0] == "^":
                    stuff = "\\" + stuff
                res = "%s[%s]" % (res, stuff)
        else:
            res = res + re.escape(c)
    return res
