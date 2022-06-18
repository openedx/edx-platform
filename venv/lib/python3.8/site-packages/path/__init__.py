"""
Path Pie

Implements ``path.Path`` - An object representing a
path to a file or directory.

Example::

    from path import Path
    d = Path('/home/guido/bin')

    # Globbing
    for f in d.files('*.py'):
        f.chmod(0o755)

    # Changing the working directory:
    with Path("somewhere"):
        # cwd in now `somewhere`
        ...

    # Concatenate paths with /
    foo_txt = Path("bar") / "foo.txt"
"""

import sys
import warnings
import os
import fnmatch
import glob
import shutil
import hashlib
import errno
import tempfile
import functools
import re
import contextlib
import io
import importlib
import itertools

with contextlib.suppress(ImportError):
    import win32security

with contextlib.suppress(ImportError):
    import pwd

with contextlib.suppress(ImportError):
    import grp

from . import matchers
from . import masks
from . import classes
from .py37compat import best_realpath, lru_cache


__all__ = ['Path', 'TempDir']


LINESEPS = ['\r\n', '\r', '\n']
U_LINESEPS = LINESEPS + ['\u0085', '\u2028', '\u2029']
B_NEWLINE = re.compile('|'.join(LINESEPS).encode())
U_NEWLINE = re.compile('|'.join(U_LINESEPS))
B_NL_END = re.compile(B_NEWLINE.pattern + b'$')
U_NL_END = re.compile(U_NEWLINE.pattern + '$')


class TreeWalkWarning(Warning):
    pass


class Traversal:
    """
    Wrap a walk result to customize the traversal.

    `follow` is a function that takes an item and returns
    True if that item should be followed and False otherwise.

    For example, to avoid traversing into directories that
    begin with `.`:

    >>> traverse = Traversal(lambda dir: not dir.startswith('.'))
    >>> items = list(traverse(Path('.').walk()))

    Directories beginning with `.` will appear in the results, but
    their children will not.

    >>> dot_dir = next(item for item in items if item.isdir() and item.startswith('.'))
    >>> any(item.parent == dot_dir for item in items)
    False
    """

    def __init__(self, follow):
        self.follow = follow

    def __call__(self, walker):
        traverse = None
        while True:
            try:
                item = walker.send(traverse)
            except StopIteration:
                return
            yield item

            traverse = functools.partial(self.follow, item)


