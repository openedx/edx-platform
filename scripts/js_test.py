"""
Javascript test tasks
"""

import click
import os
import re
import sys
import subprocess

from path import Path as path

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect


class Env:
    """
    Load information about the execution environment.
    """

    @staticmethod
    def repo_root():
        """
        Get the root of the git repository (edx-platform).

        This sometimes fails on Docker Devstack, so it's been broken
        down with some additional error handling.  It usually starts
        working within 30 seconds or so; for more details, see
        https://openedx.atlassian.net/browse/PLAT-1629 and
        https://github.com/docker/for-mac/issues/1509
        """

        file_path = path(__file__)
        attempt = 1
        while True:
            try:
                absolute_path = file_path.abspath()
                break
            except OSError:
                print(f'Attempt {attempt}/180 to get an absolute path failed')
                if attempt < 180:
                    attempt += 1
                    sleep(1)
                else:
                    print('Unable to determine the absolute path of the edx-platform repo, aborting')
                    raise
        return absolute_path.parent.parent

    # Root of the git repository (edx-platform)
    REPO_ROOT = repo_root()

    # Reports Directory
    REPORT_DIR = REPO_ROOT / 'reports'

    # Detect if in a Docker container, and if so which one
    FRONTEND_TEST_SERVER_HOST = os.environ.get('FRONTEND_TEST_SERVER_HOSTNAME', '0.0.0.0')
    USING_DOCKER = FRONTEND_TEST_SERVER_HOST != '0.0.0.0'

    # Configured browser to use for the js test suites
    SELENIUM_BROWSER = os.environ.get('SELENIUM_BROWSER', 'firefox')
    if USING_DOCKER:
        KARMA_BROWSER = 'ChromeDocker' if SELENIUM_BROWSER == 'chrome' else 'FirefoxDocker'
    else:
        KARMA_BROWSER = 'FirefoxNoUpdates'

    # Files used to run each of the js test suites
    # TODO:  Store this as a dict. Order seems to matter for some
    # reason. See issue TE-415.
    KARMA_CONFIG_FILES = [
        REPO_ROOT / 'cms/static/karma_cms.conf.js',
        REPO_ROOT / 'cms/static/karma_cms_squire.conf.js',
        REPO_ROOT / 'cms/static/karma_cms_webpack.conf.js',
        REPO_ROOT / 'lms/static/karma_lms.conf.js',
        REPO_ROOT / 'xmodule/js/karma_xmodule.conf.js',
        REPO_ROOT / 'xmodule/js/karma_xmodule_webpack.conf.js',
        REPO_ROOT / 'common/static/karma_common.conf.js',
        REPO_ROOT / 'common/static/karma_common_requirejs.conf.js',
    ]

    JS_TEST_ID_KEYS = [
        'cms',
        'cms-squire',
        'cms-webpack',
        'lms',
        'xmodule',
        'xmodule-webpack',
        'common',
        'common-requirejs',
        'jest-snapshot'
    ]

    JS_REPORT_DIR = REPORT_DIR / 'javascript'

    # Service variant (lms, cms, etc.) configured with an environment variable
    # We use this to determine which envs.json file to load.
    SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

    # If service variant not configured in env, then pass the correct
    # environment for lms / cms
    if not SERVICE_VARIANT:  # this will intentionally catch "";
        if any(i in sys.argv[1:] for i in ('cms', 'studio')):
            SERVICE_VARIANT = 'cms'
        else:
            SERVICE_VARIANT = 'lms'


# def clean_test_files():
#     """
#     Clean fixture files used by tests and .pyc files
#     """
#     # "git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads"
#     subprocess.run("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
#     # This find command removes all the *.pyc files that aren't in the .git
#     # directory.  See this blog post for more details:
#     # http://nedbatchelder.com/blog/201505/be_careful_deleting_files_around_git.html
#     subprocess.run(r"find . -name '.git' -prune -o -name '*.pyc' -exec rm {} \;")
#     subprocess.run("rm -rf test_root/log/auto_screenshots/*")
#     subprocess.run("rm -rf /tmp/mako_[cl]ms")


# def clean_dir(directory):
#     """
#     Delete all the files from the specified directory.
#     """
#     # We delete the files but preserve the directory structure
#     # so that coverage.py has a place to put the reports.
#     subprocess.run(f'find {directory} -type f -delete')


# @task
# @cmdopts([
#     ('skip-clean', 'C', 'skip cleaning repository before running tests'),
#     ('skip_clean', None, 'deprecated in favor of skip-clean'),
# ])

# def clean_reports_dir(options):
#     """
#     Clean coverage files, to ensure that we don't use stale data to generate reports.
#     """
#     if getattr(options, 'skip_clean', False):
#         print('--skip-clean is set, skipping...')
#         return

