"""
This is the start of a test for grades.
It is very incomplete - we're only testing one function
right now.
"""

from courseware.model_data import LmsKeyValueStore
from courseware.grades import yield_dynamic_descriptor_descendents
from courseware import grades
from mock import MagicMock

import unittest


class FakeChildFactory(object):
    """
    Makes fake child descriptors.
    """
    @classmethod
    def create(cls, name):
        """
        Creates a new fake child with the given name.
        """
        out = MagicMock()
        out.has_dynamic_children = lambda: False
        out.get_children = lambda: []
        out.name = name
        return out


class TestGrades(unittest.TestCase):
    """
    Test the grader.
    """

    def test_yield_dynamic_descriptor_descendents(self):
        """
        Make sure that yield_dynamic_descriptor_descendents instantiates
        modules to get children.
        """
        child_a = FakeChildFactory.create('a')
        child_b = FakeChildFactory.create('b')
        child_c = FakeChildFactory.create('c')

        fake_parent = MagicMock()
        fake_parent.has_dynamic_children = lambda: True
        # These are the wrong children.
        fake_parent.get_children = lambda: [child_a, child_b, child_c]

        def fake_module_creator(descriptor):
            """
            A mock of the module creator.  Returns a set of children only
            if called with our fake_parent.
            """
            if descriptor == fake_parent:
                fake_module = MagicMock()
                fake_module.get_child_descriptors = lambda: [child_a, child_b]
                return fake_module
            else:
                return None

        # Test with dynamic children
        dynamic_children = list(yield_dynamic_descriptor_descendents(fake_parent, fake_module_creator))
        self.assertTrue(child_a in dynamic_children)
        self.assertTrue(child_b in dynamic_children)
        self.assertTrue(child_c not in dynamic_children)

        # Test without dynamic children
        fake_parent.has_dynamic_children = lambda: False
        regular_children = list(yield_dynamic_descriptor_descendents(fake_parent, fake_module_creator))
        self.assertTrue(child_a in regular_children)
        self.assertTrue(child_b in regular_children)
        self.assertTrue(child_c in regular_children)


class TestFindShouldGradeSection(unittest.TestCase):
    """
    Test find_should_grade_section.

    find_should_grade_section should:
        return True when at least one problem in the section has been seen in cache
        return True when a module's grades should always be recalculated
        otherwise return False when no problem has been seen in cache
    """

    def setUp(self):

        def fake_find_key(fake_key):
            self.assertIsInstance(fake_key, LmsKeyValueStore.Key)
            print fake_key
            if fake_key.block_scope_id:
                fake_found = MagicMock()
                fake_found.grade = fake_key.student_id
                return fake_found
            else:
                return None

        self.fake_model_data_cache = MagicMock()
        self.fake_model_data_cache.find = fake_find_key

    def fake_module(self, is_in_cache, recalculate):
        output = MagicMock()
        output.location = is_in_cache
        output.always_recalculate_grades = recalculate
        return output

    def test_not_in_cache(self):
        #Test returning false when not always-recalculating-grades and when no problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(False, False) for i in range(5)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertFalse(result)

    def test_first_in_cache(self):
        #Test returning true when the first problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False)] + [self.fake_module(False, False) for i in range(7)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_last_in_cache(self):
        #Test returning true when the last problem has been seen in cache
        fake_xmoduledescriptors = [self.fake_module(False, False) for i in range(3)] + [self.fake_module(True, False)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_all_in_cache(self):
        #Test returning true when all problems have been seen in cache
        fake_xmoduledescriptors = [self.fake_module(True, False) for i in range(9)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_always_recalculate(self):
        #Test returning true when a module's grades should always be recalculated, even if False otherwise
        fake_xmoduledescriptors = [self.fake_module(False, True) for i in range(2)]
        result = grades.find_should_grade_section(fake_xmoduledescriptors, self.fake_model_data_cache, 42)
        self.assertTrue(result)

    def test_empty_list(self):
        #Test returning false when the list of xmodule descriptors is empty
        result = grades.find_should_grade_section([], self.fake_model_data_cache, 42)
        self.assertFalse(result)


class TestFindAttempted(unittest.TestCase):

    def setUp(self):

        def fake_find_key(fake_key):
            self.assertIsInstance(fake_key, LmsKeyValueStore.Key)
            print fake_key
            if fake_key.block_scope_id:
                fake_found = MagicMock()
                fake_found.grade = fake_key.student_id
                return fake_found
            else:
                return None

        self.fake_model_data_cache = MagicMock()
        self.fake_model_data_cache.find = fake_find_key

    def fake_module(self, is_in_cache):
        output = MagicMock()
        output.location = is_in_cache
        return output

    def test_not_attempted(self):
        #Test returning false when student has not attempted problem
        fake_module = self.fake_module(False)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, None)
        self.assertFalse(result)

    def test_no_grade(self):
        #Test returning false when student has attempted problem, but grade is None
        fake_module = self.fake_module(True)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, None)
        self.assertFalse(result)

    def test_has_grade(self):
        #Test returning true when student has attempted problem and has a grade
        fake_module = self.fake_module(True)
        result = grades.find_attempted(fake_module, self.fake_model_data_cache, 3.0)
        self.assertTrue(result)
