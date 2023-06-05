"""
Class used for defining and running Bok Choy acceptance test suite
"""


import os
from time import sleep

from paver.easy import call_task, cmdopts, dry, might_call, needs, sh, task

from common.test.acceptance.fixtures.course import CourseFixture, FixtureError
from pavelib.database import update_local_bokchoy_db_from_s3
from pavelib.utils.envs import Env
from pavelib.utils.test import utils as test_utils
from pavelib.utils.test.bokchoy_options import (
    BOKCHOY_DEFAULT_STORE,
    BOKCHOY_DEFAULT_STORE_DEPR,
    BOKCHOY_FASTTEST,
    BOKCHOY_IMPORTS_DIR,
    BOKCHOY_IMPORTS_DIR_DEPR
)
from pavelib.utils.test.bokchoy_utils import check_services, clear_mongo, start_servers, wait_for_test_servers
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.timer import timed

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect

DEFAULT_NUM_PROCESSES = 1
DEFAULT_VERBOSITY = 2


@task
@cmdopts([BOKCHOY_DEFAULT_STORE, BOKCHOY_DEFAULT_STORE_DEPR])
@timed
def load_bok_choy_data(options):
    """
    Loads data into database from db_fixtures
    """
    print('Loading data from json fixtures in db_fixtures directory')
    sh(
        "DEFAULT_STORE={default_store}"
        " ./manage.py lms --settings {settings} loaddata --traceback"
        " common/test/db_fixtures/*.json".format(
            default_store=options.default_store,
            settings=Env.SETTINGS
        )
    )


@task
@cmdopts([
    BOKCHOY_IMPORTS_DIR, BOKCHOY_IMPORTS_DIR_DEPR, BOKCHOY_DEFAULT_STORE,
    BOKCHOY_DEFAULT_STORE_DEPR
])
@timed
def load_courses(options):
    """
    Loads courses from options.imports_dir.

    Note: options.imports_dir is the directory that contains the directories
    that have courses in them. For example, if the course is located in
    `test_root/courses/test-example-course/`, options.imports_dir should be
    `test_root/courses/`.
    """
    if 'imports_dir' in options:
        msg = colorize('green', "Importing courses from {}...".format(options.imports_dir))
        print(msg)

        sh(
            "DEFAULT_STORE={default_store}"
            " ./manage.py cms --settings={settings} import {import_dir}".format(
                default_store=options.default_store,
                import_dir=options.imports_dir,
                settings=Env.SETTINGS
            )
        )
    else:
        print(colorize('blue', "--imports-dir not set, skipping import"))


@task
@timed
def update_fixtures():
    """
    Use the correct domain for the current test environment in each Site
    fixture.  This currently differs between devstack cms, devstack lms,
    and Jenkins.
    """
    msg = colorize('green', "Updating the Site fixture domains...")
    print(msg)

    sh(
        " ./manage.py lms --settings={settings} update_fixtures".format(
            settings=Env.SETTINGS
        )
    )


@task
@timed
def reset_test_database():
    """
    Reset the database used by the bokchoy tests.

    Use the database cache automation defined in pavelib/database.py
    """
    update_local_bokchoy_db_from_s3()  # pylint: disable=no-value-for-parameter


@task
@needs(['reset_test_database', 'clear_mongo', 'load_bok_choy_data', 'load_courses', 'update_fixtures'])
@might_call('start_servers')
@cmdopts([BOKCHOY_FASTTEST], share_with=['start_servers'])
@timed
def prepare_bokchoy_run(options):
    """
    Sets up and starts servers for a Bok Choy run. If --fasttest is not
    specified then static assets are collected
    """
    if not options.get('fasttest', False):

        print(colorize('green', "Generating optimized static assets..."))
        if options.get('log_dir') is None:
            call_task('update_assets', args=['--settings', 'test_static_optimized'])
        else:
            call_task('update_assets', args=[
                '--settings', 'test_static_optimized',
                '--collect-log', options.log_dir
            ])

    # Ensure the test servers are available
    msg = colorize('green', "Confirming servers are running...")
    print(msg)
    start_servers()  # pylint: disable=no-value-for-parameter


