"""
Tests for pavelib/utils/test/utils
"""

from pavelib.utils.test.utils import check_firefox_version, MINIMUM_FIREFOX_VERSION
import unittest
from mock import patch


class TestUtils(unittest.TestCase):
    """
    Test utils.py under pavelib/utils/test
    """

    @patch('subprocess.check_output')
    def test_firefox_version_ok(self, _mock_subprocesss):
        test_version = MINIMUM_FIREFOX_VERSION
        _mock_subprocesss.return_value = "Mozilla Firefox {version}".format(
            version=str(test_version)
        )
        # No exception should be raised
        check_firefox_version()

    @patch('subprocess.check_output')
    def test_firefox_version_below_expected(self, _mock_subprocesss):
        test_version = MINIMUM_FIREFOX_VERSION - 1
        _mock_subprocesss.return_value = "Mozilla Firefox {version}".format(
            version=test_version
        )
        with self.assertRaises(Exception):
            check_firefox_version()

    @patch('subprocess.check_output')
    def test_firefox_version_not_detected(self, _mock_subprocesss):
        _mock_subprocesss.return_value = "Mozilla Firefox"
        with self.assertRaises(Exception):
            check_firefox_version()

    @patch('subprocess.check_output')
    def test_firefox_version_bad(self, _mock_subprocesss):
        _mock_subprocesss.return_value = "garbage"
        with self.assertRaises(Exception):
            check_firefox_version()
