"""
Utils functions for tagging
"""
from __future__ import annotations

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2

from .types import ContentKey


def get_content_key_from_string(key_str: str) -> ContentKey:
    """
    Get content key from string
    """
    try:
        return CourseKey.from_string(key_str)
    except InvalidKeyError:
        try:
            return LibraryLocatorV2.from_string(key_str)
        except InvalidKeyError:
            try:
                return UsageKey.from_string(key_str)
            except InvalidKeyError as usage_key_error:
                raise ValueError("object_id must be a CourseKey, LibraryLocatorV2 or a UsageKey") from usage_key_error


def get_context_key_from_key_string(key_str: str) -> CourseKey | LibraryLocatorV2:
    """
    Get context key from an key string
    """
    content_key = get_content_key_from_string(key_str)
    # If the content key is a CourseKey or a LibraryLocatorV2, return it
    if isinstance(content_key, CourseKey) or isinstance(content_key, LibraryLocatorV2):
        return content_key

    # If the content key is a UsageKey, return the context key
    context_key = content_key.context_key

    if isinstance(context_key, CourseKey) or isinstance(context_key, LibraryLocatorV2):
        return context_key

    raise ValueError("context must be a CourseKey or a LibraryLocatorV2")