class BokChoyTestSuite(TestSuite):
    """
    TestSuite for running Bok Choy tests
    Properties (below is a subset):
      test_dir - parent directory for tests
      log_dir - directory for test output
      report_dir - directory for reports (e.g., coverage) related to test execution
      xunit_report - directory for xunit-style output (xml)
      fasttest - when set, skip various set-up tasks (e.g., collectstatic)
      serversonly - prepare and run the necessary servers, only stopping when interrupted with Ctrl-C
      testsonly - assume servers are running (as per above) and run tests with no setup or cleaning of environment
      test_spec - when set, specifies test files, classes, cases, etc. See platform doc.
      default_store - modulestore to use when running tests (split or draft)
      eval_attr - only run tests matching given attribute expression
      num_processes - number of processes or threads to use in tests. Recommendation is that this
      is less than or equal to the number of available processors.
      verify_xss - when set, check for XSS vulnerabilities in the page HTML.
      See pytest documentation: https://docs.pytest.org/en/latest/
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_dir = Env.BOK_CHOY_DIR / kwargs.get('test_dir', 'tests')
        self.log_dir = Env.BOK_CHOY_LOG_DIR
        self.report_dir = kwargs.get('report_dir', Env.BOK_CHOY_REPORT_DIR)
        self.xunit_report = self.report_dir / "xunit.xml"
        self.cache = Env.BOK_CHOY_CACHE
        self.fasttest = kwargs.get('fasttest', False)
        self.serversonly = kwargs.get('serversonly', False)
        self.testsonly = kwargs.get('testsonly', False)
        self.test_spec = kwargs.get('test_spec', None)
        self.default_store = kwargs.get('default_store', None)
        self.eval_attr = kwargs.get('eval_attr', None)
        self.verbosity = kwargs.get('verbosity', DEFAULT_VERBOSITY)
        self.num_processes = kwargs.get('num_processes', DEFAULT_NUM_PROCESSES)
        self.verify_xss = kwargs.get('verify_xss', os.environ.get('VERIFY_XSS', True))
        self.extra_args = kwargs.get('extra_args', '')
        self.har_dir = self.log_dir / 'hars'
        self.a11y_file = Env.BOK_CHOY_A11Y_CUSTOM_RULES_FILE
        self.imports_dir = kwargs.get('imports_dir', None)
        self.coveragerc = kwargs.get('coveragerc', None)
        self.save_screenshots = kwargs.get('save_screenshots', False)

    def __enter__(self):
        super().__enter__()

        # Ensure that we have a directory to put logs and reports
        self.log_dir.makedirs_p()
        self.har_dir.makedirs_p()
        self.report_dir.makedirs_p()
        test_utils.clean_reports_dir()  # pylint: disable=no-value-for-parameter

        # Set the environment so that webpack understands where to compile its resources.
        # This setting is expected in other environments, so we are setting it for the
        # bok-choy test run.
        os.environ['EDX_PLATFORM_SETTINGS'] = 'test_static_optimized'

        if not (self.fasttest or self.skip_clean or self.testsonly):
            test_utils.clean_test_files()

        msg = colorize('green', "Checking for mongo, memchache, and mysql...")
        print(msg)
        check_services()

        if not self.testsonly:
            call_task('prepare_bokchoy_run', options={'log_dir': self.log_dir, 'coveragerc': self.coveragerc})
        else:
            # load data in db_fixtures
            load_bok_choy_data()  # pylint: disable=no-value-for-parameter
            update_fixtures()

        msg = colorize('green', "Confirming servers have started...")
        print(msg)
        wait_for_test_servers()
        try:
            # Create course in order to seed forum data underneath. This is
            # a workaround for a race condition. The first time a course is created;
            # role permissions are set up for forums.
            dry(
                "Installing course fixture for forums",
                CourseFixture('foobar_org', '1117', 'seed_forum', 'seed_foo').install
            )
            print('Forums permissions/roles data has been seeded')
        except FixtureError:
            # this means it's already been done
            pass

        if self.serversonly:
            self.run_servers_continuously()

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)

        # Using testsonly will leave all fixtures in place (Note: the db will also be dirtier.)
        if self.testsonly:
            msg = colorize('green', 'Running in testsonly mode... SKIPPING database cleanup.')
            print(msg)
        else:
            # Clean up data we created in the databases
            msg = colorize('green', "Cleaning up databases...")
            print(msg)
            sh("./manage.py lms --settings {settings} flush --traceback --noinput".format(settings=Env.SETTINGS))
            clear_mongo()

    @property
    def verbosity_processes_command(self):
        """
        Construct the proper combination of multiprocessing, XUnit XML file, color, and verbosity for use with pytest.
        """
        command = ["--junitxml={}".format(self.xunit_report)]

        if self.num_processes != 1:
            # Construct "multiprocess" pytest command
            command += [
                "-n {}".format(self.num_processes),
                "--color=no",
            ]
        if self.verbosity < 1:
            command.append("--quiet")
        elif self.verbosity > 1:
            command.append("--verbose")
        if self.eval_attr:
            command.append("-a '{}'".format(self.eval_attr))

        return command

    def run_servers_continuously(self):
        """
        Infinite loop. Servers will continue to run in the current session unless interrupted.
        """
        print('Bok-choy servers running. Press Ctrl-C to exit...\n')
        print('Note: pressing Ctrl-C multiple times can corrupt system state. Just press it once.\n')

        while True:
            try:
                sleep(10000)
            except KeyboardInterrupt:
                print("Stopping bok-choy servers.\n")
                break

    @property
    def cmd(self):
        """
        This method composes the pytest command to send to the terminal. If pytest isn't being run,
         the command returns None.
        """
        # Default to running all tests if no specific test is specified
        if not self.test_spec:
            test_spec = self.test_dir
        else:
            test_spec = self.test_dir / self.test_spec

        # Skip any additional commands (such as pytest) if running in
        # servers only mode
        if self.serversonly:
            return None

        # Construct the pytest command, specifying where to save
        # screenshots and XUnit XML reports
        cmd = [
            "DEFAULT_STORE={}".format(self.default_store),
            "SAVED_SOURCE_DIR='{}'".format(self.log_dir),
            "SCREENSHOT_DIR='{}'".format(self.log_dir),
            "BOK_CHOY_HAR_DIR='{}'".format(self.har_dir),
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{}'".format(self.a11y_file),
            "SELENIUM_DRIVER_LOG_DIR='{}'".format(self.log_dir),
            "VERIFY_XSS='{}'".format(self.verify_xss),
        ]
        if self.save_screenshots:
            cmd.append("NEEDLE_SAVE_BASELINE=True")
        if self.coveragerc:
            cmd += [
                "coverage",
                "run",
            ]
            cmd.append("--rcfile={}".format(self.coveragerc))
        else:
            cmd += [
                "python",
                "-Wd",
            ]
        cmd += [
            "-m",
            "pytest",
        ]
        if self.coveragerc:
            cmd.extend([
                '-p',
                'openedx.testing.coverage_context_listener.pytest_plugin',
            ])
        cmd.append(test_spec)
        cmd.extend(self.verbosity_processes_command)
        if self.extra_args:
            cmd.append(self.extra_args)
        cmd.extend(self.passthrough_options)

        return cmd
