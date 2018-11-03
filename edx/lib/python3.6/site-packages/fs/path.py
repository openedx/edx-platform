"""Useful functions for working with PyFilesystem paths.

This is broadly similar to the standard `os.path` module but works
with paths in the canonical format expected by all FS objects (that is,
separated by forward slashes and with an optional leading slash).

See :ref:`paths` for an explanation of PyFilesystem paths.

"""

from __future__ import print_function
from __future__ import unicode_literals

import re
import typing

from .errors import IllegalBackReference

if False:  # typing.TYPE_CHECKING
    from typing import List, Text, Tuple


__all__ = [
    "abspath",
    "basename",
    "combine",
    "dirname",
    "forcedir",
    "frombase",
    "isabs",
    "isbase",
    "isdotfile",
    "isparent",
    "issamedir",
    "iswildcard",
    "iteratepath",
    "join",
    "normpath",
    "parts",
    "recursepath",
    "relativefrom",
    "relpath",
    "split",
    "splitext",
]

_requires_normalization = re.compile(r"(^|/)\.\.?($|/)|//", re.UNICODE).search


def normpath(path):
    # type: (Text) -> Text
    """Normalize a path.

    This function simplifies a path by collapsing back-references
    and removing duplicated separators.

    Arguments:
        path (str): Path to normalize.

    Returns:
        str: A valid FS path.

    Example:
        >>> normpath("/foo//bar/frob/../baz")
        '/foo/bar/baz'
        >>> normpath("foo/../../bar")
        Traceback (most recent call last)
            ...
        IllegalBackReference: Too many backrefs in 'foo/../../bar'

    """
    if path in "/":
        return path

    # An early out if there is no need to normalize this path
    if not _requires_normalization(path):
        return path.rstrip("/")

    prefix = "/" if path.startswith("/") else ""
    components = []  # type: List[Text]
    try:
        for component in path.split("/"):
            if component in "..":  # True for '..', '.', and ''
                if component == "..":
                    components.pop()
            else:
                components.append(component)
    except IndexError:
        raise IllegalBackReference("Too many backrefs in '{}'".format(path))
    return prefix + "/".join(components)


def iteratepath(path):
    # type: (Text) -> List[Text]
    """Iterate over the individual components of a path.

    Arguments:
        path (str): Path to iterate over.

    Returns:
        list: A list of path components.

    Example:
        >>> iteratepath('/foo/bar/baz')
        ['foo', 'bar', 'baz']

    """
    path = relpath(normpath(path))
    if not path:
        return []
    return path.split("/")


def recursepath(path, reverse=False):
    # type: (Text, bool) -> List[Text]
    """Get intermediate paths from the root to the given path.

    Arguments:
        path (str): A PyFilesystem path
        reverse (bool): Reverses the order of the paths
            (default `False`).

    Returns:
        list: A list of paths.

    Example:
        >>> recursepath('a/b/c')
        ['/', '/a', '/a/b', '/a/b/c']

    """
    if path in "/":
        return ["/"]

    path = abspath(normpath(path)) + "/"

    paths = ["/"]
    find = path.find
    append = paths.append
    pos = 1
    len_path = len(path)

    while pos < len_path:
        pos = find("/", pos)
        append(path[:pos])
        pos += 1

    if reverse:
        return paths[::-1]
    return paths


def isabs(path):
    # type: (Text) -> bool
    """Check if a path is an absolute path.

    Arguments:
        path (str): A PyFilesytem path.

    Returns:
        bool: `True` if the path is absolute (starts with a ``'/'``).

    """
    # Somewhat trivial, but helps to make code self-documenting
    return path.startswith("/")


def abspath(path):
    # type: (Text) -> Text
    """Convert the given path to an absolute path.

    Since FS objects have no concept of a *current directory*, this
    simply adds a leading ``/`` character if the path doesn't already
    have one.

    Arguments:
        path (str): A PyFilesytem path.

    Returns:
        str: An absolute path.

    """
    if not path.startswith("/"):
        return "/" + path
    return path


def relpath(path):
    # type: (Text) -> Text
    """Convert the given path to a relative path.

    This is the inverse of `abspath`, stripping a leading ``'/'`` from
    the path if it is present.

    Arguments:
        path (str): A path to adjust.

    Returns:
        str: A relative path.

    Example:
        >>> relpath('/a/b')
        'a/b'

    """
    return path.lstrip("/")