#     # We delete the files but preserve the directory structure
#     # so that coverage.py has a place to put the reports.
#     reports_dir = Env.REPORT_DIR.makedirs_p()
#     clean_dir(reports_dir)


class TestSuite:
    """
    TestSuite is a class that defines how groups of tests run.
    """
    def __init__(self, *args, **kwargs):
        self.root = args[0]
        self.subsuites = kwargs.get('subsuites', [])
        self.failed_suites = []
        self.verbosity = int(kwargs.get('verbosity', 1))
        self.skip_clean = kwargs.get('skip_clean', False)
        self.passthrough_options = kwargs.get('passthrough_options', [])

    def __enter__(self):
        """
        This will run before the test suite is run with the run_suite_tests method.
        If self.run_test is called directly, it should be run in a 'with' block to
        ensure that the proper context is created.

        Specific setup tasks should be defined in each subsuite.

        i.e. Checking for and defining required directories.
        """
        print(f"\nSetting up for {self.root}")
        self.failed_suites = []

    def __exit__(self, exc_type, exc_value, traceback):
        """
        This is run after the tests run with the run_suite_tests method finish.
        Specific clean up tasks should be defined in each subsuite.

        If self.run_test is called directly, it should be run in a 'with' block
        to ensure that clean up happens properly.

        i.e. Cleaning mongo after the lms tests run.
        """
        print(f"\nCleaning up after {self.root}")

    @property
    def cmd(self):
        """
        The command to run tests (as a string). For this base class there is none.
        """
        return None

    @staticmethod
    def kill_process(proc):
        """
        Kill the process `proc` created with `subprocess`.
        """
        p1_group = psutil.Process(proc.pid)
        child_pids = p1_group.children(recursive=True)

        for child_pid in child_pids:
            os.kill(child_pid.pid, signal.SIGKILL)

    @staticmethod
    def is_success(exit_code):
        """
        Determine if the given exit code represents a success of the test
        suite.  By default, only a zero counts as a success.
        """
        return exit_code == 0

    def run_test(self):
        """
        Runs a self.cmd in a subprocess and waits for it to finish.
        It returns False if errors or failures occur. Otherwise, it
        returns True.
        """
        # cmd = " ".join(self.cmd)
        cmd = " ".join(str(part) for part in self.cmd)
        sys.stdout.write(cmd)

        msg = colorize(
            'green',
            '\n{bar}\n Running tests for {suite_name} \n{bar}\n'.format(suite_name=self.root, bar='=' * 40),
        )

        sys.stdout.write(msg)
        sys.stdout.flush()

        if 'TEST_SUITE' not in os.environ:
            os.environ['TEST_SUITE'] = self.root.replace("/", "_")
        kwargs = {'shell': True, 'cwd': None}
        process = None

        try:
            process = subprocess.Popen(cmd, **kwargs)  # lint-amnesty, pylint: disable=consider-using-with
            return self.is_success(process.wait())
        except KeyboardInterrupt:
            self.kill_process(process)
            sys.exit(1)

    def run_suite_tests(self):
        """
        Runs each of the suites in self.subsuites while tracking failures
        """
        # Uses __enter__ and __exit__ for context
        with self:
            # run the tests for this class, and for all subsuites
            if self.cmd:
                passed = self.run_test()
                if not passed:
                    self.failed_suites.append(self)

            for suite in self.subsuites:
                suite.run_suite_tests()
                if suite.failed_suites:
                    self.failed_suites.extend(suite.failed_suites)

    def report_test_results(self):
        """
        Writes a list of failed_suites to sys.stderr
        """
        if self.failed_suites:
            msg = colorize('red', "\n\n{bar}\nTests failed in the following suites:\n* ".format(bar="=" * 48))
            msg += colorize('red', '\n* '.join([s.root for s in self.failed_suites]) + '\n\n')
        else:
            msg = colorize('green', "\n\n{bar}\nNo test failures ".format(bar="=" * 48))

        print(msg)

    def run(self):
        """
        Runs the tests in the suite while tracking and reporting failures.
        """
        self.run_suite_tests()

        # if tasks.environment.dry_run:
        #     return

        self.report_test_results()

        if self.failed_suites:
            sys.exit(1)


