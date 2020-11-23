"""
Safe version of tarfile.extractall which does not extract any files that would
be, or symlink to a file that is, outside of the directory extracted in.

Adapted from:
http://stackoverflow.com/questions/10060069/safely-extract-zip-or-tar-using-python
"""

import logging
from os.path import join as joinpath
from os.path import abspath, dirname, realpath

from django.conf import settings
from django.core.exceptions import SuspiciousOperation

log = logging.getLogger(__name__)


def resolved(rpath):
    """
    Returns the canonical absolute path of `rpath`.
    """
    return realpath(abspath(rpath))


def _is_bad_path(path, base):
    """
    Is (the canonical absolute path of) `path` outside `base`?
    """
    return not resolved(joinpath(base, path)).startswith(base)


def _is_bad_link(info, base):
    """
    Does the file sym- or hard-link to files outside `base`?
    """
    # Links are interpreted relative to the directory containing the link
    tip = resolved(joinpath(base, dirname(info.name)))
    return _is_bad_path(info.linkname, base=tip)


def safemembers(members, base):
    """
    Check that all elements of a tar file are safe.
    """

    base = resolved(base)

    # check that we're not trying to import outside of the github_repo_root
    if not base.startswith(resolved(settings.GITHUB_REPO_ROOT)):
        raise SuspiciousOperation("Attempted to import course outside of data dir")

    for finfo in members:
        if _is_bad_path(finfo.name, base):
            log.debug(u"File %r is blocked (illegal path)", finfo.name)
            raise SuspiciousOperation("Illegal path")
        elif finfo.issym() and _is_bad_link(finfo, base):
            log.debug(u"File %r is blocked: Hard link to %r", finfo.name, finfo.linkname)
            raise SuspiciousOperation("Hard link")
        elif finfo.islnk() and _is_bad_link(finfo, base):
            log.debug(u"File %r is blocked: Symlink to %r", finfo.name,
                      finfo.linkname)
            raise SuspiciousOperation("Symlink")
        elif finfo.isdev():
            log.debug(u"File %r is blocked: FIFO, device or character file",
                      finfo.name)
            raise SuspiciousOperation("Dev file")

    return members


def safetar_extractall(tar_file, path=".", members=None):  # pylint: disable=unused-argument
    """
    Safe version of `tar_file.extractall()`.
    """
    path = str(path)
    return tar_file.extractall(path, safemembers(tar_file, path))
