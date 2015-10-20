"""
TODO
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer
from course_api.blocks.transformers.block_counts import BlockCountsTransformer
from course_api.blocks.transformers.student_view import StudentViewTransformer
from course_api.blocks.transformers.block_depth import BlockDepthTransformer
from course_api.blocks.transformers.navigation import BlockNavigationTransformer


class BlocksAPITransformer(BlockStructureTransformer):
    """
    ...
    """
    VERSION = 1
    STUDENT_VIEW_DATA = 'student_view_data'
    STUDENT_VIEW_MULTI_DEVICE = 'student_view_multi_device'

    def __init__(self, block_types_to_count, requested_student_view_data, depth=None, nav_depth=None):
        self.block_types_to_count = block_types_to_count
        self.requested_student_view_data = requested_student_view_data
        self.depth = depth
        self.nav_depth = nav_depth

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields('graded', 'format', 'display_name', 'category')

        # collect data from containing transformers
        StudentViewTransformer.collect(block_structure)
        BlockCountsTransformer.collect(block_structure)
        BlockDepthTransformer.collect(block_structure)
        BlockNavigationTransformer.collect(block_structure)

        # TODO support olx_data by calling export_to_xml(?)

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        StudentViewTransformer(self.requested_student_view_data).transform(user_info, block_structure)
        BlockCountsTransformer(self.block_types_to_count).transform(user_info, block_structure)
        BlockDepthTransformer(self.depth).transform(user_info, block_structure)
        BlockNavigationTransformer(self.nav_depth).transform(user_info, block_structure)