class JsTestSuite(TestSuite):
    """
    A class for running JavaScript tests.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')
        self.report_dir = Env.JS_REPORT_DIR
        self.opts = kwargs

        suite = args[0]
        self.subsuites = self._default_subsuites if suite == 'all' else [JsTestSubSuite(*args, **kwargs)]

    def __enter__(self):
        super().__enter__()
        self.report_dir.makedirs_p()
        # self.report_dir.mkdir(exist_ok=True)
        # if not self.skip_clean:
        # test_utils.clean_test_files()

        # if self.mode == 'run' and not self.run_under_coverage:
        # test_utils.clean_dir(self.report_dir)

    @property
    def _default_subsuites(self):
        """
        Returns all JS test suites
        """
        return [JsTestSubSuite(test_id, **self.opts) for test_id in Env.JS_TEST_ID_KEYS if test_id != 'jest-snapshot']


class JsTestSubSuite(TestSuite):
    """
    Class for JS suites like cms, cms-squire, lms, common,
    common-requirejs and xmodule
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_id = args[0]
        self.run_under_coverage = kwargs.get('with_coverage', True)
        self.mode = kwargs.get('mode', 'run')
        self.port = kwargs.get('port')
        self.root = self.root + ' javascript'
        self.report_dir = Env.JS_REPORT_DIR

        try:
            self.test_conf_file = Env.KARMA_CONFIG_FILES[Env.JS_TEST_ID_KEYS.index(self.test_id)]
        except ValueError:
            self.test_conf_file = Env.KARMA_CONFIG_FILES[0]

        self.coverage_report = self.report_dir / f'coverage-{self.test_id}.xml'
        self.xunit_report = self.report_dir / f'javascript_xunit-{self.test_id}.xml'

    @property
    def cmd(self):
        """
        Run the tests using karma runner.
        """
        cmd = [
            "node",
            "--max_old_space_size=4096",
            "node_modules/.bin/karma",
            "start",
            self.test_conf_file,
            "--single-run={}".format('false' if self.mode == 'dev' else 'true'),
            "--capture-timeout=60000",
            f"--junitreportpath={self.xunit_report}",
            f"--browsers={Env.KARMA_BROWSER}",
        ]

        if self.port:
            cmd.append(f"--port={self.port}")

        if self.run_under_coverage:
            cmd.extend([
                "--coverage",
                f"--coveragereportpath={self.coverage_report}",
            ])

        return cmd


class JestSnapshotTestSuite(TestSuite):
    """
    A class for running Jest Snapshot tests.
    """
    @property
    def cmd(self):
        """
        Run the tests using Jest.
        """
        return ["jest"]


def test_js(suite, mode, coverage, port, skip_clean):
    """
    Run the JavaScript tests
    """

    if (suite != 'all') and (suite not in Env.JS_TEST_ID_KEYS):
        sys.stderr.write(
            "Unknown test suite. Please choose from ({suites})\n".format(
                suites=", ".join(Env.JS_TEST_ID_KEYS)
            )
        )
        return

    if suite != 'jest-snapshot':
        test_suite = JsTestSuite(suite, mode=mode, with_coverage=coverage, port=port, skip_clean=skip_clean)
        test_suite.run()

    if (suite == 'jest-snapshot') or (suite == 'all'):  # lint-amnesty, pylint: disable=consider-using-in
        test_suite = JestSnapshotTestSuite('jest')
        test_suite.run()


# @needs('pavelib.prereqs.install_coverage_prereqs')
# @cmdopts([
#     ("compare-branch=", "b", "Branch to compare against, defaults to origin/master"),
# ], share_with=['coverage'])

def diff_coverage():
    """
    Build the diff coverage reports
    """

    compare_branch = 'origin/master'

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = []
    for filepath in Env.REPORT_DIR.walk():
        if bool(re.match(r'^coverage.*\.xml$', filepath.basename())):
            xml_reports.append(filepath)

    if not xml_reports:
        err_msg = colorize(
            'red',
            "No coverage info found.  Run `quality test` before running "
            "`coverage test`.\n"
        )
        sys.stderr.write(err_msg)
    else:
        xml_report_str = ' '.join(xml_reports)
        diff_html_path = os.path.join(Env.REPORT_DIR, 'diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        # The --diff-range-notation parameter is a workaround for https://github.com/Bachmann1234/diff_cover/issues/153
        command = (
            f"diff-cover {xml_report_str}"
            f"--diff-range-notation '..'"
            f"--compare-branch={compare_branch} "
            f"--html-report {diff_html_path}"
        )
        subprocess.run(command,
                       shell=True,
                       check=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)


@click.command("main")
@click.option(
    '--option', 'option',
    help='Run javascript tests or coverage test as per given option'
)
@click.option(
    '--s', 'suite',
    default='all',
    help='Test suite to run.'
)
@click.option(
    '--m', 'mode',
    default='run',
    help='dev or run'
)
@click.option(
    '--coverage', 'coverage',
    default=True,
    help='Run test under coverage'
)
@click.option(
    '--p', 'port',
    default=None,
    help='Port to run test server on (dev mode only)'
)
@click.option(
    '--C', 'skip_clean',
    default=False,
    help='skip cleaning repository before running tests'
)
def main(option, suite, mode, coverage, port, skip_clean):
    if option == 'jstest':
        test_js(suite, mode, coverage, port, skip_clean)
    elif option == 'coverage':
        diff_coverage()


if __name__ == "__main__":
    main()
