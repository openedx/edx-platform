"""Test safe_exec.py"""

import random
import unittest

from capa.safe_exec import safe_exec

class TestSafeExec(unittest.TestCase):
    def test_set_values(self):
        g, l = {}, {}
        safe_exec("a = 17", g, l)
        self.assertEqual(l['a'], 17)

    def test_division(self):
        g, l = {}, {}
        # Future division: 1/2 is 0.5.
        safe_exec("a = 1/2", g, l)
        self.assertEqual(l['a'], 0.5)

    def test_assumed_imports(self):
        g, l = {}, {}
        # Math is always available.
        safe_exec("a = int(math.pi)", g, l)
        self.assertEqual(l['a'], 3)

    def test_random_seeding(self):
        g, l = {}, {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in xrange(100)]

        # Without a seed, the results are unpredictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g, l)
        self.assertNotEqual(l['rnums'], rnums)

        # With a seed, the results are predictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g, l, random_seed=17)
        self.assertEqual(l['rnums'], rnums)
