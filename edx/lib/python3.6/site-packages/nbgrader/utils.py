import os
import hashlib
import dateutil.parser
import glob
import six
import sys
import shutil
import stat
import logging
import traceback
import contextlib

from setuptools.archive_util import unpack_archive
from setuptools.archive_util import unpack_tarfile
from setuptools.archive_util import unpack_zipfile
from contextlib import contextmanager
from tornado.log import LogFormatter
from dateutil.tz import gettz


# pwd is for unix passwords only, so we shouldn't import it on
# windows machines
if sys.platform != 'win32':
    import pwd
else:
    pwd = None


def is_grade(cell):
    """Returns True if the cell is a grade cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('grade', False)


def is_solution(cell):
    """Returns True if the cell is a solution cell."""
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('solution', False)


def is_locked(cell):
    """Returns True if the cell source is locked (will be overwritten)."""
    if 'nbgrader' not in cell.metadata:
        return False
    elif is_solution(cell):
        return False
    elif is_grade(cell):
        return True
    else:
        return cell.metadata['nbgrader'].get('locked', False)


def determine_grade(cell):
    if not is_grade(cell):
        raise ValueError("cell is not a grade cell")

    max_points = float(cell.metadata['nbgrader']['points'])
    if is_solution(cell):
        # if it's a solution cell and the checksum hasn't changed, that means
        # they didn't provide a response, so we can automatically give this a
        # zero grade
        if "checksum" in cell.metadata.nbgrader and cell.metadata.nbgrader["checksum"] == compute_checksum(cell):
            return 0, max_points
        else:
            return None, max_points

    elif cell.cell_type == 'code':
        for output in cell.outputs:
            if output.output_type == 'error':
                return 0, max_points
        return max_points, max_points

    else:
        return None, max_points


def to_bytes(string):
    """A python 2/3 compatible function for converting a string to bytes.
    In Python 2, this just returns the 8-bit string. In Python 3, this first
    encodes the string to utf-8.

    """
    if sys.version_info[0] == 3 or (sys.version_info[0] == 2 and isinstance(string, unicode)):
        return bytes(string.encode('utf-8'))
    else:
        return bytes(string)


def compute_checksum(cell):
    m = hashlib.md5()
    # add the cell source and type
    m.update(to_bytes(cell.source))
    m.update(to_bytes(cell.cell_type))

    # add whether it's a grade cell and/or solution cell
    m.update(to_bytes(str(is_grade(cell))))
    m.update(to_bytes(str(is_solution(cell))))
    m.update(to_bytes(str(is_locked(cell))))

    # include the cell id
    m.update(to_bytes(cell.metadata.nbgrader['grade_id']))

    # include the number of points that the cell is worth, if it is a grade cell
    if is_grade(cell):
        m.update(to_bytes(str(float(cell.metadata.nbgrader['points']))))

    return m.hexdigest()


def parse_utc(ts):
    """Parses a timestamp into datetime format, converting it to UTC if necessary."""
    if ts is None:
        return None
    if isinstance(ts, six.string_types):
        ts = dateutil.parser.parse(ts)
    if ts.tzinfo is not None:
        ts = (ts - ts.utcoffset()).replace(tzinfo=None)
    return ts


def as_timezone(ts, timezone):
    """Converts UTC timestamp ts to have timezone tz."""
    if not timezone:
        return ts
    tz = gettz(timezone)
    if tz:
        return (ts + tz.utcoffset(ts)).replace(tzinfo=tz)
    else:
        return ts


def check_mode(path, read=False, write=False, execute=False):
    """Can the current user can rwx the path."""
    mode = 0
    if read:
        mode |= os.R_OK
    if write:
        mode |= os.W_OK
    if execute:
        mode |= os.X_OK
    return os.access(path, mode)


def check_directory(path, read=False, write=False, execute=False):
    """Does that path exist and can the current user rwx."""
    if os.path.isdir(path) and check_mode(path, read=read, write=write, execute=execute):
        return True
    else:
        return False


def get_username():
    """Get the username of the current process."""
    if pwd is None:
        raise OSError("get_username cannot be called on Windows")
    return pwd.getpwuid(os.getuid())[0]


def find_owner(path):
    """Get the username of the owner of path."""
    if pwd is None:
        raise OSError("find_owner cannot be called on Windows")
    return pwd.getpwuid(os.stat(os.path.abspath(path)).st_uid).pw_name


def self_owned(path):
    """Is the path owned by the current user of this process?"""
    return get_username() == find_owner(os.path.abspath(path))


def is_ignored(filename, ignore_globs=None):
    """Determines whether a filename should be ignored, based on whether it
    matches any file glob in the given list. Note that this only matches on the
    base filename itself, not the full path."""
    if ignore_globs is None:
        return False
    dirname = os.path.dirname(filename)
    for expr in ignore_globs:
        globs = glob.glob(os.path.join(dirname, expr))
        if filename in globs:
            return True
    return False


def find_all_files(path, exclude=None):
    """Recursively finds all filenames rooted at `path`, optionally excluding
    some based on filename globs."""
    files = []
    for dirname, dirnames, filenames in os.walk(path):
        if is_ignored(dirname, exclude):
            continue
        for filename in filenames:
            fullpath = os.path.join(dirname, filename)
            if is_ignored(fullpath, exclude):
                continue
            else:
                files.append(fullpath)
    return files


def find_all_notebooks(path):
    """Return a sorted list of notebooks recursively found rooted at `path`."""
    notebooks = list()
    rootpath = os.path.abspath(path)
    for _file in find_all_files(rootpath):
        if os.path.splitext(_file)[-1] == '.ipynb':
            notebooks.append(os.path.relpath(_file, rootpath))
    notebooks.sort()
    return notebooks


def full_split(path):
    rest, last = os.path.split(path)
    if last == path:
        return (path,)
    elif rest == path:
        return (rest,)
    else:
        return full_split(rest) + (last,)


@contextlib.contextmanager
def chdir(dirname):
    currdir = os.getcwd()
    if dirname:
        os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(currdir)


def rmtree(path):
    # for windows, we need to go through and make sure everything
    # is writeable, otherwise rmtree will fail
    if sys.platform == 'win32':
        for dirname, _, filenames in os.walk(path):
            os.chmod(dirname, stat.S_IWRITE)
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), stat.S_IWRITE)

    # now we can remove the path
    shutil.rmtree(path)


def remove(path):
    # for windows, we need to make sure that the file is writeable,
    # otherwise remove will fail
    if sys.platform == 'win32':
        os.chmod(path, stat.S_IWRITE)

    # now we can remove the path
    os.remove(path)


def unzip(src, dest, zip_ext=None, create_own_folder=False, tree=False):
    """Extract all content from an archive file to a destination folder.

    Arguments
    ---------
    src: str
        Absolute path to the archive file ('/path/to/archive_filename.zip')
    dest: str
        Asolute path to extract all content to ('/path/to/extract/')

    Keyword Arguments
    -----------------
    zip_ext: list
        Valid zip file extensions. Default: ['.zip', '.gz']
    create_own_folder: bool
        Create a sub-folder in 'dest' with the archive file name if True
        ('/path/to/extract/archive_filename/'). Default: False
    tree: bool
        Extract archive files within archive files (into their own
        sub-directory) if True. Default: False
    """
    zip_ext = list(zip_ext or ['.zip', '.gz'])
    filename, ext = os.path.splitext(os.path.basename(src))
    if ext not in zip_ext:
        raise ValueError("Invalid archive file extension {}: {}".format(ext, src))
    if not check_directory(dest, write=True, execute=True):
        raise OSError("Directory not found or unwritable: {}".format(dest))

    if create_own_folder:
        # double splitext for .tar.gz
        fname, ext = os.path.splitext(os.path.basename(filename))
        if ext == '.tar':
            filename = fname
        dest = os.path.join(dest, filename)
        if not os.path.isdir(dest):
            os.makedirs(dest)

    unpack_archive(src, dest, drivers=(unpack_zipfile, unpack_tarfile))

    # extract flat, don't extract archive files within archive files
    if not tree:
        return

    def find_archive_files(skip):
        found = []
        # find archive files in dest that are not in skip
        for root, _, filenames in os.walk(dest):
            for basename in filenames:
                src_file = os.path.join(root, basename)
                _, ext = os.path.splitext(basename)
                if ext in zip_ext and src_file not in skip:
                    found.append(src_file)
        return found

    skip = []
    new_files = find_archive_files(skip)
    # keep walking dest until no new archive files are found
    while new_files:
        # unzip (flat) new archive files found in dest
        for src_file in new_files:
            dest_path = os.path.split(src_file)[0]
            unzip(
                src_file,
                dest_path,
                zip_ext=zip_ext,
                create_own_folder=True,
                tree=False
            )
            skip.append(src_file)
        new_files = find_archive_files(skip)


@contextmanager
def temp_attrs(app, **newvals):
    oldvals = {}
    for k, v in newvals.items():
        oldvals[k] = getattr(app, k)
        setattr(app, k, v)

    yield app

    for k, v in oldvals.items():
        setattr(app, k, v)


def capture_log(app, fmt="[%(levelname)s] %(message)s"):
    """Adds an extra handler to the given application the logs to a string
    buffer, calls ``app.start()``, and returns the log output. The extra
    handler is removed from the application before returning.

    Arguments
    ---------
    app: LoggingConfigurable
        An application, withh the `.start()` method implemented
    fmt: string
        A format string for formatting log messages

    Returns
    -------
    A dictionary with the following keys (error and log may or may not be present):

        - success (bool): whether or not the operation completed successfully
        - error (string): formatted traceback
        - log (string): captured log output

    """
    log_buff = six.StringIO()
    handler = logging.StreamHandler(log_buff)
    formatter = LogFormatter(fmt="[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    app.log.addHandler(handler)

    try:
        app.start()

    except:
        log_buff.flush()
        val = log_buff.getvalue()
        result = {"success": False}
        result["error"] = traceback.format_exc()
        if val:
            result["log"] = val

    else:
        log_buff.flush()
        val = log_buff.getvalue()
        result = {"success": True}
        if val:
            result["log"] = val

    finally:
        log_buff.close()
        app.log.removeHandler(handler)

    return result
