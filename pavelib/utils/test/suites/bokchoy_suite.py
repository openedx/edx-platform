"""
Class used for defining and running Bok Choy acceptance test suite
"""
from time import sleep
from urllib import urlencode

from common.test.acceptance.fixtures.course import CourseFixture, FixtureError

from path import Path as path
from paver.easy import sh, BuildFailure
from pavelib.utils.test.suites.suite import TestSuite
from pavelib.utils.envs import Env
from pavelib.utils.test import bokchoy_utils
from pavelib.utils.test import utils as test_utils

import os

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

__test__ = False  # do not collect

DEFAULT_NUM_PROCESSES = 1
DEFAULT_VERBOSITY = 2


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
        test_utils.clean_reports_dir()      # pylint: disable=no-value-for-parameter

        if not (self.fasttest or self.skip_clean or self.testsonly):
            test_utils.clean_test_files()

        msg = colorize('green', "Checking for mongo, memchache, and mysql...")
        print msg
        bokchoy_utils.check_services()

        if not self.testsonly:
            self.prepare_bokchoy_run()
        else:
            # load data in db_fixtures
            self.load_data()

        msg = colorize('green', "Confirming servers have started...")
        print msg
        bokchoy_utils.wait_for_test_servers()
        try:
            # Create course in order to seed forum data underneath. This is
            # a workaround for a race condition. The first time a course is created;
            # role permissions are set up for forums.
            CourseFixture('foobar_org', '1117', 'seed_forum', 'seed_foo').install()
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
            bokchoy_utils.clear_mongo()

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

    def prepare_bokchoy_run(self):
        """
        Sets up and starts servers for a Bok Choy run. If --fasttest is not
        specified then static assets are collected
        """
        sh("{}/scripts/reset-test-db.sh".format(Env.REPO_ROOT))

        if not self.fasttest:
            self.generate_optimized_static_assets()

        # Clear any test data already in Mongo or MySQLand invalidate
        # the cache
        bokchoy_utils.clear_mongo()
        self.cache.flush_all()

        # load data in db_fixtures
        self.load_data()

        # load courses if self.imports_dir is set
        self.load_courses()

        # Ensure the test servers are available
        msg = colorize('green', "Confirming servers are running...")
        print msg
        bokchoy_utils.start_servers(self.default_store, self.coveragerc)

    def load_courses(self):
        """
        Loads courses from self.imports_dir.

        Note: self.imports_dir is the directory that contains the directories
        that have courses in them. For example, if the course is located in
        `test_root/courses/test-example-course/`, self.imports_dir should be
        `test_root/courses/`.
        """
        msg = colorize('green', "Importing courses from {}...".format(self.imports_dir))
        print msg

        if self.imports_dir:
            sh(
                "DEFAULT_STORE={default_store}"
                " ./manage.py cms --settings=bok_choy import {import_dir}".format(
                    default_store=self.default_store,
                    import_dir=self.imports_dir
                )
            )

    def load_data(self):
        """
        Loads data into database from db_fixtures
        """
        print 'Loading data from json fixtures in db_fixtures directory'
        sh(
            "DEFAULT_STORE={default_store}"
            " ./manage.py lms --settings bok_choy loaddata --traceback"
            " common/test/db_fixtures/*.json".format(
                default_store=self.default_store,
            )
        )

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
        if self.imports_dir:
            # If imports_dir has been specified, assume the files are
            # already there -- no need to fetch them from github. This
            # allows someome to crawl a different course. They are responsible
            # for putting it, un-archived, in the directory.
            self.should_fetch_course = False
        else:
            # Otherwise, obey `--skip-fetch` command and use the default
            # test course.  Note that the fetch will also be skipped when
            # using `--fast`.
            self.should_fetch_course = kwargs.get('should_fetch_course')
            self.imports_dir = path('test_root/courses/')

        self.pa11y_report_dir = os.path.join(self.report_dir, 'pa11ycrawler_reports')
        self.tar_gz_file = "https://github.com/edx/demo-test-course/archive/master.tar.gz"

        self.start_urls = []
        auto_auth_params = {
            "redirect": 'true',
            "staff": 'true',
            "course_id": self.course_key,
        }
        cms_params = urlencode(auto_auth_params)
        self.start_urls.append("\"http://localhost:8031/auto_auth?{}\"".format(cms_params))

        sequence_url = "/api/courses/v1/blocks/?{}".format(
            urlencode({
                "course_id": self.course_key,
                "depth": "all",
                "all_blocks": "true",
            })
        )
        auto_auth_params.update({'redirect_to': sequence_url})
        lms_params = urlencode(auto_auth_params)
        self.start_urls.append("\"http://localhost:8003/auto_auth?{}\"".format(lms_params))

    def __enter__(self):
        if self.should_fetch_course:
            self.get_test_course()
        super(Pa11yCrawler, self).__enter__()

    def get_test_course(self):
        """
        Fetches the test course.
        """
        self.imports_dir.makedirs_p()
        zipped_course = self.imports_dir + 'demo_course.tar.gz'

        msg = colorize('green', "Fetching the test course from github...")
        print msg

        sh(
            'wget {tar_gz_file} -O {zipped_course}'.format(
                tar_gz_file=self.tar_gz_file,
                zipped_course=zipped_course,
            )
        )

        msg = colorize('green', "Uncompressing the test course...")
        print msg

        sh(
            'tar zxf {zipped_course} -C {courses_dir}'.format(
                zipped_course=zipped_course,
                courses_dir=self.imports_dir,
            )
        )

    def generate_html_reports(self):
        """
        Runs pa11ycrawler json-to-html
        """
        cmd_str = (
            'pa11ycrawler json-to-html --pa11ycrawler-reports-dir={report_dir}'
        ).format(report_dir=self.pa11y_report_dir)

        sh(cmd_str)

    @property
    def cmd(self):
        """
        Runs pa11ycrawler as staff user against the test course.
        """
        cmd = [
            'pa11ycrawler',
            'run',
        ] + self.start_urls + [
            '--pa11ycrawler-allowed-domains=localhost',
            '--pa11ycrawler-reports-dir={}'.format(self.pa11y_report_dir),
            '--pa11ycrawler-deny-url-matcher=logout',
            '--pa11y-reporter="1.0-json"',
            '--depth-limit=6',
        ]
        return cmd
