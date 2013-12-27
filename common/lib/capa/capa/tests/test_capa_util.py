"""
Tests for capa/util.py
"""
import unittest

from sys import float_info
from capa import util

epsilon = float_info.epsilon
fcmp = util.float_compare

class FloatCompareTest(unittest.TestCase):

    eq = lambda self, x, y:  self.assertTrue(fcmp(x, y))
    neq = lambda self, x, y:  self.assertFalse(fcmp(x, y))

    def test_examples(self):
        self.eq(0,0)
        self.eq(0.000016, 1.6*10**-5)
        self.eq(1.9e24, 1.9*10**24)
        self.eq(epsilon, epsilon)
        self.eq(-epsilon, -epsilon)

        # meaningful digits are same
        self.eq(3141592653589793238., 3141592653589793115.)

        self.neq(0.1234567890123457,   0.1234567890123456)
        self.eq(  0.1234567890123457,   0.1234567890123457)
        self.eq(  0.12345678901234577, 0.12345678901234579)

        self.neq(1.0, 2.0)
        self.neq(epsilon, -epsilon)
        self.neq(epsilon, 2 * epsilon)

        self.neq(0.00001600000000000001,   1.6*10**-5)
        self.eq(  0.000016000000000000001, 1.6*10**-5)





