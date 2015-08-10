"""
Tests for VisibilityTransformer.
"""
import ddt

from course_blocks.transformers.visibility import VisibilityTransformer
from .test_helpers import BlockParentsMapTestCase


@ddt.ddt
class VisibilityTransformerTestCase(BlockParentsMapTestCase):
    """
    ...
    """
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
        self, staff_only_blocks, expected_student_visible_blocks, blocks_with_differing_student_access
    ):
        for i, _ in enumerate(self.parents_map):
            block = self.get_block(i)
            block.visible_to_staff_only = (i in staff_only_blocks)
            self.update_block(block)

        self.check_transformer_results(
            expected_student_visible_blocks, blocks_with_differing_student_access, [VisibilityTransformer()]
        )
