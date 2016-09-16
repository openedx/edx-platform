"""
Tests for the bok-choy paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_bok_choy_cmds.py
"""
import os
import unittest
from paver.easy import BuildFailure
from pavelib.utils.test.suites import BokChoyTestSuite

REPO_DIR = os.getcwd()


class TestPaverBokChoyCmd(unittest.TestCase):
    """
    Paver Bok Choy Command test cases
    """

    def _expected_command(self, name, store=None):
        """
        Returns the command that is expected to be run for the given test spec
        and store.
        """

        expected_statement = (
            "DEFAULT_STORE={default_store} "
            "SCREENSHOT_DIR='{repo_dir}/test_root/log{shard_str}' "
            "BOK_CHOY_HAR_DIR='{repo_dir}/test_root/log{shard_str}/hars' "
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{repo_dir}/{a11y_custom_file}' "
            "SELENIUM_DRIVER_LOG_DIR='{repo_dir}/test_root/log{shard_str}' "
            "nosetests {repo_dir}/common/test/acceptance/{exp_text} "
            "--with-xunit "
            "--xunit-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml "
            "--verbosity=2 "
        ).format(
            default_store=store,
            repo_dir=REPO_DIR,
            shard_str='/shard_' + self.shard if self.shard else '',
            exp_text=name,
            a11y_custom_file='node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js',
        )
        return expected_statement

    def setUp(self):
        super(TestPaverBokChoyCmd, self).setUp()
        self.shard = os.environ.get('SHARD')

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
        self.assertEqual(suite.cmd, "")

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
        expected_verbosity_string = (
            "--with-xunit --xunit-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml --verbosity=2".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else ''
            )
        )
        suite = BokChoyTestSuite('', num_processes=1)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_verbosity_settings_2_processes(self):
        """
        Using multiple processes means specific xunit, coloring, and process-related settings should
        be used.
        """
        process_count = 2
        expected_verbosity_string = (
            "--with-xunitmp --xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml"
            " --processes={procs} --no-color --process-timeout=1200".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
                procs=process_count
            )
        )
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_verbosity_settings_3_processes(self):
        """
        With the above test, validate that num_processes can be set to various values
        """
        process_count = 3
        expected_verbosity_string = (
            "--with-xunitmp --xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml"
            " --processes={procs} --no-color --process-timeout=1200".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
                procs=process_count
            )
        )
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_invalid_verbosity_and_processes(self):
        """
        If an invalid combination of verbosity and number of processors is passed in, a
        BuildFailure should be raised
        """
        suite = BokChoyTestSuite('', num_processes=2, verbosity=3)
        with self.assertRaises(BuildFailure):
            BokChoyTestSuite.verbosity_processes_string(suite)
