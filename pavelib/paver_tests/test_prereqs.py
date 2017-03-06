"""
Tests covering the Open edX Paver prequisites installation workflow
"""

import os
import unittest
from pavelib.prereqs import no_prereq_install


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
