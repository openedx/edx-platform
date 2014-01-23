from paver.easy import *
import os
import subprocess

__test__ = False  # do not collect


class TestFailed(Exception):
    pass

FAILED_TESTS = 0


# Run sh on args. If TESTS_FAIL_FAST is set, then stop on the first shell failure.
# Otherwise, a final task will be added that will fail if any tests have failed
def test_sh(cmd, discard_stdout=True):
    global FAILED_TESTS

    kwargs = {'shell': True, 'cwd': None}
    try:
        if discard_stdout:
            out_log_file = open('/dev/null', 'w')
            kwargs['stdout'] = out_log_file

        subprocess.call(cmd, **kwargs)

    except Exception as e:
        print e.message
        if 'TESTS_FAIL_FAST' in os.environ and os.environ['TEST_FAIL_FAST']:
            raise TestFailed('Test failed!')
        else:
            FAILED_TESTS += 1
    else:
        return True


# "Clean fixture files used by tests and .pyc files"
def clean_test_files():
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name *.pyc -delete")


# Clean coverage files, to ensure that we don't use stale data to generate reports.
def clean_dir(dir):
    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    sh('find {dir} -type f -delete'.format(dir=dir))


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def find_executable(cmd):
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, cmd)
        if is_exe(exe_file):
            return exe_file

    return None
