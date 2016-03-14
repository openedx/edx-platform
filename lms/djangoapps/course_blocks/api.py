"""
API entry point to the course_blocks app with top-level
get_course_blocks and clear_course_from_cache functions.
"""
from django.core.cache import cache

from openedx.core.lib.block_cache.block_cache import get_blocks, clear_block_cache
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
        root_block_usage_key,
        transformers=None
):
    """
    A higher order function implemented on top of the
    block_cache.get_blocks function returning a transformed block
    structure for the given user starting at root_block_usage_key.

    Note: The current implementation requires the root_block_usage_key
    to be the root block of its corresponding course. However, this
    is a short-term limitation, which will be addressed in a coming
    ticket (https://openedx.atlassian.net/browse/MA-1604). Once that
    ticket is implemented, callers will be able to get course blocks
    starting at any arbitrary location within a block structure.

    Arguments:
        user (django.contrib.auth.models.User) - User object for
            which the block structure is to be transformed.

        root_block_usage_key (UsageKey) - The usage_key for the root
            of the block structure that is being accessed.

        transformers ([BlockStructureTransformer]) - The list of
            transformers whose transform methods are to be called.
            If None, COURSE_BLOCK_ACCESS_TRANSFORMERS is used.

    Returns:
        BlockStructureBlockData - A transformed block structure,
            starting at root_block_usage_key, that has undergone the
            transform methods for the given user and the course
            associated with the block structure.  If using the default
            transformers, the transformed block structure will be
            exactly equivalent to the blocks that the given user has
            access.
    """
    store = modulestore()
    if root_block_usage_key != store.make_course_usage_key(root_block_usage_key.course_key):
        # Enforce this check for now until MA-1604 is implemented.
        # Otherwise, callers will get incorrect block data after a
        # new version of the course is published, since
        # clear_course_from_cache only clears the cached block
        # structures starting at the root block of the course.
        raise NotImplementedError

    return get_blocks(
        cache,
        store,
        CourseUsageInfo(root_block_usage_key.course_key, user),
        root_block_usage_key,
        COURSE_BLOCK_ACCESS_TRANSFORMERS if transformers is None else transformers,
    )


def clear_course_from_cache(course_key):
    """
    A higher order function implemented on top of the
    block_cache.clear_block_cache function that clears the block
    structure from the cache for the block structure starting at the
    root block of the course for the given course_key.

    Note: See Note in get_course_blocks. Even after MA-1604 is
    implemented, this implementation should still be valid since the
    entire block structure of the course is cached, even though
    arbitrary access to an intermediate block will be supported.
    """
    course_usage_key = modulestore().make_course_usage_key(course_key)
    return clear_block_cache(cache, course_usage_key)
