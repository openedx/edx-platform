"""
general helper functions for xblocks
"""

from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from xblock.core import XBlock
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content_tagging.api import get_object_tag_counts


def usage_key_with_run(usage_key_string: str) -> UsageKey:
    """
    Converts usage_key_string to a UsageKey, adding a course run if necessary
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    return usage_key


def get_definition_from_usage_key(usage_key: UsageKey) -> str:
    """
    Extracts the block_type and the block_id from `usage_key`
    """
    return f"{usage_key.block_type}@{usage_key.block_id}"


def get_usage_key_from_definition(definition_key: str, course_key: CourseKey) -> UsageKey:
    """
    Build an usage key using a definition key and a course
    """
    parts = definition_key.split('@')
    block_type = parts[0]
    block_id = parts[1]
    return BlockUsageLocator(course_key, block_type, block_id)


def get_tags_count(xblock: XBlock, include_children=False) -> dict[str, int]:
    """
    Returns a map with tag count of the `xblock`

    Use `include_children` to include each children on the query.
    """
    query_list = [str(xblock.location)]

    if include_children:
        children = xblock.get_children()
        child_usage_keys = [str(child.location) for child in children]
        query_list.extend(child_usage_keys)

    tags_count_query = ",".join(query_list)

    return get_object_tag_counts(tags_count_query, count_implicit=True)
