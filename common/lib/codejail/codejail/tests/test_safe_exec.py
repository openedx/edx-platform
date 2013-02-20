"""Test safe_exec.py"""

import os.path
import unittest
from nose.plugins.skip import SkipTest

from codejail.safe_exec import safe_exec, not_safe_exec

class SafeExecTests(object):
    """The tests for `safe_exec`, will be mixed into specific test classes below."""
    def test_set_values(self):
        g, l = {}, {}
        self.safe_exec("a = 17", g, l)
        self.assertEqual(l['a'], 17)

    def test_assumed_imports(self):
        g, l = {}, {}
        # Using string without importing it is bad.
        with self.assertRaises(Exception):
            self.safe_exec("a = string.ascii_lowercase[0]", g, l)
        # Using string with an assumed import is fine.
        self.safe_exec("a = string.ascii_lowercase[0]", g, l, assumed_imports=["string"])
        self.assertEqual(l['a'], 'a')
        # Can also import with a shorthand.
        self.safe_exec("a = op.join('x', 'y')", g, l, assumed_imports=[("op", "os.path")])
        self.assertEqual(l['a'][0], 'x')
        self.assertEqual(l['a'][-1], 'y')

    def test_files_are_copied(self):
        g, l = {}, {}
        self.safe_exec(
            "a = 'Look: ' + open('hello.txt').read()", g, l,
            files=[os.path.dirname(__file__) + "/hello.txt"]
        )
        self.assertEqual(l['a'], 'Look: Hello there.\n')

    def test_python_path(self):
        g, l = {}, {}
        self.safe_exec(
            "import module; a = module.const", g, l,
            python_path=[os.path.dirname(__file__) + "/pylib"]
        )
        self.assertEqual(l['a'], 42)


class TestSafeExec(SafeExecTests, unittest.TestCase):
    """Run SafeExecTests, with the real safe_exec."""
    def safe_exec(self, *args, **kwargs):
        safe_exec(*args, **kwargs)

class TestNotSafeExec(SafeExecTests, unittest.TestCase):
    """Run SafeExecTests, with not_safe_exec."""
    def setUp(self):
        if safe_exec is not_safe_exec:
            raise SkipTest

    def safe_exec(self, *args, **kwargs):
        not_safe_exec(*args, **kwargs)
