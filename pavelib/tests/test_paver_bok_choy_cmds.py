
import os
import unittest
from pavelib.utils.test.suites.bokchoy_suite import BokChoyTestSuite

REPO_DIR = os.getcwd()


class TestPaverBokChoy(unittest.TestCase):

    def test_default_bokchoy(self):
        command = BokChoyTestSuite('paver -t test_bokchoy')
        expected_output = ("SCREENSHOT_DIR='{repo_dir}/test_root/log' "
                                       "HAR_DIR='{repo_dir}/test_root/log/hars' "
                                       "SELENIUM_DRIVER_LOG_DIR='{repo_dir}/test_root/log' "
                                       "nosetests {repo_dir}/common/test/acceptance/tests "
                                       "--with-xunit "
                                       "--xunit-file={repo_dir}/reports/bok_choy/xunit.xml "
                                       "--verbosity=2 ".format(repo_dir=REPO_DIR))
        print expected_output
        self.assertTrue(command.cmd == expected_output)
