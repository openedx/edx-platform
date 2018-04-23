"""
Simple test to ensure that modulestore base classes remain abstract
"""
from unittest import TestCase
from nose.plugins.attrib import attr

from xmodule.modulestore import ModuleStoreRead, ModuleStoreWrite


@attr(shard=1)
class AbstractionTest(TestCase):
    """
    Tests that the ModuleStore objects are properly abstracted
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, ModuleStoreRead)  # Cannot be instantiated due to explicit abstraction
        self.assertRaises(TypeError, ModuleStoreWrite)
