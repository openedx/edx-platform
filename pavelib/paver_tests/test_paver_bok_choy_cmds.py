"""
Tests for the bok-choy paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_bok_choy_cmds.py
"""
import os
import unittest
from textwrap import dedent

import ddt
from mock import patch, call, Mock
from test.test_support import EnvironmentVarGuard
from paver.easy import BuildFailure, call_task, environment
from pavelib.utils.test.suites import BokChoyTestSuite, Pa11yCrawler
from pavelib.utils.test.suites.bokchoy_suite import DEMO_COURSE_TAR_GZ, DEMO_COURSE_IMPORT_DIR

REPO_DIR = os.getcwd()


class TestPaverBokChoyCmd(unittest.TestCase):
    """
    Paver Bok Choy Command test cases
    """

    def _expected_command(self, name, store=None, verify_xss=True):
        """
        Returns the command that is expected to be run for the given test spec
        and store.
        """

        shard_str = '/shard_' + self.shard if self.shard else ''

        expected_statement = [
            "DEFAULT_STORE={}".format(store),
            "SCREENSHOT_DIR='{}/test_root/log{}'".format(REPO_DIR, shard_str),
            "BOK_CHOY_HAR_DIR='{}/test_root/log{}/hars'".format(REPO_DIR, shard_str),
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{}/{}'".format(
                REPO_DIR,
                'node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js'
            ),
            "SELENIUM_DRIVER_LOG_DIR='{}/test_root/log{}'".format(REPO_DIR, shard_str),
            "VERIFY_XSS='{}'".format(verify_xss),
            "nosetests",
            "{}/common/test/acceptance/{}".format(REPO_DIR, name),
            "--xunit-file={}/reports/bok_choy{}/xunit.xml".format(REPO_DIR, shard_str),
            "--verbosity=2",
        ]
        return expected_statement

    def setUp(self):
        super(TestPaverBokChoyCmd, self).setUp()
        self.shard = os.environ.get('SHARD')
        self.env_var_override = EnvironmentVarGuard()

    def test_default(self):
        suite = BokChoyTestSuite('')
        name = 'tests'
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_suite_spec(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_class_spec(self):
        spec = 'test_foo.py:FooTest'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_testcase_spec(self):
        spec = 'test_foo.py:FooTest.test_bar'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_spec_with_draft_default_store(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec, default_store='draft')
        name = 'tests/{}'.format(spec)
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=name, store='draft')
        )

    def test_invalid_default_store(self):
        # the cmd will dumbly compose whatever we pass in for the default_store
        suite = BokChoyTestSuite('', default_store='invalid')
        name = 'tests'
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=name, store='invalid')
        )

    def test_serversonly(self):
        suite = BokChoyTestSuite('', serversonly=True)
        self.assertEqual(suite.cmd, None)

    def test_verify_xss(self):
        suite = BokChoyTestSuite('', verify_xss=True)
        name = 'tests'
        self.assertEqual(suite.cmd, self._expected_command(name=name, verify_xss=True))

    def test_verify_xss_env_var(self):
        self.env_var_override.set('VERIFY_XSS', 'False')
        with self.env_var_override:
            suite = BokChoyTestSuite('')
            name = 'tests'
            self.assertEqual(suite.cmd, self._expected_command(name=name, verify_xss=False))

    def test_test_dir(self):
        test_dir = 'foo'
        suite = BokChoyTestSuite('', test_dir=test_dir)
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=test_dir)
        )

    def test_verbosity_settings_1_process(self):
        """
        Using 1 process means paver should ask for the traditional xunit plugin for plugin results
        """
        expected_verbosity_command = [
            "--xunit-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else ''
            ),
            "--verbosity=2",
        ]
        suite = BokChoyTestSuite('', num_processes=1)
        self.assertEqual(suite.verbosity_processes_command, expected_verbosity_command)

    def test_verbosity_settings_2_processes(self):
        """
        Using multiple processes means specific xunit, coloring, and process-related settings should
        be used.
        """
        process_count = 2
        expected_verbosity_command = [
            "--xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
            ),
            "--processes={}".format(process_count),
            "--no-color",
            "--process-timeout=1200",
        ]
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(suite.verbosity_processes_command, expected_verbosity_command)

    def test_verbosity_settings_3_processes(self):
        """
        With the above test, validate that num_processes can be set to various values
        """
        process_count = 3
        expected_verbosity_command = [
            "--xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
            ),
            "--processes={}".format(process_count),
            "--no-color",
            "--process-timeout=1200",
        ]
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(suite.verbosity_processes_command, expected_verbosity_command)

    def test_invalid_verbosity_and_processes(self):
        """
        If an invalid combination of verbosity and number of processors is passed in, a
        BuildFailure should be raised
        """
        suite = BokChoyTestSuite('', num_processes=2, verbosity=3)
        with self.assertRaises(BuildFailure):
            # pylint: disable=pointless-statement
            suite.verbosity_processes_command


