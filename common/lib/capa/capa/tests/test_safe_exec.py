"""Test safe_exec.py"""

import os.path
import random
import unittest

from capa.safe_exec import safe_exec

class TestSafeExec(unittest.TestCase):
    def test_set_values(self):
        g = {}
        safe_exec("a = 17", g)
        self.assertEqual(g['a'], 17)

    def test_division(self):
        g = {}
        # Future division: 1/2 is 0.5.
        safe_exec("a = 1/2", g)
        self.assertEqual(g['a'], 0.5)

    def test_assumed_imports(self):
        g = {}
        # Math is always available.
        safe_exec("a = int(math.pi)", g)
        self.assertEqual(g['a'], 3)

    def test_random_seeding(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in xrange(100)]

        # Without a seed, the results are unpredictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g)
        self.assertNotEqual(g['rnums'], rnums)

        # With a seed, the results are predictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g, random_seed=17)
        self.assertEqual(g['rnums'], rnums)

    def test_python_lib(self):
        pylib = os.path.dirname(__file__) + "/test_files/pylib"
        g = {}
        safe_exec(
            "import constant; a = constant.THE_CONST",
            g, python_path=[pylib]
        )
