"""
...
"""
from django.conf import settings
from django.core.cache import get_cache

from openedx.core.lib.block_cache.block_cache import get_blocks, clear_block_cache
from xmodule.modulestore.django import modulestore

from lms.djangoapps.course_blocks.transformers import start_date, user_partitions, visibility, split_test, library_content, randomize
from lms.djangoapps.course_blocks.user_info import CourseUserInfo


LMS_COURSE_TRANSFORMERS = {
    visibility.VisibilityTransformer(),
    start_date.StartDateTransformer(),
    user_partitions.UserPartitionTransformer(),
    split_test.SplitTestTransformer(),
    library_content.ContentLibraryTransformer(),
}

_cache = None


def _get_cache():
    global _cache
    if not _cache:
        _cache = get_cache('lms.course_blocks')
    return _cache


def get_course_blocks(
        user,
        course_key,
        root_usage_key,
        transformers=LMS_COURSE_TRANSFORMERS,
):
    if transformers is None:
        transformers = settings.LMS_COURSE_TRANSFORMERS

    return get_blocks(
        _get_cache(), modulestore(), CourseUserInfo(course_key, user), root_usage_key, transformers,
    )


def clear_course_from_cache(course_key):
    # TODO move this to mixed.py so it can be store specific
    # This will NOT work for old Mongo, which uses run as the block_id
    course_usage_key = course_key.make_usage_key('course', 'course')
    return clear_block_cache(_get_cache(), course_usage_key)
