"""Test lazymod.py"""

import sys
import unittest

from codejail.lazymod import LazyModule
from codejail.util import ModuleIsolation


class TestLazyMod(unittest.TestCase):

    def setUp(self):
        # Each test will remove modules that it imported.
        self.addCleanup(ModuleIsolation().clean_up)

    def test_simple(self):
        # Import some stdlib module that has not been imported before
        self.assertNotIn("colorsys", sys.modules)
        colorsys = LazyModule("colorsys")
        hsv = colorsys.rgb_to_hsv(.3, .4, .2)
        self.assertEqual(hsv[0], 0.25)

    def test_dotted(self):
        self.assertNotIn("email.utils", sys.modules)
        email_utils = LazyModule("email.utils")
        self.assertEqual(email_utils.quote('"hi"'), r'\"hi\"')
