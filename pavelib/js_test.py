"""
Javascript test tasks
"""


import os
import re
import sys

from paver.easy import cmdopts, needs, task

from pavelib.utils.envs import Env
from pavelib.utils.test.suites import JestSnapshotTestSuite, JsTestSuite
from pavelib.utils.timer import timed
from paver.easy import cmdopts, needs, sh, task

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


@task
@needs(
    'pavelib.prereqs.install_node_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
    'pavelib.assets.process_xmodule_assets',
)
@cmdopts([
    ("suite=", "s", "Test suite to run"),
    ("mode=", "m", "dev or run"),
    ("coverage", "c", "Run test under coverage"),
    ("port=", "p", "Port to run test server on (dev mode only)"),
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
], share_with=["pavelib.utils.tests.utils.clean_reports_dir"])
@timed
def test_js(options):
    """
    Run the JavaScript tests
    """
    mode = getattr(options, 'mode', 'run')
    port = None
    skip_clean = getattr(options, 'skip_clean', False)

    if mode == 'run':
        suite = getattr(options, 'suite', 'all')
        coverage = getattr(options, 'coverage', False)
    elif mode == 'dev':
        suite = getattr(options, 'suite', None)
        coverage = False
        port = getattr(options, 'port', None)
    else:
        sys.stderr.write("Invalid mode. Please choose 'dev' or 'run'.")
        return

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


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
    ("coverage", "c", "Run test under coverage"),
])
@timed
def test_js_run(options):
    """
    Run the JavaScript tests and print results to the console
    """
    options.mode = 'run'
    test_js(options)


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
    ("port=", "p", "Port to run test server on"),
])
@timed
def test_js_dev(options):
    """
    Run the JavaScript tests in your default browsers
    """
    options.mode = 'dev'
    test_js(options)


@task
@needs('pavelib.prereqs.install_coverage_prereqs')
@cmdopts([
    ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
], share_with=['coverage'])
@timed
def diff_coverage(options):
    """
    Build the diff coverage reports
    """
    compare_branch = options.get('compare_branch', 'origin/master')

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []

    for filepath in Env.REPORT_DIR.walk():
        if bool(re.match(r'^coverage.*\.xml$', filepath.basename())):
            xml_reports.append(filepath)

    if not xml_reports:
        err_msg = colorize(
            'red',
            "No coverage info found.  Run `paver test` before running "
            "`paver coverage`.\n"
        )
        sys.stderr.write(err_msg)
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(Env.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        # The --diff-range-notation parameter is a workaround for https://github.com/Bachmann1234/diff_cover/issues/153
        sh(
            "diff-cover {xml_report_str} --diff-range-notation '..' --compare-branch={compare_branch} "
            "--html-report {diff_html_path}".format(
                xml_report_str=xml_report_str,
                compare_branch=compare_branch,
                diff_html_path=diff_html_path,
            )
        )

        print("\n")