@ddt.ddt
class TestPaverPa11yCrawlerCmd(unittest.TestCase):

    """
    Paver pa11ycrawler command test cases.  Most of the functionality is
    inherited from BokChoyTestSuite, so those tests aren't duplicated.
    """

    def setUp(self):
        super(TestPaverPa11yCrawlerCmd, self).setUp()

        # Mock shell commands
        mock_sh = patch('pavelib.utils.test.suites.bokchoy_suite.sh')
        self._mock_sh = mock_sh.start()

        # Cleanup mocks
        self.addCleanup(mock_sh.stop)

        # reset the options for all tasks
        environment.options.clear()

    def test_default(self):
        suite = Pa11yCrawler(
            'pa11ycrawler', course_key="course-v1:edX+Test101+course",
        )
        ignore = (
            "pa11y_ignore_rules_url="
            "https://raw.githubusercontent.com/edx/"
            "pa11ycrawler-ignore/master/ignore.yaml"
        )
        expected_cmd = [
            "scrapy",
            "crawl",
            "edx",
            "-a",
            "port=8003",
            "-a",
            "course_key=course-v1:edX+Test101+course",
            "-a",
            ignore,
            "-a",
            "data_dir=/edx/app/edxapp/edx-platform/reports/pa11ycrawler/data",
        ]
        actual_cmd = suite.cmd
        # verify that the final section of this command is for specifying the
        # data directory
        self.assertEqual(actual_cmd[-2], "-a")
        self.assertTrue(actual_cmd[-1].startswith("data_dir="))
        # chop off the `data_dir` argument when comparing,
        # since it is highly dependent on who is running this paver command,
        # and where it's being run (devstack, jenkins, etc)
        self.assertEqual(actual_cmd[0:-2], expected_cmd[0:-2])

    @ddt.data(
        (True, True, None),
        (True, False, None),
        (False, True, DEMO_COURSE_IMPORT_DIR),
        (False, False, None),
    )
    @ddt.unpack
    def test_get_test_course(self, import_dir_set, should_fetch_course_set, downloaded_to):
        options = {}
        if import_dir_set:
            options['imports_dir'] = 'some_import_dir'
        if should_fetch_course_set:
            options['should_fetch_course'] = True

        call_task('pavelib.utils.test.suites.bokchoy_suite.get_test_course', options=options)

        if downloaded_to is None:
            self._mock_sh.assert_has_calls([])
        else:
            self._mock_sh.assert_has_calls([
                call(
                    'wget {targz} -O {dir}demo_course.tar.gz'.format(targz=DEMO_COURSE_TAR_GZ, dir=downloaded_to)),
                call(
                    'tar zxf {dir}demo_course.tar.gz -C {dir}'.format(dir=downloaded_to)),
            ])

    @patch("pavelib.utils.test.suites.bokchoy_suite.path")
    def test_scrapy_cfg_exists(self, mocked_path_func):
        # setup
        mock_path = Mock()
        mock_path.expand.return_value = mock_path
        mock_path.isfile.return_value = True
        mocked_path_func.return_value = mock_path

        # test
        Pa11yCrawler('pa11ycrawler')

        # check
        mocked_path_func.assert_called_with("~/.config/scrapy.cfg")
        self.assertTrue(mock_path.isfile.called)
        self.assertFalse(mock_path.write_text.called)

    @patch("pavelib.utils.test.suites.bokchoy_suite.path")
    def test_scrapy_cfg_not_exists(self, mocked_path_func):
        # setup
        mock_path = Mock()
        mock_path.expand.return_value = mock_path
        mock_path.isfile.return_value = False
        mocked_path_func.return_value = mock_path

        # test
        Pa11yCrawler('pa11ycrawler')

        # check
        mocked_path_func.assert_called_with("~/.config/scrapy.cfg")
        self.assertTrue(mock_path.isfile.called)
        self.assertTrue(mock_path.parent.makedirs_p.called)
        content = dedent("""
            [settings]
            default = pa11ycrawler.settings

            [deploy]
            project = pa11ycrawler
        """)
        mock_path.write_text.assert_called_with(content)

    def test_generate_html_reports(self):
        suite = Pa11yCrawler('pa11ycrawler')
        suite.generate_html_reports()
        self._mock_sh.assert_has_calls([
            call([
                'pa11ycrawler-html',
                '--data-dir',
                os.path.join(suite.report_dir, "data"),
                '--output-dir',
                os.path.join(suite.report_dir, "html"),
            ])
        ])
