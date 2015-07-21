"""
...
"""
from django.core.cache import get_cache

from openedx.core.lib.course_cache.interface import CourseCacheInterface

from .transformations import LMS_COURSE_TRANSFORMATIONS


_cache_interface = None


def _get_cache_interface():
    """
    Returns:
        django.core.cache.BaseCache
    """
    global _cache_interface
    if not _cache_interface:
        _cache_interface = CourseCacheInterface(
            get_cache('course_blocks_cache'),  # TODO: For Django 1.7+, use django.core.caches[cache_name].
            LMS_COURSE_TRANSFORMATIONS
        )
    return _cache_interface


def get_course_blocks(user, course_key, root_block_key=None, transformations=LMS_COURSE_TRANSFORMATIONS):
    """
    Arguments:
        user (User)
        course_key (CourseKey): Course to which desired blocks belong.
        root_block_key (UsageKey): Usage key for root block in the subtree
            for which block information will be returned. Passing in the usage
            key of a course will return the entire user-specific course
            hierarchy.
        transformations (list[Transformation])

    Returns:
        (CourseBlockStructure, dict[UsageKey: CourseBlockData])
    """
    return _get_cache_interface().get_course_blocks(
        user, course_key, root_block_key, transformations
    )


def clear_course_from_cache(course_key):
    """
    Arguments:
        course_key (CourseKey)
    """
    return _get_cache_interface().clear_course(course_key)
