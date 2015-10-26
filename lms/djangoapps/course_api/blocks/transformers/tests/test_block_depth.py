"""
Tests for BlockDepthTransformer.
"""
import ddt
from unittest import TestCase

from course_api.blocks.transformers.block_depth import BlockDepthTransformer
from openedx.core.lib.block_cache.tests.test_utils import ChildrenMapTestMixin
from openedx.core.lib.block_cache.block_structure import BlockStructureXBlockData


@ddt.ddt
class BlockDepthTransformerTestCase(TestCase, ChildrenMapTestMixin):
    """
    ...
    """
    @ddt.data(
        (0, [], [], []),
        (0, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, [[], [], [], [], []], [1, 2, 3, 4]),
        (1, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, [[1, 2], [], [], [], []], [3, 4]),
        (2, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, []),
        (3, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, []),
        (None, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, ChildrenMapTestMixin.SIMPLE_CHILDREN_MAP, []),

        (0, ChildrenMapTestMixin.DAG_CHILDREN_MAP, [[], [], [], [], [], [], []], [1, 2, 3, 4, 5, 6]),
        (1, ChildrenMapTestMixin.DAG_CHILDREN_MAP, [[1, 2], [], [], [], [], [], []], [3, 4, 5, 6]),
        (2, ChildrenMapTestMixin.DAG_CHILDREN_MAP, [[1, 2], [3], [3, 4], [], [], [], []], [5, 6]),
        (3, ChildrenMapTestMixin.DAG_CHILDREN_MAP, ChildrenMapTestMixin.DAG_CHILDREN_MAP, []),
        (4, ChildrenMapTestMixin.DAG_CHILDREN_MAP, ChildrenMapTestMixin.DAG_CHILDREN_MAP, []),
        (None, ChildrenMapTestMixin.DAG_CHILDREN_MAP, ChildrenMapTestMixin.DAG_CHILDREN_MAP, []),
    )
    @ddt.unpack
    def test_block_depth(self, block_depth, children_map, transformed_children_map, missing_blocks):
        block_structure = self.create_block_structure(BlockStructureXBlockData, children_map)
        BlockDepthTransformer(block_depth).transform(user_info=None, block_structure=block_structure)
        block_structure._prune()
        self.assert_block_structure(block_structure, transformed_children_map, missing_blocks)
