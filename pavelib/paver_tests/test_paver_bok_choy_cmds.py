"""
Tests for the bok-choy paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_bok_choy_cmds.py
"""
import os
import unittest
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite

REPO_DIR = os.getcwd()


class TestPaverBokChoyCmd(unittest.TestCase):

    def _expected_command(self, name, store=None):
        expected_statement = (
            "DEFAULT_STORE={default_store} "
            "SCREENSHOT_DIR='{repo_dir}/test_root/log' "
            "BOK_CHOY_HAR_DIR='{repo_dir}/test_root/log/hars' "
            "SELENIUM_DRIVER_LOG_DIR='{repo_dir}/test_root/log' "
            "nosetests {repo_dir}/common/test/acceptance/{exp_text} "
            "--with-xunit "
            "--xunit-file={repo_dir}/reports/bok_choy/xunit.xml "
            "--verbosity=2 "
        ).format(
            default_store=store,
            repo_dir=REPO_DIR,
            exp_text=name,
        )
        return expected_statement

    def test_default(self):
        self.suite = BokChoyTestSuite('')
        name = 'tests'
        self.assertEqual(self.suite.cmd, self._expected_command(name=name))

    def test_suite_spec(self):
        spec = 'test_foo.py'
        self.suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(self.suite.cmd, self._expected_command(name=name))

    def test_class_spec(self):
        spec = 'test_foo.py:FooTest'
        self.suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(self.suite.cmd, self._expected_command(name=name))

    def test_testcase_spec(self):
        spec='test_foo.py:FooTest.test_bar'
        self.suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(self.suite.cmd, self._expected_command(name=name))

    def test_spec_with_draft_default_store(self):
        spec = 'test_foo.py'
        self.suite = BokChoyTestSuite('', test_spec=spec, default_store='draft')
        name = 'tests/{}'.format(spec)
        self.assertEqual(self.suite.cmd, self._expected_command(name=name, store='draft'))

    def test_invalid_default_store(self):
        # the cmd will dumbly compose whatever we pass in for the default_store
        self.suite = BokChoyTestSuite('', default_store='invalid')
        name = 'tests'
        self.assertEqual(self.suite.cmd, self._expected_command(name=name, store='invalid'))

    def test_test_dir(self):
        test_dir = 'foo'
        self.suite = BokChoyTestSuite('', test_dir=test_dir)
        self.assertEqual(self.suite.cmd, self._expected_command(name=test_dir))
