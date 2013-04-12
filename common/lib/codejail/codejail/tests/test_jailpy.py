"""Test jail_code.py"""

import os.path
import textwrap
import unittest
from nose.plugins.skip import SkipTest

from codejail.jail_code import jail_code, is_configured

dedent = textwrap.dedent


def jailpy(*args, **kwargs):
    """Run `jail_code` on Python."""
    return jail_code("python", *args, **kwargs)


def file_here(fname):
    """Return the full path to a file alongside this code."""
    return os.path.join(os.path.dirname(__file__), fname)


class JailCodeHelpers(object):
    """Assert helpers for jail_code tests."""
    def setUp(self):
        super(JailCodeHelpers, self).setUp()
        if not is_configured("python"):
            raise SkipTest

    def assertResultOk(self, res):
        self.assertEqual(res.stderr, "")
        self.assertEqual(res.status, 0)


class TestFeatures(JailCodeHelpers, unittest.TestCase):
    def test_hello_world(self):
        res = jailpy(code="print 'Hello, world!'")
        self.assertResultOk(res)
        self.assertEqual(res.stdout, 'Hello, world!\n')

    def test_argv(self):
        res = jailpy(
                code="import sys; print ':'.join(sys.argv[1:])",
                argv=["Hello", "world", "-x"]
                )
        self.assertResultOk(res)
        self.assertEqual(res.stdout, "Hello:world:-x\n")

    def test_ends_with_exception(self):
        res = jailpy(code="""raise Exception('FAIL')""")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")
        self.assertEqual(res.stderr, dedent("""\
            Traceback (most recent call last):
              File "jailed_code", line 1, in <module>
                raise Exception('FAIL')
            Exception: FAIL
            """))

    def test_stdin_is_provided(self):
        res = jailpy(
            code="import json,sys; print sum(json.load(sys.stdin))",
            stdin="[1, 2.5, 33]"
        )
        self.assertResultOk(res)
        self.assertEqual(res.stdout.strip(), "36.5")

    def test_files_are_copied(self):
        res = jailpy(
            code="print 'Look:', open('hello.txt').read()",
            files=[file_here("hello.txt")]
        )
        self.assertResultOk(res)
        self.assertEqual(res.stdout, 'Look: Hello there.\n\n')

    def test_executing_a_copied_file(self):
        res = jailpy(
            files=[file_here("doit.py")],
            argv=["doit.py", "1", "2", "3"]
        )
        self.assertResultOk(res)
        self.assertEqual(res.stdout, "This is doit.py!\nMy args are ['doit.py', '1', '2', '3']\n")


class TestLimits(JailCodeHelpers, unittest.TestCase):
    def test_cant_use_too_much_memory(self):
        res = jailpy(code="print sum(range(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_cpu(self):
        res = jailpy(code="print sum(xrange(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_time(self):
        raise SkipTest  # TODO: test this once we can kill sleeping processes.
        res = jailpy(code=dedent("""\
                import time
                time.sleep(5)
                print 'Done!'
                """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_write_files(self):
        res = jailpy(code=dedent("""\
                print "Trying"
                with open("mydata.txt", "w") as f:
                    f.write("hello")
                with open("mydata.txt") as f2:
                    print "Got this:", f2.read()
                """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "Trying\n")
        self.assertIn("ermission denied", res.stderr)

    def test_cant_use_network(self):
        res = jailpy(code=dedent("""\
                import urllib
                print "Reading google"
                u = urllib.urlopen("http://google.com")
                google = u.read()
                print len(google)
                """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "Reading google\n")
        self.assertIn("IOError", res.stderr)

    # TODO: write files
    # TODO: read network
    # TODO: fork


class TestMalware(JailCodeHelpers, unittest.TestCase):
    def test_crash_cpython(self):
        # http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
        res = jailpy(code=dedent("""\
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
        res = jailpy(code=dedent("""\
            bytes = len(open('/etc/passwd').read())
            print 'Gotcha', bytes
            """))
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")
        self.assertIn("ermission denied", res.stderr)

    def test_find_other_sandboxes(self):
        res = jailpy(code=dedent("""
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
