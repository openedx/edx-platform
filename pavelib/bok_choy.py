"""
Run acceptance tests that use the bok-choy framework
https://bok-choy.readthedocs.org/en/latest/
"""


import os

from paver.easy import cmdopts, needs, sh, task, call_task

from pavelib.utils.envs import Env
from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.test.bokchoy_options import BOKCHOY_OPTS
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite
from pavelib.utils.test.utils import check_firefox_version
from pavelib.utils.timer import timed

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
@timed
def test_bokchoy(options, passthrough_options):
    """
    Run acceptance tests that use the bok-choy framework.
    Skips some static asset steps if `fasttest` is True.
    Using 'serversonly' will prepare and run servers, leaving a process running in the terminal. At
        the same time, a user can open a separate terminal and use 'testsonly' for executing tests against
        those running servers.

    `test_spec` is a nose-style test specifier relative to the test directory
    Examples:
    - path/to/test.py
    - path/to/test.py:TestFoo
    - path/to/test.py:TestFoo.test_bar
    It can also be left blank to run all tests in the suite.
    """
    # Note: Bok Choy uses firefox if SELENIUM_BROWSER is not set. So we are using
    # firefox as the default here.
    using_firefox = (os.environ.get('SELENIUM_BROWSER', 'firefox') == 'firefox')
    validate_firefox = getattr(options, 'validate_firefox_version', using_firefox)
    options.test_bokchoy.coveragerc = options.get('coveragerc', None)

    if validate_firefox:
        check_firefox_version()

    if hasattr(options.test_bokchoy, 'with_wtw'):
        call_task('fetch_coverage_test_selection_data', options={
            'compare_branch': options.test_bokchoy.with_wtw
        })

    run_bokchoy(options.test_bokchoy, passthrough_options)


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
@timed
def test_a11y(options, passthrough_options):
    """
    Run accessibility tests that use the bok-choy framework.
    Skips some static asset steps if `fasttest` is True.
    Using 'serversonly' will prepare and run servers, leaving a process running in the terminal. At
        the same time, a user can open a separate terminal and use 'testsonly' for executing tests against
        those running servers.

    `test_spec` is a nose-style test specifier relative to the test directory
    Examples:
    - path/to/test.py
    - path/to/test.py:TestFoo
    - path/to/test.py:TestFoo.test_bar
    It can also be left blank to run all tests in the suite that are tagged
    with `@attr("a11y")`.
    """
    # Modify the options object directly, so that any subsequently called tasks
    # that share with this task get the modified options
    options.test_a11y.report_dir = Env.BOK_CHOY_A11Y_REPORT_DIR
    options.test_a11y.extra_args = options.get('extra_args', '') + ' -a "a11y" '
    options.test_a11y.coveragerc = options.get('coveragerc', None)
    run_bokchoy(options.test_a11y, passthrough_options)


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
@timed
def perf_report_bokchoy(options, passthrough_options):
    """
    Generates a har file for with page performance info.
    """
    # Modify the options object directly, so that any subsequently called tasks
    # that share with this task get the modified options
    options.perf_report_bokchoy.test_dir = 'performance'

    run_bokchoy(options.perf_report_bokchoy, passthrough_options)


def run_bokchoy(options, passthrough_options):
    """
    Runs BokChoyTestSuite with the given options.
    """
    test_suite = BokChoyTestSuite('bok-choy', passthrough_options=passthrough_options, **options)
    msg = colorize(
        'green',
        'Running tests using {default_store} modulestore.'.format(
            default_store=test_suite.default_store,
        )
    )
    print(msg)
    test_suite.run()


def parse_coverage(report_dir, coveragerc):
    """
    Generate coverage reports for bok-choy or a11y tests
    """
    report_dir.makedirs_p()

    msg = colorize('green', "Combining coverage reports")
    print(msg)

    sh("coverage combine --rcfile={}".format(coveragerc))

    msg = colorize('green', "Generating coverage reports")
    print(msg)

    sh("coverage html --rcfile={}".format(coveragerc))
    sh("coverage xml --rcfile={}".format(coveragerc))
    sh("coverage report --rcfile={}".format(coveragerc))


@task
@timed
def bokchoy_coverage():
    """
    Generate coverage reports for bok-choy tests
    """
    parse_coverage(
        Env.BOK_CHOY_REPORT_DIR,
        Env.BOK_CHOY_COVERAGERC
    )


@task
@timed
def a11y_coverage():
    """
    Generate coverage reports for a11y tests. Note that this coverage report
    is just a guideline to find areas that are missing tests.  If the view
    isn't 'covered', there definitely isn't a test for it.  If it is
    'covered', we are loading that page during the tests but not necessarily
    calling ``page.a11y_audit.check_for_accessibility_errors`` on it.
    """
    parse_coverage(
        Env.BOK_CHOY_A11Y_REPORT_DIR,
        Env.BOK_CHOY_A11Y_COVERAGERC
    )
