"""Unit tests for the Paver JavaScript testing tasks."""

from unittest.mock import patch

import ddt
from paver.easy import call_task

import pavelib.js_test
from pavelib.utils.envs import Env

from .utils import PaverTestCase


@ddt.ddt
class TestPaverJavaScriptTestTasks(PaverTestCase):
    """
    Test the Paver JavaScript testing tasks.
    """

    EXPECTED_DELETE_JAVASCRIPT_REPORT_COMMAND = 'find {platform_root}/reports/javascript -type f -delete'
    EXPECTED_INSTALL_NPM_ASSETS_COMMAND = 'install npm_assets'
    EXPECTED_KARMA_OPTIONS = (
        "{config_file} "
        "--single-run={single_run} "
        "--capture-timeout=60000 "
        "--junitreportpath="
        "{platform_root}/reports/javascript/javascript_xunit-{suite}.xml "
        "--browsers={browser}"
    )
    EXPECTED_COVERAGE_OPTIONS = (
        ' --coverage --coveragereportpath={platform_root}/reports/javascript/coverage-{suite}.xml'
    )

    EXPECTED_COMMANDS = [
        "make report_dir",
        'git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads',
        "find . -name '.git' -prune -o -name '*.pyc' -exec rm {} \\;",
        'rm -rf test_root/log/auto_screenshots/*',
        "rm -rf /tmp/mako_[cl]ms",
    ]

    def setUp(self):
        super().setUp()

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

        command_template = (
            'node --max_old_space_size=4096 node_modules/.bin/karma start {options}'
        )

        for suite in suites:
            # Karma test command
            if suite != 'jest-snapshot':
                karma_config_file = Env.KARMA_CONFIG_FILES[Env.JS_TEST_ID_KEYS.index(suite)]
                expected_test_tool_command = command_template.format(
                    options=self.EXPECTED_KARMA_OPTIONS.format(
                        config_file=karma_config_file,
                        single_run='false' if dev_mode else 'true',
                        suite=suite,
                        platform_root=self.platform_root,
                        browser=Env.KARMA_BROWSER,
                    ),
                )
                if is_coverage:
                    expected_test_tool_command += self.EXPECTED_COVERAGE_OPTIONS.format(
                        platform_root=self.platform_root,
                        suite=suite
                    )
                if port:
                    expected_test_tool_command += f" --port={port}"
            else:
                expected_test_tool_command = 'jest'

            expected_messages.append(expected_test_tool_command)

        assert self.task_messages == expected_messages
