"""Make temporary directories nicely."""

import atexit
import os.path
import shutil
import tempfile


def mkdtemp_clean(suffix="", prefix="tmp", dir=None):   # pylint: disable=redefined-builtin
    """Just like mkdtemp, but the directory will be deleted when the process ends."""
    the_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
    atexit.register(cleanup_tempdir, the_dir)
    return the_dir


def cleanup_tempdir(the_dir):
    """Called on process exit to remove a temp directory."""
    if os.path.exists(the_dir):
        shutil.rmtree(the_dir)
