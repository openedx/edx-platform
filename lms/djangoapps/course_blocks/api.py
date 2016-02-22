"""
API entry point to the course_blocks app with top-level
get_course_blocks and clear_course_from_cache functions.
"""
from django.core.cache import cache
from openedx.core.lib.block_structure.manager import BlockStructureManager
from openedx.core.lib.block_structure.transformers import BlockStructureTransformers
from xmodule.modulestore.django import modulestore

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

    return _get_block_structure_manager(starting_block_usage_key.course_key).get_transformed(
        transformers,
        starting_block_usage_key,
    )


def get_course_in_cache(course_key):
    """
    A higher order function implemented on top of the
    block_structure.get_collected function that returns the block
    structure in the cache for the given course_key.

    Returns:
        BlockStructureBlockData - The collected block structure,
            starting at root_block_usage_key.
    """
    return _get_block_structure_manager(course_key).get_collected()


def update_course_in_cache(course_key):
    """
    A higher order function implemented on top of the
    block_structure.updated_collected function that updates the block
    structure in the cache for the given course_key.
    """
    return _get_block_structure_manager(course_key).update_collected()


def clear_course_from_cache(course_key):
    """
    A higher order function implemented on top of the
    block_structure.clear_block_cache function that clears the block
    structure from the cache for the given course_key.

    Note: See Note in get_course_blocks. Even after MA-1604 is
    implemented, this implementation should still be valid since the
    entire block structure of the course is cached, even though
    arbitrary access to an intermediate block will be supported.
    """
    _get_block_structure_manager(course_key).clear()


def _get_block_structure_manager(course_key):
    """
    Returns the manager for managing Block Structures for the given course.
    """
    store = modulestore()
    course_usage_key = store.make_course_usage_key(course_key)
    return BlockStructureManager(course_usage_key, store, _get_cache())


def _get_cache():
    """
    Returns the storage for caching Block Structures.
    """
    return cache
