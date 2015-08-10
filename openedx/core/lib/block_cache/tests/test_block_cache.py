"""
Tests for block_cache.py
"""

from mock import patch
from unittest import TestCase
from .test_utils import (
    MockModulestoreFactory, MockCache, MockUserInfo, MockTransformer, SIMPLE_CHILDREN_MAP, BlockStructureTestMixin
)
from ..block_cache import get_blocks

class TestBlockCache(TestCase, BlockStructureTestMixin):

    class TestTransformer1(MockTransformer):
        @classmethod
        def block_key(cls):
            return 't1.key1'

        @classmethod
        def block_val(cls, block_key):
            return 't1.val1.' + unicode(block_key)

        @classmethod
        def collect(self, block_structure):
            list(
                block_structure.topological_traversal(
                    get_result=lambda block_key: block_structure.set_transformer_block_data(
                        block_key, self, self.block_key(), self.block_val(block_key)
            )))

        def transform(self, user_info, block_structure):
            def assert_collected_value(block_key):
                assert (
                    block_structure.get_transformer_block_data(
                        block_key,
                        self,
                        self.block_key()
                    ) == self.block_val(block_key)
                )

            list(
                block_structure.topological_traversal(
                    get_result=lambda block_key: assert_collected_value(block_key)
            ))

    @patch('openedx.core.lib.block_cache.transformer.BlockStructureTransformers.get_available_plugins')
    def test_get_blocks(self, mock_available_transforms):
        children_map = SIMPLE_CHILDREN_MAP
        cache = MockCache()
        user_info = MockUserInfo()
        modulestore = MockModulestoreFactory.create(children_map)
        transformers = [self.TestTransformer1()]

        mock_available_transforms.return_value = {}
        with self.assertRaisesRegexp(Exception, "requested transformers are not registered"):
            get_blocks(cache, modulestore, user_info, root_block_key=0, transformers=transformers)

        mock_available_transforms.return_value = {transformer.name(): transformer for transformer in transformers}
        block_structure = get_blocks(cache, modulestore, user_info, root_block_key=0, transformers=transformers)
        self.verify_block_structure(block_structure, children_map)
