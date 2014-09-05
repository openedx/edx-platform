
import os
import unittest
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite

REPO_DIR = os.getcwd()


class TestPaverBokChoy(unittest.TestCase):

    def setUp(self):
        self.request = BokChoyTestSuite('')

    def _expected_command(self, expected_text_append):
        if expected_text_append:
            expected_text_append = "/" + expected_text_append
        expected_statement = ("SCREENSHOT_DIR='{repo_dir}/test_root/log' "
                                       "HAR_DIR='{repo_dir}/test_root/log/hars' "
                                       "SELENIUM_DRIVER_LOG_DIR='{repo_dir}/test_root/log' "
                                       "nosetests {repo_dir}/common/test/acceptance/tests{exp_text} "
                                       "--with-xunit "
                                       "--xunit-file={repo_dir}/reports/bok_choy/xunit.xml "
                                       "--verbosity=2 ".format(repo_dir=REPO_DIR,
                                                               exp_text=expected_text_append))
        return expected_statement

    def test_default_bokchoy(self):
        self.assertEqual(self.request.cmd, self._expected_command(''))

    def test_suite_request_bokchoy(self):
        self.request.test_spec = "test_foo.py"
        self.assertEqual(self.request.cmd, self._expected_command(self.request.test_spec))

    def test_class_request_bokchoy(self):
        self.request.test_spec = "test_foo.py:FooTest"
        self.assertEqual(self.request.cmd, self._expected_command(self.request.test_spec))

    def test_case_request_bokchoy(self):
        self.request.test_spec = "test_foo.py:FooTest.test_bar"
        self.assertEqual(self.request.cmd, self._expected_command(self.request.test_spec))


    # TODO: Test when bok_choy test file is in a subdir