class Path(str):
    """
    Represents a filesystem path.

    For documentation on individual methods, consult their
    counterparts in :mod:`os.path`.

    Some methods are additionally included from :mod:`shutil`.
    The functions are linked directly into the class namespace
    such that they will be bound to the Path instance. For example,
    ``Path(src).copy(target)`` is equivalent to
    ``shutil.copy(src, target)``. Therefore, when referencing
    the docs for these methods, assume `src` references `self`,
    the Path instance.
    """

    module = os.path
    """ The path module to use for path operations.

    .. seealso:: :mod:`os.path`
    """

    def __init__(self, other=''):
        if other is None:
            raise TypeError("Invalid initial value for path: None")
        with contextlib.suppress(AttributeError):
            self._validate()

    @classmethod
    @lru_cache
    def using_module(cls, module):
        subclass_name = cls.__name__ + '_' + module.__name__
        bases = (cls,)
        ns = {'module': module}
        return type(subclass_name, bases, ns)

    @classes.ClassProperty
    @classmethod
    def _next_class(cls):
        """
        What class should be used to construct new instances from this class
        """
        return cls

    # --- Special Python methods.

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super(Path, self).__repr__())

    # Adding a Path and a string yields a Path.
    def __add__(self, more):
        return self._next_class(super(Path, self).__add__(more))

    def __radd__(self, other):
        return self._next_class(other.__add__(self))

    # The / operator joins Paths.
    def __div__(self, rel):
        """fp.__div__(rel) == fp / rel == fp.joinpath(rel)

        Join two path components, adding a separator character if
        needed.

        .. seealso:: :func:`os.path.join`
        """
        return self._next_class(self.module.join(self, rel))

    # Make the / operator work even when true division is enabled.
    __truediv__ = __div__

    # The / operator joins Paths the other way around
    def __rdiv__(self, rel):
        """fp.__rdiv__(rel) == rel / fp

        Join two path components, adding a separator character if
        needed.

        .. seealso:: :func:`os.path.join`
        """
        return self._next_class(self.module.join(rel, self))

    # Make the / operator work even when true division is enabled.
    __rtruediv__ = __rdiv__

    def __enter__(self):
        self._old_dir = self.getcwd()
        os.chdir(self)
        return self

    def __exit__(self, *_):
        os.chdir(self._old_dir)

    @classmethod
    def getcwd(cls):
        """Return the current working directory as a path object.

        .. seealso:: :func:`os.getcwd`
        """
        return cls(os.getcwd())

    #
    # --- Operations on Path strings.

    def abspath(self):
        """.. seealso:: :func:`os.path.abspath`"""
        return self._next_class(self.module.abspath(self))

    def normcase(self):
        """.. seealso:: :func:`os.path.normcase`"""
        return self._next_class(self.module.normcase(self))

    def normpath(self):
        """.. seealso:: :func:`os.path.normpath`"""
        return self._next_class(self.module.normpath(self))

    def realpath(self):
        """.. seealso:: :func:`os.path.realpath`"""
        realpath = best_realpath(self.module)
        return self._next_class(realpath(self))

    def expanduser(self):
        """.. seealso:: :func:`os.path.expanduser`"""
        return self._next_class(self.module.expanduser(self))

    def expandvars(self):
        """.. seealso:: :func:`os.path.expandvars`"""
        return self._next_class(self.module.expandvars(self))

    def dirname(self):
        """.. seealso:: :attr:`parent`, :func:`os.path.dirname`"""
        return self._next_class(self.module.dirname(self))

    def basename(self):
        """.. seealso:: :attr:`name`, :func:`os.path.basename`"""
        return self._next_class(self.module.basename(self))

    def expand(self):
        """Clean up a filename by calling :meth:`expandvars()`,
        :meth:`expanduser()`, and :meth:`normpath()` on it.

        This is commonly everything needed to clean up a filename
        read from a configuration file, for example.
        """
        return self.expandvars().expanduser().normpath()

    @property
    def stem(self):
        """The same as :meth:`name`, but with one file extension stripped off.

        >>> Path('/home/guido/python.tar.gz').stem
        'python.tar'
        """
        base, ext = self.module.splitext(self.name)
        return base

    @property
    def ext(self):
        """The file extension, for example ``'.py'``."""
        f, ext = self.module.splitext(self)
        return ext

    def with_suffix(self, suffix):
        """Return a new path with the file suffix changed (or added, if none)

        >>> Path('/home/guido/python.tar.gz').with_suffix(".foo")
        Path('/home/guido/python.tar.foo')

        >>> Path('python').with_suffix('.zip')
        Path('python.zip')

        >>> Path('filename.ext').with_suffix('zip')
        Traceback (most recent call last):
        ...
        ValueError: Invalid suffix 'zip'
        """
        if not suffix.startswith('.'):
            raise ValueError("Invalid suffix {suffix!r}".format(**locals()))

        return self.stripext() + suffix

    @property
    def drive(self):
        """The drive specifier, for example ``'C:'``.

        This is always empty on systems that don't use drive specifiers.
        """
        drive, r = self.module.splitdrive(self)
        return self._next_class(drive)

    parent = property(
        dirname,
        None,
        None,
        """ This path's parent directory, as a new Path object.

        For example,
        ``Path('/usr/local/lib/libpython.so').parent ==
        Path('/usr/local/lib')``

        .. seealso:: :meth:`dirname`, :func:`os.path.dirname`
        """,
    )

    name = property(
        basename,
        None,
        None,
        """ The name of this file or directory without the full path.

        For example,
        ``Path('/usr/local/lib/libpython.so').name == 'libpython.so'``

        .. seealso:: :meth:`basename`, :func:`os.path.basename`
        """,
    )

    def splitpath(self):
        """Return two-tuple of ``.parent``, ``.name``.

        .. seealso:: :attr:`parent`, :attr:`name`, :func:`os.path.split`
        """
        parent, child = self.module.split(self)
        return self._next_class(parent), child

    def splitdrive(self):
        """Return two-tuple of ``.drive`` and rest without drive.

        Split the drive specifier from this path.  If there is
        no drive specifier, :samp:`{p.drive}` is empty, so the return value
        is simply ``(Path(''), p)``.  This is always the case on Unix.

        .. seealso:: :func:`os.path.splitdrive`
        """
        drive, rel = self.module.splitdrive(self)
        return self._next_class(drive), self._next_class(rel)

    def splitext(self):
        """Return two-tuple of ``.stripext()`` and ``.ext``.

        Split the filename extension from this path and return
        the two parts.  Either part may be empty.

        The extension is everything from ``'.'`` to the end of the
        last path segment.  This has the property that if
        ``(a, b) == p.splitext()``, then ``a + b == p``.

        .. seealso:: :func:`os.path.splitext`
        """
        filename, ext = self.module.splitext(self)
        return self._next_class(filename), ext

    def stripext(self):
        """Remove one file extension from the path.

        For example, ``Path('/home/guido/python.tar.gz').stripext()``
        returns ``Path('/home/guido/python.tar')``.
        """
        return self.splitext()[0]

    @classes.multimethod
    def joinpath(cls, first, *others):
        """
        Join first to zero or more :class:`Path` components,
        adding a separator character (:samp:`{first}.module.sep`)
        if needed.  Returns a new instance of
        :samp:`{first}._next_class`.

        .. seealso:: :func:`os.path.join`
        """
        return cls._next_class(cls.module.join(first, *others))

    def splitall(self):
        r"""Return a list of the path components in this path.

        The first item in the list will be a Path.  Its value will be
        either :data:`os.curdir`, :data:`os.pardir`, empty, or the root
        directory of this path (for example, ``'/'`` or ``'C:\\'``).  The
        other items in the list will be strings.

        ``Path.joinpath(*result)`` will yield the original path.

        >>> Path('/foo/bar/baz').splitall()
        [Path('/'), 'foo', 'bar', 'baz']
        """
        return list(self._parts())

    def parts(self):
        """
        >>> Path('/foo/bar/baz').parts()
        (Path('/'), 'foo', 'bar', 'baz')
        """
        return tuple(self._parts())

    def _parts(self):
        return reversed(tuple(self._parts_iter()))

    def _parts_iter(self):
        loc = self
        while loc != os.curdir and loc != os.pardir:
            prev = loc
            loc, child = prev.splitpath()
            if loc == prev:
                break
            yield child
        yield loc

    def relpath(self, start='.'):
        """Return this path as a relative path,
        based from `start`, which defaults to the current working directory.
        """
        cwd = self._next_class(start)
        return cwd.relpathto(self)

    def relpathto(self, dest):
        """Return a relative path from `self` to `dest`.

        If there is no relative path from `self` to `dest`, for example if
        they reside on different drives in Windows, then this returns
        ``dest.abspath()``.
        """
        origin = self.abspath()
        dest = self._next_class(dest).abspath()

        orig_list = origin.normcase().splitall()
        # Don't normcase dest!  We want to preserve the case.
        dest_list = dest.splitall()

        if orig_list[0] != self.module.normcase(dest_list[0]):
            # Can't get here from there.
            return dest

        # Find the location where the two paths start to differ.
        i = 0
        for start_seg, dest_seg in zip(orig_list, dest_list):
            if start_seg != self.module.normcase(dest_seg):
                break
            i += 1

        # Now i is the point where the two paths diverge.
        # Need a certain number of "os.pardir"s to work up
        # from the origin to the point of divergence.
        segments = [os.pardir] * (len(orig_list) - i)
        # Need to add the diverging part of dest_list.
        segments += dest_list[i:]
        if len(segments) == 0:
            # If they happen to be identical, use os.curdir.
            relpath = os.curdir
        else:
            relpath = self.module.join(*segments)
        return self._next_class(relpath)

    # --- Listing, searching, walking, and matching

    def listdir(self, match=None):
        """List of items in this directory.

        Use :meth:`files` or :meth:`dirs` instead if you want a listing
        of just files or just subdirectories.

        The elements of the list are Path objects.

        With the optional `match` argument, a callable,
        only return items whose names match the given pattern.

        .. seealso:: :meth:`files`, :meth:`dirs`
        """
        match = matchers.load(match)
        return list(filter(match, (self / child for child in os.listdir(self))))

    def dirs(self, *args, **kwargs):
        """List of this directory's subdirectories.

        The elements of the list are Path objects.
        This does not walk recursively into subdirectories
        (but see :meth:`walkdirs`).

        Accepts parameters to :meth:`listdir`.
        """
        return [p for p in self.listdir(*args, **kwargs) if p.isdir()]

    def files(self, *args, **kwargs):
        """List of the files in self.

        The elements of the list are Path objects.
        This does not walk into subdirectories (see :meth:`walkfiles`).

        Accepts parameters to :meth:`listdir`.
        """

        return [p for p in self.listdir(*args, **kwargs) if p.isfile()]

    def walk(self, match=None, errors='strict'):
        """Iterator over files and subdirs, recursively.

        The iterator yields Path objects naming each child item of
        this directory and its descendants.  This requires that
        ``D.isdir()``.

        This performs a depth-first traversal of the directory tree.
        Each directory is returned just before all its children.

        The `errors=` keyword argument controls behavior when an
        error occurs.  The default is ``'strict'``, which causes an
        exception.  Other allowed values are ``'warn'`` (which
        reports the error via :func:`warnings.warn()`), and ``'ignore'``.
        `errors` may also be an arbitrary callable taking a msg parameter.
        """

        errors = Handlers._resolve(errors)
        match = matchers.load(match)

        try:
            childList = self.listdir()
        except Exception as exc:
            errors(f"Unable to list directory '{self}': {exc}")
            return

        for child in childList:
            traverse = None
            if match(child):
                traverse = yield child
            traverse = traverse or child.isdir
            try:
                do_traverse = traverse()
            except Exception as exc:
                errors(f"Unable to access '{child}': {exc}")
                continue

            if do_traverse:
                for item in child.walk(errors=errors, match=match):
                    yield item

    def walkdirs(self, *args, **kwargs):
        """Iterator over subdirs, recursively."""
        return (item for item in self.walk(*args, **kwargs) if item.isdir())

    def walkfiles(self, *args, **kwargs):
        """Iterator over files, recursively."""
        return (item for item in self.walk(*args, **kwargs) if item.isfile())

    def fnmatch(self, pattern, normcase=None):
        """Return ``True`` if `self.name` matches the given `pattern`.

        `pattern` - A filename pattern with wildcards,
            for example ``'*.py'``. If the pattern contains a `normcase`
            attribute, it is applied to the name and path prior to comparison.

        `normcase` - (optional) A function used to normalize the pattern and
            filename before matching. Defaults to normcase from
            ``self.module``, :func:`os.path.normcase`.

        .. seealso:: :func:`fnmatch.fnmatch`
        """
        default_normcase = getattr(pattern, 'normcase', self.module.normcase)
        normcase = normcase or default_normcase
        name = normcase(self.name)
        pattern = normcase(pattern)
        return fnmatch.fnmatchcase(name, pattern)

    def glob(self, pattern):
        """Return a list of Path objects that match the pattern.

        `pattern` - a path relative to this directory, with wildcards.

        For example, ``Path('/users').glob('*/bin/*')`` returns a list
        of all the files users have in their :file:`bin` directories.

        .. seealso:: :func:`glob.glob`

        .. note:: Glob is **not** recursive, even when using ``**``.
                  To do recursive globbing see :func:`walk`,
                  :func:`walkdirs` or :func:`walkfiles`.
        """
        cls = self._next_class
        return [cls(s) for s in glob.glob(self / pattern)]

    def iglob(self, pattern):
        """Return an iterator of Path objects that match the pattern.

        `pattern` - a path relative to this directory, with wildcards.

        For example, ``Path('/users').iglob('*/bin/*')`` returns an
        iterator of all the files users have in their :file:`bin`
        directories.

        .. seealso:: :func:`glob.iglob`

        .. note:: Glob is **not** recursive, even when using ``**``.
                  To do recursive globbing see :func:`walk`,
                  :func:`walkdirs` or :func:`walkfiles`.
        """
        cls = self._next_class
        return (cls(s) for s in glob.iglob(self / pattern))

    #
    # --- Reading or writing an entire file at once.

    def open(self, *args, **kwargs):
        """Open this file and return a corresponding file object.

        Keyword arguments work as in :func:`io.open`.  If the file cannot be
        opened, an :class:`OSError` is raised.
        """
        return io.open(self, *args, **kwargs)

    def bytes(self):
        """Open this file, read all bytes, return them as a string."""
        with self.open('rb') as f:
            return f.read()

    def chunks(self, size, *args, **kwargs):
        """Returns a generator yielding chunks of the file, so it can
         be read piece by piece with a simple for loop.

        Any argument you pass after `size` will be passed to :meth:`open`.

        :example:

            >>> hash = hashlib.md5()
            >>> for chunk in Path("CHANGES.rst").chunks(8192, mode='rb'):
            ...     hash.update(chunk)

         This will read the file by chunks of 8192 bytes.
        """
        with self.open(*args, **kwargs) as f:
            for chunk in iter(lambda: f.read(size) or None, None):
                yield chunk

    def write_bytes(self, bytes, append=False):
        """Open this file and write the given bytes to it.

        Default behavior is to overwrite any existing file.
        Call ``p.write_bytes(bytes, append=True)`` to append instead.
        """
        with self.open('ab' if append else 'wb') as f:
            f.write(bytes)

    def read_text(self, encoding=None, errors=None):
        r"""Open this file, read it in, return the content as a string.

        Optional parameters are passed to :meth:`open`.

        .. seealso:: :meth:`lines`
        """
        with self.open(encoding=encoding, errors=errors) as f:
            return f.read()

    def read_bytes(self):
        r"""Return the contents of this file as bytes."""
        with self.open(mode='rb') as f:
            return f.read()

    def text(self, encoding=None, errors='strict'):
        r"""Legacy function to read text.

        Converts all newline sequences to ``\n``.
        """
        warnings.warn(".text is deprecated; use read_text", DeprecationWarning)
        return U_NEWLINE.sub('\n', self.read_text(encoding, errors))

    def write_text(
        self, text, encoding=None, errors='strict', linesep=os.linesep, append=False
    ):
        r"""Write the given text to this file.

        The default behavior is to overwrite any existing file;
        to append instead, use the `append=True` keyword argument.

        There are two differences between :meth:`write_text` and
        :meth:`write_bytes`: newline handling and Unicode handling.
        See below.

        Parameters:

          `text` - str/bytes - The text to be written.

          `encoding` - str - The text encoding used.

          `errors` - str - How to handle Unicode encoding errors.
              Default is ``'strict'``.  See ``help(unicode.encode)`` for the
              options.  Ignored if `text` isn't a Unicode string.

          `linesep` - keyword argument - str/unicode - The sequence of
              characters to be used to mark end-of-line.  The default is
              :data:`os.linesep`.  Specify ``None`` to
              use newlines unmodified.

          `append` - keyword argument - bool - Specifies what to do if
              the file already exists (``True``: append to the end of it;
              ``False``: overwrite it).  The default is ``False``.


        --- Newline handling.

        ``write_text()`` converts all standard end-of-line sequences
        (``'\n'``, ``'\r'``, and ``'\r\n'``) to your platform's default
        end-of-line sequence (see :data:`os.linesep`; on Windows, for example,
        the end-of-line marker is ``'\r\n'``).

        To override the platform's default, pass the `linesep=`
        keyword argument. To preserve the newlines as-is, pass
        ``linesep=None``.

        This handling applies to Unicode text and bytes, except
        with Unicode, additional non-ASCII newlines are recognized:
        ``\x85``, ``\r\x85``, and ``\u2028``.

        --- Unicode

        If `text` isn't Unicode, then apart from newline handling, the
        bytes are written verbatim to the file.  The `encoding` and
        `errors` arguments are not used and must be omitted.

        If `text` is Unicode, it is first converted to :func:`bytes` using the
        specified `encoding` (or the default encoding if `encoding`
        isn't specified).  The `errors` argument applies only to this
        conversion.
        """
        if isinstance(text, str):
            if linesep is not None:
                text = U_NEWLINE.sub(linesep, text)
            bytes = text.encode(encoding or sys.getdefaultencoding(), errors)
        else:
            warnings.warn(
                "Writing bytes in write_text is deprecated",
                DeprecationWarning,
                stacklevel=1,
            )
            assert encoding is None
            if linesep is not None:
                text = B_NEWLINE.sub(linesep.encode(), text)
            bytes = text
        self.write_bytes(bytes, append=append)

    def lines(self, encoding=None, errors=None, retain=True):
        r"""Open this file, read all lines, return them in a list.

        Optional arguments:
            `encoding` - The Unicode encoding (or character set) of
                the file.  The default is ``None``, meaning use
                ``locale.getpreferredencoding()``.
            `errors` - How to handle Unicode errors; see
                `open <https://docs.python.org/3/library/functions.html#open>`_
                for the options.  Default is ``None`` meaning "strict".
            `retain` - If ``True`` (default), retain newline characters,
                but translate all newline
                characters to ``\n``.  If ``False``, newline characters are
                omitted.

        .. seealso:: :meth:`text`
        """
        text = U_NEWLINE.sub('\n', self.read_text(encoding, errors))
        return text.splitlines(retain)

    def write_lines(
        self, lines, encoding=None, errors='strict', linesep=os.linesep, append=False
    ):
        r"""Write the given lines of text to this file.

        By default this overwrites any existing file at this path.

        This puts a platform-specific newline sequence on every line.
        See `linesep` below.

            `lines` - A list of strings.

            `encoding` - A Unicode encoding to use.  This applies only if
                `lines` contains any Unicode strings.

            `errors` - How to handle errors in Unicode encoding.  This
                also applies only to Unicode strings.

            linesep - The desired line-ending.  This line-ending is
                applied to every line.  If a line already has any
                standard line ending (``'\r'``, ``'\n'``, ``'\r\n'``,
                ``u'\x85'``, ``u'\r\x85'``, ``u'\u2028'``), that will
                be stripped off and this will be used instead.  The
                default is os.linesep, which is platform-dependent
                (``'\r\n'`` on Windows, ``'\n'`` on Unix, etc.).
                Specify ``None`` to write the lines as-is, like
                ``.writelines`` on a file object.

        Use the keyword argument ``append=True`` to append lines to the
        file.  The default is to overwrite the file.

        .. warning ::

            When you use this with Unicode data, if the encoding of the
            existing data in the file is different from the encoding
            you specify with the `encoding=` parameter, the result is
            mixed-encoding data, which can really confuse someone trying
            to read the file later.
        """
        with self.open('ab' if append else 'wb') as f:
            for line in lines:
                isUnicode = isinstance(line, str)
                if linesep is not None:
                    pattern = U_NL_END if isUnicode else B_NL_END
                    line = pattern.sub('', line) + linesep
                if isUnicode:
                    line = line.encode(encoding or sys.getdefaultencoding(), errors)
                f.write(line)

    def read_md5(self):
        """Calculate the md5 hash for this file.

        This reads through the entire file.

        .. seealso:: :meth:`read_hash`
        """
        return self.read_hash('md5')

    def _hash(self, hash_name):
        """Returns a hash object for the file at the current path.

        `hash_name` should be a hash algo name (such as ``'md5'``
        or ``'sha1'``) that's available in the :mod:`hashlib` module.
        """
        m = hashlib.new(hash_name)
        for chunk in self.chunks(8192, mode="rb"):
            m.update(chunk)
        return m

    def read_hash(self, hash_name):
        """Calculate given hash for this file.

        List of supported hashes can be obtained from :mod:`hashlib` package.
        This reads the entire file.

        .. seealso:: :meth:`hashlib.hash.digest`
        """
        return self._hash(hash_name).digest()

    def read_hexhash(self, hash_name):
        """Calculate given hash for this file, returning hexdigest.

        List of supported hashes can be obtained from :mod:`hashlib` package.
        This reads the entire file.

        .. seealso:: :meth:`hashlib.hash.hexdigest`
        """
        return self._hash(hash_name).hexdigest()

    # --- Methods for querying the filesystem.
    # N.B. On some platforms, the os.path functions may be implemented in C
    # (e.g. isdir on Windows, Python 3.2.2), and compiled functions don't get
    # bound. Playing it safe and wrapping them all in method calls.

    def isabs(self):
        """
        >>> Path('.').isabs()
        False

        .. seealso:: :func:`os.path.isabs`
        """
        return self.module.isabs(self)

    def exists(self):
        """.. seealso:: :func:`os.path.exists`"""
        return self.module.exists(self)

    def isdir(self):
        """.. seealso:: :func:`os.path.isdir`"""
        return self.module.isdir(self)

    def isfile(self):
        """.. seealso:: :func:`os.path.isfile`"""
        return self.module.isfile(self)

    def islink(self):
        """.. seealso:: :func:`os.path.islink`"""
        return self.module.islink(self)

    def ismount(self):
        """
        >>> Path('.').ismount()
        False

        .. seealso:: :func:`os.path.ismount`
        """
        return self.module.ismount(self)

    def samefile(self, other):
        """.. seealso:: :func:`os.path.samefile`"""
        return self.module.samefile(self, other)

    def getatime(self):
        """.. seealso:: :attr:`atime`, :func:`os.path.getatime`"""
        return self.module.getatime(self)

    atime = property(
        getatime,
        None,
        None,
        """
        Last access time of the file.

        >>> Path('.').atime > 0
        True

        .. seealso:: :meth:`getatime`, :func:`os.path.getatime`
        """,
    )

    def getmtime(self):
        """.. seealso:: :attr:`mtime`, :func:`os.path.getmtime`"""
        return self.module.getmtime(self)

    mtime = property(
        getmtime,
        None,
        None,
        """
        Last modified time of the file.

        .. seealso:: :meth:`getmtime`, :func:`os.path.getmtime`
        """,
    )

    def getctime(self):
        """.. seealso:: :attr:`ctime`, :func:`os.path.getctime`"""
        return self.module.getctime(self)

    ctime = property(
        getctime,
        None,
        None,
        """ Creation time of the file.

        .. seealso:: :meth:`getctime`, :func:`os.path.getctime`
        """,
    )

    def getsize(self):
        """.. seealso:: :attr:`size`, :func:`os.path.getsize`"""
        return self.module.getsize(self)

    size = property(
        getsize,
        None,
        None,
        """ Size of the file, in bytes.

        .. seealso:: :meth:`getsize`, :func:`os.path.getsize`
        """,
    )

    def access(self, *args, **kwargs):
        """
        Return does the real user have access to this path.

        >>> Path('.').access(os.F_OK)
        True

        .. seealso:: :func:`os.access`
        """
        return os.access(self, *args, **kwargs)

    def stat(self):
        """
        Perform a ``stat()`` system call on this path.

        >>> Path('.').stat()
        os.stat_result(...)

        .. seealso:: :meth:`lstat`, :func:`os.stat`
        """
        return os.stat(self)

    def lstat(self):
        """
        Like :meth:`stat`, but do not follow symbolic links.

        >>> Path('.').lstat() == Path('.').stat()
        True

        .. seealso:: :meth:`stat`, :func:`os.lstat`
        """
        return os.lstat(self)

    def __get_owner_windows(self):  # pragma: nocover
        r"""
        Return the name of the owner of this file or directory. Follow
        symbolic links.

        Return a name of the form ``DOMAIN\User Name``; may be a group.

        .. seealso:: :attr:`owner`
        """
        desc = win32security.GetFileSecurity(
            self, win32security.OWNER_SECURITY_INFORMATION
        )
        sid = desc.GetSecurityDescriptorOwner()
        account, domain, typecode = win32security.LookupAccountSid(None, sid)
        return domain + '\\' + account

    def __get_owner_unix(self):  # pragma: nocover
        """
        Return the name of the owner of this file or directory. Follow
        symbolic links.

        .. seealso:: :attr:`owner`
        """
        st = self.stat()
        return pwd.getpwuid(st.st_uid).pw_name

    def __get_owner_not_implemented(self):  # pragma: nocover
        raise NotImplementedError("Ownership not available on this platform.")

    get_owner = (
        __get_owner_windows
        if 'win32security' in globals()
        else __get_owner_unix
        if 'pwd' in globals()
        else __get_owner_not_implemented
    )

    owner = property(
        get_owner,
        None,
        None,
        """ Name of the owner of this file or directory.

        .. seealso:: :meth:`get_owner`""",
    )

    if hasattr(os, 'statvfs'):

        def statvfs(self):
            """Perform a ``statvfs()`` system call on this path.

            .. seealso:: :func:`os.statvfs`
            """
            return os.statvfs(self)

    if hasattr(os, 'pathconf'):

        def pathconf(self, name):
            """.. seealso:: :func:`os.pathconf`"""
            return os.pathconf(self, name)

    #
    # --- Modifying operations on files and directories

    def utime(self, *args, **kwargs):
        """Set the access and modified times of this file.

        .. seealso:: :func:`os.utime`
        """
        os.utime(self, *args, **kwargs)
        return self

    def chmod(self, mode):
        """
        Set the mode. May be the new mode (os.chmod behavior) or a `symbolic
        mode <http://en.wikipedia.org/wiki/Chmod#Symbolic_modes>`_.

        .. seealso:: :func:`os.chmod`
        """
        if isinstance(mode, str):
            mask = masks.compound(mode)
            mode = mask(self.stat().st_mode)
        os.chmod(self, mode)
        return self

    if hasattr(os, 'chown'):

        def chown(self, uid=-1, gid=-1):
            """
            Change the owner and group by names or numbers.

            .. seealso:: :func:`os.chown`
            """

            def resolve_uid(uid):
                return uid if isinstance(uid, int) else pwd.getpwnam(uid).pw_uid

            def resolve_gid(gid):
                return gid if isinstance(gid, int) else grp.getgrnam(gid).gr_gid

            os.chown(self, resolve_uid(uid), resolve_gid(gid))
            return self

    def rename(self, new):
        """.. seealso:: :func:`os.rename`"""
        os.rename(self, new)
        return self._next_class(new)

    def renames(self, new):
        """.. seealso:: :func:`os.renames`"""
        os.renames(self, new)
        return self._next_class(new)

    #
    # --- Create/delete operations on directories

    def mkdir(self, mode=0o777):
        """.. seealso:: :func:`os.mkdir`"""
        os.mkdir(self, mode)
        return self

    def mkdir_p(self, mode=0o777):
        """Like :meth:`mkdir`, but does not raise an exception if the
        directory already exists."""
        with contextlib.suppress(FileExistsError):
            self.mkdir(mode)
        return self

    def makedirs(self, mode=0o777):
        """.. seealso:: :func:`os.makedirs`"""
        os.makedirs(self, mode)
        return self

    def makedirs_p(self, mode=0o777):
        """Like :meth:`makedirs`, but does not raise an exception if the
        directory already exists."""
        with contextlib.suppress(FileExistsError):
            self.makedirs(mode)
        return self

    def rmdir(self):
        """.. seealso:: :func:`os.rmdir`"""
        os.rmdir(self)
        return self

    def rmdir_p(self):
        """Like :meth:`rmdir`, but does not raise an exception if the
        directory is not empty or does not exist."""
        suppressed = FileNotFoundError, FileExistsError, DirectoryNotEmpty
        with contextlib.suppress(suppressed):
            with DirectoryNotEmpty.translate():
                self.rmdir()
        return self

    def removedirs(self):
        """.. seealso:: :func:`os.removedirs`"""
        os.removedirs(self)
        return self

    def removedirs_p(self):
        """Like :meth:`removedirs`, but does not raise an exception if the
        directory is not empty or does not exist."""
        with contextlib.suppress(FileExistsError, DirectoryNotEmpty):
            with DirectoryNotEmpty.translate():
                self.removedirs()
        return self

    # --- Modifying operations on files

    def touch(self):
        """Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        fd = os.open(self, os.O_WRONLY | os.O_CREAT, 0o666)
        os.close(fd)
        os.utime(self, None)
        return self

    def remove(self):
        """.. seealso:: :func:`os.remove`"""
        os.remove(self)
        return self

    def remove_p(self):
        """Like :meth:`remove`, but does not raise an exception if the
        file does not exist."""
        with contextlib.suppress(FileNotFoundError):
            self.unlink()
        return self

    unlink = remove
    unlink_p = remove_p

    # --- Links

    def link(self, newpath):
        """Create a hard link at `newpath`, pointing to this file.

        .. seealso:: :func:`os.link`
        """
        os.link(self, newpath)
        return self._next_class(newpath)

    def symlink(self, newlink=None):
        """Create a symbolic link at `newlink`, pointing here.

        If newlink is not supplied, the symbolic link will assume
        the name self.basename(), creating the link in the cwd.

        .. seealso:: :func:`os.symlink`
        """
        if newlink is None:
            newlink = self.basename()
        os.symlink(self, newlink)
        return self._next_class(newlink)

    def readlink(self):
        """Return the path to which this symbolic link points.

        The result may be an absolute or a relative path.

        .. seealso:: :meth:`readlinkabs`, :func:`os.readlink`
        """
        return self._next_class(os.readlink(self))

    def readlinkabs(self):
        """Return the path to which this symbolic link points.

        The result is always an absolute path.

        .. seealso:: :meth:`readlink`, :func:`os.readlink`
        """
        p = self.readlink()
        return p if p.isabs() else (self.parent / p).abspath()

    # High-level functions from shutil
    # These functions will be bound to the instance such that
    # Path(name).copy(target) will invoke shutil.copy(name, target)

    copyfile = shutil.copyfile
    copymode = shutil.copymode
    copystat = shutil.copystat
    copy = shutil.copy
    copy2 = shutil.copy2
    copytree = shutil.copytree
    if hasattr(shutil, 'move'):
        move = shutil.move
    rmtree = shutil.rmtree

    def rmtree_p(self):
        """Like :meth:`rmtree`, but does not raise an exception if the
        directory does not exist."""
        with contextlib.suppress(FileNotFoundError):
            self.rmtree()
        return self

    def chdir(self):
        """.. seealso:: :func:`os.chdir`"""
        os.chdir(self)

    cd = chdir

    def merge_tree(
        self,
        dst,
        symlinks=False,
        *,
        copy_function=shutil.copy2,
        ignore=lambda dir, contents: [],
    ):
        """
        Copy entire contents of self to dst, overwriting existing
        contents in dst with those in self.

        Pass ``symlinks=True`` to copy symbolic links as links.

        Accepts a ``copy_function``, similar to copytree.

        To avoid overwriting newer files, supply a copy function
        wrapped in ``only_newer``. For example::

            src.merge_tree(dst, copy_function=only_newer(shutil.copy2))
        """
        dst = self._next_class(dst)
        dst.makedirs_p()

        sources = self.listdir()
        _ignored = ignore(self, [item.name for item in sources])

        def ignored(item):
            return item.name in _ignored

        for source in itertools.filterfalse(ignored, sources):
            dest = dst / source.name
            if symlinks and source.islink():
                target = source.readlink()
                target.symlink(dest)
            elif source.isdir():
                source.merge_tree(
                    dest,
                    symlinks=symlinks,
                    copy_function=copy_function,
                    ignore=ignore,
                )
            else:
                copy_function(source, dest)

        self.copystat(dst)

    #
    # --- Special stuff from os

    if hasattr(os, 'chroot'):

        def chroot(self):  # pragma: nocover
            """.. seealso:: :func:`os.chroot`"""
            os.chroot(self)

    if hasattr(os, 'startfile'):

        def startfile(self, *args, **kwargs):  # pragma: nocover
            """.. seealso:: :func:`os.startfile`"""
            os.startfile(self, *args, **kwargs)
            return self

    # in-place re-writing, courtesy of Martijn Pieters
    # http://www.zopatista.com/python/2013/11/26/inplace-file-rewriting/
    @contextlib.contextmanager
    def in_place(
        self,
        mode='r',
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        backup_extension=None,
    ):
        """
        A context in which a file may be re-written in-place with
        new content.

        Yields a tuple of :samp:`({readable}, {writable})` file
        objects, where `writable` replaces `readable`.

        If an exception occurs, the old file is restored, removing the
        written data.

        Mode *must not* use ``'w'``, ``'a'``, or ``'+'``; only
        read-only-modes are allowed. A :exc:`ValueError` is raised
        on invalid modes.

        For example, to add line numbers to a file::

            p = Path(filename)
            assert p.isfile()
            with p.in_place() as (reader, writer):
                for number, line in enumerate(reader, 1):
                    writer.write('{0:3}: '.format(number)))
                    writer.write(line)

        Thereafter, the file at `filename` will have line numbers in it.
        """
        if set(mode).intersection('wa+'):
            raise ValueError('Only read-only file modes can be used')

        # move existing file to backup, create new file with same permissions
        # borrowed extensively from the fileinput module
        backup_fn = self + (backup_extension or os.extsep + 'bak')
        backup_fn.remove_p()
        self.rename(backup_fn)
        readable = io.open(
            backup_fn,
            mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
        try:
            perm = os.fstat(readable.fileno()).st_mode
        except OSError:
            writable = self.open(
                'w' + mode.replace('r', ''),
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        else:
            os_mode = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
            os_mode |= getattr(os, 'O_BINARY', 0)
            fd = os.open(self, os_mode, perm)
            writable = io.open(
                fd,
                "w" + mode.replace('r', ''),
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
            with contextlib.suppress(OSError, AttributeError):
                self.chmod(perm)
        try:
            yield readable, writable
        except Exception:
            # move backup back
            readable.close()
            writable.close()
            self.remove_p()
            backup_fn.rename(self)
            raise
        else:
            readable.close()
            writable.close()
        finally:
            backup_fn.remove_p()

    @classes.ClassProperty
    @classmethod
    def special(cls):
        """
        Return a SpecialResolver object suitable referencing a suitable
        directory for the relevant platform for the given
        type of content.

        For example, to get a user config directory, invoke:

            dir = Path.special().user.config

        Uses the `appdirs
        <https://pypi.python.org/pypi/appdirs/1.4.0>`_ to resolve
        the paths in a platform-friendly way.

        To create a config directory for 'My App', consider:

            dir = Path.special("My App").user.config.makedirs_p()

        If the ``appdirs`` module is not installed, invocation
        of special will raise an ImportError.
        """
        return functools.partial(SpecialResolver, cls)


class DirectoryNotEmpty(OSError):
    @staticmethod
    @contextlib.contextmanager
    def translate():
        try:
            yield
        except OSError as exc:
            if exc.errno == errno.ENOTEMPTY:
                raise DirectoryNotEmpty(*exc.args) from exc
            raise


def only_newer(copy_func):
    """
    Wrap a copy function (like shutil.copy2) to return
    the dst if it's newer than the source.
    """

    @functools.wraps(copy_func)
    def wrapper(src, dst, *args, **kwargs):
        is_newer_dst = dst.exists() and dst.getmtime() >= src.getmtime()
        if is_newer_dst:
            return dst
        return copy_func(src, dst, *args, **kwargs)

    return wrapper


class ExtantPath(Path):
    """
    >>> ExtantPath('.')
    ExtantPath('.')
    >>> ExtantPath('does-not-exist')
    Traceback (most recent call last):
    OSError: does-not-exist does not exist.
    """

    def _validate(self):
        if not self.exists():
            raise OSError(f"{self} does not exist.")


class ExtantFile(Path):
    """
    >>> ExtantFile('.')
    Traceback (most recent call last):
    FileNotFoundError: . does not exist as a file.
    >>> ExtantFile('does-not-exist')
    Traceback (most recent call last):
    FileNotFoundError: does-not-exist does not exist as a file.
    """

    def _validate(self):
        if not self.isfile():
            raise FileNotFoundError(f"{self} does not exist as a file.")


class SpecialResolver:
    class ResolverScope:
        def __init__(self, paths, scope):
            self.paths = paths
            self.scope = scope

        def __getattr__(self, class_):
            return self.paths.get_dir(self.scope, class_)

    def __init__(self, path_class, *args, **kwargs):
        appdirs = importlib.import_module('appdirs')

        vars(self).update(
            path_class=path_class, wrapper=appdirs.AppDirs(*args, **kwargs)
        )

    def __getattr__(self, scope):
        return self.ResolverScope(self, scope)

    def get_dir(self, scope, class_):
        """
        Return the callable function from appdirs, but with the
        result wrapped in self.path_class
        """
        prop_name = '{scope}_{class_}_dir'.format(**locals())
        value = getattr(self.wrapper, prop_name)
        MultiPath = Multi.for_class(self.path_class)
        return MultiPath.detect(value)


class Multi:
    """
    A mix-in for a Path which may contain multiple Path separated by pathsep.
    """

    @classmethod
    def for_class(cls, path_cls):
        name = 'Multi' + path_cls.__name__
        return type(name, (cls, path_cls), {})

    @classmethod
    def detect(cls, input):
        if os.pathsep not in input:
            cls = cls._next_class
        return cls(input)

    def __iter__(self):
        return iter(map(self._next_class, self.split(os.pathsep)))

    @classes.ClassProperty
    @classmethod
    def _next_class(cls):
        """
        Multi-subclasses should use the parent class
        """
        return next(class_ for class_ in cls.__mro__ if not issubclass(class_, Multi))


class TempDir(Path):
    """
    A temporary directory via :func:`tempfile.mkdtemp`, and
    constructed with the same parameters that you can use
    as a context manager.

    For example:

    >>> with TempDir() as d:
    ...     d.isdir() and isinstance(d, Path)
    True

    The directory is deleted automatically.

    >>> d.isdir()
    False

    .. seealso:: :func:`tempfile.mkdtemp`
    """

    @classes.ClassProperty
    @classmethod
    def _next_class(cls):
        return Path

    def __new__(cls, *args, **kwargs):
        dirname = tempfile.mkdtemp(*args, **kwargs)
        return super(TempDir, cls).__new__(cls, dirname)

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        # TempDir should return a Path version of itself and not itself
        # so that a second context manager does not create a second
        # temporary directory, but rather changes CWD to the location
        # of the temporary directory.
        return self._next_class(self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.rmtree()


class Handlers:
    def strict(msg):
        raise

    def warn(msg):
        warnings.warn(msg, TreeWalkWarning)

    def ignore(msg):
        pass

    @classmethod
    def _resolve(cls, param):
        if not callable(param) and param not in vars(Handlers):
            raise ValueError("invalid errors parameter")
        return vars(cls).get(param, param)
