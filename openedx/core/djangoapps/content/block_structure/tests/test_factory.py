"""
Tests for block_structure_factory.py
"""

import pytest
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.exceptions import ItemNotFoundError

from ..exceptions import BlockStructureNotFound
from ..factory import BlockStructureFactory
from ..store import BlockStructureStore
from .helpers import ChildrenMapTestMixin, MockCache, MockModulestoreFactory


class TestBlockStructureFactory(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructureFactory
    """

    def block_key_factory(self, block_id):
        """
        Returns a usage_key object for the given block_id.
        This overrides the method in the ChildrenMapTestMixin.
        """
        return CourseKey.from_string("course-v1:org+course+run").make_usage_key("html", str(block_id))

    def setUp(self):
        super().setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.modulestore = MockModulestoreFactory.create(self.children_map, self.block_key_factory)

    def test_from_modulestore(self):
        usage_key = CourseKey.from_string("course-v1:org+course+run").make_usage_key("html", "0")
        block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_usage_key=usage_key, modulestore=self.modulestore
        )
        self.assert_block_structure(block_structure, self.children_map)

    def test_from_modulestore_fail(self):
        with pytest.raises(ItemNotFoundError):
            BlockStructureFactory.create_from_modulestore(
                root_block_usage_key=len(self.children_map) + 1,
                modulestore=self.modulestore,
            )

    def test_from_cache(self):
        store = BlockStructureStore(MockCache())
        block_structure = self.create_block_structure(self.children_map)
        store.add(block_structure)
        from_cache_block_structure = BlockStructureFactory.create_from_store(
            block_structure.root_block_usage_key,
            store,
        )
        self.assert_block_structure(from_cache_block_structure, self.children_map)

    def test_from_cache_none(self):
        store = BlockStructureStore(MockCache())
        # Non-existent usage key
        usage_key = CourseKey.from_string("course-v1:org+course+run").make_usage_key("html", "0")
        with pytest.raises(BlockStructureNotFound):
            BlockStructureFactory.create_from_store(
                root_block_usage_key=usage_key,
                block_structure_store=store,
            )

    def test_new(self):
        usage_key = CourseKey.from_string("course-v1:org+course+run").make_usage_key("html", "0")
        block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_usage_key=usage_key, modulestore=self.modulestore
        )
        new_structure = BlockStructureFactory.create_new(
            block_structure.root_block_usage_key,
            block_structure._block_relations,  # pylint: disable=protected-access
            block_structure.transformer_data,
            block_structure._block_data_map,  # pylint: disable=protected-access
        )
        self.assert_block_structure(new_structure, self.children_map)
