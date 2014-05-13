"""
Unit test tasks
"""
import os
import sys
from paver.easy import sh, task, cmdopts, needs
from pavelib.utils.test import suites
from pavelib.utils.test import utils as test_utils
from pavelib.utils.envs import Env

__test__ = False  # do not collect


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
    ("fasttest", "a", "Run without collectstatic")
])
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
    }

    if test_id:
        system = test_id.split('/')[0]
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
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("lib=", "l", "lib to test"),
    ("test_id=", "t", "Test id"),
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
])
def test_lib(options):
    """
    Run tests for common/lib/
    """
    lib = getattr(options, 'lib', None)
    test_id = getattr(options, 'test_id', lib)

    opts = {
        'failed_only': getattr(options, 'failed', None),
        'fail_fast': getattr(options, 'fail_fast', None),
    }

    if test_id:
        lib = '/'.join(test_id.split('/')[0:3])
        opts['test_id'] = test_id
        lib_tests = [suites.LibTestSuite(lib, **opts)]
    else:
        lib_tests = [suites.LibTestSuite(d, **opts) for d in Env.LIB_TEST_DIRS]

    test_suite = suites.PythonTestSuite('python tests', subsuites=lib_tests, **opts)
    test_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("failed", "f", "Run only failed tests"),
    ("fail_fast", "x", "Run only failed tests"),
])
def test_python():
    """
    Run all python tests
    """
    python_suite = suites.PythonTestSuite('Python Tests')
    python_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
def test_i18n():
    """
    Run all i18n tests
    """
    i18n_suite = suites.I18nTestSuite('i18n')
    i18n_suite.run()


@task
@needs('pavelib.prereqs.install_prereqs')
def test():
    """
    Run all tests
    """
    # Subsuites to be added to the main suite
    python_suite = suites.PythonTestSuite('Python Tests')
    i18n_suite = suites.I18nTestSuite('i18n')
    js_suite = suites.JsTestSuite('JS Tests', mode='run', with_coverage=True)

    # Main suite to be run
    all_unittests_suite = suites.TestSuite('All Tests', subsuites=[i18n_suite, js_suite, python_suite])
    all_unittests_suite.run(with_build_docs=True)


@task
def coverage():
    """
    Build the html, xml, and diff coverage reports
    """
    for directory in Env.LIB_TEST_DIRS:
        report_dir = os.path.join(Env.REPORT_DIR, directory)

        if os.path.isfile(os.path.join(report_dir, '.coverage')):
            # Generate the coverage.py HTML report
            sh("coverage html --rcfile={dir}/.coveragerc".format(dir=directory))

            # Generate the coverage.py XML report
            sh("coverage xml -o {report_dir}/coverage.xml --rcfile={dir}/.coveragerc".format(
                report_dir=report_dir,
                dir=directory
            ))

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []

    for subdir, _dirs, files in os.walk(Env.REPORT_DIR):
        if 'coverage.xml' in files:
            xml_reports.append(os.path.join(subdir, 'coverage.xml'))

    if len(xml_reports) < 1:
        err_msg = test_utils.colorize(
            "No coverage info found.  Run `paver test` before running `paver coverage`.",
            'RED'
        )
        sys.stderr.write(err_msg)
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(Env.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        sh("diff-cover {xml_report_str} --html-report {diff_html_path}".format(
            xml_report_str=xml_report_str, diff_html_path=diff_html_path))
        sh("diff-cover {xml_report_str}".format(xml_report_str=xml_report_str))
        print("\n")
