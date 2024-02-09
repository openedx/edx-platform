"""
Types used by content tagging API and implementation
"""
from typing import Union

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2

ContentKey = Union[LibraryLocatorV2, CourseKey, UsageKey]
