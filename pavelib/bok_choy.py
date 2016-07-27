"""
Run acceptance tests that use the bok-choy framework
http://bok-choy.readthedocs.org/en/latest/
"""
from paver.easy import task, needs, cmdopts, sh
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite, Pa11yCrawler
from pavelib.utils.test.bokchoy_options import (
    BOKCHOY_OPTS,
    PA11Y_HTML,
    PA11Y_COURSE_KEY,
    PA11Y_FETCH_COURSE,
)
from pavelib.utils.envs import Env
from pavelib.utils.test.utils import check_firefox_version
from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.timer import timed
from optparse import make_option
import os

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

    if validate_firefox:
        check_firefox_version()

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
    options.test_a11y.coveragerc = Env.BOK_CHOY_A11Y_COVERAGERC
    options.test_a11y.extra_args = options.get('extra_args', '') + ' -a "a11y" '
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


@needs('pavelib.prereqs.install_prereqs', 'get_test_course')
@cmdopts(
    BOKCHOY_OPTS + [PA11Y_HTML, PA11Y_COURSE_KEY, PA11Y_FETCH_COURSE],
    share_with = ['get_test_course', 'prepare_bokchoy_run', 'load_courses']
)
@PassthroughTask
@timed
def pa11ycrawler(options, passthrough_options):
    """
    Runs pa11ycrawler against the demo-test-course to generates accessibility
    reports. (See https://github.com/edx/demo-test-course)

    Note: Like the bok-choy tests, this can be used with the `serversonly`
    flag to get an environment running. The setup for this is the same as
    for bok-choy tests, only test course is imported as well.
    """
    # Modify the options object directly, so that any subsequently called tasks
    # that share with this task get the modified options
    options.pa11ycrawler.report_dir = Env.PA11YCRAWLER_REPORT_DIR
    options.pa11ycrawler.coveragerc = Env.PA11YCRAWLER_COVERAGERC
    options.pa11ycrawler.should_fetch_course = getattr(
        options,
        'should_fetch_course',
        not options.get('fasttest')
    )
    options.pa11ycrawler.course_key = getattr(options, 'course-key', "course-v1:edX+Test101+course")
    test_suite = Pa11yCrawler('a11y_crawler', passthrough_options=passthrough_options, **options.pa11ycrawler)
    test_suite.run()

    if getattr(options, 'with_html', False):
        test_suite.generate_html_reports()


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
    print msg
    test_suite.run()


def parse_coverage(report_dir, coveragerc):
    """
    Generate coverage reports for bok-choy or a11y tests
    """
    report_dir.makedirs_p()

    msg = colorize('green', "Combining coverage reports")
    print msg

    sh("coverage combine --rcfile={}".format(coveragerc))

    msg = colorize('green', "Generating coverage reports")
    print msg

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


@task
@timed
def pa11ycrawler_coverage():
    """
    Generate coverage reports for bok-choy tests
    """
    parse_coverage(
        Env.PA11YCRAWLER_REPORT_DIR,
        Env.PA11YCRAWLER_COVERAGERC
    )
