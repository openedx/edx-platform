"""
Javascript test tasks
"""
from __future__ import print_function
import sys
from invoke import task
from tasks.utils.test.suites import JsTestSuite
from tasks.utils.envs import Env

__test__ = False  # do not collect


@task('prereqs.install',
    help={'suite': "Test suite to run",
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

    if (suite != 'all') and (suite not in Env.JS_TEST_ID_KEYS):
        sys.stderr.write(
            "Unknown test suite. Please choose from ({suites})\n".format(
                suites=", ".join(Env.JS_TEST_ID_KEYS)
            )
        )
        return

    test_suite = JsTestSuite(suite, mode=mode, with_coverage=coverage)
    test_suite.run()


@task(
    help={'suite': "Test suite to run",
          'coverage': "Run test under coveraage",
})
def test_js_run(suite=None, coverage=False):
    """
    Run the JavaScript tests and print results to the console
    """
    test_js(suite=suite, coverage=coverage, mode="run")


@task(
    help={'suite': "Test suite to run",}
)
def test_js_dev(suite):
    """
    Run the JavaScript tests in your default browsers
    """
    test_js(suite=suite, mode="dev")
