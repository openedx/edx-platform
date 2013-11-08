"""Module progress tests"""

import unittest
from mock import Mock

from xblock.field_data import DictFieldData

from xmodule.progress import Progress
from xmodule import x_module

from . import get_test_system


class ProgressTest(unittest.TestCase):
    ''' Test that basic Progress objects work.  A Progress represents a
    fraction between 0 and 1.
    '''
    not_started = Progress(0, 17)
    part_done = Progress(2, 6)
    half_done = Progress(3, 6)
    also_half_done = Progress(1, 2)
    done = Progress(7, 7)

    def test_create_object(self):
        # These should work:
        p = Progress(0, 2)
        p = Progress(1, 2)
        p = Progress(2, 2)

        p = Progress(2.5, 5.0)
        p = Progress(3.7, 12.3333)

        # These shouldn't
        self.assertRaises(ValueError, Progress, 0, 0)
        self.assertRaises(ValueError, Progress, 2, 0)
        self.assertRaises(ValueError, Progress, 1, -2)

        self.assertRaises(TypeError, Progress, 0, "all")
        # check complex numbers just for the heck of it :)
        self.assertRaises(TypeError, Progress, 2j, 3)

    def test_clamp(self):
        self.assertEqual((2, 2), Progress(3, 2).frac())
        self.assertEqual((0, 2), Progress(-2, 2).frac())

    def test_frac(self):
        p = Progress(1, 2)
        (a, b) = p.frac()
        self.assertEqual(a, 1)
        self.assertEqual(b, 2)

    def test_percent(self):
        self.assertEqual(self.not_started.percent(), 0)
        self.assertAlmostEqual(self.part_done.percent(), 33.33333333333333)
        self.assertEqual(self.half_done.percent(), 50)
        self.assertEqual(self.done.percent(), 100)

        self.assertEqual(self.half_done.percent(), self.also_half_done.percent())

    def test_started(self):
        self.assertFalse(self.not_started.started())

        self.assertTrue(self.part_done.started())
        self.assertTrue(self.half_done.started())
        self.assertTrue(self.done.started())

    def test_inprogress(self):
        # only true if working on it
        self.assertFalse(self.done.inprogress())
        self.assertFalse(self.not_started.inprogress())

        self.assertTrue(self.part_done.inprogress())
        self.assertTrue(self.half_done.inprogress())

    def test_done(self):
        self.assertTrue(self.done.done())
        self.assertFalse(self.half_done.done())
        self.assertFalse(self.not_started.done())

    def test_str(self):
        self.assertEqual(str(self.not_started), "0/17")
        self.assertEqual(str(self.part_done), "2/6")
        self.assertEqual(str(self.done), "7/7")

    def test_ternary_str(self):
        self.assertEqual(self.not_started.ternary_str(), "none")
        self.assertEqual(self.half_done.ternary_str(), "in_progress")
        self.assertEqual(self.done.ternary_str(), "done")

    def test_to_js_status(self):
        '''Test the Progress.to_js_status_str() method'''

        self.assertEqual(Progress.to_js_status_str(self.not_started), "none")
        self.assertEqual(Progress.to_js_status_str(self.half_done), "in_progress")
        self.assertEqual(Progress.to_js_status_str(self.done), "done")
        self.assertEqual(Progress.to_js_status_str(None), "0")

    def test_to_js_detail_str(self):
        '''Test the Progress.to_js_detail_str() method'''
        f = Progress.to_js_detail_str
        for p in (self.not_started, self.half_done, self.done):
            self.assertEqual(f(p), str(p))
        # But None should be encoded as 0
        self.assertEqual(f(None), "0")

    def test_add(self):
        '''Test the Progress.add_counts() method'''
        p = Progress(0, 2)
        p2 = Progress(1, 3)
        p3 = Progress(2, 5)
        pNone = None
        add = lambda a, b: Progress.add_counts(a, b).frac()

        self.assertEqual(add(p, p), (0, 4))
        self.assertEqual(add(p, p2), (1, 5))
        self.assertEqual(add(p2, p3), (3, 8))

        self.assertEqual(add(p2, pNone), p2.frac())
        self.assertEqual(add(pNone, p2), p2.frac())

    def test_equality(self):
        '''Test that comparing Progress objects for equality
        works correctly.'''
        p = Progress(1, 2)
        p2 = Progress(2, 4)
        p3 = Progress(1, 2)
        self.assertTrue(p == p3)
        self.assertFalse(p == p2)

        # Check != while we're at it
        self.assertTrue(p != p2)
        self.assertFalse(p != p3)


class ModuleProgressTest(unittest.TestCase):
    ''' Test that get_progress() does the right thing for the different modules
    '''
    def test_xmodule_default(self):
        '''Make sure default get_progress exists, returns None'''
        xm = x_module.XModule(Mock(), get_test_system(), DictFieldData({'location': 'a://b/c/d/e'}), Mock())
        p = xm.get_progress()
        self.assertEqual(p, None)
