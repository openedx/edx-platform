"""
...
"""
from django.core.cache import get_cache

from openedx.core.lib.block_cache.block_cache import get_blocks, clear_block_cache
from xmodule.modulestore.django import modulestore

from .transformers import (
    start_date,
    user_partitions,
    visibility,
    library_content,
)
from .user_info import CourseUserInfo


LMS_COURSE_TRANSFORMERS = [
    visibility.VisibilityTransformer(),
    start_date.StartDateTransformer(),
    user_partitions.UserPartitionTransformer(),
    library_content.ContentLibraryTransformer(),
]


_COURSE_BLOCKS_CACHE = None


def _get_cache():
    global _COURSE_BLOCKS_CACHE
    if not _COURSE_BLOCKS_CACHE:
        _COURSE_BLOCKS_CACHE = get_cache('lms.course_blocks')
    return _COURSE_BLOCKS_CACHE


def get_course_blocks(
    user,
    root_usage_key=None,
    course_key=None,
    transformers=None,
):
    store = modulestore()

    if transformers is None:
        transformers = LMS_COURSE_TRANSFORMERS

    if root_usage_key is None:
        root_usage_key = store.make_course_usage_key(course_key)

    return get_blocks(
        _get_cache(), store, CourseUserInfo(root_usage_key.course_key, user), root_usage_key, transformers,
    )


def clear_course_from_cache(course_key):
    course_usage_key = modulestore().make_course_usage_key(course_key)
    return clear_block_cache(_get_cache(), course_usage_key)
