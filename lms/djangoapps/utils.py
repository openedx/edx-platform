"""
Helper Methods
"""
import six


def _get_key(key_or_id, key_cls):
    """
    Helper method to get a course/usage key either from a string or a key_cls,
    where the key_cls (CourseKey or UsageKey) will simply be returned.
    """
    return (
        key_cls.from_string(key_or_id)
        if isinstance(key_or_id, six.string_types)
        else key_or_id
    )
