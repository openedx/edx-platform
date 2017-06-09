"""
Helper functions for test tasks
"""
from paver.easy import sh, task, cmdopts
from pavelib.utils.envs import Env
from pavelib.utils.timer import timed
import os
import re
import subprocess

MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')
MINIMUM_FIREFOX_VERSION = 28.0

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


def clean_dir(directory):
    """
    Delete all the files from the specified directory.
    """
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    sh('find {dir} -type f -delete'.format(dir=directory))


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
        print '--skip-clean is set, skipping...'
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
        host=MONGO_HOST,
        port=MONGO_PORT_NUM,
        repo_root=Env.REPO_ROOT,
    ))


def check_firefox_version():
    """
    Check that firefox is the correct version.
    """
    expected_firefox_ver = "Mozilla Firefox " + str(MINIMUM_FIREFOX_VERSION)
    firefox_ver_string = subprocess.check_output("firefox --version", shell=True).strip()
    firefox_version_regex = re.compile(r"Mozilla Firefox (\d+.\d+)")
    try:
        firefox_ver = float(firefox_version_regex.search(firefox_ver_string).group(1))
    except AttributeError:
        firefox_ver = 0.0
    debian_location = 'https://s3.amazonaws.com/vagrant.testeng.edx.org/'
    debian_package = 'firefox-mozilla-build_42.0-0ubuntu1_amd64.deb'
    debian_path = '{location}{package}'.format(location=debian_location, package=debian_package)

    if firefox_ver < MINIMUM_FIREFOX_VERSION:
        raise Exception(
            'Required firefox version not found.\n'
            'Expected: {expected_version}; Actual: {actual_version}.\n\n'
            'As the vagrant user in devstack, run the following:\n\n'
            '\t$ sudo wget -O /tmp/firefox_42.deb {debian_path}\n'
            '\t$ sudo apt-get remove firefox\n\n'
            '\t$ sudo gdebi -nq /tmp/firefox_42.deb\n\n'
            'Confirm the new version:\n'
            '\t$ firefox --version\n'
            '\t{expected_version}'.format(
                actual_version=firefox_ver,
                expected_version=expected_firefox_ver,
                debian_path=debian_path
            )
        )
