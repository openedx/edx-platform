"""Test safe_exec.py"""

import hashlib
import os
import os.path
import random
import textwrap
import unittest

from nose.plugins.skip import SkipTest

from capa.safe_exec import safe_exec, update_hash
from codejail.safe_exec import SafeExecException
from codejail import is_configured


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

    def test_random_is_still_importable(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in xrange(100)]

        # With a seed, the results are predictable even from the random module
        safe_exec(
            "import random\n"
            "rnums = [random.randint(0, 999) for _ in xrange(100)]\n",
            g, random_seed=17)
        self.assertEqual(g['rnums'], rnums)

    def test_python_lib(self):
        pylib = os.path.dirname(__file__) + "/test_files/pylib"
        g = {}
        safe_exec(
            "import constant; a = constant.THE_CONST",
            g, python_path=[pylib]
        )

    def test_raising_exceptions(self):
        g = {}
        with self.assertRaises(SafeExecException) as cm:
            safe_exec("1/0", g)
        self.assertIn("ZeroDivisionError", cm.exception.message)


class TestSafeOrNot(unittest.TestCase):
    def test_cant_do_something_forbidden(self):
        # Can't test for forbiddenness if CodeJail isn't configured for python.
        if not is_configured("python"):
            raise SkipTest

        g = {}
        with self.assertRaises(SafeExecException) as cm:
            safe_exec("import os; files = os.listdir('/')", g)
        self.assertIn("OSError", cm.exception.message)
        self.assertIn("Permission denied", cm.exception.message)

    def test_can_do_something_forbidden_if_run_unsafely(self):
        g = {}
        safe_exec("import os; files = os.listdir('/')", g, unsafely=True)
        self.assertEqual(g['files'], os.listdir('/'))


class DictCache(object):
    """A cache implementation over a simple dict, for testing."""

    def __init__(self, d):
        self.cache = d

    def get(self, key):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        return self.cache.get(key)

    def set(self, key, value):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        self.cache[key] = value


class TestSafeExecCaching(unittest.TestCase):
    """Test that caching works on safe_exec."""

    def test_cache_miss_then_hit(self):
        g = {}
        cache = {}

        # Cache miss
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        self.assertEqual(g['a'], 3)
        # A result has been cached
        self.assertEqual(cache.values()[0], (None, {'a': 3}))

        # Fiddle with the cache, then try it again.
        cache[cache.keys()[0]] = (None, {'a': 17})

        g = {}
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        self.assertEqual(g['a'], 17)

    def test_cache_large_code_chunk(self):
        # Caching used to die on memcache with more than 250 bytes of code.
        # Check that it doesn't any more.
        code = "a = 0\n" + ("a += 1\n" * 12345)

        g = {}
        cache = {}
        safe_exec(code, g, cache=DictCache(cache))
        self.assertEqual(g['a'], 12345)

    def test_cache_exceptions(self):
        # Used to be that running code that raised an exception didn't cache
        # the result.  Check that now it does.
        code = "1/0"
        g = {}
        cache = {}
        with self.assertRaises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        # The exception should be in the cache now.
        self.assertEqual(len(cache), 1)
        cache_exc_msg, cache_globals = cache.values()[0]
        self.assertIn("ZeroDivisionError", cache_exc_msg)

        # Change the value stored in the cache, the result should change.
        cache[cache.keys()[0]] = ("Hey there!", {})

        with self.assertRaises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        self.assertEqual(len(cache), 1)
        cache_exc_msg, cache_globals = cache.values()[0]
        self.assertEqual("Hey there!", cache_exc_msg)

        # Change it again, now no exception!
        cache[cache.keys()[0]] = (None, {'a': 17})
        safe_exec(code, g, cache=DictCache(cache))
        self.assertEqual(g['a'], 17)

    def test_unicode_submission(self):
        # Check that using non-ASCII unicode does not raise an encoding error.
        # Try several non-ASCII unicode characters.
        for code in [129, 500, 2 ** 8 - 1, 2 ** 16 - 1]:
            code_with_unichr = unicode("# ") + unichr(code)
            try:
                safe_exec(code_with_unichr, {}, cache=DictCache({}))
            except UnicodeEncodeError:
                self.fail("Tried executing code with non-ASCII unicode: {0}".format(code))


