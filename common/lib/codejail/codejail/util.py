"""Helpers for codejail."""

import contextlib
import os
import shutil
import sys
import tempfile


class TempDirectory(object):
    def __init__(self, delete_when_done=True):
        self.delete_when_done = delete_when_done
        self.temp_dir = tempfile.mkdtemp(prefix="codejail-")
        # Make directory readable by other users ('sandbox' user needs to be able to read it)
        os.chmod(self.temp_dir, 0775)

    def clean_up(self):
        if self.delete_when_done:
            # if this errors, something is genuinely wrong, so don't ignore errors.
            shutil.rmtree(self.temp_dir)

@contextlib.contextmanager
def temp_directory(delete_when_done=True):
    """
    A context manager to make and use a temp directory.  If `delete_when_done`
    is true (the default), the directory will be removed when done.
    """
    tmp = TempDirectory(delete_when_done)
    try:
        yield tmp.temp_dir
    finally:
        tmp.clean_up()


class ModuleIsolation(object):
    """
    Manage changes to sys.modules so that we can roll back imported modules.

    Create this object, it will snapshot the currently imported modules. When
    you call `clean_up()`, it will delete any module imported since its creation.
    """
    def __init__(self):
        # Save all the names of all the imported modules.
        self.mods = set(sys.modules)

    def clean_up(self):
        # Get a list of modules that didn't exist when we were created
        new_mods = [m for m in sys.modules if m not in self.mods]
        # and delete them all so another import will run code for real again.
        for m in new_mods:
            del sys.modules[m]


class ChangeDirectory(object):
    def __init__(self, new_dir):
        self.old_dir = os.getcwd()
        os.chdir(new_dir)

    def clean_up(self):
        os.chdir(self.old_dir)

@contextlib.contextmanager
def change_directory(new_dir):
    """
    A context manager to change the directory, and then change it back.
    """
    cd = ChangeDirectory(new_dir)
    try:
        yield new_dir
    finally:
        cd.clean_up()
