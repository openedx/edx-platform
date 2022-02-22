"""
Helper functions for test tasks
"""


import os

from paver.easy import cmdopts, sh, task

from pavelib.utils.envs import Env
from pavelib.utils.timer import timed


MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))

COVERAGE_CACHE_BUCKET = "edx-tools-coverage-caches"
COVERAGE_CACHE_BASEPATH = "test_root/who_tests_what"
COVERAGE_CACHE_BASELINE = "who_tests_what.{}.baseline".format(os.environ.get('WTW_CONTEXT', 'all'))
WHO_TESTS_WHAT_DIFF = "who_tests_what.diff"


__test__ = False  # do not collect


@task
@timed
def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    # This find command removes all the *.pyc files that aren't in the .git
    # directory.  See this blog post for more details:
    # http://nedbatchelder.com/blog/201505/be_careful_deleting_files_around_git.html
    sh(r"find . -name '.git' -prune -o -name '*.pyc' -exec rm {} \;")
    sh("rm -rf test_root/log/auto_screenshots/*")
    sh("rm -rf /tmp/mako_[cl]ms")


@task
@timed
def ensure_clean_package_lock():
    """
    Ensure no untracked changes have been made in the current git context.
    """
    sh("""
      git diff --name-only --exit-code package-lock.json ||
      (echo \"Dirty package-lock.json, run 'npm install' and commit the generated changes\" && exit 1)
    """)


def clean_dir(directory):
    """
    Delete all the files from the specified directory.
    """
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    sh(f'find {directory} -type f -delete')


@task
@cmdopts([
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
])
@timed
def clean_reports_dir(options):
    """
    Clean coverage files, to ensure that we don't use stale data to generate reports.
    """
    if getattr(options, 'skip_clean', False):
        print('--skip-clean is set, skipping...')
        return

    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    reports_dir = Env.REPORT_DIR.makedirs_p()
    clean_dir(reports_dir)


@task
@timed
def clean_mongo():
    """
    Clean mongo test databases
    """
    sh("mongo {host}:{port} {repo_root}/scripts/delete-mongo-test-dbs.js".format(
        host=Env.MONGO_HOST,
        port=MONGO_PORT_NUM,
        repo_root=Env.REPO_ROOT,
    ))
