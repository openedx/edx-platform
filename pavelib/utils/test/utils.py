"""
Helper functions for test tasks
"""
from paver.easy import sh, task, cmdopts
from pavelib.utils.envs import Env
import os
import subprocess

MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

__test__ = False  # do not collect


@task
def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name \"*.pyc\" -not -path './.git/*' -delete")
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
@cmdopts([
    ('skip_clean', 'C', 'skip cleaning repository before running tests'),
])
def clean_reports_dir(options):
    """
    Clean coverage files, to ensure that we don't use stale data to generate reports.
    """
    if getattr(options, 'skip_clean', False):
        print('--skip_clean is set, skipping...')
        return

    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    reports_dir = Env.REPORT_DIR.makedirs_p()
    clean_dir(reports_dir)


@task
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
    expected_firefox_ver = "Mozilla Firefox 28.0"
    firefox_ver = subprocess.check_output("firefox --version", shell=True).strip()

    if firefox_ver != expected_firefox_ver:
        raise Exception(
            'Required firefox version not found.\n'
            'Expected: {expected_version}; Actual: {actual_version}.\n\n'
            'As the vagrant user in devstack, run the following:\n\n'
            '\t$ sudo wget -O /tmp/firefox_28.deb https://s3.amazonaws.com/vagrant.testeng.edx.org/firefox_28.0%2Bbuild2-0ubuntu0.12.04.1_amd64.deb\n'
            '\t$ sudo apt-get remove firefox\n\n'
            '\t$ sudo gdebi -nq /tmp/firefox_28.deb\n\n'
            'Confirm the new version:\n'
            '\t$ firefox --version\n'
            '\t{expected_version}'.format(actual_version=firefox_ver, expected_version=expected_firefox_ver)
        )
