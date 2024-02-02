"""
Utils functions for tagging
"""
from __future__ import annotations

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from .types import ContentKey


def get_content_key_from_string(key_str: str) -> ContentKey:
    """
    Get content key from string
    """
    # Library locators are also subclasses of CourseKey
    try:
        return CourseKey.from_string(key_str)
    except InvalidKeyError:
        try:
            return UsageKey.from_string(key_str)
        except InvalidKeyError as usage_key_error:
            raise ValueError("object_id must be from a CourseKey or a UsageKey") from usage_key_error


def get_context_key_from_key_string(key_str: str) -> CourseKey:
    """
    Get context key from an key string
    """
    content_key = get_content_key_from_string(key_str)
    if isinstance(content_key, CourseKey):
        return content_key

    if not isinstance(content_key.context_key, CourseKey):
        raise ValueError("context must be from a CourseKey")

    return content_key.context_key
