"""
A barebones copy of lms/djangoapps/course_blocks/api.py, used by lms workers with input from cms
processes.
"""
from django.core.cache import cache
from openedx.core.lib.block_structure.manager import BlockStructureManager
from xmodule.modulestore.django import modulestore


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
