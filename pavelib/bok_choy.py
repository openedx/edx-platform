"""
Run acceptance tests that use the bok-choy framework
http://bok-choy.readthedocs.org/en/latest/
"""
from paver.easy import task, needs, cmdopts, sh
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite
from pavelib.utils.envs import Env
from pavelib.utils.test.utils import check_firefox_version
from optparse import make_option
import os

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name

__test__ = False  # do not collect


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ('test_spec=', 't', 'Specific test to run'),
    ('fasttest', 'a', 'Skip some setup'),
    ('serversonly', 'r', 'Prepare suite and leave servers running'),
    ('testsonly', 'o', 'Assume servers are running and execute tests only'),
    ('extra_args=', 'e', 'adds as extra args to the test command'),
    ('default_store=', 's', 'Default modulestore'),
    ('test_dir=', 'd', 'Directory for finding tests (relative to common/test/acceptance)'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
    make_option("--pdb", action="store_true", help="Drop into debugger on failures or errors"),
    make_option("--skip_firefox_version_validation", action='store_false', dest="validate_firefox_version")
])
def test_bokchoy(options):
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

    opts = {
        'test_spec': getattr(options, 'test_spec', None),
        'fasttest': getattr(options, 'fasttest', False),
        'serversonly': getattr(options, 'serversonly', False),
        'testsonly': getattr(options, 'testsonly', False),
        'default_store': getattr(options, 'default_store', 'split'),
        'verbosity': getattr(options, 'verbosity', 2),
        'extra_args': getattr(options, 'extra_args', ''),
        'pdb': getattr(options, 'pdb', False),
        'test_dir': getattr(options, 'test_dir', 'tests'),
    }
    run_bokchoy(**opts)


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ('test_spec=', 't', 'Specific test to run'),
    ('fasttest', 'a', 'Skip some setup'),
    ('imports_dir=', 'd', 'Directory containing (un-archived) courses to be imported'),
    ('default_store=', 's', 'Default modulestore'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
])
def perf_report_bokchoy(options):
    """
    Generates a har file for with page performance info.
    """
    opts = {
        'test_spec': getattr(options, 'test_spec', None),
        'fasttest': getattr(options, 'fasttest', False),
        'default_store': getattr(options, 'default_store', 'split'),
        'imports_dir': getattr(options, 'imports_dir', None),
        'verbosity': getattr(options, 'verbosity', 2),
        'test_dir': 'performance',
    }
    run_bokchoy(**opts)


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
    print(msg)
    test_suite.run()


@task
def bokchoy_coverage():
    """
    Generate coverage reports for bok-choy tests
    """
    Env.BOK_CHOY_REPORT_DIR.makedirs_p()
    coveragerc = Env.BOK_CHOY_COVERAGERC

    msg = colorize('green', "Combining coverage reports")
    print(msg)

    sh("coverage combine --rcfile={}".format(coveragerc))

    msg = colorize('green', "Generating coverage reports")
    print(msg)

    sh("coverage html --rcfile={}".format(coveragerc))
    sh("coverage xml --rcfile={}".format(coveragerc))
    sh("coverage report --rcfile={}".format(coveragerc))
