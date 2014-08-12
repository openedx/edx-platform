"""
Helper functions for test tasks
"""
from paver.easy import sh, task
from pavelib.utils.envs import Env

__test__ = False  # do not collect


@task
def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name \"*.pyc\" -delete")
    sh("rm -rf test_root/log/auto_screenshots/*")
    sh("rm -rf /tmp/mako_[cl]ms")


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
    reports_dir = Env.REPORT_DIR.makedirs_p()
    clean_dir(reports_dir)


@task
def clean_mongo():
    """
    Clean mongo test databases
    """
    sh("mongo {repo_root}/scripts/delete-mongo-test-dbs.js".format(repo_root=Env.REPO_ROOT))
