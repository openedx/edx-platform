import functools
import os


def best_realpath(module):
    """
    Given a path module (i.e. ntpath, posixpath),
    determine the best 'realpath' function to use
    for best future compatibility.
    """
    needs_backport = module.realpath is module.abspath
    return realpath_backport if needs_backport else module.realpath


# backport taken from jaraco.windows 5
def realpath_backport(path):
    if isinstance(path, str):
        prefix = '\\\\?\\'
        unc_prefix = prefix + 'UNC'
        new_unc_prefix = '\\'
        cwd = os.getcwd()
    else:
        prefix = b'\\\\?\\'
        unc_prefix = prefix + b'UNC'
        new_unc_prefix = b'\\'
        cwd = os.getcwdb()
    had_prefix = path.startswith(prefix)
    path, ok = _resolve_path(cwd, path, {})
    # The path returned by _getfinalpathname will always start with \\?\ -
    # strip off that prefix unless it was already provided on the original
    # path.
    if not had_prefix:
        # For UNC paths, the prefix will actually be \\?\UNC - handle that
        # case as well.
        if path.startswith(unc_prefix):
            path = new_unc_prefix + path[len(unc_prefix) :]
        elif path.startswith(prefix):
            path = path[len(prefix) :]
    return path


def _resolve_path(path, rest, seen):  # noqa: C901
    # Windows normalizes the path before resolving symlinks; be sure to
    # follow the same behavior.
    rest = os.path.normpath(rest)

    if isinstance(rest, str):
        sep = '\\'
    else:
        sep = b'\\'

    if os.path.isabs(rest):
        drive, rest = os.path.splitdrive(rest)
        path = drive + sep
        rest = rest[1:]

    while rest:
        name, _, rest = rest.partition(sep)
        new_path = os.path.join(path, name) if path else name
        if os.path.exists(new_path):
            if not rest:
                # The whole path exists.  Resolve it using the OS.
                path = os.path._getfinalpathname(new_path)
            else:
                # The OS can resolve `new_path`; keep traversing the path.
                path = new_path
        elif not os.path.lexists(new_path):
            # `new_path` does not exist on the filesystem at all.  Use the
            # OS to resolve `path`, if it exists, and then append the
            # remainder.
            if os.path.exists(path):
                path = os.path._getfinalpathname(path)
            rest = os.path.join(name, rest) if rest else name
            return os.path.join(path, rest), True
        else:
            # We have a symbolic link that the OS cannot resolve.  Try to
            # resolve it ourselves.

            # On Windows, symbolic link resolution can be partially or
            # fully disabled [1].  The end result of a disabled symlink
            # appears the same as a broken symlink (lexists() returns True
            # but exists() returns False).  And in both cases, the link can
            # still be read using readlink().  Call stat() and check the
            # resulting error code to ensure we don't circumvent the
            # Windows symbolic link restrictions.
            # [1] https://technet.microsoft.com/en-us/library/cc754077.aspx
            try:
                os.stat(new_path)
            except OSError as e:
                # WinError 1463:  The symbolic link cannot be followed
                # because its type is disabled.
                if e.winerror == 1463:
                    raise

            key = os.path.normcase(new_path)
            if key in seen:
                # This link has already been seen; try to use the
                # previously resolved value.
                path = seen[key]
                if path is None:
                    # It has not yet been resolved, which means we must
                    # have a symbolic link loop.  Return what we have
                    # resolved so far plus the remainder of the path (who
                    # cares about the Zen of Python?).
                    path = os.path.join(new_path, rest) if rest else new_path
                    return path, False
            else:
                # Mark this link as in the process of being resolved.
                seen[key] = None
                # Try to resolve it.
                path, ok = _resolve_path(path, os.readlink(new_path), seen)
                if ok:
                    # Resolution succeded; store the resolved value.
                    seen[key] = path
                else:
                    # Resolution failed; punt.
                    return (os.path.join(path, rest) if rest else path), False
    return path, True


def lru_cache(user_function):
    """
    Support for lru_cache(user_function)
    """
    return functools.lru_cache()(user_function)
