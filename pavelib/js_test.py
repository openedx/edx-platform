"""
Javascript test tasks
"""


import sys

from paver.easy import cmdopts, needs, task

from pavelib.utils.envs import Env
from pavelib.utils.test.suites import JestSnapshotTestSuite, JsTestSuite
from pavelib.utils.timer import timed

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

    if (suite == 'jest-snapshot') or (suite == 'all'):
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
