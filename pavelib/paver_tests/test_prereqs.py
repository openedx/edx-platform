
import os
import unittest
from pavelib.prereqs import no_prereq_install


class TestPaverPrereqInstall(unittest.TestCase):

    def check_val(self, set_val, expected_val):
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

    def test_no_prereq_install_true(self):
        self.check_val('true', True)

    def test_no_prereq_install_false(self):
        self.check_val('false', False)

    def test_no_prereq_install_True(self):
        self.check_val('True', True)

    def test_no_prereq_install_False(self):
        self.check_val('False', False)

    def test_no_prereq_install_0(self):
        self.check_val('0', False)

    def test_no_prereq_install_1(self):
        self.check_val('1', True)
