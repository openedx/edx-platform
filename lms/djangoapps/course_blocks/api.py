"""
API entry point to the course_blocks app with top-level
get_course_blocks function.
"""
from openedx.core.djangoapps.content.block_structure.api import get_block_structure_manager
from openedx.core.lib.block_structure.transformers import BlockStructureTransformers

from lms.djangoapps.grades.transformer import GradesTransformer
from .transformers import (
    library_content,
    start_date,
    user_partitions,
    visibility,
)
from .usage_info import CourseUsageInfo


# Default list of transformers for manipulating course block structures
# based on the user's access to the course blocks.
COURSE_BLOCK_ACCESS_TRANSFORMERS = [
    library_content.ContentLibraryTransformer(),
    start_date.StartDateTransformer(),
    user_partitions.UserPartitionTransformer(),
    visibility.VisibilityTransformer(),
]


def get_course_blocks(
        user,
        starting_block_usage_key,
        transformers=None,
        collected_block_structure=None,
):
    """
    A higher order function implemented on top of the
    block_structure.get_blocks function returning a transformed block
    structure for the given user starting at starting_block_usage_key.

    Arguments:
        user (django.contrib.auth.models.User) - User object for
            which the block structure is to be transformed.

        starting_block_usage_key (UsageKey) - Specifies the starting block
            of the block structure that is to be transformed.

        transformers (BlockStructureTransformers) - A collection of
            transformers whose transform methods are to be called.
            If None, COURSE_BLOCK_ACCESS_TRANSFORMERS is used.

        collected_block_structure (BlockStructureBlockData) - A
            block structure retrieved from a prior call to
            BlockStructureManager.get_collected.  Can be optionally
            provided if already available, for optimization.

    Returns:
        BlockStructureBlockData - A transformed block structure,
            starting at starting_block_usage_key, that has undergone the
            transform methods for the given user and the course
            associated with the block structure.  If using the default
            transformers, the transformed block structure will be
            exactly equivalent to the blocks that the given user has
            access.
    """
    if not transformers:
        transformers = BlockStructureTransformers(COURSE_BLOCK_ACCESS_TRANSFORMERS)
    transformers.usage_info = CourseUsageInfo(starting_block_usage_key.course_key, user)

    return get_block_structure_manager(starting_block_usage_key.course_key).get_transformed(
        transformers,
        starting_block_usage_key,
        collected_block_structure,
    )
