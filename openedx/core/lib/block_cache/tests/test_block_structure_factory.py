"""
Tests for block_structure_factory.py
"""
# pylint: disable=protected-access
from mock import patch
from unittest import TestCase

from ..block_structure_factory import BlockStructureFactory
from .test_utils import (
    MockCache, MockModulestoreFactory, MockTransformer, ChildrenMapTestMixin
)


class TestBlockStructureFactory(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructureFactory
    """
    def setUp(self):
        super(TestBlockStructureFactory, self).setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.modulestore = MockModulestoreFactory.create(self.children_map)

        self.block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_usage_key=0, modulestore=self.modulestore
        )

        self.transformers = [MockTransformer]
        mock_registry = patch(
            'openedx.core.lib.block_cache.transformer_registry.TransformerRegistry.get_available_plugins'
        )
        mock_registry.return_value = {transformer.name(): transformer for transformer in self.transformers}
        self.addCleanup(mock_registry.stop)
        mock_registry.start()

    def add_transformers(self):
        """
        Add each registered transformer to the block structure.
        Mimic collection by setting test transformer block data.
        """
        for transformer in self.transformers:
            self.block_structure._add_transformer(transformer)
            self.block_structure.set_transformer_block_field(
                usage_key=0, transformer=transformer, key='test', value='{} val'.format(transformer.name())
            )

    def test_create_from_modulestore(self):
        self.assert_block_structure(self.block_structure, self.children_map)

    def test_not_in_cache(self):
        cache = MockCache()

        self.assertIsNone(
            BlockStructureFactory.create_from_cache(
                root_block_usage_key=0,
                cache=cache,
                transformers=self.transformers,
            )
        )

    def test_uncollected_transformers(self):
        cache = MockCache()

        # serialize the structure to cache, but without collecting any transformer data
        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)

        with patch('openedx.core.lib.block_cache.block_structure_factory.logger.info') as mock_logger:
            # cached data does not have collected information for all registered transformers
            self.assertIsNone(
                BlockStructureFactory.create_from_cache(
                    root_block_usage_key=0,
                    cache=cache,
                    transformers=self.transformers,
                )
            )
            self.assertTrue(mock_logger.called)

    def test_cache(self):
        cache = MockCache()

        # collect transformer data
        self.add_transformers()

        # serialize to cache
        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)

        # test re-create from cache
        self.modulestore.get_items_call_count = 0
        from_cache_block_structure = BlockStructureFactory.create_from_cache(
            root_block_usage_key=0,
            cache=cache,
            transformers=self.transformers,
        )
        self.assertIsNotNone(from_cache_block_structure)
        self.assert_block_structure(from_cache_block_structure, self.children_map)
        self.assertEquals(self.modulestore.get_items_call_count, 0)

    def test_remove_from_cache(self):
        cache = MockCache()

        # collect transformer data
        self.add_transformers()

        # serialize to cache
        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)

        # remove from cache
        BlockStructureFactory.remove_from_cache(root_block_usage_key=0, cache=cache)
        self.assertIsNone(
            BlockStructureFactory.create_from_cache(
                root_block_usage_key=0,
                cache=cache,
                transformers=self.transformers
            )
        )
