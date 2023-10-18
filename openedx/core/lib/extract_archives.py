"""
Safe version of extractall which does not extract any files that would
be, or symlink to a file that is, outside of the directory extracted in.

Adapted from:
http://stackoverflow.com/questions/10060069/safely-extract-zip-or-tar-using-python
"""

import logging
import tarfile
from contextlib import contextmanager
from os.path import join as joinpath
from os.path import abspath, dirname, realpath
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import SuspiciousOperation

log = logging.getLogger(__name__)


def _resolved(rpath):
    """
    Returns the canonical absolute path of `rpath`.
    """
    return realpath(abspath(rpath))


def _is_bad_path(path, base):
    """
    Is (the canonical absolute path of) `path` outside `base`?
    """
    return not _resolved(joinpath(base, path)).startswith(base)


def _is_bad_link(info, base):
    """
    Does the file sym- or hard-link to files outside `base`?
    """
    # Links are interpreted relative to the directory containing the link
    tip = _resolved(joinpath(base, dirname(info.name)))
    return _is_bad_path(info.linkname, base=tip)


def _checkmembers(members, base):
    """
    Check that all elements of the archive file are safe.
    """
    base = _resolved(base)

    # check that we're not trying to import outside of the github_repo_root
    if not base.startswith(_resolved(settings.GITHUB_REPO_ROOT)):
        raise SuspiciousOperation(
            "Attempted to import course outside of data dir")

    for finfo in members:
        if _is_bad_path(finfo.name, base):
            log.debug("File %r is blocked (illegal path)", finfo.name)
            raise SuspiciousOperation("Illegal path")
        if finfo.issym() and _is_bad_link(finfo, base):
            log.debug(
                "File %r is blocked: Hard link to %r",
                finfo.name,
                finfo.linkname
            )
            raise SuspiciousOperation("Hard link")
        if finfo.islnk() and _is_bad_link(finfo, base):
            log.debug("File %r is blocked: Symlink to %r", finfo.name,
                      finfo.linkname)
            raise SuspiciousOperation("Symlink")
        if finfo.isdev():
            log.debug("File %r is blocked: FIFO, device or character file",
                      finfo.name)
            raise SuspiciousOperation("Dev file")


class ZipMemberAdapter:
    """
    Adapter ZipInfo to Member

    from the stack overflow link above:
        Starting with python 2.7.4, this is a non-issue for ZIP archives:
        The method zipfile.extract() prohibits the creation of files
        outside the sandbox
    """
    def __init__(self, zipinfo):
        self.name = zipinfo.filename
        self.issym = lambda: False
        self.islnk = lambda: False
        self.isdev = lambda: False


@contextmanager
def safe_open_archive(file_name, output_path):
    """
    Safe Extract Zip or Tar files
    """
    if not output_path.endswith('/'):
        output_path += '/'
    try:
        if file_name.endswith('.zip'):
            archive = ZipFile(file_name, 'r')
            members = [
                ZipMemberAdapter(zipinfo)
                for zipinfo in archive.infolist()
            ]
        elif file_name.endswith('.tar.gz'):
            archive = tarfile.open(file_name)
            members = archive.getmembers()

        _checkmembers(members, output_path)
        yield archive
    finally:
        archive.close()


def safe_extractall(file_name, output_path):
    """
    Extract Zip or Tar files
    """
    with safe_open_archive(file_name, output_path) as archive:
        archive.extractall(output_path)
