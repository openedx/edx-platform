"""
Utility library file for executing shell commands
"""
import os
import subprocess
import logging

from i18n.config import BASE_DIR

LOG = logging.getLogger(__name__)


def execute(command, working_directory=BASE_DIR, stderr=subprocess.STDOUT):
    """
    Executes shell command in a given working_directory.
    Command is a string to pass to the shell.
    Output is ignored.
    """
    LOG.info("Executing in %s ...", working_directory)
    LOG.info(command)
    subprocess.check_call(command, cwd=working_directory, stderr=stderr, shell=True)


def call(command, working_directory=BASE_DIR):
    """
    Executes shell command in a given working_directory.
    Command is a list of strings to execute as a command line.
    Returns a tuple of two strings: (stdout, stderr)

    """
    LOG.info(command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory, shell=True)
    out, err = p.communicate()
    return (out, err)


def remove_file(filename, verbose=True):
    """
    Attempt to delete filename.
    log is boolean. If true, removal is logged.
    Log a warning if file does not exist.
    Logging filenames are releative to BASE_DIR to cut down on noise in output.
    """
    if verbose:
        LOG.info('Deleting file %s' % os.path.relpath(filename, BASE_DIR))
    if not os.path.exists(filename):
        LOG.warn("File does not exist: %s" % os.path.relpath(filename, BASE_DIR))
    else:
        os.remove(filename)
