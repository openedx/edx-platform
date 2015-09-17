"""
Tests for block_structure.py
"""
from collections import namedtuple
from copy import deepcopy
import ddt
import itertools
from mock import patch
from unittest import TestCase

from ..block_structure import (
    BlockStructure, BlockStructureCollectedData, BlockStructureBlockData, BlockStructureFactory
)
from ..graph_traversals import traverse_post_order
from ..transformer import BlockStructureTransformer, BlockStructureTransformers
from .test_utils import (
    MockCache, MockXBlock, MockModulestoreFactory, MockTransformer,
    ChildrenMapTestMixin
)


@ddt.ddt
class TestBlockStructure(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructure
    """
    @ddt.data(
        [],
        ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP,
        ChildrenMapTestMixin.LINEAR_CHILDREN_MAP,
        ChildrenMapTestMixin.DAG_CHILDREN_MAP,
    )
    def test_relations(self, children_map):
        block_structure = self.create_block_structure(BlockStructure, children_map)

        # get_children
        for parent, children in enumerate(children_map):
            self.assertSetEqual(set(block_structure.get_children(parent)), set(children))

        # get_parents
        for child, parents in enumerate(self.get_parents_map(children_map)):
            self.assertSetEqual(set(block_structure.get_parents(child)), set(parents))

        # has_block
        for node in range(len(children_map)):
            self.assertTrue(block_structure.has_block(node))
        self.assertFalse(block_structure.has_block(len(children_map) + 1))


@ddt.ddt
class TestBlockStructureData(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructureBlockData and BlockStructureCollectedData
    """
    def test_non_versioned_transformer(self):
        class TestNonVersionedTransformer(BlockStructureTransformer):
            def transform(self, user_info, block_structure):
                pass

        block_structure = BlockStructureCollectedData(root_block_key=0)

        with self.assertRaisesRegexp(Exception, "VERSION attribute is not set"):
            block_structure.add_transformer(TestNonVersionedTransformer())

    def test_transformer_data(self):
        # transformer test cases
        TransformerInfo = namedtuple("TransformerInfo", "transformer structure_wide_data block_specific_data")
        transformers_info = [
            TransformerInfo(
                transformer=MockTransformer(),
                structure_wide_data=[("t1.global1", "t1.g.val1"), ("t1.global2", "t1.g.val2")],
                block_specific_data={
                    "B1": [("t1.key1", "t1.b1.val1"), ("t1.key2", "t1.b1.val2")],
                    "B2": [("t1.key1", "t1.b2.val1"), ("t1.key2", "t1.b2.val2")],
                    "B3": [("t1.key1", True), ("t1.key2", False)],
                    "B4": [("t1.key1", None), ("t1.key2", False)],
                },
            ),
            TransformerInfo(
                transformer=MockTransformer(),
                structure_wide_data=[("t2.global1", "t2.g.val1"), ("t2.global2", "t2.g.val2")],
                block_specific_data={
                    "B1": [("t2.key1", "t2.b1.val1"), ("t2.key2", "t2.b1.val2")],
                    "B2": [("t2.key1", "t2.b2.val1"), ("t2.key2", "t2.b2.val2")],
                },
            ),
        ]

        # create block structure
        block_structure = BlockStructureCollectedData(root_block_key=0)

        # set transformer data
        for t_info in transformers_info:
            block_structure.add_transformer(t_info.transformer)
            for key, val in t_info.structure_wide_data:
                block_structure.set_transformer_data(t_info.transformer, key, val)
            for block, block_data in t_info.block_specific_data.iteritems():
                for key, val in block_data:
                    block_structure.set_transformer_block_data(block, t_info.transformer, key, val)

        # verify transformer data
        for t_info in transformers_info:
            self.assertEquals(
                block_structure.get_transformer_data_version(t_info.transformer),
                MockTransformer.VERSION
            )
            for key, val in t_info.structure_wide_data:
                self.assertEquals(
                    block_structure.get_transformer_data(t_info.transformer, key),
                    val,
                )
            for block, block_data in t_info.block_specific_data.iteritems():
                for key, val in block_data:
                    self.assertEquals(
                        block_structure.get_transformer_block_data(block, t_info.transformer, key),
                        val,
                    )

    def test_xblock_data(self):
        # block test cases
        blocks = [
            MockXBlock("A", {}),
            MockXBlock("B", {"field1": "B.val1"}),
            MockXBlock("C", {"field1": "C.val1", "field2": "C.val2"}),
            MockXBlock("D", {"field1": True, "field2": False}),
            MockXBlock("E", {"field1": None, "field2": False}),
        ]

        # add each block
        block_structure = BlockStructureCollectedData(root_block_key=0)
        for block in blocks:
            block_structure.add_xblock(block)

        # request fields
        fields = ["field1", "field2", "field3"]
        block_structure.request_xblock_fields(*fields)

        # verify fields have not been collected yet
        for block in blocks:
            for field in fields:
                self.assertIsNone(block_structure.get_xblock_field(block.location, field))

        # collect fields
        block_structure.collect_requested_xblock_fields()

        # verify values of collected fields
        for block in blocks:
            for field in fields:
                self.assertEquals(
                    block_structure.get_xblock_field(block.location, field),
                    block.field_map.get(field),
                )

    @ddt.data(
        *itertools.product(
            [True, False],
            range(7),
            [
                # ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP,
                ChildrenMapTestMixin.LINEAR_CHILDREN_MAP,
                # ChildrenMapTestMixin.DAG_CHILDREN_MAP,
            ],
        )
    )
    @ddt.unpack
    def test_remove_block(self, keep_descendants, block_to_remove, children_map):
        ### skip test if invalid
        if (
            (block_to_remove >= len(children_map)) or
            (keep_descendants and block_to_remove == 0)
        ):
            return

        ### create structure
        block_structure = self.create_block_structure(BlockStructureBlockData, children_map)
        parents_map = self.get_parents_map(children_map)

        ### verify blocks pre-exist
        self.assert_block_structure(block_structure, children_map)

        ### remove block
        block_structure.remove_block(block_to_remove, keep_descendants)
        missing_blocks = [block_to_remove]

        ### compute and verify updated children_map
        removed_children_map = deepcopy(children_map)
        removed_children_map[block_to_remove] = []
        [removed_children_map[parent].remove(block_to_remove) for parent in parents_map[block_to_remove]]

        if keep_descendants:
            # update the graph connecting the old parents to the old children
            [
                removed_children_map[parent].append(child)
                for child in children_map[block_to_remove]
                for parent in parents_map[block_to_remove]
            ]

        self.assert_block_structure(block_structure, removed_children_map, missing_blocks)

        ### prune the structure
        block_structure.prune()

        ### compute and verify updated children_map
        pruned_children_map = deepcopy(removed_children_map)

        if not keep_descendants:
            def update_descendant(block):
                """
                add descendant to missing blocks and empty its children
                """
                missing_blocks.append(block)
                pruned_children_map[block] = []

            # update all descendants
            for child in children_map[block_to_remove]:
                list(traverse_post_order(
                    child,
                    get_children=lambda block: pruned_children_map[block],
                    get_result=update_descendant,
                ))
        self.assert_block_structure(block_structure, pruned_children_map, missing_blocks)


class TestBlockStructureFactory(TestCase, ChildrenMapTestMixin):
    """
    Tests for BlockStructureFactory
    """
    def setUp(self):
        super(TestBlockStructureFactory, self).setUp()
        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.modulestore = MockModulestoreFactory.create(self.children_map)

        self.block_structure = BlockStructureFactory.create_from_modulestore(
            root_block_key=0, modulestore=self.modulestore
        )

    def add_transformers(self):
        """
        Add each registered transformer to the block structure.
        """
        for transformer in BlockStructureTransformers.get_registered_transformers():
            self.block_structure.add_transformer(transformer)
            self.block_structure.set_transformer_block_data(
                usage_key=0, transformer=transformer, key='test', value='{} val'.format(transformer.name())
            )

    def test_create_from_modulestore(self):
        self.assert_block_structure(self.block_structure, self.children_map)

    def test_uncollected_transformers(self):
        cache = MockCache()

        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)
        with patch('openedx.core.lib.block_cache.block_structure.logger.info') as mock_logger:
            # cached data does not have collected information for all registered transformers
            self.assertIsNone(BlockStructureFactory.create_from_cache(root_block_key=0, cache=cache))
            self.assertTrue(mock_logger.called)

    def test_not_in_cache(self):
        cache = MockCache()

        self.assertIsNone(BlockStructureFactory.create_from_cache(root_block_key=0, cache=cache))

    def test_cache(self):
        cache = MockCache()
        self.add_transformers()

        # serialize to cache
        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)

        # test re-create from cache
        self.modulestore.get_items_call_count = 0
        from_cache_block_structure = BlockStructureFactory.create_from_cache(root_block_key=0, cache=cache)
        self.assertIsNotNone(from_cache_block_structure)
        self.assert_block_structure(from_cache_block_structure, self.children_map)
        self.assertEquals(self.modulestore.get_items_call_count, 0)

    def test_remove_from_cache(self):
        cache = MockCache()
        self.add_transformers()

        BlockStructureFactory.serialize_to_cache(self.block_structure, cache)
        BlockStructureFactory.remove_from_cache(root_block_key=0, cache=cache)
        self.assertIsNone(BlockStructureFactory.create_from_cache(root_block_key=0, cache=cache))
