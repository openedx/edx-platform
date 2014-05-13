"""
Helper functions for test tasks
"""
import os
from paver.easy import sh, task
from pavelib.utils.envs import Env
import errno

__test__ = False  # do not collect


def get_or_make_dir(directory_path):
    """
    Ensure that a directory exists, and return its path
    """
    try:
        os.makedirs(directory_path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            # If we get an error other than one that says
            # that the file already exists
            raise

    return directory_path


@task
def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name \"*.pyc\" -delete")
    sh("rm -rf test_root/log/auto_screenshots/*")


def clean_dir(directory):
    """
    Clean coverage files, to ensure that we don't use stale data to generate reports.
    """
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    sh('find {dir} -type f -delete'.format(dir=directory))


@task
def clean_reports_dir():
    """
    Clean coverage files, to ensure that we don't use stale data to generate reports.
    """
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    reports_dir = get_or_make_dir(Env.REPORT_DIR)
    clean_dir(reports_dir)


@task
def clean_mongo():
    """
    Clean mongo test databases
    """
    sh("mongo {repo_root}/scripts/delete-mongo-test-dbs.js".format(repo_root=Env.REPO_ROOT))


# For colorizing stdout/stderr
COLORS = {
    'PURPLE': '\033[95m',
    'BLUE': '\033[94m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
}


def colorize(msg, color):
    """
    :returns: a string that when used as the msg arg to sys.stdout or sys.stderr will be
    the specified color
    """
    color = COLORS.get(color, 'ENDC')
    return(color + msg + COLORS['ENDC'])
