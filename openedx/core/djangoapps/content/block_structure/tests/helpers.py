"""
Helpers for Course Blocks tests.
"""

from openedx.core.lib.block_structure.cache import BlockStructureCache
from ..api import get_cache


def is_course_in_block_structure_cache(course_key, store):
    """
    Returns whether the given course is in the Block Structure cache.
    """
    course_usage_key = store.make_course_usage_key(course_key)
    return BlockStructureCache(get_cache()).get(course_usage_key) is not None
