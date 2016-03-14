"""
Unit test tasks
"""
import os
import sys
from paver.easy import sh, task, cmdopts, needs, call_task
from pavelib.utils.test import suites
from pavelib.utils.envs import Env
from optparse import make_option

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


@task
@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Fail suite on first failed test"),
    ("fasttest", "a", "Run without collectstatic"),
    ('extra_args=', 'e', 'adds as extra args to the test command'),
    ('cov_args=', 'c', 'adds as args to coverage for the test run'),
    ('skip_clean', 'C', 'skip cleaning repository before running tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option("--pdb", action="store_true", help="Drop into debugger on failures or errors"),
], share_with=['pavelib.utils.test.utils.clean_reports_dir'])
def test_system(options):
    """
    Run tests on our djangoapps for lms and cms
    """
    system = getattr(options, 'system', None)
    test_id = getattr(options, 'test_id', None)

    opts = {
        'failed_only': getattr(options, 'failed', None),
        'fail_fast': getattr(options, 'fail_fast', None),
        'fasttest': getattr(options, 'fasttest', None),
        'verbosity': getattr(options, 'verbosity', 1),
        'extra_args': getattr(options, 'extra_args', ''),
        'cov_args': getattr(options, 'cov_args', ''),
        'skip_clean': getattr(options, 'skip_clean', False),
        'pdb': getattr(options, 'pdb', False),
    }

    if test_id:
        if not system:
            system = test_id.split('/')[0]
        if system in ['common', 'openedx']:
            system = 'lms'
        opts['test_id'] = test_id

    if test_id or system:
        system_tests = [suites.SystemTestSuite(system, **opts)]
    else:
        system_tests = []
        for syst in ('cms', 'lms'):
            system_tests.append(suites.SystemTestSuite(syst, **opts))

    test_suite = suites.PythonTestSuite('python tests', subsuites=system_tests, **opts)
    test_suite.run()


@task
@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("lib=", "l", "lib to test"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
    ('extra_args=', 'e', 'adds as extra args to the test command'),
    ('cov_args=', 'c', 'adds as args to coverage for the test run'),
    ('skip_clean', 'C', 'skip cleaning repository before running tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option("--pdb", action="store_true", help="Drop into debugger on failures or errors"),
], share_with=['pavelib.utils.test.utils.clean_reports_dir'])
def test_lib(options):
    """
    Run tests for common/lib/ and pavelib/ (paver-tests)
    """
    lib = getattr(options, 'lib', None)
    test_id = getattr(options, 'test_id', lib)

    opts = {
        'failed_only': getattr(options, 'failed', None),
        'fail_fast': getattr(options, 'fail_fast', None),
        'verbosity': getattr(options, 'verbosity', 1),
        'extra_args': getattr(options, 'extra_args', ''),
        'cov_args': getattr(options, 'cov_args', ''),
        'skip_clean': getattr(options, 'skip_clean', False),
        'pdb': getattr(options, 'pdb', False),
    }

    if test_id:
        if '/' in test_id:
            lib = '/'.join(test_id.split('/')[0:3])
        else:
            lib = 'common/lib/' + test_id.split('.')[0]
        opts['test_id'] = test_id
        lib_tests = [suites.LibTestSuite(lib, **opts)]
    else:
        lib_tests = [suites.LibTestSuite(d, **opts) for d in Env.LIB_TEST_DIRS]

    test_suite = suites.PythonTestSuite('python tests', subsuites=lib_tests, **opts)
    test_suite.run()


@task
@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
    ('extra_args=', 'e', 'adds as extra args to the test command'),
    ('cov_args=', 'c', 'adds as args to coverage for the test run'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option("--pdb", action="store_true", help="Drop into debugger on failures or errors"),
])
def test_python(options):
    """
    Run all python tests
    """
    opts = {
        'failed_only': getattr(options, 'failed', None),
        'fail_fast': getattr(options, 'fail_fast', None),
        'verbosity': getattr(options, 'verbosity', 1),
        'extra_args': getattr(options, 'extra_args', ''),
        'cov_args': getattr(options, 'cov_args', ''),
        'pdb': getattr(options, 'pdb', False),
    }

    python_suite = suites.PythonTestSuite('Python Tests', **opts)
    python_suite.run()


@task
@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("suites", "s", "List of unit test suites to run. (js, lib, cms, lms)"),
    ('extra_args=', 'e', 'adds as extra args to the test command'),
    ('cov_args=', 'c', 'adds as args to coverage for the test run'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity", default=1),
    make_option("--pdb", action="store_true", help="Drop into debugger on failures or errors"),
])
def test(options):
    """
    Run all tests
    """
    opts = {
        'verbosity': getattr(options, 'verbosity', 1),
        'extra_args': getattr(options, 'extra_args', ''),
        'cov_args': getattr(options, 'cov_args', ''),
        'pdb': getattr(options, 'pdb', False),
    }
    # Subsuites to be added to the main suite
    python_suite = suites.PythonTestSuite('Python Tests', **opts)
    js_suite = suites.JsTestSuite('JS Tests', mode='run', with_coverage=True)

    # Main suite to be run
    all_unittests_suite = suites.TestSuite('All Tests', subsuites=[js_suite, python_suite])
    all_unittests_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("compare_branch=", "b", "Branch to compare against, defaults to origin/master"),
])
def coverage(options):
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
    call_task('diff_coverage', options=dict(options))


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("compare_branch=", "b", "Branch to compare against, defaults to origin/master"),
])
def diff_coverage(options):
    """
    Build the diff coverage reports
    """
    compare_branch = getattr(options, 'compare_branch', 'origin/master')

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []

    for filepath in Env.REPORT_DIR.walk():
        if filepath.basename() == 'coverage.xml':
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
