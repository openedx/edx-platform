"""
Tests for the bok-choy paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_bok_choy_cmds.py
"""


import os
import unittest

from test.support import EnvironmentVarGuard

from pavelib.utils.test.suites import BokChoyTestSuite

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
            f"DEFAULT_STORE={store}",
            f"SAVED_SOURCE_DIR='{REPO_DIR}/test_root/log{shard_str}'",
            f"SCREENSHOT_DIR='{REPO_DIR}/test_root/log{shard_str}'",
            f"BOK_CHOY_HAR_DIR='{REPO_DIR}/test_root/log{shard_str}/hars'",
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{}/{}'".format(
                REPO_DIR,
                'node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js'
            ),
            f"SELENIUM_DRIVER_LOG_DIR='{REPO_DIR}/test_root/log{shard_str}'",
            f"VERIFY_XSS='{verify_xss}'",
            "python",
            "-Wd",
            "-m",
            "pytest",
            f"{REPO_DIR}/common/test/acceptance/{name}",
            f"--junitxml={REPO_DIR}/reports/bok_choy{shard_str}/xunit.xml",
            "--verbose",
        ]
        return expected_statement

    def setUp(self):
        super().setUp()
        self.shard = os.environ.get('SHARD')
        self.env_var_override = EnvironmentVarGuard()

    def test_default(self):
        suite = BokChoyTestSuite('')
        name = 'tests'
        assert suite.cmd == self._expected_command(name=name)

    def test_suite_spec(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = f'tests/{spec}'
        assert suite.cmd == self._expected_command(name=name)

    def test_class_spec(self):
        spec = 'test_foo.py:FooTest'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = f'tests/{spec}'
        assert suite.cmd == self._expected_command(name=name)

    def test_testcase_spec(self):
        spec = 'test_foo.py:FooTest.test_bar'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = f'tests/{spec}'
        assert suite.cmd == self._expected_command(name=name)

    def test_spec_with_draft_default_store(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec, default_store='draft')
        name = f'tests/{spec}'
        assert suite.cmd == self._expected_command(name=name, store='draft')

    def test_invalid_default_store(self):
        # the cmd will dumbly compose whatever we pass in for the default_store
        suite = BokChoyTestSuite('', default_store='invalid')
        name = 'tests'
        assert suite.cmd == self._expected_command(name=name, store='invalid')

    def test_serversonly(self):
        suite = BokChoyTestSuite('', serversonly=True)
        assert suite.cmd is None

    def test_verify_xss(self):
        suite = BokChoyTestSuite('', verify_xss=True)
        name = 'tests'
        assert suite.cmd == self._expected_command(name=name, verify_xss=True)

    def test_verify_xss_env_var(self):
        self.env_var_override.set('VERIFY_XSS', 'False')
        with self.env_var_override:
            suite = BokChoyTestSuite('')
            name = 'tests'
            assert suite.cmd == self._expected_command(name=name, verify_xss=False)

    def test_test_dir(self):
        test_dir = 'foo'
        suite = BokChoyTestSuite('', test_dir=test_dir)
        assert suite.cmd == self._expected_command(name=test_dir)

    def test_verbosity_settings_1_process(self):
        """
        Using 1 process means paver should ask for the traditional xunit plugin for plugin results
        """
        expected_verbosity_command = [
            "--junitxml={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else ''
            ),
            "--verbose",
        ]
        suite = BokChoyTestSuite('', num_processes=1)
        assert suite.verbosity_processes_command == expected_verbosity_command

    def test_verbosity_settings_2_processes(self):
        """
        Using multiple processes means specific xunit, coloring, and process-related settings should
        be used.
        """
        process_count = 2
        expected_verbosity_command = [
            "--junitxml={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
            ),
            f"-n {process_count}",
            "--color=no",
            "--verbose",
        ]
        suite = BokChoyTestSuite('', num_processes=process_count)
        assert suite.verbosity_processes_command == expected_verbosity_command

    def test_verbosity_settings_3_processes(self):
        """
        With the above test, validate that num_processes can be set to various values
        """
        process_count = 3
        expected_verbosity_command = [
            "--junitxml={repo_dir}/reports/bok_choy{shard_str}/xunit.xml".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
            ),
            f"-n {process_count}",
            "--color=no",
            "--verbose",
        ]
        suite = BokChoyTestSuite('', num_processes=process_count)
        assert suite.verbosity_processes_command == expected_verbosity_command
