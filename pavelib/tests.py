"""
Unit test tasks
"""
import re
import os
import sys
from paver.easy import sh, task, cmdopts, needs
from pavelib.utils.test import suites
from pavelib.utils.envs import Env
from pavelib.utils.timer import timed
from pavelib.utils.passthrough_opts import PassthroughTask
from optparse import make_option

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test-id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail-fast", "x", "Fail suite on first failed test"),
    ("fasttest", "a", "Run without collectstatic"),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    ('processes=', 'p', 'number of processes to use running tests'),
    make_option('-r', '--randomize', action='store_true', help='run the tests in a random order'),
    make_option('--no-randomize', action='store_false', dest='randomize', help="don't run the tests in a random order"),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option(
        '--disable-migrations',
        action='store_true',
        dest='disable_migrations',
        help="Create tables directly from apps' models. Can also be used by exporting DISABLE_MIGRATIONS=1."
    ),
    make_option(
        '--enable-migrations',
        action='store_false',
        dest='disable_migrations',
        help="Create tables by applying migrations."
    ),
    ("fail_fast", None, "deprecated in favor of fail-fast"),
    ("test_id=", None, "deprecated in favor of test-id"),
    ('cov_args=', None, 'deprecated in favor of cov-args'),
    make_option(
        "-e", "--extra_args", default="",
        help="deprecated, pass extra options directly in the paver commandline"
    ),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
], share_with=['pavelib.utils.test.utils.clean_reports_dir'])
@PassthroughTask
@timed
def test_system(options, passthrough_options):
    """
    Run tests on our djangoapps for lms and cms
    """
    system = getattr(options, 'system', None)
    test_id = getattr(options, 'test_id', None)

    if test_id:
        if not system:
            system = test_id.split('/')[0]
        if system in ['common', 'openedx']:
            system = 'lms'
        options.test_system['test_id'] = test_id

    if test_id or system:
        system_tests = [suites.SystemTestSuite(
            system,
            passthrough_options=passthrough_options,
            **options.test_system
        )]
    else:
        system_tests = []
        for syst in ('cms', 'lms'):
            system_tests.append(suites.SystemTestSuite(
                syst,
                passthrough_options=passthrough_options,
                **options.test_system
            ))

    test_suite = suites.PythonTestSuite(
        'python tests',
        subsuites=system_tests,
        passthrough_options=passthrough_options,
        **options.test_system
    )
    test_suite.run()


@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("lib=", "l", "lib to test"),
    ("test-id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail-fast", "x", "Run only failed tests"),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    ('cov_args=', None, 'deprecated in favor of cov-args'),
    make_option(
        '-e', '--extra_args', default='',
        help='deprecated, pass extra options directly in the paver commandline'
    ),
    ("fail_fast", None, "deprecated in favor of fail-fast"),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
    ("test_id=", None, "deprecated in favor of test-id"),
], share_with=['pavelib.utils.test.utils.clean_reports_dir'])
@PassthroughTask
@timed
def test_lib(options, passthrough_options):
    """
    Run tests for common/lib/ and pavelib/ (paver-tests)
    """
    lib = getattr(options, 'lib', None)
    test_id = getattr(options, 'test_id', lib)

    if test_id:
        if '/' in test_id:
            lib = '/'.join(test_id.split('/')[0:3])
        else:
            lib = 'common/lib/' + test_id.split('.')[0]
        options.test_lib['test_id'] = test_id
        lib_tests = [suites.LibTestSuite(
            lib,
            passthrough_options=passthrough_options,
            **options.test_lib
        )]
    else:
        lib_tests = [
            suites.LibTestSuite(
                d,
                passthrough_options=passthrough_options,
                **options.test_lib
            ) for d in Env.LIB_TEST_DIRS
        ]

    test_suite = suites.PythonTestSuite(
        'python tests',
        subsuites=lib_tests,
        passthrough_options=passthrough_options,
        **options.test_lib
    )
    test_suite.run()


@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("failed", "f", "Run only failed tests"),
    ("fail-fast", "x", "Run only failed tests"),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option(
        '--disable-migrations',
        action='store_true',
        dest='disable_migrations',
        help="Create tables directly from apps' models. Can also be used by exporting DISABLE_MIGRATIONS=1."
    ),
    ('cov_args=', None, 'deprecated in favor of cov-args'),
    make_option(
        '-e', '--extra_args', default='',
        help='deprecated, pass extra options directly in the paver commandline'
    ),
    ("fail_fast", None, "deprecated in favor of fail-fast"),
])
@PassthroughTask
@timed
def test_python(options, passthrough_options):
    """
    Run all python tests
    """
    python_suite = suites.PythonTestSuite(
        'Python Tests',
        passthrough_options=passthrough_options,
        **options.test_python
    )
    python_suite.run()


@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("suites", "s", "List of unit test suites to run. (js, lib, cms, lms)"),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    ('cov_args=', None, 'deprecated in favor of cov-args'),
    make_option(
        '-e', '--extra_args', default='',
        help='deprecated, pass extra options directly in the paver commandline'
    ),
])
@PassthroughTask
@timed
def test(options, passthrough_options):
    """
    Run all tests
    """
    # Subsuites to be added to the main suite
    python_suite = suites.PythonTestSuite(
        'Python Tests',
        passthrough_options=passthrough_options,
        **options.test
    )
    js_suite = suites.JsTestSuite('JS Tests', mode='run', with_coverage=True)

    # Main suite to be run
    all_unittests_suite = suites.TestSuite('All Tests', subsuites=[js_suite, python_suite])
    all_unittests_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
    ("compare_branch=", None, "deprecated in favor of compare-branch"),
])
@timed
def coverage():
    """
    Build the html, xml, and diff coverage reports
    """
    report_dir = Env.REPORT_DIR
    rcfile = Env.PYTHON_COVERAGERC

    if not (report_dir / '.coverage').isfile():
        # This may be that the coverage files were generated using -p,
        # try to combine them to the one file that we need.
        sh("coverage combine --rcfile={}".format(rcfile))

    if not os.path.getsize(report_dir / '.coverage') > 50:
        # Check if the .coverage data file is larger than the base file,
        # because coverage combine will always at least make the "empty" data
        # file even when there isn't any data to be combined.
        err_msg = colorize(
            'red',
            "No coverage info found.  Run `paver test` before running "
            "`paver coverage`.\n"
        )
        sys.stderr.write(err_msg)
        return

    # Generate the coverage.py XML report
    sh("coverage xml --rcfile={}".format(rcfile))
    # Generate the coverage.py HTML report
    sh("coverage html --rcfile={}".format(rcfile))
    diff_coverage()  # pylint: disable=no-value-for-parameter


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
    ("compare_branch=", None, "deprecated in favor of compare-branch"),
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
        sh(
            "diff-cover {xml_report_str} --compare-branch={compare_branch} "
            "--html-report {diff_html_path}".format(
                xml_report_str=xml_report_str,
                compare_branch=compare_branch,
                diff_html_path=diff_html_path,
            )
        )

        print "\n"
