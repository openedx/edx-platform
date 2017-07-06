"""
Helper functions for unit tests
"""

from opaque_keys.edx.keys import UsageKey


def deserialize_usage_key(usage_key_string, course_key):
    """
    Returns the deserialized UsageKey object of the given usage_key_string for the given course.
    """
    return UsageKey.from_string(usage_key_string).replace(course_key=course_key)
