"""
Tests covering the Open edX Paver prequisites installation workflow
"""

import os
import unittest
from mock import call, patch
from paver.easy import BuildFailure
from pavelib.prereqs import no_prereq_install, node_prereqs_installation
from pavelib.paver_tests.utils import PaverTestCase, CustomShMock
from pavelib.paver_tests.test_paver_quality import CustomShMock


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
            no_prereq_install(),
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
        super(TestPaverNodeInstall, self).setUp()
        os.environ['NO_PREREQ_INSTALL'] = 'false'
        patcher = patch('pavelib.prereqs.sh', return_value=True)
        self._mock_paver_sh = patcher.start()
        self.addCleanup(patcher.stop)

    def test_npm_install_with_subprocess_error(self):
        """
        Test that we handle a subprocess 1 (proxy for cb() never called error)
        TE-1767
        """
        self._mock_paver_sh.side_effect = CustomShMock().fail_on_npm_install
        with self.assertRaises(BuildFailure):
            node_prereqs_installation()
        actual_calls = self._mock_paver_sh.mock_calls

        # npm install will be called twice
        self.assertEqual(actual_calls.count(call('npm install')), 2)

    def test_npm_install_called_once_when_successful(self):
        """
        Vanilla npm install should only be calling npm install one time
        """
        node_prereqs_installation()
        actual_calls = self._mock_paver_sh.mock_calls

        # when there's no failure, npm install is only called once
        self.assertEqual(actual_calls.count(call('npm install')), 1)

    def test_npm_install_with_unexpected_subprocess_error(self):
        """
        If there's some other error, only call npm install once, and raise a failure
        """
        self._mock_paver_sh.side_effect = CustomShMock().unexpected_fail_on_npm_install
        with self.assertRaises(BuildFailure):
            node_prereqs_installation()
        actual_calls = self._mock_paver_sh.mock_calls

        self.assertEqual(actual_calls.count(call('npm install')), 1)
