import textwrap
import unittest

from codejail.jailpy import jailpy

dedent = textwrap.dedent

class TestFeatures(unittest.TestCase):
    def test_hello_world(self):
        res = jailpy("print 'Hello, world!'")
        self.assertEqual(res.status, 0)
        self.assertEqual(res.stdout, 'Hello, world!\n')

    def test_argv(self):
        res = jailpy(
                "import sys; print ':'.join(sys.argv[1:])",
                argv=["Hello", "world", "-x"]
                )
        self.assertEqual(res.status, 0)
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


class TestLimits(unittest.TestCase):
    def test_cant_use_too_much_memory(self):
        res = jailpy("print sum(range(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_cpu(self):
        res = jailpy("print sum(xrange(100000000))")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")

    def test_cant_use_too_much_time(self):
        res = jailpy("import time; time.sleep(5); print 'Done!'")
        self.assertNotEqual(res.status, 0)
        self.assertEqual(res.stdout, "")
