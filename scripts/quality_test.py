"""  # lint-amnesty, pylint: disable=django-not-configured
Check code quality using pycodestyle, pylint, and diff_quality.
"""

import argparse
import glob
import json
import os
import re
import sys
import subprocess
import shutil
from pathlib import Path
from time import sleep

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text


class BuildFailure(Exception):
    """Represents a problem with some part of the build's execution."""


def fail_quality(name, message):
    """
    Fail the specified quality check.
    """
    print(name)
    print(message)
    sys.exit()


def _prepare_report_dir(dir_name):
    """
    Sets a given directory to a created, but empty state
    """
    if os.path.isdir(dir_name):
        shutil.rmtree(dir_name)
    os.makedirs(dir_name, exist_ok=True)


def repo_root():
    """
    Get the root of the git repository (edx-platform).

    This sometimes fails on Docker Devstack, so it's been broken
    down with some additional error handling.  It usually starts
    working within 30 seconds or so; for more details, see
    https://openedx.atlassian.net/browse/PLAT-1629 and
    https://github.com/docker/for-mac/issues/1509
    """

    file_path = Path(__file__)
    max_attempts = 180
    for attempt in range(1, max_attempts + 1):
        try:
            absolute_path = file_path.resolve(strict=True)
            return absolute_path.parents[1]
        except OSError:
            print(f'Attempt {attempt}/{max_attempts} to get an absolute path failed')
            if attempt < max_attempts:
                sleep(1)
            else:
                print('Unable to determine the absolute path of the edx-platform repo, aborting')
                raise RuntimeError('Could not determine the repository root after multiple attempts')


def _get_report_contents(filename, report_name, last_line_only=False):
    """
    Returns the contents of the given file. Use last_line_only to only return
    the last line, which can be used for getting output from quality output
    files.

    Arguments:
        last_line_only: True to return the last line only, False to return a
            string with full contents.

    Returns:
        String containing full contents of the report, or the last line.

    """
    if os.path.isfile(filename):
        with open(filename) as report_file:
            if last_line_only:
                lines = report_file.readlines()
                for line in reversed(lines):
                    if line != '\n':
                        return line
                return None
            else:
                return report_file.read()
    else:
        file_not_found_message = f"FAILURE: The following log file could not be found: {filename}"
        fail_quality(report_name, file_not_found_message)


def _get_count_from_last_line(filename, file_type):
    """
    This will return the number in the last line of a file.
    It is returning only the value (as a floating number).
    """
    report_contents = _get_report_contents(filename, file_type, last_line_only=True)
    if report_contents is None:
        return 0

    last_line = report_contents.strip()
    # Example of the last line of a compact-formatted eslint report (for example): "62829 problems"
    regex = r'^\d+'

    try:
        return float(re.search(regex, last_line).group(0))
    # An AttributeError will occur if the regex finds no matches.
    # A ValueError will occur if the returned regex cannot be cast as a float.
    except (AttributeError, ValueError):
        return None


def run_eslint():
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """

    REPO_ROOT = repo_root()
    REPORT_DIR = REPO_ROOT / 'reports'
    eslint_report_dir = REPORT_DIR / "eslint"
    eslint_report = eslint_report_dir / "eslint.report"
    _prepare_report_dir(eslint_report_dir)
    violations_limit = 4950

    command = [
        "node",
        "--max_old_space_size=4096",
        "node_modules/.bin/eslint",
        "--ext", ".js",
        "--ext", ".jsx",
        "--format=compact",
        "."
    ]

    with open(eslint_report, 'w') as report_file:
        subprocess.run(
            command,
            stdout=report_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )

    try:
        num_violations = int(_get_count_from_last_line(eslint_report, "eslint"))
    except TypeError:
        fail_quality(
            'eslint',
            "FAILURE: Number of eslint violations could not be found in {eslint_report}".format(
                eslint_report=eslint_report
            )
        )

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit > -1:
        fail_quality(
            'eslint',
            "FAILURE: Too many eslint violations ({count}).\nThe limit is {violations_limit}.".format(
                count=num_violations, violations_limit=violations_limit
            )
        )
    else:
        print("successfully run eslint with violations")
        print(num_violations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=['eslint'])

    argument = parser.parse_args()

    if argument.command == 'eslint':
        run_eslint()
