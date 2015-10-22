"""
...
"""
from django.core.cache import cache

from openedx.core.lib.block_cache.block_cache import get_blocks, clear_block_cache
from xmodule.modulestore.django import modulestore

from .transformers import (
    library_content,
    split_test,
    start_date,
    user_partitions,
    visibility,
)
from .user_info import CourseUserInfo


LMS_COURSE_TRANSFORMERS = [
    library_content.ContentLibraryTransformer(),
    split_test.SplitTestTransformer(),
    start_date.StartDateTransformer(),
    user_partitions.UserPartitionTransformer(),
    visibility.VisibilityTransformer(),
]


def _get_cache():
    """Function exists for mocking/testing, or if we want a custom cache."""
    return cache


def get_course_blocks(
        user,
        root_usage_key=None,
        course_key=None,
        transformers=None
):
    """
    TODO
    """
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
