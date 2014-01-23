from paver.easy import *
from pavelib import assets, test_utils, paver_utils, prereqs, js_test, proc_utils
import os

__test__ = False  # do not collect

CLOBBER = []
CLOBBER.append([assets.REPORT_DIR, 'test_root/*_repo', 'test_root/staticfiles'])

TEST_TASK_DIRS = ['cms', 'lms']

dirs = os.listdir('common/lib')

for dir in dirs:
    if os.path.isdir(os.path.join('common/lib', dir)):
        TEST_TASK_DIRS.append(dir)


def run_under_coverage(cmd, root):
    cmd0, cmd_rest = cmd.split(" ", 1)
    # We use "python -m coverage" so that the proper python will run the importable coverage
    # rather than the coverage that OS path finds.

    cmd = "python -m coverage run --rcfile={root}/.coveragerc `which {cmd0}` {cmd_rest}".format(
        root=root, cmd0=cmd0, cmd_rest=cmd_rest)
    return cmd


def run_tests(system, report_dir, test_id=None):

    # If no test id is provided, we need to limit the test runner
    # to the Djangoapps we want to test.  Otherwise, it will
    # run tests on all installed packages.

    default_test_id = "{system}/djangoapps common/djangoapps".format(system=system)

    if system in ('lms', 'cms'):
        default_test_id += " {system}/lib".format(system=system)

    if not test_id:
        test_id = default_test_id

    # Handle "--failed" as a special case: we want to re-run only
    # the tests that failed within our Django apps
    elif test_id == '--failed':
        test_id = "{default_test_id} --failed".format(default_test_id=default_test_id)

    cmd = './manage.py {system} test {test_id} --traceback --settings=test --pythonpath=. '.format(
        system=system, test_id=test_id)

    test_utils.test_sh(run_under_coverage(cmd, system))


@task
def test_docs():
    """
    Run documentation tests
    """
    test_message = ("\nIf test fails, you shoud run 'paver doc --type=docs --verbose' and look at whole output and fix exceptions."
                    "(You shouldn't fix rst warnings and errors for this to pass, just get rid of exceptions.)\n"
                    )
    paver_utils.print_green(test_message)
    test_utils.test_sh('paver build_docs', discard_stdout=False)


@task
def clean_test_files():
    """
    Clean fixture files used by tests and .pyc files
    """
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name *.pyc -delete")


@task
def clean_reports_dir():
    """
    Clean coverage files, to ensure that we don't use stale data to generate reports.
    """
    sh("find {REPORT_DIR} -type f -delete".format(REPORT_DIR=assets.REPORT_DIR))


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test_id=", "t", "Test id"),
])
def test_system(options):
    """
    Run all django tests on our djangoapps for system
    """
    clean_test_files()
    prereqs.install_prereqs()

    setattr(options, 'env', 'test')
    assets.compile_assets(options)

    fasttest(options)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("test_id=", "t", "Test id"),
])
def fasttest(options):
    """
    Run the tests without running collectstatic
    """
    system = getattr(options, 'system', 'lms')
    test_id = getattr(options, 'test_id', None)

    report_dir = os.path.join(assets.REPORT_DIR, 'system')
    run_tests(system, report_dir, test_id)


@task
@cmdopts([
    ("lib=", "l", "lib to test"),
    ("test_id=", "t", "Test id"),
])
def test_lib(options):
    """
    Run tests for common lib
    """
    lib = getattr(options, 'lib', '')
    test_id = getattr(options, 'test_id', '')

    report_dir = os.path.join(assets.REPORT_DIR, lib)
    test_id_dir = os.path.join(assets.TEST_DIR, lib)

    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    if not os.path.exists(report_dir):
        os.makedirs(test_id_dir)

    test_ids = os.path.join(test_id_dir, '.noseids')

    clean_test_files()
    clean_reports_dir()
    prereqs.install_prereqs()

    if os.path.exists(os.path.join(report_dir, "nosetests.xml")):
        os.environ['NOSE_XUNIT_FILE'] = os.path.join(report_dir, "nosetests.xml")

    cmd = "nosetests --id-file={test_ids} {test_id}".format(
        test_ids=test_ids, test_id=test_id)

    proc_utils.write_stderr(paver_utils.colorize_red('\n---------------------------'))
    proc_utils.write_stderr(paver_utils.colorize_red(' Running tests for {lib} '.format(lib=lib)))
    proc_utils.write_stderr(paver_utils.colorize_red('--------------------------\n\n'))

    test_utils.test_sh(run_under_coverage(cmd, lib))


@task
@cmdopts([
    ("lib=", "l", "lib to test"),
])
def fasttest_lib(options):
    """
    Run tests for common lib (aliased for backwards compatibility)"
    Run all django tests on our djangoapps for system
    """
    test_lib(options)


@task
def test_python(options):
    """
    Run all python tests
    """
    for dir in TEST_TASK_DIRS:
        setattr(options, 'lib', dir)
        test_lib(options)


@task
def test(options):
    """
    Run all tests
    """
    test_docs(options)
    test_python(options)
    js_test.test_js_coverage(options)


@task
def coverage():
    """
    Build the html, xml, and diff coverage reports
    """
    for dir in TEST_TASK_DIRS:
        report_dir = os.path.join(assets.REPORT_DIR, dir)

        if os.path.isfile(os.path.join(report_dir, '.coverage')):
            # Generate the coverage.py HTML report
            sh("coverage html --rcfile={dir}/.coveragerc".format(dir=dir))

            # Generate the coverage.py XML report
            sh("coverage xml -o {report_dir}/coverage.xml --rcfile={dir}/.coveragerc".format(
                report_dir=report_dir, dir=dir))

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []

    for subdir, dirs, files in os.walk(assets.REPORT_DIR):
        if 'coverage.xml' in files:
            xml_reports.append(os.path.join(subdir, 'coverage.xml'))

    if len(xml_reports) < 1:
        paver_utils.print_red("No coverage info found.  Run `paver test` before running `paver coverage`.")
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(assets.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        sh("diff-cover {xml_report_str} --html-report {diff_html_path}".format(
            xml_report_str=xml_report_str, diff_html_path=diff_html_path))
        sh("diff-cover {xml_report_str}".format(xml_report_str=xml_report_str))
        print("\n")
