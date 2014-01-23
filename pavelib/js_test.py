from paver.easy import *
from pavelib import assets, test_utils
import os

__test__ = False  # do not collect

JS_TEST_SUITES = {'lms': 'lms/static/js_test.yml',
                  'cms': 'cms/static/js_test.yml',
                  'cms-squire': 'cms/static/js_test_squire.yml',
                  'xmodule': 'common/lib/xmodule/xmodule/js/js_test.yml',
                  'common': 'common/static/js_test.yml',
                  }

# Turn relative paths to absolute paths from the repo root.
for key, val in JS_TEST_SUITES.iteritems():
    JS_TEST_SUITES[key] = os.path.join(assets.REPO_ROOT, val)

# Define the directory for coverage reports
JS_REPORT_DIR = os.path.join(assets.REPORT_DIR, 'javascript')

if not os.path.exists(JS_REPORT_DIR):
    os.makedirs(JS_REPORT_DIR)


# Given an environment (a key in `JS_TEST_SUITES`)
# return the path to the JavaScript test suite description
# If `env` is nil, return a string containing
# all available descriptions.
def test_suite(suite):

    if not suite:
        return ' '.join(JS_TEST_SUITES.values())
    else:
        return os.path.join(assets.REPO_ROOT, JS_TEST_SUITES[suite])


# Run the tests using js-test-tool
# See js-test-tool docs for description of different
# command line arguments
def js_test_tool(suite, command, do_coverage):
    suite_yml = test_suite(suite)
    xunit_report = os.path.join(JS_REPORT_DIR, 'javascript_xunit.xml')
    cmd = "js-test-tool {command} {suite} --use-firefox --timeout-sec 600 --xunit-report {xunit_report}".format(
        command=command, suite=suite_yml, xunit_report=xunit_report)

    if do_coverage:
        report_dir = os.path.join(JS_REPORT_DIR, 'coverage.xml')
        cmd += " --coverage-xml {report_dir}".format(report_dir=report_dir)

    test_utils.test_sh(cmd)


# Print a list of js_test commands for
# all available environments
def print_js_test_cmds(mode):
    for key, value in JS_TEST_SUITES.iteritems():
        print("    paver test_js --mode={mode} --system={key}".format(mode=mode, key=key))


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js_run(options):
    """
    Run the JavaScript tests and print results to the console
    """
    suite = getattr(options, 'suite', '')

    test_utils.clean_test_files()

    assets.compile_coffeescript(options)

    if not suite:
        print("Running all test suites.  To run a specific test suite, try:")
        print_js_test_cmds('run')
        js_test_tool(None, 'run', False)
    else:
        js_test_tool(suite, 'run', False)


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js(options):
    """
    Run the JavaScript tests and print results to the console
    """
    test_js_run(options)


@task
@cmdopts([
    ("suite=", "s", "Test suite to run"),
])
def test_js_dev(options):
    """
    Run the JavaScript tests in your default browser
    """
    suite = getattr(options, 'suite', '')

    test_utils.clean_test_files()

    assets.compile_coffeescript(options)

    if not suite:
        print("Error: No test suite specified.  Try one of these instead:")
        print_js_test_cmds('dev')
    else:
        js_test_tool(suite, 'dev', False)


@task
def test_js_coverage(options):
    """
    Run all JavaScript tests and collect coverage information
    """
    test_utils.clean_dir(JS_REPORT_DIR)
    test_utils.clean_test_files()

    assets.compile_coffeescript(options)

    js_test_tool(None, 'dev', True)
