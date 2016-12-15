"""
Tests for block_structure/cache.py
"""
from unittest import TestCase

from ..cache import BlockStructureCache
from .helpers import ChildrenMapTestMixin, MockCache, MockTransformer


class TestBlockStructureCache(ChildrenMapTestMixin, TestCase):
    """
    Tests for BlockStructureFactory
    """
    def setUp(self):
        super(TestBlockStructureCache, self).setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.block_structure = self.create_block_structure(self.children_map)
        self.cache = BlockStructureCache(MockCache())

    def add_transformers(self):
        """
        Add each registered transformer to the block structure.
        Mimic collection by setting test transformer block data.
        """
        for transformer in [MockTransformer]:
            self.block_structure._add_transformer(transformer)  # pylint: disable=protected-access
            self.block_structure.set_transformer_block_field(
                usage_key=0, transformer=transformer, key='test', value='{} val'.format(transformer.name())
            )

    def test_add(self):
        self.add_transformers()
        self.cache.add(self.block_structure)
        cached_value = self.cache.get(self.block_structure.root_block_usage_key)
        self.assertIsNotNone(cached_value)
        self.assert_block_structure(cached_value, self.children_map)

    def test_get_none(self):
        self.assertIsNone(
            self.cache.get(self.block_structure.root_block_usage_key)
        )

    def test_delete(self):
        self.add_transformers()
        self.cache.add(self.block_structure)
        self.cache.delete(self.block_structure.root_block_usage_key)
        self.assertIsNone(
            self.cache.get(self.block_structure.root_block_usage_key)
        )
