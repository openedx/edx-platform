"""
Helper functions for test tasks
"""
from paver.easy import sh, task
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
    sh("mongo {host}:{port} {repo_root}/scripts/delete-mongo-test-dbs.js".format(
        host=MONGO_HOST,
        port=MONGO_PORT_NUM,
        repo_root=Env.REPO_ROOT,
    ))

def check_firefox_and_selenium_version_compatibility():
    """
    Check that the pairing of firefox and selenium version is a known compatible one.
    """
    firefox_ver = subprocess.check_output("firefox --version", shell=True).strip()
    selenium_ver = subprocess.check_output( "pip freeze | grep selenium==", shell=True).strip()

    compatible_versions = [
        ("Mozilla Firefox 28.0", "selenium==2.42.1"),
        ("Mozilla Firefox 29.0", "selenium==2.42.1"),
        ("Mozilla Firefox 25.0", "selenium==2.39.0"),
    ]

    current_versions = (firefox_ver, selenium_ver)

    if current_versions not in compatible_versions:
        raise Exception(
            'Browser and selenium versions not compatible.\nCurrently installed versions:\n{}.\n'
            '\nKnown compatible versions:\n{}'.format(
                current_versions,
                "\n".join(str(i) for i in compatible_versions),
            )
        )

