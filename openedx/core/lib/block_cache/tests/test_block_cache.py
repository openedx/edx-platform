"""
Tests for block_cache.py
"""

from django.core.cache import get_cache
from mock import patch
from unittest import TestCase

from ..block_cache import get_blocks
from ..exceptions import TransformerException
from .test_utils import (
    MockModulestoreFactory, MockCache, MockTransformer, ChildrenMapTestMixin
)


@patch('openedx.core.lib.block_cache.transformer_registry.TransformerRegistry.get_available_plugins')
class TestBlockCache(TestCase, ChildrenMapTestMixin):
    """
    Test class for block cache functionality.
    """

    class TestTransformer1(MockTransformer):
        """
        Test Transformer class.
        """
        @classmethod
        def block_key(cls):
            """
            Returns the dictionary key for transformer block data.
            """
            return 't1.key1'

        @classmethod
        def block_val(cls, block_key):
            """
            Returns the dictionary value for transformer block data for
            the block identified by the given block key.
            """
            return 't1.val1.' + unicode(block_key)

        @classmethod
        def collect(cls, block_structure):
            """
            Sets transformer block data for each block in the structure
            as it is visited using topological traversal.
            """
            for block_key in block_structure.topological_traversal():
                block_structure.set_transformer_block_field(
                    block_key, cls, cls.block_key(), cls.block_val(block_key)
                )

        def transform(self, usage_info, block_structure):
            """
            Verifies the transformer block data set for each block
            in the structure.
            """
            def assert_collected_value(block_key):
                """
                Verifies the transformer block data for the given
                block equates the value stored in the collect method.
                """
                assert (
                    block_structure.get_transformer_block_field(
                        block_key,
                        self,
                        self.block_key()
                    ) == self.block_val(block_key)
                )

            for block_key in block_structure.topological_traversal():
                assert_collected_value(block_key)

    def setUp(self):
        super(TestBlockCache, self).setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.usage_info = None
        self.mock_cache = MockCache()
        self.modulestore = MockModulestoreFactory.create(self.children_map)
        self.transformers = [self.TestTransformer1()]

    def test_get_blocks(self, mock_available_transforms):
        mock_available_transforms.return_value = {transformer.name(): transformer for transformer in self.transformers}
        block_structure = get_blocks(
            self.mock_cache, self.modulestore, self.usage_info, root_block_usage_key=0, transformers=self.transformers
        )
        self.assert_block_structure(block_structure, self.children_map)

    def test_unregistered_transformers(self, mock_available_transforms):
        mock_available_transforms.return_value = {}
        with self.assertRaisesRegexp(TransformerException, "requested transformers are not registered"):
            get_blocks(
                self.mock_cache,
                self.modulestore,
                self.usage_info,
                root_block_usage_key=0,
                transformers=self.transformers,
            )

    def test_block_caching(self, mock_available_transforms):
        mock_available_transforms.return_value = {transformer.name(): transformer for transformer in self.transformers}

        cache = get_cache('block_cache')

        for iteration in range(2):
            self.modulestore.get_items_call_count = 0
            block_structure = get_blocks(
                cache, self.modulestore, self.usage_info, root_block_usage_key=0, transformers=self.transformers
            )
            self.assert_block_structure(block_structure, self.children_map)
            if iteration == 0:
                self.assertGreater(self.modulestore.get_items_call_count, 0)
            else:
                self.assertEquals(self.modulestore.get_items_call_count, 0)
