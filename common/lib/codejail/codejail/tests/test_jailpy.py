"""Test jailpy.py"""

import os.path
import textwrap
import unittest
from nose.plugins.skip import SkipTest

from codejail.jailpy import jailpy, is_configured

dedent = textwrap.dedent

class JailPyHelpers(object):
    """Assert helpers for jailpy tests."""
    def setUp(self):
        super(JailPyHelpers, self).setUp()
        if not is_configured():
            raise SkipTest

    def assertResultOk(self, res):
        self.assertEqual(res.stderr, "")
        self.assertEqual(res.status, 0)


class TestFeatures(JailPyHelpers, unittest.TestCase):
    def test_hello_world(self):
        res = jailpy("print 'Hello, world!'")
        self.assertResultOk(res)
        self.assertEqual(res.stdout, 'Hello, world!\n')

    def test_argv(self):
        res = jailpy(
                "import sys; print ':'.join(sys.argv[1:])",
                argv=["Hello", "world", "-x"]
                )
        self.assertResultOk(res)
        self.assertEqual(res.stdout, "Hello:world:-x\n")

    def test_ends_with_exception(self):
        res = jailpy("""raise Exception('FAIL')""")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")
        self.assertEqual(res.stderr, dedent("""\
            Traceback (most recent call last):
              File "jailed_code.py", line 1, in <module>
                raise Exception('FAIL')
            Exception: FAIL
            """))

    def test_stdin_is_provided(self):
        res = jailpy(
            "import json,sys; print sum(json.load(sys.stdin))",
            stdin="[1, 2.5, 33]"
        )
        self.assertResultOk(res)
        self.assertEqual(res.stdout.strip(), "36.5")

    def test_files_are_copied(self):
        res = jailpy(
            "print 'Look:', open('hello.txt').read()",
            files=[os.path.dirname(__file__) + "/hello.txt"]
        )
        self.assertResultOk(res)
        self.assertEqual(res.stdout, 'Look: Hello there.\n\n')


class TestLimits(JailPyHelpers, unittest.TestCase):
    def test_cant_use_too_much_memory(self):
        res = jailpy("print sum(range(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_cpu(self):
        res = jailpy("print sum(xrange(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_time(self):
        raise SkipTest  # TODO: test this once we can kill sleeping processes.
        res = jailpy(dedent("""\
                import time
                time.sleep(5)
                print 'Done!'
                """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_write_files(self):
        res = jailpy(dedent("""\
                print "Trying"
                with open("mydata.txt", "w") as f:
                    f.write("hello")
                with open("mydata.txt") as f2:
                    print "Got this:", f2.read()
                """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "Trying\n")
        self.assertIn("ermission denied", res.stderr)

    # TODO: write files
    # TODO: read network
    # TODO: fork

class TestMalware(JailPyHelpers, unittest.TestCase):
    def test_crash_cpython(self):
        # http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
        res = jailpy(dedent("""\
            import new, sys
            crash_me = new.function(new.code(0,0,0,0,"KABOOM",(),(),(),"","",0,""), {})
            print "Here we go..."
            sys.stdout.flush()
            crash_me()
            print "The afterlife!"
            """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "Here we go...\n")
        self.assertEqual(res.stderr, "")

    def test_read_etc_passwd(self):
        res = jailpy(dedent("""\
            bytes = len(open('/etc/passwd').read())
            print 'Gotcha', bytes
            """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")
        self.assertIn("ermission denied", res.stderr)

    def test_find_other_sandboxes(self):
        res = jailpy(dedent("""
            import os;
            places = [
                "..", "/tmp", "/", "/home", "/etc",
                "/var"
                ]
            for place in places:
                try:
                    files = os.listdir(place)
                except Exception:
                    # darn
                    pass
                else:
                    print "Files in %r: %r" % (place, files)
            print "Done."
            """))
        self.assertResultOk(res)
        self.assertEqual(res.stdout, "Done.\n")
