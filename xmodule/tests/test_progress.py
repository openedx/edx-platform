"""Module progress tests"""


import unittest

from xmodule.progress import Progress


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
        prg1 = Progress(0, 2)  # pylint: disable=unused-variable
        prg2 = Progress(1, 2)  # pylint: disable=unused-variable
        prg3 = Progress(2, 2)  # pylint: disable=unused-variable

        prg4 = Progress(2.5, 5.0)  # pylint: disable=unused-variable
        prg5 = Progress(3.7, 12.3333)  # pylint: disable=unused-variable

        # These shouldn't
        self.assertRaises(ValueError, Progress, 0, 0)
        self.assertRaises(ValueError, Progress, 2, 0)
        self.assertRaises(ValueError, Progress, 1, -2)

        self.assertRaises(TypeError, Progress, 0, "all")
        # check complex numbers just for the heck of it :)
        self.assertRaises(TypeError, Progress, 2j, 3)

    def test_clamp(self):
        assert (2, 2) == Progress(3, 2).frac()
        assert (0, 2) == Progress((- 2), 2).frac()

    def test_frac(self):
        prg = Progress(1, 2)
        (a_mem, b_mem) = prg.frac()
        assert a_mem == 1
        assert b_mem == 2

    def test_percent(self):
        assert self.not_started.percent() == 0
        assert round(self.part_done.percent() - 33.33333333333333, 7) >= 0
        assert self.half_done.percent() == 50
        assert self.done.percent() == 100

        assert self.half_done.percent() == self.also_half_done.percent()

    def test_started(self):
        assert not self.not_started.started()

        assert self.part_done.started()
        assert self.half_done.started()
        assert self.done.started()

    def test_inprogress(self):
        # only true if working on it
        assert not self.done.inprogress()
        assert not self.not_started.inprogress()

        assert self.part_done.inprogress()
        assert self.half_done.inprogress()

    def test_done(self):
        assert self.done.done()
        assert not self.half_done.done()
        assert not self.not_started.done()

    def test_str(self):
        assert str(self.not_started) == '0/17'
        assert str(self.part_done) == '2/6'
        assert str(self.done) == '7/7'
        assert str(Progress(2.1234, 7)) == '2.12/7'
        assert str(Progress(2.0034, 7)) == '2/7'
        assert str(Progress(0.999, 7)) == '1/7'

    def test_add(self):
        '''Test the Progress.add_counts() method'''
        prg1 = Progress(0, 2)
        prg2 = Progress(1, 3)
        prg3 = Progress(2, 5)
        prg_none = None
        add = lambda a, b: Progress.add_counts(a, b).frac()

        assert add(prg1, prg1) == (0, 4)
        assert add(prg1, prg2) == (1, 5)
        assert add(prg2, prg3) == (3, 8)

        assert add(prg2, prg_none) == prg2.frac()
        assert add(prg_none, prg2) == prg2.frac()

    def test_equality(self):
        '''Test that comparing Progress objects for equality
        works correctly.'''
        prg1 = Progress(1, 2)
        prg2 = Progress(2, 4)
        prg3 = Progress(1, 2)
        assert prg1 == prg3
        assert prg1 != prg2

        # Check != while we're at it
        assert prg1 != prg2
        assert prg1 == prg3
