"""
Class used for defining and running Bok Choy acceptance test suite
"""
from time import sleep
from urllib import urlencode
from textwrap import dedent

from common.test.acceptance.fixtures.course import CourseFixture, FixtureError

from path import Path as path
from paver.easy import sh, BuildFailure, cmdopts, task, needs, might_call, call_task, dry
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env
from pavelib.utils.test.bokchoy_utils import (
    clear_mongo, start_servers, check_services, wait_for_test_servers
)
from pavelib.utils.test.bokchoy_options import (
    BOKCHOY_IMPORTS_DIR, BOKCHOY_IMPORTS_DIR_DEPR,
    BOKCHOY_DEFAULT_STORE, BOKCHOY_DEFAULT_STORE_DEPR,
    BOKCHOY_FASTTEST,
    PA11Y_FETCH_COURSE
)
from pavelib.utils.test import utils as test_utils
from pavelib.utils.timer import timed

import os

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect

DEFAULT_NUM_PROCESSES = 1
DEFAULT_VERBOSITY = 2

DEMO_COURSE_TAR_GZ = "https://github.com/edx/demo-test-course/archive/master.tar.gz"
DEMO_COURSE_IMPORT_DIR = path('test_root/courses/')


@task
@cmdopts([BOKCHOY_DEFAULT_STORE, BOKCHOY_DEFAULT_STORE_DEPR])
@timed
def load_bok_choy_data(options):
    """
    Loads data into database from db_fixtures
    """
    print 'Loading data from json fixtures in db_fixtures directory'
    sh(
        "DEFAULT_STORE={default_store}"
        " ./manage.py lms --settings bok_choy loaddata --traceback"
        " common/test/db_fixtures/*.json".format(
            default_store=options.default_store,
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
        print msg

        sh(
            "DEFAULT_STORE={default_store}"
            " ./manage.py cms --settings=bok_choy import {import_dir}".format(
                default_store=options.default_store,
                import_dir=options.imports_dir
            )
        )
    else:
        print colorize('blue', "--imports-dir not set, skipping import")


@task
@cmdopts([BOKCHOY_IMPORTS_DIR, BOKCHOY_IMPORTS_DIR_DEPR, PA11Y_FETCH_COURSE])
@timed
def get_test_course(options):
    """
    Fetches the test course.
    """

    if options.get('imports_dir'):
        print colorize("green", "--imports-dir specified, skipping fetch of test course")
        return

    if options.get('skip-fetch'):
        print colorize("green", "--skip-fetch specified, skipping fetch of test course")
        return

    # Set the imports_dir for use by other tasks
    options.imports_dir = DEMO_COURSE_IMPORT_DIR

    options.imports_dir.makedirs_p()
    zipped_course = options.imports_dir + 'demo_course.tar.gz'

    msg = colorize('green', "Fetching the test course from github...")
    print msg

    sh(
        'wget {tar_gz_file} -O {zipped_course}'.format(
            tar_gz_file=DEMO_COURSE_TAR_GZ,
            zipped_course=zipped_course,
        )
    )

    msg = colorize('green', "Uncompressing the test course...")
    print msg

    sh(
        'tar zxf {zipped_course} -C {courses_dir}'.format(
            zipped_course=zipped_course,
            courses_dir=options.imports_dir,
        )
    )


@task
@timed
def reset_test_database():
    """
    Reset the database used by the bokchoy tests.
    """
    sh("{}/scripts/reset-test-db.sh".format(Env.REPO_ROOT))


@task
@needs(['reset_test_database', 'clear_mongo', 'load_bok_choy_data', 'load_courses'])
@might_call('start_servers')
@cmdopts([BOKCHOY_FASTTEST], share_with=['start_servers'])
@timed
def prepare_bokchoy_run(options):
    """
    Sets up and starts servers for a Bok Choy run. If --fasttest is not
    specified then static assets are collected
    """
    if not options.get('fasttest', False):

        print colorize('green', "Generating optimized static assets...")
        if options.get('log_dir') is None:
            call_task('update_assets', args=['--settings', 'test_static_optimized'])
        else:
            call_task('update_assets', args=[
                '--settings', 'test_static_optimized',
                '--collect-log', options.log_dir
            ])

    # Ensure the test servers are available
    msg = colorize('green', "Confirming servers are running...")
    print msg
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
      num_processes - number of processes or threads to use in tests. Recommendation is that this
      is less than or equal to the number of available processors.
      verify_xss - when set, check for XSS vulnerabilities in the page HTML.
      See nosetest documentation: http://nose.readthedocs.org/en/latest/usage.html
    """
    def __init__(self, *args, **kwargs):
        super(BokChoyTestSuite, self).__init__(*args, **kwargs)
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
        super(BokChoyTestSuite, self).__enter__()

        # Ensure that we have a directory to put logs and reports
        self.log_dir.makedirs_p()
        self.har_dir.makedirs_p()
        self.report_dir.makedirs_p()
        test_utils.clean_reports_dir()  # pylint: disable=no-value-for-parameter

        if not (self.fasttest or self.skip_clean or self.testsonly):
            test_utils.clean_test_files()

        msg = colorize('green', "Checking for mongo, memchache, and mysql...")
        print msg
        check_services()

        if not self.testsonly:
            call_task('prepare_bokchoy_run', options={'log_dir': self.log_dir})  # pylint: disable=no-value-for-parameter
        else:
            # load data in db_fixtures
            load_bok_choy_data()  # pylint: disable=no-value-for-parameter

        msg = colorize('green', "Confirming servers have started...")
        print msg
        wait_for_test_servers()
        try:
            # Create course in order to seed forum data underneath. This is
            # a workaround for a race condition. The first time a course is created;
            # role permissions are set up for forums.
            dry(
                "Installing course fixture for forums",
                CourseFixture('foobar_org', '1117', 'seed_forum', 'seed_foo').install
            )
            print 'Forums permissions/roles data has been seeded'
        except FixtureError:
            # this means it's already been done
            pass

        if self.serversonly:
            self.run_servers_continuously()

    def __exit__(self, exc_type, exc_value, traceback):
        super(BokChoyTestSuite, self).__exit__(exc_type, exc_value, traceback)

        # Using testsonly will leave all fixtures in place (Note: the db will also be dirtier.)
        if self.testsonly:
            msg = colorize('green', 'Running in testsonly mode... SKIPPING database cleanup.')
            print msg
        else:
            # Clean up data we created in the databases
            msg = colorize('green', "Cleaning up databases...")
            print msg
            sh("./manage.py lms --settings bok_choy flush --traceback --noinput")
            clear_mongo()

    @property
    def verbosity_processes_command(self):
        """
        Multiprocessing, xunit, color, and verbosity do not work well together. We need to construct
        the proper combination for use with nosetests.
        """
        command = []

        if self.verbosity != DEFAULT_VERBOSITY and self.num_processes != DEFAULT_NUM_PROCESSES:
            msg = 'Cannot pass in both num_processors and verbosity. Quitting'
            raise BuildFailure(msg)

        if self.num_processes != 1:
            # Construct "multiprocess" nosetest command
            command = [
                "--xunitmp-file={}".format(self.xunit_report),
                "--processes={}".format(self.num_processes),
                "--no-color",
                "--process-timeout=1200",
            ]

        else:
            command = [
                "--xunit-file={}".format(self.xunit_report),
                "--verbosity={}".format(self.verbosity),
            ]

        return command

    def run_servers_continuously(self):
        """
        Infinite loop. Servers will continue to run in the current session unless interrupted.
        """
        print 'Bok-choy servers running. Press Ctrl-C to exit...\n'
        print 'Note: pressing Ctrl-C multiple times can corrupt noseid files and system state. Just press it once.\n'

        while True:
            try:
                sleep(10000)
            except KeyboardInterrupt:
                print "Stopping bok-choy servers.\n"
                break

    @property
    def cmd(self):
        """
        This method composes the nosetests command to send to the terminal. If nosetests aren't being run,
         the command returns None.
        """
        # Default to running all tests if no specific test is specified
        if not self.test_spec:
            test_spec = self.test_dir
        else:
            test_spec = self.test_dir / self.test_spec

        # Skip any additional commands (such as nosetests) if running in
        # servers only mode
        if self.serversonly:
            return None

        # Construct the nosetests command, specifying where to save
        # screenshots and XUnit XML reports
        cmd = [
            "DEFAULT_STORE={}".format(self.default_store),
            "SCREENSHOT_DIR='{}'".format(self.log_dir),
            "BOK_CHOY_HAR_DIR='{}'".format(self.har_dir),
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{}'".format(self.a11y_file),
            "SELENIUM_DRIVER_LOG_DIR='{}'".format(self.log_dir),
            "VERIFY_XSS='{}'".format(self.verify_xss),
            "nosetests",
            test_spec,
        ] + self.verbosity_processes_command
        if self.save_screenshots:
            cmd.append("--with-save-baseline")
        if self.extra_args:
            cmd.append(self.extra_args)
        cmd.extend(self.passthrough_options)

        return cmd


class Pa11yCrawler(BokChoyTestSuite):
    """
    Sets up test environment with mega-course loaded, and runs pa11ycralwer
    against it.
    """

    def __init__(self, *args, **kwargs):
        super(Pa11yCrawler, self).__init__(*args, **kwargs)
        self.course_key = kwargs.get('course_key')
        self.ensure_scrapy_cfg()

    def ensure_scrapy_cfg(self):
        """
        Scrapy requires a few configuration settings in order to run:
        http://doc.scrapy.org/en/1.1/topics/commands.html#configuration-settings
        This method ensures they are correctly written to the filesystem
        in a location where Scrapy knows to look for them.

        Returns True if the file was created, or False if the file already
        exists (in which case it was not modified.)
        """
        cfg_file = path("~/.config/scrapy.cfg").expand()
        if cfg_file.isfile():
            return False
        cfg_file.parent.makedirs_p()
        content = dedent("""
            [settings]
            default = pa11ycrawler.settings

            [deploy]
            project = pa11ycrawler
        """)
        cfg_file.write_text(content)
        return True

    def generate_html_reports(self):
        """
        Runs pa11ycrawler-html
        """
        command = [
            'pa11ycrawler-html',
            '--data-dir',
            os.path.join(self.report_dir, 'data'),
            '--output-dir',
            os.path.join(self.report_dir, 'html'),
        ]
        sh(command)

    @property
    def cmd(self):
        """
        Runs pa11ycrawler as staff user against the test course.
        """
        data_dir = os.path.join(self.report_dir, 'data')
        url = "https://raw.githubusercontent.com/singingwolfboy/pa11ycrawler-ignore/master/ignore.yaml"
        return [
            "scrapy",
            "test",
            "edx",
            "-a",
            "port=8003",
            "-a",
            "course_key={key}".format(key=self.course_key),
            "-a",
            "pa11y_ignore_rules_url={url}".format(url=url),
            "-a",
            "data_dir={dir}".format(dir=data_dir)
        ]