class TestUpdateHash(unittest.TestCase):
    """Test the safe_exec.update_hash function to be sure it canonicalizes properly."""

    def hash_obj(self, obj):
        """Return the md5 hash that `update_hash` makes us."""
        md5er = hashlib.md5()
        update_hash(md5er, obj)
        return md5er.hexdigest()

    def equal_but_different_dicts(self):
        """
        Make two equal dicts with different key order.

        Simple literals won't do it.  Filling one and then shrinking it will
        make them different.

        """
        d1 = {k: 1 for k in "abcdefghijklmnopqrstuvwxyz"}
        d2 = dict(d1)
        for i in xrange(10000):
            d2[i] = 1
        for i in xrange(10000):
            del d2[i]

        # Check that our dicts are equal, but with different key order.
        self.assertEqual(d1, d2)
        self.assertNotEqual(d1.keys(), d2.keys())

        return d1, d2

    def test_simple_cases(self):
        h1 = self.hash_obj(1)
        h10 = self.hash_obj(10)
        hs1 = self.hash_obj("1")

        self.assertNotEqual(h1, h10)
        self.assertNotEqual(h1, hs1)

    def test_list_ordering(self):
        h1 = self.hash_obj({'a': [1, 2, 3]})
        h2 = self.hash_obj({'a': [3, 2, 1]})
        self.assertNotEqual(h1, h2)

    def test_dict_ordering(self):
        d1, d2 = self.equal_but_different_dicts()
        h1 = self.hash_obj(d1)
        h2 = self.hash_obj(d2)
        self.assertEqual(h1, h2)

    def test_deep_ordering(self):
        d1, d2 = self.equal_but_different_dicts()
        o1 = {'a': [1, 2, [d1], 3, 4]}
        o2 = {'a': [1, 2, [d2], 3, 4]}
        h1 = self.hash_obj(o1)
        h2 = self.hash_obj(o2)
        self.assertEqual(h1, h2)


class TestRealProblems(unittest.TestCase):
    def test_802x(self):
        code = textwrap.dedent("""\
            import math
            import random
            import numpy
            e=1.602e-19 #C
            me=9.1e-31  #kg
            mp=1.672e-27 #kg
            eps0=8.854e-12 #SI units
            mu0=4e-7*math.pi #SI units

            Rd1=random.randrange(1,30,1)
            Rd2=random.randrange(30,50,1)
            Rd3=random.randrange(50,70,1)
            Rd4=random.randrange(70,100,1)
            Rd5=random.randrange(100,120,1)

            Vd1=random.randrange(1,20,1)
            Vd2=random.randrange(20,40,1)
            Vd3=random.randrange(40,60,1)

            #R=[0,10,30,50,70,100] #Ohm
            #V=[0,12,24,36] # Volt

            R=[0,Rd1,Rd2,Rd3,Rd4,Rd5] #Ohms
            V=[0,Vd1,Vd2,Vd3] #Volts
            #here the currents IL and IR are defined as in figure ps3_p3_fig2
            a=numpy.array([  [  R[1]+R[4]+R[5],R[4] ],[R[4], R[2]+R[3]+R[4] ] ])
            b=numpy.array([V[1]-V[2],-V[3]-V[2]])
            x=numpy.linalg.solve(a,b)
            IL='%.2e' % x[0]
            IR='%.2e' % x[1]
            ILR='%.2e' % (x[0]+x[1])
            def sign(x):
                return abs(x)/x

            RW="Rightwards"
            LW="Leftwards"
            UW="Upwards"
            DW="Downwards"
            I1='%.2e' % abs(x[0])
            I1d=LW if sign(x[0])==1 else RW
            I1not=LW if I1d==RW else RW
            I2='%.2e' % abs(x[1])
            I2d=RW if sign(x[1])==1 else LW
            I2not=LW if I2d==RW else RW
            I3='%.2e' % abs(x[1])
            I3d=DW if sign(x[1])==1 else UW
            I3not=DW if I3d==UW else UW
            I4='%.2e' % abs(x[0]+x[1])
            I4d=UW if sign(x[1]+x[0])==1 else DW
            I4not=DW if I4d==UW else UW
            I5='%.2e' % abs(x[0])
            I5d=RW if sign(x[0])==1 else LW
            I5not=LW if I5d==RW else RW
            VAP=-x[0]*R[1]-(x[0]+x[1])*R[4]
            VPN=-V[2]
            VGD=+V[1]-x[0]*R[1]+V[3]+x[1]*R[2]
            aVAP='%.2e' % VAP
            aVPN='%.2e' % VPN
            aVGD='%.2e' % VGD
            """)
        g = {}
        safe_exec(code, g)
        self.assertIn("aVAP", g)
