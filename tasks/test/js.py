"""
Javascript test tasks
"""
from __future__ import print_function
import sys
from invoke import task, Collection
from tasks.utils.test.suites import JsTestSuite
from tasks.utils.test.suites.js_suite import JS_TEST_IDS
from tasks.utils.envs import Env

__test__ = False  # do not collect

ns = Collection('js')


@task('prereqs.install', positional=["suite"], help={
    'suite': "Test suite to run",
    'mode': "dev or run",
    'coverage': "Run test under coverage",
})
def test_js(suite=None, mode="run", coverage=False):
    """
    Run the JavaScript tests
    """
    if not mode in ("dev", "run"):
        sys.stderr.write("Invalid mode. Please choose 'dev' or 'run'.")
        return

    if mode == 'run':
        suite = suite or "all"

    if suite != 'all' and suite not in JS_TEST_IDS:
        sys.stderr.write(
            "Unknown test suite. Please choose from ({suites})\n".format(
                suites=", ".join(JS_TEST_IDS.keys())
            )
        )
        return

    test_suite = JsTestSuite(suite, mode=mode, with_coverage=coverage)
    test_suite.run()

ns.add_task(test_js, 'run', default=True)


@task(help={
    'suite': "Test suite to run",
})
def test_js_dev(suite):
    """
    Run the JavaScript tests in your default browsers
    """
    test_js(suite=suite, mode="dev")

ns.add_task(test_js_dev, "dev")
