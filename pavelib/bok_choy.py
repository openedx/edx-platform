"""
Run acceptance tests that use the bok-choy framework
http://bok-choy.readthedocs.org/en/latest/
"""
from paver.easy import task, needs, cmdopts, sh
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite, Pa11yCrawler
from pavelib.utils.envs import Env
from pavelib.utils.test.utils import check_firefox_version
from pavelib.utils.passthrough_opts import PassthroughTask
from optparse import make_option
import os

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect

BOKCHOY_OPTS = [
    ('test-spec=', 't', 'Specific test to run'),
    ('fasttest', 'a', 'Skip some setup'),
    ('skip-clean', 'C', 'Skip cleaning repository before running tests'),
    ('serversonly', 'r', 'Prepare suite and leave servers running'),
    ('testsonly', 'o', 'Assume servers are running and execute tests only'),
    ('default-store=', 's', 'Default modulestore'),
    ('test-dir=', 'd', 'Directory for finding tests (relative to common/test/acceptance)'),
    ('imports-dir=', 'i', 'Directory containing (un-archived) courses to be imported'),
    ('num-processes=', 'n', 'Number of test threads (for multiprocessing)'),
    ('verify-xss', 'x', 'Run XSS vulnerability tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
    make_option("--skip-firefox-version-validation", action='store_false', dest="validate_firefox_version"),
    make_option("--save-screenshots", action='store_true', dest="save_screenshots"),
    ('default_store=', None, 'deprecated in favor of default-store'),
    ('extra_args=', 'e', 'deprecated, pass extra options directly in the paver commandline'),
    ('imports_dir=', None, 'deprecated in favor of imports-dir'),
    ('num_processes=', None, 'deprecated in favor of num-processes'),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
    ('test_dir=', None, 'deprecated in favor of test-dir'),
    ('test_spec=', None, 'Specific test to run'),
    ('verify_xss', None, 'deprecated in favor of verify-xss'),
    make_option(
        "--skip_firefox_version_validation",
        action='store_false',
        dest="validate_firefox_version",
        help="deprecated in favor of --skip-firefox-version-validation"
    ),
    make_option(
        "--save_screenshots",
        action='store_true',
        dest="save_screenshots",
        help="deprecated in favor of save-screenshots"
    ),
]


def parse_bokchoy_opts(options, passthrough_options=None):
    """
    Parses bok choy options.

    Returns: dict of options.
    """
    if passthrough_options is None:
        passthrough_options = []

    return {
        'test_spec': getattr(options, 'test_spec', None),
        'fasttest': getattr(options, 'fasttest', False),
        'num_processes': int(getattr(options, 'num_processes', 1)),
        'verify_xss': getattr(options, 'verify_xss', os.environ.get('VERIFY_XSS', False)),
        'serversonly': getattr(options, 'serversonly', False),
        'testsonly': getattr(options, 'testsonly', False),
        'default_store': getattr(options, 'default_store', os.environ.get('DEFAULT_STORE', 'split')),
        'verbosity': getattr(options, 'verbosity', 2),
        'extra_args': getattr(options, 'extra_args', ''),
        'pdb': getattr(options, 'pdb', False),
        'test_dir': getattr(options, 'test_dir', 'tests'),
        'imports_dir': getattr(options, 'imports_dir', None),
        'save_screenshots': getattr(options, 'save_screenshots', False),
        'passthrough_options': passthrough_options
    }


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
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

    opts = parse_bokchoy_opts(options, passthrough_options)
    run_bokchoy(**opts)


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
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
    opts = parse_bokchoy_opts(options, passthrough_options)
    opts['report_dir'] = Env.BOK_CHOY_A11Y_REPORT_DIR
    opts['coveragerc'] = Env.BOK_CHOY_A11Y_COVERAGERC
    opts['extra_args'] = opts['extra_args'] + ' -a "a11y" '
    run_bokchoy(**opts)


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS)
@PassthroughTask
def perf_report_bokchoy(options, passthrough_options):
    """
    Generates a har file for with page performance info.
    """
    opts = parse_bokchoy_opts(options, passthrough_options)
    opts['test_dir'] = 'performance'

    run_bokchoy(**opts)


@needs('pavelib.prereqs.install_prereqs')
@cmdopts(BOKCHOY_OPTS + [
    ('with-html', 'w', 'Include html reports'),
    make_option('--course-key', help='Course key for test course'),
    make_option(
        "--fetch-course",
        action="store_true",
        dest="should_fetch_course",
        help='Course key for test course',
    ),
])
@PassthroughTask
def pa11ycrawler(options, passthrough_options):
    """
    Runs pa11ycrawler against the demo-test-course to generates accessibility
    reports. (See https://github.com/edx/demo-test-course)

    Note: Like the bok-choy tests, this can be used with the `serversonly`
    flag to get an environment running. The setup for this is the same as
    for bok-choy tests, only test course is imported as well.
    """
    opts = parse_bokchoy_opts(options, passthrough_options)
    opts['report_dir'] = Env.PA11YCRAWLER_REPORT_DIR
    opts['coveragerc'] = Env.PA11YCRAWLER_COVERAGERC
    opts['should_fetch_course'] = getattr(options, 'should_fetch_course', not opts['fasttest'])
    opts['course_key'] = getattr(options, 'course-key', "course-v1:edX+Test101+course")
    test_suite = Pa11yCrawler('a11y_crawler', **opts)
    test_suite.run()

    if getattr(options, 'with_html', False):
        test_suite.generate_html_reports()


def run_bokchoy(**opts):
    """
    Runs BokChoyTestSuite with the given options.
    """
    test_suite = BokChoyTestSuite('bok-choy', **opts)
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
def bokchoy_coverage():
    """
    Generate coverage reports for bok-choy tests
    """
    parse_coverage(
        Env.BOK_CHOY_REPORT_DIR,
        Env.BOK_CHOY_COVERAGERC
    )


@task
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
def pa11ycrawler_coverage():
    """
    Generate coverage reports for bok-choy tests
    """
    parse_coverage(
        Env.PA11YCRAWLER_REPORT_DIR,
        Env.PA11YCRAWLER_COVERAGERC
    )
