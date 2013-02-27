"""Test safe_exec.py"""

import os.path
import textwrap
import unittest
from nose.plugins.skip import SkipTest

from codejail.safe_exec import safe_exec, not_safe_exec

class SafeExecTests(object):
    """The tests for `safe_exec`, will be mixed into specific test classes below."""
    def test_set_values(self):
        g = {}
        self.safe_exec("a = 17", g)
        self.assertEqual(g['a'], 17)

    def test_assumed_imports(self):
        g = {}
        # Using string without importing it is bad.
        with self.assertRaises(Exception):
            self.safe_exec("a = string.ascii_lowercase[0]", g)
        # Using string with an assumed import is fine.
        self.safe_exec("a = string.ascii_lowercase[0]", g, assumed_imports=["string"])
        self.assertEqual(g['a'], 'a')
        # Can also import with a shorthand.
        self.safe_exec("a = op.join('x', 'y')", g, assumed_imports=[("op", "os.path")])
        self.assertEqual(g['a'][0], 'x')
        self.assertEqual(g['a'][-1], 'y')

    def test_files_are_copied(self):
        g = {}
        self.safe_exec(
            "a = 'Look: ' + open('hello.txt').read()", g,
            files=[os.path.dirname(__file__) + "/hello.txt"]
        )
        self.assertEqual(g['a'], 'Look: Hello there.\n')

    def test_python_path(self):
        g = {}
        self.safe_exec(
            "import module; a = module.const", g,
            python_path=[os.path.dirname(__file__) + "/pylib"]
        )
        self.assertEqual(g['a'], 42)

    def test_functions_calling_each_other(self):
        g = {}
        self.safe_exec(textwrap.dedent("""\
            def f():
                return 1723
            def g():
                return f()
            x = g()
            """), g)
        self.assertEqual(g['x'], 1723)

    def test_printing_stuff_when_you_shouldnt(self):
        g = {}
        self.safe_exec("a = 17; print 'hi!'", g)
        self.assertEqual(g['a'], 17)

    def test_importing_lots_of_crap(self):
        g = {}
        self.safe_exec(textwrap.dedent("""\
            from numpy import *
            a = 1723
            """), g)
        self.assertEqual(g['a'], 1723)


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
