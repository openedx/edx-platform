"""
Tests for block_structure_factory.py
"""

import pytest
from django.test import TestCase

from xmodule.modulestore.exceptions import ItemNotFoundError

from ..factory import BlockStructureFactory
from .helpers import ChildrenMapTestMixin, MockModulestoreFactory


class TestBlockStructureFactory(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructureFactory
    """

    def setUp(self):
        super().setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.modulestore = MockModulestoreFactory.create(self.children_map, self.block_key_factory)

    def test_from_modulestore(self):
        block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_usage_key=0, modulestore=self.modulestore
        )
        self.assert_block_structure(block_structure, self.children_map)

    def test_from_modulestore_fail(self):
        with pytest.raises(ItemNotFoundError):
            BlockStructureFactory.create_from_modulestore(
                root_block_usage_key=len(self.children_map) + 1,
                modulestore=self.modulestore,
            )
        
    def test_from_cache(self):
        block_structure = self.create_block_structure(self.children_map)
        from_cache_block_structure = BlockStructureFactory.create_from_modulestore(
            block_structure.root_block_usage_key,
            self.modulestore,
        )
        self.assert_block_structure(from_cache_block_structure, self.children_map)

    def test_new(self):
        block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_usage_key=0, modulestore=self.modulestore
        )
        new_structure = BlockStructureFactory.create_new(
            block_structure.root_block_usage_key,
            block_structure._block_relations,  # pylint: disable=protected-access
            block_structure.transformer_data,
            block_structure._block_data_map,  # pylint: disable=protected-access
        )
        self.assert_block_structure(new_structure, self.children_map)
