"""
Tests for VisibilityTransformer.
"""
import ddt

from ..visibility import VisibilityTransformer
from .helpers import BlockParentsMapTestCase, update_block


@ddt.ddt
class VisibilityTransformerTestCase(BlockParentsMapTestCase):
    """
    VisibilityTransformer Test
    """
    TRANSFORMER_CLASS_TO_TEST = VisibilityTransformer

    # Following test cases are based on BlockParentsMapTestCase.parents_map
    @ddt.data(
        ({}, {0, 1, 2, 3, 4, 5, 6}, {}),
        ({0}, {}, {1, 2, 3, 4, 5, 6}),
        ({1}, {0, 2, 5, 6}, {3, 4}),
        ({2}, {0, 1, 3, 4, 6}, {5}),
        ({3}, {0, 1, 2, 4, 5, 6}, {}),
        ({4}, {0, 1, 2, 3, 5, 6}, {}),
        ({5}, {0, 1, 2, 3, 4, 6}, {}),
        ({6}, {0, 1, 2, 3, 4, 5}, {}),
        ({1, 2}, {0}, {3, 4, 5, 6}),
        ({2, 4}, {0, 1, 3}, {5, 6}),
        ({1, 2, 3, 4, 5, 6}, {0}, {}),
    )
    @ddt.unpack
    def test_block_visibility(
            self, staff_only_blocks, expected_visible_blocks, blocks_with_differing_access
    ):
        for idx, _ in enumerate(self.parents_map):
            block = self.get_block(idx)
            block.visible_to_staff_only = (idx in staff_only_blocks)
            update_block(block)

        self.assert_transform_results(
            self.student,
            expected_visible_blocks,
            blocks_with_differing_access,
            self.transformers,
        )