def join(*paths):
    # type: (*Text) -> Text
    """Join any number of paths together.

    Arguments:
        *paths (str): Paths to join, given as positional arguments.

    Returns:
        str: The joined path.

    Example:
        >>> join('foo', 'bar', 'baz')
        'foo/bar/baz'
        >>> join('foo/bar', '../baz')
        'foo/baz'
        >>> join('foo/bar', '/baz')
        '/baz'

    """
    absolute = False
    relpaths = []  # type: List[Text]
    for p in paths:
        if p:
            if p[0] == "/":
                del relpaths[:]
                absolute = True
            relpaths.append(p)

    path = normpath("/".join(relpaths))
    if absolute:
        path = abspath(path)
    return path


def combine(path1, path2):
    # type: (Text, Text) -> Text
    """Join two paths together.

    This is faster than :func:`~fs.path.join`, but only works when the
    second path is relative, and there are no back references in either
    path.

    Arguments:
        path1 (str): A PyFilesytem path.
        path2 (str): A PyFilesytem path.

    Returns:
        str: The joint path.

    Example:
        >>> combine("foo/bar", "baz")
        'foo/bar/baz'

    """
    if not path1:
        return path2.lstrip()
    return "{}/{}".format(path1.rstrip("/"), path2.lstrip("/"))


def parts(path):
    # type: (Text) -> List[Text]
    """Split a path in to its component parts.

    Arguments:
        path (str): Path to split in to parts.

    Returns:
        list: List of components

    Example:
        >>> parts('/foo/bar/baz')
        ['/', 'foo', 'bar', 'baz']

    """
    _path = normpath(path)
    components = _path.strip("/")

    _parts = ["/" if _path.startswith("/") else "./"]
    if components:
        _parts += components.split("/")
    return _parts


def split(path):
    # type: (Text) -> Tuple[Text, Text]
    """Split a path into (head, tail) pair.

    This function splits a path into a pair (head, tail) where 'tail' is
    the last pathname component and 'head' is all preceding components.

    Arguments:
        path (str): Path to split

    Returns:
        (str, str): a tuple containing the head and the tail of the path.

    Example:
        >>> split("foo/bar")
        ('foo', 'bar')
        >>> split("foo/bar/baz")
        ('foo/bar', 'baz')
        >>> split("/foo/bar/baz")
        ('/foo/bar', 'baz')

    """
    if "/" not in path:
        return ("", path)
    split = path.rsplit("/", 1)
    return (split[0] or "/", split[1])


def splitext(path):
    # type: (Text) -> Tuple[Text, Text]
    """Split the extension from the path.

    Arguments:
        path (str): A path to split.

    Returns:
        (str, str): A tuple containing the path and the extension.

    Example:
        >>> splitext('baz.txt')
        ('baz', '.txt')
        >>> splitext('foo/bar/baz.txt')
        ('foo/bar/baz', '.txt')
        >>> splitext('foo/bar/.foo')
        ('foo/bar/.foo', '')

    """
    parent_path, pathname = split(path)
    if pathname.startswith(".") and pathname.count(".") == 1:
        return path, ""
    if "." not in pathname:
        return path, ""
    pathname, ext = pathname.rsplit(".", 1)
    path = join(parent_path, pathname)
    return path, "." + ext


def isdotfile(path):
    # type: (Text) -> bool
    """Detect if a path references a dot file.

    Arguments:
        path (str): Path to check.

    Returns:
        bool: `True` if the resource name starts with a ``'.'``.

    Example:
        >>> isdotfile('.baz')
        True
        >>> isdotfile('foo/bar/.baz')
        True
        >>> isdotfile('foo/bar.baz')
        False

    """
    return basename(path).startswith(".")


def dirname(path):
    # type: (Text) -> Text
    """Return the parent directory of a path.

    This is always equivalent to the 'head' component of the value
    returned by ``split(path)``.

    Arguments:
        path (str): A PyFilesytem path.

    Returns:
        str: the parent directory of the given path.

    Example:
        >>> dirname('foo/bar/baz')
        'foo/bar'
        >>> dirname('/foo/bar')
        '/foo'
        >>> dirname('/foo')
        '/'

    """
    return split(path)[0]


def basename(path):
    # type: (Text) -> Text
    """Return the basename of the resource referenced by a path.

    This is always equivalent to the 'tail' component of the value
    returned by split(path).

    Arguments:
        path (str): A PyFilesytem path.

    Returns:
        str: the name of the resource at the given path.

    Example:
        >>> basename('foo/bar/baz')
        'baz'
        >>> basename('foo/bar')
        'bar'
        >>> basename('foo/bar/')
        ''

    """
    return split(path)[1]


