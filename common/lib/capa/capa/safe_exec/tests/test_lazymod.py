"""Test lazymod.py"""

import sys
import unittest

from capa.safe_exec.lazymod import LazyModule


class ModuleIsolation(object):
    """
    Manage changes to sys.modules so that we can roll back imported modules.

    Create this object, it will snapshot the currently imported modules. When
    you call `clean_up()`, it will delete any module imported since its creation.
    """
    def __init__(self):
        # Save all the names of all the imported modules.
        self.mods = set(sys.modules)

    def clean_up(self):
        # Get a list of modules that didn't exist when we were created
        new_mods = [m for m in sys.modules if m not in self.mods]
        # and delete them all so another import will run code for real again.
        for m in new_mods:
            del sys.modules[m]


class TestLazyMod(unittest.TestCase):

    def setUp(self):
        super(TestLazyMod, self).setUp()
        # Each test will remove modules that it imported.
        self.addCleanup(ModuleIsolation().clean_up)

    def test_simple(self):
        # Import some stdlib module that has not been imported before.
        self.assertNotIn(
            "colorsys",
            sys.modules,
            "Found colorsys in sys.modules: {!r}".format(sys.modules.get("colorsys")),
        )
        colorsys = LazyModule("colorsys")
        hsv = colorsys.rgb_to_hsv(.3, .4, .2)
        self.assertEqual(hsv[0], 0.25)

    def test_dotted(self):
        # wsgiref is a module with submodules that is not already imported.
        # Any similar module would do. This test demonstrates that the module
        # is not already imported.
        self.assertNotIn(
            "wsgiref.util",
            sys.modules,
            "Found wsgiref.util in sys.modules: {!r}".format(sys.modules.get("wsgiref.util")),
        )
        wsgiref_util = LazyModule("wsgiref.util")
        self.assertEqual(wsgiref_util.guess_scheme({}), "http")
