"""
...
"""

from collections import defaultdict

import django.core.cache
from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore

from .block_cache_data import CourseBlockStructure, CourseBlockData, UserCourseInfo


def _get_cache():
    """
    Returns:
        django.core.cache.BaseCache
    """
    # TODO: For Django 1.7+, use django.core.cache.caches[cache_name].
    return django.core.cache.get_cache('course_blocks_cache')


def create_block_structure(course_key):
    """
    Arguments:
        course_key (CourseKey)

    Returns:
        (CourseBlockStructure, dict[UsageKey: XBlock])
    """

    visited_keys = set()
    xblock_dict = {}
    adj = CourseBlockStructure.AdjacencyInfo(
        defaultdict(set), defaultdict(set)
    )

    def build_block_structure(xblock):
        """
        Helper function to recursively walk course structure and build
        xblock_dict and adj.

        Arguments:
            xblock (XBlock)
        """
        visited_keys.add(xblock.usage_key)
        xblock_dict[xblock.usage_key] = xblock

        for child in xblock.get_children():
            adj[xblock.usage_key].children.add(child.usage_key)
            adj[child.usage_key].parents.add(xblock.usage_key)
            if child.usage_key not in visited_keys:
                build_block_structure(child.usage_key)

    course = modulestore().get_course(course_key, depth=None)  # depth=None => load entire course
    build_block_structure(course)
    block_structure = CourseBlockStructure(course.usage_key, True, adj)
    return block_structure, xblock_dict


def create_block_data_dict(block_structure, xblock_dict, transformations):
    """
    Arguments:
        block_structure (CourseBlockStructure)
        xblock_dict (dict[UsageKey: XBlock])
        transformations (list[Transformation])

    Returns:
        dict[UsageKey: CourseBlockData]
    """
    if not block_structure.root_block_is_course_root:
        raise ValueError("block_structure must be entire course hierarchy.")

    # Define functions for traversing course hierarchy.
    get_children = lambda block: [
        xblock_dict[child_key]
        for child_key in block_structure.get_children(block.usage_key)
    ]
    get_parents = lambda block: [
        xblock_dict[child_key]
        for child_key in block_structure.get_parents(block.usage_key)
    ]

    # For each transformation, extract required fields and collect specially
    # computed data.
    required_fields = set()
    collected_data = {}
    for transformation in transformations:
        required_fields |= transformation.required_fields
        collected_data[transformation.id] = transformation.collect(
            xblock_dict[block_structure.root_block_key],
            get_children,
            get_parents
        )

    # Build a dictionary mapping usage keys to block information.
    return {
        usage_key: CourseBlockData(
            {
                required_field.name: getattr(xblock, required_field.name, None)
                for required_field in required_fields
            },
            {
                transformation_id: transformation_data.get(usage_key, None)
                for transformation_id, transformation_data in collected_data.iteritems()
            }
        )
        for usage_key, xblock in xblock_dict.iteritems()
    }


def cache_block_structure(course_key, block_structure):
    """
    Arguments:
        block_structure (CourseBlockStructure)
    """
    if not block_structure.root_block_is_course_root:
        raise ValueError("block_structure must be entire course hierarchy.")
    child_map = {
        usage_key: block_structure.get_children(usage_key)
        for usage_key in block_structure.get_block_keys()
    }
    _get_cache().set(
        str(course_key),
        (block_structure.root_block_key, child_map)
    )


def cache_block_data_dict(block_data_dict):
    """
    Arguments:
        block_data_dict (dict[UsageKey: CourseBlockData])
    """
    _get_cache().set_many({
        str(usage_key): block_data
        for usage_key, block_data
        in block_data_dict.iteritems()
    })


def get_cached_block_structure(course_key):
    """
    Arguments:
        course_key (CourseKey)
        root_block_key (UsageKey or NoneType)

    Returns:
        CourseBlockStructure, if the block structure is in the cache, and
        NoneType otherwise.
    """
    cached = _get_cache().get(str(course_key), None)
    if not cached:
        return None
    course_root_block_key, child_map = cached

    # We have a singly-linked DAG (child_map).
    # We want to create a doubly-linked DAG.
    # To do so, we must populate a parent map.

    # For each block...
    parent_map = defaultdict(set)
    for usage_key, children in child_map.iteritems():
        # For each child of the block...
        for child in children:
            # Add the block to the child's set of parents.
            parent_map[child].add(usage_key)

    # Zip parent_map and child_map together to construct an adjacency list.
    adj = {
        usage_key: CourseBlockStructure.AdjacencyInfo(parent_map[usage_key], children)
        for usage_key, children in child_map.iteritems()
    }
    return CourseBlockStructure(course_root_block_key, True, adj)


def get_cached_block_data_dict(usage_keys):
    """
    Arguments:
        usage_keys (list[UsageKey])

    Returns:
        dict[UsageKey: CourseBlockData]
    """
    usage_key_strings = (str(usage_key) for usage_key in usage_keys)
    return {
        UsageKey.from_string(usage_key_string)
        for usage_key_string, block_data
        in _get_cache().get_many(usage_key_strings).iteritems()
    }


def clear_course_from_block_cache(course_key):
    """
    Arguments:
        course_key (CourseKey)

    It is safe to call this with a course_key that isn't in the cache.
    """
    _get_cache().delete(str(course_key))


def filter_block_data_dict(block_data_dict, block_structure):
    """
    Arguments:
        block_data_dict (dict[UsageKey: CourseBlockData])
        block_structure: CourseBlockStructure

    Returns:
        CourseBlockStructure
    """
    return (
        block_structure,
        {
            usage_key: block_data
            for usage_key, block_data in block_data_dict
            if usage_key in block_structure.get_block_keys()
        }
    )


def get_user_course_info(user, course_key):
    """
    Arguments:
        user (User)
        course_key (CourseKey)

    Returns:
        UserCourseInfo
    """
    # TODO me: Write this method.
    return UserCourseInfo(None)
