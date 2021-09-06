"""
Tests for BlockDepthTransformer.
"""

# pylint: disable=protected-access


from unittest import TestCase

import ddt

from openedx.core.djangoapps.content.block_structure.block_structure import BlockStructureModulestoreData
from openedx.core.djangoapps.content.block_structure.tests.helpers import ChildrenMapTestMixin

from ..block_depth import BlockDepthTransformer


@ddt.ddt
class BlockDepthTransformerTestCase(TestCase, ChildrenMapTestMixin):
    """
    Test behavior of BlockDepthTransformer
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
        block_structure = self.create_block_structure(children_map, BlockStructureModulestoreData)
        BlockDepthTransformer(block_depth).transform(usage_info=None, block_structure=block_structure)
        block_structure._prune_unreachable()
        self.assert_block_structure(block_structure, transformed_children_map, missing_blocks)
