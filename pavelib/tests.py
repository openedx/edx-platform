"""
Unit test tasks
"""


import os
import re
import sys
from optparse import make_option  # pylint: disable=deprecated-module

from paver.easy import cmdopts, needs, sh, task, call_task

from pavelib.utils.envs import Env
from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.test import suites
from pavelib.utils.timer import timed

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
    ("fail-fast", "x", "Fail suite on first failed test"),
    ("fasttest", "a", "Run without collectstatic"),
    make_option(
        "--django_version", dest="django_version",
        help="Run against which Django version (3.2)."
    ),
    make_option(
        "--eval-attr", dest="eval_attr",
        help="Only run tests matching given attribute expression."
    ),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    make_option('-p', '--processes', dest='processes', default=0, help='number of processes to use running tests'),
    make_option('-r', '--randomize', action='store_true', help='run the tests in a random order'),
    make_option('--no-randomize', action='store_false', dest='randomize', help="don't run the tests in a random order"),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option(
        "--disable_capture", action="store_true", dest="disable_capture",
        help="Disable capturing of stdout/stderr"
    ),
    make_option(
        "--disable-coverage", action="store_false", dest="with_coverage",
        help="Run the unit tests directly through pytest, NOT coverage"
    ),
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
    make_option(
        '--disable_courseenrollment_history',
        action='store_true',
        dest='disable_courseenrollment_history',
        help="Disable history on student.CourseEnrollent. Can also be used by exporting"
             "DISABLE_COURSEENROLLMENT_HISTORY=1."
    ),
    make_option(
        '--enable_courseenrollment_history',
        action='store_false',
        dest='disable_courseenrollment_history',
        help="Enable django-simple-history on student.CourseEnrollment."
    ),
    make_option(
        '--xdist_ip_addresses',
        dest='xdist_ip_addresses',
        help="Comma separated string of ip addresses to shard tests to via xdist."
    ),
    make_option(
        '--with-wtw',
        dest='with_wtw',
        action='store',
        help="Only run tests based on the lines changed relative to the specified branch"
    ),
], share_with=[
    'pavelib.utils.test.utils.clean_reports_dir',
])
@PassthroughTask
@timed
def test_system(options, passthrough_options):
    """
    Run tests on our djangoapps for lms and cms
    """
    system = getattr(options, 'system', None)
    test_id = getattr(options, 'test_id', None)
    django_version = getattr(options, 'django_version', None)

    assert system in (None, 'lms', 'cms')
    assert django_version in (None, '3.2')

    if hasattr(options.test_system, 'with_wtw'):
        call_task('fetch_coverage_test_selection_data', options={
            'compare_branch': options.test_system.with_wtw
        })

    if test_id:
        # Testing a single test ID.
        # Ensure the proper system for the test id.
        if not system:
            system = test_id.split('/')[0]
        if system in ['common', 'openedx']:
            system = 'lms'
        system_tests = [suites.SystemTestSuite(
            system,
            passthrough_options=passthrough_options,
            **options.test_system
        )]
    else:
        # Testing a single system -or- both systems.
        if system:
            systems = [system]
        else:
            # No specified system or test_id, so run all tests of both systems.
            systems = ['cms', 'lms']
        system_tests = []
        for syst in systems:
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
        "--django_version", dest="django_version",
        help="Run against which Django version (3.2)."
    ),
    make_option(
        "--eval-attr", dest="eval_attr",
        help="Only run tests matching given attribute expression."
    ),
    make_option(
        '-c', '--cov-args', default='',
        help='adds as args to coverage for the test run'
    ),
    ('skip-clean', 'C', 'skip cleaning repository before running tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option(
        "--disable_capture", action="store_true", dest="disable_capture",
        help="Disable capturing of stdout/stderr"
    ),
    make_option(
        "--disable-coverage", action="store_false", dest="with_coverage",
        help="Run the unit tests directly through pytest, NOT coverage"
    ),
    make_option(
        '--xdist_ip_addresses',
        dest='xdist_ip_addresses',
        help="Comma separated string of ip addresses to shard tests to via xdist."
    ),
    make_option('-p', '--processes', dest='processes', default=0, help='number of processes to use running tests'),
    make_option('-r', '--randomize', action='store_true', help='run the tests in a random order'),
], share_with=['pavelib.utils.test.utils.clean_reports_dir'])
@PassthroughTask
@timed
def test_lib(options, passthrough_options):
    """
    Run tests for pavelib/ (paver-tests)
    """
    lib = getattr(options, 'lib', None)
    test_id = getattr(options, 'test_id', lib)
    django_version = getattr(options, 'django_version', None)

    assert django_version in (None, '3.2')

    if test_id:
        # Testing a single test id.
        if '/' in test_id:
            lib = '/'.join(test_id.split('/')[0:3])
        else:
            lib = 'pavelib/paver_tests' + test_id.split('.')[0]
        options.test_lib['test_id'] = test_id
        lib_tests = [suites.LibTestSuite(
            lib,
            passthrough_options=passthrough_options,
            **options.test_lib
        )]
    else:
        # Testing all tests within pavelib/paver_tests dir.
        lib_tests = [
            suites.LibTestSuite(
                d,
                passthrough_options=passthrough_options,
                append_coverage=(i != 0),
                **options.test_lib
            ) for i, d in enumerate(Env.LIB_TEST_DIRS)
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
    make_option(
        '--disable_courseenrollment_history',
        action='store_true',
        dest='disable_courseenrollment_history',
        help="Disable history on student.CourseEnrollent. Can also be used by exporting"
             "DISABLE_COURSEENROLLMENT_HISTORY=1."
    ),
    make_option(
        '--enable_courseenrollment_history',
        action='store_false',
        dest='disable_courseenrollment_history',
        help="Enable django-simple-history on student.CourseEnrollment."
    ),
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
@needs('pavelib.prereqs.install_coverage_prereqs')
@cmdopts([
    ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
    ("rcfile=", "c", "Coveragerc file to use, defaults to .coveragerc"),
])
@timed
def coverage(options):
    """
    Build the html, xml, and diff coverage reports
    """
    report_dir = Env.REPORT_DIR
    rcfile = getattr(options.coverage, 'rcfile', Env.PYTHON_COVERAGERC)

    combined_report_file = report_dir / '{}.coverage'.format(os.environ.get('TEST_SUITE', ''))

    if not combined_report_file.isfile():
        # This may be that the coverage files were generated using -p,
        # try to combine them to the one file that we need.
        sh(f"coverage combine --rcfile={rcfile}")

    if not os.path.getsize(combined_report_file) > 50:
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
    sh(f"coverage xml --rcfile={rcfile}")
    # Generate the coverage.py HTML report
    sh(f"coverage html --rcfile={rcfile}")
    diff_coverage()  # pylint: disable=no-value-for-parameter


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
