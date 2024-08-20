"""
Javascript test tasks
"""

import click
import os
import re
import sys
import subprocess

from utils.envs import Env
from suites import JestSnapshotTestSuite, JsTestSuite

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


def test_js(suite, mode, coverage, port, skip_clean):
    """
    Run the JavaScript tests
    """

    if (suite != 'all') and (suite not in Env.JS_TEST_ID_KEYS):
        sys.stderr.write(
            "Unknown test suite. Please choose from ({suites})\n".format(
                suites=", ".join(Env.JS_TEST_ID_KEYS)
            )
        )
        return

    if suite != 'jest-snapshot':
        test_suite = JsTestSuite(suite, mode=mode, with_coverage=coverage, port=port, skip_clean=skip_clean)
        test_suite.run()

    if (suite == 'jest-snapshot') or (suite == 'all'):  # lint-amnesty, pylint: disable=consider-using-in
        test_suite = JestSnapshotTestSuite('jest')
        test_suite.run()


# @needs('pavelib.prereqs.install_coverage_prereqs')
# @cmdopts([
#     ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
# ], share_with=['coverage'])

def diff_coverage():
    """
    Build the diff coverage reports
    """

    compare_branch = 'origin/master'

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []
    for filepath in Env.REPORT_DIR.walk():
        if bool(re.match(r'^coverage.*\.xml$', filepath.basename())):
            xml_reports.append(filepath)

    if not xml_reports:
        err_msg = colorize(
            'red',
            "No coverage info found.  Run `quality test` before running "
            "`coverage test`.\n"
        )
        sys.stderr.write(err_msg)
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(Env.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        # The --diff-range-notation parameter is a workaround for https://github.com/Bachmann1234/diff_cover/issues/153
        command = (
            f"diff-cover {xml_report_str}"
            f"--diff-range-notation '..'"
            f"--compare-branch={compare_branch} "
            f"--html-report {diff_html_path}"
        )
        subprocess.run(command,
                       shell=True,
                       check=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)


@click.command("main")
@click.option(
    '--option', 'option',
    help='Run javascript tests or coverage test as per given option'
)
@click.option(
    '--s', 'suite',
    default='all',
    help='Test suite to run.'
)
@click.option(
    '--m', 'mode',
    default='run',
    help='dev or run'
)
@click.option(
    '--coverage', 'coverage',
    default=True,
    help='Run test under coverage'
)
@click.option(
    '--p', 'port',
    default=None,
    help='Port to run test server on (dev mode only)'
)
@click.option(
    '--C', 'skip_clean',
    default=False,
    help='skip cleaning repository before running tests'
)
def main(option, suite, mode, coverage, port, skip_clean):
    if option == 'jstest':
        test_js(suite, mode, coverage, port, skip_clean)
    elif option == 'coverage':
        diff_coverage()


if __name__ == "__main__":
    main()
