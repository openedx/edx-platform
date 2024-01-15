"""
general helper functions for xblocks
"""

from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content_tagging.api import get_object_tag_counts


def usage_key_with_run(usage_key_string):
    """
    Converts usage_key_string to a UsageKey, adding a course run if necessary
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    return usage_key


def get_children_tags_count(xblock):
    """
    Returns a map with tag count of each child
    """
    children = xblock.get_children()
    child_usage_keys = [str(child.location) for child in children]
    tags_count_query = ','.join(child_usage_keys)
    return get_object_tag_counts(tags_count_query, count_implicit=True)
