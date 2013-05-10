import os, subprocess, logging

from config import CONFIGURATION, BASE_DIR

LOG = logging.getLogger(__name__)

def execute(command, working_directory=BASE_DIR, log=LOG):
    """
    Executes shell command in a given working_directory.
    Command is a string to pass to the shell.
    The command is logged to log, output is ignored.
    """
    if log:
        log.info(command)
    subprocess.call(command.split(' '), cwd=working_directory)


def call(command, working_directory=BASE_DIR, log=LOG):
    """
    Executes shell command in a given working_directory.
    Command is a string to pass to the shell.
    Returns a tuple of two strings: (stdout, stderr)
    """
    if log:
        log.info(command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
    out, err = p.communicate()
    return (out, err)
    
def create_dir_if_necessary(pathname):
    dirname = os.path.dirname(pathname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def remove_file(filename, log=LOG, verbose=True):
    """
    Attempt to delete filename.
    Log a warning if file does not exist.
    Logging filenames are releative to BASE_DIR to cut down on noise in output.
    """
    if verbose:
        log.info('Deleting file %s' % os.path.relpath(filename, BASE_DIR))
    if not os.path.exists(filename):
        log.warn("File does not exist: %s" % os.path.relpath(filename, BASE_DIR))
    else:
        os.remove(filename)
