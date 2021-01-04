"""
Tests covering the Open edX Paver prequisites installation workflow
"""


import os
import unittest

import mock
from mock import patch
from paver.easy import BuildFailure

import pavelib.prereqs
from pavelib.paver_tests.utils import PaverTestCase, fail_on_npm_install, unexpected_fail_on_npm_install


class TestPaverPrereqInstall(unittest.TestCase):
    """
    Test the status of the NO_PREREQ_INSTALL variable, its presence and how
    paver handles it.
    """
    def check_val(self, set_val, expected_val):
        """
        Verify that setting the variable to a certain value returns
        the expected boolean for it.

        As environment variables are only stored as strings, we have to cast
        whatever it's set at to a boolean that does not violate expectations.
        """
        _orig_environ = dict(os.environ)
        os.environ['NO_PREREQ_INSTALL'] = set_val
        self.assertEqual(
            pavelib.prereqs.no_prereq_install(),
            expected_val,
            'NO_PREREQ_INSTALL is set to {}, but we read it as {}'.format(
                set_val, expected_val),
        )

        # Reset Environment back to original state
        os.environ.clear()
        os.environ.update(_orig_environ)

    def test_no_prereq_install_true_lowercase(self):
        """
        Ensure that 'true' will be True.
        """
        self.check_val('true', True)

    def test_no_prereq_install_false_lowercase(self):
        """
        Ensure that 'false' will be False.
        """
        self.check_val('false', False)

    def test_no_prereq_install_true(self):
        """
        Ensure that 'True' will be True.
        """
        self.check_val('True', True)

    def test_no_prereq_install_false(self):
        """
        Ensure that 'False' will be False.
        """
        self.check_val('False', False)

    def test_no_prereq_install_0(self):
        """
        Ensure that '0' will be False.
        """
        self.check_val('0', False)

    def test_no_prereq_install_1(self):
        """
        Ensure that '1' will  be True.
        """
        self.check_val('1', True)


class TestPaverNodeInstall(PaverTestCase):
    """
    Test node install logic
    """

    def setUp(self):
        super().setUp()

        # Ensure prereqs will be run
        os.environ['NO_PREREQ_INSTALL'] = 'false'

    def test_npm_install_with_subprocess_error(self):
        """
        Test an error in 'npm install' execution
        """
        with patch('subprocess.Popen') as _mock_popen:
            _mock_subprocess = mock.Mock()
            attrs = {'wait': fail_on_npm_install}
            _mock_subprocess.configure_mock(**attrs)
            _mock_popen.return_value = _mock_subprocess
            with self.assertRaises(Exception):
                pavelib.prereqs.node_prereqs_installation()

        # npm install will be called twice
        self.assertEqual(_mock_popen.call_count, 2)

    def test_npm_install_called_once_when_successful(self):
        """
        Vanilla npm install should only be calling npm install one time
        """
        with patch('subprocess.Popen') as _mock_popen:
            pavelib.prereqs.node_prereqs_installation()
        # when there's no failure, npm install is only called once
        self.assertEqual(_mock_popen.call_count, 1)

    def test_npm_install_with_unexpected_subprocess_error(self):
        """
        If there's some other error, only call npm install once, and raise a failure
        """
        with patch('subprocess.Popen') as _mock_popen:
            _mock_popen.side_effect = unexpected_fail_on_npm_install
            with self.assertRaises(BuildFailure):
                pavelib.prereqs.node_prereqs_installation()
        self.assertEqual(_mock_popen.call_count, 1)
