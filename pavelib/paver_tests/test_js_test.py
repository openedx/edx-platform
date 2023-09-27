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

    @ddt.data(
        [""],
        ["--port=9999"],
        ["--suite=lms"],
        ["--suite=lms --port=9999"],
    )
    
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