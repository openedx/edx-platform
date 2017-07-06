"""Unit tests for the Paver JavaScript testing tasks."""

import ddt
from mock import patch
from paver.easy import call_task

import pavelib.js_test
from .utils import PaverTestCase
from pavelib.utils.envs import Env


@ddt.ddt
class TestPaverJavaScriptTestTasks(PaverTestCase):
    """
    Test the Paver JavaScript testing tasks.
    """

    EXPECTED_DELETE_JAVASCRIPT_REPORT_COMMAND = u'find {platform_root}/reports/javascript -type f -delete'
    EXPECTED_INSTALL_NPM_ASSETS_COMMAND = u'install npm_assets'
    EXPECTED_COFFEE_COMMAND = (
        u'node_modules/.bin/coffee --compile `find {platform_root}/lms {platform_root}/cms '
        u'{platform_root}/common -type f -name "*.coffee"`'
    )
    EXPECTED_KARMA_OPTIONS = (
        u"{config_file} "
        u"--single-run={single_run} "
        u"--capture-timeout=60000 "
        u"--junitreportpath="
        u"{platform_root}/reports/javascript/javascript_xunit-{suite}.xml"
    )
    EXPECTED_COVERAGE_OPTIONS = (
        u' --coverage --coveragereportpath={platform_root}/reports/javascript/coverage-{suite}.xml'
    )

    EXPECTED_COMMANDS = [
        u"make report_dir",
        u'git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads',
        u"find . -name '.git' -prune -o -name '*.pyc' -exec rm {} \\;",
        u'rm -rf test_root/log/auto_screenshots/*',
        u"rm -rf /tmp/mako_[cl]ms",
    ]

    def setUp(self):
        super(TestPaverJavaScriptTestTasks, self).setUp()

        # Mock the paver @needs decorator
        self._mock_paver_needs = patch.object(pavelib.js_test.test_js, 'needs').start()
        self._mock_paver_needs.return_value = 0

        # Cleanup mocks
        self.addCleanup(self._mock_paver_needs.stop)

    @ddt.data(
        [""],
        ["--coverage"],
        ["--suite=lms"],
        ["--suite=lms --coverage"],
    )
    @ddt.unpack
    def test_test_js_run(self, options_string):
        """
        Test the "test_js_run" task.
        """
        options = self.parse_options_string(options_string)
        self.reset_task_messages()
        call_task("pavelib.js_test.test_js_run", options=options)
        self.verify_messages(options=options, dev_mode=False)

    @ddt.data(
        [""],
        ["--port=9999"],
        ["--suite=lms"],
        ["--suite=lms --port=9999"],
    )
    @ddt.unpack
    def test_test_js_dev(self, options_string):
        """
        Test the "test_js_run" task.
        """
        options = self.parse_options_string(options_string)
        self.reset_task_messages()
        call_task("pavelib.js_test.test_js_dev", options=options)
        self.verify_messages(options=options, dev_mode=True)

    def parse_options_string(self, options_string):
        """
        Parse a string containing the options for a test run
        """
        parameters = options_string.split(" ")
        suite = "all"
        if "--system=lms" in parameters:
            suite = "lms"
        elif "--system=common" in parameters:
            suite = "common"
        coverage = "--coverage" in parameters
        port = None
        if "--port=9999" in parameters:
            port = 9999
        return {
            "suite": suite,
            "coverage": coverage,
            "port": port,
        }

    def verify_messages(self, options, dev_mode):
        """
        Verify that the messages generated when running tests are as expected
        for the specified options and dev_mode.
        """
        is_coverage = options['coverage']
        port = options['port']
        expected_messages = []
        suites = Env.JS_TEST_ID_KEYS if options['suite'] == 'all' else [options['suite']]

        expected_messages.extend(self.EXPECTED_COMMANDS)
        if not dev_mode and not is_coverage:
            expected_messages.append(self.EXPECTED_DELETE_JAVASCRIPT_REPORT_COMMAND.format(
                platform_root=self.platform_root
            ))
        expected_messages.append(self.EXPECTED_INSTALL_NPM_ASSETS_COMMAND)
        expected_messages.append(self.EXPECTED_COFFEE_COMMAND.format(platform_root=self.platform_root))

        for suite in suites:
            # Karma test command
            karma_config_file = Env.KARMA_CONFIG_FILES[Env.JS_TEST_ID_KEYS.index(suite)]
            expected_test_tool_command = u'karma start {options}'.format(
                options=self.EXPECTED_KARMA_OPTIONS.format(
                    config_file=karma_config_file,
                    single_run='false' if dev_mode else 'true',
                    suite=suite,
                    platform_root=self.platform_root,
                ),
            )
            if is_coverage:
                expected_test_tool_command += self.EXPECTED_COVERAGE_OPTIONS.format(
                    platform_root=self.platform_root,
                    suite=suite
                )
            if port:
                expected_test_tool_command += u" --port={port}".format(port=port)
            expected_messages.append(expected_test_tool_command)

        self.assertEquals(self.task_messages, expected_messages)
