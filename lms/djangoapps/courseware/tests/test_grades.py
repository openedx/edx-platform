"""
This is the start of a test for grades.
It is very incomplete - we're only testing one function
right now.
"""
from courseware.grades import yield_dynamic_descriptor_descendents
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