def issamedir(path1, path2):
    # type: (Text, Text) -> bool
    """Check if two paths reference a resource in the same directory.

    Arguments:
        path1 (str): A PyFilesytem path.
        path2 (str): A PyFilesytem path.

    Returns:
        bool: `True` if the two resources are in the same directory.

    Example:
        >>> issamedir("foo/bar/baz.txt", "foo/bar/spam.txt")
        True
        >>> issamedir("foo/bar/baz/txt", "spam/eggs/spam.txt")
        False

    """
    return dirname(normpath(path1)) == dirname(normpath(path2))


def isbase(path1, path2):
    # type: (Text, Text) -> bool
    """Check if ``path1`` is a base of ``path2``.

    Arguments:
        path1 (str): A PyFilesytem path.
        path2 (str): A PyFilesytem path.

    Returns:
        bool: `True` if ``path2`` starts with ``path1``

    Example:
        >>> isbase('foo/bar', 'foo/bar/baz/egg.txt')
        True

    """
    _path1 = forcedir(abspath(path1))
    _path2 = forcedir(abspath(path2))
    return _path2.startswith(_path1)  # longer one is child


def isparent(path1, path2):
    # type: (Text, Text) -> bool
    """Check if ``path1`` is a parent directory of ``path2``.

    Arguments:
        path1 (str): A PyFilesytem path.
        path2 (str): A PyFilesytem path.

    Returns:
        bool: `True` if ``path1`` is a parent directory of ``path2``

    Example:
        >>> isparent("foo/bar", "foo/bar/spam.txt")
        True
        >>> isparent("foo/bar/", "foo/bar")
        True
        >>> isparent("foo/barry", "foo/baz/bar")
        False
        >>> isparent("foo/bar/baz/", "foo/baz/bar")
        False

    """
    bits1 = path1.split("/")
    bits2 = path2.split("/")
    while bits1 and bits1[-1] == "":
        bits1.pop()
    if len(bits1) > len(bits2):
        return False
    for (bit1, bit2) in zip(bits1, bits2):
        if bit1 != bit2:
            return False
    return True


def forcedir(path):
    # type: (Text) -> Text
    """Ensure the path ends with a trailing forward slash.

    Arguments:
        path (str): A PyFilesytem path.

    Returns:
        str: The path, ending with a slash.

    Example:
        >>> forcedir("foo/bar")
        'foo/bar/'
        >>> forcedir("foo/bar/")
        'foo/bar/'
        >>> forcedir("foo/spam.txt")
        'foo/spam.txt'

    """
    if not path.endswith("/"):
        return path + "/"
    return path


def frombase(path1, path2):
    # type: (Text, Text) -> Text
    """Get the final path of ``path2`` that isn't in ``path1``.

    Arguments:
        path1 (str): A PyFilesytem path.
        path2 (str): A PyFilesytem path.

    Returns:
        str: the final part of ``path2``.

    Example:
        >>> frombase('foo/bar/', 'foo/bar/baz/egg')
        'baz/egg'

    """
    if not isparent(path1, path2):
        raise ValueError("path1 must be a prefix of path2")
    return path2[len(path1) :]


def relativefrom(base, path):
    # type: (Text, Text) -> Text
    """Return a path relative from a given base path.

    Insert backrefs as appropriate to reach the path from the base.

    Arguments:
        base (str): Path to a directory.
        path (str): Path to make relative.

    Returns:
        str: the path to ``base`` from ``path``.

    >>> relativefrom("foo/bar", "baz/index.html")
    '../../baz/index.html'

    """
    base_parts = list(iteratepath(base))
    path_parts = list(iteratepath(path))

    common = 0
    for component_a, component_b in zip(base_parts, path_parts):
        if component_a != component_b:
            break
        common += 1

    return "/".join([".."] * (len(base_parts) - common) + path_parts[common:])


_WILD_CHARS = frozenset("*?[]!{}")


def iswildcard(path):
    # type: (Text) -> bool
    """Check if a path ends with a wildcard.

    Arguments:
        path (str): A PyFilesystem path.

    Returns:
        bool: `True` if path ends with a wildcard.

    Example:
        >>> iswildcard('foo/bar/baz.*')
        True
        >>> iswildcard('foo/bar')
        False

    """
    assert path is not None
    return not _WILD_CHARS.isdisjoint(path)
