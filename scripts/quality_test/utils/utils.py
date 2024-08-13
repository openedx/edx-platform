"""
Helper functions for test tasks
"""


import os
import subprocess
from .envs import Env


MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))

def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    # "git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads"
    subprocess.run("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    # This find command removes all the *.pyc files that aren't in the .git
    # directory.  See this blog post for more details:
    # http://nedbatchelder.com/blog/201505/be_careful_deleting_files_around_git.html
    subprocess.run(r"find . -name '.git' -prune -o -name '*.pyc' -exec rm {} \;")
    subprocess.run("rm -rf test_root/log/auto_screenshots/*")
    subprocess.run("rm -rf /tmp/mako_[cl]ms")


def ensure_clean_package_lock():
    """
    Ensure no untracked changes have been made in the current git context.
    """
    try:
        # Run git diff command to check for changes in package-lock.json
        result = subprocess.run(
            ["git", "diff", "--name-only", "--exit-code", "package-lock.json"],
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode output to text
            check=True  # Raise error for non-zero exit code
        )
        # No differences found in package-lock.json
        print("package-lock.json is clean.")
    except subprocess.CalledProcessError as e:
        # Git diff command returned non-zero exit code (changes detected)
        print("Dirty package-lock.json, run 'npm install' and commit the generated changes.")
        print(e.stderr)  # Print any error output from the command
        raise  # Re-raise the exception to propagate the error


def clean_dir(directory):
    """
    Delete all the files from the specified directory.
    """
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    subprocess.run(f'find {directory} -type f -delete')


# @task
# @cmdopts([
#     ('skip-clean', 'C', 'skip cleaning repository before running tests'),
#     ('skip_clean', None, 'deprecated in favor of skip-clean'),
# ])

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
